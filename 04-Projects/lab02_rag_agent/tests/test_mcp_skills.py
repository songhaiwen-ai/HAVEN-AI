"""
tests/test_mcp_skills.py - MCP (Model Context Protocol) 客户端与 Skills 技能框架单元测试

测试 SkillManager 自动扫描与元数据提取，以及 HavenMCPClient 工具注册与转换。
"""

import asyncio
import pytest
from haven_research.skills.manager import SkillManager
from haven_research.mcp.client import HavenMCPClient


def test_skill_manager_discovery(tmp_path):
    """验证 SkillManager 扫描 SKILL.md 技能说明书"""
    # 在临时路径创建一个标准 Skill
    skill_dir = tmp_path / "sample_skill"
    skill_dir.mkdir()
    md_file = skill_dir / "SKILL.md"
    md_file.write_text(
        "---\n"
        "name: calculate_cagr\n"
        "description: 复合年均增长率计算技能\n"
        "---\n"
        "技能指导说明...",
        encoding="utf-8"
    )

    mgr = SkillManager(skills_dir=str(tmp_path))
    discovered = mgr.discover_skills()

    assert "calculate_cagr" in discovered
    assert discovered["calculate_cagr"].description == "复合年均增长率计算技能"
    prompt = mgr.get_skill_instructions_prompt()
    assert "calculate_cagr" in prompt


def test_mcp_client():
    """验证 HavenMCPClient 工具发现与 Function Calling 格式转换"""
    async def _test():
        client = HavenMCPClient(server_name="test_server")
        tools = await client.connect_and_discover()
        assert len(tools) > 0

        openai_tools = client.get_openai_function_tools()
        assert len(openai_tools) == len(tools)
        assert openai_tools[0]["type"] == "function"
        assert "name" in openai_tools[0]["function"]

        res = await client.call_tool_async("query_mysql_database", {"sql": "SELECT 1"})
        assert res["success"] is True

    asyncio.run(_test())
