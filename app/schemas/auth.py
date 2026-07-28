from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(alias="fullName", min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    model_config = ConfigDict(populate_by_name=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    model_config = ConfigDict(populate_by_name=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")
    model_config = ConfigDict(populate_by_name=True)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")
    model_config = ConfigDict(populate_by_name=True)
