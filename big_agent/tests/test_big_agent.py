"""
Big Agent测试脚本
测试完整的LangGraph工作流功能
"""

import asyncio
import os
import sys
from config import DEEPSEEK_API_KEY, CONFIG_VALID, validate_config
from big_agent_workflow import run_big_agent


async def test_basic_workflow():
    """测试基本工作流"""
    print("=== 测试基本工作流 ===")

    if not CONFIG_VALID:
        errors = validate_config()
        print("配置错误:")
        for error in errors:
            print(f"  - {error}")
        print("\n请设置正确的环境变量后重试")
        return False

    # 测试用例1: 农业指标查询
    test_input_1 = "我想计算农业的相关指标情况"

    print(f"测试输入: {test_input_1}")

    try:
        result = await run_big_agent(test_input_1, DEEPSEEK_API_KEY)

        if result["success"]:
            print("[SUCCESS] 工作流执行成功")

            workflow_result = result["result"]
            intent_result = workflow_result.get("intent_result", {})
            calculation_results = workflow_result.get("calculation_results", {})
            knowledge_result = workflow_result.get("knowledge_result", {})

            print("意图识别结果:")
            print(f"  - 类别: {intent_result.get('intent_category', 'unknown')}")
            print(f"  - 置信度: {intent_result.get('confidence', 0):.2f}")
            print(f"  - 目标配置: {intent_result.get('target_configs', [])}")

            print("指标计算结果:")
            print(f"  - 成功: {calculation_results.get('successful_calculations', 0)}")
            print(f"  - 总数: {calculation_results.get('total_configs', 0)}")

            if knowledge_result.get("success"):
                print("[SUCCESS] 知识沉淀成功")
                if knowledge_result.get("saved_path"):
                    print(f"  - 保存路径: {knowledge_result['saved_path']}")
            else:
                print("[ERROR] 知识沉淀失败")

            execution_time = result.get("execution_time")
            if execution_time:
                print(f"执行时间: {execution_time:.2f}秒")

            return True

        else:
            print("X 工作流执行失败")
            print(f"错误: {result.get('error', '未知错误')}")
            return False

    except Exception as e:
        print(f"[ERROR] 测试异常: {str(e)}")
        return False


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")

    # 测试无效输入
    test_input = ""

    try:
        result = await run_big_agent(test_input, DEEPSEEK_API_KEY)

        if not result["success"]:
            print("[SUCCESS] 错误处理正常工作")
            return True
        else:
            print("[ERROR] 错误处理未正确捕获错误")
            return False

    except Exception as e:
        print(f"[ERROR] 错误处理测试异常: {str(e)}")
        return False


async def test_workflow_components():
    """测试工作流组件"""
    print("\n=== 测试工作流组件 ===")

    from big_agent_workflow import BigAgentWorkflow

    try:
        workflow = BigAgentWorkflow(DEEPSEEK_API_KEY)
        status = workflow.get_workflow_status()

        print("工作流状态:")
        print(f"  - 可用配置: {status['available_configs']}")
        print(f"  - 知识库统计: {status['knowledge_stats']}")
        print(f"  - 工作流节点: {status['workflow_nodes']}")

        return True

    except Exception as e:
        print(f"[ERROR] 组件测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("Big Agent 测试开始")
    print("=" * 50)

    # 检查环境
    if not DEEPSEEK_API_KEY:
        print("[ERROR] 未找到DEEPSEEK_API_KEY环境变量")
        print("请创建.env文件并设置API密钥")
        print("参考.env.example文件")
        return

    # 运行测试
    test_results = []

    # 测试1: 基本工作流
    test_results.append(await test_basic_workflow())

    # 测试2: 错误处理
    test_results.append(await test_error_handling())

    # 测试3: 组件测试
    test_results.append(await test_workflow_components())

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")

    passed = sum(test_results)
    total = len(test_results)

    for i, result in enumerate(test_results, 1):
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        print(f"  测试{i}: {status}")

    print(f"\n总体结果: {passed}/{total} 通过")

    if passed == total:
        print("[SUCCESS] 所有测试通过！Big Agent系统运行正常")
    else:
        print("[WARNING] 部分测试失败，请检查系统配置")


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
