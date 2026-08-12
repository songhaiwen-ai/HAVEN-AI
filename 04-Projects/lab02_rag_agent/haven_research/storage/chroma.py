"""
haven_research/storage/chroma.py - ChromaDB 磁盘持久化向量数据库实现

【对标 gpt-researcher】: gpt_researcher/vector_store/chroma.py
使用 chromadb.PersistentClient 实现支持本地磁盘落盘与余弦相似度检索的向量数据库。
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger, VectorStoreException
from haven_research.schemas.dto import TextChunkDTO
from .base import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB 磁盘持久化向量数据库"""

    def __init__(
        self,
        collection_name: str = None,
        persist_dir: str = None
    ):
        self.collection_name = collection_name or settings.default_collection_name
        self.persist_dir = os.path.abspath(persist_dir or settings.vector_store_dir)

        logger.info(f"[VectorStore] 初始化 ChromaDB 磁盘持久化库 (目录: {self.persist_dir}, 集合: {self.collection_name})")

        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            # 配置使用余弦相似度 (cosine) 作为向量空间距离函数
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[VectorStore] ChromaDB 集合 '{self.collection_name}' 已成功加载 (当前纪录数: {self.collection.count()})")

        except Exception as e:
            logger.error(f"[VectorStore Error] 初始化 ChromaDB 失败: {e}")
            raise VectorStoreException(f"ChromaDB 初始化失败: {str(e)}")

    def add_texts(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> List[str]:
        """批量写入文本向量"""
        if not texts:
            return []

        try:
            vector_ids = ids or [f"doc_{uuid.uuid4().hex[:12]}" for _ in range(len(texts))]
            formatted_metadatas = metadatas or [{} for _ in range(len(texts))]

            # 确保元数据中没有任何 Python None 字段，符合 ChromaDB 格式约束
            cleaned_metadatas = []
            for meta in formatted_metadatas:
                cleaned_meta = {k: (v if v is not None else "") for k, v in meta.items()}
                cleaned_metadatas.append(cleaned_meta)

            self.collection.add(
                documents=texts,
                metadatas=cleaned_metadatas,
                ids=vector_ids
            )
            logger.info(f"[VectorStore] 成功向 ChromaDB 写入 {len(texts)} 条向量切片。")
            return vector_ids

        except Exception as e:
            logger.error(f"[VectorStore Error] 向量写入失败: {e}")
            raise VectorStoreException(f"写入向量数据失败: {str(e)}")

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_metadata: Dict[str, Any] = None
    ) -> List[TextChunkDTO]:
        """执行余弦相似度检索"""
        if not query or not query.strip():
            return []

        try:
            logger.debug(f"[VectorStore] 正在检索 Top-{k} 相似切片: '{query}'")
            results = self.collection.query(
                query_texts=[query],
                n_results=min(k, max(1, self.collection.count())),
                where=filter_metadata
            )

            chunks = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

                for doc, meta, dist in zip(docs, metas, distances):
                    # Chroma 余弦距离转换为相似度得分: score = 1 - distance
                    score = round(max(0.0, 1.0 - float(dist)), 4)
                    source_str = meta.get("source", "local_db")
                    page_str = meta.get("page", 1)

                    chunk = TextChunkDTO(
                        url=f"本地知识库({source_str} P.{page_str})",
                        content=doc,
                        score=score,
                        metadata=meta
                    )
                    chunks.append(chunk)

            logger.info(f"[VectorStore] 检索完毕，找到 {len(chunks)} 条高匹配向量切片。")
            return chunks

        except Exception as e:
            logger.error(f"[VectorStore Error] 向量检索失败: {e}")
            raise VectorStoreException(f"向量检索失败: {str(e)}")

    def count(self) -> int:
        """返回记录数"""
        return self.collection.count()

    def clear(self) -> None:
        """清空数据"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[VectorStore] 集合 '{self.collection_name}' 已成功清空。")
        except Exception as e:
            raise VectorStoreException(f"清空向量集合失败: {str(e)}")
