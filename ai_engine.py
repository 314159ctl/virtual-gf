# -*- coding: utf-8 -*-
"""AI 对话引擎 - 封装 OpenAI 兼容 API，支持流式输出和多模态"""

import json
import requests
from openai import OpenAI
from typing import Optional, Generator

class AIEngine:
    """AI 引擎，管理与大语言模型的交互"""

    def __init__(self, api_key: str = '', base_url: str = '', model: str = ''):
        self.api_key = api_key
        self.base_url = base_url or 'https://api.deepseek.com'
        self.model = model or 'deepseek-chat'
        self.max_token = 2000
        self.temperature = 0.9
        self._client = None

    @property
    def client(self) -> OpenAI:
        if not self._client:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def reset_client(self):
        """API 配置变更后重置客户端"""
        self._client = None

    def update_config(self, api_key: str = None, base_url: str = None,
                      model: str = None, max_token: int = None,
                      temperature: float = None):
        if api_key is not None:
            self.api_key = api_key
        if base_url is not None:
            self.base_url = base_url
        if model is not None:
            self.model = model
        if max_token is not None:
            self.max_token = max_token
        if temperature is not None:
            self.temperature = temperature
        self.reset_client()

    def build_messages(self, system_prompt: str, history: list,
                       user_message: str, image_data: str = None) -> list:
        """构建消息列表，支持文字和图片"""
        messages = [{"role": "system", "content": system_prompt}]

        for h in history:
            messages.append({"role": "user", "content": h.get("user", "")})
            messages.append({"role": "assistant", "content": h.get("ai", "")})

        if image_data:
            content = [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_message})

        return messages

    def chat_stream(self, system_prompt: str, history: list,
                    user_message: str, image_data: str = None) -> Generator[str, None, None]:
        """流式对话，逐字符生成回复"""
        messages = self.build_messages(system_prompt, history, user_message, image_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_token,
                temperature=self.temperature,
                stream=True
            )
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except Exception as e:
            yield f"\n\n[错误] {str(e)}"

    def chat_once(self, system_prompt: str, history: list,
                  user_message: str, image_data: str = None) -> str:
        """非流式对话，一次性获取完整回复"""
        messages = self.build_messages(system_prompt, history, user_message, image_data)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_token,
                temperature=self.temperature,
                stream=False
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[错误] {str(e)}"

    def generate_image(self, prompt: str, api_key: str = None,
                       base_url: str = None, model: str = None) -> Optional[str]:
        """调用绘画 API 生成图片，返回图片 URL"""
        key = api_key or self.api_key
        url = base_url or 'https://api.siliconflow.cn/v1/'
        mdl = model or 'black-forest-labs/FLUX.1-schnell'

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": mdl,
            "prompt": prompt,
            "n": 1,
            "size": "1920x1920"
        }
        try:
            resp = requests.post(f"{url.rstrip('/')}/images/generations",
                                 json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data['data'][0]['url']
            else:
                return None
        except Exception:
            return None
