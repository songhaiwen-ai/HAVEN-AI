"""
haven_research/planner/planner.py - 生产级 LLM 子主题拆解规划器

【对标 gpt-researcher】: gpt_researcher/actions/
调用 DeepSeek API (deepseek-chat)，将泛化研究课题结构化拆解为 N 个具体的搜索引擎 Query 子主题。
"""

import json
import asyncio
import openai
from typing import List
from haven_research.config import settings
from haven_research.core import logger, HavenAgentException
from .base import BasePlanner


class SubtopicPlanner(BasePlanner):
    """DeepSeek 驱动的智能子主题拆解器"""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model = settings.llm_model
        
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def plan_subtopics(self, query: str, max_subtopics: int = 3) -> List[str]:
        """
        利用 DeepSeek 智能拆解子主题
        """
        if not query or not query.strip():
            return []

        logger.info(f"[Planner] 正在调用 DeepSeek LLM ({self.model}) 拆解课题子意图: '{query}'")

        system_prompt = (
            "你是一名顶级深度研究专家与信息架构师。你的任务是将用户提出的研究课题拆解为多维度的子问题搜索关键词。\n"
            "要求：\n"
            "1. 拆解角度必须全面（例如：核心定义、技术架构、工业实践、挑战与趋势）。\n"
            "2. 输出格式必须严格为 JSON 字符串数组，格式为：[\"子搜索词1\", \"子搜索词2\", ...]\n"
            "3. 严禁输出任何 markdown 格式标记、解释性说明或除 JSON 以外的额外字符。"
        )

        user_prompt = f"请为以下研究课题拆解最多 {max_subtopics} 个具体的搜索引擎查询词：\n课题：{query}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )

            raw_content = response.choices[0].message.content.strip()
            # 提取 JSON 文本
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]
            raw_content = raw_content.strip()

            subtopics = json.loads(raw_content)
            if isinstance(subtopics, list) and len(subtopics) > 0:
                logger.info(f"[Planner] 成功拆解出 {len(subtopics)} 个精准搜索 Query: {subtopics}")
                return subtopics[:max_subtopics]

        except Exception as e:
            logger.warning(f"[Planner Warning] LLM 子主题拆解解析异常: {e}，切入保底拆解模式...")

        # 规则保底拆解
        return [
            f"{query} 核心原理与架构设计",
            f"{query} 企业级应用场景与工业实践",
            f"{query} 关键挑战与未来演进趋势"
        ][:max_subtopics]
