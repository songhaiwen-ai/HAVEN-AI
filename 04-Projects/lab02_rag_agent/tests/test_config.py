"""
tests/test_config.py - Sprint 1 基础设施与配置单元测试

测试 Settings 配置中心加载、Logger 输出与 Exceptions 异常捕获。
"""

import sys
import pytest
from haven_research.config.settings import settings
from haven_research.core.exceptions import HavenAgentException, RetrieverException
from haven_research.schemas.dto import SearchResultDTO, ResearchRequestDTO


def test_settings_default_values():
    """验证 Settings 配置中心默认值与强类型加载"""
    assert settings.app_name == "HavenResearch Engine"
    assert settings.chunk_size == 400
    assert settings.chunk_overlap == 40
    assert settings.is_production() is False


def test_custom_exceptions():
    """验证自定义异常体系继承结构与错误码转换"""
    try:
        raise RetrieverException("DuckDuckGo 检索连接超时", details={"query": "AI Agent"})
    except HavenAgentException as e:
        assert e.error_code == "RETRIEVER_ERROR"
        assert "DuckDuckGo" in str(e)
        assert e.details["query"] == "AI Agent"


def test_dto_pydantic_validation():
    """验证 DTO 数据传输对象的字段校验约束"""
    req = ResearchRequestDTO(query="2026 AI Agent 架构设计", max_subtopics=3)
    assert req.query == "2026 AI Agent 架构设计"
    assert req.max_subtopics == 3

    # 测试缺省最小值校验失败场景
    with pytest.raises(Exception):
        ResearchRequestDTO(query="A", max_subtopics=0)  # 触发 min_length & ge=1 校验错误
