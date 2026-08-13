"""
haven_research/mcp/arxiv_mcp.py - ArXiv 前沿学术论文 MCP 集成客户端

【完全免费零 Key 需求】:
通过 ArXiv 开放 API (export.arxiv.org/api/query) 检索最新的 AI / RAG / Agent 顶级学术论文，
自动提取论文标题、作者、发布日期、摘要与 PDF 原文链接。
"""

import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from typing import List, Dict, Any
from haven_research.core import logger
from haven_research.schemas.dto import SearchResultDTO


class ArXivMCPClient:
    """ArXiv 学术论文 MCP 客户端"""

    BASE_URL = "http://export.arxiv.org/api/query"

    async def search_papers_async(self, query: str, max_results: int = 5) -> List[SearchResultDTO]:
        """
        检索 arXiv.org 最新前沿学术论文
        :param query: 论文搜索主题 (如 "RAG Agent Architecture")
        :param max_results: 检索条数
        :return: SearchResultDTO 列表
        """
        if not query or not query.strip():
            return []

        logger.info(f"[ArXivMCP] 正在检索 arXiv.org 学术论文库: '{query}' (max_results: {max_results})...")
        
        search_query = f"all:{query}"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                
            xml_data = resp.text
            results = self._parse_arxiv_xml(xml_data)
            logger.info(f"[ArXivMCP] ArXiv 检索成功！返回 {len(results)} 篇最新学术论文。")
            return results

        except Exception as e:
            logger.error(f"[ArXivMCP Error] ArXiv 论文检索失败: {e}")
            return []

    def _parse_arxiv_xml(self, xml_str: str) -> List[SearchResultDTO]:
        """解析 ArXiv Atom XML 响应"""
        results = []
        try:
            root = ET.fromstring(xml_str)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                published = entry.find("atom:published", ns).text[:10]
                
                pdf_url = ""
                for link in entry.findall("atom:link", ns):
                    if link.attrib.get("title") == "pdf":
                        pdf_url = link.attrib.get("href", "")

                results.append(
                    SearchResultDTO(
                        title=f"[ArXiv {published}] {title}",
                        href=pdf_url or entry.find("atom:id", ns).text,
                        body=f"发表时间: {published} | 论文摘要: {summary[:400]}..."
                    )
                )
        except Exception as e:
            logger.error(f"[ArXivMCP Error] XML 解析异常: {e}")

        return results
