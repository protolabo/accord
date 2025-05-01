from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional

from backend.app.core.security import SECRET_KEY, ALGORITHM

# OAuth2 scheme for bearer token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the JWT token and returns the user data.
    This function can be used as a dependency to protect routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        user_id: str = payload.get("user_id")

        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email, user_id=user_id)
        return token_data

    except JWTError:
        raise credentials_exception