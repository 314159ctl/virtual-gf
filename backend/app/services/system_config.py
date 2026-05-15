"""系统级 API 配置持久化 — JSON 文件存储 + 内存同步"""

import json
from pathlib import Path

from app.core.config import settings

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "system_config.json"

DEFAULTS = {
    "painting_enabled": True,
    "painting_api_key": "",
    "painting_base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "painting_model": "doubao-seedream-4-5-251128",
    "painting_size": "2048x2048",
    "vision_enabled": True,
    "vision_api_key": "",
    "vision_base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "vision_model": "doubao-seed-2-0-pro",
}


def load_system_config():
    """启动时从 JSON 加载系统配置，覆盖 settings 默认值"""
    if not CONFIG_PATH.exists():
        try:
            _save(_current_state())
        except OSError:
            pass
        return

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {}

    for key in DEFAULTS:
        if key in data and hasattr(settings, key):
            setattr(settings, key, data[key])


def get_system_config() -> dict:
    """获取当前系统配置"""
    return _current_state()


def update_system_config(data: dict) -> dict:
    """更新系统配置（部分更新），返回完整新状态"""
    current = _current_state()
    for key in DEFAULTS:
        if key in data and hasattr(settings, key):
            val = data[key]
            if isinstance(DEFAULTS[key], bool) and not isinstance(val, bool):
                val = str(val).lower() in ("true", "1", "yes")
            current[key] = val
            setattr(settings, key, val)

    _save(current)
    return current


def _current_state() -> dict:
    return {key: getattr(settings, key, DEFAULTS[key]) for key in DEFAULTS}


def _save(data: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # 非关键路径，写入失败不影响运行
