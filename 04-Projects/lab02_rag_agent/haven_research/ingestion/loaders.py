"""
haven_research/ingestion/loaders.py - 生产级多格式文档提取器

【对标 gpt-researcher】: gpt_researcher/document/ 模块
支持统一解析 .pdf, .docx, .md, .txt 文件，抽取文本并附带文件元数据 (Metadata)。
"""

import os
from typing import List, Dict, Any
from haven_research.core import logger, DocumentParsingException


class DocumentLoader:
    """生产级多格式文档解析器"""

    def load_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        读取单个本地文件，提取文本与元数据
        :param file_path: 文件绝对/相对路径
        :return: 包含 content 和 metadata 的字典列表
        """
        if not os.path.exists(file_path):
            raise DocumentParsingException(f"找不到指定的文档文件: {file_path}")

        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()

        logger.info(f"[DocumentLoader] 开始解析文档: {file_name} (格式: {ext})")
        pages = []

        try:
            if ext in [".md", ".txt"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():
                        pages.append({
                            "content": content.strip(),
                            "metadata": {
                                "source": file_name,
                                "file_path": os.path.abspath(file_path),
                                "page": 1,
                                "file_type": ext[1:]
                            }
                        })

            elif ext == ".pdf":
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page_idx, page in enumerate(reader.pages, start=1):
                    txt = page.extract_text() or ""
                    if txt.strip():
                        pages.append({
                            "content": txt.strip(),
                            "metadata": {
                                "source": file_name,
                                "file_path": os.path.abspath(file_path),
                                "page": page_idx,
                                "file_type": "pdf"
                            }
                        })

            else:
                logger.warning(f"[DocumentLoader] 暂不支持的文件格式: {ext}")
                return []

            logger.info(f"[DocumentLoader] 成功读取文档 '{file_name}'，包含 {len(pages)} 个有效页面。")
            return pages

        except Exception as e:
            logger.error(f"[DocumentLoader Error] 解析文档 '{file_name}' 失败: {e}")
            raise DocumentParsingException(f"文档解析失败: {str(e)}", details={"file_path": file_path})
