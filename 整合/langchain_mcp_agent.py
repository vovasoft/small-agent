# langchain_mcp_agent.py
import os
import sys
import asyncio
import locale
from typing import List

# ========== 编码环境设置 ==========
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass

# ========== 导入其他模块 ==========
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool


async def create_and_run_agent():
    """
    演示如何集成 MCP 工具并创建 LangChain 智能体。
    """
    print("🤖 正在初始化 LangChain 智能体并连接 MCP 服务器...")

    try:
        # 1. 创建 MultiServerMCPClient 客户端
        client = MultiServerMCPClient(
            {
                "math": {
                    "command": "python3",
                    "args": ["mcp_math_server.py"],
                    "transport": "stdio",
                }
            }
        )

        print("✅ MCP 客户端创建成功")

        # 2. 获取所有原始工具
        raw_tools: List[BaseTool] = await client.get_tools()

        print(f"✅ 已从 MCP 服务器加载 {len(raw_tools)} 个原始工具: {[tool.name for tool in raw_tools]}")

        # 3. 创建工具包装器来修复格式问题
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
        all_tools = [add_tool, multiply_tool, calculate_expression_tool]
        print(f"✅ 创建了 {len(all_tools)} 个包装工具")

        # 4. 初始化大语言模型
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

        llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.1,
        )

        # 5. 使用工具创建 ReAct 智能体
        agent = create_react_agent(llm, all_tools)

        # 5. 定义测试用例
        test_queries = [
            "Calculate 15 plus 27",
            "What is 8 multiplied by 9?",
            "First calculate 3 plus 5, then multiply the result by 12",
            "What is the result of (20 - 5) * 3 / 2?",
        ]

        print("\n" + "=" * 60)
        print("Starting agent tests...")
        print("=" * 60)

        # 6. 运行智能体处理每个查询
        for i, query in enumerate(test_queries, 1):
            print(f"\n🧪 Test case {i}: 「{query}」")

            try:
                # 创建正确的消息格式
                messages = [HumanMessage(content=query)]

                # 调用智能体 - 传入消息列表
                response = await agent.ainvoke({"messages": messages})

                # 提取并打印智能体的最终回答
                if response and "messages" in response:
                    ai_response_found = False
                    for msg in reversed(response["messages"]):
                        if msg.type == "ai":
                            print(f"   🤖 Agent response: {msg.content}")
                            ai_response_found = True
                            break

                    if not ai_response_found:
                        print(f"   ⚠️  No AI response found in messages")
                        # 打印所有消息类型用于调试
                        msg_types = [msg.type for msg in response["messages"]]
                        print(f"   📋 Available message types: {msg_types}")
                else:
                    print(f"   📦 Unexpected response format: {type(response)}")

            except Exception as e:
                error_type = type(e).__name__
                print(f"   ❌ Error processing query ({error_type}): {e}")

                # 提供更具体的错误处理建议
                if "api" in str(e).lower():
                    print("   💡 This appears to be an API-related error. Check your API key and network connection.")
                elif "tool" in str(e).lower():
                    print("   💡 This appears to be a tool execution error. Check MCP server status.")
                elif "message" in str(e).lower():
                    print("   💡 This appears to be a message format error. Check agent configuration.")

                # 只在调试模式下打印完整堆栈跟踪
                if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
                    import traceback
                    traceback.print_exc()

        print("\n" + "=" * 60)
        print("Tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error initializing or running agent: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        print("\nCleaning up resources...")
        print("✅ Resource cleanup completed")


if __name__ == "__main__":
    asyncio.run(create_and_run_agent())
