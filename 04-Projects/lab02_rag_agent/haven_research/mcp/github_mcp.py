"""
haven_research/mcp/github_mcp.py - GitHub 开源项目代码库 MCP 集成客户端

【支持 GITHUB_TOKEN 配置】:
连接 GitHub REST API (api.github.com)，允许 Agent 检索最火的开源 AI / RAG / Agent 仓库
(如 LangChain, Qdrant, AutoGen, DeepSeek, gpt-researcher)，自动调取 Readme、Star 数与源码文件。
"""

import os
import httpx
from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger
from haven_research.schemas.dto import SearchResultDTO


class GitHubMCPClient:
    """GitHub 开源代码库 MCP 客户端"""

    BASE_URL = "https://api.github.com"

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN") or getattr(settings, "github_token", None)
        if self.github_token:
            logger.info("[GitHubMCP] 成功加载 GITHUB_TOKEN")
        else:
            logger.info("[GitHubMCP] 未检测到 GITHUB_TOKEN，将以匿名限制速率模式访问 GitHub API")

    async def search_repositories_async(self, query: str, max_results: int = 5) -> List[SearchResultDTO]:
        """
        检索 GitHub 开源仓库
        :param query: 搜索项目主题 (如 "agent framework")
        :param max_results: 返回结果数
        :return: SearchResultDTO 列表
        """
        if not query or not query.strip():
            return []

        logger.info(f"[GitHubMCP] 正在检索 GitHub 开源仓库: '{query}'...")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        params = {
            "q": f"{query} stars:>100",
            "sort": "stars",
            "order": "desc",
            "per_page": max_results
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/search/repositories", headers=headers, params=params)
                resp.raise_for_status()

            data = resp.json()
            items = data.get("items", [])
            results = []

            for item in items:
                name = item.get("full_name", "")
                stars = item.get("stargazers_count", 0)
                desc = item.get("description", "") or "暂无描述"
                url = item.get("html_url", "")
                lang = item.get("language", "Unspecified")

                results.append(
                    SearchResultDTO(
                        title=f"[GitHub {stars}⭐] {name} ({lang})",
                        href=url,
                        body=f"Star数: {stars}⭐ | 主要语言: {lang} | 项目描述: {desc}"
                    )
                )

            logger.info(f"[GitHubMCP] GitHub 检索成功！获得 {len(results)} 个热门开源项目。")
            return results

        except Exception as e:
            logger.error(f"[GitHubMCP Error] GitHub 检索失败: {e}")
            return []

    @staticmethod
    def parse_github_url(url: str) -> Optional[Dict[str, str]]:
        """从 GitHub URL 中解析出 owner 和 repo"""
        import re
        match = re.search(r"github\.com/([^/]+)/([^/?#]+)", url)
        if match:
            return {"owner": match.group(1), "repo": match.group(2).rstrip(".git")}
        return None

    async def get_repository_details_async(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        通过 GitHub REST API 真实抓取指定开源仓库的元数据 (包含最新 commit 时间 pushed_at, star 数, 描述, Readme)
        """
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        logger.info(f"[GitHubMCP] 正在通过 GitHub API 真实请求仓库数据: {owner}/{repo}...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/repos/{owner}/{repo}", headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"[GitHubMCP] 仓库 {owner}/{repo} API 返回 HTTP {resp.status_code}")
                    return None
                repo_data = resp.json()

                # 尝试真实抓取 README.md 内容
                readme_content = ""
                try:
                    r_resp = await client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/readme", headers=headers)
                    if r_resp.status_code == 200:
                        import base64
                        raw_b64 = r_resp.json().get("content", "")
                        readme_content = base64.b64decode(raw_b64).decode("utf-8", errors="ignore")[:2500]
                except Exception as re_err:
                    logger.warning(f"[GitHubMCP] Readme 抓取略过: {re_err}")

                return {
                    "full_name": repo_data.get("full_name"),
                    "description": repo_data.get("description") or "暂无描述",
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                    "pushed_at": repo_data.get("pushed_at"),  # 真实的最新 Commit 提交时间 (如 2026-08-18T10:00:00Z)
                    "updated_at": repo_data.get("updated_at"),
                    "default_branch": repo_data.get("default_branch", "main"),
                    "language": repo_data.get("language", "Unspecified"),
                    "html_url": repo_data.get("html_url"),
                    "readme": readme_content
                }
        except Exception as e:
            logger.error(f"[GitHubMCP Error] 真实抓取仓库 {owner}/{repo} 失败: {e}")
            return None
