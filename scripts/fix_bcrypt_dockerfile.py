import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# Read Dockerfile
stdin, stdout, stderr = client.exec_command(f'cat {project_dir}/Dockerfile')
original = stdout.read().decode()

# Add bcrypt version pin after the requests install line
marker = 'RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com requests\n\n# 应用代码'
replacement = 'RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com requests\n\n# 修复 passlib 与新版 bcrypt 的兼容性\nRUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com "bcrypt<4.1"\n\n# 应用代码'

new_dockerfile = original.replace(marker, replacement)

# Upload
sftp = client.open_sftp()
with sftp.file(f'{project_dir}/Dockerfile', 'w') as f:
    f.write(new_dockerfile)
sftp.close()
print("Dockerfile 已更新 (锁定 bcrypt<4.1)")

# Rebuild in background (will use cache)
print("\n=== 后台重建 ===")
stdin, stdout, stderr = client.exec_command(f'cd {project_dir} && nohup docker compose -f docker-compose.prod.yml up -d --build > /tmp/vf-build4.log 2>&1 &')
print("重建已启动 (利用缓存, 很快完成)")

import time
time.sleep(10)
print("\n=== 初始输出 ===")
stdin, stdout, stderr = client.exec_command('tail -15 /tmp/vf-build4.log 2>/dev/null')
print(stdout.read().decode())

client.close()
