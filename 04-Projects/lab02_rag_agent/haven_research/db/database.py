"""
haven_research/db/database.py - 生产级 MySQL / SQLite 双模持久化数据库服务

【支持 MySQL 工业级落盘 + SQLite 本地零配置无缝切退】:
1. 用户表 users: 账号、加密密码、创建时间
2. 会话表 sessions: 会话 ID (session_id)、关联用户 ID (user_id)、会话标题 (title)
3. 消息历史表 messages: 消息 ID、关联会话与用户、角色 (user/assistant)、包含长 Markdown 报告 (MEDIUMTEXT) 与 Sources JSON
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv
from haven_research.config.settings import ENV_FILE_PATH, settings
from haven_research.core import logger

# 优先载入 .env 文件中的环境变量
if ENV_FILE_PATH.exists():
    load_dotenv(str(ENV_FILE_PATH))
else:
    load_dotenv()

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    """会话表 (与用户 1:N 绑定，支持背景上下文持久化与 Artifacts 文档画布)"""
    __tablename__ = "chat_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="新建深度研究会话")
    background_context = Column(Text, nullable=True)  # 用户隐式补充的项目背景与约束
    current_document = Column(Text(length=16777215), nullable=True)  # 当前最新版本的 Markdown 文档
    document_version = Column(String(20), nullable=True, default="v1.0")  # 文档版本号
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """消息历史表 (长 Markdown 文本与 Sources 元数据)"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" 或 "assistant"
    content = Column(Text(length=16777215), nullable=False)  # MEDIUMTEXT 满足超长 Markdown
    sources_json = Column(Text, nullable=True)  # JSON 元数据
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """生产级数据库管理类"""

    def __init__(self):
        # 默认优先尝试 MySQL，未配置则使用本地 SQLite 数据库文件
        mysql_url = os.getenv("MYSQL_URL") or getattr(settings, "mysql_url", None)
        if not mysql_url:
            mysql_url = "sqlite:///./haven_chat.db"
            logger.info("[Database] 默认使用 SQLite 数据库文件: ./haven_chat.db (支持随时切换 MySQL)")
        else:
            logger.info(f"[Database] 成功连接 MySQL 数据库: {mysql_url.split('@')[-1] if '@' in mysql_url else mysql_url}")

        try:
            self.engine = create_engine(mysql_url, pool_pre_ping=True, echo=False)
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("[Database] 数据库初始化成功！表结构已全量创建。")
        except Exception as e:
            logger.warning(f"[Database Warning] 连接目标数据库失败 ({e})，退避切换为 SQLite 本地数据库...")
            sqlite_url = "sqlite:///./haven_chat.db"
            self.engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        """FastAPI 依赖注入 Session 生成器"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# 全局单例数据库管理器
db_manager = DatabaseManager()
