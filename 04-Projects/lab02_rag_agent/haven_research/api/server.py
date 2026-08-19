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
from openai import AsyncOpenAI
from haven_research.router import IntentRouter, UserIntent
from haven_research.editor import DocumentEditor

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

from haven_research.config.settings import ENV_FILE_PATH, settings
from dotenv import load_dotenv
if ENV_FILE_PATH.exists():
    load_dotenv(str(ENV_FILE_PATH))
else:
    load_dotenv()

intent_router = IntentRouter()
document_editor = DocumentEditor()

def get_async_client() -> Optional[AsyncOpenAI]:
    """动态安全获取 AsyncOpenAI 异步客户端 (代理至统一的 settings.get_async_llm_client)"""
    return settings.get_async_llm_client()

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


@app.post("/api/v1/auth/logout")
async def logout():
    """用户退出登录"""
    return {"success": True, "message": "已成功退出登录"}


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


@app.get("/api/v1/chat/sessions/{session_id}/artifact")
async def get_session_artifact(session_id: str, authorization: Optional[str] = Depends(security)):
    """获取指定会话的 Artifact 文档画布状态 (包含背景记忆、当前文档与版本号)"""
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)

    db = next(db_manager.get_db())
    session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session_obj.session_id,
        "title": session_obj.title,
        "background_context": session_obj.background_context or "",
        "current_document": session_obj.current_document or "",
        "document_version": session_obj.document_version or "v1.0"
    }


# ------------------------------------------------------------------------------
# 4. SSE (Server-Sent Events) 打字机流式 API 核心 Endpoint (带智能意图分流)
# ------------------------------------------------------------------------------
@app.get("/api/v1/chat/stream")
async def chat_stream_sse(
    session_id: str = Query(..., description="会话 ID"),
    query: str = Query(..., description="用户研究课题或指令"),
    report_source: str = Query("hybrid", description="数据源模式: hybrid / local / web"),
    authorization: Optional[str] = Depends(security)
):
    """
    【带状态意图路由的多轮协同 Agent 推流引擎】:
    1. 通过 IntentRouter 解析用户真实意图 (CHAT_ONLY / GENERATE_DOC / EDIT_DOC / RESEARCH_QNA) 并提取背景知识。
    2. 分流推流对话答疑、全量文档生成或已有文档的局部增量修饰。
    """
    logger.info(f"=== [SSE Connection] 收到用户提问请求: session_id='{session_id}', query='{query}' ===")
    token_str = authorization.credentials if authorization else None
    user_id = _get_user_id_from_header(f"Bearer {token_str}" if token_str else None)
    
    source_enum = ReportSource(report_source) if report_source in [e.value for e in ReportSource] else ReportSource.Hybrid
    req_dto = ResearchRequestDTO(query=query, report_source=source_enum, max_subtopics=3)

    db = next(db_manager.get_db())
    session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session_obj:
        session_obj = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=query[:30] if query else "新建深度研究会话"
        )
        db.add(session_obj)
        db.flush()
        logger.info(f"[SSE DB] 自动为您创建了新的 ChatSession 记录: {session_id}")
    elif session_obj.title in ["新深度研究对话", "新建深度研究会话"]:
        session_obj.title = query[:30]

    # 记录用户提问
    user_msg = ChatMessage(session_id=session_id, user_id=user_id, role="user", content=query)
    db.add(user_msg)
    db.commit()
    logger.info(f"[SSE DB] 用户提问落盘成功, 开始建立 EventSource 流式响应...")

    current_doc_snapshot = session_obj.current_document or ""
    current_ver_snapshot = session_obj.document_version or "v1.0"
    bg_snapshot = session_obj.background_context or ""

    async def event_generator():
        logger.info(f"[SSE Stream] 启动生成器，推送初始 Persona 给前端...")
        yield {
            "data": json.dumps({
                "type": "persona",
                "content": "正在智能识别意图与检索上下文..."
            }, ensure_ascii=False)
        }

        # 在异步流中精准判定意图
        intent, updated_bg = intent_router.route_and_extract(
            query=query,
            current_doc=current_doc_snapshot,
            existing_background=bg_snapshot
        )

        # 更新数据库保存最新的背景上下文
        if updated_bg != bg_snapshot:
            db_bg = next(db_manager.get_db())
            sess_bg = db_bg.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if sess_bg:
                sess_bg.background_context = updated_bg
                db_bg.commit()
                logger.info(f"[SSE Memory] 背景隐式记忆更新: '{updated_bg}'")

        # 优先推送 Intent 元数据事件给前端
        yield {
            "data": json.dumps({
                "type": "intent_meta",
                "intent": intent.value,
                "document_version": current_ver_snapshot,
                "has_document": bool(current_doc_snapshot)
            }, ensure_ascii=False)
        }
        logger.info(f"[SSE Intent] 匹配意图: {intent.value} | 对应处理流程准备就绪...")

        full_report_parts = []
        sources_data = []

        if intent == UserIntent.EDIT_DOC:
            logger.info(f"[SSE Workflow] 触发 EDIT_DOC (文档局部修订模式)...")
            async for event in document_editor.edit_document_stream(
                current_document=current_doc_snapshot,
                edit_instruction=query,
                background_context=updated_bg or bg_snapshot,
                current_version=current_ver_snapshot
            ):
                if event["type"] == "chunk":
                    full_report_parts.append(event["content"])
                elif event["type"] == "complete":
                    new_ver = event.get("version", current_ver_snapshot)
                    full_markdown = event.get("document", "".join(full_report_parts))
                    db_up = next(db_manager.get_db())
                    sess = db_up.query(ChatSession).filter(ChatSession.session_id == session_id).first()
                    if sess:
                        sess.current_document = full_markdown
                        sess.document_version = new_ver
                        db_up.commit()
                        logger.info(f"[SSE DB] EDIT_DOC 更新完成，保存最新文档版本 {new_ver}")

                yield {"data": json.dumps(event, ensure_ascii=False)}

        elif intent in [UserIntent.GENERATE_DOC, UserIntent.RESEARCH_QNA]:
            logger.info(f"[SSE Workflow] 触发 {intent.value} (Agent 搜索与全量生成模式)...")
            researcher = HavenResearcher(req_dto)
            async for event in researcher.conduct_research_stream():
                if event["type"] == "chunk":
                    full_report_parts.append(event["content"])
                elif event["type"] == "complete":
                    sources_data = event.get("sources", [])
                    if intent == UserIntent.GENERATE_DOC:
                        full_markdown = "".join(full_report_parts)
                        db_up = next(db_manager.get_db())
                        sess = db_up.query(ChatSession).filter(ChatSession.session_id == session_id).first()
                        if sess:
                            sess.current_document = full_markdown
                            sess.document_version = "v1.0"
                            db_up.commit()
                            logger.info(f"[SSE DB] GENERATE_DOC 完成，新建 v1.0 文档画布落盘")

                yield {"data": json.dumps(event, ensure_ascii=False)}

            logger.info(f"[SSE Workflow] 触发 CHAT_ONLY (纯对话/背景记录模式)...")
            
            # 检测是否输入了 GitHub 仓库链接并调用 GitHub MCP 真实实时抓取
            from haven_research.mcp.github_mcp import GitHubMCPClient
            parsed_gh = GitHubMCPClient.parse_github_url(query)
            gh_live_context = ""
            
            if parsed_gh:
                owner, repo = parsed_gh["owner"], parsed_gh["repo"]
                yield {
                    "data": json.dumps({
                        "type": "persona",
                        "content": f"✦ [GitHub MCP] 正在通过 GitHub API 真实请求仓库 {owner}/{repo} 数据..."
                    }, ensure_ascii=False)
                }
                gh_client = GitHubMCPClient()
                details = await gh_client.get_repository_details_async(owner, repo)
                if details:
                    pushed_date = details.get("pushed_at", "未知")
                    pushed_str = pushed_date[:10] if pushed_date else "未知"
                    yield {
                        "data": json.dumps({
                            "type": "persona",
                            "content": f"✦ [GitHub MCP] 已成功抓取仓库 {details['full_name']} 实时数据 (最新 Commit 提交时间: {pushed_str}, Star: {details['stars']}⭐)..."
                        }, ensure_ascii=False)
                    }
                    gh_live_context = (
                        f"\n【GitHub MCP 协议真实实时数据源 (已向 GitHub 官方 API 发起请求抓取)】:\n"
                        f"- 仓库名称: {details['full_name']}\n"
                        f"- 项目描述: {details['description']}\n"
                        f"- Star 数: {details['stars']}⭐ | Fork 数: {details['forks']} | Open Issues: {details['open_issues']}\n"
                        f"- 最新 Commit 提交时间 (pushed_at): {details['pushed_at']}\n"
                        f"- 最近更新时间 (updated_at): {details['updated_at']}\n"
                        f"- 项目语言: {details['language']} | 默认分支: {details['default_branch']}\n"
                        f"- README.md 文件真实内容节选:\n{details['readme'][:1500]}\n"
                    )

            try:
                client = get_async_client()
                if client:
                    logger.info(f"[SSE Chat] 成功获取 AsyncOpenAI 实例，发起对话推流...")
                    doc_summary_prompt = f"【当前右侧画布已生成的文档 ({current_ver_snapshot})】:\n{current_doc_snapshot[:600]}...\n\n" if current_doc_snapshot else "【当前右侧画布暂无文档】\n"
                    
                    system_prompt = f"""你是一个名为 HavenResearcher 的自主深度研究 Agent (Deep Research Agent)，1:1 对标 gpt-researcher 架构。
你的核心定位是：基于全网实时检索、ArXiv 学术论文 MCP、GitHub 源码 MCP 及本地向量库，帮助用户进行自动化深度研究并生成/编辑高质量的研究报告文档 (Artifacts)。

【对话答疑与追问响应原则】：
1. 当用户发送 GitHub 链接或查询 GitHub 仓库时：必须基于下方【GitHub MCP 协议真实实时数据源】给出 100% 真实客观的分析与总结，准确告知用户仓库的 Star 数、最新 Commit 提交时间及项目核心功能，严禁凭空记忆捏造 Commit 日期。
2. 当用户是对之前回答、检索数据或时间点进行质问、追问、吐槽或澄清时：请平易近人、诚恳严谨地向用户解释事实库边界、检索数据来源或技术逻辑。
3. 请在对话框做出直接、精准的简短回答，不要强行吐出大段全量 Markdown 报告。

{doc_summary_prompt}
{gh_live_context}"""

                    resp = await client.chat.completions.create(
                        model=settings.get_effective_model_name(),
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"已记忆的项目背景: {updated_bg or bg_snapshot or '暂无'}\n用户当前输入/查询: {query}"}
                        ],
                        stream=True
                    )
                    chunk_count = 0
                    async for chunk in resp:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            c = chunk.choices[0].delta.content
                            full_report_parts.append(c)
                            chunk_count += 1
                            yield {"data": json.dumps({"type": "chunk", "content": c}, ensure_ascii=False)}
                    logger.info(f"[SSE Chat] 对话推流完毕，共推流 {chunk_count} 个 Token 片段")

                else:
                    msg = "收到！已记录您的项目背景信息，后续生成或修改文档时将自动带入该约束。"
                    full_report_parts.append(msg)
                    yield {"data": json.dumps({"type": "chunk", "content": msg}, ensure_ascii=False)}

            except Exception as e:
                logger.error(f"[SSE Chat Error] 聊天对话推流产生异常: {e}")
                err_msg = f"回答出错: {str(e)}"
                full_report_parts.append(err_msg)
                yield {"data": json.dumps({"type": "chunk", "content": err_msg}, ensure_ascii=False)}

            yield {"data": json.dumps({"type": "complete", "sources": []}, ensure_ascii=False)}

        # 持久化保存助手回复到 ChatMessage
        full_assistant_text = "".join(full_report_parts)
        assistant_msg = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=full_assistant_text,
            sources_json=json.dumps(sources_data, ensure_ascii=False)
        )
        db_inner = next(db_manager.get_db())
        db_inner.add(assistant_msg)
        db_inner.commit()
        logger.info(f"=== [SSE Finish] 会话 {session_id} 处理完毕并成功持久化！ ===")

    return EventSourceResponse(event_generator())
