import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Check full log
print("=== 完整构建日志 (tail 60) ===")
stdin, stdout, stderr = client.exec_command('tail -60 /tmp/vf-build.log 2>/dev/null')
out = stdout.read().decode()
if out:
    print(out)
else:
    print("日志为空")

# Check if build process still running
print("\n=== build 进程 ===")
stdin, stdout, stderr = client.exec_command('pgrep -a -f "buildx|docker.*build" 2>/dev/null || echo "无构建进程"')
print(stdout.read().decode())

# Check wc -l of log
print("\n=== 日志行数 ===")
stdin, stdout, stderr = client.exec_command('wc -l /tmp/vf-build.log 2>/dev/null')
print(stdout.read().decode())

client.close()
