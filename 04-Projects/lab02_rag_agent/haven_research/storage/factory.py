"""
haven_research/storage/factory.py - 生产级向量数据库工厂类

【对标 gpt-researcher】: gpt_researcher/vector_store/factory.py
实现策略模式 + 工厂模式，根据配置动态无缝切换：
1. 生产首选：Qdrant Cloud 云端 Serverless 集群 (qdrant)
2. 本地单机开发模式 (chroma_local)
3. 生产私有化部署 (chroma_remote)
"""

from haven_research.config import settings
from haven_research.core import logger, ConfigurationException
from .base import BaseVectorStore
from .chroma import ChromaVectorStore
from .chroma_remote import ChromaRemoteVectorStore
from .qdrant import QdrantVectorStore


class VectorStoreFactory:
    """向量数据库工厂对象"""

    @staticmethod
    def get_vector_store(
        store_type: str = None,
        collection_name: str = None,
        persist_dir: str = None,
        host: str = None,
        port: int = None,
        qdrant_url: str = None,
        qdrant_api_key: str = None
    ) -> BaseVectorStore:
        """
        获取向量存储客户端实例 (根据配置自动适配 Qdrant Cloud / Chroma)
        """
        stype = (store_type or settings.vector_store_type).lower()
        cname = collection_name or settings.default_collection_name

        # 1. 匹配 Qdrant Cloud 云端数据库或内存模式
        if stype in ["qdrant", "qdrant_cloud", "memory", ":memory:", "in_memory"]:
            qurl = qdrant_url or (":memory:" if stype in ["memory", ":memory:", "in_memory"] else settings.qdrant_url)
            qkey = qdrant_api_key or settings.qdrant_api_key
            logger.info(f"[Factory] 实例化 Qdrant 存储客户端 (URL: {qurl})")
            return QdrantVectorStore(url=qurl, api_key=qkey, collection_name=cname)

        # 2. 单机开发环境：Chroma Local
        elif stype in ["chroma", "chroma_local", "local"]:
            pdir = persist_dir or settings.vector_store_dir
            logger.info(f"[Factory] 实例化本地开发向量存储库 (Chroma Local)")
            return ChromaVectorStore(collection_name=cname, persist_dir=pdir)

        # 3. 生产私有化环境：Chroma Remote Server
        elif stype in ["chroma_remote", "chroma_http", "remote", "http"]:
            rhost = host or settings.vector_store_host
            rport = port or settings.vector_store_port
            logger.info(f"[Factory] 实例化远程向量服务 (Chroma Remote Server: http://{rhost}:{rport})")
            return ChromaRemoteVectorStore(host=rhost, port=rport, collection_name=cname)

        else:
            logger.error(f"[Factory Error] 暂不支持的向量数据库类型: '{stype}'")
            raise ConfigurationException(f"不支持的向量数据库类型: {stype}")
