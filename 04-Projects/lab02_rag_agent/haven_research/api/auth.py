"""
haven_research/api/auth.py - JWT 身份认证与密码 Salting 网关

【大厂安全规范】:
实现注册/登录哈希校验、JWT Token 签发与 FastAPI Depends 鉴权钩子 (HTTPBearer)，
确保多用户环境下的数据完全隔离与行级权限控制。
"""

import hashlib
import time
import base64
import json
import hmac
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from haven_research.config import settings
from haven_research.core import logger

security = HTTPBearer(auto_error=False)

JWT_SECRET = getattr(settings, "jwt_secret", "haven_agent_secret_key_2026")
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """使用 SHA256 加盐对用户明文密码哈希加密"""
    salt = "haven_agent_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码哈希"""
    return hash_password(password) == password_hash


def create_access_token(data: dict, expires_delta_seconds: int = 86400 * 7) -> str:
    """签发 JWT Token"""
    payload = data.copy()
    payload.update({"exp": int(time.time()) + expires_delta_seconds})
    
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signature_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(JWT_SECRET.encode(), signature_input.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """解析与验签 JWT Token"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        signature_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(JWT_SECRET.encode(), signature_input.encode(), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

        if signature_b64 != expected_sig_b64:
            return None

        # 补全 base64 填充
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)

        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_json)

        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception as e:
        logger.error(f"[Auth Error] Token 解析失败: {e}")
        return None


async def get_current_user_payload(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """FastAPI 依赖注入: 获取当前登录用户的 JWT Payload"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization 认证 Header，请先登录！"
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的 JWT Token，请重新登录！"
        )
    return payload
