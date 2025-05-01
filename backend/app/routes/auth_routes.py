from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from backend.app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.app.email_providers.google.gmail_auth import GmailAuthManager
from backend.app.email_providers.google.email_utils import normalize_email_for_storage

router = APIRouter(prefix="/auth")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: Optional[str] = None
    service: Optional[str] = "google"


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for standard OAuth2 token generation.
    This could be used for a username/password login flow in the future.
    """
    # This is a placeholder - you would normally validate user credentials here
    user_data = {"email": form_data.username}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=user_data, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/google/token")
async def google_login_token(user_data: dict = Body(...)):
    """
    Endpoint to generate a JWT token after Google OAuth authentication.
    Called by the frontend after Google authentication is complete.
    """
    if "email" not in user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    email = user_data["email"]
    user_id = normalize_email_for_storage(email)

    # Verify that the user is authenticated with Google
    auth_manager = GmailAuthManager()
    if not auth_manager.is_authenticated(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated with Google"
        )

    # Create and return JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": email, "user_id": user_id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_email": email
    }