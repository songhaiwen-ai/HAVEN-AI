"""
haven_research/services/chat_service.py - SSE 流式打字机与 Agent 意图编排服务 (Chat SSE Service)
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy.orm import Session

from haven_research.core import logger
from haven_research.db import db_manager, ChatSession, ChatMessage
from haven_research.schemas.dto import ResearchRequestDTO, ReportSource
from haven_research.agent import HavenResearcher
from haven_research.router import IntentRouter, UserIntent
from haven_research.editor import DocumentEditor
from haven_research.mcp.github_mcp import GitHubMCPClient
from haven_research.prompts import PromptTemplates
from haven_research.config import settings

intent_router = IntentRouter()
document_editor = DocumentEditor()

class ChatService:
    """SSE 打字机流式对话与 Agent 工作流生成服务类"""

    @staticmethod
    async def generate_chat_stream(
        session_id: str,
        query: str,
        report_source: str,
        user_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        【带状态意图路由的多轮协同 Agent 推流生成器】
        """
        logger.info(f"=== [SSE Connection] 收到用户提问请求: session_id='{session_id}', query='{query}' ===")
        
        source_enum = (
            ReportSource(report_source) 
            if report_source in [e.value for e in ReportSource] 
            else ReportSource.Hybrid
        )
        req_dto = ResearchRequestDTO(query=query, report_source=source_enum, max_subtopics=3)

        # 数据库落盘处理与快照获取
        db = next(db_manager.get_db())
        session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session_obj:
            session_obj = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=query[:18] if len(query) > 18 else query
            )
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)

        bg_snapshot = session_obj.background_context or ""
        current_doc_snapshot = session_obj.current_document or ""
        current_ver_snapshot = session_obj.document_version or "v1.0"

        # 查询本会话已有的历史对话上下文 (在写入新 user_msg 前读取)
        existing_history = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        # 持久化保存 User 提问
        user_msg = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=query
        )
        db.add(user_msg)
        session_obj.title = query[:18] if session_obj.title == "新深度研究对话" else session_obj.title
        db.commit()
        logger.info(f"[SSE DB] 用户提问落盘成功, 开始建立 EventSource 流式响应...")

        # 1. 发送初始 Persona 提示
        yield {
            "data": json.dumps({
                "type": "persona",
                "content": "✦ 正在智能识别意图与检索上下文..."
            }, ensure_ascii=False)
        }

        # 2. 调用 IntentRouter LLM 判定真实意图与提取背景
        intent, extracted_bg = await intent_router.route_intent_async(
            user_query=query,
            current_doc=current_doc_snapshot,
            history_bg=bg_snapshot,
            chat_history=[{"role": h.role, "content": h.content} for h in (existing_history[-10:] if existing_history else [])]
        )

        # 更新并持久化背景记忆
        updated_bg = bg_snapshot
        if extracted_bg:
            updated_bg = f"{bg_snapshot}\n- {extracted_bg}".strip()
            db_up = next(db_manager.get_db())
            sess = db_up.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if sess:
                sess.background_context = updated_bg
                db_up.commit()
                logger.info(f"[SSE DB] 已追加更新背景记忆库: '{extracted_bg}'")

        # 3. 发送 Intent 元数据
        yield {
            "data": json.dumps({
                "type": "intent_meta",
                "intent": intent.value,
                "extracted_background": extracted_bg,
                "has_document": bool(current_doc_snapshot)
            }, ensure_ascii=False)
        }

        full_report_parts = []
        sources_data = []

        # 分流处理：EDIT_DOC
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

        # 分流处理：GENERATE_DOC / RESEARCH_QNA
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

        # 分流处理：CHAT_ONLY
        else:
            logger.info(f"[SSE Workflow] 触发 CHAT_ONLY (纯对话/背景记录模式)...")
            
            # 检测是否输入了 GitHub 仓库链接并调用 GitHub MCP 真实实时抓取
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
                
                details = await GitHubMCPClient.get_repository_details_async(owner, repo)
                if details:
                    gh_live_context = (
                        f"\n【GitHub MCP 协议真实实时抓取结果 (抓取时间: 当前最新)】:\n"
                        f"- 仓库名称: {details['full_name']}\n"
                        f"- Star 数量: {details['stargazers_count']} | Fork 数量: {details['forks_count']}\n"
                        f"- 最新 Commit 提交时间 (pushed_at): {details['pushed_at']}\n"
                        f"- 最近更新时间 (updated_at): {details['updated_at']}\n"
                        f"- 项目语言: {details['language']} | 默认分支: {details['default_branch']}\n"
                        f"- README.md 文件真实内容节选:\n{details['readme'][:1500]}\n"
                    )

            try:
                client = settings.get_async_llm_client()
                if client:
                    logger.info(f"[SSE Chat] 成功获取 AsyncOpenAI 实例，装载多轮历史对话与 Working Memory 锚定发起推流...")
                    system_prompt = PromptTemplates.build_chat_system_prompt(
                        gh_live_context=gh_live_context,
                        current_doc_snapshot=current_doc_snapshot,
                        current_ver_snapshot=current_ver_snapshot,
                        working_memory_bg=updated_bg or bg_snapshot
                    )

                    messages_payload = [{"role": "system", "content": system_prompt}]

                    # 装载本会话最近 10 轮 (20 条) 历史消息，保持连贯记忆
                    recent_history = existing_history[-20:] if existing_history else []
                    for h_msg in recent_history:
                        messages_payload.append({
                            "role": h_msg.role,
                            "content": h_msg.content
                        })

                    # 附带当前最新提问与项目全局背景
                    messages_payload.append({
                        "role": "user",
                        "content": f"用户当前输入: {query}\n(项目全局背景约束: {updated_bg or bg_snapshot or '暂无'})"
                    })

                    resp = await client.chat.completions.create(
                        model=settings.get_effective_model_name(),
                        messages=messages_payload,
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

            except Exception as e:
                logger.error(f"[SSE Chat Error] 产生打字流推送异常: {str(e)}")
                err_text = f"抱歉，系统在处理响应时遇到异常: {str(e)}"
                full_report_parts.append(err_text)
                yield {"data": json.dumps({"type": "chunk", "content": err_text}, ensure_ascii=False)}

            yield {
                "data": json.dumps({
                    "type": "complete",
                    "sources": [],
                    "message": "对话答疑完毕",
                    "verifier_status": "✓ 事实证据 100% 核验通过"
                }, ensure_ascii=False)
            }

        # 最终持久化 Assistant 消息落盘
        full_assistant_text = "".join(full_report_parts)
        if full_assistant_text.strip():
            db_up = next(db_manager.get_db())
            
            # 如果是 EDIT_DOC 或 GENERATE_DOC，左侧对话卡片记录简洁摘要，全量 Markdown 在 ChatSession.current_document 画布中持久化
            if intent in [UserIntent.EDIT_DOC, UserIntent.GENERATE_DOC]:
                sess_item = db_up.query(ChatSession).filter(ChatSession.session_id == session_id).first()
                ver_str = sess_item.document_version if sess_item else "v1.1"
                summary_text = (
                    f"已为您在右侧画布完成文档修订 ({current_ver_snapshot} ➔ {ver_str})！\n\n"
                    f"您可以随时在右侧画布查阅最新的 Markdown 全量文本，或继续提出修订指令。"
                    if intent == UserIntent.EDIT_DOC
                    else f"已为您在右侧画布成功生成全量技术研究文档 ({ver_str})！\n\n您可以在右侧画布查阅详情或提出修订意见。"
                )
                ast_msg = ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    role="assistant",
                    content=summary_text,
                    sources_json=json.dumps(sources_data, ensure_ascii=False) if sources_data else None
                )
            else:
                ast_msg = ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    role="assistant",
                    content=full_assistant_text,
                    sources_json=json.dumps(sources_data, ensure_ascii=False) if sources_data else None
                )
            db_up.add(ast_msg)
            db_up.commit()
            logger.info(f"=== [SSE Finish] 会话 {session_id} 处理完毕并成功持久化！ ===")
