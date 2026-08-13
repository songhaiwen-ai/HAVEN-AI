"""
haven_research/actions/agent_creator.py - 动态 Agent 角色定制生成器

【1:1 对标 gpt-researcher】: gpt_researcher/actions/agent_creator.py
调用 DeepSeek LLM (deepseek-chat)，根据用户给出的研究课题自动推理并定制
最具针对性的专家 Persona 角色名称与 Prompt 设想说明。
"""

import json
import asyncio
import openai
from typing import Dict, Any
from haven_research.config import settings
from haven_research.core import logger


async def choose_agent(query: str, cfg: Any = None) -> Dict[str, str]:
    """
    根据用户 Query 动态确定最佳 Agent 专家人设
    :param query: 研究课题
    :return: 包含 agent (名称) 与 role (人设设定 Prompt) 的字典
    """
    if not query or not query.strip():
        return {
            "agent": "通用技术研究专家",
            "role": "你是一名资深通用技术研究专家，负责生成客观、详实的研究报告。"
        }

    logger.info(f"[AgentCreator] 正在调用 DeepSeek LLM 为课题 '{query}' 动态生成专精 Persona 人设...")

    system_prompt = (
        "你是一名 Agent 人设专家。你的任务是根据给出的研究课题，为 AI Agent 匹配最专业的专家角色人设。\n"
        "要求：\n"
        "1. 输出格式必须严格为 JSON 对象，包含 'agent' (角色名称) 和 'role' (人设指导 Prompt) 两个字段。\n"
        "2. 'agent' 必须具体且专业（例如：'资深 AI 架构师'、'半导体行业高级分析师'）。\n"
        "3. 'role' 必须以 '你是一名...' 开头，明确其分析视角与专业原则。\n"
        "4. 严禁输出任何 markdown 标记或除 JSON 以外的额外字符。"
    )

    user_prompt = f"研究课题：{query}\n请生成该课题的最佳 Agent 角色与人设 Prompt："

    client = openai.AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url
    )

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        raw_content = response.choices[0].message.content.strip()
        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
        raw_content = raw_content.strip()

        agent_data = json.loads(raw_content)
        if isinstance(agent_data, dict) and "agent" in agent_data and "role" in agent_data:
            logger.info(f"[AgentCreator] 成功生成动态 Persona: 【{agent_data['agent']}】")
            return agent_data

    except Exception as e:
        logger.warning(f"[AgentCreator Warning] 动态 Persona 生成失败 ({e})，切入通用角色...")

    return {
        "agent": "首席技术研究员",
        "role": f"你是一名首席技术研究员，专注于对 '{query}' 进行客观、严谨、深度的行业与技术分析。"
    }
