"""
haven_research/memory/base.py - 记忆模块基础接口与数据结构

定义 Worker/Session/Long-term 三层记忆的基类接口与强类型 DTO 结构。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """单条记忆单元 DTO"""
    id: str = Field(..., description="记忆唯一标识")
    memory_type: str = Field(..., description="记忆类型: working, session, long_term")
    content: str = Field(..., description="记忆文本内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="记忆附加元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="记忆创建时间")


class BaseMemory(ABC):
    """记忆组件统一抽象基类"""

    @abstractmethod
    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加一条记忆"""
        pass

    @abstractmethod
    def get_all(self) -> List[MemoryItem]:
        """获取当前组件存储的所有记忆"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空记忆"""
        pass
