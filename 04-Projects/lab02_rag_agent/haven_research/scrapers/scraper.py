"""
haven_research/scrapers/scraper.py - 生产级网页抓取与 HTML 文本去噪清洗器 (带 Jina 免爬降级)

【对标 gpt-researcher】: gpt_researcher/scraper/
基于 requests + BeautifulSoup4，内置 Jina Reader (https://r.jina.ai/) 抗反爬降级机制，
实现超时防护、User-Agent 动态轮询与 HTML 脚本标签去除。
"""

import asyncio
import re
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from haven_research.config import settings
from haven_research.core import logger, ScraperException
from haven_research.schemas.dto import ScrapedDocumentDTO


class WebScraper:
    """生产级网页抓取与去噪清洗器 (内置 Jina Reader 免爬防护)"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    ]

    def __init__(self, timeout: int = None):
        self.timeout = timeout or settings.scraper_timeout

    async def scrape_async(self, url: str, max_chars: int = 1500) -> ScrapedDocumentDTO:
        """
        异步方式并发抓取单页
        :param url: 目标 URL
        :param max_chars: 提取的最大字符长度
        :return: 经过 Pydantic 校验的 ScrapedDocumentDTO 对象
        """
        if not url or not url.startswith("http"):
            return ScrapedDocumentDTO(url=url, text="", error="无效的 URL")

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.scrape_sync, url, max_chars)

    def scrape_sync(self, url: str, max_chars: int = 1500) -> ScrapedDocumentDTO:
        """
        同步网页抓取、Jina 免爬降级与 HTML DOM 清洗
        """
        logger.info(f"[Scraper] 正在抓取网页: {url}")
        headers = {
            "User-Agent": self.USER_AGENTS[hash(url) % len(self.USER_AGENTS)],
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            resp.encoding = resp.apparent_encoding or "utf-8"

            # 如果遇到 403 / 401 反爬拦截，自动切入 Jina Reader 免爬引擎降级
            if resp.status_code in [403, 401, 429, 503]:
                logger.warning(f"[Scraper Warning] 网页遭遇反爬阻断 (HTTP {resp.status_code})，切入 Jina Reader 免爬引擎...")
                return self._scrape_via_jina(url, max_chars)

            if resp.status_code != 200:
                logger.warning(f"[Scraper Warning] 网页返回异常状态码 {resp.status_code}: {url}")
                return ScrapedDocumentDTO(url=url, text="", error=f"HTTP Status {resp.status_code}")

            # 解析 HTML 并删除 JavaScript, CSS, Navigation, Footer 等无意义噪音
            soup = BeautifulSoup(resp.text, "html.parser")
            for noise_tag in soup(["script", "style", "nav", "footer", "header", "iframe"]):
                noise_tag.decompose()

            # 提取纯正文文本
            raw_text = soup.get_text(separator="\n")
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            cleaned_text = "\n".join(lines)

            # 限制抓取正文最大字符长度
            truncated_text = cleaned_text[:max_chars]
            logger.info(f"[Scraper] 成功提取网页正文 (提取字符数: {len(truncated_text)}): {url}")

            return ScrapedDocumentDTO(url=url, text=truncated_text)

        except Exception as e:
            logger.warning(f"[Scraper Warning] 直连抓取异常 '{url}': {e}，尝试使用 Jina Reader 降级处理...")
            return self._scrape_via_jina(url, max_chars)

    def _scrape_via_jina(self, url: str, max_chars: int) -> ScrapedDocumentDTO:
        """Jina Reader 开源免爬引擎降级通道 (绕过 Cloudflare 防火墙)"""
        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(jina_url, headers=headers, timeout=self.timeout)
            if resp.status_code == 200 and resp.text:
                text = resp.text[:max_chars]
                logger.info(f"[Scraper Jina] 成功通过 Jina 免爬通道提取网页内容 ({len(text)} 字符): {url}")
                return ScrapedDocumentDTO(url=url, text=text)
        except Exception as je:
            logger.error(f"[Scraper Jina Error] Jina 免爬通道亦无法提取 '{url}': {je}")

        return ScrapedDocumentDTO(url=url, text="", error="网页反爬阻断且 Jina 提取失败")
