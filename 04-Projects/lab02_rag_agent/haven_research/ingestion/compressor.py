"""
haven_research/ingestion/compressor.py - 两阶段搜索上下文压缩器 (Two-Stage Context Compression)

【1:1 对标 gpt-researcher 核心 Map-Reduce 压缩机制】:
在全网抓取 / MCP 检索拿到海量 HTML/PDF/Markdown 切片后，
并发调用轻量级 LLM / 规则抽取，将冗长切片压缩为 200~300 字的高密度【子课题事实证据段落】，
去除 70%+ 无关网页噪音，大幅提升 RAG 检索精准度并降低 Token 消耗。
"""

import asyncio
from typing import List, Dict, Any
from haven_research.config import settings
from haven_research.core import logger
from haven_research.schemas.dto import TextChunkDTO

class ContextCompressor:
    """两阶段搜索上下文压缩器"""

    def __init__(self):
        self.llm_client = settings.get_async_llm_client()
        self.model = settings.get_effective_model_name()

    async def compress_chunk_async(self, topic: str, chunk: TextChunkDTO) -> TextChunkDTO:
        """
        针对指定研究主题 topic，对单条原始切片进行 Map 阶段的高密度事实提炼
        """
        # 如果切片本身较短 (< 300字)，无需二次压缩
        if len(chunk.content) <= 300:
            return chunk

        if not self.llm_client:
            # 规则降级截断
            chunk.content = chunk.content[:350] + "..."
            return chunk

        prompt = f"""你是一名极其严谨的数据事实提炼专家。请针对研究主题【{topic}】，从以下原始网页/文档切片中提炼出最核心的 200 字以内的事实数据、技术细节与关键结论。

要求：
1. 绝对保留原始数据中的具体数字、日期、版本号、API 名称与核心结论。
2. 剔除所有网页导航栏、广告、无关客套话与噪音。
3. 保持客观中立，严禁编造。

【原始切片】:
{chunk.content[:2000]}

【提炼出的高密度事实】:"""

        try:
            resp = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=350
            )
            compressed_text = resp.choices[0].message.content.strip()
            if compressed_text and len(compressed_text) > 30:
                chunk.content = compressed_text
        except Exception as e:
            logger.warning(f"[ContextCompressor] 单条切片压缩跳过 (退避原文): {e}")
            chunk.content = chunk.content[:400] + "..."

        return chunk

    async def compress_chunks_parallel(
        self,
        topic: str,
        chunks: List[TextChunkDTO],
        max_concurrent: int = 5
    ) -> List[TextChunkDTO]:
        """
        并发 Map-Reduce 批量压缩切片列表
        """
        if not chunks:
            return []

        logger.info(f"[ContextCompressor] 开启 Map 阶段：针对主题 '{topic}' 并发压缩 {len(chunks)} 条原始切片...")
        
        semaphore = asyncio.Semaphore(max_concurrent)

        async def worker(c: TextChunkDTO):
            async with semaphore:
                return await self.compress_chunk_async(topic, c)

        tasks = [worker(c) for c in chunks]
        compressed_chunks = await asyncio.gather(*tasks)
        
        total_orig = sum(len(c.content) for c in chunks)
        total_comp = sum(len(c.content) for c in compressed_chunks)
        saved_rate = round((1 - total_comp / max(1, total_orig)) * 100, 1)
        
        logger.info(f"[ContextCompressor] 压缩完成！原始字符: {total_orig} -> 压缩后: {total_comp} (节省噪音: {saved_rate}%)")
        return compressed_chunks
