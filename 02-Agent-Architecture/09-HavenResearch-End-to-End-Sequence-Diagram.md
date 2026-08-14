# 📐 HavenResearch Deep Research Agent 全流程端到端时序图

本文档详尽展示了从 **前端 Vue 3 用户输入研究课题**，到 **后端 FastAPI 触发 Agent 引擎、网络抓取、向量入库、双路混合检索、BGE 重排序、DeepSeek 报告合成、防幻觉校验、MySQL 消息持久化** 以及 **SSE 打字机流式推流** 的全生命周期时序交互流程。

---

## 🔄 全流程端到端交互时序图 (Mermaid Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User as "用户 (Vue 3 前端)"
    participant Gateway as "FastAPI API 网关"
    participant Auth as "JWT Auth 鉴权"
    participant DB as "MySQL / SQLite 数据库"
    participant Agent as "HavenResearcher 主控 Agent"
    participant LLM as "DeepSeek LLM API"
    participant Search as "Tavily / DDG 搜索引擎"
    participant Scraper as "WebScraper 抓取器"
    participant VectorDB as "Qdrant Cloud 向量库"
    participant Reranker as "BGE Reranker 重排序"
    participant Verifier as "CitationVerifier 防幻觉门禁"

    %% 阶段 1: 前端发起请求与鉴权
    rect rgb(240, 246, 255)
    User->>Gateway: 发起研究 HTTP SSE 请求 ("GET /api/v1/chat/stream?query=...")
    Gateway->>Auth: 校验 Bearer JWT Token
    Auth-->>Gateway: 返回验证结果 (提取 user_id)
    end

    %% 阶段 2: 会话持久化与 Agent 初始化
    rect rgb(245, 245, 245)
    Gateway->>DB: 持久化用户提问 ("INSERT INTO chat_messages (user, query)")
    DB-->>Gateway: 落盘成功
    Gateway->>Agent: 实例化 HavenResearcher(RequestDTO)
    end

    %% 阶段 3: 动态 Persona 定制与子主题拆解
    rect rgb(255, 250, 240)
    Agent->>LLM: 1. choose_agent(query) 动态定制专家 Persona
    LLM-->>Agent: 返回专家人设 ("【资深企业级 AI Agent 架构师】")
    Gateway-->>User: [SSE 步骤推流] "🎭 调用的专家 Persona: 【资深企业级 AI Agent 架构师】"

    Agent->>LLM: 2. plan_subtopics(query) 拆解 3 个子主题 Query
    LLM-->>Agent: 返回拆解的 Queries 列表
    Gateway-->>User: [SSE 步骤推流] "🗺️ 完成子主题拆解与 Query 拓展"
    end

    %% 阶段 4: 网络检索、抓取与向量落盘
    rect rgb(240, 255, 240)
    loop 遍历每个子主题 Query
        Agent->>Search: 3. search(subquery) 全网实时搜索
        Search-->>Agent: 返回 SearchResultDTO 搜索条目
        Agent->>Scraper: 4. scrape_async(url) 并发抓取网页正文
        Scraper-->>Agent: 返回去噪文本
        Agent->>VectorDB: 5. add_texts(chunks, metadatas) 语义切片并落盘 Qdrant
        VectorDB-->>Agent: 向量落盘成功 (新增 Points)
    end
    Gateway-->>User: [SSE 步骤推流] "🌐 完成全网实时抓取与 Qdrant 动态向量落盘"
    end

    %% 阶段 5: 双路混合检索与 BGE 重排序
    rect rgb(255, 240, 245)
    Agent->>VectorDB: 6. similarity_search(subquery, top_k=10) 向量粗筛召回
    VectorDB-->>Agent: 返回候选向量切片列表
    Agent->>Reranker: 7. rerank(query, candidates) BM25 + BGE Cross-Encoder 精排
    Reranker-->>Agent: 返回精选 Top 3 高匹配切片 (带 Match Scores)
    Gateway-->>User: [SSE 步骤推流] "🔍 完成 Qdrant 粗筛与 BGE 重排序"
    end

    %% 阶段 6: 报告合成与防幻觉门禁
    rect rgb(250, 240, 255)
    Agent->>LLM: 8. _synthesize_report(subtopics, top_contexts) 合成 3000 字 Markdown
    LLM-->>Agent: 返回结构化 Markdown 深度研究报告
    Agent->>Verifier: 9. verify_report(markdown, contexts) 蕴含断言抽查
    Verifier-->>Agent: 返回防幻觉校验指标
    end

    %% 阶段 7: SSE 逐字打字推流与持久化
    rect rgb(240, 255, 255)
    loop 逐块打字推流
        Gateway-->>User: [SSE 消息推流] {"type": "chunk", "content": "..."}
    end
    Gateway->>DB: 10. 持久化 Agent 报告与 Sources ("INSERT INTO chat_messages (assistant, markdown)")
    DB-->>Gateway: 落盘成功
    Gateway-->>User: [SSE 状态推流] {"type": "complete", "cost_summary": {...}}
    end
