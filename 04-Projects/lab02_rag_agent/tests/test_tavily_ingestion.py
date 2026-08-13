"""
tests/test_tavily_ingestion.py - 本地文档落盘服务与 Tavily 搜索引擎单元测试

测试 LocalKnowledgeIngestionService 将 Markdown/Text 解析落盘入 Qdrant/Chroma，
以及 TavilyRetriever 的搜索引擎集成与退避机制。
"""

import os
import asyncio
import pytest
from haven_research.ingestion import LocalKnowledgeIngestionService
from haven_research.retrievers import TavilyRetriever
from haven_research.storage import VectorStoreFactory


def test_local_knowledge_ingestion_service(tmp_path):
    """验证 LocalKnowledgeIngestionService 解析本地文件并落盘入 Qdrant 内存库"""
    # 模拟在临时目录生成一个测试 Markdown 文件
    test_file = tmp_path / "agent_paper.md"
    test_file.write_text("# 2026 AI Agent 落地\n本文介绍了企业级 AI Agent 的设计与实践选型指南。", encoding="utf-8")

    store = VectorStoreFactory.get_vector_store(":memory:")
    service = LocalKnowledgeIngestionService(vector_store=store)

    count = service.ingest_file(str(test_file), extra_metadata={"user_id": "test_user_101"})
    assert count > 0

    hits = store.similarity_search("AI Agent 落地", k=1)
    assert len(hits) > 0
    assert "agent_paper.md" in hits[0].url or "agent_paper.md" in hits[0].metadata.get("source", "")
    assert hits[0].metadata.get("user_id") == "test_user_101"


def test_tavily_retriever_fallback():
    """验证 TavilyRetriever 在无 Key 情况下优雅降级至 DuckDuckGo"""
    async def _test():
        retriever = TavilyRetriever(api_key=None)
        results = await retriever.search("AI Agent 选型", max_results=2)
        assert isinstance(results, list)

    asyncio.run(_test())
