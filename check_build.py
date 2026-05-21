import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Check if build is running
print("=== Docker build 进程 ===")
stdin, stdout, stderr = client.exec_command('ps aux | grep -E "docker|compose" | grep -v grep')
out = stdout.read().decode()
if out:
    print(out)
else:
    print("没有发现运行中的 Docker 进程")

print("\n=== 构建日志 (最后30行) ===")
stdin, stdout, stderr = client.exec_command('tail -30 /tmp/vf-build.log 2>/dev/null || echo "无日志"')
print(stdout.read().decode())

print("\n=== Docker 容器状态 ===")
stdin, stdout, stderr = client.exec_command('docker ps -a 2>&1')
print(stdout.read().decode())

print("\n=== Docker 镜像 ===")
stdin, stdout, stderr = client.exec_command('docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>&1')
print(stdout.read().decode())

client.close()
