"""
tests/test_ingestion.py - Sprint 2 数据处理与文档加载单元测试

测试 SemanticTextSplitter 语义切片器与 DocumentLoader 文档解析器。
"""

import os
import pytest
from haven_research.ingestion import SemanticTextSplitter, DocumentLoader
from haven_research.core.exceptions import DocumentParsingException


def test_semantic_text_splitter():
    """测试语义切片器与窗口重叠逻辑"""
    splitter = SemanticTextSplitter(chunk_size=50, chunk_overlap=10)
    sample_text = "AI Agent 是基于大语言模型的自主智能体。感知、规划、记忆与工具调用是四大支柱。ReAct 循环控制着主要的思维链流程。"
    
    chunks = splitter.split_text(sample_text)
    assert len(chunks) > 1
    assert isinstance(chunks, list)
    assert all(len(c) <= 60 for c in chunks)


def test_document_loader_md():
    """测试 Markdown 本地示例文档解析与元数据提取"""
    loader = DocumentLoader()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_md = os.path.join(os.path.dirname(base_dir), "data", "sample_agent_paper.md")

    if os.path.exists(sample_md):
        docs = loader.load_document(sample_md)
        assert len(docs) == 1
        assert "metadata" in docs[0]
        assert docs[0]["metadata"]["source"] == "sample_agent_paper.md"
        assert "AI Agent" in docs[0]["content"]


def test_document_loader_invalid_file():
    """测试不可用文件的异常捕获"""
    loader = DocumentLoader()
    with pytest.raises(DocumentParsingException):
        loader.load_document("not_exist_file.pdf")
