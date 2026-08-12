"""
tests/test_storage.py - Sprint 3 向量存储与工厂模式单元测试

测试 BaseVectorStore 抽象接口、ChromaVectorStore 磁盘持久化、QdrantVectorStore 云端客户端与 VectorStoreFactory 工厂类。
"""

import os
import shutil
import pytest
from haven_research.storage import VectorStoreFactory, ChromaVectorStore, QdrantVectorStore
from haven_research.schemas.dto import TextChunkDTO


@pytest.fixture
def temp_vector_store(tmp_path):
    """创建临时 Chroma 向量数据库实例环境"""
    persist_dir = str(tmp_path / "test_chroma_db")
    store = VectorStoreFactory.get_vector_store(
        store_type="chroma",
        collection_name="test_collection",
        persist_dir=persist_dir
    )
    yield store
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir, ignore_errors=True)


def test_vector_store_factory():
    """验证 Factory 动态创建 Chroma 与 Qdrant 实例"""
    store_chroma = VectorStoreFactory.get_vector_store("chroma")
    assert isinstance(store_chroma, ChromaVectorStore)

    store_qdrant = VectorStoreFactory.get_vector_store("qdrant", qdrant_url=":memory:")
    assert isinstance(store_qdrant, QdrantVectorStore)


def test_qdrant_vector_store_add_and_search():
    """验证 Qdrant 客户端的写入与 384 维余弦相似度检索"""
    qstore = VectorStoreFactory.get_vector_store("qdrant", qdrant_url=":memory:", collection_name="test_qdrant")
    
    texts = [
        "Qdrant 是基于 Rust 编写的高性能向量数据库。",
        "Deep Research Agent 具备自动规划、多路检索与报告生成能力。"
    ]
    metadatas = [
        {"source": "qdrant_doc.md", "page": 1},
        {"source": "agent_paper.pdf", "page": 2}
    ]

    # 1. 写入
    ids = qstore.add_texts(texts, metadatas=metadatas)
    assert len(ids) == 2
    assert qstore.count() == 2

    # 2. 检索
    results = qstore.similarity_search("Qdrant 数据库的特点", k=1)
    assert len(results) == 1
    assert "Rust" in results[0].content
    assert results[0].score > 0.0


def test_vector_store_add_and_search(temp_vector_store):
    """验证向向量存储写入文本切片并执行余弦相似度检索"""
    texts = [
        "RAG 检索增强生成能够将私有知识库切片注入 Prompt，有效防止大模型产生幻觉。",
        "ReAct 循环通过 Observe -> Think -> Act 实现 Agent 的自主交互决策。",
        "ChromaDB 是一个支持磁盘持久化的轻量级开源向量数据库。"
    ]
    metadatas = [
        {"source": "rag_paper.pdf", "page": 1},
        {"source": "react_paper.pdf", "page": 2},
        {"source": "chroma_doc.md", "page": 1}
    ]

    ids = temp_vector_store.add_texts(texts, metadatas=metadatas)
    assert len(ids) == 3
    assert temp_vector_store.count() == 3

    query = "如何解决 LLM 的幻觉问题？"
    results = temp_vector_store.similarity_search(query, k=2)

    assert len(results) > 0
    assert isinstance(results[0], TextChunkDTO)
    assert "RAG 检索增强生成" in results[0].content
    assert results[0].score > 0.0
