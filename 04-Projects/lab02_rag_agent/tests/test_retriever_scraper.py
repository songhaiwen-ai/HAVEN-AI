"""
tests/test_retriever_scraper.py - 异步网络检索器与 HTML 抓取清洗器单元测试

测试 DuckDuckGoRetriever 异步搜索与 WebScraper 网页抓取去噪能力。
"""

import asyncio
import pytest
from haven_research.retrievers import DuckDuckGoRetriever
from haven_research.scrapers import WebScraper
from haven_research.schemas.dto import SearchResultDTO, ScrapedDocumentDTO


def test_duckduckgo_retriever():
    """验证 DuckDuckGo 异步网络检索能力与 DTO 数据转换"""
    async def _test():
        retriever = DuckDuckGoRetriever()
        results = await retriever.search("AI Agent 架构设计", max_results=2)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], SearchResultDTO)
            assert results[0].href.startswith("http")

    asyncio.run(_test())


def test_web_scraper():
    """验证 WebScraper HTML DOM 去噪与正文提取"""
    async def _test():
        scraper = WebScraper(timeout=5)
        res = await scraper.scrape_async("https://www.python.org", max_chars=300)
        assert isinstance(res, ScrapedDocumentDTO)
        assert res.url == "https://www.python.org"
        if not res.error:
            assert len(res.text) > 0
            assert len(res.text) <= 300

    asyncio.run(_test())
