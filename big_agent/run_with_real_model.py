"""
真实大模型调用测试脚本
=====================

此脚本用于测试和验证Big Agent系统与真实DeepSeek API的集成。

核心功能：
1. 意图识别Agent真实调用测试
   - 使用真实DeepSeek API进行意图分析
   - 记录完整的模型输入输出
   - 验证意图识别准确性

2. 知识沉淀Agent真实调用测试
   - 基于意图识别结果生成知识文档
   - 测试完整的知识沉淀流程
   - 验证文档生成质量

3. API调用监控和记录
   - 记录所有HTTP请求和响应
   - 捕获和分析API调用错误
   - 生成详细的调用日志

测试流程：
1. 环境检查
   - 验证API密钥配置
   - 检查网络连接性
   - 初始化日志系统

2. 意图识别测试
   - 发送测试查询到意图识别Agent
   - 记录模型输入和输出
   - 验证结果格式和内容

3. 知识沉淀测试
   - 构造完整的工作流数据
   - 调用知识沉淀Agent
   - 保存生成的知识文档

4. 结果分析和报告
   - 统计API调用次数
   - 分析响应时间和成功率
   - 生成测试报告

输出文件：
- logs/real_model_calls_*.log - API调用详细日志
- knowledge_base/knowledge_*.json - 生成的知识文档
- 控制台输出 - 测试进度和结果

配置要求：
- 需要有效的DEEPSEEK_API_KEY环境变量
- 网络连接正常
- jsonFiles目录存在有效的配置文件

注意事项：
- 会产生真实的API调用费用
- 网络不稳定可能导致测试失败
- 用于验证生产环境集成

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

import asyncio
import logging
import logging.handlers
from datetime import datetime
from config import DEEPSEEK_API_KEY
from agents.intent_recognition_agent import IntentRecognitionAgent
from agents.knowledge_precipitation_agent import KnowledgePrecipitationAgent

# 配置日志
LOGS_DIR = "logs"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            f"{LOGS_DIR}/real_model_calls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger("real_model_calls")


async def test_intent_recognition():
    """测试意图识别Agent的大模型调用"""
    logger.info("=== 测试意图识别Agent大模型调用 ===")

    try:
        agent = IntentRecognitionAgent(DEEPSEEK_API_KEY)
        user_input = "我想计算农业的相关指标情况"

        logger.info(f"用户输入: {user_input}")

        # 调用意图识别 - 这会记录大模型的输入输出
        result = await agent.recognize_intent(user_input)

        logger.info(f"意图识别结果: {result}")

    except Exception as e:
        logger.error(f"意图识别测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


async def test_knowledge_precipitation():
    """测试知识沉淀Agent的大模型调用"""
    logger.info("=== 测试知识沉淀Agent大模型调用 ===")

    try:
        agent = KnowledgePrecipitationAgent(DEEPSEEK_API_KEY)

        # 模拟工作流数据
        workflow_data = {
            "user_input": "我想计算农业的相关指标情况",
            "intent_result": {
                "intent_category": "农业经济",
                "target_configs": ["农业总支出指标计算", "农业总收入指标计算"],
                "confidence": 0.95
            },
            "calculation_results": {
                "success": True,
                "results": [
                    {"config_name": "农业总支出指标计算", "result": {"success": True, "data": {"total_expense": 12500.50}}},
                    {"config_name": "农业总收入指标计算", "result": {"success": True, "data": {"total_income": 18500.75}}}
                ]
            },
            "messages": [],
            "errors": []
        }

        logger.info("准备生成知识文档...")

        # 调用知识沉淀 - 这会记录大模型的输入输出
        result = await agent.precipitate_knowledge(workflow_data)

        logger.info(f"知识沉淀结果: {result.get('success', False)}")
        if result.get('saved_path'):
            logger.info(f"文档保存路径: {result['saved_path']}")

    except Exception as e:
        logger.error(f"知识沉淀测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


async def main():
    """主函数"""
    logger.info("开始真实大模型调用测试")
    logger.info(f"API Key: {'已配置' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != 'your_deepseek_api_key_here' else '未配置或无效'}")

    # 测试意图识别
    await test_intent_recognition()

    logger.info("="*50)

    # 测试知识沉淀
    await test_knowledge_precipitation()

    logger.info("真实大模型调用测试完成")
    logger.info("请查看日志文件了解大模型的输入输出详情")


if __name__ == "__main__":
    asyncio.run(main())
