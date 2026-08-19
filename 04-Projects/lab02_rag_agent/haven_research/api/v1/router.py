"""
haven_research/api/v1/router.py - v1 版本 API 路由汇总入口
"""

from fastapi import APIRouter
from haven_research.api.v1.auth import router as auth_router
from haven_research.api.v1.sessions import router as sessions_router
from haven_research.api.v1.chat import router as chat_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(chat_router)
