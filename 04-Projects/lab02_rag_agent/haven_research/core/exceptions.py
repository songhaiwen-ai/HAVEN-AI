"""
haven_research/core/exceptions.py - 企业级统一异常定义模块

构建层次分明的项目异常基类与衍生子类体系，方便全局捕获、状态码映射与错误追踪。
"""


class HavenAgentException(Exception):
    """HavenResearch Engine 项目根异常类"""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


class ConfigurationException(HavenAgentException):
    """项目配置错误异常"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="CONFIG_ERROR", details=details)


class RetrieverException(HavenAgentException):
    """网络检索器执行异常"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="RETRIEVER_ERROR", details=details)


class ScraperException(HavenAgentException):
    """网页抓取与清洗异常"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="SCRAPER_ERROR", details=details)


class VectorStoreException(HavenAgentException):
    """向量数据库存取异常"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="VECTOR_STORE_ERROR", details=details)


class DocumentParsingException(HavenAgentException):
    """文档解析与切片异常"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="DOC_PARSING_ERROR", details=details)


class AgentExecutionException(HavenAgentException):
    """Agent 核心循环与调度异常"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="AGENT_EXECUTION_ERROR", details=details)
