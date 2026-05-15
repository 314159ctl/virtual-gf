"""长期记忆 API"""

import uuid

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_optional_user
from app.db.session import get_db
from app.models.memory import LongTermMemory
from app.models.user import User
from app.services.memory_service import consolidate_memories


class MemoryUpdate(BaseModel):
    content: str | None = None
    importance: int | None = None

router = APIRouter()


@router.get("")
async def list_memories(
    character_id: uuid.UUID | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """获取用户的长期记忆"""
    stmt = (
        select(LongTermMemory)
        .where(LongTermMemory.user_id == current_user.id)
        .order_by(LongTermMemory.importance.desc(), LongTermMemory.created_at.desc())
        .limit(limit)
    )
    if character_id:
        stmt = stmt.where(LongTermMemory.character_id == character_id)

    result = await db.execute(stmt)
    memories = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "character_id": str(m.character_id),
            "content": m.content,
            "importance": m.importance,
            "created_at": m.created_at.isoformat(),
        }
        for m in memories
    ]


@router.post("/consolidate")
async def trigger_consolidation(
    character_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """触发记忆合并：将短期对话总结为长期记忆"""
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    result = await consolidate_memories(str(character_id), str(current_user.id), db)
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    character_id: uuid.UUID,
    content: str,
    importance: int = 3,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """手动添加一条长期记忆"""
    if importance < 1 or importance > 5:
        raise HTTPException(status_code=400, detail="重要性为 1-5")

    memory = LongTermMemory(
        user_id=current_user.id,
        character_id=character_id,
        content=content,
        importance=importance,
    )
    db.add(memory)
    await db.flush()
    await db.refresh(memory)

    return {
        "id": str(memory.id),
        "content": memory.content,
        "importance": memory.importance,
    }


@router.patch("/{memory_id}")
async def update_memory(
    memory_id: uuid.UUID,
    data: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """编辑记忆内容或重要性"""
    result = await db.execute(select(LongTermMemory).where(LongTermMemory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    if memory.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    if data.content is not None:
        memory.content = data.content
    if data.importance is not None:
        if data.importance < 1 or data.importance > 5:
            raise HTTPException(status_code=400, detail="重要性为 1-5")
        memory.importance = data.importance

    await db.flush()
    await db.refresh(memory)
    return {
        "id": str(memory.id),
        "content": memory.content,
        "importance": memory.importance,
    }


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """删除一条记忆"""
    result = await db.execute(
        select(LongTermMemory).where(LongTermMemory.id == memory_id)
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记忆不存在")
    if memory.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除")

    await db.delete(memory)
    await db.flush()
