"""认证 API — 注册 / 登录 / 刷新令牌 / 验证码"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserOut, UserRegister

logger = logging.getLogger(__name__)
from app.services.captcha import generate_captcha, verify_captcha

router = APIRouter()


@router.get("/captcha")
async def get_captcha():
    """获取图形验证码"""
    return await generate_captcha()


@router.post("/guest", response_model=TokenResponse)
async def guest_login(db: AsyncSession = Depends(get_db)):
    """免注册 guest 登录，始终使用固定系统访客用户"""
    from uuid import UUID
    GUEST_ID = UUID("00000000-0000-0000-0000-000000000000")

    result = await db.execute(select(User).where(User.id == GUEST_ID))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=GUEST_ID,
            email="system_guest@virtual-gf.local",
            username="访客",
            password_hash=hash_password("system-guest-no-login"),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    access_token = create_access_token(str(user.id), "free")
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """注册新用户，并自动复制默认角色，直接返回 token"""
    # 验证码校验
    if not await verify_captcha(data.captcha_id or "", data.captcha_code or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

    # 检查邮箱是否已存在
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册")

    # 检查用户名
    existing_name = await db.execute(select(User).where(User.username == data.username))
    if existing_name.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该用户名已被使用")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # 为新用户复制默认角色
    from app.api.v1.characters import _copy_defaults_for_user
    await _copy_defaults_for_user(db, user.id)

    access_token = create_access_token(str(user.id), user.membership_tier)
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """登录，返回 JWT 令牌对"""
    # 验证码校验
    if not await verify_captcha(data.captcha_id or "", data.captcha_code or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    access_token = create_access_token(str(user.id), user.membership_tier)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    """用 refresh token 换取新的 access token"""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌类型")
        user_id = payload.get("sub")
    except Exception:
        logger.exception("Refresh token decode failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效或已过期")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    new_access = create_access_token(str(user.id), user.membership_tier)
    new_refresh = create_refresh_token(str(user.id))

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
