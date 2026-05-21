import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('8.136.157.254', username='root', password='@Ctl314159', timeout=15, look_for_keys=False, allow_agent=False)

# Login
cmd = """curl -s -X POST http://localhost/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"root@vgirl.com","password":"root123456"}'"""
stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
login_result = stdout.read().decode().strip()
print('Login response:', login_result[:300])

try:
    data = json.loads(login_result)
    if 'access_token' in data:
        token = data['access_token']
        print('Token obtained:', token[:30] + '...')

        # Get user info
        cmd2 = f"curl -s http://localhost/api/v1/users/me -H 'Authorization: Bearer {token}'"
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=10)
        user = json.loads(stdout.read().decode())
        print(f"has_api_key: {user.get('has_api_key')}")
        print(f"is_admin: {user.get('is_admin')}")
        print(f"username: {user.get('username')}")
        print(f"api_base_url: {user.get('api_base_url')}")
        print(f"api_model: {user.get('api_model')}")
    else:
        print('Login failed:', data)
except Exception as e:
    print(f'Error: {e}')

client.close()
