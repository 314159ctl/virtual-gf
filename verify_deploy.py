import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Test from inside the server
print("=== 从服务器本地测试 ===")
tests = [
    ("Nginx 首页", "curl -s -o /dev/null -w '%{http_code}' http://localhost/"),
    ("API 健康检查", "curl -s http://localhost/health"),
    ("API 文档", "curl -s -o /dev/null -w '%{http_code}' http://localhost/docs"),
    ("API v1", "curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/"),
    ("前端页面", "curl -s http://localhost/ | head -5"),
]

for name, cmd in tests:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    result = stdout.read().decode().strip()
    print(f"  {name}: {result}")

# Test domain
print("\n=== DNS 解析验证 ===")
stdin, stdout, stderr = client.exec_command('curl -s -o /dev/null -w "%{http_code}" http://ctldhg.cn/ || echo "域名访问失败"')
print(f"  http://ctldhg.cn HTTP状态码: {stdout.read().decode().strip()}")

print("\n=== 后端最新日志 ===")
stdin, stdout, stderr = client.exec_command('docker logs vf-backend --tail=10 2>&1')
print(stdout.read().decode())

client.close()
