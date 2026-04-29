# -*- coding: utf-8 -*-
"""虚拟女友 - 全局配置文件（从环境变量读取敏感信息）"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def _env(key: str, default: str = '') -> str:
    return os.getenv(key, default)


# ============================================================
# API 配置
# ============================================================
API_KEY = _env('DEEPSEEK_API_KEY')
BASE_URL = _env('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
MODEL = _env('DEEPSEEK_MODEL', 'deepseek-chat')
MAX_TOKEN = int(_env('DEEPSEEK_MAX_TOKEN', '2000'))
TEMPERATURE = float(_env('DEEPSEEK_TEMPERATURE', '0.9'))

# 多模态配置
VISION_API_KEY = _env('DEEPSEEK_API_KEY')
VISION_BASE_URL = _env('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
VISION_MODEL = _env('DEEPSEEK_MODEL', 'deepseek-chat')

# 绘画 API 配置
PAINTING_ENABLED = _env('PAINTING_ENABLED', 'true').lower() == 'true'
PAINTING_API_KEY = _env('PAINTING_API_KEY')
PAINTING_BASE_URL = _env('PAINTING_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
PAINTING_MODEL = _env('PAINTING_MODEL', 'doubao-seedream-4-5-251128')

# ============================================================
# 数据库配置
# ============================================================
DATABASE_URL = _env('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/virtual_gf')
REDIS_URL = _env('REDIS_URL', 'redis://localhost:6379/0')

# ============================================================
# JWT 配置
# ============================================================
SECRET_KEY = _env('SECRET_KEY', 'dev-secret-change-in-production')
JWT_ALGORITHM = _env('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(_env('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
REFRESH_TOKEN_EXPIRE_DAYS = int(_env('REFRESH_TOKEN_EXPIRE_DAYS', '7'))

# ============================================================
# 对话配置
# ============================================================
MAX_CONTEXT_ROUNDS = 10
TYPING_SPEED = 0.03

# ============================================================
# 记忆配置
# ============================================================
ENABLE_MEMORY = True
MAX_MEMORY_ITEMS = 30

# ============================================================
# 语音配置
# ============================================================
ENABLE_TTS = True
TTS_VOICE = _env('TTS_VOICE', 'zh-CN-XiaoxiaoNeural')

# ============================================================
# 应用配置
# ============================================================
APP_PORT = int(_env('APP_PORT', '8000'))
DEBUG = _env('DEBUG', 'false').lower() == 'true'
CORS_ORIGINS = [o.strip() for o in _env('CORS_ORIGINS', 'http://localhost:5173').split(',')]

# 桌面窗口 (旧版兼容)
PORT = 5000
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 650
