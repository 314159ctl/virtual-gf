"""FastAPI 应用入口"""

import logging
import uuid
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.services.system_config import load_system_config

logger = logging.getLogger(__name__)

# 加载持久化的系统配置
load_system_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动/关闭时执行"""
    from app.db.session import engine, AsyncSessionLocal
    from app.db.base import Base
    from app.models.__init__ import (
        User, Character, Conversation, Message,
        LongTermMemory, CharacterDocument, Payment, UsageLog,
    )
    from app.core.security import hash_password

    try:
        # 自动建表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[OK] 数据库表已就绪")

        # 确保系统 guest 用户存在（避免外键约束失败）
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            guest_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
            existing = await db.execute(select(User).where(User.id == guest_id))
            if not existing.scalar_one_or_none():
                db.add(User(
                    id=guest_id,
                    email="system_guest@virtual-gf.local",
                    username="系统访客",
                    password_hash=hash_password("system-guest-no-login"),
                ))
                await db.commit()
                print("[OK] 系统 guest 用户已创建")
    except Exception as e:
        print(f"[WARN] 数据库未就绪: {e}")
        print("  请先启动 docker compose 或配置 DATABASE_URL")

    yield

    # 关闭时：释放资源
    from app.db.session import engine
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="虚拟女友 API",
        description="商用级 AI 聊天伴侣后端服务",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    origins = [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务暂时不可用，请稍后再试"},
        )

    # 注册 REST 路由
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    # 注册 WebSocket 路由
    from app.api.v1.ws import router as ws_router
    app.include_router(ws_router, prefix="/ws/chat")

    # 用户信息端点
    from app.api.v1.users import router as users_router
    app.include_router(users_router, prefix="/api/v1/users", tags=["用户"])

    # 静态文件（头像等）
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app


app = create_app()
