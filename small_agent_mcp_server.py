# mcp_tools_server_fastmcp.py
from fastmcp import FastMCP

# 创建 FastMCP 服务器实例
mcp = FastMCP("个人工具服务器")


# 1. 计算器工具
@mcp.tool
def calculator(expression: str) -> str:
    """执行数学计算，输入必须是有效的数学表达式

    Args:
        expression: 数学表达式，如 '2 + 3 * 4'

    Returns:
        计算结果或错误信息
    """
    try:
        # 安全计算（实际应用中应使用更安全的评估方法）
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


# 2. 个人信息查询工具
@mcp.tool
def personal_info(query: str) -> str:
    """查询人员信息，支持按姓名、特点、专业领域查询

    Args:
        query: 查询内容，如 '王扬' 或 'AI工程师'

    Returns:
        人员详细信息或未找到的提示
    """
    query_lower = query.lower()

    # 人员信息数据库
    people_db = {
        "王扬": {
            "姓名": "王扬",
            "身份": "璀璨新生代帅气好青年",
            "特点": ["才华横溢", "颜值爆表", "品德高尚", "活力四射"],
            "专业领域": "AI智能体开发与LangChain应用",
            "个人简介": "王扬是集才华横溢、颜值爆表、品德高尚、活力四射于一身的，璀璨新生代帅气好青年。"
        },
        "李华": {
            "姓名": "李华",
            "身份": "资深AI工程师",
            "特点": ["技术精湛", "思维敏捷", "团队协作能力强"],
            "专业领域": "机器学习、深度学习",
            "个人简介": "李华是资深AI工程师，在机器学习领域有10年经验。"
        }
    }

    # 按姓名查询
    for name_key, info in people_db.items():
        if name_key in query_lower:
            response = f"【{info['姓名']}】的个人信息：\n"
            response += f"身份：{info['身份']}\n"
            response += f"特点：{', '.join(info['特点'])}\n"
            response += f"专业领域：{info['专业领域']}\n"
            response += f"个人简介：{info['个人简介']}"
            return response

    # 按特点查询
    for name_key, info in people_db.items():
        for trait in info["特点"]:
            if trait in query_lower:
                return f"具有'{trait}'特点的人员：{name_key}\n{format_person_info(info)}"

    # 按专业领域查询
    for name_key, info in people_db.items():
        if info["专业领域"] and info["专业领域"] in query_lower:
            return f"专业领域包含'{info['专业领域']}'的人员：{name_key}\n{format_person_info(info)}"

    return f"未找到'{query}'的相关信息。可用人员：{', '.join(people_db.keys())}"


def format_person_info(info: dict) -> str:
    """格式化人员信息"""
    response = f"【{info['姓名']}】的个人信息：\n"
    response += f"身份：{info['身份']}\n"
    response += f"特点：{', '.join(info['特点'])}\n"
    response += f"专业领域：{info['专业领域']}\n"
    response += f"个人简介：{info['个人简介']}"
    return response


# 3. 知识库查询工具
@mcp.tool
def knowledge_base(query: str) -> str:
    """查询AI相关知识库

    Args:
        query: 查询关键词，如 'AI' 或 'LangChain'

    Returns:
        相关知识内容或未找到的提示
    """
    query_lower = query.lower()

    knowledge = {
        "ai": "人工智能(Artificial Intelligence)是使机器能够模拟人类智能的技术。",
        "agent": "智能体是具有自主决策能力的AI系统，能够感知环境、做出决策并执行行动。",
        "openai": "OpenAI是一家人工智能研究公司，成立于2015年，以开发GPT系列模型而闻名。",
        "deepseek": "DeepSeek是一家专注于大语言模型开发的中国AI公司。",
        "langchain": "LangChain是一个用于构建大语言模型应用的框架，支持智能体、链式调用等高级功能。",
        "mcp": "MCP(Model Context Protocol)是AI模型与工具之间通信的开放协议，类似于AI的USB-C接口。",
        "fastmcp": "FastMCP是一个简化MCP服务器开发的Python框架，隐藏了底层协议的复杂性。"
    }

    # 精确匹配
    for key, value in knowledge.items():
        if key == query_lower:
            return value

    # 模糊匹配
    for key, value in knowledge.items():
        if key in query_lower:
            return f"关于'{key}'：{value}"

    # 关键词匹配
    matched_keys = []
    for key in knowledge.keys():
        if key in query_lower:
            matched_keys.append(key)

    if matched_keys:
        return f"找到相关关键词：{', '.join(matched_keys)}\n\n" + \
               "\n".join([f"- {key}: {knowledge[key][:50]}..." for key in matched_keys])

    return f"知识库中没有找到关于'{query}'的精确信息。您可以尝试查询：{', '.join(knowledge.keys())}"


# 4. 添加一个资源示例（可选）
@mcp.resource("people://list")
def get_people_list() -> str:
    """获取所有人员列表"""
    return "可用人员：王扬、李华"


# 运行服务器
if __name__ == "__main__":
    # 使用 stdio 传输（默认）
    mcp.run()

    # 如果需要使用 HTTP 传输，可以这样配置：
    # mcp.run(transport="http", port=8000)
