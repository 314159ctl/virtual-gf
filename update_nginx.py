import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# Read local nginx.conf
with open('D:/Projects/virtual-girlfriend/nginx.conf', 'r', encoding='utf-8') as f:
    new_config = f.read()

# Upload via SFTP
print('上传新 nginx.conf...')
sftp = client.open_sftp()
with sftp.file(f'{project_dir}/nginx.conf', 'w') as f:
    f.write(new_config)
sftp.close()
print('已上传')

# Restart nginx
print('重启 nginx...')
stdin, stdout, stderr = client.exec_command(f'cd {project_dir} && docker compose -f docker-compose.prod.yml restart nginx 2>&1', timeout=30)
print(stdout.read().decode())

# Test static file access
print('测试静态文件...')
stdin, stdout, stderr = client.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost/static/avatars/ 2>&1')
print(f'HTTP状态: {stdout.read().decode()}')

# Test a specific avatar
stdin, stdout, stderr = client.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost/static/avatars/80ecb11d-4221-4522-91ce-82595b9ec5e9.jpg 2>&1')
print(f'头像文件状态: {stdout.read().decode()}')

client.close()
print('Done!')
