"""
haven_research/schemas/auth.py - 用户认证数据契约 (Auth DTO Schemas)
"""

from pydantic import BaseModel, Field
from typing import Optional

class UserAuthDTO(BaseModel):
    """用户注册 / 登录 DTO"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class UserResponseDTO(BaseModel):
    """用户响应 DTO"""
    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")

class AuthTokenResponseDTO(BaseModel):
    """Token 响应 DTO"""
    success: bool = True
    token: str = Field(..., description="JWT Access Token")
    user: UserResponseDTO
