# 🚀 Stage 2: 企业级 RAG 与资料研究助手 (Deep Research Agent) 架构与工程链路指南

> **核心目标**：构建符合企业级生产标准的 RAG 系统与多工具协同的 Deep Research Agent。

---

## 🏗️ 一、 深度研究 Agent 全景工程时序图 (Mermaid Pipeline)

```mermaid
sequenceDiagram
    autonumber
    participant User as 用户 (User Input)
    participant Orchestrator as 主控制引擎 (main_researcher.py)
    participant Retriever as 异步网络检索器 (01_retriever.py)
    participant Scraper as 网页抓取清洗器 (02_scraper.py)
    participant Context as 向量切片与去噪器 (03_context_manager.py)
    participant Writer as 带引用报告生成器 (04_report_writer.py)

    User->>Orchestrator: 提交研究主题: "AI Agent 架构设计"
    
    rect rgb(240, 248, 255)
    note right of Orchestrator: 阶段 1: 任务拆解 (Agent Planning)
    Orchestrator->>Orchestrator: generate_sub_queries() 拆解为 2 个子查询<br/>1. "AI Agent 架构设计 核心原理"<br/>2. "AI Agent 架构设计 最佳实践"
    end

    rect rgb(255, 250, 240)
    note right of Retriever: 阶段 2: 异步并发检索 (Async Retrieval)
    Orchestrator->>Retriever: asyncio.gather(search(q1), search(q2))
    Retriever-->>Orchestrator: 返回去重后的网页 URL 列表 [url1, url2, ...]
    end

    rect rgb(240, 255, 240)
    note right of Scraper: 阶段 3: 异步网页抓取与 HTML 清洗 (Async Scraping)
    Orchestrator->>Scraper: asyncio.gather(scrape_async(url1), scrape_async(url2)...)
    Scraper-->>Orchestrator: 返回清洗后的干货正文列表 [{url, text}, ...]
    end

    rect rgb(255, 240, 245)
    note right of Context: 阶段 4: 文本切片与余弦相似度筛选 (Context Manager)
    Orchestrator->>Context: get_similar_context(topic, scraped_data)
    Context->>Context: 1. Overlap Chunking 带窗口切片<br/>2. 计算 TF-IDF 余弦相似度得分<br/>3. 降序排序保留 Top-4 精选切片
    Context-->>Orchestrator: 返回精选切片列表 [{url, content, score}, ...]
    end

    rect rgb(245, 245, 255)
    note right of Writer: 阶段 5: 引用绑定与 Markdown 报告生成 (Report Generation)
    Orchestrator->>Writer: generate_report(topic, top_chunks)
    Writer->>Writer: 绑定 [Source X](URL) 引用角标注入 Prompt
    Writer-->>Orchestrator: 输出结构化 Markdown 深度研究报告
    end

    Orchestrator-->>User: 交付最终带可追溯引用的 Markdown 报告
```

---

## 📦 二、 阶段间的数据流转契约 (Data Contracts)

| 阶段 | 执行模块 | 接收输入格式 (Input) | 转换/处理动作 | 输出数据结构 (Output) |
| :--- | :--- | :--- | :--- | :--- |
| **1. 任务拆解** | `main_researcher.py` | `"AI Agent 架构设计"` (`str`) | 大目标拆解为子搜索关键词 | `["AI Agent 架构设计 核心原理", "AI Agent 架构设计 最佳实践"]` (`List[str]`) |
| **2. 并发检索** | `01_retriever.py` | 2 个搜索关键词 (`List[str]`) | 使用 `asyncio` 并发调用 DuckDuckGo 搜索 | `["https://openai.com/...", "https://docs.anthropic.com/..."]` (`List[str]`) |
| **3. 网页抓取** | `02_scraper.py` | URL 链接列表 (`List[str]`) | 使用 `requests` + `BeautifulSoup` 过滤 `<script>`、`<nav>` 等标签 | `[{"url": "...", "text": "提取的干货正文..."}, ...]` (`List[Dict]`) |
| **4. 切片与去噪**| `03_context_manager.py` | 抓取网页文本列表 (`List[Dict]`) | 窗口重叠切片 (Chunking)，计算余弦相似度 (Cosine Similarity) 提纯 | `[{"url": "...", "content": "切片段落...", "score": 0.617}, ...]` (`List[Dict]`) |
| **5. 报告生成** | `04_report_writer.py` | 保留的 Top-4 核心切片 (`List[Dict]`) | 绑定 `[Source X](URL)` 角标注入 Prompt | 格式化的 Markdown 深度研究报告字符串 (`str`) |

---

## 🗺️ 三、 生产级扩展演进方向

在当前核心主管道闭环的基础上，可按需补充以下 6 大模块：

1. **磁盘持久化向量库 (Vector Store)**：集成 ChromaDB / FAISS 向量库与真实 Embedding 模型。
2. **多源搜索引擎适配 (Multi-Source Retrievers)**：接入 Tavily, SearXNG, Arxiv API。
3. **重排精筛 (Cross-Encoder Reranker)**：集成 `bge-reranker-large` 模型消除二次假相关切片。
4. **多格式本地文档解析 (Document Loaders)**：集成 `PyPDF`、`python-docx`、`pandas`。
5. **FastAPI 与 WebSocket 流式控制台 (Streaming UI)**：支持前端可视化进度推送。
6. **MCP 协议与自定义 Skill 插件**：挂载 MCP 服务节点。

---

*文件归档：[c:\Haven-AI\04-Projects\lab02_rag_agent\00-Stage2-Roadmap-and-Architecture.md](file:///c:/Haven-AI/04-Projects/lab02_rag_agent/00-Stage2-Roadmap-and-Architecture.md)*
