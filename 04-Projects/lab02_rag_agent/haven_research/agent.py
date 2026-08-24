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
from haven_research.ingestion import SemanticTextSplitter, ContextCompressor
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
        self.compressor = ContextCompressor()  # 【两阶段 Map-Reduce 事实压缩器】
        self.splitter = SemanticTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.vector_store = VectorStoreFactory.get_vector_store(settings.vector_store_type)
        self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store)
        self.verifier = CitationVerifierGate()
        self.cost_tracker = CostTracker()
        
        self.agent_info: Dict[str, str] = {}

    async def conduct_research_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        【真·流式推流引擎 (全流程集成 MCP 协议 + Skills 技能库)】:
        解耦解包状态事件，并使用 stream=True 直接从 LLM 获取 Token 实时推流，
        TTFT (首字延迟) 缩短至 1 秒以内！
        """
        logger.info(f"=== 🚀 开启 HavenResearch 深度研究 (课题: '{self.query}', 模式: {self.report_source.value}) ===")

        # ----------------------------------------------------------------------
        # 步骤 0: 动态 Agent 角色生成
        # ----------------------------------------------------------------------
        self.agent_info = await choose_agent(self.query)

        # ----------------------------------------------------------------------
        # 步骤 1: 动态 Agent 角色生成与子主题规划
        # ----------------------------------------------------------------------
        yield {"type": "persona", "content": f"✦ [{self.agent_info.get('agent', '深度研究专家')}] 正在深度理解研究课题，规划核心分析维度..."}
        subtopics = await self.planner.plan_subtopics(self.query, max_subtopics=self.max_subtopics)
        logger.info(f"[Agent Plan] 子主题拆解完成: {subtopics}")

        # ----------------------------------------------------------------------
        # 步骤 2: 多源抓取与实时向量入库
        # ----------------------------------------------------------------------
        all_sources: List[str] = []
        if self.report_source in [ReportSource.Web, ReportSource.Hybrid]:
            for idx, subtopic in enumerate(subtopics, 1):
                yield {"type": "persona", "content": f"✦ 正在检索第 {idx}/{len(subtopics)} 个维度 ('{subtopic}') 的前沿文献与权威数据..."}
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

                search_results = await self.retriever.search(subtopic, max_results=settings.search_max_results)
                scrape_tasks = [self.scraper.scrape_async(res.href, max_chars=1500) for res in search_results]
                scraped_docs = await asyncio.gather(*scrape_tasks)
                
                # 语义切片与存入 Qdrant
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
            yield {"type": "persona", "content": "✦ 正在调起专用知识库检索精准事实..."}

        # ----------------------------------------------------------------------
        # 步骤 3: 事实筛选与二次交叉精排
        # ----------------------------------------------------------------------
        yield {"type": "persona", "content": "✦ 正在交叉验证高价值数据源与核心事实..."}
        retrieved_contexts: List[TextChunkDTO] = []
        
        # 检查研究课题中是否包含 GitHub 仓库链接，优先直连 GitHub MCP 抓取 Live 元数据
        from haven_research.mcp.github_mcp import GitHubMCPClient
        parsed_gh = GitHubMCPClient.parse_github_url(self.query)
        if parsed_gh:
            owner, repo = parsed_gh["owner"], parsed_gh["repo"]
            try:
                gh_details = await GitHubMCPClient().get_repository_details_async(owner, repo)
                if gh_details:
                    gh_chunk_text = (
                        f"【GitHub MCP 官方 API 实时抓取事实 (最高优先权威证据)】:\n"
                        f"- 项目仓库: {gh_details['full_name']}\n"
                        f"- Star 数: {gh_details['stars']}⭐ | Fork 数: {gh_details['forks']}\n"
                        f"- 真实最新 Commit 提交时间 (pushed_at): {gh_details['pushed_at']}\n"
                        f"- 真实最近更新时间 (updated_at): {gh_details['updated_at']}\n"
                        f"- 项目描述: {gh_details['description']}\n"
                        f"- 真实 README 内容节选:\n{gh_details['readme'][:2000]}"
                    )
                    retrieved_contexts.append(
                        TextChunkDTO(url=gh_details['html_url'], content=gh_chunk_text, score=2.0)
                    )
                    logger.info(f"[Agent GitHub MCP] 成功注入 GitHub 实时数据源 (pushed_at: {gh_details['pushed_at']})")
            except Exception as gh_err:
                logger.warning(f"[Agent GitHub MCP Warning] GitHub 直连抓取异常: {gh_err}")

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
        import datetime
        current_date_str = datetime.datetime.now().strftime("%Y年%m月%d日")

        # 自动化证据时效性分层 (Dual-Tier Knowledge Classification)
        live_tier_chunks = []
        static_rag_chunks = []

        for ctx in contexts:
            # 得分 >= 1.5 或来自实时 MCP / Web 抓取的数据归为实时动态层
            if ctx.score >= 1.5 or "http" in ctx.url or "MCP" in ctx.content:
                live_tier_chunks.append(ctx)
            else:
                static_rag_chunks.append(ctx)

        live_str_list = [f"【实时动态证据 {i}】得分: {c.score} | 来源: {c.url}\n内容: {c.content}" for i, c in enumerate(live_tier_chunks, 1)]
        static_str_list = [f"【静态规范证据 {i}】得分: {c.score} | 来源: {c.url}\n内容: {c.content}" for i, c in enumerate(static_rag_chunks, 1)]

        live_context = "\n\n".join(live_str_list[:8]) if live_str_list else "暂无实时网络抓取数据。"
        static_context = "\n\n".join(static_str_list[:6]) if static_str_list else "暂无静态知识库数据。"

        aggregated_context = (
            f"=== 🟢 第一级：实时动态事实层 (Live & High-Freshness Tier - 最最新数据) ===\n"
            f"{live_context}\n\n"
            f"=== 🔵 第二级：静态/私有知识与背景规范层 (Static RAG & Baseline Tier - 企业规范/历史背景) ===\n"
            f"{static_context}"
        )

        agent_role = self.agent_info.get("role", "你是一名资深技术研究员。")
        
        system_prompt = (
            f"{agent_role}\n"
            f"你需要根据提供的实时网络抓取事实与证据，撰写一份严谨、详实、逻辑严密的 {self.report_type.value} 深度研究报告。\n"
            f"{skills_prompt}\n"
            "排版规范与真实时间线最高约束：\n"
            "1. 必须使用 Markdown 格式，包含一级标题、二级标题、加粗强调与无序列表。\n"
            "2. 结构包含：一、执行摘要；二、核心技术架构与原理；三、工业落地实践与应用；四、面临挑战与未来展望；五、参考来源链接。\n"
            "3. 文风客观严谨、富有深度，禁用泛泛而谈的废话。\n"
            f"4. 真实系统时间与时间戳最高优先级防伪 Guardrail：\n"
            f"   - 当前真实现实世界时间为：{current_date_str}。报告落款与分析必须以当前真实系统时间为基准，绝对禁止将参考资料本身的创作日期（例如2024年的旧博客）错误当做本报告的发布时间或当前数据的截止时间！\n"
            f"5. 双层知识分级与时效性最高原则 (Dual-Tier Knowledge Freshness Principle)：\n"
            f"   - 🟢 第一级【实时动态事实层】包含由全网、MCP API 实时抓取的最最新数据，用于描述项目当前状态、最新 Commit 时间、最新版本与实时指标；\n"
            f"   - 🔵 第二级【静态/私有知识与背景规范层】包含向量库中的企业规范、私有架构与历史文献，仅用于补充底层原理与规范约束；\n"
            f"   - 当两层信息在时效性、最新状态或提交时间上存在差异时，必须 100% 优先以【第一级：实时动态事实层】的最新数据为准！\n"
            f"6. 商业化正文严禁内漏原则 (No Backend Jargon Leak)：\n"
            f"   - 报告正文必须是纯粹、专业、干净的技术报告，绝对禁止在生成的 Markdown 文本中打印任何系统内部提示词术语或后端实现逻辑！\n"
            f"   - 严禁在正文中写出：'Dual-Tier Knowledge Freshness Principle'、'实时动态事实层'、'静态规范层'、'系统时间锚定声明'、'基于证据 X & Y'、'MCP/Qdrant 检索说明' 等内部背景声明或堆砌废话！所有事实必须自然融入技术分析之中。"
        )

        user_prompt = (
            f"研究课题：{self.query}\n"
            f"拆解的子研究主题：{', '.join(subtopics)}\n\n"
            f"【实时检索事实与网页证据 (含 MCP 工具与 ArXiv 学术干货)】:\n{aggregated_context}\n\n"
            f"请为我撰写一份完整的深度技术研究报告："
        )

        client = settings.get_async_llm_client()
        if not client:
            logger.error("[Agent Error] 未配置有效的大模型 API Key，终止研报合成。")
            yield "【错误】：未检测到可用的 LLM API Key，请在 .env 中配置 OPENAI_API_KEY。"
            return

        model_name = settings.get_effective_model_name()

        for attempt in range(1, max_retries + 1):
            try:
                response = await client.chat.completions.create(
                    model=model_name,
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
