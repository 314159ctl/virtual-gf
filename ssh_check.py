import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(
        '8.136.157.254',
        username='root',
        password='@Ctl314159',
        timeout=15,
        look_for_keys=False,
        allow_agent=False,
    )
    print('SSH连接成功!')

    cmds = [
        ('系统版本', 'cat /etc/os-release | head -3'),
        ('Docker版本', 'docker --version 2>&1 || echo "Docker未安装"'),
        ('Docker Compose', 'docker compose version 2>&1 || docker-compose --version 2>&1 || echo "未安装"'),
        ('磁盘空间', 'df -h /'),
        ('内存', 'free -h'),
    ]

    for name, cmd in cmds:
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(f'\n=== {name} ===')
        print(output or error)

    client.close()
except paramiko.AuthenticationException as e:
    print(f'认证失败: {e}')
    sys.exit(2)
except Exception as e:
    print(f'连接失败: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
