"""
haven_research/agent.py - 生产级 HavenResearcher 主控 Agent 调度引擎

【1:1 对标 gpt-researcher】: gpt_researcher/agent.py
调度整套自动化研究工作流：
1. 子主题拆解 (Plan)
2. 异步网络检索与网页抓取去噪 (Search & Scrape)
3. 语义切片与向量入库 (Ingest & Vector Store)
4. 向量上下文检索与引用对齐 (Retrieve & Context)
5. DeepSeek 深度生成 Markdown 技术研究报告 (Synthesize Report)
"""

import asyncio
import openai
from typing import List, Dict, Any
from haven_research.config import settings
from haven_research.core import logger, HavenAgentException
from haven_research.schemas.dto import (
    ResearchRequestDTO,
    ResearchReportDTO,
    TextChunkDTO,
    SearchResultDTO
)
from haven_research.planner import SubtopicPlanner
from haven_research.retrievers import DuckDuckGoRetriever
from haven_research.scrapers import WebScraper
from haven_research.ingestion import SemanticTextSplitter
from haven_research.storage import VectorStoreFactory


class HavenResearcher:
    """生产级深度研究 Agent 主控引擎 (Deep Research Agent)"""

    def __init__(self, request: ResearchRequestDTO):
        self.request = request
        self.query = request.query
        self.max_subtopics = request.max_subtopics or settings.max_subtopics
        
        # 实例化基础设施组件
        self.planner = SubtopicPlanner()
        self.retriever = DuckDuckGoRetriever()
        self.scraper = WebScraper(timeout=settings.scraper_timeout)
        self.splitter = SemanticTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.vector_store = VectorStoreFactory.get_vector_store(settings.vector_store_type)
        
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )

    async def conduct_research(self) -> ResearchReportDTO:
        """
        全自动化深度研究工作流调度主入口
        """
        logger.info(f"=== 🚀 开启 HavenResearch 深度研究 Agent (课题: '{self.query}') ===")

        # ----------------------------------------------------------------------
        # 步骤 1: 调用 DeepSeek LLM 规划拆解子问题与搜索 Queries
        # ----------------------------------------------------------------------
        subtopics = await self.planner.plan_subtopics(self.query, max_subtopics=self.max_subtopics)
        logger.info(f"[Agent Step 1/4] 子主题拆解完毕: {subtopics}")

        # ----------------------------------------------------------------------
        # 步骤 2: 高并发网络检索、网页抓取去噪与语义切片入库
        # ----------------------------------------------------------------------
        all_sources: List[str] = []
        for idx, subtopic in enumerate(subtopics, 1):
            logger.info(f"[Agent Step 2/4] (主题 {idx}/{len(subtopics)}) 正在展开检索: '{subtopic}'")
            
            # 并发网络搜索
            search_results = await self.retriever.search(subtopic, max_results=settings.search_max_results)
            
            # 并发抓取各网页正文并提取去噪文本
            scrape_tasks = [self.scraper.scrape_async(res.href, max_chars=1500) for res in search_results]
            scraped_docs = await asyncio.gather(*scrape_tasks)
            
            # 语义切片与存入 Qdrant 云端向量数据库
            for res, doc in zip(search_results, scraped_docs):
                if doc.text and len(doc.text) > 50:
                    chunks = self.splitter.split_text(doc.text)
                    texts = chunks
                    metadatas = [{"source": res.href, "title": res.title} for _ in chunks]
                    
                    self.vector_store.add_texts(texts=texts, metadatas=metadatas)
                    if res.href not in all_sources:
                        all_sources.append(res.href)

        # ----------------------------------------------------------------------
        # 步骤 3: 结合子问题，从向量数据库检索 Top-K 相关上下文
        # ----------------------------------------------------------------------
        logger.info(f"[Agent Step 3/4] 正在从 {settings.vector_store_type.upper()} 向量库检索相关研究证据与上下文...")
        retrieved_contexts: List[TextChunkDTO] = []
        for subtopic in subtopics:
            hits = self.vector_store.similarity_search(subtopic, k=3)
            retrieved_contexts.extend(hits)

        # ----------------------------------------------------------------------
        # 步骤 4: 调用 DeepSeek API 深度生成 Markdown 综合研究报告
        # ----------------------------------------------------------------------
        logger.info(f"[Agent Step 4/4] 正在调用 DeepSeek ({settings.llm_model}) 深度合成技术研究报告...")
        report_markdown = await self._synthesize_report(subtopics, retrieved_contexts)

        logger.info(f"=== 🎉 深度研究报告合成完毕！引用网络来源数: {len(all_sources)} ===")

        return ResearchReportDTO(
            success=True,
            query=self.query,
            report_markdown=report_markdown,
            sources=retrieved_contexts
        )

    async def _synthesize_report(
        self,
        subtopics: List[str],
        contexts: List[TextChunkDTO]
    ) -> str:
        """调用 DeepSeek 最终合成结构化 Markdown 报告"""
        context_str_list = []
        for idx, ctx in enumerate(contexts, 1):
            context_str_list.append(f"【证据 {idx}】来源: {ctx.url}\n内容: {ctx.content}")

        aggregated_context = "\n\n".join(context_str_list[:12]) if context_str_list else "无检索事实，依据大模型自身知识库生成。"

        system_prompt = (
            "你是一名工业级 AI 架构师与行业首席研究员。"
            "你需要根据提供的实时网络抓取事实与证据，撰写一份严谨、详实、逻辑严密的技术研究报告。\n"
            "排版规范：\n"
            "1. 必须使用 Markdown 格式，包含一级标题、二级标题、加粗强调与无序列表。\n"
            "2. 结构包含：一、执行摘要；二、核心技术架构与原理；三、工业落地实践与应用；四、面临挑战与未来展望；五、参考来源链接。\n"
            "3. 文风客观严谨、富有深度，禁用泛泛而谈的废话。"
        )

        user_prompt = (
            f"研究课题：{self.query}\n"
            f"拆解的子研究主题：{', '.join(subtopics)}\n\n"
            f"【实时检索事实与网页证据】:\n{aggregated_context}\n\n"
            f"请为我撰写一份完整的深度技术研究报告："
        )

        try:
            resp = await self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"[Agent Error] DeepSeek 报告合成失败: {e}")
            raise HavenAgentException(f"报告合成失败: {str(e)}")
