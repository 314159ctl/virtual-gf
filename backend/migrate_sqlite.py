"""将旧 SQLite 数据迁移到 PostgreSQL"""
import asyncio
import sqlite3
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


SQLITE_PATH = r"D:\Projects\虚拟女友\data\conversations.db"


async def migrate():
    # 1. 读 SQLite
    db = sqlite3.connect(SQLITE_PATH)
    db.row_factory = sqlite3.Row
    c = db.cursor()

    conv_rows = [dict(r) for r in c.execute("SELECT * FROM conversations ORDER BY id")]
    msg_rows = [dict(r) for r in c.execute("SELECT * FROM messages ORDER BY id")]
    db.close()

    print(f"SQLite: {len(conv_rows)} conversations, {len(msg_rows)} messages")

    if not conv_rows:
        print("No data to migrate.")
        return

    # 2. 插入 PostgreSQL
    async with AsyncSessionLocal() as session:
        # 查找 guest 用户（取最新一个）
        from sqlalchemy import text
        user_result = await session.execute(text("SELECT id FROM users ORDER BY created_at DESC LIMIT 1"))
        user_row = user_result.fetchone()
        if not user_row:
            print("No users in DB. Login first as guest, then re-run.")
            return
        user_id = user_row[0]

        # 查找角色
        char_result = await session.execute(text("SELECT id FROM characters ORDER BY created_at LIMIT 1"))
        char_row = char_result.fetchone()
        if not char_row:
            print("No characters in DB.")
            return
        char_id = char_row[0]

        for old_conv in conv_rows:
            new_conv_id = uuid.uuid4()
            now = datetime.now(timezone.utc)
            session.add(Conversation(
                id=new_conv_id,
                user_id=user_id,
                character_id=char_id,
                title=old_conv.get("character_name") or "旧对话",
                message_count=len([m for m in msg_rows if m["conversation_id"] == old_conv["id"]]),
                created_at=now,
                updated_at=now,
            ))

            for old_msg in msg_rows:
                if old_msg["conversation_id"] != old_conv["id"]:
                    continue
                metadata = {}
                if old_msg.get("image_data"):
                    metadata["image_base64"] = old_msg["image_data"]
                session.add(Message(
                    id=uuid.uuid4(),
                    conversation_id=new_conv_id,
                    role=old_msg["role"],
                    content=old_msg["content"],
                    content_type="image" if old_msg.get("msg_type") == "image" else "text",
                    metadata_=metadata or None,
                    created_at=now,
                    updated_at=now,
                ))

        await session.commit()
        print(f"Done! Migrated {len(msg_rows)} messages into conversation {new_conv_id}")


if __name__ == "__main__":
    asyncio.run(migrate())
