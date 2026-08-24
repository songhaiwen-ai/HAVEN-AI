"""
haven_research/api/deps.py - FastAPI 依赖注入中心 (Dependencies Injection)
"""

from typing import Optional, Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from haven_research.db import db_manager
from haven_research.api.auth import security, decode_access_token

from fastapi import Depends, Query

def get_db() -> Generator[Session, None, None]:
    """数据库 Session 依赖注入"""
    yield from db_manager.get_db()

def get_user_id_from_header_or_token(auth_header: Optional[str], token_param: Optional[str] = None) -> int:
    """提取 Header 或 Query Param 中的 Token 并解析 user_id，无 Token 降级为 1 (演示访客)"""
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif token_param:
        token = token_param
        
    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return int(payload["sub"])
    return 1

def get_current_user_id(
    authorization: Optional[str] = Depends(security),
    token: Optional[str] = Query(None, description="JWT Token (支持 EventSource 查询参数注入)")
) -> int:
    """FastAPI 依赖注入：自动解析当前请求的 user_id (兼容 Header 与 SSE Token Query)"""
    token_str = authorization.credentials if authorization else None
    return get_user_id_from_header_or_token(f"Bearer {token_str}" if token_str else None, token_param=token)
