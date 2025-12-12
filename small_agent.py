"""
LangChain 1.0 极简智能体 - 使用create_agent API
基于LangChain官方1.0文档更新
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Dict, Any
import os

# 安全提示：不要在代码中硬编码API密钥
# 建议使用环境变量：os.getenv("DEEPSEEK_API_KEY")

# 1. 定义工具 - 使用新的@tool装饰器
@tool
def calculator(expression: str) -> str:
    """执行数学计算，输入必须是有效的数学表达式。"""
    try:
        # 安全计算（实际应用中应使用更安全的评估方法）
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def knowledge_base(query: str) -> str:
    """查询AI相关知识，输入是关键词或问题。"""
    knowledge = {
        "ai": "人工智能(Artificial Intelligence)是使机器能够模拟人类智能的技术。",
        "agent": "智能体是具有自主决策能力的AI系统，能够感知环境、做出决策并执行行动[2]。",
        "openai": "OpenAI是一家人工智能研究公司，成立于2015年，以开发GPT系列模型而闻名。",
        "deepseek": "DeepSeek是一家专注于大语言模型开发的中国AI公司。",
        "langchain": "LangChain是一个用于构建大语言模型应用的框架，支持智能体、链式调用等高级功能[2]。"
    }

    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower:
            return value

    return f"知识库中没有找到关于'{query}'的精确信息。您可以尝试查询：ai, agent, openai等关键词。"


# 在现有的工具定义部分添加以下代码
@tool
def personal_info(query: str) -> str:
    """查询人员信息。输入可以是姓名或'介绍'、'个人信息'等关键词。"""

    # 人员信息数据库
    people_database = {
        "王扬": {
            "姓名": "王扬",
            "身份": "璀璨新生代帅气好青年",
            "特点": ["才华横溢", "颜值爆表", "品德高尚", "活力四射"],
            "专业领域": "AI智能体开发与LangChain应用",
            "个人简介": "王扬是集才华横溢、颜值爆表、品德高尚、活力四射于一身的，璀璨新生代帅气好青年。他在AI智能体开发领域有着深入的研究和实践经验。",
            "联系方式": "wangyang@example.com"
        },
        "王璐": {
            "姓名": "王璐",
            "身份": "资产项目总监",
            "特点": ["个字高高像电线杆", "思维敏捷", "爱吃"],
            "专业领域": "PPT，Excel",
            "个人简介": "王璐是资深项目总监，除了写代码，啥都会",
            "联系方式": "wanglu@example.com"
        },
        "张伟": {
            "姓名": "张伟",
            "身份": "产品经理",
            "特点": ["用户导向", "沟通能力强", "创新思维"],
            "专业领域": "产品设计、用户体验",
            "个人简介": "张伟是资深产品经理，专注于AI产品设计，善于将技术转化为用户价值。",
            "联系方式": "zhangwei@example.com"
        }
    }

    query_lower = query.lower().strip()

    # 1. 直接按姓名查询
    for name in people_database.keys():
        if name in query_lower:
            person = people_database[name]
            return format_person_info(person)

    # 2. 关键词查询（如"介绍"、"个人信息"）
    general_keywords = ["介绍", "个人信息", "关于", "是谁", "people"]
    for keyword in general_keywords:
        if keyword in query_lower:
            # 返回所有人列表或让用户指定
            return "请指定要查询的人员姓名。可用人员：王扬、王璐、张伟"

    # 3. 按特点或领域模糊查询
    for name, person in people_database.items():
        # 检查特点
        for trait in person["特点"]:
            if trait in query_lower:
                return f"具有'{trait}'特点的人员：{name}\n{format_person_info(person)}"

        # 检查专业领域
        if person["专业领域"] and person["专业领域"] in query_lower:
            return f"专业领域包含'{person['专业领域']}'的人员：{name}\n{format_person_info(person)}"

    return f"未找到相关信息。可用人员：{', '.join(people_database.keys())}"


def format_person_info(person: dict) -> str:
    """格式化人员信息输出"""
    response = f"【{person['姓名']}】的个人信息：\n"
    response += f"身份：{person['身份']}\n"
    response += f"特点：{', '.join(person['特点'])}\n"
    response += f"专业领域：{person['专业领域']}\n"
    response += f"个人简介：{person['个人简介']}\n"
    if "联系方式" in person:
        response += f"联系方式：{person['联系方式']}"
    return response



# 2. 初始化模型 - DeepSeek
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-ba07b95e9c004f00b957b01c2297fba6",  # 建议使用环境变量
    base_url="https://api.deepseek.com",
    temperature=0.3,
    max_tokens=1000
)

# 3. 创建智能体 - 使用LangChain 1.0的create_agent API
agent = create_agent(
    model=llm,
    tools=[calculator, knowledge_base,personal_info],
    system_prompt="你是一个具有自主决策能力的AI智能体。能够分析用户意图，自主决定何时使用工具，何时直接回答。"  # 注意：1.0中改为system_prompt[1]

)

# 4. 使用智能体 - 新的调用方式
print("=" * 60)
print("LangChain 1.0 智能体演示")
print("=" * 60)

# 测试用例
test_cases = [
    "计算一下 25 * 4 等于多少？",
    "王扬这个人如何？",
    "王璐是谁",
    "你好，今天天气怎么样？",
]

for i, query in enumerate(test_cases, 1):
    print(f"\n[{i}] 用户: {query}")

    # 调用智能体 - 新的消息格式
    response = agent.invoke({
        "messages": [{
            "role": "user",
            "content": query
        }]
    })

    # 提取响应内容
    if "messages" in response:
        last_message = response["messages"][-1]
        if hasattr(last_message, 'content'):
            print(f"智能体: {last_message.content}")
        else:
            print(f"智能体: {last_message}")
    else:
        print(f"智能体: {response}")

    print("-" * 50)

print("\n" + "=" * 60)
print("智能体架构说明")
print("=" * 60)
print("""
LangChain 1.0 核心变化[1][2]：

1. 统一入口: 所有智能体创建统一为 create_agent() API
2. 中间件机制: 支持横切能力（日志、HITL、摘要、安全等）
3. 结构化输出: 内联到主循环，新增 toolStrategy / providerStrategy
4. 精简包结构: langchain 专注 agent 核心能力

本实现特点：
- 使用 @tool 装饰器定义工具
- 系统提示改为 system_prompt 参数
- 调用时使用标准消息格式: {"messages": [{"role": "user", "content": query}]}
- 智能体自主决策何时使用工具
""")
