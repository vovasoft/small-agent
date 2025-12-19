"""
Big Agent 演示脚本
================

此脚本提供Big Agent系统的用户友好演示，展示如何使用系统进行农业指标计算。

演示内容：
1. 环境检查
   - 验证系统配置完整性
   - 检查API密钥可用性
   - 确认必要文件和目录存在

2. 农业指标计算演示
   - 展示完整的查询->分析->计算->报告流程
   - 演示意图识别和指标匹配
   - 展示知识文档自动生成

3. 结果展示和分析
   - 格式化输出计算结果
   - 展示生成的知识文档
   - 提供使用统计信息

4. 错误处理演示
   - 展示配置问题时的错误提示
   - 演示网络问题时的降级处理
   - 提供故障排除指导

技术特点：
- 用户友好的交互界面
- 彩色控制台输出
- 进度指示和状态反馈
- 完善的错误处理
- 教育性的注释和说明

使用方法：
1. 确保系统已正确配置
2. 运行: python demo.py
3. 跟随控制台提示进行操作
4. 查看生成的知识文档

演示查询示例：
- "我想计算农业的相关指标情况"
- "帮我分析农业总支出和总收入"
- "计算2023年全国粮食作物的农业指标"

输出说明：
- 实时显示处理进度
- 详细的计算结果展示
- 生成的知识文档路径
- 性能统计信息

适用场景：
- 新用户系统介绍
- 功能特性展示
- 快速功能验证
- 教学和培训

注意事项：
- 需要有效的API密钥进行完整演示
- 演示过程中会产生API调用费用
- 网络连接影响演示效果

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

import asyncio
import os
from config import DEEPSEEK_API_KEY, CONFIG_VALID
from big_agent_workflow import run_big_agent


async def demo_agriculture_metrics():
    """演示农业指标计算"""
    print("=== Big Agent 农业指标计算演示 ===")
    print()

    if not CONFIG_VALID:
        print("[ERROR] 配置无效，请检查环境变量设置")
        print("请确保设置了有效的 DEEPSEEK_API_KEY")
        return

    # 示例查询
    queries = [
        "我想计算农业的相关指标情况",
        "帮我分析农业总支出和总收入",
        "计算2023年农业经济指标数据"
    ]

    for i, query in enumerate(queries, 1):
        print(f"查询 {i}: {query}")
        print("-" * 50)

        try:
            result = await run_big_agent(query, DEEPSEEK_API_KEY)

            if result["success"]:
                print("[SUCCESS] 处理成功")

                workflow_result = result["result"]

                # 显示意图识别结果
                intent_result = workflow_result.get("intent_result", {})
                if intent_result:
                    print(f"意图类别: {intent_result.get('intent_category', 'unknown')}")
                    print(f"目标配置: {intent_result.get('target_configs', [])}")

                # 显示计算结果
                calculation_results = workflow_result.get("calculation_results", {})
                if calculation_results:
                    successful = calculation_results.get("successful_calculations", 0)
                    total = calculation_results.get("total_configs", 0)
                    print(f"计算结果: {successful}/{total} 成功")

                # 显示知识沉淀结果
                knowledge_result = workflow_result.get("knowledge_result", {})
                if knowledge_result and knowledge_result.get("success"):
                    print("[SUCCESS] 知识文档已生成")
                    if knowledge_result.get("saved_path"):
                        print(f"保存路径: {knowledge_result['saved_path']}")

                execution_time = result.get("execution_time")
                if execution_time:
                    print(".2f")

            else:
                print("[ERROR] 处理失败")
                print(f"错误: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"[ERROR] 执行异常: {str(e)}")

        print()
        print("=" * 50)
        print()


async def demo_knowledge_search():
    """演示知识库搜索功能"""
    print("=== 知识库搜索演示 ===")
    print()

    try:
        from agents.knowledge_precipitation_agent import KnowledgePrecipitationAgent

        agent = KnowledgePrecipitationAgent(DEEPSEEK_API_KEY)

        # 搜索农业相关的知识
        search_results = agent.search_knowledge("农业", limit=3)

        if search_results:
            print(f"找到 {len(search_results)} 条相关知识:")
            for i, result in enumerate(search_results, 1):
                doc = result["document"]
                print(f"{i}. {doc.get('title', '无标题')}")
                print(f"   创建时间: {doc.get('metadata', {}).get('created_at', 'unknown')}")
                if doc.get('summary'):
                    summary = doc['summary'][:100] + "..." if len(doc['summary']) > 100 else doc['summary']
                    print(f"   摘要: {summary}")
                print()
        else:
            print("知识库中没有找到相关内容")

    except Exception as e:
        print(f"[ERROR] 搜索失败: {str(e)}")

    print()


async def show_system_status():
    """显示系统状态"""
    print("=== 系统状态 ===")
    print()

    try:
        from big_agent_workflow import BigAgentWorkflow

        workflow = BigAgentWorkflow(DEEPSEEK_API_KEY)
        status = workflow.get_workflow_status()

        print("可用指标配置:")
        for config in status["available_configs"]:
            print(f"  - {config}")
        print()

        knowledge_stats = status["knowledge_stats"]
        print("知识库统计:")
        print(f"  - 文档数量: {knowledge_stats['total_documents']}")
        print(f"  - 总大小: {knowledge_stats['total_size_mb']:.2f} MB")
        print()

        print("工作流节点:")
        for node in status["workflow_nodes"]:
            print(f"  - {node}")

    except Exception as e:
        print(f"[ERROR] 获取状态失败: {str(e)}")

    print()


async def main():
    """主演示函数"""
    print("Big Agent 多Agent LangGraph框架演示")
    print("=" * 60)
    print()

    # 显示系统状态
    await show_system_status()

    # 演示农业指标计算
    await demo_agriculture_metrics()

    # 演示知识库搜索
    await demo_knowledge_search()

    print("演示完成！")
    print()
    print("使用提示:")
    print("1. 设置有效的 DEEPSEEK_API_KEY 以获得完整功能")
    print("2. 修改 json_files/ 下的配置文件以添加新的指标计算")
    print("3. 查看 knowledge_base/ 目录中的知识文档")
    print("4. 运行 python test_big_agent.py 进行系统测试")


if __name__ == "__main__":
    asyncio.run(main())
