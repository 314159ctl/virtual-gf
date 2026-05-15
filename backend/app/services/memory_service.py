"""记忆服务 — 自动总结 + AI 重要性评分 + 容量淘汰"""

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.memory import LongTermMemory
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.character import Character

logger = logging.getLogger(__name__)

# ── 记忆容量 ──
MAX_MEMORIES_PER_CHARACTER = 30
CONSOLIDATE_MIN_MESSAGES = 12


def _build_ai_client(api_key: str | None = None, api_base_url: str | None = None, api_model: str | None = None):
    from openai import AsyncOpenAI
    return AsyncOpenAI(
        api_key=api_key or settings.deepseek_api_key,
        base_url=api_base_url or settings.deepseek_base_url,
    ), (api_model or settings.deepseek_model)


async def _get_unlinked_messages(
    character_id: str, user_id: str, db: AsyncSession, limit: int = 100
) -> list[Message]:
    """获取未关联长期记忆的消息（最多跨3个会话）"""
    from uuid import UUID

    # 获取该角色用户的最近几个会话
    conv_stmt = (
        select(Conversation)
        .where(
            Conversation.character_id == UUID(character_id),
            Conversation.user_id == UUID(user_id),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(3)
    )
    conv_result = await db.execute(conv_stmt)
    conversations = conv_result.scalars().all()

    if not conversations:
        return []

    conv_ids = [c.id for c in conversations]

    # 获取这些会话中未关联长期记忆的消息
    msg_stmt = (
        select(Message)
        .where(
            Message.conversation_id.in_(conv_ids),
            Message.role.in_(["user", "assistant"]),
            ~Message.id.in_(
                select(LongTermMemory.source_message_id).where(
                    LongTermMemory.source_message_id.isnot(None)
                )
            ),
        )
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    msg_result = await db.execute(msg_stmt)
    return list(msg_result.scalars().all())


async def consolidate_memories(
    character_id: str, user_id: str, db: AsyncSession, api_key: str | None = None, api_base_url: str | None = None, api_model: str | None = None
) -> dict:
    """将短期记忆（未总结的消息）合并为长期记忆"""
    from uuid import UUID

    messages = await _get_unlinked_messages(character_id, user_id, db)
    if len(messages) < CONSOLIDATE_MIN_MESSAGES:
        return {"consolidated": False, "reason": f"消息不足（{len(messages)}/{CONSOLIDATE_MIN_MESSAGES}）"}

    # 获取角色信息
    char_result = await db.execute(
        select(Character).where(Character.id == UUID(character_id))
    )
    character = char_result.scalar_one_or_none()
    char_name = character.name if character else "角色"

    # 格式化消息日志
    log_lines = []
    for m in messages:
        speaker = char_name if m.role == "assistant" else "用户"
        log_lines.append(f"[{speaker}] {m.content}")
    full_log = "\n".join(log_lines)

    client, model = _build_ai_client(api_key, api_base_url, api_model)

    # Step 1: AI 以角色视角总结
    summary_prompt = (
        f"你正在扮演{char_name}。请以{char_name}的第一人称视角，"
        f"总结以下与用户的对话内容，提取重要的信息，用一段话描述"
        f"（只输出总结内容，不要加前缀标签）：\n\n{full_log}"
    )
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=400,
            temperature=0.5,
        )
        summary = resp.choices[0].message.content or ""
        summary = summary.strip()
    except Exception as e:
        logger.error(f"记忆总结失败: {e}")
        return {"consolidated": False, "reason": "AI 总结失败"}

    if not summary:
        return {"consolidated": False, "reason": "AI 返回空总结"}

    # Step 2: AI 重要性评分 (1-5)
    importance_prompt = (
        f"评估以下记忆的重要性（1=琐碎，5=非常重要），只回复数字1-5：\n\n{summary}"
    )
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": importance_prompt}],
            max_tokens=10,
            temperature=0.1,
        )
        importance_text = resp.choices[0].message.content or "3"
        match = re.search(r"[1-5]", importance_text)
        importance = int(match.group()) if match else 3
    except Exception:
        importance = 3

    # 保存长期记忆
    last_msg = messages[-1]
    memory = LongTermMemory(
        user_id=UUID(user_id),
        character_id=UUID(character_id),
        content=summary,
        importance=importance,
        source_message_id=last_msg.id,
    )
    db.add(memory)
    await db.flush()

    # 容量管理
    await manage_memory_capacity(character_id, user_id, db)

    logger.info(
        f"记忆已合并: character={char_name}, importance={importance}, "
        f"messages={len(messages)}, summary_len={len(summary)}"
    )
    return {
        "consolidated": True,
        "importance": importance,
        "summary": summary[:200],
        "message_count": len(messages),
    }


async def manage_memory_capacity(
    character_id: str, user_id: str, db: AsyncSession
):
    """记忆容量管理：按评分公式淘汰低分记忆"""
    from uuid import UUID

    stmt = (
        select(LongTermMemory)
        .where(
            LongTermMemory.character_id == UUID(character_id),
            LongTermMemory.user_id == UUID(user_id),
        )
        .order_by(LongTermMemory.created_at.desc())
    )
    result = await db.execute(stmt)
    memories = list(result.scalars().all())

    if len(memories) <= MAX_MEMORIES_PER_CHARACTER:
        return

    now = datetime.now(timezone.utc)

    scored = []
    for m in memories:
        age_hours = (now - m.created_at).total_seconds() / 3600
        score = 0.6 * m.importance - 0.4 * age_hours
        scored.append((score, m))

    scored.sort(key=lambda x: -x[0])
    keep_ids = {s[1].id for s in scored[:MAX_MEMORIES_PER_CHARACTER]}

    to_delete = [m for m in memories if m.id not in keep_ids]
    for m in to_delete:
        await db.delete(m)

    if to_delete:
        logger.info(f"记忆淘汰: 删除了 {len(to_delete)} 条低分记忆")
