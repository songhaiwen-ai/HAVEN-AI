import sys
import os

# 兼容 Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 确保导入路径正确
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import run_agent_loop


def main():
    print("=" * 60)
    print("  [Lab 01] Haven-AI: 手写 Minimal ReAct Agent Loop 测试")
    print("=" * 60)

    # 测试任务 1: 包含连续工具调用的复合任务
    task1 = "请帮我查一下当前系统时间，然后计算 25 * 4 的值，最后运行 Python 校验输出结果。"
    
    result = run_agent_loop(user_goal=task1, max_iterations=5)

    print("=" * 60)
    print("  📊 任务统计报告 (Task Execution Summary)")
    print("=" * 60)
    print(f"✔️ 状态: {'成功' if result['success'] else '失败'}")
    print(f"🔢 耗费循环轮次: {result['loops_used']} 轮")
    print(f"📝 最终交付成果: {result['final_answer']}")
    print("-" * 60)
    print("🔍 完整履约轨迹 (Execution Trace):")
    for step in result['trace']:
        print(f"  [Loop 0{step['loop']}] Action: {step['action']} -> Obs: {step['observation'][:60]}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
