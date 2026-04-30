"""WebSocket 流式聊天 — 接通记忆 + 情绪 + 摘要管线"""

import asyncio
import json
import re
import uuid
import random

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.character import Character
from app.models.character_document import CharacterDocument
from app.models.memory import LongTermMemory
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


@router.websocket("/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    user_id = None

    # 必须先接受 WebSocket 连接，才能收发消息
    await websocket.accept()

    try:
        # 等待认证消息
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=15)
        msg = json.loads(raw)

        if msg.get("type") != "auth":
            await websocket.send_json({"type": "error", "message": "请先发送认证消息"})
            await websocket.close(code=4000)
            return

        # 验证 JWT
        try:
            payload = decode_token(msg["token"])
            user_id = payload.get("sub")
            if not user_id:
                await websocket.send_json({"type": "error", "message": "无效的令牌"})
                await websocket.close(code=4001)
                return
        except Exception:
            await websocket.send_json({"type": "error", "message": "令牌验证失败"})
            await websocket.close(code=4001)
            return

        manager.active[f"{user_id}:{conversation_id}"] = websocket

        # 监听消息
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "chat":
                user_message = msg.get("message", "")
                image_data = msg.get("image")

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

                async for chunk in engine.chat_stream(
                    system_prompt=system_prompt,
                    history=history,
                    user_message=user_message,
                    image_data=image_data,
                    personality_profile=personality_profile,
                    emotion_state=conv.emotion_state,
                    memories=memories,
                    summary=conv.summary,
                    character_name=character_name,
                    knowledge_docs=knowledge_docs,
                    multi_message=multi,
                ):
                    full_reply += chunk
                    # 流式输出时隐藏分隔符
                    clean_chunk = chunk.replace("[NEXT_MSG]", "")
                    if clean_chunk:
                        await websocket.send_json({"type": "chunk", "content": clean_chunk})
                    await asyncio.sleep(0.01)

                # 等待情绪检测完成
                try:
                    await emotion_task
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

                # 发送 done 事件：第一条（已流式展示），后续逐条模拟流式
                for i, part in enumerate(msg_parts):
                    if i == 0:
                        await websocket.send_json({
                            "type": "done",
                            "full_reply": part,
                            "emotion_state": conv.emotion_state,
                        })
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
        await websocket.send_json({"type": "error", "message": "认证超时"})
        await websocket.close(code=4000)
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
