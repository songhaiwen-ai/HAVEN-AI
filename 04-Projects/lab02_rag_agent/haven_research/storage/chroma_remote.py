"""
haven_research/storage/chroma_remote.py - 生产级集群化 ChromaDB 远程 HTTP 客户端实现

【企业级生产架构】: 在实际生产上线环境（如 Kubernetes 容器集群或分布式服务端），
客服系统后端不将向量文件写在应用服务本地磁盘，而是通过 HTTP / gRPC 连接池连向远程独立的 ChromaDB 向量数据库集群。
"""

from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger, VectorStoreException
from haven_research.schemas.dto import TextChunkDTO
from .base import BaseVectorStore


class ChromaRemoteVectorStore(BaseVectorStore):
    """生产级集群化 ChromaDB 远程 HTTP 向量存储策略客户端"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        collection_name: str = None,
        ssl: bool = False,
        headers: Dict[str, str] = None
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name or settings.default_collection_name

        logger.info(f"[VectorStore Remote] 连接企业级远程向量数据库集群: http{'s' if ssl else ''}://{self.host}:{self.port} (集合: {self.collection_name})")

        try:
            import chromadb
            # 使用 HttpClient 连接远程独立部署的 ChromaDB 向量服务
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                ssl=ssl,
                headers=headers
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[VectorStore Remote] 远程向量集群集合 '{self.collection_name}' 连接成功 (当前日志条目数: {self.collection.count()})")

        except Exception as e:
            logger.error(f"[VectorStore Remote Error] 连接远程向量数据库集群失败: {e}")
            raise VectorStoreException(f"连接远程向量集群失败 (http://{self.host}:{self.port}): {str(e)}")

    def add_texts(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> List[str]:
        """向远程集群批量写入向量"""
        if not texts:
            return []

        try:
            import uuid
            vector_ids = ids or [f"doc_{uuid.uuid4().hex[:12]}" for _ in range(len(texts))]
            formatted_metadatas = metadatas or [{} for _ in range(len(texts))]

            cleaned_metadatas = []
            for meta in formatted_metadatas:
                cleaned_meta = {k: (v if v is not None else "") for k, v in meta.items()}
                cleaned_metadatas.append(cleaned_meta)

            self.collection.add(
                documents=texts,
                metadatas=cleaned_metadatas,
                ids=vector_ids
            )
            logger.info(f"[VectorStore Remote] 成功向远程向量数据库发送 {len(texts)} 条文本向量。")
            return vector_ids

        except Exception as e:
            logger.error(f"[VectorStore Remote Error] 远程向量写入失败: {e}")
            raise VectorStoreException(f"远程向量写入失败: {str(e)}")

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_metadata: Dict[str, Any] = None
    ) -> List[TextChunkDTO]:
        """向远程向量集群发送相似度检索请求"""
        if not query or not query.strip():
            return []

        try:
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
                    score = round(max(0.0, 1.0 - float(dist)), 4)
                    source_str = meta.get("source", "remote_db")
                    page_str = meta.get("page", 1)

                    chunk = TextChunkDTO(
                        url=f"企业向量集群({source_str} P.{page_str})",
                        content=doc,
                        score=score,
                        metadata=meta
                    )
                    chunks.append(chunk)

            logger.info(f"[VectorStore Remote] 远程检索完毕，集群返回 {len(chunks)} 条最佳匹配结果。")
            return chunks

        except Exception as e:
            logger.error(f"[VectorStore Remote Error] 远程检索失败: {e}")
            raise VectorStoreException(f"远程向量检索失败: {str(e)}")

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
