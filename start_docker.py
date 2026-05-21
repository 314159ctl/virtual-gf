import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'
project_dir = '/opt/virtual-girlfriend'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Step 1: Check .env
print("=== 验证 .env 配置 ===")
stdin, stdout, stderr = client.exec_command(f'grep -E "^(DATABASE_URL|REDIS_URL|DB_PASSWORD|DEEPSEEK_API_KEY|SECRET_KEY|CORS_ORIGINS)=" {project_dir}/.env')
print(stdout.read().decode())

# Step 2: Create docker-compose alias if needed
print("=== 检查 docker compose ===")
stdin, stdout, stderr = client.exec_command('docker compose version 2>&1')
print(stdout.read().decode().strip())

# Step 3: Build and start (this will take a while)
print("\n=== 开始构建 Docker 镜像 (可能需要几分钟) ===")
# Use -T to disable TTY allocation for compose
cmd = f'cd {project_dir} && docker compose -f docker-compose.prod.yml build --no-cache 2>&1'
stdin, stdout, stderr = client.exec_command(cmd, timeout=600)

import select
import sys

# Read output in real-time
stdout.channel.setblocking(0)
stderr.channel.setblocking(0)

while not stdout.channel.exit_status_ready():
    while stdout.channel.recv_ready():
        data = stdout.channel.recv(4096)
        if data:
            print(data.decode('utf-8', errors='replace'), end='', flush=True)
    while stderr.channel.recv_ready():
        data = stderr.channel.recv(4096)
        if data:
            print(data.decode('utf-8', errors='replace'), end='', flush=True)

# Get exit status
exit_code = stdout.channel.recv_exit_status()
print(f"\n构建完成 (exit code: {exit_code})")

if exit_code != 0:
    print("构建失败，请检查上面的错误信息")
    client.close()
    exit(1)

# Step 4: Start containers
print("\n=== 启动容器 ===")
cmd = f'cd {project_dir} && docker compose -f docker-compose.prod.yml up -d 2>&1'
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("STDERR:", err)

# Step 5: Check container status
print("\n=== 容器状态 ===")
stdin, stdout, stderr = client.exec_command('docker compose -f /opt/virtual-girlfriend/docker-compose.prod.yml ps 2>&1')
print(stdout.read().decode())

# Step 6: Check logs for errors
print("\n=== 后端日志 (最近) ===")
stdin, stdout, stderr = client.exec_command('docker compose -f /opt/virtual-girlfriend/docker-compose.prod.yml logs --tail=20 backend 2>&1')
print(stdout.read().decode())

client.close()
print("\nDone")
