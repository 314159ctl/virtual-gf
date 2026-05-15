"""用户相关 Pydantic Schema"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    avatar_url: str | None
    membership_tier: str
    membership_expires_at: datetime | None
    is_admin: bool
    has_api_key: bool = False  # 是否已配置 API key（不暴露实际值）
    api_base_url: str | None = None
    api_model: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
    api_key: str | None = None
    api_base_url: str | None = None
    api_model: str | None = None
