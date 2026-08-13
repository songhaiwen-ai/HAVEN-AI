# 💻 Lab 02: 资料研究助手 (Deep Research Agent) 全景生产级架构与源码指南

> **对标标杆**：开源深度研究 Agent 框架 [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher)  
> **生产级架构**：基于 DeepSeek API + Qdrant Cloud 云端 Serverless 向量数据库，构建包含**私有本地 PDF/Word/Markdown 知识库自动向量落盘 + 全网实时检索 (Tavily/DDG) + 三层记忆管理 + CodeInterpreter 沙箱代码解释器 + 动态 Agent 角色生成 + BM25 与 BGE Reranker 二次精排 + 防幻觉引用门禁 + MCP (Model Context Protocol) 扩展 + Agent Skills 动态技能加载**的工业级 Deep Research Agent。

---

## 🔄 一、 深度研究 Agent 全景工程架构与包结构

```text
lab02_rag_agent/
├── haven_research/                  # 【大厂规范】本地可编辑开发包 (pip install -e .)
│   ├── config/                      # Pydantic Settings 配置中心 (DeepSeek + Qdrant Cloud)
│   ├── core/                        # 异常基类与结构化日志模块
│   ├── schemas/                     # DTO 强类型数据契约 (ResearchRequestDTO, ReportType, ReportSource)
│   ├── ingestion/                   # 本地多格式文档提取与 Qdrant 向量落盘服务 (LocalKnowledgeIngestionService)
│   ├── storage/                     # QdrantVectorStore 云端 Serverless 向量存储工厂
│   ├── retrievers/                  # 异步网络检索器 DuckDuckGoRetriever & TavilyRetriever
│   ├── scrapers/                    # 高并发网页抓取 WebScraper (带 Jina Reader 免爬降级)
│   ├── planner/                     # 智能子主题拆解器 SubtopicPlanner
│   ├── actions/                     # 动态 Agent 角色定制生成器 (choose_agent)
│   ├── memory/                      # 三层记忆架构体系 (Working / Session / LongTerm)
│   ├── interpreter/                 # Python Code Interpreter 代码解释器沙箱
│   ├── reranker/                    # 双路混合检索 (BM25 + Vector) 与 BGE Reranker 重排序
│   ├── verifier/                    # 防幻觉引用后置校验门禁 CitationVerifierGate
│   ├── utils/                       # Token 消耗与 API 费用折算 CostTracker
│   ├── skills/                      # 【重点】Agent Skills 技能发现与执行管理器 (SkillManager)
│   │   ├── manager.py               # 动态扫描 SKILL.md 与技能 Prompt 注入
│   │   └── sample_skill/            # 示例 Skill 模块 (SKILL.md)
│   ├── mcp/                         # 【重点】MCP (Model Context Protocol) 扩展客户端
│   │   └── client.py                # HavenMCPClient (连接外部 MCP Server & 转换 OpenAI Function Calling)
│   └── agent.py                     # HavenResearcher Agent 主控调度引擎
├── tests/                           # 全量自动化测试套件 (PyTest 25/25 全亮 Green 跑通)
├── main.py                          # CLI 命令行应用运行入口
└── setup.py                         # 可编辑包注册脚本
```

---

## 🧩 二、 Agent Skills 与 MCP 协议架构规范

```mermaid
graph TD
    Agent["HavenResearcher Agent 引擎"] --> SkillMgr["SkillManager (技能管理器)"]
    SkillMgr -->|扫描 haven_research/skills/| SKILL_MD["SKILL.md 技能说明书 (YAML Frontmatter)"]
    
    Agent --> MCPClient["HavenMCPClient (MCP 协议客户端)"]
    MCPClient -->|Stdio / HTTP SSE| MCPServer["外部 MCP Server (如 MySQL / GitHub / DevTools)"]
    MCPClient -->|list_tools() 动态拉取| FuncCalling["转换为 OpenAI Function Calling Schema"]
```

---

## ⚡ 三、 快速开始与测试

### 1. 运行 PyTest 自动化全量单测
```bash
python -m pytest tests/
```
*(通过率: **25/25 100% PASSED**)*

### 2. 运行端到端 Agent 深度研究任务
```bash
python main.py --query "2026年企业级 AI Agent 架构设计与技术选型"
```
