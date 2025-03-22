from httpx import AsyncClient, HTTPStatusError
from datetime import datetime, timedelta
from app.core.config import settings
from app.db.models import User
from fastapi import HTTPException

class OutlookAuth:
    # Get OAuth2 access token
    @staticmethod
    async def get_oauth_tokens(code: str) -> dict:
        async with AsyncClient() as client:
            try:
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
                token_response.raise_for_status()
                return token_response.json()
            
            except HTTPStatusError as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed request token: {e.response.text}"
                )
    # Get User Profile
    @staticmethod
    async def get_user_profile(access_token: str) -> dict:
        async with AsyncClient() as client:
            try:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except HTTPStatusError as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Get User profile failed: {e.response.text}"
                )