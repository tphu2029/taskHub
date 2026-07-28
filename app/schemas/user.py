from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, UUID4
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)
