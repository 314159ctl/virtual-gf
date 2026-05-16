"""完整流程测试：登录 → WebSocket → 发消息 → 收回复"""
import asyncio
import json
import re
import requests
import websockets

async def main():
    base = "http://localhost:8000"

    # Guest 登录（无需验证码）
    resp = requests.post(f"{base}/api/v1/auth/guest")
    data = resp.json()
    token = data["access_token"]
    # 从 JWT 中解码 user_id
    import base64
    payload = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "===").decode())
    user_id = payload["sub"]
    print(f"Guest login OK: user_id={user_id}")

    # 3. 获取角色
    chars_resp = requests.get(f"{base}/api/v1/characters", headers={"Authorization": f"Bearer {token}"})
    chars = chars_resp.json()
    if not chars:
        print("No characters available")
        return
    char = chars[0]
    print(f"Using character: {char['name']} ({char['id']})")

    # 4. 获取或创建会话
    convs = requests.get(
        f"{base}/api/v1/conversations?character_id={char['id']}",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    if convs:
        conv_id = convs[0]["id"]
    else:
        conv_id = requests.post(
            f"{base}/api/v1/conversations?character_id={char['id']}",
            headers={"Authorization": f"Bearer {token}"}
        ).json()["id"]
    print(f"Conversation: {conv_id}")

    # 5. WebSocket 测试
    ws_url = f"ws://localhost:8000/ws/chat/{conv_id}"
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"type": "auth", "token": token}))

        # 等待 auth 响应（可能没有）
        print("Auth sent, sending chat message...")
        await asyncio.sleep(0.5)

        # 发送会触发 force_image 的消息
        msg = json.dumps({"type": "chat", "message": "拍张自拍给我看看", "image": None})
        print(f"\n>>> Sending: {msg}")
        await ws.send(msg)

        # 接收所有响应
        print("\n=== Responses ===")
        for i in range(20):
            try:
                data = await asyncio.wait_for(ws.recv(), timeout=60)
                parsed = json.loads(data)
                t = parsed.get("type")
                if t == "chunk":
                    print(f"[{i}] chunk: {parsed.get('content', '')[:60]}", flush=True)
                elif t == "done":
                    fr = parsed.get("full_reply", "")
                    print(f"[{i}] DONE: len={len(fr)} full_reply={repr(fr[:200])}", flush=True)
                elif t == "image":
                    print(f"[{i}] IMAGE: url={parsed.get('url', '')[:80]} prompt={repr(parsed.get('prompt', '')[:80])}", flush=True)
                elif t == "ai_error":
                    print(f"[{i}] AI_ERROR: code={parsed.get('code')} msg={parsed.get('message', '')[:100]}", flush=True)
                elif t == "error":
                    print(f"[{i}] ERROR: {parsed.get('message', '')[:100]}", flush=True)
                else:
                    print(f"[{i}] {t}: keys={list(parsed.keys())}", flush=True)
            except asyncio.TimeoutError:
                print(f"[{i}] timeout", flush=True)
                break

    print("\nDone.")

asyncio.run(main())
