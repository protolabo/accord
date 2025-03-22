from fastapi import APIRouter, Depends, HTTPException
from app.db.models import User, Email
from app.core.security import current_user
from app.services.email.outlookClient import OutlookClient

router = APIRouter()

# Get email contents
@router.get("/emails/{email_id}")
async def get_email_content(
    email_id: str,
    user: User = Depends(current_user)
):
    # Validate User Existence
    if not await Email.find_one(
        Email.email_id == email_id,
        Email.user_id == user.microsoft_id
    ).exists():
        raise HTTPException(404, "Email do not exist or not accessible")

    # Get contents from Outlook
    try:
        outlook = OutlookClient(user)
        content = await outlook.get_email_content(email_id)
    except Exception as e:
        raise HTTPException(502, f"Get email content failed: {str(e)}")
    
    return {
        "email_id": email_id,
        "content": content,
        # "analysis": {
        #     "attention_score": calculate_attention(content),
        #     "action_items": extract_actions(content)
        # }
    }