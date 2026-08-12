"""
haven_research/storage/base.py - 向量数据库抽象基类

【对标 gpt-researcher】: gpt_researcher/vector_store/base.py
使用 Python ABC 策略模式，定义统一的向量存储与检索接口规范。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from haven_research.schemas.dto import TextChunkDTO


class BaseVectorStore(ABC):
    """向量存储策略抽象基类"""

    @abstractmethod
    def add_texts(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> List[str]:
        """
        向向量数据库批量写入文本与关联元数据
        :param texts: 文本切片列表
        :param metadatas: 对应的元数据字典列表 (如 source, page)
        :param ids: 唯一的向量 ID 列表 (可选)
        :return: 写入成功保存的矢量 ID 列表
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_metadata: Dict[str, Any] = None
    ) -> List[TextChunkDTO]:
        """
        在向量空间中执行相似度查询
        :param query: 查询意图文本
        :param k: 返回最相似的前 K 条结果
        :param filter_metadata: 元数据过滤条件 (可选)
        :return: 经过强类型封装的 TextChunkDTO 切片对象列表
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """返回当前数据库/集合中的总纪录数"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空当前向量集合数据"""
        pass
