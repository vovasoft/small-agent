# debug_test.py - 逐步调试MCP和LangChain集成
import asyncio
import os
import sys

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def test_mcp_tools():
    """测试MCP工具是否正常工作"""
    print("=== 测试MCP工具功能 ===")

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

        print("✅ MCP客户端创建成功")

        # 获取工具
        tools = await client.get_tools()
        print(f"✅ 获取到 {len(tools)} 个工具: {[t.name for t in tools]}")

        # 测试直接调用工具
        print("\n--- 测试工具直接调用 ---")
        for tool in tools:
            print(f"工具: {tool.name}")
            print(f"描述: {tool.description}")

            # 测试add工具
            if tool.name == "add":
                print("测试 add(15, 27)...")
                result = await tool.ainvoke({"a": 15, "b": 27})
                print(f"结果类型: {type(result)}")
                print(f"结果内容: {result}")
                if isinstance(result, list) and result:
                    print(f"第一个元素类型: {type(result[0])}")
                    if isinstance(result[0], dict) and 'text' in result[0]:
                        print(f"提取的文本: {result[0]['text']}")

            # 测试multiply工具
            elif tool.name == "multiply":
                print("测试 multiply(8, 9)...")
                result = await tool.ainvoke({"a": 8, "b": 9})
                print(f"结果类型: {type(result)}")
                print(f"结果内容: {result}")
                if isinstance(result, list) and result:
                    print(f"第一个元素类型: {type(result[0])}")
                    if isinstance(result[0], dict) and 'text' in result[0]:
                        print(f"提取的文本: {result[0]['text']}")

            # 测试calculate_expression工具
            elif tool.name == "calculate_expression":
                print("测试 calculate_expression('(20 - 5) * 3 / 2')...")
                result = await tool.ainvoke({"expression": "(20 - 5) * 3 / 2"})
                print(f"结果类型: {type(result)}")
                print(f"结果内容: {result}")
                if isinstance(result, list) and result:
                    print(f"第一个元素类型: {type(result[0])}")
                    if isinstance(result[0], dict) and 'text' in result[0]:
                        print(f"提取的文本: {result[0]['text']}")

        # 注意：MultiServerMCPClient没有close方法，使用上下文管理器或手动清理
        print("✅ MCP工具测试完成")

    except Exception as e:
        print(f"❌ MCP工具测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_langchain_agent():
    """测试LangChain智能体"""
    print("\n=== 测试LangChain智能体 ===")

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_openai import ChatOpenAI
        from langchain_core.tools import tool

        # 创建MCP客户端
        client = MultiServerMCPClient({
            "math": {
                "command": "python3",
                "args": ["mcp_math_server.py"],
                "transport": "stdio",
            }
        })

        raw_tools = await client.get_tools()
        print(f"✅ 获取到 {len(raw_tools)} 个原始工具")

        # 创建工具包装器来修复格式问题
        @tool
        async def add_tool(a: float, b: float) -> str:
            """将两个数字相加。"""
            for t in raw_tools:
                if t.name == "add":
                    result = await t.ainvoke({"a": a, "b": b})
                    # 提取文本内容
                    if isinstance(result, list) and result and isinstance(result[0], dict) and 'text' in result[0]:
                        return result[0]['text']
                    return str(result)
            return "Error: add tool not found"

        @tool
        async def multiply_tool(a: float, b: float) -> str:
            """将两个数字相乘。"""
            for t in raw_tools:
                if t.name == "multiply":
                    result = await t.ainvoke({"a": a, "b": b})
                    # 提取文本内容
                    if isinstance(result, list) and result and isinstance(result[0], dict) and 'text' in result[0]:
                        return result[0]['text']
                    return str(result)
            return "Error: multiply tool not found"

        @tool
        async def calculate_expression_tool(expression: str) -> str:
            """计算一个简单的数学表达式。"""
            for t in raw_tools:
                if t.name == "calculate_expression":
                    result = await t.ainvoke({"expression": expression})
                    # 提取文本内容
                    if isinstance(result, list) and result and isinstance(result[0], dict) and 'text' in result[0]:
                        return result[0]['text']
                    return str(result)
            return "Error: calculate_expression tool not found"

        # 使用包装后的工具
        tools = [add_tool, multiply_tool, calculate_expression_tool]
        print(f"✅ 创建了 {len(tools)} 个包装工具")

        # 创建LLM
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

        llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.1,
        )

        print("✅ LLM创建成功")

        # 使用简单的工具调用而不是智能体
        print("\n--- 测试直接工具调用 ---")
        test_cases = [
            ("add", {"a": 15, "b": 27}),
            ("multiply", {"a": 8, "b": 9}),
            ("calculate_expression", {"expression": "(20 - 5) * 3 / 2"})
        ]

        for tool_name, params in test_cases:
            if tool_name == "add":
                result = await add_tool.ainvoke(params)
                print(f"✅ add(15, 27) = {result}")
            elif tool_name == "multiply":
                result = await multiply_tool.ainvoke(params)
                print(f"✅ multiply(8, 9) = {result}")
            elif tool_name == "calculate_expression":
                result = await calculate_expression_tool.ainvoke(params)
                print(f"✅ calculate_expression('(20 - 5) * 3 / 2') = {result}")

        # 注意：MultiServerMCPClient没有close方法

    except Exception as e:
        print(f"❌ LangChain智能体测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("开始逐步调试MCP + LangChain集成")
    print("=" * 50)

    await test_mcp_tools()
    await test_langchain_agent()

    print("\n" + "=" * 50)
    print("调试完成")


if __name__ == "__main__":
    asyncio.run(main())
