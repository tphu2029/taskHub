import uuid
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, user_in: RegisterRequest) -> User:
        stmt = select(User).where(User.email == user_in.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )

        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=get_password_hash(user_in.password),
            role=UserRole.MEMBER,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def refresh_token(
        db: AsyncSession, redis_conn: Redis, refresh_in: RefreshTokenRequest
    ) -> TokenResponse:
        token = refresh_in.refresh_token
        try:
            is_blacklisted = await redis_conn.get(f"blacklist:{token}")
            if is_blacklisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked",
                )
        except HTTPException:
            raise
        except Exception:
            pass

        payload = decode_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        new_access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)

        try:
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
            await redis_conn.setex(f"blacklist:{token}", ttl, "revoked")
        except Exception:
            pass

        return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)

    @staticmethod
    async def logout(redis_conn: Redis, logout_in: LogoutRequest) -> dict[str, str]:
        token = logout_in.refresh_token
        payload = decode_token(token)
        token_type = payload.get("type")

        if not payload or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token"
            )

        try:
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
            await redis_conn.setex(f"blacklist:{token}", ttl, "revoked")
        except Exception:
            pass

        return {"message": "Successfully logged out"}
