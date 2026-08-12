"""
main.py - HavenResearch Engine 深度研究 Agent 主运行入口

命令行执行示例:
    python main.py --query "2026 年企业级 AI Agent 架构设计与技术选型"
"""

import sys
import asyncio
import argparse
from haven_research import HavenResearcher
from haven_research.schemas.dto import ResearchRequestDTO
from haven_research.core import logger

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


async def run_agent(query: str):
    print("\n" + "=" * 80)
    print(" 🚀 HavenResearch Deep Research Agent (1:1 对标 gpt-researcher)")
    print(" 大脑 LLM: DeepSeek API (deepseek-chat)")
    print(" 向量数据库: Qdrant Cloud 云端 Serverless 集群")
    print("=" * 80 + "\n")

    request = ResearchRequestDTO(query=query, max_subtopics=3)
    researcher = HavenResearcher(request)
    
    report_dto = await researcher.conduct_research()

    print("\n" + "=" * 80)
    print(" 📄 生成的 Markdown 深度研究报告正文如下:")
    print("=" * 80 + "\n")
    print(report_dto.report_markdown)

    print("\n" + "=" * 80)
    print(f" 🌐 参考数据源与精选上下文列表 ({len(report_dto.sources)} 个):")
    for s in report_dto.sources:
        print(f"  - [{s.url}] 得分: {s.score}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="HavenResearch Deep Research Agent CLI")
    parser.add_argument(
        "--query",
        type=str,
        default="2026 年企业级 AI Agent 架构设计与技术选型",
        help="研究课题描述"
    )
    args = parser.parse_args()

    asyncio.run(run_agent(args.query))


if __name__ == "__main__":
    main()
