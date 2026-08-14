"""
haven_research/api/server.py - 生产级前后端分离 Web ChatGPT 深度研究 Agent 后端 API 服务

【大厂生产架构】:
1. 身份认证与行级隔离: JWT Bearer Token + SHA256 加盐哈希 + 多租户 user_id 行隔离
2. 持久化存储 (MySQL/SQLite): 实时记录 users, chat_sessions, chat_messages 长文档历史
3. SSE 实时打字机推流: /api/v1/chat/stream 支持推流 Agent Persona、推理步骤与逐字 Markdown
4. 1:1 ChatGPT Web 前端: 静态挂载 /web 目录提供 Vue 3 SPA 交互界面
"""

import json
import asyncio
import os
import uuid
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException, Depends, status, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from haven_research.config import settings
from haven_research.core import logger
from haven_research.schemas.dto import ResearchRequestDTO, ResearchReportDTO, ReportType, ReportSource
from haven_research.agent import HavenResearcher
from haven_research.ingestion import LocalKnowledgeIngestionService

# 引入数据库持久化模型与 Auth 鉴权网关
from haven_research.db import db_manager, User, ChatSession, ChatMessage
from haven_research.api.auth import (
    security,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user_payload
)

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


# ------------------------------------------------------------------------------
# DTO 请求数据契约
# ------------------------------------------------------------------------------
class UserAuthDTO(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class SessionCreateDTO(BaseModel):
    title: Optional[str] = Field(default="新深度研究对话", description="会话标题")


# ------------------------------------------------------------------------------
# 1. 前端 Vue 3 静态页面路由
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/web", response_class=HTMLResponse)
async def serve_web_ui():
    """提供 1:1 ChatGPT 风格的 Vue 3 单页应用"""
    html_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse(content="<h3>HavenResearch Web UI 目录未安装</h3>")


# ------------------------------------------------------------------------------
# 2. 身份认证 API (注册 / 登录 / 当前用户信息)
# ------------------------------------------------------------------------------
@app.post("/api/v1/auth/register")
async def register(dto: UserAuthDTO):
    """用户注册"""
    db = next(db_manager.get_db())
    existing = db.query(User).filter(User.username == dto.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在，请直接登录！")

    user = User(
        username=dto.username,
        password_hash=hash_password(dto.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {
        "success": True,
        "token": token,
        "user": {"id": user.id, "username": user.username}
    }


@app.post("/api/v1/auth/login")
async def login(dto: UserAuthDTO):
    """用户登录"""
    db = next(db_manager.get_db())
    user = db.query(User).filter(User.username == dto.username).first()
    if not user or not verify_password(dto.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误！")

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {
        "success": True,
        "token": token,
        "user": {"id": user.id, "username": user.username}
    }


@app.get("/api/v1/auth/me")
async def get_me(payload: dict = Depends(get_current_user_payload)):
    """获取当前登录用户信息"""
    user_id = int(payload.get("sub", 1))
    db = next(db_manager.get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"id": user.id, "username": user.username}


# ------------------------------------------------------------------------------
# 3. 历史会话管理 API (创建 / 获取列表 / 消息历史 / 删除)
# ------------------------------------------------------------------------------
def _get_user_id_from_header(auth_header: Optional[str]) -> int:
    """提取 Header 中的 user_id，无 Token 则默认为 1 (演示访客)"""
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return int(payload["sub"])
    return 1


@app.get("/api/v1/chat/sessions")
async def get_sessions(authorization: Optional[str] = Depends(security)):
    """获取当前用户的全部历史会话列表"""
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)
    
    db = next(db_manager.get_db())
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    return [
        {
            "session_id": s.session_id,
            "title": s.title,
            "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        } for s in sessions
    ]


@app.post("/api/v1/chat/sessions")
async def create_session(dto: SessionCreateDTO, authorization: Optional[str] = Depends(security)):
    """创建新会话"""
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)

    session_id = str(uuid.uuid4())
    db = next(db_manager.get_db())
    session_obj = ChatSession(
        session_id=session_id,
        user_id=user_id,
        title=dto.title or "新深度研究对话"
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    return {
        "session_id": session_obj.session_id,
        "title": session_obj.title,
        "updated_at": session_obj.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    }


@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_session(session_id: str, authorization: Optional[str] = Depends(security)):
    """删除会话及其历史消息"""
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)

    db = next(db_manager.get_db())
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id).delete()
    db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id).delete()
    db.commit()

    return {"success": True, "message": "会话已成功删除"}


@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, authorization: Optional[str] = Depends(security)):
    """获取指定会话的历史消息列表"""
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)

    db = next(db_manager.get_db())
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id).order_by(ChatMessage.created_at.asc()).all()

    result = []
    for m in messages:
        sources = json.loads(m.sources_json) if m.sources_json else []
        result.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": sources,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return result


# ------------------------------------------------------------------------------
# 4. SSE (Server-Sent Events) 打字机流式 API 核心 Endpoint
# ------------------------------------------------------------------------------
@app.get("/api/v1/chat/stream")
async def chat_stream_sse(
    session_id: str = Query(..., description="会话 ID"),
    query: str = Query(..., description="用户研究课题"),
    report_source: str = Query("hybrid", description="数据源模式: hybrid / local / web"),
    authorization: Optional[str] = Depends(security)
):
    """
    【网页版 ChatGPT 核心推流引擎】:
    实时推流 Agent Persona、推理步骤 (Step Events)、逐字 Markdown 报告，
    并将提问与回答持久化存储到 MySQL/SQLite 数据库中。
    """
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)
    
    source_enum = ReportSource(report_source) if report_source in [e.value for e in ReportSource] else ReportSource.Hybrid
    req_dto = ResearchRequestDTO(query=query, report_source=source_enum, max_subtopics=3)

    # 1. 记录用户提问到 MySQL/SQLite
    db = next(db_manager.get_db())
    user_msg = ChatMessage(session_id=session_id, user_id=user_id, role="user", content=query)
    db.add(user_msg)
    
    # 自动更新会话标题为首次提问内容
    session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if session_obj and session_obj.title == "新深度研究对话":
        session_obj.title = query[:30]
    db.commit()

    async def event_generator():
        researcher = HavenResearcher(req_dto)
        full_report_parts = []
        sources_data = []

        # 消费 Agent 的真·Token 实时流式生成器
        async for event in researcher.conduct_research_stream():
            if event["type"] == "chunk":
                full_report_parts.append(event["content"])
            elif event["type"] == "complete":
                sources_data = event.get("sources", [])
            
            yield {"data": json.dumps(event, ensure_ascii=False)}

        # 2. 将 Agent 回答与全量 Markdown 持久化落盘到 MySQL/SQLite
        full_markdown = "".join(full_report_parts)
        assistant_msg = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=full_markdown,
            sources_json=json.dumps(sources_data, ensure_ascii=False)
        )
        db_inner = next(db_manager.get_db())
        db_inner.add(assistant_msg)
        db_inner.commit()

    return EventSourceResponse(event_generator())
