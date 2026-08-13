"""
haven_research/reranker/base.py - 重排序与混合检索器抽象基类

定义 Cross-Encoder 重排序器与双路混合检索器的统一接口模型。
"""

from abc import ABC, abstractmethod
from typing import List
from haven_research.schemas.dto import TextChunkDTO


class BaseReranker(ABC):
    """文本重排序器策略基类"""

    @abstractmethod
    def rerank(self, query: str, chunks: List[TextChunkDTO], top_n: int = 5) -> List[TextChunkDTO]:
        """
        对输入的候选 TextChunkDTO 列表根据与 query 的相关度重新打分与排序
        :param query: 搜索意图或问题
        :param chunks: 粗筛出的候选切片列表 (如 Top 20)
        :param top_n: 重排序后保留的最精粹切片数量
        :return: 重新打分并降序排列的 TextChunkDTO 列表 (Top N)
        """
        pass
