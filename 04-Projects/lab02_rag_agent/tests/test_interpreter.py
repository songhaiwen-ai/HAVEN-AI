"""
tests/test_interpreter.py - 重点 2: CodeInterpreter 代码解释器沙箱单元测试

测试 PythonSandbox 计算表达式求值、控制台输出捕获与 CodeInterpreterTool 提取执行能力。
"""

import pytest
from haven_research.interpreter import PythonSandbox, CodeInterpreterTool


def test_python_sandbox_calculation():
    """验证 PythonSandbox 精确数学计算能力"""
    sandbox = PythonSandbox(timeout_seconds=5.0)
    code = (
        "p0 = 10000\n"
        "p1 = 25000\n"
        "cagr = (p1 / p0) ** (1 / 3) - 1\n"
        "print(f'CAGR: {cagr:.4f}')\n"
    )
    res = sandbox.execute_code(code)
    
    assert res.success is True
    assert "CAGR: 0.3572" in res.stdout
    assert res.error == ""


def test_code_interpreter_tool_extraction():
    """验证 CodeInterpreterTool 解析 LLM ```python ``` 代码块能力"""
    tool = CodeInterpreterTool()
    llm_markdown = (
        "以下是计算逻辑：\n"
        "```python\n"
        "x = 50 + 50\n"
        "print(f'RESULT={x}')\n"
        "```\n"
        "报告结论完毕。"
    )
    
    extracted = tool.extract_code_blocks(llm_markdown)
    assert len(extracted) == 1
    assert "x = 50 + 50" in extracted[0]

    out = tool.process_llm_code_response(llm_markdown)
    assert out["has_code"] is True
    assert len(out["results"]) == 1
    assert out["results"][0]["success"] is True
    assert "RESULT=100" in out["results"][0]["stdout"]
