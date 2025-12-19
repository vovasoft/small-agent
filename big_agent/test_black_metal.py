"""
黑色金属指标计算测试脚本
========================

此脚本专门用于测试黑色金属总经营收入的计算功能，包含完整的日志记录。

测试内容：
- 测试查询："请计算黑色金属总经营收入"
- 完整流程日志记录到logs目录
- 详细的执行过程跟踪

日志功能：
- 记录每个工作流节点的执行状态
- 记录API调用详情
- 记录计算结果和错误信息
- 记录执行时间统计

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-19
"""

import asyncio
import logging
import os
from datetime import datetime
from config import DEEPSEEK_API_KEY, CONFIG_VALID, PATHS
from big_agent_workflow import run_big_agent


def setup_logging():
    """
    设置详细的日志记录配置

    日志级别：DEBUG
    日志格式：包含时间戳、级别、模块名和消息
    日志文件：保存到logs目录，按日期命名
    """
    # 确保logs目录存在
    logs_dir = PATHS["logs"]
    os.makedirs(logs_dir, exist_ok=True)

    # 生成日志文件名（包含日期）
    today = datetime.now().strftime("%Y%m%d")
    log_filename = f"black_metal_test_{today}.log"
    log_filepath = os.path.join(logs_dir, log_filename)

    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 清除现有的handlers（避免重复）
    logger.handlers.clear()

    # 创建文件handler
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建格式器
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # 设置格式器
    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)

    # 添加handlers到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("=" * 80)
    logging.info("黑色金属指标计算测试开始")
    logging.info(f"日志文件: {log_filepath}")
    logging.info("=" * 80)

    return logger


async def test_black_metal_calculation():
    """
    执行黑色金属总经营收入计算测试

    测试流程：
    1. 验证配置
    2. 执行Big Agent工作流
    3. 记录详细的执行过程
    4. 输出测试结果
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("开始黑色金属指标计算测试")

        # 1. 配置验证
        logger.info("步骤1: 验证系统配置")
        if not CONFIG_VALID:
            logger.error("配置验证失败，请检查环境变量设置")
            logger.error("请确保设置了有效的 DEEPSEEK_API_KEY")
            return False

        logger.info("✓ 配置验证通过")

        # 2. 定义测试查询
        test_query = "请计算黑色金属总经营收入"
        logger.info(f"步骤2: 测试查询 - {test_query}")

        # 3. 执行工作流
        logger.info("步骤3: 执行Big Agent工作流")
        start_time = datetime.now()

        logger.debug("调用run_big_agent函数")
        result = await run_big_agent(test_query, DEEPSEEK_API_KEY)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        logger.info(f"工作流执行完成，耗时: {execution_time:.2f}秒")
        # 4. 处理结果
        logger.info("步骤4: 处理和分析结果")

        if result["success"]:
            logger.info("✓ 工作流执行成功")

            workflow_result = result["result"]

            # 记录意图识别结果
            intent_result = workflow_result.get("intent_result", {})
            if intent_result:
                logger.info("意图识别结果:")
                logger.info(f"  - 意图类别: {intent_result.get('intent_category', 'unknown')}")
                logger.info(f"  - 置信度: {intent_result.get('confidence', 0):.2f}")
                logger.info(f"  - 目标配置: {intent_result.get('target_configs', [])}")

                # 记录意图识别的详细分析
                analysis = intent_result.get('analysis', {})
                if analysis:
                    logger.debug("意图识别详细分析:")
                    for key, value in analysis.items():
                        logger.debug(f"  {key}: {value}")

            # 记录计算结果
            calculation_results = workflow_result.get("calculation_results", {})
            if calculation_results:
                logger.info("指标计算结果:")
                logger.info(f"  - 成功计算: {calculation_results.get('successful_calculations', 0)}")
                logger.info(f"  - 总配置数: {calculation_results.get('total_configs', 0)}")
                logger.info(f"  - 失败计算: {calculation_results.get('failed_calculations', 0)}")

                # 记录具体的计算详情
                successful_calculations = calculation_results.get('successful_calculations_details', [])
                failed_calculations = calculation_results.get('failed_calculations_details', [])

                if successful_calculations:
                    logger.info("成功的计算详情:")
                    for calc in successful_calculations:
                        logger.info(f"  ✓ {calc.get('config_name', 'unknown')}: {calc.get('result', 'no result')}")

                if failed_calculations:
                    logger.warning("失败的计算详情:")
                    for calc in failed_calculations:
                        logger.warning(f"  ✗ {calc.get('config_name', 'unknown')}: {calc.get('error', 'unknown error')}")

            # 记录知识沉淀结果
            knowledge_result = workflow_result.get("knowledge_result", {})
            if knowledge_result and knowledge_result.get("success"):
                logger.info("✓ 知识沉淀成功")
                if knowledge_result.get("saved_path"):
                    logger.info(f"  - 知识文档路径: {knowledge_result['saved_path']}")

                # 记录知识文档的元数据
                metadata = knowledge_result.get('metadata', {})
                if metadata:
                    logger.debug("知识文档元数据:")
                    for key, value in metadata.items():
                        logger.debug(f"  {key}: {value}")

            # 记录执行时间
            if result.get("execution_time"):
                logger.info(f"  - 工作流执行时间: {result['execution_time']:.2f}秒")
            # 记录对话历史
            messages = workflow_result.get("messages", [])
            if messages:
                logger.debug(f"对话历史共 {len(messages)} 条消息")
                for i, msg in enumerate(messages, 1):
                    logger.debug(f"消息 {i}: [{msg.get('role', 'unknown')}] {msg.get('content', '')[:100]}...")

            # 记录API调用结果
            api_result = workflow_result.get("api_result", {})
            if api_result:
                logger.info(f"API调用结果: 共 {len(api_result)} 个API调用")
                for call_id, call_info in api_result.items():
                    logger.info(f"  - {call_id}: {call_info.get('agent', 'unknown')} - {call_info.get('success', False)} - {call_info.get('response', {}).get('duration', 0):.2f}s")
                    if not call_info.get('success', True):
                        logger.warning(f"    错误: {call_info.get('response', {}).get('error', 'unknown error')}")
            else:
                logger.warning("未找到API调用结果")

            # 记录错误信息
            errors = workflow_result.get("errors", [])
            if errors:
                logger.warning(f"执行过程中发现 {len(errors)} 个错误:")
                for error in errors:
                    logger.warning(f"  - {error}")

        else:
            logger.error("✗ 工作流执行失败")
            logger.error(f"错误信息: {result.get('error', '未知错误')}")

            # 记录详细的错误信息
            workflow_result = result.get("result")
            if workflow_result:
                errors = workflow_result.get("errors", [])
                if errors:
                    logger.error("详细错误列表:")
                    for error in errors:
                        logger.error(f"  - {error}")

            return False

        logger.info("=" * 80)
        logger.info("黑色金属指标计算测试完成")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"测试执行异常: {str(e)}", exc_info=True)
        return False


async def main():
    """主函数"""
    # 设置日志
    setup_logging()

    logger = logging.getLogger(__name__)

    try:
        # 执行测试
        success = await test_black_metal_calculation()

        if success:
            logger.info("🎉 测试成功完成！")
            print("\n🎉 测试成功完成！请查看logs目录中的详细日志文件。")
        else:
            logger.error("❌ 测试失败！")
            print("\n❌ 测试失败！请查看logs目录中的错误日志。")

    except KeyboardInterrupt:
        logger.info("用户中断测试")
        print("\n测试被用户中断")

    except Exception as e:
        logger.critical(f"未处理的异常: {str(e)}", exc_info=True)
        print(f"\n发生未处理的异常: {str(e)}")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())