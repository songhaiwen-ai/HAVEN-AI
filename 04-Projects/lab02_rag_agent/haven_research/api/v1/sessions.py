"""
haven_research/api/v1/sessions.py - 历史会话管理与 Artifacts 文档画布 API 路由控制器
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from haven_research.api.deps import get_db, get_current_user_id
from haven_research.schemas.session import SessionCreateDTO
from haven_research.services.session_service import SessionService

router = APIRouter(prefix="/chat/sessions", tags=["Session & History"])

@router.get("")
@router.get("/")
async def get_sessions(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取当前用户的全部历史会话列表"""
    return SessionService.get_user_sessions(db, user_id)

@router.post("")
@router.post("/")
async def create_session(
    dto: SessionCreateDTO,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """创建新会话"""
    return SessionService.create_session(db, user_id, dto.title or "新深度研究对话")

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除会话及其历史消息"""
    return SessionService.delete_session(db, user_id, session_id)

@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取指定会话的历史消息列表"""
    return SessionService.get_session_messages(db, user_id, session_id)

@router.get("/{session_id}/artifact")
async def get_session_artifact(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取指定会话的 Artifact 文档画布状态"""
    return SessionService.get_session_artifact(db, user_id, session_id)
