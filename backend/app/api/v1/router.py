"""API v1 路由聚合"""

from fastapi import APIRouter

from app.api.v1 import auth, characters, conversations, memories, users, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(characters.router, prefix="/characters", tags=["角色"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["会话"])
api_router.include_router(memories.router, prefix="/memories", tags=["记忆"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理"])
