"""
tests/test_actions.py - 阶段 1: 动态 Agent 角色生成器单元测试

测试 choose_agent() 自动根据课题选择专家 Persona 人设与 Prompt。
"""

import asyncio
import pytest
from haven_research.actions import choose_agent


def test_choose_agent_persona():
    """验证 choose_agent 根据课题生成定制 Agent 角色"""
    async def _test():
        res = await choose_agent("2026 年大语言模型分布式训练最佳实践")
        assert isinstance(res, dict)
        assert "agent" in res
        assert "role" in res
        assert len(res["agent"]) > 0
        assert res["role"].startswith("你是一名")

    asyncio.run(_test())
