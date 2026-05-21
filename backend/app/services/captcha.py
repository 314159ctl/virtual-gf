"""SVG 图形验证码 — Redis 存储，服务重启不丢失"""

import base64
import random
import uuid

import redis.asyncio as aioredis

from app.core.config import settings

TTL = 300  # 5 分钟


def _key(captcha_id: str) -> str:
    return f"captcha:{captcha_id}"


async def generate_captcha() -> dict:
    """生成 SVG 验证码，返回 {captcha_id, captcha_image}"""
    # 4 位随机字母数字（排除易混淆字符 0O1Il）
    chars = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
    code = "".join(random.choices(chars, k=4))

    svg = _render_svg(code)

    captcha_id = uuid.uuid4().hex[:12]
    r = aioredis.from_url(settings.redis_url)
    await r.setex(_key(captcha_id), TTL, code)
    await r.aclose()

    svg_b64 = base64.b64encode(svg.encode()).decode()
    return {
        "captcha_id": captcha_id,
        "captcha_image": f"data:image/svg+xml;base64,{svg_b64}",
    }


async def verify_captcha(captcha_id: str, captcha_code: str) -> bool:
    """校验验证码，无论对错都删除（一次性使用）"""
    if not captcha_id or not captcha_code:
        return False

    r = aioredis.from_url(settings.redis_url)
    key = _key(captcha_id)
    stored = await r.getdel(key)
    await r.aclose()

    if not stored:
        return False
    return captcha_code.strip().upper() == stored.decode().upper()


def _render_svg(code: str) -> str:
    """生成带干扰的 SVG"""
    w, h = 120, 44
    colors = ["#e87d8a", "#c44d6a", "#d4687c", "#b84560", "#f598a5", "#9b3d54"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#fef5f7" rx="6"/>',
    ]

    # 干扰线（3 条）
    for _ in range(3):
        x1, y1 = random.randint(0, w // 3), random.randint(4, h - 4)
        x2, y2 = random.randint(w * 2 // 3, w), random.randint(4, h - 4)
        stroke = random.choice(colors)
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="1" opacity="0.3"/>'
        )

    # 噪点（15 个）
    for _ in range(15):
        cx, cy = random.randint(4, w - 4), random.randint(4, h - 4)
        fill = random.choice(colors)
        r = random.uniform(0.5, 1.5)
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" opacity="0.3"/>')

    # 字符（旋转 + 偏移）
    char_w = w // len(code)
    for i, ch in enumerate(code):
        x = char_w * i + random.randint(6, char_w - 20)
        y = random.randint(28, 36)
        angle = random.randint(-30, 30)
        font_size = random.randint(22, 26)
        fill = random.choice(colors)
        parts.append(
            f'<text x="{x}" y="{y}" font-size="{font_size}" fill="{fill}" '
            f'font-family="Arial,Helvetica,sans-serif" font-weight="bold" '
            f'transform="rotate({angle},{x},{y})">{ch}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)
