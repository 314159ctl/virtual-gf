"""WebSocket 流式聊天 — 接通记忆 + 情绪 + 摘要管线"""

import asyncio
import json
import re
import uuid
import random
import requests
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.character import Character
from app.models.character_document import CharacterDocument
from app.models.memory import LongTermMemory
from app.core.config import settings
from app.core.security import decode_token
from app.services.ai_engine import EnhancedAIEngine

router = APIRouter()

# 每 N 条用户消息触发一次记忆提取
MEMORY_EXTRACT_INTERVAL = 10
# 每 N 条消息触发一次对话摘要
SUMMARY_INTERVAL = 30


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

    # 加载历史消息
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(msg_result.scalars().all())
    ]

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


async def _detect_and_update_emotion(db, conv, user_message: str):
    """检测情绪并更新对话状态"""
    try:
        emotion = await engine.detect_emotion(user_message)
        conv.emotion_state = emotion
        await db.flush()
        return emotion
    except Exception:
        return conv.emotion_state


async def _extract_and_save_memories(db, user_id: str, character_id, history: list[dict]):
    """从对话中提取记忆并保存到数据库"""
    try:
        extracted = await engine.extract_memories(history)
        for content in extracted:
            memory = LongTermMemory(
                user_id=uuid.UUID(user_id),
                character_id=character_id,
                content=content,
                importance=3,
            )
            db.add(memory)
        await db.flush()
    except Exception:
        pass


async def _maybe_summarize(db, conv, conversation_id: str):
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
            summary = await engine.summarize_conversation(recent)
            if summary:
                conv.summary = summary
                await db.flush()
        except Exception:
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
    """检查最近5分钟内是否已生成过图片"""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = await db.execute(
        select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id,
            Message.content_type == "image",
            Message.created_at >= cutoff,
        )
    )
    return result.scalar() == 0


@router.websocket("/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    user_id = str(uuid.uuid4())  # 默认使用随机 guest ID
    token_authenticated = False

    await websocket.accept()

    try:
        # 首条消息：可选 JWT 认证
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=15)
        msg = json.loads(raw)

        if msg.get("type") == "auth" and msg.get("token"):
            try:
                payload = decode_token(msg["token"])
                uid = payload.get("sub")
                if uid:
                    user_id = uid
                    token_authenticated = True
            except Exception:
                pass  # token 无效，继续用 guest ID

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

                # 有图片时先调视觉模型识图
                if image_data and settings.vision_enabled:
                    try:
                        description = await engine.describe_image(image_data)
                        user_message = f"[用户发了一张照片：{description}] 用户说：{user_message or '看看这张图'}"
                    except Exception:
                        user_message = user_message or "[图片]"

                async with AsyncSessionLocal() as db:
                    # 记录用户消息
                    message = Message(
                        conversation_id=uuid.UUID(conversation_id),
                        role="user",
                        content=user_message or "[图片]",
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
                        _detect_and_update_emotion(db, conv, user_message)
                    )

                    # 提取角色信息
                    system_prompt = char.system_prompt if char else "你是一个温柔友好的AI助手。请用中文回复。"
                    personality_profile = char.personality_profile if char else None
                    character_name = char.name if char else ""

                    await db.commit()

                # 流式调用 AI（在 session 外执行，避免长时间占用连接）
                full_reply = ""

                # 随机多消息模式（约 35% 概率，让回复更生动）
                multi = random.random() < 0.35

                IMAGE_TAG = "[IMAGE:"
                SPLIT_TAGS = ["[IMAGE:", "[NEXT_MSG]"]  # 需要跨 chunk 过滤的标记

                stream_buffer = ""
                async for chunk in engine.chat_stream(
                    system_prompt=system_prompt,
                    history=history,
                    user_message=user_message,
                    image_data=None,  # 图片已转为文字描述，不再直接传图
                    personality_profile=personality_profile,
                    emotion_state=conv.emotion_state,
                    memories=memories,
                    summary=conv.summary,
                    character_name=character_name,
                    knowledge_docs=knowledge_docs,
                    multi_message=multi,
                ):
                    full_reply += chunk
                    stream_buffer += chunk.replace("[NEXT_MSG]", "")

                    # 循环处理 buffer：移除完整的 [IMAGE:...] 标记，扣住部分前缀
                    while True:
                        m = re.search(r'\[IMAGE:.*?\]', stream_buffer)
                        if m:
                            if m.start() > 0:
                                await websocket.send_json({"type": "chunk", "content": stream_buffer[:m.start()]})
                            stream_buffer = stream_buffer[m.end():]
                            continue  # 继续看剩余 buffer 还有没有更多标记

                        # 没有完整标记 — 检查末尾是否可能是 [IMAGE: 前缀
                        held = False
                        for i in range(1, len(IMAGE_TAG) + 1):
                            if stream_buffer.endswith(IMAGE_TAG[:i]):
                                # 扣住前缀部分
                                if len(stream_buffer) > i:
                                    await websocket.send_json({"type": "chunk", "content": stream_buffer[:-i]})
                                    stream_buffer = stream_buffer[-i:]
                                held = True
                                break

                        if not held:
                            if stream_buffer:
                                await websocket.send_json({"type": "chunk", "content": stream_buffer})
                                stream_buffer = ""
                        break  # 当前轮处理完毕

                    await asyncio.sleep(0.01)

                # 发送缓冲区残留（可能只剩下无意义的 [IMAGE: 前缀残片）
                if stream_buffer:
                    # 最后做一次清理
                    stream_buffer = re.sub(r'\[IMAGE:.*?\]', '', stream_buffer)
                    if stream_buffer.strip():
                        await websocket.send_json({"type": "chunk", "content": stream_buffer})

                # 等待情绪检测完成
                try:
                    await emotion_task
                except Exception:
                    pass

                # 检查是否有 [IMAGE:...] 标记，触发生图
                image_result = None
                image_prompt = ""
                image_matches = re.findall(r'\[IMAGE:(.*?)\]', full_reply)
                if image_matches and settings.painting_enabled:
                    image_prompt = image_matches[0].strip()
                    # 从回复中移除标记，保持文本干净
                    clean_reply = re.sub(r'\[IMAGE:.*?\]', '', full_reply).strip()
                    full_reply = clean_reply or full_reply

                    async with AsyncSessionLocal() as img_db:
                        if await _check_image_cooldown(img_db, uuid.UUID(conversation_id)):
                            try:
                                headers = {
                                    "Authorization": f"Bearer {settings.painting_api_key}",
                                    "Content-Type": "application/json",
                                }
                                payload = {
                                    "model": settings.painting_model,
                                    "prompt": image_prompt,
                                    "n": 1,
                                    "size": "1920x1920",
                                }
                                resp = requests.post(
                                    f"{settings.painting_base_url.rstrip('/')}/images/generations",
                                    json=payload, headers=headers, timeout=60,
                                )
                                if resp.status_code == 200:
                                    img_url = resp.json()['data'][0]['url']
                                    # 保存图片消息
                                    img_msg = Message(
                                        conversation_id=uuid.UUID(conversation_id),
                                        role="assistant",
                                        content=image_prompt,
                                        content_type="image",
                                        metadata_={"image_url": img_url, "prompt": image_prompt},
                                    )
                                    img_db.add(img_msg)
                                    await img_db.flush()
                                    await img_db.commit()
                                    image_result = {"url": img_url, "prompt": image_prompt}
                            except Exception:
                                pass

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
                            asyncio.create_task(_maybe_summarize(db, conv, conversation_id))

                    if conv and conv.message_count % MEMORY_EXTRACT_INTERVAL == 0:
                        char_id = conv.character_id
                        msg_result = await db.execute(
                            select(Message)
                            .where(Message.conversation_id == uuid.UUID(conversation_id))
                            .order_by(Message.created_at.desc())
                            .limit(20)
                        )
                        recent_history = [
                            {"role": m.role, "content": m.content}
                            for m in reversed(msg_result.scalars().all())
                        ]
                        asyncio.create_task(
                            _extract_and_save_memories(db, user_id, char_id, recent_history)
                        )

                    await db.commit()

                # 发送 done 事件：第一条（已流式展示 + 可能的图片），后续逐条模拟流式
                for i, part in enumerate(msg_parts):
                    if i == 0:
                        done_msg = {
                            "type": "done",
                            "full_reply": part,
                            "emotion_state": conv.emotion_state,
                        }
                        if image_result:
                            done_msg["image_url"] = image_result["url"]
                            done_msg["image_prompt"] = image_result["prompt"]
                        await websocket.send_json(done_msg)
                    else:
                        # 模拟真人连续发消息的自然间隔
                        delay = 1.8 + random.uniform(0, 2.5)
                        await asyncio.sleep(delay)
                        # 逐字流式输出
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
        if user_id:
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass
    finally:
        if user_id:
            manager.disconnect(user_id, conversation_id)
