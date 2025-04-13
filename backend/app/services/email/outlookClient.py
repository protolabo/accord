from app.core.config import settings
from app.db.models import User
from httpx import AsyncClient, HTTPError
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Refresh Outlook Access Token
async def refresh_outlook_token(user: User) -> bool:
    # Simulate token refresh
    if settings.IS_DEMO:
        user.outlook_tokens = {
            "access_token": "dummy_access_token_refreshed",
            "refresh_token": user.outlook_tokens.get("refresh_token", "dummy_refresh_token"),
            "expires_at": datetime.now() + timedelta(seconds=3600)
        }
        await user.save()
        return True
    
    # Real token refresh process
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
        # Do not check in simulate state
        if settings.IS_DEMO:
            return
        
        # Real check process
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

        # Simulate get emails (get data from mock emails file)
        if settings.IS_DEMO:
            try:
                with open(settings.MOCK_DATA_FILE, 'r', encoding='utf-8') as f:
                    email_data = json.load(f)
                
                for email in email_data:
                    if datetime.strptime(email["date"], "%Y-%m-%d %H:%M:%S") >= since:
                        email_filtered = {key: value for key, value in email.items() if key != "body"}
                        all_emails.append(email_filtered)
            
                return all_emails
            except Exception as e:
                logger.error(f"Read mock data failed: {e}")
                return all_emails
        
        # Real get email process
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
                    "received_at": msg["receivedDateTime"],
                    "cc": [cc["emailAddress"]["address"] for cc in msg.get("ccRecipients", [])],
                    "bcc": [bcc["emailAddress"]["address"] for bcc in msg.get("bccRecipients", [])]
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

        # Simulation
        if settings.IS_DEMO:
            try:
                with open(settings.MOCK_DATA_FILE, 'r', encoding='utf-8') as f:
                    emails = json.load(f)
                for email in emails:
                    if email.get("id") == email_id:
                        return email.get("body", "")
                logger.error(f"No email found with id: {email_id}")
                return ""
            except Exception as e:
                logger.error(f"Read mock data failed: {e}")
                return ""
            
        # Real process
        try:
            response = await self.client.get(f"/me/messages/{email_id}?$select=body")
            response.raise_for_status()
            return response.json()["body"]["content"]
        except HTTPError as e:
            logger.error(f"Get email body failed: {e}")
            return ""
        

    # Forward an email
    async def forward_email(self, email_id: str, to: list, comment: str = "") -> bool:
        await self._check_token()

        # Simulate forwarding email
        if settings.IS_DEMO:
            logger.info(f"Simulate forwarding: Email_ID={email_id}, Receiver={to}, Comment={comment}")
            return True
         
        # Real process
        try:
            payload = {
                "comment": comment,
                "toRecipients": [{"emailAddress": {"address": address}} for address in to]
            }
            response = await self.client.post(f"/me/messages/{email_id}/forward", json=payload)
            response.raise_for_status()
            return True
        except HTTPError as e:
            logger.error(f"Forward email failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error when forwarding email: {str(e)}")
        return False
    

    # Reply email
    async def reply_email(self, email_id: str, comment: str) -> bool:
        await self._check_token()

        # Simulate replying
        if settings.IS_DEMO:
            logger.info(f"Simulate replying: Email_ID={email_id}, Reply_content={comment}")
            return True
        
        # Real process
        try:
            payload = {"comment": comment}
            response = await self.client.post(f"/me/messages/{email_id}/reply", json=payload)
            response.raise_for_status()
            return True
        except HTTPError as e:
            logger.error(f"Reply email failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error when replying email: {str(e)}")
        return False
    

    # Send email
    async def send_email(self, subject: str, content: str, to: List[str], cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, content_type: str = "HTML") -> bool:
        await self._check_token()
        
        # Simulate sending email
        if settings.IS_DEMO:
            logger.info(f"Simulate sending email: Subject='{subject}', Receiver={to}, Cc={cc}, Bcc={bcc}, Content='{content[:50]}...'")
            return True

        # Real sending process
        message = {
            "subject": subject,
            "body": {
                "contentType": content_type,
                "content": content
            },
            "toRecipients": [{"emailAddress": {"address": email}} for email in to]
        }
        if cc:
            message["ccRecipients"] = [{"emailAddress": {"address": email}} for email in cc]
        if bcc:
            message["bccRecipients"] = [{"emailAddress": {"address": email}} for email in bcc]
        
        payload = {"message": message, "saveToSentItems": "true"}
        
        try:
            response = await self.client.post("/me/sendMail", json=payload)
            response.raise_for_status()
            return True
        except HTTPError as e:
            logger.error(f"Failed sending email: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error when sending email: {str(e)}")
            return False
    

    # Delete email
    async def delete_email(self, email_id: str) -> bool:
        await self._check_token()
        
        # Simulation 
        if settings.IS_DEMO:
            logger.info(f"Simulate deleting email: Email_ID={email_id}")
            return True
        
        # Real process
        try:
            response = await self.client.delete(f"/me/messages/{email_id}")
            response.raise_for_status()
            return True
        except HTTPError as e:
            logger.error(f"Failed delete email: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error when deleting email: {str(e)}")
            return False