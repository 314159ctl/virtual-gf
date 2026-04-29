"""会话管理 API"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.character import Character
from app.models.message import Message
from app.models.user import User

router = APIRouter()


@router.get("")
async def list_conversations(
    character_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户的会话列表"""
    stmt = select(Conversation).where(Conversation.user_id == current_user.id)
    if character_id:
        stmt = stmt.where(Conversation.character_id == character_id)
    stmt = stmt.order_by(Conversation.updated_at.desc()).limit(50)

    result = await db.execute(stmt)
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "character_id": str(c.character_id),
            "title": c.title,
            "message_count": c.message_count,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


@router.post("")
async def create_conversation(
    character_id: uuid.UUID,
    title: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新会话"""
    # 验证角色存在
    char_result = await db.execute(select(Character).where(Character.id == character_id))
    char = char_result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    conv = Conversation(
        user_id=current_user.id,
        character_id=character_id,
        title=title or f"与{char.name}的对话",
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)

    return {
        "id": str(conv.id),
        "character_id": str(conv.character_id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
    }


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, le=200),
    before: uuid.UUID | None = Query(None),  # 游标分页
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话消息（游标分页）"""
    # 权限检查
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")

    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if before:
        stmt = stmt.where(Message.id < before)
    stmt = stmt.order_by(Message.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "content_type": m.content_type,
            "metadata": m.metadata_,
            "emotion_label": m.emotion_label,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(messages)
    ]


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除会话及其所有消息"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此会话")

    await db.delete(conv)
    await db.flush()
