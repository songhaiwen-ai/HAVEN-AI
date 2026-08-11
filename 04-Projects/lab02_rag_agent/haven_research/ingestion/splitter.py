"""
haven_research/ingestion/splitter.py - 语义文本切片器

【对标 gpt-researcher】: gpt_researcher/context/ 文本分块逻辑
实现带有句末标点退避与固定窗口重叠 (Overlap) 的生产级文本切片器，
保证切片语义的完整性，防止关键句在窗口边界被断开。
"""

from typing import List
from haven_research.config import settings
from haven_research.core import logger


class SemanticTextSplitter:
    """带语义边界退避与重叠窗口的文本切片器"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        # 标点分隔符优先级：换行符 -> 句号 -> 问号/感叹号 -> 分号 -> 空格
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", ";", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        执行语义文本切片
        :param text: 待切片的长文本
        :return: 文本切片字符串列表
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # 在 [end - 50, end] 范围内寻找最佳标点分隔符进行退避切分
            split_pos = end
            search_window = text[max(start, end - 50):end]
            
            found_sep = False
            for sep in self.separators:
                if sep and sep in search_window:
                    rel_idx = search_window.rfind(sep)
                    split_pos = max(start, end - 50) + rel_idx + len(sep)
                    found_sep = True
                    break

            chunk = text[start:split_pos].strip()
            if chunk:
                chunks.append(chunk)

            # 下一个窗口起点向后回退 chunk_overlap 长度，保留跨边界语义
            start = split_pos - self.chunk_overlap if found_sep else split_pos

        logger.debug(f"[TextSplitter] 原始文本 (长 {text_len} 字符) 被切割为 {len(chunks)} 个语义切片。")
        return chunks
