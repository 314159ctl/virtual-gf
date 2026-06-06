<p align="center">
  <h1 align="center">💕 virtual-gf</h1>
  <p align="center"><strong>AI 虚拟女友 — 一个全栈 AI 陪伴聊天应用</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.5-green?logo=vuedotjs" alt="Vue">
  <img src="https://img.shields.io/badge/FastAPI-0.115-teal?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-ready-blue?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="License">
</p>

---

## ✨ 功能

- 💬 **多角色 AI 对话** — 流式输出，支持自定义角色人设
- 🎨 **AI 绘画生成** — 集成豆包 Seedream，聊天中可生成图片
- 🖼️ **多模态图片识别** — 支持发送图片让 AI 理解
- 🎤 **语音合成 (TTS)** — 将 AI 回复转为语音
- 👤 **用户系统** — 注册/登录、JWT 认证、角色权限
- 📝 **聊天记录持久化** — SQLite / PostgreSQL，长期记忆
- 📊 **管理后台** — 用户管理、系统配置
- 🐳 **Docker 一键部署** — 含 Nginx + Let's Encrypt HTTPS

## 🖥️ 界面预览

> 柚子社画风 (Yuzusoft × Sakura) — 樱花粉色调、柔和圆角、温暖治愈

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/314159ctl/virtual-gf.git
cd virtual-gf
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-key
PAINTING_API_KEY=your-painting-api-key
```

### 3. 选择启动方式

<details>
<summary><b>Docker 部署（推荐）</b></summary>

```bash
# 完整生产环境（后端 + 前端 + Nginx + HTTPS）
docker compose -f docker-compose.prod.yml up -d
```

</details>

<details>
<summary><b>本地开发</b></summary>

**后端 (FastAPI 新版):**
```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

**后端 (Flask 旧版):**
```bash
pip install -r requirements.txt
python app.py
```

</details>

然后访问 `http://localhost:5173`（前端）或 `http://localhost:8000`（后端 API）。

## 📁 项目结构

```
virtual-gf/
├── backend/                # FastAPI 新版后端
│   ├── app/
│   │   ├── api/v1/         # RESTful API 路由
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 验证模型
│   │   ├── services/       # 业务逻辑层
│   │   └── core/           # 配置、安全、依赖注入
│   └── alembic/            # 数据库迁移
├── frontend/               # Vue 3 前端 (TypeScript)
│   └── src/
│       ├── views/          # 页面组件
│       ├── components/     # 通用组件
│       ├── composables/    # 组合式函数
│       └── stores/         # Pinia 状态管理
├── static/                 # Flask 旧版前端静态文件
├── characters/             # 角色定义 (JSON)
├── app.py                  # Flask 旧版入口
├── ai_engine.py            # AI 对话引擎
├── memory.py               # 记忆系统 (SQLite)
├── config.py               # 全局配置
├── DESIGN.md               # UI 设计规范
└── docker-compose.prod.yml # 生产环境编排
```

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| **后端** | Python 3.12+, FastAPI, Flask, SQLAlchemy |
| **前端** | Vue 3, TypeScript, Vite, Pinia |
| **AI** | DeepSeek API, 豆包 Seedream (火山引擎) |
| **数据库** | PostgreSQL / SQLite, Redis |
| **部署** | Docker, Nginx, Let's Encrypt |
| **认证** | JWT + bcrypt |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feat/amazing-feature`)
3. 提交你的修改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feat/amazing-feature`)
5. 打开一个 Pull Request

## 📄 许可证

MIT License — 详见 [LICENSE](./LICENSE) 文件

---

<p align="center">Made with 💕 by <a href="https://github.com/314159ctl">314159ctl</a></p>