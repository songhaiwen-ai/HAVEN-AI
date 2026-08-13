"""
tests/test_arxiv_github_mcp.py - ArXiv 学术论文与 GitHub 开源代码库 MCP 客户端单元测试

测试 ArXivMCPClient 完全免费零 Key 检索能力，与 GitHubMCPClient 开源仓库查询。
"""

import asyncio
import pytest
from haven_research.mcp import ArXivMCPClient, GitHubMCPClient
from haven_research.schemas.dto import SearchResultDTO


def test_arxiv_mcp_client():
    """验证 ArXivMCPClient 检索 arXiv.org 最新前沿论文"""
    async def _test():
        client = ArXivMCPClient()
        results = await client.search_papers_async("Retrieval-Augmented Generation", max_results=2)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], SearchResultDTO)
            assert "[ArXiv" in results[0].title

    asyncio.run(_test())


def test_github_mcp_client():
    """验证 GitHubMCPClient 检索 GitHub 最火开源仓库"""
    async def _test():
        client = GitHubMCPClient()
        results = await client.search_repositories_async("agent framework", max_results=2)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], SearchResultDTO)
            assert "⭐" in results[0].title

    asyncio.run(_test())
