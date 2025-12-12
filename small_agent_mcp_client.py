# mcp_client_fastmcp.py
import asyncio
from fastmcp import Client


async def test_mcp_server():
    """测试 FastMCP 服务器"""

    # 连接到本地服务器（使用 stdio 传输）
    # 注意：如果服务器使用 HTTP 传输，URL 应为 "http://localhost:8000/mcp"
    client = Client("small_agent_mcp_server.py")  # 直接指向服务器脚本文件

    async with client:
        print("✅ 已连接到 MCP 服务器")

        # 测试用例
        test_cases = [
            ("calculator", {"expression": "25 * 4"}),
            ("personal_info", {"query": "王扬"}),
            ("personal_info", {"query": "技术精湛"}),
            ("knowledge_base", {"query": "AI"}),
            ("knowledge_base", {"query": "什么是LangChain？"}),
        ]

        for tool_name, arguments in test_cases:
            print(f"\n🔧 测试工具: {tool_name}")
            print(f"   参数: {arguments}")

            try:
                result = await client.call_tool(tool_name, arguments)
                print(f"   结果: {result}")
            except Exception as e:
                print(f"   ❌ 错误: {e}")

        print("\n📋 获取可用工具列表:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
