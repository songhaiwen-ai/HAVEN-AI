"""
batch_ingest_all.py - 批量解析 PDF 电子书与 Markdown 技术文档并持久化落盘入 Qdrant Cloud

读取：
1. C:\baidunetdiskdownload\电子书 (107 本 AI / LLM / RAG / Agent 高质量 PDF 电子书)
2. c:\Haven-AI (全部 Markdown 架构与技术文档)

提取 -> 语义切片 -> 向量化 -> 批量落盘 Qdrant Cloud (agent_knowledge_base)
"""

import os
import sys
import time

# 自动将当前项目根目录加入 sys.path，防止 PyCharm 导包标红
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from haven_research.core import logger
from haven_research.ingestion import LocalKnowledgeIngestionService
from haven_research.storage import VectorStoreFactory


def run_batch_ingestion():
    logger.info("=== 🚀 启动 HavenResearch 知识库批量向量化落盘任务 ===")

    # 实例化 Qdrant VectorStore 与 Ingestion Service
    store = VectorStoreFactory.get_vector_store("qdrant")
    service = LocalKnowledgeIngestionService(vector_store=store)

    # --------------------------------------------------------------------------
    # 任务 1: 解析并落盘 c:\Haven-AI\ 根目录下所有的 Markdown 技术文档
    # --------------------------------------------------------------------------
    workspace_dir = "c:\\Haven-AI"
    logger.info(f"--- 任务 1: 开始扫描工作区 Markdown 文档: {workspace_dir} ---")
    md_count = 0
    total_md_chunks = 0

    for root, _, files in os.walk(workspace_dir):
        # 排除 .venv, .git 等依赖目录
        if ".venv" in root or ".git" in root or "__pycache__" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                try:
                    chunks_count = service.ingest_file(full_path, extra_metadata={"category": "workspace_tech_docs", "source_type": "markdown"})
                    if chunks_count > 0:
                        md_count += 1
                        total_md_chunks += chunks_count
                except Exception as e:
                    logger.error(f"[Ingest Warning] 解析 Markdown 文件 '{file}' 失败: {e}")

    logger.info(f"--- 任务 1 完成！成功解析 {md_count} 个 Markdown 技术文档，落盘 {total_md_chunks} 条切片向量到 Qdrant ---")

    # --------------------------------------------------------------------------
    # 任务 2: 解析并落盘 C:\baidunetdiskdownload\电子书 下所有的 PDF 电子书
    # --------------------------------------------------------------------------
    pdf_dir = r"C:\baidunetdiskdownload\电子书"
    logger.info(f"--- 任务 2: 开始扫描 PDF 电子书目录: {pdf_dir} ---")
    
    if os.path.exists(pdf_dir):
        pdf_count = 0
        total_pdf_chunks = 0
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        logger.info(f"在 '{pdf_dir}' 中发现 {len(pdf_files)} 本 PDF 电子书。开始逐一解析落盘...")

        for idx, file in enumerate(pdf_files, 1):
            full_path = os.path.join(pdf_dir, file)
            logger.info(f"[{idx}/{len(pdf_files)}] 正在解析 PDF 电子书: {file}...")
            try:
                chunks_count = service.ingest_file(full_path, extra_metadata={"category": "ebook_pdf", "source_type": "pdf"})
                if chunks_count > 0:
                    pdf_count += 1
                    total_pdf_chunks += chunks_count
            except Exception as e:
                logger.error(f"[Ingest Warning] 解析 PDF 电子书 '{file}' 失败: {e}")

        logger.info(f"--- 任务 2 完成！成功解析 {pdf_count} 本 PDF 电子书，落盘 {total_pdf_chunks} 条切片向量到 Qdrant ---")
    else:
        logger.warning(f"目录未找到: {pdf_dir}")

    total_chunks = total_md_chunks + (total_pdf_chunks if 'total_pdf_chunks' in locals() else 0)
    logger.info(f"=== 🎉 全量向量化落盘任务圆满完成！Qdrant 数据库共新增 {total_chunks} 条高匹配知识点向量！ ===")


if __name__ == "__main__":
    run_batch_ingestion()
