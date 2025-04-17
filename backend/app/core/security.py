from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.db.models import User
from app.core.config import settings
from datetime import datetime, timedelta

jwt_scheme = OAuth2PasswordBearer(tokenUrl="/auth/{provider}/callback")

# Get current user
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

# Create JWT Token
def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(hours=8)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )