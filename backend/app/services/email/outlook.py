import httpx
from app.core.config import settings

class OutlookService:
    def __init__(self, access_token: str):
        self.client = httpx.AsyncClient(
            base_url="https://graph.microsoft.com/v1.0",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    async def get_emails(self, since: datetime):
        params = {
            "$filter": f"receivedDateTime ge {since.isoformat()}",
            "$select": "subject,body,from,receivedDateTime",
            "$top": 100
        }
        response = await self.client.get("/me/messages", params=params)
        return response.json().get("value", [])