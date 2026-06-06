import paramiko
import time

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# Start docker compose build in background with nohup
print("=== 后台启动 Docker 构建 ===")
cmd = f'cd {project_dir} && nohup docker compose -f docker-compose.prod.yml up -d --build > /tmp/vf-build.log 2>&1 &'
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()
err = stderr.read().decode()
print(out or err)
print(f"后台构建已启动，PID: ...")

# Wait a few seconds then check log
time.sleep(10)

print("\n=== 构建日志 (前30行) ===")
stdin, stdout, stderr = client.exec_command('head -50 /tmp/vf-build.log 2>/dev/null || echo "日志文件尚未生成"')
print(stdout.read().decode())

print("\n构建正在后台运行中，约需3-5分钟...")
print("你可以稍后等待完成，或者先去做其他事情。")
client.close()
