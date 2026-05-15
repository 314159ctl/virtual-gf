"""测试所有 force_image 场景"""
import asyncio, json, re, base64, sys, os, requests

API = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws/chat"

def login():
    resp = requests.get(f"{API}/auth/captcha")
    cap = resp.json()
    svg = base64.b64decode(cap["captcha_image"].split(",", 1)[1]).decode()
    code = "".join(re.findall(r'<text[^>]*>([^<]+)</text>', svg))
    resp = requests.post(f"{API}/auth/login", json={
        "email": "root@vgirl.com", "password": "root123456",
        "captcha_id": cap["captcha_id"], "captcha_code": code
    })
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}"); sys.exit(1)
    return resp.json()["access_token"]

def get_conv(token):
    resp = requests.get(f"{API}/characters", headers={"Authorization": f"Bearer {token}"})
    char = resp.json()[0]
    resp = requests.get(f"{API}/conversations", params={"character_id": char["id"]},
                        headers={"Authorization": f"Bearer {token}"})
    convs = resp.json()
    if convs:
        return convs[0]["id"]
    resp = requests.post(f"{API}/conversations", params={"character_id": char["id"]},
                         headers={"Authorization": f"Bearer {token}"})
    return resp.json()["id"]

async def test(name, token, conv_id, text, expect_image, expect_text, desc=""):
    print(f"\n{'='*50}")
    print(f"[{name}] {desc}")
    print(f"  发送: {text[:60] if text else '(空/图片)'}")
    print(f"  期望: {'图' if expect_image else '无图'} + {'文字' if expect_text else '无文字'}")
    print(f"{'='*50}")

    url = f"{WS_BASE}/{conv_id}"
    events = []

    try:
        import websockets
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"type": "auth", "token": token}))
            await asyncio.sleep(0.3)
            await ws.send(json.dumps({"type": "chat", "message": text}))

            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=45)
                    ev = json.loads(raw)
                    events.append(ev)
                    t = ev["type"]
                    if t == "chunk":
                        pass  # 不打印每个chunk
                    elif t == "done":
                        print(f"  done: '{ev.get('full_reply','')[:50]}'")
                        try:
                            raw2 = await asyncio.wait_for(ws.recv(), timeout=3)
                            ev2 = json.loads(raw2)
                            events.append(ev2)
                            if ev2["type"] == "image":
                                print(f"  image: {ev2.get('url','')[:50]}")
                        except asyncio.TimeoutError:
                            pass
                        break
                    elif t == "image":
                        print(f"  image: {ev.get('url','')[:50]}")
                    elif t in ("ai_error", "error"):
                        print(f"  {t}: {ev.get('message','')[:60]}")
                        break
                except asyncio.TimeoutError:
                    print(f"  超时")
                    break
    except Exception as e:
        print(f"  连接错误: {e}")

    images = [e for e in events if e["type"] == "image"]
    dones = [e for e in events if e["type"] == "done"]
    has_img = len(images) > 0
    has_txt = len(dones) > 0

    # 检查空气泡
    empty = sum(1 for e in dones if not e.get("full_reply","").strip() or e.get("full_reply","").strip() == "[图片]")

    ok = True
    if expect_image and not has_img:
        print(f"  FAIL: 期望有图片但没收到"); ok = False
    if not expect_image and has_img:
        print(f"  FAIL: 期望无图片但收到了"); ok = False
    if expect_text and not has_txt:
        print(f"  FAIL: 期望有文字但没收到"); ok = False
    if empty > 0:
        print(f"  FAIL: {empty} 个空气泡"); ok = False

    status = "PASS" if ok else "FAIL"
    print(f"  => {status} (图:{has_img} 文:{has_txt} 空:{empty})")
    return ok

async def main():
    print("=" * 50)
    print("force_image 全部场景测试")
    print("=" * 50)

    token = login()
    conv_id = get_conv(token)
    print(f"Token: {token[:15]}... Conv: {conv_id[:12]}...")

    results = []

    # 场景1: 纯文字请求图片 → 应该生图
    results.append(await test("纯文字请求图片", token, conv_id,
        "发一张可爱猫咪的照片给我看看",
        expect_image=True, expect_text=False,
        desc="纯文字'发一张xxx照片' → force_image=True → 只生图"))

    # 场景2: 纯文字聊天 → 应该只回复文字
    results.append(await test("纯文字聊天", token, conv_id,
        "你好呀，今天天气真好",
        expect_image=False, expect_text=True,
        desc="普通聊天 → force_image=False → 只回文字"))

    # 场景3: 纯文字发一张/来一张 → force_image=True
    results.append(await test("发一张", token, conv_id,
        "来一张日落的照片",
        expect_image=True, expect_text=False,
        desc="'来一张xxx照片' → force_image=True"))

    # 场景4: 模拟发图(用文字让AI以为在描述图) + 无文字
    # 注意：无法真正测发图，但可以测原始文本为空的场景
    # 用 /stats 确认逻辑正确
    results.append(await test("空消息", token, conv_id,
        "",
        expect_image=False, expect_text=True,
        desc="空消息 → force_image=False → 正常回复"))

    # 场景5: 看看你 → force_image=True
    results.append(await test("看看你", token, conv_id,
        "看看你长什么样子",
        expect_image=True, expect_text=False,
        desc="'看看你' → force_image=True"))

    # 场景6: 拍张照 → force_image=True
    results.append(await test("拍张照", token, conv_id,
        "拍张自拍给我",
        expect_image=True, expect_text=False,
        desc="'拍张' → force_image=True"))

    # 场景7: 文字含"图"但非请求 → force_image依正则
    results.append(await test("非请求含图字", token, conv_id,
        "我昨天画了一幅图，你觉得怎么样",
        expect_image=False, expect_text=True,
        desc="聊天提到图但非请求 → force_image=False"))

    print(f"\n{'='*50}")
    print(f"结果汇总")
    print(f"{'='*50}")
    passed = sum(results)
    total = len(results)
    names = ["纯文请求图","纯文聊天","发一张","空消息","看看你","拍张照","非请求"]
    for i, (r, n) in enumerate(zip(results, names)):
        print(f"  {'PASS' if r else 'FAIL'}  {n}")
    print(f"\n通过: {passed}/{total}")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
