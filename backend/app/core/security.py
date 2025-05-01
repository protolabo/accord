from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
#from backend.app.db.models import User
#from backend.app.core.config import settings
from datetime import datetime, timedelta

jwt_scheme = OAuth2PasswordBearer(tokenUrl="/auth/{provider}/callback")

# Get current user
""""
async def get_current_user(token: str = Depends(jwt_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

        # Decoded Info
        user_id    = payload.get("sub")
        provider   = payload.get("provider")
        account_id = payload.get("account_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        # Find User
        user = await User.find_one(User.user_id == user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if provider and account_id:
            matched = any(
                acc.provider == provider and
                acc.user_id_on_platform == account_id
                for acc in user.accounts
            )
            if not matched:
                raise HTTPException(status_code=403, detail="Account not linked to this user")

        return user
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

current_user = get_current_user
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets
from jose import jwt
from passlib.context import CryptContext

# This is a generated secure key - only for testing!
SECRET_KEY = "b496e1c3d8b5e83af48901cd39f5f0c67a0f3f8f0b3ba5a0db4dbc820abd53b9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT token with the given data and expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    """
    Verifies if the plain password matches the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Creates a hash for the given password.
    """
    return pwd_context.hash(password)