"""用户信息 API"""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.security import encrypt_api_key, decrypt_api_key, verify_password, hash_password
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
from app.schemas.user import UserOut, UserUpdate


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

router = APIRouter()

AVATAR_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5MB


def _user_to_out(user: User) -> dict:
    """将 ORM 对象转为 UserOut 字典，补充 computed 字段"""
    return {
        **{c.name: getattr(user, c.name) for c in user.__table__.columns},
        "has_api_key": bool(user.api_key_encrypted),
    }


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return _user_to_out(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新当前用户信息"""
    if data.username is not None:
        current_user.username = data.username
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    if data.api_key is not None:
        current_user.api_key_encrypted = encrypt_api_key(data.api_key)
    if data.api_base_url is not None:
        current_user.api_base_url = data.api_base_url
    if data.api_model is not None:
        current_user.api_model = data.api_model
    await db.flush()
    await db.refresh(current_user)
    return _user_to_out(current_user)


@router.post("/me/avatar", response_model=UserOut)
async def upload_user_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传用户头像"""

    if file.content_type not in AVATAR_ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅支持 JPEG/PNG/WebP/GIF")

    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小超过上限 (5MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "png"
    filename = f"user_{current_user.id}.{ext}"
    filepath = f"static/avatars/{filename}"

    with open(filepath, "wb") as f:
        f.write(content)

    current_user.avatar_url = f"/{filepath}"
    await db.flush()
    await db.refresh(current_user)
    return _user_to_out(current_user)


@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码"""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")
    current_user.password_hash = hash_password(data.new_password)
    current_user.must_change_password = False
    await db.flush()
    return {"message": "密码修改成功"}


@router.post("/me/test-api")
async def test_api_connection(current_user: User = Depends(get_current_user)):
    """测试 API 连接：用用户配置的 Key/URL/Model 发一条极短消息验证连通性"""
    api_key = decrypt_api_key(current_user.api_key_encrypted) if current_user.api_key_encrypted else None
    base_url = current_user.api_base_url or settings.deepseek_base_url
    model = current_user.api_model or settings.deepseek_model

    if not api_key:
        raise HTTPException(status_code=400, detail="请先设置 API Key")

    from openai import AsyncOpenAI, AuthenticationError, RateLimitError, APIStatusError

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            temperature=0,
            timeout=15,
        )
        return {"status": "ok", "model": model, "base_url": base_url}
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="API Key 无效，请检查后重试")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="API 请求过于频繁或余额不足，请稍后重试")
    except APIStatusError as e:
        if e.status_code == 402:
            raise HTTPException(status_code=402, detail="API 余额不足，请充值后重试")
        raise HTTPException(status_code=502, detail=f"AI 服务返回错误（{e.status_code}），请稍后重试")
    except Exception as e:
        logger.exception("API key validation failed")
        raise HTTPException(status_code=502, detail=f"连接失败: {str(e)[:120]}")
