"""测试动作描写括号禁令"""
import asyncio, json, re, base64, requests, websockets

API = "http://localhost:8000/api/v1"
WS = "ws://localhost:8000/ws/chat"

resp = requests.get(f"{API}/auth/captcha")
cap = resp.json()
svg = base64.b64decode(cap["captcha_image"].split(",", 1)[1]).decode()
code = "".join(re.findall(r'<text[^>]*>([^<]+)</text>', svg))
resp = requests.post(f"{API}/auth/login", json={
    "email": "root@vgirl.com", "password": "root123456",
    "captcha_id": cap["captcha_id"], "captcha_code": code
})
token = resp.json()["access_token"]

resp = requests.get(f"{API}/characters", headers={"Authorization": f"Bearer {token}"})
char = resp.json()[0]
resp = requests.post(f"{API}/conversations", params={"character_id": char["id"]},
                     headers={"Authorization": f"Bearer {token}"})
conv_id = resp.json()["id"]
print(f"Char: {char['name']}  Conv: {conv_id[:12]}...")

async def test(msg):
    print(f"\n--- Send: {msg[:40]} ---")
    url = f"{WS}/{conv_id}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "auth", "token": token}))
        await asyncio.sleep(0.3)
        await ws.send(json.dumps({"type": "chat", "message": msg}))
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                ev = json.loads(raw)
                t = ev["type"]
                if t == "done":
                    reply = ev.get("full_reply", "")
                    has_paren = bool(re.search(r'[（(]', reply))
                    has_bracket = bool(re.search(r'【', reply))
                    has_star = bool(re.search(r'\*[^*]+\*', reply))
                    print(f"Reply: {reply}")
                    status = "FAIL" if (has_paren or has_bracket or has_star) else "PASS"
                    print(f"{status}: paren={has_paren} bracket={has_bracket} star={has_star}")
                    return status == "PASS"
                elif t == "image":
                    print(f"Image: {ev.get('url','')[:50]}")
                elif t in ("ai_error", "error"):
                    print(f"{t}: {ev.get('message','')[:60]}")
                    return False
            except asyncio.TimeoutError:
                print("Timeout"); return False

async def main():
    results = []
    results.append(await test("你今天想做什么呀"))
    results.append(await test("我真的很喜欢你宝贝"))
    results.append(await test("（害羞地笑了）你今天真好看"))
    # 发图也测一下
    results.append(await test("看看你"))
    print(f"\n{'='*40}")
    print(f"Results: {sum(results)}/{len(results)} passed")

asyncio.run(main())
