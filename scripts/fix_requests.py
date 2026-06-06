import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# Read current Dockerfile
stdin, stdout, stderr = client.exec_command(f'cat {project_dir}/Dockerfile')
original = stdout.read().decode()

# Add separate RUN line for requests (after the main pip install but before COPY . .)
# This preserves build cache for the main pip install step
marker = '# 应用代码'
insert_line = 'RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com requests\n\n# 应用代码'

new_dockerfile = original.replace(marker, insert_line)

print("=== 新 Dockerfile 中 pip 相关部分 ===")
for i, line in enumerate(new_dockerfile.split('\n')):
    if 'pip' in line.lower() or 'requests' in line.lower() or '应用代码' in line:
        print(f"  L{i+1}: {line}")

# Upload via SFTP
sftp = client.open_sftp()
with sftp.file(f'{project_dir}/Dockerfile', 'w') as f:
    f.write(new_dockerfile)
sftp.close()
print("\nDockerfile 已更新")

# Clean up
print("\n=== 清理旧容器 ===")
stdin, stdout, stderr = client.exec_command(f'cd {project_dir} && docker compose -f docker-compose.prod.yml down 2>&1')
print(stdout.read().decode())

# Rebuild
print("\n=== 重新构建 (利用缓存) ===")
cmd = f'cd {project_dir} && nohup docker compose -f docker-compose.prod.yml up -d --build > /tmp/vf-build3.log 2>&1 &'
stdin, stdout, stderr = client.exec_command(cmd)
print("后台构建已启动")

import time
time.sleep(5)
print("\n=== 构建日志初始输出 ===")
stdin, stdout, stderr = client.exec_command('tail -10 /tmp/vf-build3.log 2>/dev/null || echo "日志尚未生成"')
print(stdout.read().decode())

client.close()
