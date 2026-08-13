"""
haven_research/memory/session.py - 会话记忆 (Session Memory)

维护多轮对话与交互历史上下文。
内置“固定滑动窗口 (Sliding Window)”与“DeepSeek LLM 自动摘要压缩 (Summary Memory)”机制，
防止长会话导致 Token 溢出与注意力分散。
"""

import uuid
import asyncio
import openai
from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger
from .base import BaseMemory, MemoryItem


class SessionMemory(BaseMemory):
    """带滑动窗口与 LLM 摘要压缩的会话记忆组件"""

    def __init__(self, session_id: str = "default_session", max_window: int = 10):
        self.session_id = session_id
        self.max_window = max_window
        self._messages: List[Dict[str, str]] = []
        self._summary: str = ""
        
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        logger.info(f"[Memory] 初始化 SessionMemory 会话记忆 (SessionID: {self.session_id}, 窗口上限: {self.max_window})")

    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加对话消息 (role 包含在 metadata 中，默认 user)"""
        role = (metadata or {}).get("role", "user")
        self._messages.append({"role": role, "content": content})
        
        mem_id = str(uuid.uuid4())[:8]
        logger.debug(f"[SessionMemory] 记录会话消息: [{role}] '{content[:30]}...'")

        # 触发窗口超限保护
        if len(self._messages) > self.max_window:
            logger.info(f"[SessionMemory] 会话条数 ({len(self._messages)}) 超过上限 ({self.max_window})，触发摘要压缩机制...")
            asyncio.create_task(self.compress_summary_async())

        return mem_id

    def add_user_message(self, content: str):
        return self.add(content, {"role": "user"})

    def add_assistant_message(self, content: str):
        return self.add(content, {"role": "assistant"})

    async def compress_summary_async(self) -> str:
        """异步调用 DeepSeek LLM 对被剪裁的老会话进行增量摘要压缩"""
        if len(self._messages) <= self.max_window // 2:
            return self._summary

        # 提取要被移除的前半部分旧消息
        cutoff = len(self._messages) - (self.max_window // 2)
        old_messages = self._messages[:cutoff]
        self._messages = self._messages[cutoff:]

        old_dialogue_str = "\n".join([f"{m['role']}: {m['content']}" for m in old_messages])
        
        prompt = (
            f"你是一名专业的大模型会话历史摘要专家。\n"
            f"已有的历史摘要: '{self._summary}'\n"
            f"新增需压缩的对话记录:\n{old_dialogue_str}\n\n"
            f"请将上述对话融合成一段简明扼要的综合上下文摘要，保留关键事实、要求与已知结论。"
        )

        try:
            resp = await self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            self._summary = resp.choices[0].message.content.strip()
            logger.info(f"[SessionMemory] 成功更新会话历史摘要: '{self._summary[:50]}...'")
        except Exception as e:
            logger.warning(f"[SessionMemory Warning] 会话摘要压缩异常: {e}")

        return self._summary

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """获取直接供 LLM 调用的格式化消息数组（包含摘要 System Message + 最新消息）"""
        formatted = []
        if self._summary:
            formatted.append({
                "role": "system",
                "content": f"【历史对话综合摘要】: {self._summary}"
            })
        formatted.extend(self._messages)
        return formatted

    def get_all(self) -> List[MemoryItem]:
        """转换为 MemoryItem 标准列表"""
        items = []
        for idx, m in enumerate(self._messages):
            items.append(
                MemoryItem(
                    id=f"{self.session_id}_{idx}",
                    memory_type="session",
                    content=m["content"],
                    metadata={"role": m["role"], "session_id": self.session_id}
                )
            )
        return items

    def clear(self) -> None:
        self._messages.clear()
        self._summary = ""
        logger.info(f"[SessionMemory] 会话 {self.session_id} 记忆已清空")
