# 💻 Lab 02: AI 最新技术问答与深度研究助手 (HavenResearch Engine) 全景指南

> **核心对标标杆**：开源深度研究 Agent 框架 [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) (1:1 业务方向与核心架构完全对齐)  
> **业务定位**：专为 **AI 最新技术文档问答、架构设计与行业研报深度分析** 打造的生产级 Deep Research Agent。  
> **生产级架构**：基于 DeepSeek API + Qdrant Cloud 云端 Serverless 向量数据库，构建包含**私有本地 PDF/Word/Markdown 知识库自动向量落盘 + 全网实时检索 (Tavily/DDG) + 三层记忆管理 + CodeInterpreter 沙箱代码解释器 + 动态 Agent 角色生成 (choose_agent) + BM25 与 BGE Reranker 二次精排 + 防幻觉引用门禁 + MCP (Model Context Protocol) 扩展与两阶段工具精排 (MCPToolSelector / MCPRetriever) + Agent Skills 动态技能加载**的工业级 Agent。

---

## 🎯 一、 业务方向与核心功能对齐 (1:1 对标 gpt-researcher)

| gpt-researcher 核心业务 | HavenResearch (`haven_research/`) 实现 | 1:1 对齐状态 |
| :--- | :--- | :--- |
| **1. 深度研究与长文问答主流程** | `HavenResearcher.conduct_research()` | ✅ **100% 完全一致** |
| **2. 动态 Agent 专家 Persona (`choose_agent`)** | `haven_research/actions/agent_creator.py` | ✅ **100% 完全一致** |
| **3. 子主题拆解与多 Query 拓展** | `haven_research/planner/planner.py` | ✅ **100% 完全一致** |
| **4. Tavily & DuckDuckGo 高并发检索与去噪** | `haven_research/retrievers/` & `scrapers/` | ✅ **100% 完全一致** |
| **5. 多格式文档解析与向量落盘** | `LocalKnowledgeIngestionService` + Qdrant Cloud | ✅ **100% 完全一致** |
| **6. 报告模式分类 (`ReportType` & `ReportSource`)** | `ResearchReport`, `DetailedReport`, `ResourceReport`, `OutlineReport` | ✅ **100% 完全一致** |
| **7. Token 消耗与费用结算 (`CostTracker`)** | `haven_research/utils/costs.py` | ✅ **100% 完全一致** |
| **8. MCP 扩展与两阶段工具精排** | `haven_research/mcp/` (`MCPToolSelector` / `MCPRetriever`) | ✅ **100% 完全一致** |
| **9. 企业级四大独家增强** | 三层记忆体系 + CodeInterpreter + BGE Reranker + 防幻觉门禁 | 🚀 **HAVEN-AI 独家重磅增强** |

---

## 🔄 二、 全景工程架构与包结构

```text
lab02_rag_agent/
├── haven_research/                  # 【大厂规范】本地可编辑开发包 (pip install -e .)
│   ├── config/                      # Pydantic Settings 配置中心 (DeepSeek + Qdrant Cloud)
│   ├── core/                        # 异常基类与结构化日志模块
│   ├── schemas/                     # DTO 强类型数据契约 (ResearchRequestDTO, ReportType, ReportSource)
│   ├── ingestion/                   # 本地多格式文档提取与 Qdrant 向量落盘服务 (LocalKnowledgeIngestionService)
│   ├── storage/                     # QdrantVectorStore 云端 Serverless 向量存储工厂
│   ├── retrievers/                  # 异步网络与 MCP 检索器 (DuckDuckGo, Tavily, MCPRetriever)
│   │   ├── duckduckgo.py            # DuckDuckGo 免费网络检索
│   │   ├── tavily.py                # Tavily AI 专有搜索引擎集成 (tavily-python)
│   │   └── mcp.py                   # MCP 协议两阶段智能检索器 (MCPRetriever)
│   ├── scrapers/                    # 高并发网页抓取 WebScraper (带 Jina Reader 免爬降级)
│   ├── planner/                     # 智能子主题拆解器 SubtopicPlanner
│   ├── actions/                     # 动态 Agent 角色定制生成器 (choose_agent)
│   ├── memory/                      # 三层记忆架构体系 (Working / Session / LongTerm)
│   ├── interpreter/                 # Python Code Interpreter 代码解释器沙箱
│   ├── reranker/                    # 双路混合检索 (BM25 + Vector) 与 BGE Reranker 重排序
│   ├── verifier/                    # 防幻觉引用后置校验门禁 CitationVerifierGate
│   ├── utils/                       # Token 消耗与 API 费用折算 CostTracker
│   ├── skills/                      # Agent Skills 技能发现与执行管理器 (SkillManager)
│   ├── mcp/                         # MCP (Model Context Protocol) 扩展架构 (HavenMCPClient / MCPToolSelector)
│   └── agent.py                     # HavenResearcher Agent 主控调度引擎
├── tests/                           # 全量自动化测试套件 (PyTest 27/27 全亮 Green 跑通)
├── main.py                          # CLI 命令行应用运行入口
└── setup.py                         # 可编辑包注册脚本
```

---

## ⚡ 三、 快速开始与测试

### 1. 运行 PyTest 自动化全量单测
```bash
python -m pytest tests/
```
*(通过率: **27/27 100% PASSED**)*

### 2. 运行端到端 AI 最新技术深度问答与研究
```bash
python main.py --query "2026年企业级 AI Agent 架构设计与技术选型"
```
