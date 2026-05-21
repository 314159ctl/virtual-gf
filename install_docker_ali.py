import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('8.136.157.254', username='root', password='@Ctl314159', timeout=15, look_for_keys=False, allow_agent=False)

print("=== 使用阿里云镜像安装 Docker ===")

# Use Aliyun mirrors for Docker installation
install_script = """
# 卸载旧版本
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# 安装依赖
apt-get update -qq
apt-get install -y ca-certificates curl gnupg lsb-release

# 添加阿里云 Docker GPG 密钥
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加阿里云 Docker APT 源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
apt-get update -qq
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动 Docker
systemctl enable docker
systemctl start docker

# 配置镜像加速器（阿里云容器镜像服务）
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'DOCKERJSON'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://docker.m.daocloud.io"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
DOCKERJSON

systemctl daemon-reload
systemctl restart docker

echo ""
echo "======== Docker 版本 ========"
docker --version
echo ""
echo "======== Docker Compose 版本 ========"
docker compose version
echo ""
echo "======== Docker 服务状态 ========"
systemctl status docker --no-pager | head -5
"""

stdin, stdout, stderr = client.exec_command(install_script, timeout=180)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("STDERR:", err[:500])

client.close()
