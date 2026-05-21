import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('8.136.157.254', username='root', password='@Ctl314159', timeout=15, look_for_keys=False, allow_agent=False)

print("=== 安装 Docker ===")

# Install Docker using official script
cmds = [
    ("安装 Docker", "curl -fsSL https://get.docker.com | sh 2>&1"),
    ("启动 Docker", "systemctl enable docker && systemctl start docker 2>&1"),
    ("验证 Docker", "docker --version 2>&1"),
    ("验证 Compose", "docker compose version 2>&1"),
]

for name, cmd in cmds:
    print(f"\n--- {name} ---")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    if err:
        print(err)

client.close()
print("\nDONE")
