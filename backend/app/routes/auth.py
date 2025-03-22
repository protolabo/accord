from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
from httpx import AsyncClient
from app.core.config import settings
from app.db.models import User
from app.services.email.outlookAuth import OutlookAuth
from datetime import datetime, timedelta
from app.core.security import create_jwt_token

router = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
)

# Get login url
@router.get("/outlook/login")
async def outlook_login():
    return {
        "auth_url": f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={settings.REDIRECT_URI}"
        f"&scope=openid profile email Mail.Read"
    }

# Callback from outlook
@router.get("/outlook/callback")
async def outlook_callback(code: str): # Paremeter code returned directly by microsoft service ex./outlook/callback?code=YOUR_AUTH_CODE
    # Get Access Token
    tokens = await OutlookAuth.get_oauth_tokens(code)

    # Get User Profile
    user_info = await OutlookAuth.get_user_profile(tokens["access_token"])

    # Create or update user to MongoDB
    user = await User.find_one(User.microsoft_id == user_info["id"])
    if not user:
        user = User(
            microsoft_id=user_info["id"],
            email=user_info["mail"],
            outlook_tokens={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "expires_at": datetime.now() + timedelta(seconds=tokens["expires_in"])
            }
        )
    else:
        user.outlook_tokens = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_at": datetime.now() + timedelta(seconds=tokens["expires_in"])
        }
    await user.save()
    
    # Generate JWT Token
    return {
        "access_token": create_jwt_token(user.email),
        "user_info": {
            "email": user.email,
            "microsoft_id": user.microsoft_id
        }
    }