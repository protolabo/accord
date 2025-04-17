from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
from httpx import AsyncClient
from app.core.config import settings
from app.db.models import User
from app.services.email.outlookAuth import OutlookAuth
from app.email_providers.google.gmail_auth import GmailAuthManager
from datetime import datetime, timedelta
from app.core.security import create_jwt_token
import os

router = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
)

# Get login url for Outlook
@router.get("/outlook/login")
async def outlook_login():
    return {
        "auth_url": f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={settings.REDIRECT_URI}"
        f"&scope=openid%20profile%20email%20Mail.Read%20Mail.ReadWrite%20Mail.Send"
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
        "jwt_token": create_jwt_token({"sub": user.microsoft_id}),
        "user_info": {
            "email": user.email,
            "microsoft_id": user.microsoft_id
        }
    }

# Get login url for Gmail
@router.get("/gmail/login")
async def gmail_login():
    # Initialize Gmail Auth Manager with your credentials
    from app.email_providers.google.settings import GOOGLE_CREDENTIALS_PATH, TOKEN_DIR
    auth_manager = GmailAuthManager(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR)
    
    # Generate a state to identify the user after callback
    state = "random_state_value"  # In production, use a secure random value
    
    # Get authentication URL
    auth_url = auth_manager.get_auth_url(state)
    
    return {
        "auth_url": auth_url
    }

# Callback from Gmail
@router.get("/gmail/callback")
async def gmail_callback(code: str, state: str = None):
    # Initialize Gmail Auth Manager
    from app.email_providers.google.settings import GOOGLE_CREDENTIALS_PATH, TOKEN_DIR
    auth_manager = GmailAuthManager(GOOGLE_CREDENTIALS_PATH, TOKEN_DIR)
    
    # Exchange code for tokens
    tokens = auth_manager.exchange_code_for_tokens(code)
    
    # Get user info
    user_info = auth_manager.get_user_info(tokens["access_token"])
    
    # Create or update user in MongoDB
    user = await User.find_one(User.email == user_info["email"])
    if not user:
        user = User(
            email=user_info["email"],
            google_id=user_info["id"],
            gmail_tokens={
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token"),
                "expires_at": datetime.now() + timedelta(seconds=tokens["expires_in"])
            }
        )
    else:
        # Update tokens
        user.google_id = user_info["id"]
        user.gmail_tokens = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token") or user.gmail_tokens.get("refresh_token"),
            "expires_at": datetime.now() + timedelta(seconds=tokens["expires_in"])
        }
    await user.save()
    
    # Generate JWT token
    return {
        "jwt_token": create_jwt_token({"sub": user.microsoft_id}),
        "user_info": {
            "email": user.email,
            "google_id": user.google_id
        }
    }