from datetime import timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from database import (
    create_access_token,
    get_current_user,
    get_database,
    get_password_hash,
    verify_password,
)
from models.schemas import TokenResponse, UserOut

class AuthRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenResponse)
async def register(request: AuthRequest, db = Depends(get_database)) -> TokenResponse:
    if not request.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required",
        )
    
    existing = await db.users.find_one({"email": request.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user_id = str(uuid.uuid4())
    user_doc = {
        "_id": user_id,
        "email": request.email.lower(),
        "username": request.username,
        "hashed_password": get_password_hash(request.password),
        "created_at": None,  # MongoDB will set this with server timestamp
    }
    
    from datetime import datetime, timedelta
    user_doc["created_at"] = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    await db.users.insert_one(user_doc)

    access_token = create_access_token(data={"sub": user_id}, expires_delta=timedelta(days=7))
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(id=user_id, email=user_doc["email"], username=user_doc["username"]),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: AuthRequest, db = Depends(get_database)) -> TokenResponse:
    user = await db.users.find_one({"email": request.email.lower()})
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user["_id"]}, expires_delta=timedelta(days=7))
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(id=user["_id"], email=user["email"], username=user["username"]),
    )


@router.get("/auth/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)) -> UserOut:
    return UserOut(id=current_user["_id"], email=current_user["email"], username=current_user["username"])
