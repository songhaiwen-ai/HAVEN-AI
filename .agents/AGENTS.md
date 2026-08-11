# Workspace Rules for Haven-AI

## Markdown & Typora Compatibility Rules

为了保证生成的 Markdown 在 Typora、Obsidian、GitHub 等各种渲染器中 100% 无报错、清爽美观，在编写任何文档时必须严格遵守以下排版规范：

1. **禁用含中文/表情符号的 LaTeX 数学公式块**：
   - 严禁写 `$$\text{AI Agent} = \text{LLM (大脑)} ...$$` 或在 `\text{...}` 中包含中文字符和 Emoji，这会在 Typora 内置的 MathJax 中触发变红报错。
   - 替代方案：一律使用原生 Markdown 引用块（`>`）与加粗文本表示公式结构。

2. **禁用 `$\rightarrow$` 转义字符作为普通文本箭头**：
   - 严禁在正文列表中写 `$\rightarrow$`。
   - 替代方案：一律使用直观、原生的 Unicode 实体箭头 `→`。

3. **Mermaid 流程图全版本兼容规范**：
   - 所有节点的文本标签必须使用**双引号**完全包裹，格式为 `NodeID["节点描述文本"]`。
   - 严禁在 `subgraph` 名称中直接出现未带引号的空格或特殊字符，格式必须为 `subgraph SG1 ["标题描述"]`。

## User Profile & Teaching Rules

1. **用户背景 (User Background)**：
   - 角色：Java 后端开发工程师（精通 Java, Spring Boot, 设计模式, REST API, JVM 等）。
   - Python 能力：具备 Python 基本语法能力，属于 AI / Agent 初学者。

2. **教学与代码编写原则 (Teaching Principles)**：
   - **客观严谨的技术讲解**：直接聚焦于 AI / Agent 架构、原理、算法与代码实现本身，保持纯粹、标准、通用的技术文档风格，无需刻意与 Java 概念做对比。
   - **代码简洁易懂**：Python 代码需保持结构清晰、注释详尽，类型提示 (Type Hints) 标注规范。
