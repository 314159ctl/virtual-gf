import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Check backend logs
print("=== 后端容器日志 ===")
stdin, stdout, stderr = client.exec_command('docker logs vf-backend --tail=50 2>&1')
print(stdout.read().decode())

print("\n=== 容器状态 ===")
stdin, stdout, stderr = client.exec_command('docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1')
print(stdout.read().decode())

print("\n=== Docker Compose 状态 ===")
stdin, stdout, stderr = client.exec_command('cd /opt/virtual-girlfriend && docker compose -f docker-compose.prod.yml ps 2>&1')
print(stdout.read().decode())

client.close()
