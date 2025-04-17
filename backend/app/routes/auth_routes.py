from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional

from app.services.auth.handlers import SUPPORTED, login_handlers, callback_handlers, get_current_user_optional
from app.db.models import User

# ----------------------------------------------------
router = APIRouter()

# -------------------------Routes---------------------------
# Get Login URL
@router.get("/auth/{provider}/login")
async def oauth_login(provider: str):
    if provider not in login_handlers:
        raise HTTPException(400, f"Do not supported provider: {provider}")
    auth_url = await login_handlers[provider]()
    return {"provider": provider, "auth_url": auth_url}

# Callback
@router.get("/auth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: Optional[str] = None, current_user: Optional[User] = Depends(get_current_user_optional)):
    if provider not in callback_handlers:
        raise HTTPException(400, f"Do not supported provider: {provider}")
    return await callback_handlers[provider](code, state, current_user)