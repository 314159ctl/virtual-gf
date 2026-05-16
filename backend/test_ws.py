"""直接调用 WebSocket 测试完整消息流"""
import asyncio
import json
import websockets

async def main():
    # 先登录获取 token
    import requests
    login_resp = requests.post("http://localhost:8000/api/v1/auth/login", json={
        "email": "root@root.com",
        "password": "root123456"
    })
    token = login_resp.json()["access_token"]
    user_id = login_resp.json()["user"]["id"]
    print(f"Logged in as: {user_id}")

    # 获取小娜角色
    chars = requests.get("http://localhost:8000/api/v1/characters", headers={
        "Authorization": f"Bearer {token}"
    }).json()
    xiaona = None
    for c in chars:
        if "小娜" in c.get("name", ""):
            xiaona = c
            break
    if not xiaona:
        print("未找到小娜角色，用第一个")
        xiaona = chars[0] if chars else None
    if not xiaona:
        print("无角色可用")
        return
    print(f"Character: {xiaona['name']} ({xiaona['id']})")

    # 获取或创建会话
    convs = requests.get(f"http://localhost:8000/api/v1/conversations?character_id={xiaona['id']}", headers={
        "Authorization": f"Bearer {token}"
    }).json()
    if convs:
        conv_id = convs[0]["id"]
    else:
        conv_id = requests.post(f"http://localhost:8000/api/v1/conversations?character_id={xiaona['id']}", headers={
            "Authorization": f"Bearer {token}"
        }).json()["id"]
    print(f"Conversation: {conv_id}")

    # 连接 WebSocket
    ws_url = f"ws://localhost:8000/ws/chat/{conv_id}"
    async with websockets.connect(ws_url) as ws:
        # 发送 auth
        await ws.send(json.dumps({"type": "auth", "token": token}))
        auth_ok = False
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Auth response: {resp}")
            auth_ok = True
        except:
            pass

        if not auth_ok:
            print("Auth timeout, trying to send anyway")

        # 发送一个会触发 force_image 的消息
        msg = json.dumps({"type": "chat", "message": "拍张自拍给我看看"})
        print(f"\nSending: {msg}")
        await ws.send(msg)

        # 接收所有响应
        print("\n=== WebSocket 响应 ===")
        for i in range(20):
            try:
                data = await asyncio.wait_for(ws.recv(), timeout=30)
                parsed = json.loads(data)
                print(f"[{i}] type={parsed.get('type')}, keys={list(parsed.keys())}")
                if parsed.get('type') == 'done':
                    print(f"    full_reply={repr(parsed.get('full_reply', ''))[:120]}")
                elif parsed.get('type') == 'image':
                    print(f"    url={parsed.get('url', '')[:80]}")
                    print(f"    prompt={repr(parsed.get('prompt', ''))[:80]}")
                elif parsed.get('type') == 'chunk':
                    print(f"    content={repr(parsed.get('content', ''))[:80]}")
                elif parsed.get('type') == 'ai_error':
                    print(f"    code={parsed.get('code')} message={parsed.get('message')[:100]}")
            except asyncio.TimeoutError:
                print(f"[{i}] timeout - no more messages")
                break

asyncio.run(main())
