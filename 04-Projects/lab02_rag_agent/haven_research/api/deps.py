"""
haven_research/api/deps.py - FastAPI 依赖注入中心 (Dependencies Injection)
"""

from typing import Optional, Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from haven_research.db import db_manager
from haven_research.api.auth import security, decode_access_token

def get_db() -> Generator[Session, None, None]:
    """数据库 Session 依赖注入"""
    yield from db_manager.get_db()

def get_user_id_from_header(auth_header: Optional[str]) -> int:
    """提取 Header 中的 user_id，无 Token 则默认为 1 (演示访客)"""
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return int(payload["sub"])
    return 1

def get_current_user_id(authorization: Optional[str] = Depends(security)) -> int:
    """FastAPI 依赖注入：自动解析当前请求的 user_id"""
    token_str = authorization.credentials if authorization else None
    return get_user_id_from_header(f"Bearer {token_str}" if token_str else None)
