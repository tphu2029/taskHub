from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    full_name: str | None = Field(default=None, alias="fullName")
    role: UserRole
    is_active: bool = Field(alias="isActive")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, alias="fullName", max_length=255)

    model_config = ConfigDict(populate_by_name=True)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(alias="oldPassword")
    new_password: str = Field(alias="newPassword", min_length=6, max_length=128)

    model_config = ConfigDict(populate_by_name=True)
