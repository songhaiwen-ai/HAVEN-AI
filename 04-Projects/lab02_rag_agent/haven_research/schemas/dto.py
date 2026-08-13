"""
haven_research/schemas/dto.py - 生产级 DTO 强类型契约数据规范模块

【1:1 对标 gpt-researcher】: gpt_researcher/utils/enum.py
定义检索输入/输出、抓取切片、报告类型枚举与报告交付的强类型 Pydantic 模型。
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """【1:1 对标 gpt-researcher】报告类型枚举"""
    ResearchReport = "research_report"     # 标准技术/行业研究报告
    DetailedReport = "detailed_report"     # 深度分章节大报告
    ResourceReport = "resource_report"     # 资源与工具清单型报告
    OutlineReport = "outline_report"       # 结构化大纲报告


class ReportSource(str, Enum):
    """【1:1 对标 gpt-researcher】数据源类型枚举"""
    Web = "web"                           # 全网实时检索抓取
    Local = "local"                       # 本地私有文档库
    Hybrid = "hybrid"                     # 本地私有库 + 全网实时检索双引擎


class SearchResultDTO(BaseModel):
    """单条搜索结果 DTO"""
    title: str = Field(..., description="网页或检索项标题")
    href: str = Field(..., description="原始网页 URL 链接")
    body: str = Field(..., description="搜索摘要或抓取文本片段")


class ScrapedDocumentDTO(BaseModel):
    """单页抓取干货正文 DTO"""
    url: str = Field(..., description="目标网页 URL")
    text: str = Field(..., description="清洗后的文本正文")
    error: Optional[str] = Field(default="", description="抓取异常信息")


class TextChunkDTO(BaseModel):
    """精选向量切片 DTO"""
    url: str = Field(..., description="数据来源 (URL 或 本地文档+页码)")
    content: str = Field(..., description="文本切片具体内容")
    score: float = Field(..., description="与意图的匹配得分 (余弦相似度)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据 (例如 file_name, page)")


class ResearchRequestDTO(BaseModel):
    """用户提交的研究任务 DTO"""
    query: str = Field(..., min_length=2, description="终极研究主题/目标")
    report_type: ReportType = Field(default=ReportType.ResearchReport, description="报告类型")
    report_source: ReportSource = Field(default=ReportSource.Web, description="数据源类型")
    max_subtopics: Optional[int] = Field(default=3, ge=1, le=10, description="最大衍生子搜索项数量")


class ResearchReportDTO(BaseModel):
    """最终交付的深度研究报告 DTO"""
    success: bool = Field(..., description="任务是否成功履约")
    query: str = Field(..., description="研究主题")
    agent_persona: Optional[str] = Field(default="通用研究专家", description="使用的 Agent Persona 动态角色")
    report_markdown: str = Field(..., description="带引用的完整 Markdown 报告")
    sources: List[TextChunkDTO] = Field(default_factory=list, description="所参考的精选切片清单")
    cost_summary: Dict[str, Any] = Field(default_factory=dict, description="Token 消耗与费用开销统计")
    verification_summary: Dict[str, Any] = Field(default_factory=dict, description="防幻觉引用校验结果")
