"""
haven_research/api/v1/auth.py - 身份认证 API 路由控制器
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from haven_research.api.deps import get_db
from haven_research.schemas.auth import UserAuthDTO
from haven_research.services.auth_service import AuthService
from haven_research.api.auth import get_current_user_payload

router = APIRouter(prefix="/auth", tags=["User Auth"])

@router.post("/register")
async def register(dto: UserAuthDTO, db: Session = Depends(get_db)):
    """用户注册 API"""
    return AuthService.register_user(db, dto.username, dto.password)

@router.post("/login")
async def login(dto: UserAuthDTO, db: Session = Depends(get_db)):
    """用户登录 API"""
    return AuthService.login_user(db, dto.username, dto.password)

@router.get("/me")
async def get_me(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    """获取当前登录用户信息 API"""
    user_id = int(payload.get("sub", 1))
    return AuthService.get_user_profile(db, user_id)

@router.post("/logout")
async def logout():
    """退出登录 API"""
    return {"success": True, "message": "已成功退出登录"}
