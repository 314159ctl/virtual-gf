"""测试完整管道：AI 生成 → 清理 → 拆分 → 发送"""
import asyncio
import re
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ai_engine import EnhancedAIEngine

IMAGE_RE = re.compile(r'\[[Ii][Mm][Aa][Gg][Ee][：:](.*?)\]')
FAKE_SEND_RE = re.compile(r'\[(?:发送了|已发送|图片)[^\]]*\]')
IMAGE_REQUEST_KW = re.compile(
    r'发.*(?:照片|图片|自拍|图|张)|'
    r'(?:照片|图片|自拍|爆照).*发|'
    r'看看你|发一张|来一张|拍一张|拍个照|拍张'
)


def _split_messages(text: str) -> list[str]:
    if "[NEXT_MSG]" in text:
        return [p.strip() for p in text.split("[NEXT_MSG]") if p.strip()]
    if len(text) <= 80:
        return [text]
    sentences = re.split(r'(?<=[。！？~…\.\!\?\n])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) <= 1:
        return [text]
    if len(sentences) <= 4:
        mid = len(sentences) // 2
        return [''.join(sentences[:mid]), ''.join(sentences[mid:])]
    n = min(3, len(sentences) - 1)
    size = max(1, len(sentences) // n)
    result = []
    for i in range(0, len(sentences), size):
        group = sentences[i:i+size]
        if group:
            result.append(''.join(group))
    if len(result) >= 2 and len(result[-1]) < 10:
        result[-2] += result[-1]
        result.pop()
    return result[:3]


def clean_text(raw_full_reply: str) -> str:
    full_reply = IMAGE_RE.sub("", raw_full_reply)
    full_reply = FAKE_SEND_RE.sub("", full_reply).strip()
    full_reply = re.sub(r'[（(][^）)]*?[）)]', '', full_reply)
    full_reply = re.sub(r'\*[^*]+?\*', '', full_reply)
    full_reply = re.sub(r'【[^】]+?】', '', full_reply)
    return full_reply


async def main():
    engine = EnhancedAIEngine()

    # 模拟一个请求发图的场景
    history = [
        {"role": "user", "content": "拍张自拍给我看看"},
    ]

    system_prompt = """你是小娜，一个可爱的女朋友。请用温柔可爱的语气回复。
回复尽量简短30字以内。不要用括号描述动作和心理，只输出语言。"""

    user_message = "拍张自拍给我看看"
    force_image = bool(IMAGE_REQUEST_KW.search(user_message))
    print(f"force_image: {force_image}")
    print(f"IMAGE_REQUEST_KW pattern: {IMAGE_REQUEST_KW.pattern}")

    raw_full_reply = ""
    async for chunk in engine.chat_stream(
        system_prompt=system_prompt,
        history=history,
        user_message=user_message,
        image_data=None,
        personality_profile=None,
        emotion_state=None,
        memories=None,
        summary=None,
        character_name="小娜",
        knowledge_docs=None,
        multi_message=False,
        force_image=force_image,
    ):
        raw_full_reply += chunk

    print(f"\n=== 原始 AI 回复 ({len(raw_full_reply)} chars) ===")
    print(repr(raw_full_reply))

    # 检查是否有 IMAGE 标记
    m = IMAGE_RE.search(raw_full_reply)
    print(f"\nIMAGE_RE match: {m.group(0) if m else 'None'}")

    # 清理
    full_reply = clean_text(raw_full_reply)
    print(f"\n=== 清理后 ({len(full_reply)} chars) ===")
    print(repr(full_reply))

    # 拆分
    msg_parts = _split_messages(full_reply)
    if not msg_parts:
        msg_parts = [full_reply]
    print(f"\n=== 拆分后 ({len(msg_parts)} 条) ===")
    for i, p in enumerate(msg_parts):
        print(f"  [{i}]: {repr(p)}")

    # 过滤
    text_parts = [p for p in msg_parts if p.strip() and p.strip() != "[图片]"]
    print(f"\n=== 过滤后 text_parts ({len(text_parts)} 条) ===")
    for i, p in enumerate(text_parts):
        print(f"  [{i}]: {repr(p)}")

    print(f"\n=== 最终结果 ===")
    print(f"有文字: {bool(text_parts)}")
    print(f"有图片: {bool(m)}")


if __name__ == "__main__":
    asyncio.run(main())
