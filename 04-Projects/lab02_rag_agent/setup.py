from setuptools import setup, find_packages

setup(
    name="haven_research",
    version="0.1.0",
    description="HavenResearch Engine - 企业级深度研究 Agent 软件框架",
    author="Haven-AI Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "openai>=1.0.0",
        "chromadb>=0.4.0",
        "pypdf>=3.0.0",
        "duckduckgo_search>=4.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "pytest>=7.4.0"
    ],
)
