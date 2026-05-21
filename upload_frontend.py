import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# Upload tar
local_file = 'D:/Projects/vf-frontend.tar.gz'
remote_file = '/root/vf-frontend.tar.gz'

print("上传前端文件...")
sftp = client.open_sftp()
sftp.put(local_file, remote_file)
sftp.close()
print("上传完成")

# Extract
print("解压...")
cmd = f'cd {project_dir} && rm -rf frontend/dist && tar xzf {remote_file} && rm {remote_file} && ls frontend/dist/'
stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
print(stdout.read().decode())

# Verify nginx picks up new files (no restart needed since volume mount)
print("验证...")
stdin, stdout, stderr = client.exec_command('curl -s http://localhost/ | head -1')
print(stdout.read().decode())

# Clean local tar
import os
os.remove(local_file)

client.close()
print("Done! 刷新浏览器即可")
