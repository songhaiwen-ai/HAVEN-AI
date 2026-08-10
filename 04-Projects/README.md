# 💻 04-Projects (实战项目与代码仓库)

“纸上得来终觉浅，绝知此事要躬行”。本目录包含所有配合知识库学习的**从零手撕代码与实战演练 Labs**。

---

## 🧪 规划实战 Labs 列表

### 📍 [**Lab 01: 手写 Minimal ReAct Agent**](file:///c:/Haven-AI/04-Projects/lab01_minimal_react/README.md) (`lab01_minimal_react`)
- **目标**：不使用任何第三方框架（仅用 `openai` SDK 或纯 Python），从零手写 ReAct 循环。
- **包含组件**：
  - 手写 System Prompt
  - 自定义函数工具（计算器、时间查询、代码执行）
  - 观察-思考-行动循环解析器与死循环防御

### 📍 Lab 02: 搭建企业私有文档 RAG 助手 (`lab02_rag_agent`)
- **目标**：结合 Chroma 向量数据库与 Python，构建可检索 PDF / Markdown 并进行引用的 QA Agent。

### 📍 Lab 03: 基于 LangGraph 的自我修正代码生成器 (`lab03_self_correcting_coder`)
- **目标**：使用 LangGraph 搭建带“反思 (Reflexion)”能力的 Agent：写代码 → 跑单元测试 → 失败则自动读 Traceback 并修正代码 → 重试直至测试通过。

### 📍 Lab 04: 基于 CrewAI 的自动化研报写作团队 (`lab04_research_team`)
- **目标**：配置 Researcher（分析师）、Writer（主编）和 Critic（审稿人）三个 Agent 协同完成深度行业报告。

---

*每个 Lab 都会创建独立的文件夹，包含 `README.md`（项目说明书）、`requirements.txt` 和可运行的 `.py` 代码脚本。*
