import paramiko

host = '8.136.157.254'
user = 'root'
password = '@Ctl314159'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=15, look_for_keys=False, allow_agent=False)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + "\n" + err

# Fix bcrypt version compatibility
print("=== 修复 bcrypt 兼容性 ===")
print(run("docker exec vf-backend pip install 'bcrypt==4.0.1' 2>&1"))

# Now run seed
print("\n=== 运行种子数据初始化 ===")
print(run("docker exec vf-backend python -m app.core.seed 2>&1"))

# Verify admin user exists
print("\n=== 验证管理员 ===")
print(run("docker exec vf-backend python -c \"import asyncio; from app.db.session import AsyncSessionLocal; from app.models.user import User; from sqlalchemy import select; async def check(): async with AsyncSessionLocal() as db: r = await db.execute(select(User).where(User.email=='root@vgirl.com')); u = r.scalar_one_or_none(); print(f'管理员存在: {u.email if u else None}, is_admin: {u.is_admin if u else None}'); asyncio.run(check())\" 2>&1"))

client.close()
