# 🐳 HavenResearch 服务器 Docker Compose 生产部署全指南

本文档指导如何在全新的 Linux 远程服务器（Ubuntu / CentOS / Debian）上，使用 **Docker 与 Docker Compose 一键一键拉起 MySQL 8.0 数据库、FastAPI Agent 后端与 Vue 3 Nginx 前端**！

---

## 🛠️ 1. 服务器环境准备 (三步搞定)

在您的 Linux 服务器上运行以下命令安装 Docker 与 Docker Compose：

```bash
# 1. 更新系统软件包并安装 Docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 2. 启动 Docker 并设置开机自启
systemctl start docker
systemctl enable docker

# 3. 验证 Docker 环境
docker --version
docker compose version
```

---

## 📦 2. 项目代码上传到服务器

可以通过 Git 仓库直接拉取，或使用 `scp` / SFTP 工具将项目上传到服务器：

```bash
# 方式 A：直接从 GitHub 拉取
git clone https://github.com/songhaiwen-ai/HAVEN-AI.git
cd HAVEN-AI/04-Projects/lab02_rag_agent
```

---

## 🚀 3. 一键 Docker Compose 启动容器集群

在 `lab02_rag_agent` 目录下执行以下一键启动命令：

```bash
# 1. 运行 Docker Compose 后台构建并启动集群
docker compose up -d --build

# 2. 查看所有容器运行状态
docker compose ps
```

控制台会显示以下 3 个 Healthy / Running 容器：
- `haven_mysql` (MySQL 8.0 数据库，映射端口 3306)
- `haven_backend` (FastAPI Agent 网关，映射端口 8000)
- `haven_frontend` (Vue 3 + Nginx 前端，映射端口 80)

---

## 🌐 4. 验证与访问

在浏览器中直接访问您服务器的公网 IP 或域名：
👉 **http://<您的服务器公网IP>**

系统会自动加载 Vue 3 极简界面，前端请求会经由 Nginx 自动反向代理到 `backend:8000` 并自动创建落盘 `haven_agent` MySQL 数据库！

---

## 🧹 5. 常用运维管理命令

```bash
# 查看实时运行日志 (后端与 MySQL)
docker compose logs -f backend

# 停止并清理容器集群
docker compose down

# 单独重启后端服务
docker compose restart backend
```
