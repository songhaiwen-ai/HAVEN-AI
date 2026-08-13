"""
tests/test_verifier_costs.py - 阶段 4: CitationVerifierGate 与 CostTracker 单元测试

测试 Token 计数与美元费用折算，以及防幻觉引用门禁正则提取。
"""

import pytest
from haven_research.utils import CostTracker
from haven_research.verifier import CitationVerifierGate
from haven_research.schemas.dto import TextChunkDTO


def test_cost_tracker_calculation():
    """验证 CostTracker Token 与美元费用折算精确性"""
    tracker = CostTracker()
    tracker.add_tokens(prompt_tokens=1000, completion_tokens=500, step_name="test_step")
    tracker.add_embeddings(count=10)

    summary = tracker.get_summary()
    assert summary["total_tokens"] == 1500
    assert summary["prompt_tokens"] == 1000
    assert summary["completion_tokens"] == 500
    assert summary["embeddings_count"] == 10
    assert summary["total_cost_usd"] > 0.0


def test_citation_verifier_extraction():
    """验证 CitationVerifierGate 的断言与引用对抽取正则"""
    verifier = CitationVerifierGate()
    markdown = "根据最新研究 [AI Agent 选型](https://example.com/article)，Agent 框架正在快速演进。"
    
    extracted = verifier.extract_statements_and_citations(markdown)
    assert len(extracted) == 1
    assert "https://example.com/article" in extracted[0][1]
