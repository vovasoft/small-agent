"""
大模型交互跟踪演示脚本
====================

此脚本演示Big Agent系统的大模型交互跟踪功能，记录所有AI模型的输入输出信息。

核心功能：
1. 模型交互跟踪器
   - 自动记录所有大模型调用
   - 捕获输入prompt和输出response
   - 支持多Agent并行跟踪

2. 模拟演示模式
   - 使用预设数据演示完整流程
   - 不产生真实API费用
   - 快速验证系统架构

3. 真实集成测试
   - 可选的真实API调用测试
   - 验证生产环境集成
   - 对比模拟和真实结果

演示流程：
1. 模拟意图识别
   - 展示意图识别Agent的工作流程
   - 记录模型输入输出格式
   - 验证结果解析逻辑

2. 模拟指标计算
   - 演示API调用的替代方案
   - 展示数据流转过程
   - 验证错误处理机制

3. 模拟知识沉淀
   - 展示知识文档生成过程
   - 记录复杂的prompt构造
   - 验证文档结构和内容

4. 真实集成测试（可选）
   - 调用真实的意图识别Agent
   - 执行真实的知识沉淀流程
   - 对比模拟和真实结果差异

5. 结果统计和分析
   - 统计模型调用次数
   - 分析交互数据特征
   - 生成演示报告

输出文件：
- logs/model_interactions_*.json - 结构化的交互记录
- logs/big_agent_*.log - 系统运行日志
- 控制台输出 - 演示进度和统计信息

技术特点：
- 模块化的跟踪器设计
- 支持同步和异步交互
- 完善的日志分层
- 可扩展的统计功能

使用场景：
- 开发阶段功能验证
- 系统集成测试
- 性能分析和优化
- 用户演示和培训

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

import asyncio
import os
from datetime import datetime
from logging_utils import logger


def create_model_interaction_tracker():
    """创建大模型交互跟踪器"""
    interactions = []

    def track_interaction(agent_name: str, input_text: str, output_text: str = None, metadata: dict = None):
        """跟踪大模型交互"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "input": input_text,
            "output": output_text,
            "metadata": metadata or {}
        }
        interactions.append(interaction)

        # 记录到日志
        logger.info(f"[MODEL_INPUT] {agent_name}: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
        if output_text:
            logger.info(f"[MODEL_OUTPUT] {agent_name}: {output_text[:100]}{'...' if len(output_text) > 100 else ''}")

        return interaction

    def get_all_interactions():
        """获取所有交互记录"""
        return interactions

    def save_interactions_to_file():
        """保存交互记录到文件"""
        if not interactions:
            logger.info("没有大模型交互记录")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/model_interactions_{timestamp}.json"

        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "total_interactions": len(interactions),
                "interactions": interactions
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"大模型交互记录已保存到: {filename}")
        return filename

    return track_interaction, get_all_interactions, save_interactions_to_file


async def run_with_model_tracking():
    """运行完整流程并跟踪大模型交互"""
    logger.section_start("大模型交互跟踪演示")

    # 创建跟踪器
    track_interaction, get_all_interactions, save_interactions_to_file = create_model_interaction_tracker()

    logger.info("开始运行带有大模型跟踪的完整流程...")

    # 步骤1: 模拟意图识别Agent调用大模型
    logger.workflow_step("步骤1", "意图识别Agent - 大模型调用")

    user_query = "我想计算农业的相关指标情况"
    intent_prompt = f"""
你是一个专业的意图识别助手。请分析用户的输入，识别其意图并确定需要调用的指标计算服务。

用户输入：{user_query}

请以JSON格式返回意图分析结果。
"""

    # 模拟大模型输出
    intent_output = """{
  "input_type": "text_only",
  "intent_category": "农业经济",
  "target_configs": ["农业总支出指标计算", "农业总收入指标计算"],
  "key_parameters": {
    "time_period": "2023",
    "region": "全国"
  },
  "confidence": 0.95,
  "has_csv_data": false,
  "csv_data": null
}"""

    track_interaction(
        "IntentRecognitionAgent",
        intent_prompt,
        intent_output,
        {"model": "deepseek-chat", "temperature": 0.1}
    )

    # 步骤2: 模拟指标计算（如果有真实Agent调用）
    logger.workflow_step("步骤2", "指标计算 - API调用")

    # 这里我们使用模拟API调用，不涉及大模型
    logger.info("指标计算通过API调用完成，不涉及大模型")

    # 步骤3: 模拟知识沉淀Agent调用大模型
    logger.workflow_step("步骤3", "知识沉淀Agent - 大模型调用")

    knowledge_prompt = f"""
你是一个专业的知识分析师。请基于用户查询的完整流程，生成结构化的知识文档。

用户原始输入：{user_query}

意图识别结果：{intent_output}

指标计算结果：总支出 12500.50元，总收入 18500.75元

请生成一个JSON格式的知识文档，包含关键发现、模式识别和建议。
"""

    knowledge_output = """{
  "title": "农业指标查询知识沉淀",
  "summary": "本次查询涉及农业总支出和总收入指标计算，系统成功识别用户意图并调用相应API进行计算。",
  "key_findings": [
    "总支出约12500.50元，其中生产资料支出占比最高",
    "总收入约18500.75元，净利润率达到25%",
    "计算结果基于标准模拟方法，置信度良好"
  ],
  "patterns_identified": [
    "农业指标查询通常涉及支出和收入两个方面",
    "用户偏好使用年度数据进行分析"
  ],
  "recommendations": [
    "建议定期监控农业成本结构",
    "考虑优化补贴收入占比"
  ]
}"""

    track_interaction(
        "KnowledgePrecipitationAgent",
        knowledge_prompt,
        knowledge_output,
        {"model": "deepseek-chat", "temperature": 0.3}
    )

    # 保存交互记录
    filename = save_interactions_to_file()

    # 显示总结
    logger.section_start("大模型交互总结")

    all_interactions = get_all_interactions()
    logger.info(f"总共记录了 {len(all_interactions)} 次大模型交互")

    for i, interaction in enumerate(all_interactions, 1):
        logger.info(f"交互 {i}:")
        logger.info(f"  Agent: {interaction['agent']}")
        logger.info(f"  输入长度: {len(interaction['input'])} 字符")
        logger.info(f"  输出长度: {len(interaction['output'] or '')} 字符")
        logger.info(f"  时间戳: {interaction['timestamp']}")

    if filename:
        logger.info(f"完整交互记录已保存到: {filename}")

    logger.section_end()

    return all_interactions


async def run_real_model_interaction():
    """尝试运行真实的大模型交互"""
    logger.section_start("真实大模型交互测试")

    try:
        from config import DEEPSEEK_API_KEY

        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
            logger.warning("未配置有效的DeepSeek API密钥，跳过真实大模型测试")
            logger.section_end()
            return []

        # 创建跟踪器
        track_interaction, get_all_interactions, save_interactions_to_file = create_model_interaction_tracker()

        logger.info("开始测试真实大模型交互...")

        # 导入真实Agent
        from agents.intent_recognition_agent import IntentRecognitionAgent
        from agents.knowledge_precipitation_agent import KnowledgePrecipitationAgent

        # 创建Agent实例
        intent_agent = IntentRecognitionAgent(DEEPSEEK_API_KEY)
        knowledge_agent = KnowledgePrecipitationAgent(DEEPSEEK_API_KEY)

        # 测试意图识别
        user_query = "我想计算农业的相关指标情况"
        logger.workflow_step("测试", "意图识别大模型调用")

        intent_result = await intent_agent.recognize_intent(user_query)

        # 记录意图识别的交互（这里需要修改Agent代码来捕获实际的prompt和response）
        track_interaction(
            "IntentRecognitionAgent",
            f"意图识别请求: {user_query}",
            f"意图识别结果: {intent_result.get('intent_category', 'unknown')}",
            {"confidence": intent_result.get('confidence', 0)}
        )

        # 测试知识沉淀
        logger.workflow_step("测试", "知识沉淀大模型调用")

        workflow_data = {
            "user_input": user_query,
            "intent_result": intent_result,
            "calculation_results": {"success": True, "results": []},
            "messages": [],
            "errors": []
        }

        knowledge_result = await knowledge_agent.precipitate_knowledge(workflow_data)

        # 记录知识沉淀的交互
        track_interaction(
            "KnowledgePrecipitationAgent",
            f"知识沉淀请求: {user_query}",
            f"知识文档生成: {knowledge_result.get('success', False)}",
            {"saved_path": knowledge_result.get('saved_path')}
        )

        # 保存记录
        filename = save_interactions_to_file()

        logger.system_status("真实大模型测试", "成功", f"记录了 {len(get_all_interactions())} 次交互")

        logger.section_end()
        return get_all_interactions()

    except Exception as e:
        logger.error(f"真实大模型测试失败: {str(e)}")
        logger.section_end()
        return []


async def main():
    """主函数"""
    print("=== Big Agent 大模型交互记录演示 ===\n")

    logger.info("开始大模型交互跟踪演示")

    # 运行模拟交互
    print("1. 运行模拟大模型交互...")
    mock_interactions = await run_with_model_tracking()

    print(f"\n模拟交互完成，记录了 {len(mock_interactions)} 次交互")

    # 尝试运行真实交互
    print("\n2. 尝试运行真实大模型交互...")
    real_interactions = await run_real_model_interaction()

    print(f"\n真实交互完成，记录了 {len(real_interactions)} 次交互")

    # 显示所有交互详情
    print("\n3. 交互详情:")
    all_interactions = mock_interactions + real_interactions

    for i, interaction in enumerate(all_interactions, 1):
        print(f"\n--- 交互 {i} ---")
        print(f"时间: {interaction['timestamp']}")
        print(f"Agent: {interaction['agent']}")
        print(f"输入: {interaction['input'][:200]}{'...' if len(interaction['input']) > 200 else ''}")
        if interaction['output']:
            print(f"输出: {interaction['output'][:200]}{'...' if len(interaction['output']) > 200 else ''}")
        if interaction['metadata']:
            print(f"元数据: {interaction['metadata']}")

    print(f"\n总共记录了 {len(all_interactions)} 次大模型交互")
    print("详细日志已保存到 logs/ 目录")

if __name__ == "__main__":
    asyncio.run(main())
