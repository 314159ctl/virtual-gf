"""角色相关 Schema"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CharacterCreate(BaseModel):
    name: str
    description: str | None = None
    system_prompt: str
    avatar_url: str | None = None
    is_public: bool = False
    tags: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    avatar_url: str | None = None
    is_public: bool | None = None
    tags: str | None = None


class CharacterOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    system_prompt: str
    avatar_url: str | None
    is_template: bool
    is_public: bool
    tags: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
