"""FastAPI 依赖注入"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 中解析当前用户。未登录抛出 401。"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌类型")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已过期或无效")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """可选登录——未登录返回 None，不报错。"""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id:
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            return result.scalar_one_or_none()
    except JWTError:
        pass
    return None


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求管理员权限。"""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user


def check_quota(feature: str):
    """工厂函数：检查用户配额。用法: Depends(check_quota("chat"))"""

    async def checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        from datetime import datetime, timezone

        from app.core.config import settings
        from app.models.payment import UsageLog

        if current_user.membership_tier == "vip":
            return current_user

        today = datetime.now(timezone.utc).date()
        # 简化计数：查今天的 usage_logs 条数
        from sqlalchemy import func

        if feature == "chat":
            limit = (
                settings.premium_daily_messages
                if current_user.membership_tier == "premium"
                else settings.free_daily_messages
            )
        elif feature == "image":
            limit = (
                settings.premium_daily_images
                if current_user.membership_tier == "premium"
                else settings.free_daily_images
            )
        else:
            limit = 10

        count_result = await db.execute(
            select(func.count()).select_from(UsageLog).where(
                UsageLog.user_id == current_user.id,
                UsageLog.endpoint == feature,
                func.date(UsageLog.created_at) == today,
            )
        )
        count = count_result.scalar() or 0

        if count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"今日{feature}配额已用完 ({limit}次/天)。请升级会员获取更多。",
            )

        return current_user

    return checker
