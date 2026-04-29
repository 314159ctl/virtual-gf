"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动/关闭时执行"""
    # 启动时：验证数据库连接
    try:
        from app.db.session import engine
        async with engine.connect() as conn:
            await conn.execute(  # type: ignore
                __import__("sqlalchemy").text("SELECT 1")
            )
        print("[OK] 数据库连接正常")
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

    # 注册 REST 路由
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    # 注册 WebSocket 路由
    from app.api.v1.ws import router as ws_router
    app.include_router(ws_router, prefix="/ws/chat")

    # 用户信息端点
    from app.api.v1.users import router as users_router
    app.include_router(users_router, prefix="/api/v1/users", tags=["用户"])

    return app


app = create_app()
