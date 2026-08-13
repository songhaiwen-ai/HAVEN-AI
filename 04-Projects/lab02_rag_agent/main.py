"""
main.py - HavenResearch Engine 深度研究 Agent 主运行入口

命令行执行示例:
    python main.py --query "2026 年企业级 AI Agent 架构设计与技术选型"
"""

import os
import sys
import asyncio
import argparse

# 自动将当前项目根目录加入 sys.path，防止 PyCharm 导包标红或找不到模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    print(f" 🎭 调用的 Agent 动态专家 Persona: 【{report_dto.agent_persona}】")
    print(" 📄 生成的 Markdown 深度研究报告正文如下:")
    print("=" * 80 + "\n")
    print(report_dto.report_markdown)

    # 自动保存为本地 .md 格式文件落盘供在 Typora 或 PyCharm 中随时阅读查看
    outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    # 清理文件名中的非法字符
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)[:50].strip("_")
    report_file_path = os.path.join(outputs_dir, f"{safe_title}_research_report.md")
    
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write(report_dto.report_markdown)

    print("\n" + "=" * 80)
    print(f" 💾 【报告已自动落盘保存】: {report_file_path}")
    print(f" 🌐 参考数据源与精选上下文列表 ({len(report_dto.sources)} 个):")
    for s in report_dto.sources:
        print(f"  - [{s.url}] 得分: {s.score}")
        
    print("-" * 80)
    costs = report_dto.cost_summary
    print(f" 💰 Token 消耗与费用结算: 总 Token={costs.get('total_tokens', 0)} (输入={costs.get('prompt_tokens', 0)}, 输出={costs.get('completion_tokens', 0)}), 预估费用=${costs.get('total_cost_usd', 0)}")
    
    verifier = report_dto.verification_summary
    print(f" 🛡️ 防幻觉引用校验门禁: 通状态={verifier.get('verified', True)}, 校验引用数={verifier.get('total_citations', 0)}, 合规极性={verifier.get('pass_rate', 1.0)*100}%")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="HavenResearch Deep Research Agent CLI")
    parser.add_argument(
        "--query",
        type=str,
        default="2026年，AI大模型对程序员的工作形式产生了很大改变，你认为目前来看，那个方向更适合程序员的未来发展呢 ",
        help="研究课题描述"
    )
    args = parser.parse_args()

    asyncio.run(run_agent(args.query))


if __name__ == "__main__":
    main()
