from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.db.models import User
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password
)

router = APIRouter()

@router.post("/register")
async def register(username: str, email: str, password: str):
    if await User.find_one(User.username == username):
        raise HTTPException(status_code=400, detail="Username exists")
    
    hashed_pwd = get_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed_pwd)
    await user.insert()
    return {"message": "User created"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.username == form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}