# -*- coding: utf-8 -*-
"""语音模块 - TTS 语音合成"""

import os
import asyncio
import threading
import base64
from typing import Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'audio_cache')


class VoiceEngine:
    """语音引擎，负责 TTS 合成"""

    def __init__(self, voice: str = 'zh-CN-XiaoxiaoNeural'):
        self.voice = voice
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

    async def _synthesize_async(self, text: str, output_path: str) -> bool:
        """异步执行 TTS 合成"""
        if not EDGE_TTS_AVAILABLE:
            return False
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return os.path.exists(output_path)
        except Exception:
            return False

    def synthesize(self, text: str) -> Optional[str]:
        """合成语音，返回 base64 编码的音频数据"""
        if not EDGE_TTS_AVAILABLE:
            return None

        # 清理文本：去除特殊标记和过长的内容
        clean_text = text.replace('*', '').replace('#', '').replace('~', '')
        if len(clean_text) > 500:
            clean_text = clean_text[:500]

        import hashlib
        hash_str = hashlib.md5(clean_text.encode()).hexdigest()
        output_path = os.path.join(AUDIO_CACHE_DIR, f'{hash_str}.mp3')

        # 检查缓存
        if os.path.exists(output_path):
            with open(output_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()

        # 合成语音
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(
                self._synthesize_async(clean_text, output_path)
            )
            loop.close()

            if success:
                with open(output_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode()
        except Exception:
            return None

        return None

    def set_voice(self, voice_name: str):
        """设置 TTS 语音"""
        self.voice = voice_name
