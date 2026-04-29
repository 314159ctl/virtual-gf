"""AI 绘画 API"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.dependencies import get_current_user, check_quota
from app.schemas.chat import GenerateImageRequest
from app.models.user import User

router = APIRouter()


@router.post("/generate")
async def generate_image(
    data: GenerateImageRequest,
    current_user: User = Depends(get_current_user),
    _quota=Depends(check_quota("image")),
):
    """生成 AI 图片"""
    if not settings.painting_enabled:
        raise HTTPException(status_code=400, detail="绘画功能未启用")

    import sys
    sys.path.insert(0, "../..")
    from ai_engine import AIEngine
    from config import PAINTING_API_KEY, PAINTING_BASE_URL, PAINTING_MODEL

    engine = AIEngine()
    url = engine.generate_image(
        data.prompt,
        api_key=PAINTING_API_KEY,
        base_url=PAINTING_BASE_URL,
        model=PAINTING_MODEL,
    )

    if url:
        return {"url": url, "prompt": data.prompt}
    else:
        raise HTTPException(status_code=500, detail="图片生成失败，请稍后重试")
