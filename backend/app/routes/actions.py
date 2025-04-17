from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.db.models import User, Email
from app.core.security import get_current_user
from app.services.email.outlookClient import OutlookClient
from app.services.ai.pipeline import process_email
from app.services.email.email_sync import sync_emails_for_user

# -------------------------------------------------
router = APIRouter()


# Is read ?
@router.post("/emails/{email_id}/read")
async def update_email_read_status(
    email_id: str,
    is_read: bool,
    user: User = Depends(get_current_user)
):
    # Validate User
    email = await Email.find_one(
        Email.email_id == email_id,
        Email.user_id == user.microsoft_id
    )
    if not email:
        raise HTTPException(404, "Email does not exist or not accessible")
    
    email.is_read = is_read
    await email.save()
    
    return {"message": "Email read status updated", "email_id": email_id, "is_read": is_read}

# Classification pipeline
@router.post("/sync_emails")
async def sync_emails(
    user=Depends(get_current_user), 
    since: datetime = Query(default_factory=lambda: datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
):
    result = await sync_and_classify_emails(user, since)
    return result