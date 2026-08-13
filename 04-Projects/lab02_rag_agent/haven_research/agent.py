"""
haven_research/agent.py - 生产级 HavenResearcher 主控 Agent 调度引擎

【1:1 对标 gpt-researcher + HAVEN-AI 独家重排序与防幻觉门禁】: gpt_researcher/agent.py
调度整套自动化研究工作流：
1. 动态 Agent 角色生成 (choose_agent)
2. 子主题拆解 (Plan)
3. 数据源选择性检索 (ReportSource: Web / Local / Hybrid)
4. 语义切片与向量入库 (Ingest & Vector Store)
5. 双路混合检索与 BGE Reranker 二次精排 (Hybrid Search & Rerank)
6. DeepSeek 深度生成 Markdown 技术研究报告 (Synthesize Report)
7. 防幻觉引用后置校验门禁 (Citation Verifier Gate)
8. Token 消耗与费用统计 (CostTracker)
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
    SearchResultDTO,
    ReportType,
    ReportSource
)
from haven_research.actions import choose_agent
from haven_research.planner import SubtopicPlanner
from haven_research.retrievers import DuckDuckGoRetriever, TavilyRetriever
from haven_research.scrapers import WebScraper
from haven_research.ingestion import SemanticTextSplitter
from haven_research.storage import VectorStoreFactory
from haven_research.reranker import HybridRetriever
from haven_research.verifier import CitationVerifierGate
from haven_research.utils import CostTracker


class HavenResearcher:
    """生产级深度研究 Agent 主控引擎 (Deep Research Agent)"""

    def __init__(self, request: ResearchRequestDTO):
        self.request = request
        self.query = request.query
        self.max_subtopics = request.max_subtopics or settings.max_subtopics
        self.report_type = request.report_type
        self.report_source = request.report_source
        
        # 实例化基础设施组件
        self.planner = SubtopicPlanner()
        self.retriever = TavilyRetriever()
        self.scraper = WebScraper(timeout=settings.scraper_timeout)
        self.splitter = SemanticTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.vector_store = VectorStoreFactory.get_vector_store(settings.vector_store_type)
        self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store)
        self.verifier = CitationVerifierGate()
        self.cost_tracker = CostTracker()
        
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.agent_info: Dict[str, str] = {}

    async def conduct_research(self) -> ResearchReportDTO:
        """
        全自动化深度研究工作流调度主入口
        """
        logger.info(f"=== 🚀 开启 HavenResearch 深度研究 Agent (课题: '{self.query}', 模式: {self.report_type.value}, 目标数据源: {self.report_source.value}) ===")

        # ----------------------------------------------------------------------
        # 步骤 0: 动态定制专精 Agent 角色与人设 Persona (gpt-researcher 1:1)
        # ----------------------------------------------------------------------
        self.agent_info = await choose_agent(self.query)
        logger.info(f"[Agent Step 0] 动态确定专家 Persona: 【{self.agent_info.get('agent')}】")

        # ----------------------------------------------------------------------
        # 步骤 1: 调用 DeepSeek LLM 规划拆解子问题与搜索 Queries
        # ----------------------------------------------------------------------
        subtopics = await self.planner.plan_subtopics(self.query, max_subtopics=self.max_subtopics)
        logger.info(f"[Agent Step 1/5] 子主题拆解完毕: {subtopics}")

        # ----------------------------------------------------------------------
        # 步骤 2: 根据 ReportSource (Web / Local / Hybrid) 执行检索与抓取
        # ----------------------------------------------------------------------
        all_sources: List[str] = []
        
        # 如果包含 Web 检索 (Web 或 Hybrid 模式)
        if self.report_source in [ReportSource.Web, ReportSource.Hybrid]:
            for idx, subtopic in enumerate(subtopics, 1):
                logger.info(f"[Agent Step 2/5] (网络检索 {idx}/{len(subtopics)}) 正在展开全网检索: '{subtopic}'")
                
                # 并发网络搜索 (Tavily / DDG)
                search_results = await self.retriever.search(subtopic, max_results=settings.search_max_results)
                
                # 并发抓取各网页正文并提取去噪文本
                scrape_tasks = [self.scraper.scrape_async(res.href, max_chars=1500) for res in search_results]
                scraped_docs = await asyncio.gather(*scrape_tasks)
                
                # 语义切片与存入 Qdrant 云端向量数据库
                for res, doc in zip(search_results, scraped_docs):
                    if doc.text and len(doc.text) > 50:
                        chunks = self.splitter.split_text(doc.text)
                        metadatas = [{"source": res.href, "title": res.title} for _ in chunks]
                        
                        self.vector_store.add_texts(texts=chunks, metadatas=metadatas)
                        self.cost_tracker.add_embeddings(len(chunks))
                        if res.href not in all_sources:
                            all_sources.append(res.href)
        else:
            logger.info(f"[Agent Step 2/5] 纯本地知识库模式 (Local Mode)，跳过全网实时抓取。")

        # ----------------------------------------------------------------------
        # 步骤 3: 结合子问题，双路混合检索 + BGE Reranker 二次精排 (HAVEN-AI 独家)
        # ----------------------------------------------------------------------
        logger.info(f"[Agent Step 3/5] 正在触发【双路混合检索 + BGE Reranker 重排序】提取精排研究证据...")
        retrieved_contexts: List[TextChunkDTO] = []
        for subtopic in subtopics:
            hits = self.hybrid_retriever.hybrid_search(subtopic, top_k=3, coarse_k=10)
            retrieved_contexts.extend(hits)

        # ----------------------------------------------------------------------
        # 步骤 4: 调用 DeepSeek API 深度生成 Markdown 综合研究报告
        # ----------------------------------------------------------------------
        logger.info(f"[Agent Step 4/5] 正在调用 DeepSeek ({settings.llm_model}) 深度合成技术研究报告...")
        report_markdown = await self._synthesize_report(subtopics, retrieved_contexts)

        # ----------------------------------------------------------------------
        # 步骤 5: 防幻觉引用后置校验门禁与 Token 费用结算 (HAVEN-AI 独家)
        # ----------------------------------------------------------------------
        logger.info(f"[Agent Step 5/5] 正在触发【防幻觉引用后置校验门禁】执行蕴含断言核查...")
        verification = await self.verifier.verify_report(report_markdown, retrieved_contexts)
        
        cost_summary = self.cost_tracker.get_summary()
        logger.info(f"=== 🎉 深度研究报告履约完成！总计消耗 Token: {cost_summary['total_tokens']}, 预估费用: ${cost_summary['total_cost_usd']} ===")

        return ResearchReportDTO(
            success=True,
            query=self.query,
            agent_persona=self.agent_info.get("agent", "通用研究专家"),
            report_markdown=report_markdown,
            sources=retrieved_contexts,
            cost_summary=cost_summary,
            verification_summary=verification
        )

    async def _synthesize_report(
        self,
        subtopics: List[str],
        contexts: List[TextChunkDTO]
    ) -> str:
        """调用 DeepSeek 结合动态 Agent Persona 最终合成结构化 Markdown 报告"""
        context_str_list = []
        for idx, ctx in enumerate(contexts, 1):
            context_str_list.append(f"【精排证据 {idx}】得分: {ctx.score} | 来源: {ctx.url}\n内容: {ctx.content}")

        aggregated_context = "\n\n".join(context_str_list[:12]) if context_str_list else "无检索事实，依据大模型自身知识库生成。"

        agent_role = self.agent_info.get("role", "你是一名资深技术研究员。")
        
        system_prompt = (
            f"{agent_role}\n"
            f"你需要根据提供的实时网络抓取事实与证据，撰写一份严谨、详实、逻辑严密的 {self.report_type.value} 深度研究报告。\n"
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

            # 记录 Token 消耗
            if resp.usage:
                self.cost_tracker.add_tokens(
                    prompt_tokens=resp.usage.prompt_tokens,
                    completion_tokens=resp.usage.completion_tokens,
                    step_name="report_synthesis"
                )

            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"[Agent Error] DeepSeek 报告合成失败: {e}")
            raise HavenAgentException(f"报告合成失败: {str(e)}")
