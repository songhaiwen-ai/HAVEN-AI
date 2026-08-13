"""
haven_research/retrievers/mcp.py - 生产级 MCP 架构数据检索器

【1:1 复现 gpt-researcher 检索器架构】: gpt_researcher/retrievers/mcp/retriever.py
把 Model Context Protocol (MCP) 连接抽象为标准 Agent Retriever，
实现两阶段检索工作流：
1. 阶段 1 (Tool Selection): 由 MCPToolSelector 精排挑选出 2-3 个最匹配的 MCP 工具。
2. 阶段 2 (Research Execution): 调起 MCP 工具执行查询，并包装为标准 SearchResultDTO 输出。
"""

from typing import List, Dict, Any, Optional
from haven_research.core import logger
from haven_research.schemas.dto import SearchResultDTO
from haven_research.mcp.client import HavenMCPClient
from haven_research.mcp.tool_selector import MCPToolSelector
from .base import BaseRetriever


class MCPRetriever(BaseRetriever):
    """【1:1 复现 gpt-researcher】基于 MCP 协议的智能检索器"""

    def __init__(self, mcp_client: Optional[HavenMCPClient] = None):
        self.mcp_client = mcp_client or HavenMCPClient()
        self.tool_selector = MCPToolSelector()
        logger.info("[Retriever] 初始化 MCP 协议标准检索器 (MCPRetriever)")

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultDTO]:
        """
        通过 MCP 协议发起两阶段智能研究检索
        """
        if not query or not query.strip():
            return []

        logger.info(f"[MCPRetriever] 正在通过 MCP 协议开启智能检索: '{query}'...")

        # 1. 建立 MCP 连接并动态发现可用工具表
        available_tools = await self.mcp_client.connect_and_discover()
        if not available_tools:
            logger.warning("[MCPRetriever Warning] 目标 MCP Server 未提供可用工具。")
            return []

        # 2. 阶段一：工具智能精排 (Two-Stage Tool Selection)
        selected_tools = await self.tool_selector.select_best_tools(query, available_tools, max_tools=2)
        
        # 3. 阶段二：调起精选 MCP 工具并执行查询
        results: List[SearchResultDTO] = []
        for tool in selected_tools:
            try:
                res = await self.mcp_client.call_tool_async(
                    tool_name=tool.name,
                    arguments={"query": query}
                )
                if res.get("success"):
                    results.append(
                        SearchResultDTO(
                            title=f"MCP Tool Output [{tool.name}]",
                            href=f"mcp://{self.mcp_client.server_name}/{tool.name}",
                            body=str(res.get("result", ""))
                        )
                    )
            except Exception as e:
                logger.error(f"[MCPRetriever Error] 执行 MCP 工具 [{tool.name}] 失败: {e}")

        logger.info(f"[MCPRetriever] MCP 两阶段检索完成！获得 {len(results)} 条智能工具研究数据。")
        return results
