"""
haven_research/retrievers/tavily.py - 生产级 Tavily AI 搜索引擎集成器

【大厂 / gpt-researcher 标配】: Tavily Search API
专为大模型 (LLM) 和 Agent 设计的高质量搜索引擎 API。
自动过滤广告、提取正文干货，直接返回格式化的精炼 Markdown/JSON 供 Agent 消费。
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger, RetrieverException
from haven_research.schemas.dto import SearchResultDTO
from .base import BaseRetriever


class TavilyRetriever(BaseRetriever):
    """Tavily AI 专有搜索引擎接口封装"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY") or getattr(settings, "tavily_api_key", None)
        if self.api_key:
            logger.info("[Retriever] 成功加载 Tavily AI 搜索引擎 API Key")
        else:
            logger.info("[Retriever] 未检测到 TAVILY_API_KEY，TavilyRetriever 将回退使用 DuckDuckGo 引擎")

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultDTO]:
        """
        调用 Tavily Search API 执行 AI 优化搜索
        :param query: 搜索关键词
        :param max_results: 最大返回条数
        :return: SearchResultDTO 列表
        """
        if not query or not query.strip():
            return []

        if not self.api_key:
            logger.warning("[TavilyRetriever Warning] 未配置 TAVILY_API_KEY，降级退避至 DuckDuckGo 搜索...")
            from .duckduckgo import DuckDuckGoRetriever
            ddg = DuckDuckGoRetriever()
            return await ddg.search(query, max_results=max_results)

        logger.info(f"[TavilyRetriever] 正在调用 Tavily AI 搜索: '{query}' (max_results: {max_results})")

        try:
            from tavily import AsyncTavilyClient
            client = AsyncTavilyClient(api_key=self.api_key)
            response = await client.search(query=query, max_results=max_results, search_depth="advanced")

            results: List[SearchResultDTO] = []
            for item in response.get("results", []):
                results.append(
                    SearchResultDTO(
                        title=item.get("title", "未命名"),
                        href=item.get("url", ""),
                        body=item.get("content", "")
                    )
                )

            logger.info(f"[TavilyRetriever] Tavily 搜索成功！返回 {len(results)} 条高质量 AI 清洗结果。")
            return results

        except Exception as e:
            logger.error(f"[TavilyRetriever Error] Tavily 搜索失败: {e}")
            # 优雅降级
            from .duckduckgo import DuckDuckGoRetriever
            ddg = DuckDuckGoRetriever()
            return await ddg.search(query, max_results=max_results)
