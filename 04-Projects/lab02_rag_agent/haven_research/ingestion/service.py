"""
haven_research/ingestion/service.py - 本地知识库文件提取与 Qdrant 向量落盘服务

解析本地指定目录或单个文件 (.pdf, .docx, .md, .txt) 提取干货正文，
调用 SemanticTextSplitter 语义切片，并自动批量写入 Qdrant Cloud / Chroma 向量数据库完成持久化落盘。
"""

import os
from typing import List, Dict, Any, Optional
from haven_research.config import settings
from haven_research.core import logger, DocumentParsingException
from haven_research.ingestion.loaders import DocumentLoader
from haven_research.ingestion.splitter import SemanticTextSplitter
from haven_research.storage import VectorStoreFactory, BaseVectorStore


class LocalKnowledgeIngestionService:
    """本地多格式文件自动解析与 Qdrant/Chroma 向量持久化落盘服务"""

    def __init__(self, vector_store: Optional[BaseVectorStore] = None):
        self.loader = DocumentLoader()
        self.splitter = SemanticTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.vector_store = vector_store or VectorStoreFactory.get_vector_store(settings.vector_store_type)
        logger.info(f"[IngestionService] 初始化本地知识库落盘服务 (向量库类型: {settings.vector_store_type})")

    def ingest_file(self, file_path: str, extra_metadata: Dict[str, Any] = None) -> int:
        """
        解析单个文件并持久化切片落盘入 Qdrant
        :param file_path: 文件绝对/相对路径
        :param extra_metadata: 附加元数据 (如 user_id, category)
        :return: 成功落盘入库的向量切片条数
        """
        logger.info(f"[IngestionService] 开始读取并解析文件: {file_path}")
        pages = self.loader.load_document(file_path)
        if not pages:
            logger.warning(f"[IngestionService Warning] 文件 '{file_path}' 未提取出有效干货内容。")
            return 0

        all_texts: List[str] = []
        all_metadatas: List[Dict[str, Any]] = []
        meta_base = extra_metadata or {}

        for page in pages:
            content = page["content"]
            page_meta = page["metadata"]

            # 执行语义切片
            chunks = self.splitter.split_text(content)
            for chunk in chunks:
                all_texts.append(chunk)
                merged_meta = {
                    **page_meta,
                    **meta_base,
                    "length": len(chunk)
                }
                all_metadatas.append(merged_meta)

        if not all_texts:
            return 0

        # 批量向量化并持久化写入 Qdrant/Chroma
        logger.info(f"[IngestionService] 正在将 {len(all_texts)} 个切片批量持久化落盘入 Qdrant 向量库...")
        ids = self.vector_store.add_texts(texts=all_texts, metadatas=all_metadatas)
        logger.info(f"[IngestionService] 🎉 文件 '{os.path.basename(file_path)}' 成功落盘 {len(ids)} 条切片向量！")
        return len(ids)

    def ingest_directory(self, dir_path: str, extra_metadata: Dict[str, Any] = None) -> Dict[str, int]:
        """
        扫描并批量解析整个目录下的所有 PDF / MD / Text 文件落盘入库
        """
        if not os.path.exists(dir_path):
            raise DocumentParsingException(f"指定的扫描目录不存在: {dir_path}")

        logger.info(f"[IngestionService] 开始扫描目录: {dir_path}")
        summary = {}
        supported_exts = [".pdf", ".md", ".txt", ".docx"]

        for root, _, files in os.walk(dir_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_exts:
                    full_path = os.path.join(root, file)
                    try:
                        count = self.ingest_file(full_path, extra_metadata=extra_metadata)
                        summary[file] = count
                    except Exception as e:
                        logger.error(f"[IngestionService Error] 处理文件 {file} 失败: {e}")
                        summary[file] = 0

        total_chunks = sum(summary.values())
        logger.info(f"[IngestionService] 目录 '{dir_path}' 批量落盘完成！处理文件数: {len(summary)}, 总向量点数: {total_chunks}")
        return summary
