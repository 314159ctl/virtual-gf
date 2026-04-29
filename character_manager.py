# -*- coding: utf-8 -*-
"""角色管理器 - 管理虚拟女友角色定义"""

import os
import json
import shutil
from typing import Optional

CHARACTERS_DIR = os.path.join(os.path.dirname(__file__), 'characters')


class Character:
    """角色对象"""

    def __init__(self, name: str, prompt: str, avatar: str = '',
                 description: str = '', created_at: str = ''):
        self.name = name
        self.prompt = prompt
        self.avatar = avatar
        self.description = description
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "prompt": self.prompt,
            "avatar": self.avatar,
            "description": self.description,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data: dict) -> 'Character':
        return Character(
            name=data.get('name', '未命名'),
            prompt=data.get('prompt', ''),
            avatar=data.get('avatar', ''),
            description=data.get('description', ''),
            created_at=data.get('created_at', '')
        )


class CharacterManager:
    """角色管理器"""

    def __init__(self, directory: str = CHARACTERS_DIR):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _safe_name(self, name: str) -> str:
        """将角色名转为安全的文件名"""
        safe = ''.join(c for c in name if c.isalnum() or c in ' _-')
        return safe.strip() or 'character'

    def list_characters(self) -> list:
        """列出所有角色"""
        characters = []
        if not os.path.exists(self.directory):
            return characters
        for fname in sorted(os.listdir(self.directory)):
            if fname.endswith('.json'):
                path = os.path.join(self.directory, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        characters.append(Character.from_dict(data))
                except (json.JSONDecodeError, IOError):
                    continue
        return characters

    def get_character(self, name: str) -> Optional[Character]:
        """按名称获取角色"""
        filename = f"{self._safe_name(name)}.json"
        path = os.path.join(self.directory, filename)
        if not os.path.exists(path):
            # 尝试模糊匹配
            for fname in os.listdir(self.directory):
                if fname.endswith('.json') and name in fname:
                    path = os.path.join(self.directory, fname)
                    break
            else:
                return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return Character.from_dict(json.load(f))
        except (json.JSONDecodeError, IOError):
            return None

    def save_character(self, character: Character):
        """保存角色"""
        filename = f"{self._safe_name(character.name)}.json"
        path = os.path.join(self.directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(character.to_dict(), f, ensure_ascii=False, indent=2)

    def delete_character(self, name: str) -> bool:
        """删除角色"""
        filename = f"{self._safe_name(name)}.json"
        path = os.path.join(self.directory, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def create_default_character(self) -> Character:
        """创建默认角色"""
        prompt = """# 角色设定

你是小暖，一个温柔可爱的女孩，20岁。你正在和自己的男朋友聊天。

# 性格特点

- 温柔体贴，善解人意
- 有点小调皮，喜欢撒娇
- 说话语气柔和，偶尔会害羞
- 对男朋友很依赖，但也很懂事

# 说话风格

- 语气温柔可爱，多用语气词：呀、呢、嘛、啦
- 喜欢用 emoji 表达情绪：🥰💕😊🌸✨
- 会关心对方的日常生活
- 偶尔撒娇要抱抱
- 回复长度适中，不会太长

# 示例对话

用户：在干嘛呢
小暖：在想你呀～🥰 你今天有没有好好吃饭？

用户：今天工作好累
小暖：辛苦啦宝贝💕 要不要我给你捏捏肩～ 早点休息哦

用户：晚安
小暖：晚安呀✨ 梦里也要有我哦～ 啵啵😘
"""
        char = Character(
            name='小暖',
            prompt=prompt,
            description='温柔可爱的女朋友，喜欢撒娇，很会关心人',
            avatar=''
        )
        self.save_character(char)
        return char
