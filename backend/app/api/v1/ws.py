"""WebSocket 流式聊天 — 接通记忆 + 情绪 + 摘要管线"""

import asyncio
import json
import logging
import re
import uuid
import random
import requests
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.character import Character
from app.models.character_document import CharacterDocument
from app.models.memory import LongTermMemory
from app.core.config import settings
from app.core.security import decode_token, decrypt_api_key
from app.services.ai_engine import EnhancedAIEngine
from app.services.memory_service import consolidate_memories

router = APIRouter()

# 每 N 条用户消息触发一次记忆合并
MEMORY_CONSOLIDATE_INTERVAL = 20
# 每 N 条消息触发一次对话摘要
SUMMARY_INTERVAL = 30
# 匹配 [IMAGE:xxx] / [image:xxx] / [IMAGE：xxx]（大小写不敏感+中英文冒号）
IMAGE_RE = re.compile(r'\[[Ii][Mm][Aa][Gg][Ee][：:](.*?)\]')
# 匹配 AI 假装发图的文字标记：[发送了...] / [已发送...] / [图片N张] 等
FAKE_SEND_RE = re.compile(r'\[(?:发送了|已发送|图片)[^\]]*\]')
# 用户要求图片的关键词
IMAGE_REQUEST_KW = re.compile(
    r'发.*(?:照片|图片|自拍|图|张)|'
    r'(?:照片|图片|自拍|爆照).*发|'
    r'看看你|发一张|来一张|拍一张|拍个照|拍张'
)


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        await websocket.accept()
        key = f"{user_id}:{conversation_id}"
        self.active[key] = websocket

    def disconnect(self, user_id: str, conversation_id: str):
        key = f"{user_id}:{conversation_id}"
        self.active.pop(key, None)


manager = ConnectionManager()
engine = EnhancedAIEngine()


def _maybe_generate_image(raw_reply: str, force_image: bool, user_message: str,
                          history: list, character_name: str, personality_profile: dict | None,
                          conversation_id: str, api_key: str | None, api_base_url: str | None,
                          api_model: str | None) -> asyncio.Task | None:
    """从 AI 回复中提取 [IMAGE:xxx] 或触发兜底生图，返回 Task 或 None"""
    m = IMAGE_RE.search(raw_reply)
    if m:
        prompt = m.group(1).strip()
        if prompt:
            return asyncio.create_task(_generate_image(conversation_id, prompt))
        return None
    if not force_image:
        return None

    async def _fallback():
        intent = await engine.detect_image_intent(
            user_message=user_message, conversation_history=history,
            character_name=character_name, personality_profile=personality_profile,
            api_key=api_key, api_base_url=api_base_url, api_model=api_model,
            force_image=True,
        )
        prompt = intent.get("image_prompt") if intent.get("wants_image") else None
        return await _generate_image(conversation_id, prompt or user_message)

    return asyncio.create_task(_fallback())


async def _load_context(db, conversation_id: str, user_id: str):
    """加载对话上下文：角色、历史、记忆、情绪、摘要"""
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        return None

    # 加载角色
    char_result = await db.execute(
        select(Character).where(Character.id == conv.character_id)
    )
    char = char_result.scalar_one_or_none()

    # 加载历史消息（过滤 [图片] 占位符，防止 AI 模仿）
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history = []
    for m in reversed(msg_result.scalars().all()):
        content = m.content
        content = FAKE_SEND_RE.sub("", content).strip()
        if not content:
            content = "[图片消息]"
        history.append({"role": m.role, "content": content})

    # 加载长期记忆
    mem_result = await db.execute(
        select(LongTermMemory)
        .where(
            LongTermMemory.user_id == uuid.UUID(user_id),
            LongTermMemory.character_id == conv.character_id,
        )
        .order_by(LongTermMemory.importance.desc(), LongTermMemory.created_at.desc())
        .limit(10)
    )
    memories = [{"content": m.content, "importance": m.importance, "id": str(m.id)} for m in mem_result.scalars().all()]

    # 加载知识库文档
    doc_result = await db.execute(
        select(CharacterDocument)
        .where(CharacterDocument.character_id == conv.character_id)
        .order_by(CharacterDocument.created_at.desc())
        .limit(5)
    )
    knowledge_docs = [d.content_text for d in doc_result.scalars().all()]

    return {
        "conversation": conv,
        "character": char,
        "history": history,
        "memories": memories,
        "knowledge_docs": knowledge_docs,
        "emotion_state": conv.emotion_state,
        "summary": conv.summary,
    }


async def _detect_and_update_emotion(db, conv, user_message: str, api_key: str | None = None, api_base_url: str | None = None, api_model: str | None = None):
    """检测情绪并更新对话状态"""
    try:
        emotion = await engine.detect_emotion(user_message, api_key=api_key, api_base_url=api_base_url, api_model=api_model)
        conv.emotion_state = emotion
        await db.flush()
        return emotion
    except Exception:
        logger.exception("Emotion detection failed")
        return conv.emotion_state



async def _maybe_summarize(db, conv, conversation_id: str, api_key: str | None = None, api_base_url: str | None = None, api_model: str | None = None):
    """如果消息数量达到阈值，生成对话摘要"""
    if conv.message_count > 0 and conv.message_count % SUMMARY_INTERVAL == 0:
        try:
            msg_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == uuid.UUID(conversation_id))
                .order_by(Message.created_at.desc())
                .limit(30)
            )
            recent = [
                {"role": m.role, "content": m.content}
                for m in reversed(msg_result.scalars().all())
            ]
            summary = await engine.summarize_conversation(recent, api_key=api_key, api_base_url=api_base_url, api_model=api_model)
            if summary:
                conv.summary = summary
                await db.flush()
        except Exception:
            logger.exception("Conversation summarization failed")
            pass


def _split_messages(text: str) -> list[str]:
    """将 AI 回复拆成多条消息，用于模拟真人连续发消息"""
    # 优先使用 AI 主动标记的分隔符
    if "[NEXT_MSG]" in text:
        return [p.strip() for p in text.split("[NEXT_MSG]") if p.strip()]

    # 短回复不拆
    if len(text) <= 80:
        return [text]

    # 按句子边界拆分
    sentences = re.split(r'(?<=[。！？~…\.\!\?\n])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 1:
        return [text]

    # 2-4 句 → 拆成 2 条；更多 → 拆成 2-3 条
    if len(sentences) <= 4:
        mid = len(sentences) // 2
        return [''.join(sentences[:mid]), ''.join(sentences[mid:])]

    n = min(3, len(sentences) - 1)
    size = max(1, len(sentences) // n)
    result = []
    for i in range(0, len(sentences), size):
        group = sentences[i:i+size]
        if group:
            result.append(''.join(group))

    # 如果最后一条太短，合并到前一条
    if len(result) >= 2 and len(result[-1]) < 10:
        result[-2] += result[-1]
        result.pop()

    return result[:3]


async def _check_image_cooldown(db, conversation_id: uuid.UUID) -> bool:
    """检查最近5分钟内是否已生成过图片（临时取消限制）"""
    return True  # 取消冷却限制
    # cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    # result = await db.execute(
    #     select(func.count()).select_from(Message).where(
    #         Message.conversation_id == conversation_id,
    #         Message.content_type == "image",
    #         Message.created_at >= cutoff,
    #     )
    # )
    # return result.scalar() == 0


def _call_painting_api(prompt: str) -> dict | None:
    """同步调用绘画 API（在线程池中执行，避免阻塞事件循环）"""
    headers = {
        "Authorization": f"Bearer {settings.painting_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.painting_model,
        "prompt": prompt,
        "n": 1,
        "size": settings.painting_size,
    }
    try:
        resp = requests.post(
            f"{settings.painting_base_url.rstrip('/')}/images/generations",
            json=payload, headers=headers, timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"url": data["data"][0]["url"], "prompt": prompt}
        logger.error(f"Painting API error {resp.status_code}: {resp.text[:300]}")
    except Exception as e:
        logger.error(f"Painting API call failed: {e}")
    return None


async def _generate_image(conversation_id: str, image_prompt: str) -> dict | None:
    """异步调绘画 API 生图，保存到数据库，返回 {url, prompt}"""
    logger.info(f"[IMAGE GEN] Starting generation for conversation={conversation_id}, prompt={image_prompt[:80]}")
    async with AsyncSessionLocal() as db:
        can_generate = await _check_image_cooldown(db, uuid.UUID(conversation_id))
        if not can_generate:
            logger.info(f"[IMAGE GEN] Blocked by cooldown for conversation={conversation_id}")
            return None
        try:
            logger.info(f"[IMAGE GEN] Calling painting API...")
            result = await asyncio.to_thread(_call_painting_api, image_prompt)
            if not result:
                logger.warning(f"[IMAGE GEN] Painting API returned no result for prompt: {image_prompt[:100]}")
            if result:
                logger.info(f"[IMAGE GEN] Painting API success, URL={result.get('url', '')[:80]}")
                img_msg = Message(
                    conversation_id=uuid.UUID(conversation_id),
                    role="assistant",
                    content="[图片]",
                    content_type="image",
                    metadata_={"image_url": result["url"], "prompt": image_prompt},
                )
                db.add(img_msg)
                await db.flush()
                await db.commit()
                return result
        except Exception as e:
            logger.error(f"[IMAGE GEN] Exception: {e}", exc_info=True)
    return None


@router.websocket("/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    user_id = str(uuid.uuid4())
    user_api_key: str | None = None
    user_api_base_url: str | None = None
    user_api_model: str | None = None

    await websocket.accept()

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=15)
        msg = json.loads(raw)

        if msg.get("type") == "auth" and msg.get("token"):
            try:
                payload = decode_token(msg["token"])
                uid = payload.get("sub")
                if uid:
                    user_id = uid
                    async with AsyncSessionLocal() as db:
                        from app.models.user import User as UserModel
                        user_result = await db.execute(
                            select(UserModel).where(UserModel.id == uuid.UUID(user_id))
                        )
                        user_row = user_result.scalar_one_or_none()
                        if user_row:
                            if user_row.api_key_encrypted:
                                user_api_key = decrypt_api_key(user_row.api_key_encrypted)
                            user_api_base_url = user_row.api_base_url
                            user_api_model = user_row.api_model
            except Exception:
                logger.exception("Failed to load user API key")

        manager.active[f"{user_id}:{conversation_id}"] = websocket

        # 如果首条消息是 auth，等下一轮；否则立即处理为 chat
        first_message = msg if msg.get("type") != "auth" else None

        # 监听消息
        while True:
            if first_message:
                msg = first_message
                first_message = None
            else:
                raw = await websocket.receive_text()
                msg = json.loads(raw)

            if msg.get("type") == "chat":
                user_message = msg.get("message", "")
                image_data = msg.get("image")
                original_text = user_message  # 保存原始文本，用于 force_image 判断
                logger.info(f"[CHAT] Received message: user_message={user_message[:80] if user_message else '(empty)'}, has_image={bool(image_data)}")

                # 有图片时先调视觉模型识图
                display_content = user_message or "[图片]"  # 用户消息气泡显示的内容
                fallback_image = None
                if image_data and settings.vision_enabled:
                    try:
                        description = await engine.describe_image(image_data)
                        user_message = f"[用户发了一张照片：{description}] 用户说：{user_message or '看看这张图'}"
                    except Exception:
                        logger.exception("Vision description failed, falling back to raw image")
                        user_message = user_message or "看看这张图"
                        fallback_image = image_data

                async with AsyncSessionLocal() as db:
                    # 记录用户消息（只保存用户看到的文本，不保存 AI 识图上下文）
                    message = Message(
                        conversation_id=uuid.UUID(conversation_id),
                        role="user",
                        content=display_content,
                        content_type="image" if image_data else "text",
                        metadata_={"image_base64": image_data} if image_data else None,
                    )
                    db.add(message)
                    await db.flush()

                    # 加载完整上下文
                    ctx = await _load_context(db, conversation_id, user_id)
                    if not ctx:
                        await websocket.send_json({"type": "error", "message": "对话不存在"})
                        continue

                    conv = ctx["conversation"]
                    char = ctx["character"]
                    history = ctx["history"]
                    memories = ctx["memories"]
                    knowledge_docs = ctx["knowledge_docs"]

                    # 更新消息计数
                    conv.message_count = (conv.message_count or 0) + 1

                    # 情绪检测（异步，不阻塞回复）
                    emotion_task = asyncio.create_task(
                        _detect_and_update_emotion(db, conv, user_message, user_api_key, user_api_base_url, user_api_model)
                    )

                    # 提取角色信息
                    system_prompt = char.system_prompt if char else "你是一个温柔友好的AI助手。请用中文回复。"
                    personality_profile = char.personality_profile if char else None
                    character_name = char.name if char else ""

                    await db.commit()

                # 流式调用 AI（在 session 外执行，避免长时间占用连接）
                multi = random.random() < 0.35

                raw_full_reply = ""
                # 用原始文本判断，排除识图上下文干扰
                force_image = bool(IMAGE_REQUEST_KW.search(original_text))

                # force_image：直接并行调绘图 API，不依赖 AI 的 [IMAGE:xxx] 标记
                image_task = None
                if force_image:
                    async def _force_image_generate():
                        intent = await engine.detect_image_intent(
                            user_message=original_text, conversation_history=history,
                            character_name=character_name, personality_profile=personality_profile,
                            api_key=user_api_key, api_base_url=user_api_base_url, api_model=user_api_model,
                            force_image=True,
                        )
                        prompt = intent.get("image_prompt") if intent.get("wants_image") else original_text
                        return await _generate_image(conversation_id, prompt)
                    image_task = asyncio.create_task(_force_image_generate())
                    logger.info(f"[CHAT] force_image detected, started image generation task")

                async for chunk in engine.chat_stream(
                    system_prompt=system_prompt,
                    history=history,
                    user_message=user_message,
                    image_data=fallback_image,
                    personality_profile=personality_profile,
                    emotion_state=conv.emotion_state,
                    memories=memories,
                    summary=conv.summary,
                    character_name=character_name,
                    knowledge_docs=knowledge_docs,
                    multi_message=multi,
                    api_key=user_api_key,
                    api_base_url=user_api_base_url,
                    api_model=user_api_model,
                    force_image=force_image,
                ):
                    raw_full_reply += chunk

                logger.info(f"[CHAT] Stream ended, reply_len={len(raw_full_reply)}")

                # 检测 AI 错误标记
                err_match = re.search(r'\[AI_ERROR:(\w+)\](.*)', raw_full_reply)
                if err_match:
                    err_code = err_match.group(1)
                    err_message = err_match.group(2).strip()
                    await websocket.send_text(json.dumps({
                        "type": "ai_error",
                        "code": err_code,
                        "message": err_message,
                    }))
                    continue

                # 提取 [IMAGE:xxx] 自发标记（仅非 force_image 时，force_image 已并行生图）
                if not force_image:
                    image_task = _maybe_generate_image(
                        raw_full_reply, False, user_message, history,
                        character_name, personality_profile, conversation_id,
                        user_api_key, user_api_base_url, user_api_model,
                    )

                # 清理文本（移除 [IMAGE:xxx] 和 [发送了...] 伪装标记）
                full_reply = IMAGE_RE.sub("", raw_full_reply)
                full_reply = FAKE_SEND_RE.sub("", full_reply).strip()
                # 移除动作描写括号：（脸红）（叹气）*笑* 【开心】等
                full_reply = re.sub(r'[（(][^）)]*?[）)]', '', full_reply)
                full_reply = re.sub(r'\*[^*]+?\*', '', full_reply)
                full_reply = re.sub(r'【[^】]+?】', '', full_reply)

                tasks = [emotion_task]
                if image_task:
                    tasks.append(image_task)
                results = await asyncio.gather(*tasks, return_exceptions=True)

                image_result = None
                if image_task:
                    img_res = results[1] if len(results) > 1 else None
                    if img_res and not isinstance(img_res, Exception):
                        image_result = img_res

                # 多消息模式下拆分回复
                msg_parts = _split_messages(full_reply) if multi else [full_reply]
                if not msg_parts:
                    msg_parts = [full_reply]

                # 保存所有消息 + 后台任务
                async with AsyncSessionLocal() as db:
                    for part in msg_parts:
                        ai_msg = Message(
                            conversation_id=uuid.UUID(conversation_id),
                            role="assistant",
                            content=part,
                            content_type="text",
                        )
                        db.add(ai_msg)

                    conv_result = await db.execute(
                        select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
                    )
                    conv = conv_result.scalar_one_or_none()
                    if conv:
                        conv.message_count = (conv.message_count or 0) + 1

                        if conv.message_count % SUMMARY_INTERVAL == 0:
                            asyncio.create_task(_maybe_summarize(db, conv, conversation_id, user_api_key, user_api_base_url, user_api_model))

                    if conv and conv.message_count % MEMORY_CONSOLIDATE_INTERVAL == 0:
                        asyncio.create_task(
                            consolidate_memories(str(conv.character_id), user_id, db, user_api_key, user_api_base_url, user_api_model)
                        )

                    await db.commit()

                # 过滤掉 [图片] 占位符和空字符串，避免空文字气泡
                text_parts = [p for p in msg_parts if p.strip() and p.strip() != "[图片]"]
                logger.info(f"[SEND] image={bool(image_result)} text_parts={len(text_parts)} full_reply={repr(full_reply[:100]) if full_reply else 'EMPTY'}")

                # 发送图片事件（独立气泡，先于文字）
                if image_result:
                    await websocket.send_json({
                        "type": "image",
                        "url": image_result["url"],
                        "prompt": "",
                    })

                # 没有实际文字内容，也没有图片 → 发送错误提示
                if image_result is None and not text_parts:
                    await websocket.send_json({
                        "type": "ai_error",
                        "code": "image_failed",
                        "message": "呜…图片生成失败了，请稍后再试吧 (′；ω；`)",
                    })
                elif text_parts:
                    # 发送文字气泡（只发送有实际内容的）
                    for i, part in enumerate(text_parts):
                        if i == 0:
                            done_msg = {
                                "type": "done",
                                "full_reply": part,
                                "emotion_state": conv.emotion_state,
                            }
                            await websocket.send_json(done_msg)
                        else:
                            delay = 1.8 + random.uniform(0, 2.5)
                            await asyncio.sleep(delay)
                            for j in range(0, len(part), 2):
                                await websocket.send_json({
                                    "type": "chunk",
                                    "content": part[j:j+2]
                                })
                                await asyncio.sleep(0.025)
                            await websocket.send_json({
                                "type": "done",
                                "full_reply": part,
                                "emotion_state": conv.emotion_state,
                            })

    except asyncio.TimeoutError:
        pass  # 超时静默关闭
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("WebSocket chat error")
        if user_id:
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass
    finally:
        if user_id:
            manager.disconnect(user_id, conversation_id)
