import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# Step 1: Read current Dockerfile
print("=== 当前 Dockerfile ===")
stdin, stdout, stderr = client.exec_command(f'cat {project_dir}/Dockerfile')
original = stdout.read().decode()
print(original)

# Step 2: Modify Dockerfile to add Chinese pip mirror and apt mirror
# Replace the RUN pip install line to use Aliyun mirrors
new_dockerfile = '''# ============================================================
# 虚拟女友 - 后端 Dockerfile (FastAPI)
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# 使用阿里云 Debian 镜像源加速
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖 (使用阿里云 PyPI 镜像)
COPY backend/pyproject.toml backend/
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -e backend/.[dev] 2>/dev/null || \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com fastapi[standard] uvicorn sqlalchemy[asyncio] asyncpg alembic \
    pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart \
    PyPDF2 python-docx openai httpx redis python-dotenv

# 应用代码
COPY . .

# 工作目录切换到 backend 以便 alembic 能找到 alembic.ini
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

# Write new Dockerfile
print("\n=== 写入新 Dockerfile ===")
stdin, stdout, stderr = client.exec_command(f'cat > {project_dir}/Dockerfile << \'DOCKEREOF\'\n{new_dockerfile}\nDOCKEREOF')
out = stdout.read().decode()
err = stderr.read().decode()
if err:
    print("Error:", err)
else:
    print("写入成功")

# Step 3: Kill previous compose processes
print("\n=== 清理旧进程 ===")
stdin, stdout, stderr = client.exec_command('pkill -f "docker compose" 2>/dev/null; pkill -f "buildx" 2>/dev/null; echo done')
print(stdout.read().decode())

# Step 4: Rebuild - this time with nohup
print("\n=== 重新构建 (后台) ===")
cmd = f'cd {project_dir} && nohup docker compose -f docker-compose.prod.yml up -d --build > /tmp/vf-build2.log 2>&1 &'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

# Verify it started
import time
time.sleep(3)
stdin, stdout, stderr = client.exec_command('ps aux | grep -E "docker.*compose" | grep -v grep')
print("\n=== 运行中进程 ===")
print(stdout.read().decode())

client.close()
print("\nDone - 重新构建已启动")
