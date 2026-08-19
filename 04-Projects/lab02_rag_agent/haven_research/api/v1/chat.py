"""
haven_research/api/v1/chat.py - SSE 打字机流式推流 API 路由控制器
"""

from fastapi import APIRouter, Query, Depends
from sse_starlette.sse import EventSourceResponse

from haven_research.api.deps import get_current_user_id
from haven_research.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Agent Chat SSE"])

@router.get("/stream")
async def chat_stream_sse(
    session_id: str = Query(..., description="会话 ID"),
    query: str = Query(..., description="用户研究课题或指令"),
    report_source: str = Query("hybrid", description="数据源模式: hybrid / local / web"),
    user_id: int = Depends(get_current_user_id)
):
    """
    【带状态意图路由的多轮协同 Agent 推流 Endpoint】
    """
    generator = ChatService.generate_chat_stream(
        session_id=session_id,
        query=query,
        report_source=report_source,
        user_id=user_id
    )
    return EventSourceResponse(generator)
