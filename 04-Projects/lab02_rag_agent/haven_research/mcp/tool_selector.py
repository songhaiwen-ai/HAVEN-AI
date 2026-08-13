"""
haven_research/mcp/tool_selector.py - MCP 工具智能精排选择器

【1:1 复现 gpt-researcher MCP 架构】: gpt_researcher/mcp/tool_selector.py
两阶段工具路由 (Two-Stage Approach):
当连接的 MCP Servers 包含几十上百个 Tools 时，首先调用 DeepSeek API
根据当前研究 Query 精选出最匹配的 2-3 个 MCP Tools，避免全部绑定造成 Token 爆炸与干扰。
"""

import json
import openai
from typing import List, Dict, Any
from haven_research.config import settings
from haven_research.core import logger
from .client import MCPToolSchemaDTO


class MCPToolSelector:
    """MCP 工具智能精排器"""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )

    async def select_best_tools(
        self,
        query: str,
        available_tools: List[MCPToolSchemaDTO],
        max_tools: int = 3
    ) -> List[MCPToolSchemaDTO]:
        """
        根据用户课题，从所有 MCP 外部工具中精选出最匹配的 2-3 个工具
        """
        if not available_tools:
            return []

        if len(available_tools) <= max_tools:
            return available_tools

        logger.info(f"[MCPToolSelector] (阶段 1) 正在从 {len(available_tools)} 个 MCP 工具中为课题 '{query}' 智能精排最相关的 {max_tools} 个工具...")

        tool_descriptions = [f"- {t.name}: {t.description}" for t in available_tools]
        tools_str = "\n".join(tool_descriptions)

        prompt = (
            f"你是一名 MCP 智能工具选择专家。\n"
            f"研究课题：'{query}'\n"
            f"以下是可用的 MCP 外部工具库：\n{tools_str}\n\n"
            f"请挑选出解决该课题最关键的 1~{max_tools} 个工具名称。\n"
            f"仅输出 JSON 字符串数组，例如：[\"tool_a\", \"tool_b\"]"
        )

        try:
            resp = await self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            selected_names = json.loads(raw)
            if isinstance(selected_names, list):
                selected_tools = [t for t in available_tools if t.name in selected_names]
                if selected_tools:
                    logger.info(f"[MCPToolSelector] 成功精排出 Top {len(selected_tools)} MCP 工具: {[t.name for t in selected_tools]}")
                    return selected_tools
        except Exception as e:
            logger.warning(f"[MCPToolSelector Warning] 工具精排失败 ({e})，退避取前 {max_tools} 个工具。")

        return available_tools[:max_tools]
