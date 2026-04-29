"""增强版 AI 对话引擎 — 动态提示词 + Token 管理 + 对话摘要"""

from openai import AsyncOpenAI
from typing import AsyncGenerator, Optional

from app.core.config import settings


class EnhancedAIEngine:
    """增强版 AI 引擎"""

    def __init__(self):
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self._client:
            self._client = AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )
        return self._client

    async def build_system_prompt(
        self,
        character_prompt: str,
        emotion_state: dict | None = None,
        memories: list[str] | None = None,
        conversation_summary: str | None = None,
    ) -> str:
        """动态组装系统提示词"""
        parts = [character_prompt]

        if emotion_state:
            parts.append(
                f"\n# 当前情绪状态\n"
                f"情绪: {emotion_state.get('primary', '平静')}\n"
                f"强度: {emotion_state.get('intensity', 5)}/10"
            )

        if memories:
            parts.append(
                "\n# 关于对方的记忆\n" +
                "\n".join(f"- {m}" for m in memories[:10])
            )

        if conversation_summary:
            parts.append(f"\n# 之前的对话摘要\n{conversation_summary}")

        return "\n\n".join(parts)

    async def chat_stream(
        self,
        system_prompt: str,
        history: list[dict],
        user_message: str,
        image_data: str | None = None,
        emotion_state: dict | None = None,
        memories: list[str] | None = None,
        summary: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        prompt = await self.build_system_prompt(
            system_prompt, emotion_state, memories, summary
        )

        messages = [{"role": "system", "content": prompt}]

        for h in history[-20:]:
            if h.get("role") == "user":
                messages.append({"role": "user", "content": h.get("content", "")})
            elif h.get("role") == "assistant":
                messages.append({"role": "assistant", "content": h.get("content", "")})

        if image_data:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                ]
            })
        else:
            messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                max_tokens=settings.deepseek_max_token,
                temperature=settings.deepseek_temperature,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
        except Exception as e:
            yield f"\n\n[错误] {str(e)}"

    async def summarize_conversation(self, messages: list[dict]) -> str:
        """用 AI 总结对话历史，用于压缩上下文"""
        if not messages:
            return ""

        text = "\n".join(
            f"{'用户' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:200]}"
            for m in messages[-30:]
        )

        try:
            response = await self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": "请用200字以内总结以下对话的关键信息和重要事实。"},
                    {"role": "user", "content": text},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception:
            return ""

    async def detect_emotion(self, text: str) -> dict:
        """检测用户消息的情感"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": "分析以下消息的情感。返回 JSON: {\"primary\": \"开心/难过/生气/焦虑/平静/期待/其他\", \"intensity\": 1-10, \"valence\": -1到1的值}"},
                    {"role": "user", "content": text},
                ],
                max_tokens=100,
                temperature=0.1,
            )
            import json
            content = response.choices[0].message.content or "{}"
            content = content.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(content)
        except Exception:
            return {"primary": "平静", "intensity": 5, "valence": 0.0}

    async def extract_memories(self, messages: list[dict]) -> list[str]:
        """从对话中自动提取关键记忆"""
        if len(messages) < 6:
            return []

        text = "\n".join(
            f"{'用户' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:150]}"
            for m in messages[-20:]
        )

        try:
            response = await self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": "从以下对话中提取关于「用户」的重要信息，每条一行，最多5条。只提取值得长期记住的事实。"},
                    {"role": "user", "content": text},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return [line.strip("- ").strip() for line in content.split("\n") if line.strip() and len(line) > 5]
        except Exception:
            return []
