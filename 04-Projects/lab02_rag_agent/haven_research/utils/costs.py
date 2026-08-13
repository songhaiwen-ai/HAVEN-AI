"""
haven_research/utils/costs.py - 生产级 Token 消耗与费用追踪器

【1:1 对标 gpt-researcher】: gpt_researcher/utils/costs.py
精准统计 LLM Prompt Tokens, Completion Tokens, 向量 Embeddings 开销与折算总费用。
"""

from typing import Dict, Any
from haven_research.core import logger


class CostTracker:
    """Token 消耗与 API 费用追踪器"""

    # 单位: 美元 / 1K Tokens (DeepSeek-V3 计费标准)
    PRICE_PER_1K_PROMPT_TOKENS = 0.00014   # $0.14 / 1M input
    PRICE_PER_1K_COMPLETION_TOKENS = 0.00028 # $0.28 / 1M output

    def __init__(self):
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_embeddings_count: int = 0
        self.step_costs: Dict[str, float] = {}

    def add_tokens(self, prompt_tokens: int, completion_tokens: int, step_name: str = "llm_call"):
        """累加 LLM 产生的 Token 数量与步骤费用"""
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        prompt_cost = (prompt_tokens / 1000.0) * self.PRICE_PER_1K_PROMPT_TOKENS
        completion_cost = (completion_tokens / 1000.0) * self.PRICE_PER_1K_COMPLETION_TOKENS
        cost = prompt_cost + completion_cost

        self.step_costs[step_name] = self.step_costs.get(step_name, 0.0) + cost
        logger.info(f"[CostTracker] 记录步骤 [{step_name}] Token 消耗: 输入={prompt_tokens}, 输出={completion_tokens}, 耗费=${cost:.6f}")

    def add_embeddings(self, count: int):
        """记录向量嵌入条数"""
        self.total_embeddings_count += count

    def get_total_cost(self) -> float:
        """计算总费用 (美元)"""
        return sum(self.step_costs.values())

    def get_summary(self) -> Dict[str, Any]:
        """获取费用与 Token 消耗统计摘要"""
        total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        total_cost = round(self.get_total_cost(), 6)
        return {
            "total_tokens": total_tokens,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "embeddings_count": self.total_embeddings_count,
            "total_cost_usd": total_cost,
            "step_costs": self.step_costs
        }
