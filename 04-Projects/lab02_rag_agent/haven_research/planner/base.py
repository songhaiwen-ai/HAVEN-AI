"""
haven_research/planner/base.py - Agent 子主题拆解与规划器抽象基类

【对标 gpt-researcher】: gpt_researcher/actions/
定义基于 LLM 的子问题拆解与 Search Query 扩展接口。
"""

from abc import ABC, abstractmethod
from typing import List


class BasePlanner(ABC):
    """子主题拆解与规划器基类"""

    @abstractmethod
    async def plan_subtopics(self, query: str, max_subtopics: int = 3) -> List[str]:
        """
        根据用户的主课题，拆解出多维度关联子主题
        :param query: 主课题描述
        :param max_subtopics: 最多拆解的子主题数量
        :return: 子主题 Query 列表
        """
        pass
