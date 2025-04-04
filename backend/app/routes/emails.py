from fastapi import APIRouter, Depends, HTTPException
from app.db.models import User, Email
from app.core.security import current_user
from app.services.email.outlookClient import OutlookClient
from typing import List, Optional

router = APIRouter()

# Get email contents
@router.get("/emails/{email_id}")
async def get_email_content(
    email_id: str,
    user: User = Depends(current_user)
):
    # Validate User Existence
    email = await Email.find_one(
        Email.email_id == email_id,
        Email.user_id == user.microsoft_id
    )
    if not email:
        raise HTTPException(404, "Email does not exist or not accessible")

    # Get contents from Outlook
    try:
        outlook = OutlookClient(user)
        content = await outlook.get_email_content(email_id)
    except Exception as e:
        raise HTTPException(502, f"Get email content failed: {str(e)}")
    
    return {
        "email_id": email_id,
        "content": content,
        "is_read": email.is_read
    }


# Forward Email
@router.post("/emails/{email_id}/forward")
async def forward_email(
    email_id: str,
    to: List[str],            
    comment: Optional[str] = "",
    user: User = Depends(current_user)
):
    # Validate User
    if not await Email.find_one(
        Email.email_id == email_id,
        Email.user_id == user.microsoft_id
    ).exists():
        raise HTTPException(404, "Email does not exist or not accessible")

    try:
        outlook = OutlookClient(user)
        success = await outlook.forward_email(email_id, to, comment)
    except Exception as e:
        raise HTTPException(502, f"Forward email failed: {str(e)}")
    
    if success:
        return {"message": "Email forwarded successfully"}
    else:
        raise HTTPException(500, "Failed to forward email")


# Reply Email
@router.post("/emails/{email_id}/reply")
async def reply_email(
    email_id: str,
    comment: str,      
    user: User = Depends(current_user)
):
    # Validate User
    if not await Email.find_one(
        Email.email_id == email_id,
        Email.user_id == user.microsoft_id
    ).exists():
        raise HTTPException(404, "Email does not exist or not accessible")

    try:
        outlook = OutlookClient(user)
        success = await outlook.reply_email(email_id, comment)
    except Exception as e:
        raise HTTPException(502, f"Reply email failed: {str(e)}")
    
    if success:
        return {"message": "Email replied successfully"}
    else:
        raise HTTPException(500, "Failed to reply email")
    
