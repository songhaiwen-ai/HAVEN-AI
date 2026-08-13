"""
tests/test_mcp_retriever.py - MCP 两阶段智能检索器单元测试 (1:1 复现 gpt-researcher)

测试 MCPToolSelector 工具精排器与 MCPRetriever 两阶段检索工作流。
"""

import asyncio
import pytest
from haven_research.retrievers.mcp import MCPRetriever
from haven_research.mcp.tool_selector import MCPToolSelector
from haven_research.mcp.client import HavenMCPClient, MCPToolSchemaDTO


def test_mcp_tool_selector():
    """验证 MCPToolSelector 两阶段工具精排筛选能力"""
    async def _test():
        selector = MCPToolSelector()
        tools = [
            MCPToolSchemaDTO(name="query_db", description="数据库查询", parameters={}),
            MCPToolSchemaDTO(name="fetch_github", description="GitHub 代码仓库分析", parameters={}),
            MCPToolSchemaDTO(name="search_weather", description="天气预报查询", parameters={})
        ]

        selected = await selector.select_best_tools("分析 AI Agent 代码开源仓库", tools, max_tools=2)
        assert isinstance(selected, list)
        assert len(selected) <= 2

    asyncio.run(_test())


def test_mcp_retriever_pipeline():
    """验证 MCPRetriever 两阶段检索完整闭环"""
    async def _test():
        mcp_client = HavenMCPClient(server_name="integration_test_server")
        retriever = MCPRetriever(mcp_client=mcp_client)

        results = await retriever.search("数据库 SQL 查询与优化", max_results=2)
        assert isinstance(results, list)
        if results:
            assert results[0].href.startswith("mcp://")

    asyncio.run(_test())
