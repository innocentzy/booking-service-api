from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_user, get_user_by_email
from app.database import get_db
from app.models import TokenType
from app.schemas import LoginRequest, Token, UserCreate, UserResponse, TokensPair
from app.security import (
    create_access_token,
    verify_password,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register/{role}", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(role, user: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    return await create_user(db, user, role)


@router.post("/login", response_model=TokensPair)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, credentials.email)

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": Token(value=access_token, token_type=TokenType.ACCESS),
        "refresh_token": Token(value=refresh_token, token_type=TokenType.REFRESH),
    }


@router.post("/update-token", response_model=TokensPair)
async def update_token(token: Token):
    if token.token_type is not TokenType.REFRESH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect refresh token",
        )

    payload = decode_token(token.value)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    return {
        "access_token": Token(value=access_token, token_type=TokenType.ACCESS),
        "refresh_token": Token(value=refresh_token, token_type=TokenType.REFRESH),
    }
