"""管理员 API — 仪表盘 + 用户管理"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.character import Character
from app.services.system_config import get_system_config, update_system_config

router = APIRouter()


class UserUpdateData(BaseModel):
    is_active: bool | None = None
    membership_tier: str | None = None


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """仪表盘统计数据"""
    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    vip_users = (await db.execute(
        select(func.count()).select_from(User).where(User.membership_tier == "vip")
    )).scalar() or 0
    total_chars = (await db.execute(select(func.count()).select_from(Character))).scalar() or 0
    total_convos = (await db.execute(select(func.count()).select_from(Conversation))).scalar() or 0
    total_msgs = (await db.execute(select(func.count()).select_from(Message))).scalar() or 0

    today_msgs = (await db.execute(
        select(func.count()).select_from(Message).where(Message.created_at >= today_start)
    )).scalar() or 0

    today_users = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )).scalar() or 0

    active_today = (await db.execute(
        select(func.count(func.distinct(Conversation.user_id))).select_from(Message).join(
            Conversation, Message.conversation_id == Conversation.id
        ).where(Message.created_at >= today_start, Message.role == "user")
    )).scalar() or 0

    return {
        "total_users": total_users,
        "vip_users": vip_users,
        "total_characters": total_chars,
        "total_conversations": total_convos,
        "total_messages": total_msgs,
        "today_messages": today_msgs,
        "today_users": today_users,
        "active_users_today": active_today,
    }


@router.get("/stats/trend")
async def get_trend(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """近 7 天消息趋势"""
    today = datetime.now(timezone.utc).date()
    days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        cnt = (await db.execute(
            select(func.count()).select_from(Message).where(
                Message.created_at >= day_start, Message.created_at < day_end
            )
        )).scalar() or 0
        days.append({
            "date": d.isoformat(),
            "label": f"{d.month}/{d.day}",
            "count": cnt,
        })
    return {"days": days}


@router.get("/users")
async def list_users(
    search: str = Query("", max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """用户列表（搜索 + 分页）"""
    base = select(User)
    if search:
        pattern = f"%{search}%"
        base = base.where(
            User.email.ilike(pattern) | User.username.ilike(pattern)
        )
    base = base.order_by(User.created_at.desc())

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "membership_tier": u.membership_tier,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdateData,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """更新用户（禁用/启用、修改会员等级）"""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == _admin.id:
        raise HTTPException(status_code=403, detail="不能修改自己的状态或会员等级")

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.membership_tier is not None:
        if data.membership_tier not in ("free", "vip"):
            raise HTTPException(status_code=400, detail="无效的会员等级")
        user.membership_tier = data.membership_tier

    await db.flush()
    await db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "membership_tier": user.membership_tier,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
    }


class SystemSettingsData(BaseModel):
    painting_enabled: bool | None = None
    painting_api_key: str | None = None
    painting_base_url: str | None = None
    painting_model: str | None = None
    painting_size: str | None = None
    vision_enabled: bool | None = None
    vision_api_key: str | None = None
    vision_base_url: str | None = None
    vision_model: str | None = None


@router.get("/settings")
async def get_settings(_admin: User = Depends(get_admin_user)):
    """获取绘画/识图系统 API 配置"""
    return get_system_config()


@router.put("/settings")
async def update_settings(
    data: SystemSettingsData,
    _admin: User = Depends(get_admin_user),
):
    """更新绘画/识图系统 API 配置"""
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=400, detail="请至少提供一项设置")
    return update_system_config(payload)
