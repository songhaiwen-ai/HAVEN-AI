# 🛠️ 03-Frameworks-and-Tools (主流框架与工具箱)

本模块记录开发 AI Agent 所需的开源框架、协议与生态工具。

---

## 1. 核心 Agent 框架对比

| 框架名称 | 开发语言 | 核心特点与擅长场景 | 推荐指数 |
| :--- | :--- | :--- | :--- |
| **LangChain / LangGraph** | Python / TS | 生态最庞大。LangGraph 引入基于**图 (Graph)** 的状态机模型，支持复杂的循环与分支控制。 | ⭐⭐⭐⭐⭐ |
| **LlamaIndex** | Python / TS | 专注于 **RAG (检索增强生成)** 与数据源连接，适合搭建基于私有数据知识库的 Agent。 | ⭐⭐⭐⭐ |
| **AutoGen (Microsoft)** | Python | 微软开源的**多 Agent 协作框架**，擅长复杂对话、代码生成与多角色协同。 | ⭐⭐⭐⭐ |
| **CrewAI** | Python | 强调基于**角色扮演 (Role-Playing)** 的智能体团队协作，上手简单，语义化强。 | ⭐⭐⭐⭐ |
| **OpenAI Assistants API** | API 服务 | 开箱即用的内置 Code Interpreter、Retrieval 和 Function Calling。 | ⭐⭐⭐ |

---

## 2. 协议标准：MCP (Model Context Protocol)

**MCP (模型上下文协议)** 是由 Anthropic 提出的开放标准，旨在标准化 LLM / Agent 如何连接本地与远程的数据源、工具及上下文（类比为 AI 时代的 USB 接口）。

- **MCP Client**：Agent 或 IDE（如 Claude Desktop, Antigravity）。
- **MCP Server**：暴露出工具（Tools）、资源（Resources）和提示词（Prompts）的独立服务。

---

## 3. 📚 本目录官方指南与技术归档

- 📄 [**01-OpenAI-Function-Calling-Guide.md**](file:///c:/Haven-AI/03-Frameworks-and-Tools/01-OpenAI-Function-Calling-Guide.md)
  - OpenAI 官方 Function Calling 权威指南与 5 步生命周期拆解
  - Strict Mode (严格模式强约束)、并行函数调用 (Parallel Function Calling)
  - Java 后端视角概念映射与手写 ReAct 正则对比表
- 📄 [**02-Google-Gemini-Function-Calling-Guide.md**](file:///c:/Haven-AI/03-Frameworks-and-Tools/02-Google-Gemini-Function-Calling-Guide.md)
  - Google Gemini 官方 Function Calling 权威指南与 Interactions API
  - 多模态函数响应 (返回图片 Base64)、远程 MCP 服务器集成、Google Search 混用
  - 独创update() 专用工具避开前置文本报错解法与 OpenAI 横向对比表
- 📄 [**03-Anthropic-Claude-Tool-Use-Guide.md**](file:///c:/Haven-AI/03-Frameworks-and-Tools/03-Anthropic-Claude-Tool-Use-Guide.md)
  - Anthropic Claude 官方 Tool Use 权威指南与 Messages API 交互闭环
  - 三维工具划分 (Client / Schema-Client / Server Tools)、Advisor Tool 导师模式
  - SDK Tool Runner 自动轮询、系统提示词 Token 消耗明细与三大巨头横向对比表
- `02-LlamaIndex-RAG-Agent.md`: 数据检索 Agent 搭建指南。
- `03-CrewAI-Multi-Agent.md`: 多 Agent 团队配置指南。
- `04-MCP-Protocol.md`: 编写你的第一个 MCP Server。
