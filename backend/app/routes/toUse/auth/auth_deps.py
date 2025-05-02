from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.security import get_current_user
from app.db.models import User

jwt_scheme = OAuth2PasswordBearer(tokenUrl="/auth/{provider}/callback", auto_error=False)

async def get_current_user_optional(
    token: str = Depends(jwt_scheme)
) -> Optional[User]:
    try:
        return await get_current_user(token)
    except:
        return None