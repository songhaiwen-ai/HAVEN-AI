"""
haven_research/memory/working.py - 单任务工作记忆 (Working Memory / Scratchpad)

作为 Agent 单次研究任务执行期间的临时思考与中间结果暂存区 (Scratchpad)，
任务完成后自动清空销毁，防止跨任务污染。
"""

import uuid
from typing import List, Dict, Any, Optional
from haven_research.core import logger
from .base import BaseMemory, MemoryItem


class WorkingMemory(BaseMemory):
    """单任务临时思考与中间步骤工作记忆 (Scratchpad)"""

    def __init__(self):
        self._items: List[MemoryItem] = []
        logger.info("[Memory] 初始化 WorkingMemory 工作记忆暂存区")

    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """记录中间推理或步骤数据"""
        mem_id = str(uuid.uuid4())[:8]
        item = MemoryItem(
            id=mem_id,
            memory_type="working",
            content=content,
            metadata=metadata or {}
        )
        self._items.append(item)
        logger.debug(f"[WorkingMemory] 写入工作记忆暂存项: ID={mem_id}, 描述='{content[:40]}'")
        return mem_id

    def add_step(self, step_name: str, data: Any) -> str:
        """结构化记录中间步骤"""
        content_str = f"[{step_name}] {data}"
        return self.add(content=content_str, metadata={"step_name": step_name, "raw_data": str(data)})

    def get_all(self) -> List[MemoryItem]:
        """获取当前工作记忆中所有记录"""
        return self._items

    def get_scratchpad_formatted(self) -> str:
        """获取格式化后的 Scratchpad 字符串，方便作为 Prompt 喂给 LLM"""
        if not self._items:
            return "无工作记忆记录"
        
        lines = []
        for idx, item in enumerate(self._items, 1):
            step = item.metadata.get("step_name", "思考步骤")
            lines.append(f"步骤 {idx} ({step}): {item.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        """任务结束销毁暂存区"""
        count = len(self._items)
        self._items.clear()
        logger.info(f"[WorkingMemory] 工作记忆已销毁 (释放 {count} 项记录)")
