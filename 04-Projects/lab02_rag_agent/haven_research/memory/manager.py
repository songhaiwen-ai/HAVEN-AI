"""
haven_research/memory/manager.py - 三层记忆总控制器 (MemoryManager)

统一调度管理 WorkingMemory (工作记忆), SessionMemory (会话记忆), 与 LongTermMemory (长期记忆)，
为 Agent 提供一站式记忆存取与 Context 注入接口。
"""

from typing import List, Dict, Any, Optional
from haven_research.core import logger
from .working import WorkingMemory
from .session import SessionMemory
from .long_term import LongTermMemory


class MemoryManager:
    """三层记忆总控制器包面类 (Facade Pattern)"""

    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        
        self.working_memory = WorkingMemory()
        self.session_memory = SessionMemory(session_id=session_id)
        self.long_term_memory = LongTermMemory()
        
        logger.info(f"[MemoryManager] 三层记忆体系初始化成功 (SessionID: {self.session_id})")

    def record_working_step(self, step_name: str, data: Any):
        """记录单次研究任务的 Scratchpad 中间步骤"""
        return self.working_memory.add_step(step_name, data)

    def record_user_query(self, query: str):
        """记录用户输入的 Query"""
        return self.session_memory.add_user_message(query)

    def record_agent_response(self, response: str):
        """记录 Agent 生成的回复/报告"""
        return self.session_memory.add_assistant_message(response)

    def save_user_preference(self, preference: str, category: str = "preference"):
        """持久化保存用户个人偏好到 Qdrant 云端长期记忆"""
        return self.long_term_memory.add(content=preference, metadata={"category": category})

    def get_full_context_for_agent(self, query: str) -> Dict[str, Any]:
        """
        为 Agent 提炼并组合完整的上下文 (工作暂存 + 会话历史 + 长期记忆偏好)
        """
        # 1. 检索长期偏好
        lt_memories = self.long_term_memory.search_relevant_memory(query, k=2)
        
        # 2. 格式化工作记忆
        working_scratchpad = self.working_memory.get_scratchpad_formatted()
        
        # 3. 格式化会话记忆
        session_messages = self.session_memory.get_messages_for_llm()

        return {
            "working_scratchpad": working_scratchpad,
            "session_messages": session_messages,
            "long_term_preferences": lt_memories
        }

    def clear_working_memory(self):
        """任务完成后销毁工作记忆"""
        self.working_memory.clear()
