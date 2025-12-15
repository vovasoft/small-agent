# run_test.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP + LangChain 集成完整测试用例
"""
import asyncio
import sys
import os


def setup_encoding():
    """设置正确的编码环境"""
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # 设置标准流的编码
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')


async def main():
    setup_encoding()

    print("=" * 70)
    print("MCP 工具与 LangChain 智能体完整集成测试")
    print("=" * 70)

    try:
        # 直接运行智能体脚本
        print("\n运行 LangChain 智能体...")

        # 导入并运行智能体
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_module",
            "langchain_mcp_agent.py"
        )
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)

        await agent_module.create_and_run_agent()

    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("测试流程结束。")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
