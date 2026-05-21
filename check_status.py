import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode() + stderr.read().decode()

# Check current state
print("=== Docker 镜像 ===")
print(run('docker images 2>&1'))

print("\n=== 运行中的容器 ===")
print(run('docker ps -a 2>&1'))

print("\n=== 项目文件 ===")
print(run('ls /opt/virtual-girlfriend/.env 2>&1'))

client.close()
