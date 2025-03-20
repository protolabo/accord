# app/routes/auth.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt
from httpx import AsyncClient
from app.core.config import settings
from app.db.models import User
from datetime import datetime, timedelta

router = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
)

async def get_microsoft_user(code: str):
    async with AsyncClient() as client:
        # 1. Get access token
        token_response = await client.post(
            f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
            data={
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.REDIRECT_URI,
                "scope": "openid profile email Mail.Read"
            }
        )
        
        token_data = token_response.json()
        if "error" in token_data:
            raise HTTPException(400, token_data["error_description"])
            # raise Exception(f"Failed request token: {token_data["error_description"]}")

        # 2. Get User Information
        user_response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        
        return {
            "microsoft_id": user_response.json()["id"],
            "email": user_response.json()["mail"],
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data["expires_in"]
        }

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
    user_info = await get_microsoft_user(code)
    
    # 3. Save or update user to MongoDB
    user = await User.find_one(User.microsoft_id == user_info["microsoft_id"])
    
    if not user:
        user = User(
            microsoft_id=user_info["microsoft_id"],
            email=user_info["email"],
            outlook_tokens={
                "access_token": user_info["access_token"],
                "refresh_token": user_info["refresh_token"],
                "expires_at": datetime.now() + timedelta(seconds=user_info["expires_in"])
            }
        )
        await user.insert()
    else:
        user.outlook_tokens = {
            "access_token": user_info["access_token"],
            "refresh_token": user_info["refresh_token"],
            "expires_at": datetime.now() + timedelta(seconds=user_info["expires_in"])
        }
        await user.save()
    
    # 4. Generate JWT Token
    return {
        "access_token": create_jwt_token(user.email),
        "user_info": {
            "email": user.email,
            "microsoft_id": user.microsoft_id
        }
    }