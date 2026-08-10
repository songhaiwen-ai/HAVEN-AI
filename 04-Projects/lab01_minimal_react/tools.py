"""
tools.py - 自定义 Python 工具箱与工具注册表 (Tool Registry)

【Java 后端工程师视角】：
在 Java 开发中，如果你想根据字符串动态调用某个业务逻辑，通常有两种做法：
1. 策略模式 (Strategy Pattern)：定义接口 `ToolStrategy`，实现类注册到 `Map<String, ToolStrategy>` 中。
2. 反射 (Reflection) / Spring Bean 容器：通过 `@Component("toolName")` 或 Method 反射直接调用。

在 Python 中，函数是一等公民 (First-class Function)。我们可以使用装饰器 (Decorator)
或者直接用字典 `dict` 维护一个 `TOOL_REGISTRY`（类似于 Spring 的 Bean Factory）。
"""

import datetime
import math
import sys
from typing import Callable, Dict, Any, List


def get_system_time(args_json: Dict[str, Any] = None) -> str:
    """
    工具 1: 获取当前的系统精确日期与时间。
    
    :param args_json: 无需额外入参
    :return: 当前格式化的日期时间字符串
    """
    now = datetime.datetime.now()
    return f"当前系统时间为: {now.strftime('%Y-%m-%d %H:%M:%S (%A)')}"


def calculator(expression: str) -> str:
    """
    工具 2: 执行数学表达式计算 (支持加减乘除、乘方、开方等)。
    
    【Java 对齐】：类似于在 Java 中调用 Spring SpEL 表达式解析器，或者 Aviator 脚本引擎。
    
    :param expression: 数学表达式，如 "2 ** 10 + sqrt(144)"
    :return: 计算结果字符串
    """
    try:
        # 安全受限的环境中评估数学表达式
        safe_dict = {
            "sqrt": math.sqrt,
            "pow": math.pow,
            "sin": math.sin,
            "cos": math.cos,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "round": round
        }
        result = eval(expression, {"__builtins__": None}, safe_dict)
        return f"计算表达式 '{expression}' 的结果为: {result}"
    except Exception as e:
        return f"计算表达式失败，错误信息: {type(e).__name__}: {str(e)}"


def execute_python_code(code: str) -> str:
    """
    工具 3: 动态 Python 代码解释器。
    
    【Java 对齐】：类似于 Java 中的 GroovyScriptEngine 或 JShell 动态代码执行器。
    
    :param code: 待执行的 Python 代码字符串
    :return: 代码的标准输出 (stdout) 或报错信息
    """
    import io
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        # 在独立的局部作用域中执行代码
        exec_scope = {}
        exec(code, exec_scope)
        output = redirected_output.getvalue().strip()
        if not output:
            output = "代码执行成功，但没有 stdout 输出。"
        return f"代码执行成功，标准输出结果:\n{output}"
    except Exception as e:
        return f"代码执行异常，抛出错误:\n{type(e).__name__}: {str(e)}"
    finally:
        sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# 工具注册表与 Tool Schema 定义 (类似 Spring Bean 注册与 Swagger OpenAPI 描述)
# ---------------------------------------------------------------------------

# 1. 简易注册表字典: ToolName -> Callable
TOOL_REGISTRY: Dict[str, Callable] = {
    "get_system_time": get_system_time,
    "calculator": calculator,
    "execute_python_code": execute_python_code
}

# 2. 供 LLM 阅读的工具 Schema 定义（告诉 LLM 有哪些工具、怎么用）
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "get_system_time",
        "description": "获取当前精确的系统日期和时间（包含星期几）。无入参。",
        "parameters": {}
    },
    {
        "name": "calculator",
        "description": "用于进行精密数学运算的计算器。入参为合法数学表达式字符串。",
        "parameters": {
            "expression": "例如 '1024 * 3.14 + sqrt(16)'"
        }
    },
    {
        "name": "execute_python_code",
        "description": "动态运行一段 Python 脚本并捕获其 print() 输出。用于复杂逻辑推理、算法处理与数据整理。",
        "parameters": {
            "code": "多行 Python 代码字符串，必须包含 print() 才能获取输出结果"
        }
    }
]


def dispatch_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """
    工具调度器 (Tool Dispatcher)
    
    【Java 对齐】：类似于 Spring MVC 的 HandlerMapping 路由 + Reflection.invoke() 执行方法！
    """
    if tool_name not in TOOL_REGISTRY:
        return f"错误: 找不到名为 '{tool_name}' 的工具！可用工具列表: {list(TOOL_REGISTRY.keys())}"
    
    tool_func = TOOL_REGISTRY[tool_name]
    try:
        # 兼容无参和带参函数调用
        if not tool_args:
            return tool_func()
        elif isinstance(tool_args, dict):
            return tool_func(**tool_args)
        elif isinstance(tool_args, str):
            # 处理部分 LLM 只传单字符串参数的情况
            return tool_func(tool_args)
        else:
            return tool_func(tool_args)
    except TypeError as te:
        return f"工具参数传递类型错误: {str(te)}"
    except Exception as e:
        return f"工具执行阶段抛出未知异常: {type(e).__name__}: {str(e)}"
