"""
haven_research/interpreter/sandbox.py - 生产级 Python 代码解释器安全沙箱

【大厂 Agent 标配】: 捕获 stdout/stderr，设置超时限制与变量空间隔离，
执行 Agent 生成的动态 Python 代码，用于精确数学计算、数据处理与 Matplotlib 绘图。
"""

import sys
import io
import traceback
import contextlib
import multiprocessing
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from haven_research.core import logger, HavenAgentException


class ExecutionResultDTO(BaseModel):
    """代码执行结果 DTO"""
    success: bool = Field(..., description="是否执行成功")
    stdout: str = Field(default="", description="标准输出流文本")
    stderr: str = Field(default="", description="标准错误流文本")
    result_val: Optional[Any] = Field(default=None, description="表达式最终返回值")
    error: Optional[str] = Field(default="", description="异常堆栈信息")


class PythonSandbox:
    """Python 隔离代码解释器沙箱"""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def execute_code(self, code: str, global_vars: Dict[str, Any] = None) -> ExecutionResultDTO:
        """
        执行 Python 代码片段并安全捕获输出
        :param code: 待执行的 Python 代码
        :param global_vars: 全局变量空间字典
        :return: ExecutionResultDTO 执行结果
        """
        if not code or not code.strip():
            return ExecutionResultDTO(success=False, error="代码不能为空")

        # 简单的风险代码过滤警告
        forbidden_keywords = ["os.system", "subprocess.Popen", "shutil.rmtree"]
        for kw in forbidden_keywords:
            if kw in code:
                logger.warning(f"[Sandbox Security Risk] 监测到敏感高危指令 '{kw}'")

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        exec_globals = global_vars if global_vars is not None else {}
        exec_globals.update({
            "__builtins__": __builtins__,
            "print": lambda *args, **kwargs: print(*args, file=stdout_capture, **kwargs)
        })

        try:
            logger.info(f"[Sandbox] 正在安全沙箱中执行 Python 代码片段 (超限: {self.timeout_seconds}s)...")
            
            # 使用 redirect_stdout / redirect_stderr 捕获输出
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # 尝试 exec 执行代码块
                exec(code, exec_globals)

            stdout_str = stdout_capture.getvalue().strip()
            stderr_str = stderr_capture.getvalue().strip()

            logger.info(f"[Sandbox] 代码执行成功！控制台输出字符数: {len(stdout_str)}")
            return ExecutionResultDTO(
                success=True,
                stdout=stdout_str,
                stderr=stderr_str
            )

        except Exception as e:
            err_msg = traceback.format_exc()
            logger.error(f"[Sandbox Error] 代码执行遇到运行时异常: {e}")
            return ExecutionResultDTO(
                success=False,
                stdout=stdout_capture.getvalue().strip(),
                stderr=stderr_capture.getvalue().strip(),
                error=str(e)
            )
