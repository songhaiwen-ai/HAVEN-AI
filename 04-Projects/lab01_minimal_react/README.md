# 💻 Lab 01: 手写 Minimal ReAct Agent Loop (最小智能体循环)

> **实战类型**：纯 Python 零依赖框架手撕  
> **面向人群**：Java 后端开发工程师 (用面向对象与后端架构视角解读)  
> **运行状态**：✅ 验证通过，已成功运行并输出履约 Track 轨迹

---

## 🎯 实验目的与核心收获

在不使用任何第三方 Agent 框架（如 LangChain, CrewAI, AutoGen）的前提下，用**纯 Python**实现底层的 **Observe → Think → Act → Observe** 控制循环。

通过本 Lab 的手写实战，可以彻底掌握：
1. 大模型是如何通过 System Prompt 约束输出 `Thought`（思考）与 `Action`（决策动作）的。
2. 如何手写一个工具注册表 (Tool Registry) 与派发器 (Tool Dispatcher)。
3. 如何通过维护一个全局 `messages` 对话列表（Session 上下文），把工具返回的 `Observation`（观察结果）闭环喂回给大脑。
4. 如何加入死循环保护 (`max_iterations`) 与异常抛错平滑处理。

---

## 📂 项目代码结构

* 📄 [**tools.py**](file:///c:/Haven-AI/04-Projects/lab01_minimal_react/tools.py)：定义工具函数、JSON Schema 说明与工具派发器。
* 📄 [**agent.py**](file:///c:/Haven-AI/04-Projects/lab01_minimal_react/agent.py)：定义 System Prompt、Action 文本解析器与 ReAct 主控制循环。
* 📄 [**main.py**](file:///c:/Haven-AI/04-Projects/lab01_minimal_react/main.py)：测试入口与任务轨迹履约统计。

---

## ☕ Java 后端视角概念映射表

| Python Agent 组件 | Java 后端对应概念 | 详细解读 |
| :--- | :--- | :--- |
| `TOOL_REGISTRY` | `Map<String, StrategyInterface>` 或 Spring `BeanFactory` | 用字典存储工具名到可执行函数的映射，实现策略模式与动态路由。 |
| `dispatch_tool()` | Spring `HandlerMapping` + `Reflection.invoke()` | 根据工具名和 JSON 参数动态派发调用具体的 Python 函数。 |
| `parse_action()` | Jackson `ObjectMapper` + 正则提取器 | 从 LLM 返回的自由文本中正则解析出 `Thought`、`Action` 与 JSON 格式的 `Action Input`。 |
| `messages` 列表 | `List<ChatMessage>` 或 Session 会话容器 | 贯穿全生命周期的状态上下文。每一次观察到的 `Observation` 都包装成新消息追加到列表末尾。 |
| `run_agent_loop()` | 后端主线程轮询循环 (Worker Loop / State Machine) | 带有 `max_iterations` 防死循环硬约束的逻辑主循环。 |

---

## 🚀 真实运行轨迹示例

```text
================ [START] 开启 Agent 自主任务循环 ================
[Goal] 用户目标: 请帮我查一下当前系统时间，然后计算 25 * 4 的值，最后运行 Python 校验输出结果。
[Limit] 最大循环保护次数: 5

------------ [Loop 01 / 05] ------------
[Think] 思考过程: 用户询问了系统时间，我需要先调用 get_system_time 工具获取当前时间。
[Act] 决定的动作: get_system_time | 参数: {}
[Act Execution] 正在派发执行工具 'get_system_time'...
[Observe] 环境返回结果 (Observation): 当前系统时间为: 2026-08-09 20:04:22 (Sunday)

------------ [Loop 02 / 05] ------------
[Think] 思考过程: 我已经获取到了系统时间。接下来用户要求计算 25 * 4 的值，我需要使用 calculator 工具。
[Act] 决定的动作: calculator | 参数: {'expression': '25 * 4'}
[Act Execution] 正在派发执行工具 'calculator'...
[Observe] 环境返回结果 (Observation): 计算表达式 '25 * 4' 的结果为: 100

------------ [Loop 03 / 05] ------------
[Think] 思考过程: 数学计算也完成了（结果为 100）。最后，我使用 execute_python_code 工具运行一段 Python 代码验证输出。
[Act] 决定的动作: execute_python_code | 参数: {'code': "result = 25 * 4\nprint(f'经过 Python 运算，最终结果为: {result}')"}
[Act Execution] 正在派发执行工具 'execute_python_code'...
[Observe] 环境返回结果 (Observation): 代码执行成功，标准输出结果: 经过 Python 运算，最终结果为: 100

------------ [Loop 04 / 05] ------------
[Think] 思考过程: 所有步骤均已完成，我向用户交付最终答案。
[Act] 决定的动作: None | 参数: {}

[Final Answer] 目标已达成!
[Output] 输出结果: 任务处理完成！当前系统时间查询、25 * 4 数学运算以及 Python 引擎测试均已执行完毕，结果完全正确。
```

---

*项目位置：[c:\Haven-AI\04-Projects\lab01_minimal_react](file:///c:/Haven-AI/04-Projects/lab01_minimal_react)*
