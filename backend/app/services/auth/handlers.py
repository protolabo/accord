from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Callable, Awaitable

from app.core.config import settings
from app.core.security import create_jwt_token
from app.db.models import User, EmailAccount, TokenInfo
from backend.app.services.auth.outlookAuth import OutlookAuth
from app.email_providers.google.gmail_auth import GmailAuthManager

# ---------------------------------------------------
SUPPORTED = {"outlook", "gmail"}

# -------------------Login Handler----------------------
# Outlook login URL
async def _outlook_login() -> str:
    return (
        f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={settings.REDIRECT_URI}"
        f"&scope=openid profile email Mail.Read Mail.ReadWrite Mail.Send"
    )

# Gmail login URL
async def _gmail_login() -> str:
    from app.email_providers.google.settings import GOOGLE_CREDENTIALS_PATH, TOKEN_DIR
    mgr = GmailAuthManager(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR)
    state = "secure_random_state"  # In production, use a secure random value
    return mgr.get_auth_url(state)

login_handlers: dict[str, Callable[[], Awaitable[str]]] = {
    "outlook": _outlook_login,
    "gmail":  _gmail_login,
}

# -------------------CallBack Handler----------------------
# Outlook Callback
async def _outlook_callback(code: str, state: Optional[str], current_user: Optional[User]) -> JSONResponse:
    raw = await OutlookAuth.get_oauth_tokens(code)
    token_info = TokenInfo(
        access_token = raw["access_token"],
        refresh_token = raw.get("refresh_token"),
        expires_at = datetime.now() + timedelta(seconds=raw["expires_in"])
    )
    profile = await OutlookAuth.get_user_profile(token_info.access_token)
    platform_id = profile["id"]
    email_addr = profile.get("mail") or profile.get("userPrincipalName")
    display = profile.get("displayName")
    return _upsert_user_and_issue_jwt("outlook", platform_id, email_addr, display, token_info, current_user)

# Gmail Callback
async def _gmail_callback(code: str, state: Optional[str], current_user: Optional[User]) -> JSONResponse:
    from app.email_providers.google.settings import GOOGLE_CREDENTIALS_PATH, TOKEN_DIR
    mgr = GmailAuthManager(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR)
    raw = mgr.exchange_code_for_tokens(code)
    token_info = TokenInfo(
        access_token=raw["access_token"],
        refresh_token=raw.get("refresh_token"),
        expires_at=datetime.now() + timedelta(seconds=raw["expires_in"])
    )
    profile = mgr.get_user_info(raw["access_token"])
    platform_id = profile["id"]
    email_addr = profile["email"]
    display = profile.get("name")
    return _upsert_user_and_issue_jwt("gmail", platform_id, email_addr, display, token_info, current_user)

callback_handlers: dict[str, Callable[[str, Optional[str], Optional[User]], Awaitable[JSONResponse]]] = {
    "outlook": _outlook_callback,
    "gmail":  _gmail_callback,
}


# -------------------Util Function----------------------

# Create User in DataBase and Issue JWT Token
async def _upsert_user_and_issue_jwt(
    provider: str,
    platform_id: str,
    email_addr: str,
    display: Optional[str],
    token_info: TokenInfo,
    current_user: Optional[User] = None
) -> JSONResponse:
    # Create or find User
    if current_user:    # New account for existing user
        user = current_user
    else:   # Other User or new User
        user = await User.find_one({
            "accounts": {
                "$elemMatch": {
                    "provider": provider,
                    "user_id_on_platform": platform_id
                }
            }
        }) or User()

    # Renew or Add EmailAccount
    existing_email = next(
        (acc for acc in user.accounts
         if acc.provider == provider and acc.user_id_on_platform == platform_id),
        None
    )
    if existing_email:
        existing_email.tokens = token_info
        existing_email.email = email_addr
        existing_email.display_name = display
    else:
        user.accounts.append(
            EmailAccount(
                provider=provider,
                email=email_addr,
                user_id_on_platform=platform_id,
                tokens=token_info,
                display_name=display,
                primary=not user.accounts
            )
        )

    await user.save()

    # Issue JWT
    jwt_token = create_jwt_token({
        "sub": user.user_id,
        "provider": provider,
        "account_id": platform_id
    })
    return JSONResponse({
        "jwt_token": jwt_token,
        "user": {
            "user_id": user.user_id,
            "email": email_addr,
            "provider": provider
        }
    })

