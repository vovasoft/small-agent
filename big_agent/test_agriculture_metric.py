#!/usr/bin/env python3
"""
测试农业指标计算的脚本
"""

import asyncio
import sys
import os
sys.path.append('.')

from agents.metric_calculation_agent import MetricCalculationAgent


async def test_agriculture_metric():
    """测试农业-交易对手支出排名TOP3指标计算"""

    print("🚀 开始测试农业-交易对手支出排名TOP3指标计算")
    print("=" * 60)

    # 创建指标计算代理
    agent = MetricCalculationAgent("dummy_api_key")

    # 查看数据文件映射
    print("📁 数据文件映射:")
    for key, path in agent.data_files.items():
        print(f"  {key}: {path}")
    print()

    # 测试配置文件
    config_name = "指标计算-农业-交易对手支出排名TOP3"

    # 测试数据文件选择
    print(f"🔍 测试配置文件: {config_name}")
    selected_data_file = agent._select_data_file(config_name)
    print(f"   选择的数据文件: {selected_data_file}")

    if selected_data_file:
        # 检查文件是否存在
        if os.path.exists(selected_data_file):
            print(f"   ✅ 文件存在，路径有效")

            # 尝试加载数据
            table_data = agent._load_table_data(selected_data_file)
            print(f"   📊 加载数据条数: {len(table_data)}")

            if table_data:
                print(f"   🔍 样本数据 (前3条):")
                for i, row in enumerate(table_data[:3], 1):
                    # 只显示部分字段
                    sample_fields = {k: v for k, v in row.items() if k in ['txCounterparty', 'txAmount', 'txDirection', 'businessType']}
                    print(f"     {i}. {sample_fields}")
        else:
            print(f"   ❌ 文件不存在: {selected_data_file}")
    else:
        print("   ❌ 没有找到对应的数据文件")

    print("\n" + "=" * 60)

    # 测试实际的指标计算
    print("🧮 开始执行指标计算...")

    # 构造意图识别结果
    intent_result = {
        "target_configs": [config_name],
        "intent_category": "指标计算"
    }

    try:
        # 执行指标计算
        result = await agent.calculate_metrics(intent_result)

        print("📋 计算结果:")
        print(f"   成功: {result.get('success', False)}")
        print(f"   总配置数: {result.get('total_configs', 0)}")
        print(f"   成功计算数: {result.get('successful_calculations', 0)}")

        if result.get('success') and result.get('results'):
            for item in result['results']:
                print(f"\n   配置: {item.get('config_name')}")
                if 'result' in item:
                    calc_result = item['result']
                    print(f"   计算成功: {calc_result.get('success', False)}")
                    if calc_result.get('success'):
                        print("   📊 结果数据已生成")
                else:
                    print(f"   错误: {item.get('error', '未知错误')}")

    except Exception as e:
        print(f"❌ 计算过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 测试完成")


if __name__ == "__main__":
    asyncio.run(test_agriculture_metric())
