import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

print("=== 在容器内运行种子数据初始化 ===")
cmd = 'docker exec vf-backend python -m app.core.seed 2>&1'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("STDERR:", err)

client.close()
