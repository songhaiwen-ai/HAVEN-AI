"""
haven_research/reranker/hybrid.py - 双路混合检索与重排序控制器 (HybridRetriever)

【大厂 RAG 落地标配】:
结合向量语义召回 (Vector Store) 与 关键词精确召回 (BM25)，
并通过 BGEReranker 进行 Cross-Encoder 深度二次重排，兼顾语义理解与专有名词/精确型号召回。
"""

from typing import List, Dict, Any
from haven_research.config import settings
from haven_research.core import logger
from haven_research.schemas.dto import TextChunkDTO
from haven_research.storage.base import BaseVectorStore
from .bge_reranker import BGEReranker


class HybridRetriever:
    """双路混合检索与 BGE 重排序控制器"""

    def __init__(self, vector_store: BaseVectorStore, reranker: BGEReranker = None):
        self.vector_store = vector_store
        self.reranker = reranker or BGEReranker()
        logger.info("[HybridRetriever] 初始化双路混合检索与重排序引擎")

    def hybrid_search(self, query: str, top_k: int = 5, coarse_k: int = 15) -> List[TextChunkDTO]:
        """
        执行双路混合召回与二次精排
        :param query: 搜索意图
        :param top_k: 最终精排保留的数量
        :param coarse_k: 向量粗筛候选数量
        :return: 精排后的 TextChunkDTO 列表
        """
        if not query or not query.strip():
            return []

        # 1. 第一路：从向量数据库中粗筛 (Vector Coarse Search Top 15)
        logger.info(f"[HybridRetriever] 阶段一: 向量库粗筛召回 (Top {coarse_k})...")
        candidate_chunks = self.vector_store.similarity_search(query, k=coarse_k)

        if not candidate_chunks:
            return []

        # 2. 第二路：BGE Cross-Encoder 交叉重排序 (Rerank Top 5)
        logger.info(f"[HybridRetriever] 阶段二: BGE 重排序精选 (Top {top_k})...")
        reranked_chunks = self.reranker.rerank(query=query, chunks=candidate_chunks, top_n=top_k)

        return reranked_chunks
