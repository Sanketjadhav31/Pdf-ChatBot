from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import (
    User,
    create_access_token,
    get_current_user,
    get_db,
    get_password_hash,
    verify_password,
)
from models.schemas import TokenResponse, UserOut

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenResponse)
def register(request: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        email=request.email.lower(),
        hashed_password=get_password_hash(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(days=7))
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(id=user.id, email=user.email),
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(request: AuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(days=7))
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(id=user.id, email=user.email),
    )


@router.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=current_user.id, email=current_user.email)

