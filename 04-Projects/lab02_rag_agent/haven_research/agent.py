"""
haven_research/agent.py - 生产级 HavenResearcher 主控 Agent 调度引擎

【1:1 对标 gpt-researcher + HAVEN-AI 独家 MCP 协议、Skills 技能库与真·流式推流】:
1. 动态 Agent 角色生成 (choose_agent)
2. 子主题拆解 (Plan)
3. 调起 MCP 协议 (ArXiv 学术论文 MCP + GitHub 开源码 MCP) 与 Tavily / DDG 全网抓取
4. 动态加载与注入 Agent Skills 技能库 (SkillManager)
5. 语义切片与向量入库 (Ingest & Qdrant Cloud Vector Store)
6. 双路混合检索与 BGE Reranker 二次精排 (Hybrid Search & Rerank)
7. DeepSeek API 指数退避重试 (Exponential Backoff) 与真·Token 实时流式打字推流 (conduct_research_stream)
8. 伴随式防幻觉校验 (Non-blocking Citation Verifier)
9. Token 消耗与费用统计 (CostTracker)
"""

import asyncio
import openai
import time
from typing import List, Dict, Any, AsyncGenerator
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
from haven_research.retrievers import DuckDuckGoRetriever, TavilyRetriever, MCPRetriever
from haven_research.scrapers import WebScraper
from haven_research.skills import SkillManager
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
        
        # 实例化基础设施组件与 MCP / Skills 扩展引擎
        self.planner = SubtopicPlanner()
        self.retriever = TavilyRetriever()
        self.mcp_retriever = MCPRetriever()  # 【MCP 协议标准检索器】
        self.skill_manager = SkillManager()  # 【Agent Skills 动态技能管理器】
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

    async def conduct_research_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        【真·流式推流引擎 (全流程集成 MCP 协议 + Skills 技能库)】:
        解耦解包状态事件，并使用 stream=True 直接从 LLM 获取 Token 实时推流，
        TTFT (首字延迟) 缩短至 1 秒以内！
        """
        logger.info(f"=== 🚀 开启 HavenResearch 深度研究 (课题: '{self.query}', 模式: {self.report_source.value}) ===")

        # ----------------------------------------------------------------------
        # 步骤 0: 动态 Agent 角色生成 (choose_agent)
        # ----------------------------------------------------------------------
        yield {"type": "step", "message": "🎭 正在调用 DeepSeek 分析课题并定制专家 Persona..."}
        self.agent_info = await choose_agent(self.query)
        persona = self.agent_info.get("agent", "通用研究专家")
        yield {"type": "persona", "persona": persona}
        logger.info(f"[Agent Step 0] 动态专家 Persona: 【{persona}】")

        # ----------------------------------------------------------------------
        # 步骤 1: 调用 DeepSeek 拆解子问题与搜索 Queries
        # ----------------------------------------------------------------------
        yield {"type": "step", "message": f"🗺️ 专家【{persona}】正在拆解子研究课题与构建 Multi-Queries..."}
        subtopics = await self.planner.plan_subtopics(self.query, max_subtopics=self.max_subtopics)
        logger.info(f"[Agent Step 1/5] 子主题拆解完毕: {subtopics}")

        # ----------------------------------------------------------------------
        # 步骤 2: 调起 MCP 协议 (ArXiv / GitHub MCP) 与网络抓取降级
        # ----------------------------------------------------------------------
        all_sources: List[str] = []
        if self.report_source in [ReportSource.Web, ReportSource.Hybrid]:
            for idx, subtopic in enumerate(subtopics, 1):
                # 💥 1. 调起 MCP 协议检索器 (ArXiv 学术论文 + GitHub 代码库 MCP)
                yield {"type": "step", "message": f"🔗 (MCP 协议检索 {idx}/{len(subtopics)}) 正在调起 ArXiv & GitHub MCP 工具: '{subtopic}'"}
                try:
                    mcp_results = await self.mcp_retriever.search(subtopic, max_results=3)
                    for mcp_res in mcp_results:
                        if mcp_res.body and len(mcp_res.body) > 20:
                            mcp_chunks = self.splitter.split_text(mcp_res.body)
                            mcp_metadatas = [{"source": mcp_res.href, "title": mcp_res.title} for _ in mcp_chunks]
                            self.vector_store.add_texts(texts=mcp_chunks, metadatas=mcp_metadatas)
                            if mcp_res.href not in all_sources:
                                all_sources.append(mcp_res.href)
                except Exception as me:
                    logger.warning(f"[Agent MCP Warning] MCP 检索调用警告: {me}")

                # 2. 全网通用 Web 搜索与抓取
                yield {"type": "step", "message": f"🌐 (全网抓取 {idx}/{len(subtopics)}) 正在抓取实时网页: '{subtopic}'"}
                search_results = await self.retriever.search(subtopic, max_results=settings.search_max_results)
                scrape_tasks = [self.scraper.scrape_async(res.href, max_chars=1500) for res in search_results]
                scraped_docs = await asyncio.gather(*scrape_tasks)
                
                # 语义切片与存入 Qdrant (带 Web 抓取失败自动降级为搜索引擎 Snippet 防护)
                for res, doc in zip(search_results, scraped_docs):
                    text_content = doc.text
                    if not text_content or len(text_content) < 30:
                        text_content = getattr(res, "snippet", "") or getattr(res, "body", "")
                        if text_content:
                            logger.info(f"[Scraper Fallback] 网页抓取受阻 ({res.href})，平滑降级使用搜索 Snippet 摘要。")

                    if text_content and len(text_content) >= 20:
                        chunks = self.splitter.split_text(text_content)
                        metadatas = [{"source": res.href, "title": res.title} for _ in chunks]
                        self.vector_store.add_texts(texts=chunks, metadatas=metadatas)
                        self.cost_tracker.add_embeddings(len(chunks))
                        if res.href not in all_sources:
                            all_sources.append(res.href)
        else:
            yield {"type": "step", "message": "💾 纯本地知识库模式，跳过全网与 MCP 动态检索。"}

        # ----------------------------------------------------------------------
        # 步骤 3: 双路混合检索与 BGE Reranker 二次精排
        # ----------------------------------------------------------------------
        yield {"type": "step", "message": "🔍 正在触发【双路混合检索 + BGE Reranker 二次重排序】筛选高匹配证据..."}
        retrieved_contexts: List[TextChunkDTO] = []
        for subtopic in subtopics:
            hits = self.hybrid_retriever.hybrid_search(subtopic, top_k=3, coarse_k=10)
            retrieved_contexts.extend(hits)

        # ----------------------------------------------------------------------
        # 步骤 4: 动态匹配与注入 Agent Skills 技能，开启真·打字流式合成
        # ----------------------------------------------------------------------
        skills_prompt = self.skill_manager.get_skill_instructions_prompt()
        if skills_prompt:
            yield {"type": "step", "message": f"⚡ 自动激活 Agent Skills 技能库 ({len(self.skill_manager._loaded_skills)} 个专业技能已注入提示词)..."}

        yield {"type": "step", "message": f"📄 正在调用 DeepSeek ({settings.llm_model}) 开启 Token 实时打字流式生成..."}
        
        full_report_chunks = []
        async for token_chunk in self._synthesize_report_stream_with_retry(subtopics, retrieved_contexts, skills_prompt):
            full_report_chunks.append(token_chunk)
            yield {"type": "chunk", "content": token_chunk}

        full_markdown = "".join(full_report_chunks)

        # ----------------------------------------------------------------------
        # 步骤 5: 伴随式非阻塞防幻觉校验与 Token 费用统计
        # ----------------------------------------------------------------------
        asyncio.create_task(self.verifier.verify_report(full_markdown, retrieved_contexts))

        cost_summary = self.cost_tracker.get_summary()
        sources_data = [{"url": s.url, "score": s.score} for s in retrieved_contexts]

        yield {
            "type": "complete",
            "message": "🎉 深度研究技术报告履约完成！",
            "cost_summary": cost_summary,
            "sources": sources_data
        }

    async def conduct_research(self) -> ResearchReportDTO:
        """同步一次性研究履约入口 (兼容传统 REST 接口)"""
        full_markdown_parts = []
        sources = []
        cost_summary = {}

        async for event in self.conduct_research_stream():
            if event["type"] == "chunk":
                full_markdown_parts.append(event["content"])
            elif event["type"] == "complete":
                cost_summary = event["cost_summary"]
                sources = event["sources"]

        report_markdown = "".join(full_markdown_parts)

        return ResearchReportDTO(
            success=True,
            query=self.query,
            agent_persona=self.agent_info.get("agent", "通用研究专家"),
            report_markdown=report_markdown,
            sources=[TextChunkDTO(url=s["url"], content="", score=s["score"]) for s in sources],
            cost_summary=cost_summary
        )

    async def _synthesize_report_stream_with_retry(
        self,
        subtopics: List[str],
        contexts: List[TextChunkDTO],
        skills_prompt: str = "",
        max_retries: int = 3
    ) -> AsyncGenerator[str, None]:
        """
        调用 DeepSeek API 开启 stream=True 真流式 Token 推流，
        融合 Agent Skills 技能规范与指数退避重试 (Exponential Backoff Retry)。
        """
        context_str_list = []
        for idx, ctx in enumerate(contexts, 1):
            context_str_list.append(f"【精排证据 {idx}】得分: {ctx.score} | 来源: {ctx.url}\n内容: {ctx.content}")

        aggregated_context = "\n\n".join(context_str_list[:12]) if context_str_list else "无检索事实，依据大模型自身知识库生成。"
        agent_role = self.agent_info.get("role", "你是一名资深技术研究员。")
        
        system_prompt = (
            f"{agent_role}\n"
            f"你需要根据提供的实时网络抓取事实与证据，撰写一份严谨、详实、逻辑严密的 {self.report_type.value} 深度研究报告。\n"
            f"{skills_prompt}\n"
            "排版规范：\n"
            "1. 必须使用 Markdown 格式，包含一级标题、二级标题、加粗强调与无序列表。\n"
            "2. 结构包含：一、执行摘要；二、核心技术架构与原理；三、工业落地实践与应用；四、面临挑战与未来展望；五、参考来源链接。\n"
            "3. 文风客观严谨、富有深度，禁用泛泛而谈的废话。\n"
            "4. 事实与时间防护线 (Temporal & Fact Integrity Guardrail)：\n"
            "   - 如果研究课题涉及未来时间点（例如尚未到来的年份或月份），必须在报告开头明确声明数据的已知截止范围，严谨区分【已知事实/现状】与【前瞻性趋势推演】。\n"
            "   - 严禁将搜索到的网页时间戳噪声（如新闻排播单、URL路径时间戳）误报为已发生的权威科技突破事件！"
        )

        user_prompt = (
            f"研究课题：{self.query}\n"
            f"拆解的子研究主题：{', '.join(subtopics)}\n\n"
            f"【实时检索事实与网页证据 (含 MCP 工具与 ArXiv 学术干货)】:\n{aggregated_context}\n\n"
            f"请为我撰写一份完整的深度技术研究报告："
        )

        for attempt in range(1, max_retries + 1):
            try:
                response = await self.openai_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.4,
                    stream=True
                )

                async for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta_content = chunk.choices[0].delta.content
                        if delta_content:
                            yield delta_content
                return
            except Exception as e:
                logger.warning(f"[LLM Retry Warning] DeepSeek 流式请求失败 (尝试 {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    logger.error(f"[LLM Error] DeepSeek 最终重试失败: {e}")
                    raise HavenAgentException(f"LLM 流式生成失败: {str(e)}")
                await asyncio.sleep(2 ** attempt)
