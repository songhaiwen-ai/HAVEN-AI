"""
haven_research/interpreter/tool.py - CodeInterpreter 解释器工具类

解析 Agent/LLM 输出的代码块 (```python ... ```)，
调用 PythonSandbox 执行代码，支持精细计算、Pandas 数据清洗与 Matplotlib 折线图/柱状图渲染。
"""

import re
import os
from typing import Dict, Any, List
from haven_research.core import logger
from .sandbox import PythonSandbox, ExecutionResultDTO


class CodeInterpreterTool:
    """代码解释器 Agent 工具封装"""

    def __init__(self, output_dir: str = "artifacts/charts"):
        self.sandbox = PythonSandbox(timeout_seconds=15.0)
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def extract_code_blocks(self, text: str) -> List[str]:
        """从 LLM 生成的自然语言中提取 ```python ``` 代码块"""
        pattern = r"```python\s*(.*?)\s*```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [m.strip() for m in matches if m.strip()]

    def run_interpreter(self, code_str: str) -> ExecutionResultDTO:
        """
        运行给定的 Python 代码并返回运行结果
        """
        # 如果代码包含 matplotlib 绘图，自动注入非 GUI 后端设置与图表保存逻辑
        if "matplotlib" in code_str or "plt." in code_str:
            setup_code = (
                "import matplotlib\n"
                "matplotlib.use('Agg')\n"
                "import matplotlib.pyplot as plt\n"
                "plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']\n"
                "plt.rcParams['axes.unicode_minus'] = False\n"
            )
            code_str = setup_code + "\n" + code_str

        return self.sandbox.execute_code(code_str)

    def process_llm_code_response(self, llm_response: str) -> Dict[str, Any]:
        """
        全自动解析并执行 LLM 回复中的所有代码块
        :return: 包含运行日志与生成的图片路径的结构化字典
        """
        code_blocks = self.extract_code_blocks(llm_response)
        if not code_blocks:
            return {"has_code": False, "results": []}

        results = []
        for idx, code in enumerate(code_blocks, 1):
            logger.info(f"[CodeInterpreter] 运行第 {idx}/{len(code_blocks)} 段 Python 代码...")
            res = self.run_interpreter(code)
            results.append({
                "code": code,
                "success": res.success,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "error": res.error
            })

        return {
            "has_code": True,
            "results": results
        }
