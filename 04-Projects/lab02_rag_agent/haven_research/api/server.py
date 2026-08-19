"""
haven_research/api/server.py - 生产级 Web ChatGPT 深度研究 Agent API 主服务入口
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from haven_research.api.v1 import api_v1_router
from haven_research.config.settings import ENV_FILE_PATH, settings
from dotenv import load_dotenv

if ENV_FILE_PATH.exists():
    load_dotenv(str(ENV_FILE_PATH))
else:
    load_dotenv()

app = FastAPI(
    title="HavenResearch Deep Research Web ChatGPT API",
    description="专为 AI 最新技术问答、架构设计与行业研报深度分析打造的生产级 ChatGPT 风格 Agent 平台",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 Web 静态文件目录
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web")
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
@app.get("/web", response_class=HTMLResponse)
async def serve_web_ui():
    """提供 1:1 ChatGPT 风格的 Vue 3 单页应用"""
    html_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse(content="<h3>HavenResearch Web UI 目录未安装</h3>")


# 挂载 v1 版本 API 统一路由网关
app.include_router(api_v1_router)
