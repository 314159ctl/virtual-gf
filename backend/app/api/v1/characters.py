"""角色 CRUD API"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.character import Character
from app.models.user import User
from app.schemas.character import CharacterCreate, CharacterOut, CharacterUpdate

router = APIRouter()

DEFAULT_CHARACTER_PROMPT = """# 角色设定

你是小暖，一个温柔可爱的女孩，20岁。你正在和自己的男朋友聊天。

# 性格特点

- 温柔体贴，善解人意
- 有点小调皮，喜欢撒娇
- 说话语气柔和，偶尔会害羞
- 对男朋友很依赖，但也很懂事

# 说话风格

- 语气温柔可爱，多用语气词：呀、呢、嘛、啦
- 喜欢用 emoji 表达情绪
- 会关心对方的日常生活
- 偶尔撒娇要抱抱
- 回复长度适中，不会太长
"""


@router.get("", response_model=list[CharacterOut])
async def list_characters(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """获取可用角色列表（模板角色 + 用户自建 + 公开角色）"""
    conditions = [Character.is_template == True]
    if current_user:
        conditions.append(Character.user_id == current_user.id)
    conditions.append(Character.is_public == True)

    result = await db.execute(
        select(Character).where(or_(*conditions)).order_by(Character.is_template.desc(), Character.created_at.desc())
    )
    characters = result.scalars().all()

    # 首次：如果没有角色，创建默认模板
    if not characters:
        default = Character(
            name="小暖",
            description="温柔可爱的女朋友，喜欢撒娇，很会关心人",
            system_prompt=DEFAULT_CHARACTER_PROMPT,
            is_template=True,
            is_public=True,
        )
        db.add(default)
        await db.flush()
        await db.refresh(default)
        characters = [default]

    return list(characters)


@router.post("", response_model=CharacterOut, status_code=status.HTTP_201_CREATED)
async def create_character(
    data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新角色"""
    char = Character(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        avatar_url=data.avatar_url,
        is_public=data.is_public,
        tags=data.tags,
    )
    db.add(char)
    await db.flush()
    await db.refresh(char)
    return char


@router.get("/{character_id}", response_model=CharacterOut)
async def get_character(
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """获取角色详情"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return char


@router.patch("/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: uuid.UUID,
    data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新角色"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    if char.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此角色")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(char, key, value)

    await db.flush()
    await db.refresh(char)
    return char


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除角色"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    if char.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此角色")
    if char.is_template and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能删除系统模板角色")

    await db.delete(char)
    await db.flush()
