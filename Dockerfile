# ============================================================
# 虚拟女友 - 后端 Dockerfile (FastAPI)
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY backend/pyproject.toml backend/
RUN pip install --no-cache-dir -e backend/.[dev] 2>/dev/null || \
    pip install --no-cache-dir fastapi[standard] uvicorn sqlalchemy[asyncio] asyncpg alembic \
    pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart \
    PyPDF2 python-docx openai httpx redis python-dotenv

# 应用代码
COPY . .

# 工作目录切换到 backend 以便 alembic 能找到 alembic.ini
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
