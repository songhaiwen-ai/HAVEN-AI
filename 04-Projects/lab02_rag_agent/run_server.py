"""
run_server.py - 启动 HavenResearch FastAPI + SSE 打字机 Web 服务的入口脚本

在 PyCharm 中右键运行 `run_server.py` 或在命令行输入:
    python run_server.py

运行后浏览器访问:
    - Web 控制台 UI:  http://127.0.0.1:8000
    - OpenAPI 交互文档: http://127.0.0.1:8000/docs
"""

import os
import sys
import uvicorn

# 将项目根目录加入 sys.path 防止导包标红
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from haven_research.api import app

if __name__ == "__main__":
    print("=" * 80)
    print(" 🚀 启动 HavenResearch FastAPI + SSE 打字机流式 API 服务")
    print(" 🌐 浏览器访问 Web UI 交互界面: http://127.0.0.1:8000")
    print(" 📄 Swagger 接口文档:           http://127.0.0.1:8000/docs")
    print("=" * 80 + "\n")
    uvicorn.run("haven_research.api:app", host="127.0.0.1", port=8000, reload=True)
