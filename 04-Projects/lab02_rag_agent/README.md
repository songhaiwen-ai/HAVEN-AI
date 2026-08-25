# 🚀 HavenResearch Engine (大模型深度研究与协同文档 Agent)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203-4FC08D.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20%7C%20Podman-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**HavenResearch Engine** 是一套生产级、端到端的大模型深度研究与协同文档编辑 Agent 系统（1:1 对标 GPT Researcher + Claude Artifacts 协同画布）。

系统集成了 **MCP（Model Context Protocol）扩展协议**、**多源实时检索（Tavily / GitHub / ArXiv）**、**Working Memory 动态背景记忆**、**多轮对话主题自动提炼（Refined Topic Extraction）**、**Artifacts 协同文档画布（v1.0 全量生成与 v1.1+ 增量局部修订）** 以及 **防幻觉引用核验门禁（Citation Verifier Gate）**。

---

## 🌟 核心功能特性

1. **🧠 智能意图路由与多轮主题提炼 (Intent Router & Topic Refinement)**：
   - 自动识别用户意图：`CHAT_ONLY`（纯对话与问答）、`GENERATE_DOC`（右侧画布生成全量白皮书）、`EDIT_DOC`（已有画布局部修订）、`RESEARCH_QNA`（网络检索答疑）；
   - **多轮上下文强连贯机制**：当在对话中讨论特定技术（如 LangGraph、MCP、RAG）后发送“请帮我生成技术文档”，系统能自动回溯历史，精准提炼具体技术课题（如 `LangGraph 架构设计与工程实践报告`）。

2. **📝 双栏协同文档画布 (Artifacts Canvas)**：
   - **v1.0 深度白皮书生成**：调起多源检索与结构规划，右侧画布生成 3,000 字高密度 Markdown 技术报告；
   - **v1.1+ 增量局部修订 (DocumentEditor)**：支持用户输入“删除4.2章节”、“重写第二段”、“增加流程对比表格”等自然语言指令，仅修改对应章节，保留全量文档格式与结构。

3. **🔌 MCP 协议与多源向量检索**：
   - 支持 **ArXiv 学术论文 MCP**、**GitHub API MCP 实时仓库数据抓取** 与 **Tavily 全网深度搜索**；
   - **Qdrant Cloud 线上向量数据库** + **BGE Reranker 语义重排**，确保数据权威可追溯。

4. **⚡ 真·流式推流与现代宽屏 UI**：
   - 基于 Server-Sent Events (SSE) 实现打字机 Token 实时流式响应（TTFT 首字延迟 < 1s）；
   - **Vue 3 + Vite + Tailwind CSS + Element Plus** 自适应宽屏排版（1280px max-width），告别空白割裂感。

---

## 📁 项目工程代码结构

```
lab02_rag_agent/
├── Dockerfile                  # 后端 Docker / Podman 镜像构建指令
├── docker-compose.yml          # 全量编排文件 (前端 Vue 3 + 后端 FastAPI + MySQL 8.0)
├── requirements.txt            # Python 生产依赖清单
├── run_server.py               # 后端 FastAPI Web 服务启动入口 (监听 0.0.0.0:8000)
├── setup.py                    # 包安装脚本
├── .env.example                # 生产环境环境变量配置模版
├── README.md                   # 全量架构说明与部署指南文档
│
├── haven_research/             # 【后端核心 Agent 架构】
│   ├── actions/                # 动态 Agent 角色选拔引擎 (choose_agent)
│   ├── api/                    # FastAPI 路由、认证中间件与 SSE 流式 Endpoint
│   ├── config/                 # 环境变量 (settings.py) 与全局配置
│   ├── core/                   # 核心 Logger 日志与自定义异常处理
│   ├── db/                     # SQLAlchemy 生产级数据库驱动 (MySQL / SQLite 自动退避)
│   ├── editor/                 # DocumentEditor 全量 Markdown 增量修订引擎
│   ├── ingestion/              # 语义切片器与 Map-Reduce 事实压缩器 (ContextCompressor)
│   ├── interpreter/            # Python 代码沙箱执行器
│   ├── mcp/                    # MCP 扩展协议组件 (GitHub MCP / ArXiv MCP)
│   ├── memory/                 # 会话历史持久化与 Working Memory 记忆管理
│   ├── planner/                # SubtopicPlanner 子主题规划引擎
│   ├── prompts/                # 动态 Prompt 模版管理
│   ├── reranker/               # 混合检索与 BGE Reranker 二次精排
│   ├── retrievers/             # 多源检索器 (Tavily, DuckDuckGo, MCP)
│   ├── router/                 # IntentRouter 智能意图路由与多轮主题提炼引擎
│   ├── schemas/                # Pydantic DTOs 传输对象模型
│   ├── scrapers/               # 异步网页抓取器 (Playwright / BeautifulSoup)
│   ├── services/               # ChatService / AuthService 核心业务逻辑
│   ├── skills/                 # Agent Skills 动态技能扩展库
│   ├── storage/                # VectorStoreFactory 向量数据库适配器 (Qdrant / Chroma)
│   ├── utils/                  # CostTracker 费用与 Token 消耗统计
│   └── verifier/               # CitationVerifier 防幻觉引用核验门禁
│
└── web-frontend/               # 【前端 Vue 3 + Vite 现代控制台应用】
    ├── Dockerfile              # 前端 Nginx 生产镜像构建指令
    ├── nginx.conf              # Nginx 生产反向代理、路由重定向与 SSE 流式推流配置
    ├── package.json            # 前端 NPM 依赖清单
    ├── vite.config.js          # Vite 构建配置
    ├── dist/                   # 前端编译打包产物 (全量提交至 git 供 Nginx 镜像直接挂载)
    └── src/                    # Vue 3 源码 (App.vue 主面板、API 模块、Tailwind 样式)
```

---

## 🛠️ 环境配置指南 (.env)

在本地或服务器项目根目录下创建 `.env` 文件（可参考 `.env.example`）：

```env
# 大模型 LLM API 配置 (支持 阿里通义千问 / DeepSeek / OpenAI)
LLM_MODEL=qwen-plus
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-llm-api-key-here

# Qdrant Cloud 线上向量数据库配置 (支持免费集群)
VECTOR_STORE_TYPE=qdrant
QDRANT_URL=https://your-cluster-id.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_cloud_api_key

# MySQL 生产级数据库配置 (Docker 容器内连接服务名 mysql:3306)
MYSQL_URL=mysql+pymysql://root:your_mysql_password@mysql:3306/haven_agent

# 实时检索与 MCP 凭证
TAVILY_API_KEY=tvly-your-tavily-key-here
GITHUB_TOKEN=github_pat_your-token-here

# 身份认证 JWT 密钥
JWT_SECRET=your_custom_jwt_secret_key_2026

# REST API 服务监听参数
HOST=0.0.0.0
PORT=8000
```

---

## 💻 本地开发调试运行

### 1. 后端 (FastAPI) 启动
```bash
# 激活 Python 虚拟环境并安装依赖
pip install -r requirements.txt

# 启动后端开发服务器
python run_server.py
```
- 后端访问地址：`http://127.0.0.1:8000`
- Swagger 接口文档：`http://127.0.0.1:8000/docs`

### 2. 前端 (Vue 3) 启动
```bash
cd web-frontend
npm install
npm run dev
```
- 前端开发调试地址：`http://localhost:5173`

---

## 🐳 生产环境一键部署 (Docker / Podman)

项目内置了全套 **容器化 Docker / Podman 编排方案**，包含 `FastAPI 后端` + `Vue 3 Nginx 前端` + `MySQL 8.0 数据库` 一键拉起。

### 一键部署步骤：

```bash
# 1. 克隆仓库并进入项目目录
git clone https://github.com/songhaiwen-ai/HAVEN-AI.git
cd HAVEN-AI/04-Projects/lab02_rag_agent

# 2. 配置 .env 环境变量文件
cp .env.example .env
nano .env  # 填入您的真实 API Key

# 3. 使用 Docker / Podman 一键编译构建并后台启动全套服务
docker compose up -d --build
# 或在 Podman 环境运行：
podman-compose up -d --build
```

### 生产验证与防火墙：
1. **查看服务状态**：`docker compose ps` (确认 `haven_frontend`, `haven_backend`, `haven_mysql` 三大容器均为 Up 状态)；
2. **服务器安全组放行**：在阿里云/腾讯云控制台安全组规则中**放行 80 端口**；
3. **浏览器访问**：直接访问 `http://您的服务器公网IP` 即可完美使用！

---

## ❓ 常见问题排查 (Troubleshooting)

- **Q1: 为什么部署后打开网页显示 502 Bad Gateway？**
  - 原因 1：后端容器 `run_server.py` 绑死了 `127.0.0.1`。现已统一修复为 `0.0.0.0`。
  - 原因 2：后端的容器重新构建后分配了新的容器 IP，Nginx 缓存了旧 IP。在服务器终端运行 `podman restart haven_frontend` 即可瞬间刷起！
- **Q2: 前端访问出现空白黑屏？**
  - 原因：未把编译后的 `web-frontend/dist/` 引入 Git。现已解除 `.gitignore` 限制并补全全量 JS/CSS 产物。
- **Q3: Podman 报 `TypeError: join() argument must be str or bytes, not 'dict'`？**
  - 原因：老版本 Podman 不兼容 `env_file` 字典语法。在 `docker-compose.yml` 中已统一修改为标准列表语法 `- .env`。
