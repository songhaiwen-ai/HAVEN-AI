"""
haven_research/services/auth_service.py - 用户认证与鉴权服务 (Auth Service)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from haven_research.db import User
from haven_research.api.auth import hash_password, verify_password, create_access_token

class AuthService:
    """用户身份认证与 JWT Token 业务服务类"""

    @staticmethod
    def register_user(db: Session, username: str, password: str) -> dict:
        """注册新用户"""
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在，请直接登录！"
            )

        user = User(
            username=username,
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "username": user.username})
        return {
            "success": True,
            "token": token,
            "user": {"id": user.id, "username": user.username}
        }

    @staticmethod
    def login_user(db: Session, username: str, password: str) -> dict:
        """用户登录校验与 JWT Token 签发"""
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误！"
            )

        token = create_access_token({"sub": str(user.id), "username": user.username})
        return {
            "success": True,
            "token": token,
            "user": {"id": user.id, "username": user.username}
        }

    @staticmethod
    def get_user_profile(db: Session, user_id: int) -> dict:
        """获取用户 Personal Profile"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return {"id": user.id, "username": user.username}
