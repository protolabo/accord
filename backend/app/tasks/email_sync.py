from celery import Celery
from datetime import datetime
from app.db.connection import get_db
from app.services.email.outlook import OutlookService

celery = Celery(__name__, broker="redis://localhost:6379/0")

@celery.task
async def sync_outlook_emails(user_id: str, access_token: str):
    db = get_db()
    outlook = OutlookService(access_token)
    
    # Get last sync time
    user = await db.users.find_one({"_id": user_id})
    last_sync = user.get("last_sync") or datetime(1970, 1, 1)
    
    # Get new mail
    emails = await outlook.get_emails(last_sync)
    
    # # Extract email infos
    # if emails:
    #     await db.emails.insert_many([{
    #         "user_id": user_id,
    #         "platform": "outlook",
    #         "raw_data": email,
    #         "metadata": {
    #             "received": email["receivedDateTime"],
    #             "sender": email["from"]["emailAddress"]["address"]
    #         }
    #     } for email in emails])
    
    # Update sync time
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"last_sync": datetime.utcnow()}}
    )