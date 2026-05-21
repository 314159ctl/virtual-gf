import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

project_dir = '/opt/virtual-girlfriend'

# 1. Check which avatar files exist vs database references
print('=== 数据库引用 vs 实际文件 ===')
# Check DB
stdin, stdout, stderr = client.exec_command(
    "docker exec vf-db psql -U postgres -d virtual_gf -tAc "
    "\"SELECT avatar_url FROM users WHERE avatar_url IS NOT NULL UNION SELECT avatar_url FROM characters WHERE avatar_url IS NOT NULL\" 2>&1"
)
db_urls = stdout.read().decode().strip().split('\n')
db_urls = [u.strip() for u in db_urls if u.strip()]

# Check which files exist
for url in db_urls:
    filename = url.replace('/static/', '')
    cmd = f'docker exec vf-backend test -f /app/backend/static/{filename} && echo "EXISTS" || echo "MISSING"'
    stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
    status = stdout.read().decode().strip()
    print(f'  {url}: {status}')

# 2. Add volume for static files in docker-compose
print('\n=== 添加 static 卷挂载 ===')
stdin, stdout, stderr = client.exec_command(f'cat {project_dir}/docker-compose.prod.yml')
compose = stdout.read().decode()

# Add volume mount for static files under backend service
old = '    restart: unless-stopped\n    networks:\n      - vf-network\n\n  # ===='
new = '    volumes:\n      - staticdata:/app/backend/static\n    restart: unless-stopped\n    networks:\n      - vf-network\n\n  # ===='

if 'staticdata' not in compose:
    compose = compose.replace(old, new, 1)

    # Add volume definition at bottom
    compose = compose.replace(
        'volumes:\n  pgdata:\n  redisdata:',
        'volumes:\n  pgdata:\n  redisdata:\n  staticdata:'
    )

    # Upload
    sftp = client.open_sftp()
    with sftp.file(f'{project_dir}/docker-compose.prod.yml', 'w') as f:
        f.write(compose)
    sftp.close()
    print('docker-compose.prod.yml 已更新 (添加 staticdata 卷)')
else:
    print('staticdata 卷已存在')

# 3. Sync current static files to host and restart backend with volume
print('\n=== 同步 static 文件到宿主机 ===')
cmd = f'''
# Copy current static files from container to host
docker cp vf-backend:/app/backend/static /opt/virtual-girlfriend/backend/static 2>&1
echo "已同步"
# Recreate backend with volume
cd {project_dir} && docker compose -f docker-compose.prod.yml up -d --force-recreate backend 2>&1
'''
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
print(stdout.read().decode())

# Verify
print('\n=== 验证 ===')
stdin, stdout, stderr = client.exec_command('docker exec vf-backend ls /app/backend/static/avatars/ | wc -l')
print(f'avatar 文件数: {stdout.read().decode().strip()}')

stdin, stdout, stderr = client.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost/static/avatars/80ecb11d-4221-4522-91ce-82595b9ec5e9.jpg')
print(f'头像访问状态: {stdout.read().decode()}')

client.close()
print('\nDone!')
