"""
haven_research/memory/long_term.py - 长期记忆 (Long-term Memory)

基于 Qdrant Cloud 云端 Serverless 向量数据库，
持久化跨 Session / 跨项目的用户个人偏好（如编程语言、代码规范、领域排版偏好）以及历史研究报告索引。
"""

import uuid
from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger
from haven_research.storage import VectorStoreFactory
from .base import BaseMemory, MemoryItem


class LongTermMemory(BaseMemory):
    """基于 Qdrant Cloud 的向量化长期记忆组件"""

    def __init__(self, collection_name: str = "user_long_term_memory"):
        self.collection_name = collection_name
        self.vector_store = VectorStoreFactory.get_vector_store(
            store_type=settings.vector_store_type,
            collection_name=self.collection_name
        )
        logger.info(f"[Memory] 初始化 LongTermMemory 长期记忆 (存储集合: {self.collection_name})")

    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """持久化写入一条长期偏好或事实知识"""
        meta = metadata or {}
        meta["category"] = meta.get("category", "user_preference")
        
        ids = self.vector_store.add_texts(
            texts=[content],
            metadatas=[meta]
        )
        mem_id = ids[0] if ids else str(uuid.uuid4())
        logger.info(f"[LongTermMemory] 成功向 Qdrant 写入长期记忆: '{content[:40]}...' (ID: {mem_id})")
        return mem_id

    def search_relevant_memory(self, query: str, k: int = 3) -> List[str]:
        """通过余弦相似度检索相关的长期偏好与历史知识"""
        chunks = self.vector_store.similarity_search(query=query, k=k)
        results = [c.content for c in chunks]
        logger.info(f"[LongTermMemory] 围绕 '{query}' 检索出 {len(results)} 条长期记忆知识。")
        return results

    def get_all(self) -> List[MemoryItem]:
        """获取所有存盘的长期记忆单元"""
        # 统计数量
        count = self.vector_store.count()
        return [
            MemoryItem(
                id="long_term_collection",
                memory_type="long_term",
                content=f"Qdrant 长期向量库集合 '{self.collection_name}' (总记录数: {count})",
                metadata={"count": count}
            )
        ]

    def clear(self) -> None:
        self.vector_store.clear()
        logger.info(f"[LongTermMemory] 长期记忆集合 '{self.collection_name}' 已清空")
