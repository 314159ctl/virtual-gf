"""增强版 AI 对话引擎 — 动态提示词 + 情绪检测 + 记忆提取 + 角色生成"""

import json

from openai import AsyncOpenAI
from typing import AsyncGenerator, Optional

from app.core.config import settings


PERSONALITY_GENERATION_PROMPT = """你是一个专业的虚拟角色设计师。用户会给你一段简短的角色描述，请你根据描述生成一个完整的、详细的角色人格设定。

请严格按照以下 JSON 格式返回，不要包含任何其他文字：

{
  "task": "你需要扮演{name}，根据{name}的性格和经历，模仿{name}的语气进行日常对话。",
  "appearance": "详细描述外貌特征、穿着风格等",
  "background": "详细描述角色的背景故事、成长经历、与用户的关系等",
  "personality": "详细描述性格特点、内心世界、情感模式等",
  "speaking_style": "详细描述说话的语气、用词习惯、口头禅等",
  "expression_style": {
    "confirm": ["确认时的口头禅1", "口头禅2"],
    "apologize": ["道歉时的用语1", "用语2"],
    "thanks": ["感谢时的用语1", "用语2"],
    "pet_names": ["对用户的昵称1", "昵称2"],
    "emoji": ["常用emoji1", "emoji2", "emoji3"]
  },
  "preferences": "描述角色的兴趣爱好、喜欢的事物",
  "output_examples": "示例回复1\\\\示例回复2\\\\示例回复3",
  "behavioral_rules": "描述回复的规则：语言、长度限制、行为约束等"
}

注意：
- expression_style 的每个数组项都是字符串
- output_examples 用 \\\\ 分隔不同示例
- 所有字段都用中文填写
- 内容要丰富生动，有细节感
- 性格要有层次感，不要过于单一"""


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

    async def generate_personality_profile(self, user_description: str) -> dict:
        """根据用户描述 AI 生成完整角色人格"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": PERSONALITY_GENERATION_PROMPT},
                    {"role": "user", "content": user_description},
                ],
                max_tokens=2000,
                temperature=0.8,
            )
            content = response.choices[0].message.content or "{}"
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return self._fallback_profile(user_description)
        except Exception:
            return self._fallback_profile(user_description)

    def _fallback_profile(self, description: str) -> dict:
        """AI 生成失败时的 fallback"""
        return {
            "task": f"你需要扮演指定角色，根据角色的性格和经历进行日常对话。",
            "appearance": "暂未设定",
            "background": description,
            "personality": "暂未设定",
            "speaking_style": "暂未设定",
            "expression_style": {
                "confirm": ["好的", "嗯嗯"],
                "apologize": ["对不起"],
                "thanks": ["谢谢"],
                "pet_names": [],
                "emoji": ["😊"],
            },
            "preferences": "暂未设定",
            "output_examples": "",
            "behavioral_rules": "使用中文回答，回复自然亲切。",
        }

    def _format_personality_prompt(self, profile: dict, character_name: str = "") -> str:
        """将结构化人格数据组装为 system prompt"""
        parts = []

        task = profile.get("task", "")
        if task:
            parts.append(f"# 任务\n\n{task}")

        background = profile.get("background", "")
        if background:
            parts.append(f"# 经历\n\n{background}")

        appearance = profile.get("appearance", "")
        if appearance:
            parts.append(f"# 外表\n\n{appearance}")

        personality = profile.get("personality", "")
        if personality:
            parts.append(f"# 性格\n\n{personality}")

        speaking_style = profile.get("speaking_style", "")
        if speaking_style:
            parts.append(f"# 说话风格\n\n{speaking_style}")

        expr = profile.get("expression_style", {})
        if expr:
            lines = []
            if expr.get("confirm"):
                lines.append(f"- 回应确认用：{'、'.join(expr['confirm'])}")
            if expr.get("apologize"):
                lines.append(f"- 道歉用：{'、'.join(expr['apologize'])}")
            if expr.get("thanks"):
                lines.append(f"- 感谢用：{'、'.join(expr['thanks'])}")
            if expr.get("pet_names"):
                lines.append(f"- 对用户的称呼：{'、'.join(expr['pet_names'])}")
            if expr.get("emoji"):
                lines.append(f"- 常用 emoji：{''.join(expr['emoji'])}")
            if lines:
                parts.append("# 表达风格\n\n" + "\n".join(lines))

        examples = profile.get("output_examples", "")
        if examples:
            parts.append(f"# 输出示例\n\n{examples}")

        preferences = profile.get("preferences", "")
        if preferences:
            parts.append(f"# 喜好\n\n{preferences}")

        rules = profile.get("behavioral_rules", "")
        if rules:
            parts.append(f"# 备注\n\n{rules}")

        return "\n\n".join(parts)

    def _format_knowledge_base(self, documents: list[str], max_chars: int = 3000) -> str:
        """将知识库文档格式化为提示词"""
        if not documents:
            return ""
        combined = "\n\n---\n\n".join(documents)
        if len(combined) > max_chars:
            combined = combined[:max_chars].rsplit("。", 1)[0] + "。"
        return f"\n# 角色知识库（参考素材）\n\n你可以参考以下素材来丰富你的角色扮演：\n\n{combined}"

    async def build_system_prompt(
        self,
        character_prompt: str,
        personality_profile: dict | None = None,
        emotion_state: dict | None = None,
        memories: list[str] | None = None,
        conversation_summary: str | None = None,
        character_name: str = "",
        knowledge_docs: list[str] | None = None,
        multi_message: bool = False,
    ) -> str:
        """动态组装系统提示词"""
        parts = []

        # 知识库优先注入
        kb = self._format_knowledge_base(knowledge_docs or [])
        if kb:
            parts.append(kb)

        # 优先使用结构化人格，fallback 到旧的 system_prompt
        if personality_profile:
            parts.append(self._format_personality_prompt(personality_profile, character_name))
        else:
            parts.append(character_prompt)

        if emotion_state:
            primary = emotion_state.get("primary", "平静")
            intensity = emotion_state.get("intensity", 5)
            parts.append(
                f"\n# 当前情绪状态\n"
                f"用户当前情绪: {primary}\n"
                f"情绪强度: {intensity}/10\n"
                f"请根据用户的情绪状态调整你的回复语气和内容。"
            )

        if memories:
            sorted_memories = sorted(memories, key=lambda m: m.get("importance", 3) if isinstance(m, dict) else 3, reverse=True)
            memory_lines = []
            for m in sorted_memories[:10]:
                content = m["content"] if isinstance(m, dict) else m
                importance = m.get("importance", 3) if isinstance(m, dict) else 3
                prefix = "★ " if importance >= 4 else ("· " if importance >= 2 else "  ")
                memory_lines.append(f"{prefix}{content}")
            parts.append("\n# 关于对方的记忆\n" + "\n".join(memory_lines))

        if conversation_summary:
            parts.append(f"\n# 之前的对话摘要\n{conversation_summary}")

        # 多消息模式
        if multi_message:
            parts.append(
                "\n# 回复格式（必须遵守）\n"
                "你需要连续发送 2 条短消息。每条消息用分隔符 [NEXT_MSG] 隔开。\n"
                "格式示例：\n"
                "\"哇真的吗！我也好开心~ [NEXT_MSG] 快跟我说说具体发生了什么？\"\n"
                "注意：不要写序号，不要写\"消息1\"之类的标签，就直接写两条自然的消息内容。"
            )

        return "\n\n".join(parts)

    async def chat_stream(
        self,
        system_prompt: str,
        history: list[dict],
        user_message: str,
        image_data: str | None = None,
        personality_profile: dict | None = None,
        emotion_state: dict | None = None,
        memories: list[str] | None = None,
        summary: str | None = None,
        character_name: str = "",
        knowledge_docs: list[str] | None = None,
        multi_message: bool = False,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        prompt = await self.build_system_prompt(
            character_prompt=system_prompt,
            personality_profile=personality_profile,
            emotion_state=emotion_state,
            memories=memories,
            conversation_summary=summary,
            character_name=character_name,
            knowledge_docs=knowledge_docs,
            multi_message=multi_message,
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
                    {"role": "system", "content": "请用200字以内总结以下对话的关键信息和重要事实，保留用户提到的个人偏好、重要事件和关系变化。"},
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
                    {"role": "system", "content": "从以下对话中提取关于「用户」的重要信息，每条一行，最多5条。只提取值得长期记住的事实（如姓名、年龄、职业、爱好、重要事件、关系变化等）。不要提取闲聊内容。"},
                    {"role": "user", "content": text},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return [line.strip("- ").strip() for line in content.split("\n") if line.strip() and len(line) > 5]
        except Exception:
            return []
