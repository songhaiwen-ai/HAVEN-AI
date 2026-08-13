"""
tests/test_memory.py - 重点 1: 三层记忆架构单元测试

测试 WorkingMemory (工作暂存), SessionMemory (会话滑动窗口与摘要), 
以及 LongTermMemory (Qdrant 长期偏好存取) 和 MemoryManager 调配能力。
"""

import pytest
from haven_research.memory import (
    WorkingMemory,
    SessionMemory,
    LongTermMemory,
    MemoryManager
)


def test_working_memory():
    """验证 WorkingMemory 临时 Scratchpad 记录与销毁"""
    wm = WorkingMemory()
    wm.add_step("SearchStep", "抓取了 5 条网页数据")
    wm.add_step("ParseStep", "完成 18 条向量切片")

    assert len(wm.get_all()) == 2
    scratchpad = wm.get_scratchpad_formatted()
    assert "SearchStep" in scratchpad
    assert "ParseStep" in scratchpad

    wm.clear()
    assert len(wm.get_all()) == 0


def test_session_memory():
    """验证 SessionMemory 多轮消息记录与 LLM 消息格式化"""
    sm = SessionMemory(session_id="test_session_101", max_window=4)
    sm.add_user_message("你好，请帮我研究 AI Agent 架构。")
    sm.add_assistant_message("好的，正在为您拆解子主题...")

    messages = sm.get_messages_for_llm()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_memory_manager():
    """验证 MemoryManager 三层记忆控制器组装 Context 能力"""
    mgr = MemoryManager(session_id="integration_test_session")
    
    mgr.record_working_step("Planner", "已拆解出 3 个子 Query")
    mgr.record_user_query("分析 2026 年大模型趋势")
    
    context = mgr.get_full_context_for_agent(query="大模型趋势")
    
    assert "Planner" in context["working_scratchpad"]
    assert len(context["session_messages"]) > 0
    assert "long_term_preferences" in context

    mgr.clear_working_memory()
    assert mgr.working_memory.get_scratchpad_formatted() == "无工作记忆记录"
