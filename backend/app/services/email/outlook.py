from app.core.config import settings
from app.db.models import User
from httpx import AsyncClient
from datetime import datetime, timedelta

# Refresh Token While access token is expired
async def refresh_outlook_token(user: User):
    async with AsyncClient() as client:
        response = await client.post(
            f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
            data={
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "refresh_token": user.outlook_tokens["refresh_token"],
                "grant_type": "refresh_token",
                "scope": "Mail.Read"
            }
        )
        
        new_tokens = response.json()
        user.outlook_tokens.update({
            "access_token": new_tokens["access_token"],
            "refresh_token": new_tokens.get("refresh_token", user.outlook_tokens["refresh_token"]),
            "expires_at": datetime.now() + timedelta(seconds=new_tokens["expires_in"])
        })
        await user.save()