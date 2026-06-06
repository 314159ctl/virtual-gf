import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Check Dockerfile
print("=== Dockerfile 前5行 ===")
stdin, stdout, stderr = client.exec_command('head -5 /opt/virtual-girlfriend/Dockerfile')
print(stdout.read().decode())

# Check if rebuild is running
print("=== compose 进程 ===")
stdin, stdout, stderr = client.exec_command('ps aux | grep -E "docker.*compose|buildx" | grep -v grep')
out = stdout.read().decode()
print(out if out else "无相关进程")

# Check build log
print("=== build2 日志 (tail 20) ===")
stdin, stdout, stderr = client.exec_command('tail -20 /tmp/vf-build2.log 2>/dev/null || echo "日志不存在"')
print(stdout.read().decode())

# Check docker images
print("=== 镜像 ===")
stdin, stdout, stderr = client.exec_command('docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"')
print(stdout.read().decode())

client.close()
