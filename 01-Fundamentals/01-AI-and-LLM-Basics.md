# 01-AI-and-LLM-Basics: 大语言模型（LLM）与 AI 基础概念

大语言模型（Large Language Model, LLM）是构建现代 AI Agent 的“大脑”。要理解 Agent，首先需要掌握 LLM 的基本概念与核心机制。

---

## 1. 什么是大语言模型（LLM）？

大语言模型本质上是一个**基于 Transformer 架构的概率预测模型**。它的核心任务是：**根据前面已有的 Token 序列，预测下一个最可能出现的 Token**。

> 概率语言模型公式：`P(下一个 Token | 已有 Token 序列)`

虽然原理看起来只是“文字接龙”，但当模型参数量达到百亿（10B）、千亿（100B）级别，并在海量互联网文本上训练后，模型展现出了**涌现能力（Emergent Abilities）**，包括逻辑推理、代码编写、角色扮演和指令遵循等。

---

## 2. 核心关键概念解析

### 2.1 Token（文本元）
- **概念**：LLM 处理文本的基本单位，不是单纯的“单词”或“汉字”，而是切分后的文本片段。
- **换算经验**：
  - 英文：约 100 个 Token ≈ 75 个单词。
  - 中文：1 个汉字通常占用 1 ~ 2 个 Token（取决于 Tokenizer 词表算法，如 BPE/SentencePiece）。

### 2.2 Context Window（上下文窗口）
- **概念**：模型单次处理（输入 + 输出）的最大 Token 数量上限。
- **演进**：从早期的 4K / 8K，演进到现在的 128K（GPT-4o）、1M/2M（Gemini 1.5 Pro / Claude 3.5）。
- **Agent 关联**：上下文窗口决定了 Agent 的“短期记忆容量”。窗口越大，Agent 能单次读取的文档和历史对话就越长。

### 2.3 关键采样参数 (Temperature & Top-P)

| 参数 | 含义 | 建议配置 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **Temperature** | 控制生成文本的随机性/创造力。值越低越确定，值越高越丰富。 | `0.0 - 0.2` (精确逻辑/代码)<br>`0.7 - 1.0` (创意写作) | Agent 进行工具调用和 JSON 输出时，推荐设为 **0.0** 以保证格式稳定。 |
| **Top-P (Nucleus Sampling)** | 仅从累积概率达到 P 的 Token 候选池中选择。 | 通常保持默认 `1.0` 或与 Temperature 二选一调整。 | 细粒度控制输出多样性。 |

### 2.4 Embedding（向量嵌入）与 Vector DB（向量数据库）
- **Embedding**：将高维文本映射为高维数值向量（如 1536 维），使得语义相近的文本在向量空间中的距离更近（通过余弦相似度 Cosine Similarity 计算）。
- **Vector DB**：专门用于高维向量存储与快速近邻搜索（ANN）的数据库（如 Chroma, Qdrant, Milvus, Pinecone）。
- **Agent 关联**：Vector DB 是 Agent 实现**检索增强生成（RAG）**与**长期记忆**的核心组件。

---

## 3. Prompt 工程与 Agent 的连接

Prompt（提示词）是人类与 LLM 沟通的桥梁，也是控制 Agent 行为的核心指令。

### 3.1 提示词的三层结构
1. **System Prompt (系统提示词)**：设定 Agent 的身份、角色、能力边界、输出格式限制及行为准则。
2. **User Prompt (用户输入)**：用户当前提出的问题或任务请求。
3. **Assistant Prompt (助手输出 / Context)**：模型生成的历史回复或思考过程。

### 3.2 提升 LLM 推理能力的关键技术
- **Few-Shot Learning (少样本提示)**：在 Prompt 中提供 1~3 个标准输入输出示例，极大地提高模型的输出准确率与格式稳定性。
- **Chain-of-Thought (CoT, 思维链)**：引导模型在给出最终答案前，显式写出思考步骤（例如：“请一步步思考并解答…”）。这是 Agent 进行复杂规划（Planning）的基础。

---

## 4. 小结与下一阶段

了解了 LLM 的基本原理后，我们知道 LLM 本身是**被动**且**无状态**的（你问一句，它答一句）。要让它变成能够**自主思考、使用工具、执行复杂任务**的智能体，就需要引入 **Agent 架构**。

👉 下一步请阅读：[02-Agent-Architecture/01-What-is-an-Agent.md](file:///c:/Haven-AI/02-Agent-Architecture/01-What-is-an-Agent.md)
