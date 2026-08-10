# ❓ 05-FAQ-and-Troubleshooting (问题总结与踩坑记录)

本目录用于记录在 AI Agent 学习、开发、调优过程中遇到的**所有疑难杂症、报错日志及解决方案**。

---

## 📝 记录模板 (Template)

遇到新问题时，请使用以下格式记录：

```markdown
### [问题分类] 简要描述问题标题

- **时间**：YYYY-MM-DD
- **环境**：Python 3.x / LangChain 0.x / Windows 11
- **现象 / 报错信息**：
  ```text
  [贴出具体报错 Traceback 信息]
  ```
- **根本原因 (Root Cause)**：
  分析为什么会发生这个错误。
- **解决方案 (Solution)**：
  具体的代码修改或配置调整方法。
```

---

## 🔍 已归档问题检索

| 编号 | 问题主题 | 标签 | 链接 |
| :--- | :--- | :--- | :--- |
| FAQ-001 | LLM 工具调用返回 JSON 解析失败 / 格式混乱 | `Function Calling` `JSON` | 待填充 |
| FAQ-002 | Agent 死循环（无限反复调用同一工具）的防护机制 | `ReAct` `Infinite Loop` | 待填充 |
| FAQ-003 | Windows 下终端编码问题 (UTF-8 / GBK) 导致 Shell 工具乱码 | `Windows` `Encoding` | 待填充 |
| FAQ-004 | Typora Markdown 渲染报错问题（Mermaid 兼容性与 LaTeX 数学公式陷阱） | `Typora` `Markdown` `Mermaid` | [查看规则](file:///c:/Haven-AI/.agents/AGENTS.md) |
| FAQ-005 | 为什么在 Function Calling 中输出前置思考文本会导致 Malformed_Function_Call 报错？如何用 update() 工具优雅解决？ | `Function Calling` `Gemini` `Workaround` | [查看详解](file:///c:/Haven-AI/03-Frameworks-and-Tools/02-Google-Gemini-Function-Calling-Guide.md#4-工具前文本报错的官方首选解法-preferred-workaround-硬核工程坑点) |

---

## 📖 核心问题详解归档

### [FAQ-005] 为什么在 Function Calling 中输出前置思考文本会导致 Malformed_Function_Call 报错？

- **现象 / 报错信息**：
  在 Prompt 中要求大模型在调用 API 工具前，先输出一段结构化文本或 XML 思考日志（如 `<UPDATE>分析步骤...</UPDATE>`），API 报错：
  `Malformed_Function_Call: Invalid protocol response payload.`
- **根本原因 (Java 后端视角)**：
  Function Calling 要求模型响应为 100% 纯净的 JSON 协议。前半段输出 XML 文本、后半段切 JSON 会导致 API 服务端的反序列化解析器（如 Jackson/JSONParser）因为格式混合而抛出 `JsonParseException` 协议失败。
- **解决方案 (Solution)**：
  不要让模型吐前置 XML 文本，而是声明一个专用的日志工具 `update(previous_step, plan, next_step, external)`。模型在同一步骤中同时发起两次函数调用（第一次调 `update()` 记日志，第二次调业务工具），既遵守了纯 JSON 协议，又实现了类似 Java **AOP 日志切面** 的审计追踪！
