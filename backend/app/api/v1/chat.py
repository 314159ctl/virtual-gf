"""聊天 API — REST 备用 + 内嵌 AI 引擎"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, check_quota
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user=Depends(get_current_user),
    _quota=Depends(check_quota("chat")),
):
    """非流式聊天（备用）。流式聊天请使用 WebSocket /ws/chat/{conversation_id}"""
    # 临时：使用旧版 AI 引擎
    import sys
    sys.path.insert(0, "../..")
    from ai_engine import AIEngine
    from config import API_KEY, BASE_URL, MODEL

    engine = AIEngine(API_KEY, BASE_URL, MODEL)
    reply = engine.chat_once(
        system_prompt="你是一个友好的AI助手。",
        history=[],
        user_message=data.message,
        image_data=data.image_data,
    )
    return ChatResponse(reply=reply)
