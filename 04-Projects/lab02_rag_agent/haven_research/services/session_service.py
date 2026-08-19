"""
haven_research/services/session_service.py - 历史会话与 Artifacts 画布持久化服务 (Session Service)
"""

import uuid
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from haven_research.db import ChatSession, ChatMessage

class SessionService:
    """会话生命周期与 Artifact 画布数据存储逻辑服务类"""

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的全部历史会话列表"""
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for s in sessions
        ]

    @staticmethod
    def create_session(db: Session, user_id: int, title: str = "新深度研究对话") -> Dict[str, Any]:
        """新建对话会话"""
        session_id = str(uuid.uuid4())
        session_obj = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title or "新深度研究对话"
        )
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)

        return {
            "session_id": session_obj.session_id,
            "title": session_obj.title,
            "updated_at": session_obj.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def delete_session(db: Session, user_id: int, session_id: str) -> Dict[str, Any]:
        """删除指定会话及关联的历史消息"""
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id
        ).delete()
        
        db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        ).delete()
        
        db.commit()
        return {"success": True, "message": "会话已成功删除"}

    @staticmethod
    def get_session_messages(db: Session, user_id: int, session_id: str) -> List[Dict[str, Any]]:
        """查询指定会话的消息历史记录"""
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

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

    @staticmethod
    def get_session_artifact(db: Session, user_id: int, session_id: str) -> Dict[str, Any]:
        """获取指定会话的右侧 Artifact 文档画布状态"""
        session_obj = (
            db.query(ChatSession)
            .filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id)
            .first()
        )
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        return {
            "session_id": session_obj.session_id,
            "title": session_obj.title,
            "background_context": session_obj.background_context or "",
            "current_document": session_obj.current_document or "",
            "document_version": session_obj.document_version or "v1.0"
        }
