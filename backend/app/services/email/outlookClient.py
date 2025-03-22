from app.core.config import settings
from app.db.models import User
from httpx import AsyncClient, HTTPError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Refresh Outlook Access Token
async def refresh_outlook_token(user: User) -> bool:
    try:
        async with AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "refresh_token": user.outlook_tokens["refresh_token"],
                    "grant_type": "refresh_token",
                    "scope": "Mail.Read"
                },
                timeout=10
            )
            response.raise_for_status()
            
            new_tokens = response.json()
            user.outlook_tokens = {
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens.get("refresh_token", user.outlook_tokens["refresh_token"]),
                "expires_at": datetime.now() + timedelta(seconds=new_tokens["expires_in"])
            }
            await user.save()
            return True
    except HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Refresh Token Failed {str(e)}")
    return False


class OutlookClient:
    def __init__(self, user: User):
        self.user = user
        self.client = AsyncClient(
            base_url="https://graph.microsoft.com/v1.0",
            headers={"Authorization": f"Bearer {user.outlook_tokens['access_token']}"}
        )

    # Check token status and refresh
    async def _check_token(self) -> None:
        if self.user.is_token_expired:
            success = await refresh_outlook_token(self.user)
            if success:
                self.client.headers["Authorization"] = f"Bearer {self.user.outlook_tokens['access_token']}"
            else:
                raise Exception("Cannot Refresh Access Token")

    # Get Emails from Outlook
    async def get_emails(self, since: datetime) -> list:
        await self._check_token()
        all_emails = []
        next_link = None

        while True:
            try:
                if next_link:
                    response = await self.client.get(next_link)
                else:
                    params={
                        "$filter": f"receivedDateTime ge {since.isoformat()}",
                        "$select": "id,subject,from,receivedDateTime",
                        "$top": 100
                    }
                    response = await self.client.get("/me/messages", params=params)
                
                response.raise_for_status()
                data = response.json()

                all_emails.extend([{
                    "email_id": msg["id"],
                    "subject": msg["subject"],
                    "sender": msg["from"]["emailAddress"]["address"],
                    "received_at": msg["receivedDateTime"]
                } for msg in data.get("value", [])])

                next_link = data.get("@odata.nextLink")
                if not next_link:
                    break

            except HTTPError as e:
                logger.error(f"Get email failed: {e}")
                break
        
        return all_emails

    # Get email body
    async def get_email_content(self, email_id: str) -> str:
        await self._check_token()
        try:
            response = await self.client.get(f"/me/messages/{email_id}?$select=body")
            response.raise_for_status()
            return response.json()["body"]["content"]
        except HTTPError as e:
            logger.error(f"Get email body failed: {e}")
            return ""