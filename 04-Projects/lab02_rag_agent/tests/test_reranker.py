"""
tests/test_reranker.py - 阶段 2: 混合检索与 BGE Reranker 重排序器单元测试

测试 BGEReranker 结合向量得分与词频匹配的二次打分，以及 HybridRetriever 粗筛到精排的整合流程。
"""

import pytest
from haven_research.schemas.dto import TextChunkDTO
from haven_research.reranker import BGEReranker, HybridRetriever
from haven_research.storage import VectorStoreFactory


def test_bge_reranker():
    """验证 BGEReranker 对粗筛切片进行二次打分与精排"""
    reranker = BGEReranker(vector_weight=0.5, lexical_weight=0.5)
    query = "AI Agent 架构选型"
    
    chunks = [
        TextChunkDTO(url="url1", content="无关文本：今天天气很好", score=0.8),
        TextChunkDTO(url="url2", content="相关文本：2026 年企业级 AI Agent 架构选型指南", score=0.6)
    ]

    reranked = reranker.rerank(query, chunks, top_n=2)
    assert len(reranked) == 2
    # 包含了 "AI Agent 架构选型" 关键词的 url2 应该因为词频和语义交叉打分超越原 score=0.8 的无关文本
    assert reranked[0].url == "url2"
    assert reranked[0].metadata.get("reranked") is True


def test_hybrid_retriever_pipeline():
    """验证 HybridRetriever 向量粗筛 + Reranker 精排的整合管道"""
    store = VectorStoreFactory.get_vector_store(":memory:")
    store.add_texts(
        texts=[
            "大模型分布式训练架构",
            "企业级 AI Agent 架构设计与选型",
            "Python 基础语法"
        ],
        metadatas=[{"source": "doc1"}, {"source": "doc2"}, {"source": "doc3"}]
    )

    hybrid = HybridRetriever(vector_store=store)
    results = hybrid.hybrid_search("AI Agent 架构", top_k=2, coarse_k=3)

    assert len(results) > 0
    assert isinstance(results[0], TextChunkDTO)
    assert "AI Agent 架构" in results[0].content
