import paramiko
import os
import sys

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

local_file = 'D:/Projects/vf-project.tar.gz'
remote_file = '/root/vf-project.tar.gz'
project_dir = '/opt/virtual-girlfriend'

print("连接服务器...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

# Step 1: Create project directory
print("创建项目目录...")
stdin, stdout, stderr = client.exec_command(f'mkdir -p {project_dir}')
stdout.read()
stderr.read()

# Step 2: Upload tar.gz via SFTP
print(f"上传 {local_file} ({os.path.getsize(local_file) / 1024 / 1024:.1f}MB)...")
sftp = client.open_sftp()

# Progress callback
def progress_cb(transferred, total):
    pct = transferred / total * 100
    print(f"\r  进度: {transferred / 1024 / 1024:.1f}MB / {total / 1024 / 1024:.1f}MB ({pct:.0f}%)", end='')

sftp.put(local_file, remote_file, callback=progress_cb)
print()
sftp.close()
print("上传完成!")

# Step 3: Extract on server
print("解压项目文件...")
extract_cmd = f'cd {project_dir} && tar xzf {remote_file} 2>&1 && rm {remote_file} && ls -la'
stdin, stdout, stderr = client.exec_command(extract_cmd, timeout=30)
print(stdout.read().decode())

# Step 4: Verify key files
print("验证关键文件...")
stdin, stdout, stderr = client.exec_command(f'ls {project_dir}/.env {project_dir}/docker-compose.prod.yml {project_dir}/Dockerfile {project_dir}/nginx.conf 2>&1')
print(stdout.read().decode())

# Step 5: Clean up local tarball
os.remove(local_file)
print(f"本地临时文件已清理")

client.close()
print("\n✅ 代码上传完成!")
