from fastapi import APIRouter, Depends, HTTPException
from app.db.models import User, Email
from app.core.security import current_user
from app.services.email.outlookClient import OutlookClient
from typing import List, Optional

router = APIRouter()


# Is read ?
@router.post("/emails/{email_id}/read")
async def update_email_read_status(
    email_id: str,
    is_read: bool,
    user: User = Depends(current_user)
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