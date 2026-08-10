"""
agent.py - 手写 ReAct 核心自主循环引擎 (Observe-Think-Act-Observe Loop)

【Java 后端工程师视角】：
在 Java 中，如果你想构建一个死循环轮询或状态机，通常会用：
`while (running) { state = state.next(observation); }`

在这里，`run_agent_loop` 函数就是 Agent 的**核心中央处理循环 (Control Loop)**。
它维护着一个状态上下文 `messages`（类似于 Java 中的 ThreadLocal 或状态机 Session 容器），
每一轮循环中：
1. 观察当前状态 (Observe)
2. 调大模型思考并生成指令 (Think)
3. 解析并调用外部工具或抛出最终答案 (Act)
4. 将工具执行结果追加回状态容器，开启下一轮迭代！
"""

import json
import re
import sys
from typing import List, Dict, Any, Tuple

# 兼容 Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 引入我们刚才在 tools.py 中定义的工具调度器与 Schema 描述
from tools import dispatch_tool, TOOLS_SCHEMA


# ---------------------------------------------------------------------------
# System Prompt 模板设计 (约束大模型输出严格的 ReAct 思考与行动格式)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""你是一个具备自主思考与工具调用能力的 AI Agent。
你的任务是解决用户提出的问题。请一步步思考，并严格按照下面的格式进行输出：

【思考与行动格式规范】:
Thought: <对当前问题的分析、评估与下一步行动规划>
Action: <准备调用的工具名称，必须是 [{', '.join([t['name'] for t in TOOLS_SCHEMA])}] 中的一个，若已得出最终答案则写 'None'>
Action Input: <传递给工具的参数，格式必须是合法的 JSON 对象，例如 {{"expression": "2 + 2"}} >

【完成任务格式规范】:
当你收集到了足够的信息，能够直接回答用户问题时，请使用以下格式终止循环：
Thought: 我已经获得了足够的信息，可以回答用户的问题。
Action: None
Action Input: {{}}
Final Answer: <最终给用户的详细解答>

【可用的工具列表 (Available Tools)】:
{json.dumps(TOOLS_SCHEMA, ensure_ascii=False, indent=2)}

【硬性约束规则】:
1. 每轮回复中，你必须且只能包含一组 Thought / Action / Action Input。
2. 如果 Action 不是 None，则 Action Input 必须是合法的 JSON 字典格式。
3. 请务必保持客观，不要伪造或虚构工具返回的结果。
"""


def parse_action(text: str) -> Tuple[str, str, Dict[str, Any], str]:
    """
    Action 解析器 (Parser)
    
    【Java 对齐】：类似于 Java 中的正则表达式解析器或 JSON 反序列化器 (Jackson ObjectMapper)。
    从 LLM 输出的文本中提取 Thought、Action、Action Input 和 Final Answer。
    
    :param text: LLM 输出的原始文本
    :return: (thought, action, action_input, final_answer)
    """
    thought = ""
    action = ""
    action_input_dict = {}
    final_answer = ""

    # 1. 提取 Thought
    thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()

    # 2. 检查是否有 Final Answer
    final_answer_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)
    if final_answer_match:
        final_answer = final_answer_match.group(1).strip()
        return thought, "None", {}, final_answer

    # 3. 提取 Action
    action_match = re.search(r"Action:\s*(.*)", text)
    if action_match:
        action = action_match.group(1).strip()

    # 4. 提取 Action Input 并解析为 Dict
    action_input_match = re.search(r"Action Input:\s*(.*)", text, re.DOTALL)
    if action_input_match:
        raw_input_str = action_input_match.group(1).strip()
        try:
            action_input_dict = json.loads(raw_input_str)
        except json.JSONDecodeError:
            # 如果大模型直接传了非 JSON 的纯文本/表达式，做兼容兜底处理
            action_input_dict = {"raw_input": raw_input_str}

    return thought, action, action_input_dict, final_answer


def mock_llm_reasoning(messages: List[Dict[str, str]], iteration: int) -> str:
    """
    模拟大模型推理函数 (Mock LLM)
    
    在用户没有配置真实的 API Key 时，用于进行规则驱动的模拟测试，
    完整展示 Observe -> Think -> Act 的数据流运转。
    """
    if iteration == 1:
        return """Thought: 用户询问了系统时间，我需要先调用 get_system_time 工具获取当前时间。
Action: get_system_time
Action Input: {}"""
    elif iteration == 2:
        return """Thought: 我已经获取到了系统时间。接下来用户要求计算 25 * 4 的值，我需要使用 calculator 工具。
Action: calculator
Action Input: {"expression": "25 * 4"}"""
    elif iteration == 3:
        return """Thought: 数学计算也完成了（结果为 100）。最后，我使用 execute_python_code 工具运行一段 Python 代码验证输出。
Action: execute_python_code
Action Input: {"code": "result = 25 * 4\\nprint(f'经过 Python 运算，最终结果为: {result}')"}"""
    else:
        return """Thought: 所有步骤均已完成，我向用户交付最终答案。
Action: None
Action Input: {}
Final Answer: 任务处理完成！当前系统时间查询、25 * 4 数学运算以及 Python 引擎测试均已执行完毕，结果完全正确。"""


def run_agent_loop(user_goal: str, max_iterations: int = 5, llm_client=None) -> Dict[str, Any]:
    """
    ReAct 主控制循环 (Main Control Loop)
    
    【Java 对齐】：类似于后台主工作线程循环 (Worker Loop)。
    
    :param user_goal: 用户提交的终极目标
    :param max_iterations: 最大允许循环轮数（防止无限死循环）
    :param llm_client: 真实 OpenAI / SDK 客户端 (为 None 时自动降级为 Mock 模式)
    :return: 包含完整执行轨迹与最终结果的字典
    """
    print(f"\n================ [START] 开启 Agent 自主任务循环 ================")
    print(f"[Goal] 用户目标: {user_goal}")
    print(f"[Limit] 最大循环保护次数: {max_iterations}\n")

    # 初始化对话上下文容器 (类似 Java 中的 Session 状态容器)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal}
    ]

    execution_trace = []  # 记录履约轨迹

    for iteration in range(1, max_iterations + 1):
        print(f"------------ [Loop 0{iteration} / 0{max_iterations}] ------------")

        # -------------------------------------------------------------------
        # 阶段二：Think (思考与推理)
        # -------------------------------------------------------------------
        if llm_client is not None:
            # 真实 API 调用模式
            try:
                response = llm_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.0
                )
                llm_output = response.choices[0].message.content
            except Exception as e:
                llm_output = f"Thought: 调用大模型 API 发生异常，准备终止。\nAction: None\nFinal Answer: 无法连接 LLM API: {str(e)}"
        else:
            # 本地 Mock 模式（确保零配置开箱即用体验）
            llm_output = mock_llm_reasoning(messages, iteration)

        # 追加思考记录到历史
        messages.append({"role": "assistant", "content": llm_output})

        # 格式化解析 LLM 的思考与动作
        thought, action, action_input, final_answer = parse_action(llm_output)

        print(f"[Think] 思考过程:\n   {thought}")
        print(f"[Act] 决定的动作: {action} | 参数: {action_input}")

        # 记录本轮追踪
        trace_step = {
            "loop": iteration,
            "thought": thought,
            "action": action,
            "action_input": action_input
        }

        # -------------------------------------------------------------------
        # 判断终止条件：达成目标 Final Answer
        # -------------------------------------------------------------------
        if action == "None" or final_answer:
            print(f"\n[Final Answer] 目标已达成!")
            print(f"[Output] 输出结果:\n{final_answer}\n")
            trace_step["observation"] = "Final Answer Delivered"
            execution_trace.append(trace_step)
            return {
                "success": True,
                "final_answer": final_answer,
                "loops_used": iteration,
                "trace": execution_trace
            }

        # -------------------------------------------------------------------
        # 阶段三：Act (在真实环境中执行动作/工具)
        # -------------------------------------------------------------------
        print(f"[Act Execution] 正在派发执行工具 '{action}'...")
        tool_observation = dispatch_tool(action, action_input)
        print(f"[Observe] 环境返回结果 (Observation):\n   {tool_observation}\n")

        trace_step["observation"] = tool_observation
        execution_trace.append(trace_step)

        # -------------------------------------------------------------------
        # 阶段四：Observe (再观察 - 闭环反馈!)
        # 关键步骤: 把 Observation 包装成 User 消息喂回给 LLM 大脑！
        # -------------------------------------------------------------------
        observation_prompt = f"Observation: {tool_observation}"
        messages.append({"role": "user", "content": observation_prompt})

    # 如果超过了最大迭代次数，触发死循环保护
    print(f"\n[Warning] 已达到最大循环上限 ({max_iterations} 轮)，防死循环触发！")
    return {
        "success": False,
        "final_answer": f"任务超时: 已达到最大允许迭代轮次 ({max_iterations})。",
        "loops_used": max_iterations,
        "trace": execution_trace
    }
