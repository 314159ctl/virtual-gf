"""WebSocket 流式聊天"""

import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        await websocket.accept()
        key = f"{user_id}:{conversation_id}"
        self.active[key] = websocket

    def disconnect(self, user_id: str, conversation_id: str):
        key = f"{user_id}:{conversation_id}"
        self.active.pop(key, None)

    async def send_json(self, user_id: str, conversation_id: str, data: dict):
        key = f"{user_id}:{conversation_id}"
        ws = self.active.get(key)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(user_id, conversation_id)


manager = ConnectionManager()


@router.websocket("/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket 流式聊天端点

    客户端发送:
      {"type": "auth", "token": "<jwt_access_token>"}
      {"type": "chat", "message": "...", "image": "<base64|null>"}

    服务端推送:
      {"type": "chunk", "content": "..."}
      {"type": "done", "full_reply": "...", "audio": "<base64|null>"}
      {"type": "error", "message": "..."}
    """
    user_id = None

    try:
        # 等待认证消息
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=15)
        msg = json.loads(raw)

        if msg.get("type") != "auth":
            await websocket.send_json({"type": "error", "message": "请先发送认证消息"})
            return

        # 验证 JWT
        from app.core.security import decode_token
        try:
            payload = decode_token(msg["token"])
            user_id = payload.get("sub")
            if not user_id:
                await websocket.send_json({"type": "error", "message": "无效的令牌"})
                return
        except Exception:
            await websocket.send_json({"type": "error", "message": "令牌验证失败"})
            return

        await manager.connect(websocket, user_id, conversation_id)

        # 监听消息
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "chat":
                user_message = msg.get("message", "")
                image_data = msg.get("image")

                # 记录用户消息
                try:
                    from app.db.session import AsyncSessionLocal
                    from app.models.message import Message

                    async with AsyncSessionLocal() as db:
                        message = Message(
                            conversation_id=uuid.UUID(conversation_id),
                            role="user",
                            content=user_message or "[图片]",
                            content_type="image" if image_data else "text",
                            metadata_={"image_base64": image_data} if image_data else None,
                        )
                        db.add(message)
                        await db.commit()
                except Exception:
                    pass  # 不阻塞聊天流程

                # 流式调用 AI
                import sys
                sys.path.insert(0, "../..")
                from ai_engine import AIEngine
                from config import API_KEY, BASE_URL, MODEL

                engine = AIEngine(API_KEY, BASE_URL, MODEL)
                full_reply = ""

                # 流式发送 chunks
                for chunk in engine.chat_stream(
                    system_prompt="你是一个温柔友好的AI助手。请用中文回复。",
                    history=[],
                    user_message=user_message,
                    image_data=image_data,
                ):
                    full_reply += chunk
                    await websocket.send_json({"type": "chunk", "content": chunk})
                    await asyncio.sleep(0.01)

                # 保存 AI 回复
                try:
                    async with AsyncSessionLocal() as db:
                        ai_msg = Message(
                            conversation_id=uuid.UUID(conversation_id),
                            role="assistant",
                            content=full_reply,
                            content_type="text",
                        )
                        db.add(ai_msg)
                        await db.commit()
                except Exception:
                    pass

                # 发送完成信号
                await websocket.send_json({
                    "type": "done",
                    "full_reply": full_reply,
                })

    except asyncio.TimeoutError:
        await websocket.send_json({"type": "error", "message": "认证超时"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if user_id:
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass
    finally:
        if user_id:
            manager.disconnect(user_id, conversation_id)
