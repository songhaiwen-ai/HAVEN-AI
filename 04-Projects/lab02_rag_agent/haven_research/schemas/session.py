"""
haven_research/schemas/session.py - 会话与消息历史数据契约 (Session DTO Schemas)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SessionCreateDTO(BaseModel):
    """创建新会话 DTO"""
    title: Optional[str] = Field(default="新深度研究对话", description="会话标题")

class SessionResponseDTO(BaseModel):
    """会话响应 DTO"""
    session_id: str = Field(..., description="会话 ID")
    title: str = Field(..., description="会话标题")
    updated_at: str = Field(..., description="最近更新时间")

class MessageResponseDTO(BaseModel):
    """消息历史响应 DTO"""
    id: int = Field(..., description="消息 ID")
    role: str = Field(..., description="角色: user / assistant")
    content: str = Field(..., description="消息正文")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="参考数据源")
    created_at: str = Field(..., description="创建时间")

class ArtifactResponseDTO(BaseModel):
    """Artifact 文档画布状态 DTO"""
    session_id: str = Field(..., description="会话 ID")
    title: str = Field(..., description="会话标题")
    background_context: str = Field(..., description="已被记忆的上下文背景")
    current_document: str = Field(..., description="当前画布生成的 Markdown 文档")
    document_version: str = Field(..., description="文档版本号 (如 v1.0)")
