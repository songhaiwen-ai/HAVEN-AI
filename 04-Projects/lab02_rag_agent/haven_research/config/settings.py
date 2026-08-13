"""
haven_research/config/settings.py - 企业级生产配置中心管理模块

采用 Pydantic Settings 实现强类型配置管理，支持从环境变量与 .env 文件自动加载配置，
包含全量类型检查、默认值设置与 OpenAI / DeepSeek 等多模型工厂方法。
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局应用配置类"""

    # 1. 基础应用配置
    app_name: str = "HavenResearch Engine"
    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = True

    # 2. 大模型 LLM 配置 (原生支持 DeepSeek / OpenAI / 硅基流动 等)
    llm_provider: str = "deepseek"  # 支持 openai, deepseek, siliconflow, ollama
    llm_model: str = "deepseek-chat"  # deepseek-chat 或 deepseek-reasoner
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.deepseek.com"  # DeepSeek 官方 API Base URL

    # 3. 向量数据库 Vector Store 配置 (支持 qdrant / chroma_local / chroma_remote)
    vector_store_type: str = "qdrant"  # 支持 qdrant, chroma_local, chroma_remote
    vector_store_dir: str = "./chroma_db"
    vector_store_host: str = "127.0.0.1"
    vector_store_port: int = 8000
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    default_collection_name: str = "agent_knowledge_base"

    # 4. Agent 抓取与检索工程参数
    tavily_api_key: Optional[str] = None
    max_subtopics: int = 3
    search_max_results: int = 5
    scraper_timeout: int = 10
    chunk_size: int = 400
    chunk_overlap: int = 40

    # 5. REST API & Web 服务配置
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.app_env.lower() == "production"

    def get_llm_client(self):
        """
        获取配置好的标准 OpenAI / DeepSeek 客户端实例
        """
        if not self.openai_api_key:
            return None
            
        from openai import OpenAI
        return OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_base_url
        )


# 全局单例配置实例
settings = Settings()
