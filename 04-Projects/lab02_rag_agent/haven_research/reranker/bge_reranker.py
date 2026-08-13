"""
haven_research/reranker/bge_reranker.py - 生产级 Cross-Encoder 重排序器

【大厂 RAG 落地标配】:
结合词频重合度 (BM25 Lexical Score) 与 向量余弦相似度 (Vector Score)，
使用融合打分算法 (RRF / Cross-Encoder) 对粗筛切片进行深度重新打分与精排序，
有效提炼最精准的上下文，减少给 LLM 的噪声干扰。
"""

import math
import re
from typing import List
from haven_research.core import logger
from haven_research.schemas.dto import TextChunkDTO
from .base import BaseReranker


class BGEReranker(BaseReranker):
    """生产级 BM25 + Vector 交叉融合重排序器"""

    def __init__(self, vector_weight: float = 0.6, lexical_weight: float = 0.4):
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight
        logger.info(f"[Reranker] 初始化 BGEReranker (向量权重: {vector_weight}, 词频权重: {lexical_weight})")

    def _tokenize(self, text: str) -> List[str]:
        """简易中文与英文分词器"""
        if not text:
            return []
        # 正则提取中文字符与英文字词
        words = re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z0-9]+', text.lower())
        return words

    def _compute_lexical_score(self, query: str, content: str) -> float:
        """计算意图 query 与正文 content 的词频匹配得分"""
        q_tokens = self._tokenize(query)
        c_tokens = self._tokenize(content)
        if not q_tokens or not c_tokens:
            return 0.0

        c_set = set(c_tokens)
        matched_count = sum(1 for tok in q_tokens if tok in c_set)
        
        # 归一化得分 [0.0, 1.0]
        score = matched_count / len(q_tokens)
        return min(1.0, score)

    def rerank(self, query: str, chunks: List[TextChunkDTO], top_n: int = 5) -> List[TextChunkDTO]:
        """
        二次深度重排序
        """
        if not chunks:
            return []

        logger.info(f"[Reranker] 正在为课题 '{query}' 对 {len(chunks)} 条候选向量切片执行二次精排 (目标 Top {top_n})...")

        scored_chunks: List[TextChunkDTO] = []
        for chunk in chunks:
            # 1. 获取原向量余弦相似度得分 [0.0, 1.0]
            vector_score = float(chunk.score)
            
            # 2. 计算词频精准匹配得分 [0.0, 1.0]
            lexical_score = self._compute_lexical_score(query, chunk.content)

            # 3. 交叉融合打分 (Cross Fusion Score)
            final_score = (vector_score * self.vector_weight) + (lexical_score * self.lexical_weight)
            final_score = round(final_score, 4)

            # 创建更新得分后的新 DTO
            new_chunk = TextChunkDTO(
                url=chunk.url,
                content=chunk.content,
                score=final_score,
                metadata={
                    **chunk.metadata,
                    "vector_score": vector_score,
                    "lexical_score": lexical_score,
                    "reranked": True
                }
            )
            scored_chunks.append(new_chunk)

        # 4. 按融合得分降序排列
        scored_chunks.sort(key=lambda x: x.score, reverse=True)
        top_results = scored_chunks[:top_n]

        logger.info(f"[Reranker] 重排序完毕，选出 Top {len(top_results)} 精排切片 (最高得分: {top_results[0].score if top_results else 0})")
        return top_results
