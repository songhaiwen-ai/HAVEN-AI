"""
haven_research/retrievers/base.py - 异步网络检索器策略抽象基类

【对标 gpt-researcher】: gpt_researcher/retrievers/base.py
使用 ABC 策略模式，定义统一的异步网络搜索接口规范。
"""

from abc import ABC, abstractmethod
from typing import List
from haven_research.schemas.dto import SearchResultDTO


class BaseRetriever(ABC):
    """网络检索器策略基类"""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResultDTO]:
        """
        执行异步网络检索
        :param query: 搜索关键词/子意图
        :param max_results: 返回的最多结果数量
        :return: 包含标题、URL 与摘要的 SearchResultDTO 列表
        """
        pass
