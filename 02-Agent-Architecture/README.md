# 🏗️ 02-Agent-Architecture (Agent 核心架构与设计模式)

本目录涵盖 AI Agent 核心理论、四大支柱、控制循环、反模式决策树以及 Anthropic 官方生产实践总结。

---

## 📂 目录导航（建议阅读顺序）

1. 📄 [**01-What-is-an-Agent.md**](file:///c:/Haven-AI/02-Agent-Architecture/01-What-is-an-Agent.md)
   - 什么是 AI Agent？（经典公式：Agent = LLM + 感知 + 规划 + 记忆 + 工具）
   - Agent 的四大核心支柱拆解
   - ReAct 模式全景推演

2. 📄 [**02-Chatbot-vs-Workflow-vs-Agent-vs-MultiAgent.md**](file:///c:/Haven-AI/02-Agent-Architecture/02-Chatbot-vs-Workflow-vs-Agent-vs-MultiAgent.md)
   - 四大模式对比与通俗比喻（前台、流水线、PM、跨功能团队）
   - 控制权、自主性、确定性对比矩阵
   - 技术选型逻辑树

3. 📄 [**03-Agent-Basic-Loop-Observe-Think-Act.md**](file:///c:/Haven-AI/02-Agent-Architecture/03-Agent-Basic-Loop-Observe-Think-Act.md)
   - Observe → Think → Act → Observe 核心自主循环深度拆解
   - 真实 Trace 闭环推演
   - 死循环、上下文膨胀、解析错误、错误盲目死磕四大工程死穴与解法

4. 📄 [**04-When-NOT-to-use-an-Agent.md**](file:///c:/Haven-AI/02-Agent-Architecture/04-When-NOT-to-use-an-Agent.md)
   - 什么时候绝对不该用 Agent？（反盲目 Agent 化指南）
   - 四大禁区（流程硬编码、低延迟、100% 精确、高风险无监督）
   - 评估决策树与优雅替代架构

5. 📄 [**05-Anthropic-Building-Effective-Agents.md**](file:///c:/Haven-AI/02-Agent-Architecture/05-Anthropic-Building-Effective-Agents.md)
   - Anthropic 官方工程实践指南总结
   - 重新划清 Workflows 与 Agents 界限
   - 5 大黄金架构模式（Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer）
   - 附录一：Agent 最佳落地方向（智能客服与代码 Agent SWE-bench）
   - 附录二：工具提示词工程与 ACI 防呆设计（Poka-yoke 与绝对路径硬约束）

6. 📄 [**06-OpenAI-Practical-Guide-to-Building-Agents.md**](file:///c:/Haven-AI/02-Agent-Architecture/06-OpenAI-Practical-Guide-to-Building-Agents.md)
   - OpenAI 官方白皮书指南总结（从 Chatbot 到 Agent 的 5 级演进）
   - Agent 系统三大核心原语（Model / Tools / Context）
   - 多 Agent 编排模式（Supervisor 管理者模式 vs Hand-off 转交模式）
   - 三层安全防护网（Guardrails & Safety Gates）与 Eval 评估迭代法

7. 📄 [**07-Short-Note-Why-Agent-Over-Workflow.md**](file:///c:/Haven-AI/02-Agent-Architecture/07-Short-Note-Why-Agent-Over-Workflow.md)
   - 一页纸短笔记卡片：我的场景为什么需要 Agent，而不是普通 Workflow？
   - 三大分水岭测试（分支爆炸、错误自愈、目标导向测试）
