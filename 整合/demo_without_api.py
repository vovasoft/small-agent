#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP + LangChain 集成演示（无需API密钥）
"""
import asyncio
import sys
import os

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def demo_mcp_tools():
    """演示MCP工具功能（无需API密钥）"""
    print("🚀 MCP + LangChain 集成演示")
    print("=" * 50)

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        # 创建MCP客户端
        client = MultiServerMCPClient({
            "math": {
                "command": "python3",
                "args": ["mcp_math_server.py"],
                "transport": "stdio",
            }
        })

        print("✅ MCP 客户端创建成功")

        # 获取并测试工具
        raw_tools = await client.get_tools()
        print(f"✅ 已连接到 {len(raw_tools)} 个 MCP 工具: {[t.name for t in raw_tools]}")

        # 创建工具包装器
        from langchain_core.tools import tool

        @tool
        async def add_tool(a: float, b: float) -> str:
            """将两个数字相加"""
            for t in raw_tools:
                if t.name == "add":
                    result = await t.ainvoke({"a": a, "b": b})
                    if isinstance(result, list) and result and isinstance(result[0], dict) and 'text' in result[0]:
                        return result[0]['text']
                    return str(result)
            return "Error: add tool not found"

        @tool
        async def multiply_tool(a: float, b: float) -> str:
            """将两个数字相乘"""
            for t in raw_tools:
                if t.name == "multiply":
                    result = await t.ainvoke({"a": a, "b": b})
                    if isinstance(result, list) and result and isinstance(result[0], dict) and 'text' in result[0]:
                        return result[0]['text']
                    return str(result)
            return "Error: multiply tool not found"

        @tool
        async def calculate_expression_tool(expression: str) -> str:
            """计算数学表达式"""
            for t in raw_tools:
                if t.name == "calculate_expression":
                    result = await t.ainvoke({"expression": expression})
                    if isinstance(result, list) and result and isinstance(result[0], dict) and 'text' in result[0]:
                        return result[0]['text']
                    return str(result)
            return "Error: calculate_expression tool not found"

        print("\n🧮 演示数学工具功能:")

        # 测试各种计算
        test_cases = [
            ("add", {"a": 15, "b": 27}, "15 + 27"),
            ("multiply", {"a": 8, "b": 9}, "8 × 9"),
            ("calculate_expression", {"expression": "(20 - 5) * 3 / 2"}, "(20 - 5) × 3 ÷ 2"),
        ]

        for tool_name, params, description in test_cases:
            print(f"\n  计算: {description}")
            try:
                if tool_name == "add":
                    result = await add_tool.ainvoke(params)
                elif tool_name == "multiply":
                    result = await multiply_tool.ainvoke(params)
                elif tool_name == "calculate_expression":
                    result = await calculate_expression_tool.ainvoke(params)

                print(f"  结果: {result}")
            except Exception as e:
                print(f"  ❌ 错误: {e}")

        print("\n🎯 MCP 工具演示完成！")
        print("\n💡 要体验完整的 LangChain 智能体功能，请设置 DeepSeek API 密钥：")
        print("   export DEEPSEEK_API_KEY='your_api_key'")
        print("   python3 run_test.py")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    await demo_mcp_tools()


if __name__ == "__main__":
    asyncio.run(main())
