from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserUpdate


class UserService:
    @staticmethod
    async def get_profile(current_user: User) -> User:
        return current_user

    @staticmethod
    async def update_profile(
        db: AsyncSession, current_user: User, user_in: UserUpdate
    ) -> User:
        if user_in.email is not None and user_in.email != current_user.email:
            stmt = select(User).where(User.email == user_in.email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )
            current_user.email = user_in.email

        if user_in.full_name is not None:
            current_user.full_name = user_in.full_name

        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        return current_user

    @staticmethod
    async def change_password(
        db: AsyncSession, current_user: User, pass_in: ChangePasswordRequest
    ) -> dict[str, str]:
        if not verify_password(pass_in.old_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password",
            )

        current_user.hashed_password = get_password_hash(pass_in.new_password)
        db.add(current_user)
        await db.commit()
        return {"message": "Password changed successfully"}
