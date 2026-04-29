"""聊天相关 Schema"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    character_id: str
    message: str
    image_data: str | None = None  # base64


class ChatResponse(BaseModel):
    reply: str


class GenerateImageRequest(BaseModel):
    prompt: str
    character_name: str | None = None
