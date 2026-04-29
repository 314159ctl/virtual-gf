# -*- coding: utf-8 -*-
"""记忆系统 - 聊天记录持久化 + 短期/长期记忆管理"""

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'conversations.db')


class Memory:
    """记忆管理器，使用 SQLite 存储聊天记录"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or not self._local.conn:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                content TEXT NOT NULL,
                msg_type TEXT DEFAULT 'text',
                image_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_name TEXT NOT NULL,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_memories_char ON memories(character_name);
        ''')
        conn.commit()
        conn.close()

    def get_or_create_conversation(self, character_name: str) -> int:
        """获取或创建与某个角色的对话"""
        conn = self._get_conn()
        c = conn.execute(
            'SELECT id FROM conversations WHERE character_name = ? ORDER BY updated_at DESC LIMIT 1',
            (character_name,)
        )
        row = c.fetchone()
        if row:
            return row['id']
        cur = conn.execute(
            'INSERT INTO conversations (character_name) VALUES (?)',
            (character_name,)
        )
        conn.commit()
        return cur.lastrowid

    def add_message(self, conversation_id: int, role: str, content: str,
                    msg_type: str = 'text', image_data: str = None):
        """添加消息记录"""
        conn = self._get_conn()
        conn.execute(
            'INSERT INTO messages (conversation_id, role, content, msg_type, image_data) VALUES (?,?,?,?,?)',
            (conversation_id, role, content, msg_type, image_data)
        )
        conn.execute(
            'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (conversation_id,)
        )
        conn.commit()

    def get_history(self, conversation_id: int, limit: int = 20) -> list:
        """获取最近的历史消息"""
        conn = self._get_conn()
        rows = conn.execute(
            'SELECT role, content, msg_type, image_data, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC',
            (conversation_id,)
        ).fetchall()
        # 只保留最近 limit 条用于上下文
        if len(rows) > limit * 2:
            rows = rows[-(limit * 2):]
        result = []
        for r in rows:
            item = {"role": r["role"], "content": r["content"]}
            if r["msg_type"] == 'image' and r["image_data"]:
                item["image"] = True
            result.append(item)
        return result

    def get_chat_history(self, conversation_id: int, limit: int = 50) -> list:
        """获取展示用完整聊天历史"""
        conn = self._get_conn()
        rows = conn.execute(
            '''SELECT role, content, msg_type, image_data, created_at
               FROM messages WHERE conversation_id = ?
               ORDER BY id ASC LIMIT ?''',
            (conversation_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def format_for_context(self, history: list) -> list:
        """将历史记录格式化为 AI 上下文格式"""
        context = []
        for h in history:
            if h.get('role') == 'user' and h.get('image'):
                continue  # 图片消息在 AI 引擎中特殊处理
            if h['role'] in ('user', 'assistant'):
                role_map = {'user': 'user', 'assistant': 'assistant'}
                context.append({
                    "role": role_map[h['role']],
                    "content": h['content']
                })
        return context

    # ---- 长期记忆 ----
    def save_memory(self, character_name: str, content: str, importance: int = 3):
        """保存一条长期记忆"""
        conn = self._get_conn()
        conn.execute(
            'INSERT INTO memories (character_name, content, importance) VALUES (?,?,?)',
            (character_name, content, importance)
        )
        conn.commit()

    def get_memories(self, character_name: str, limit: int = 10) -> list:
        """获取角色相关的长期记忆"""
        conn = self._get_conn()
        rows = conn.execute(
            'SELECT content, importance, created_at FROM memories WHERE character_name = ? ORDER BY importance DESC, created_at DESC LIMIT ?',
            (character_name, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
