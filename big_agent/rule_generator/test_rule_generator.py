#!/usr/bin/env python3
"""
规则生成器测试脚本
=================

支持从CSV或Excel文件批量导入指标定义进行测试。
会为每个指标生成规则并保存为JSON文件。

支持的文件格式：
- CSV文件：指标名称,指标描述
- Excel文件：xlsx格式，第一列指标名称，第二列指标描述

作者: Big Agent Team
版本: 2.0.0
"""

import json
import os
import sys
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

# 导入规则生成器
from rule_generator.generator import RuleGenerator


def load_metrics_from_file(file_path: str) -> pd.DataFrame:
    """
    从CSV或Excel文件加载指标定义

    Args:
        file_path: 文件路径

    Returns:
        包含指标名称和描述的DataFrame
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_extension = Path(file_path).suffix.lower()

    try:
        if file_extension == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}。请使用CSV或Excel文件。")

        # 检查必要的列
        required_columns = ['指标名称', '指标描述']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"文件必须包含以下列: {required_columns}")

        # 清理数据：删除空行
        df = df.dropna(subset=required_columns)

        print(f"✓ 成功加载 {len(df)} 个指标定义")
        return df

    except Exception as e:
        raise Exception(f"读取文件失败: {e}")


def generate_rule_id(metric_name: str) -> str:
    """
    根据指标名称生成规则ID

    Args:
        metric_name: 指标名称

    Returns:
        规则ID字符串
    """
    # 清理特殊字符，转换为英文标识符格式
    import re
    clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', metric_name)
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')

    # 生成ID，限制长度
    rule_id = f"metric-{clean_name}"
    if len(rule_id) > 50:
        rule_id = rule_id[:47] + "..."

    return rule_id


def generate_single_metric(generator, metric_data, output_dir):
    """
    生成单个指标的规则

    Args:
        generator: RuleGenerator实例
        metric_data: 包含指标信息的字典
        output_dir: 输出目录

    Returns:
        生成结果字典
    """
    idx, row = metric_data['idx'], metric_data['row']
    metric_name = str(row['指标名称']).strip()
    metric_desc = str(row['指标描述']).strip()

    try:
        start_time = time.time()

        # 生成规则ID
        rule_id = generate_rule_id(metric_name)

        # 创建payload
        payload = generator.create_decision_knowledge_payload(
            id=rule_id,
            name=metric_name,
            ruleDescription=metric_desc
        )

        # 生成文件名
        safe_filename = re.sub(r'[^\w\u4e00-\u9fff]', '_', metric_name)
        filename = f"{output_dir}/rule_{safe_filename}.json"

        # 保存JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        elapsed_time = time.time() - start_time

        return {
            'success': True,
            'metric_name': metric_name,
            'filename': filename,
            'rule_steps': len(payload['ruleDefinition']['ruleContent']),
            'elapsed_time': elapsed_time,
            'error': None
        }

    except Exception as e:
        return {
            'success': False,
            'metric_name': metric_name,
            'filename': None,
            'rule_steps': 0,
            'elapsed_time': 0,
            'error': str(e)
        }


def generate_metrics_batch(file_path: str, max_workers: int = 3, skip_api_save: bool = True):
    """
    批量生成指标规则

    Args:
        file_path: 包含指标定义的文件路径
        max_workers: 最大并发数（默认3，避免API限流）
        skip_api_save: 是否跳过API保存（默认True，只生成JSON文件）
    """
    print("规则生成器 - 批量指标规则生成")
    print("============================")

    # 检查环境配置
    if not DEEPSEEK_API_KEY:
        print("✗ DEEPSEEK_API_KEY环境变量未设置")
        return False

    print("✓ API配置正常")
    print(f"⚙️  并发数: {max_workers}")
    print(f"💾 跳过API保存: {skip_api_save}")

    try:
        # 加载指标定义
        df = load_metrics_from_file(file_path)
        total_metrics = len(df)

        # 初始化生成器（每个线程都需要自己的实例）
        def create_generator():
            return RuleGenerator(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL
            )

        # 创建输出目录
        output_dir = "generated_metrics_rules"
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n🚀 开始并发处理 {total_metrics} 个指标...")

        # 准备任务数据
        tasks = [{'idx': idx, 'row': row} for idx, row in df.iterrows()]

        success_count = 0
        generated_files = []
        total_time = 0

        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(generate_single_metric, create_generator(), task, output_dir): task
                for task in tasks
            }

            # 处理完成的任务
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                idx = task['idx'] + 1

                try:
                    result = future.result()

                    if result['success']:
                        print(f"✓ [{idx:2d}/{total_metrics}] {result['metric_name'][:20]:20} "
                              f"({result['elapsed_time']:.1f}s, {result['rule_steps']}步) -> {os.path.basename(result['filename'])}")
                        success_count += 1
                        generated_files.append(result['filename'])
                        total_time += result['elapsed_time']
                    else:
                        print(f"✗ [{idx:2d}/{total_metrics}] {result['metric_name'][:20]:20} -> {result['error']}")

                except Exception as e:
                    metric_name = str(task['row']['指标名称']).strip()
                    print(f"✗ [{idx:2d}/{total_metrics}] {metric_name[:20]:20} -> 任务执行异常: {e}")

        # 计算统计信息
        avg_time = total_time / success_count if success_count > 0 else 0

        print(f"\n🎉 批量生成完成！")
        print(f"📊 成功生成: {success_count}/{total_metrics} 个指标规则")
        print(f"⏱️  总耗时: {total_time:.1f}秒")
        print(f"📈 平均耗时: {avg_time:.1f}秒/指标")
        print(f"⚡ 并发效率: {total_time/max_workers:.1f}秒 (理论最小时间)")
        print(f"📁 输出目录: {output_dir}")

        if generated_files:
            print("📋 生成的文件：")
            for file in generated_files[:5]:  # 只显示前5个
                print(f"   - {os.path.basename(file)}")
            if len(generated_files) > 5:
                print(f"   ... 还有 {len(generated_files) - 5} 个文件")

        return True

    except Exception as e:
        print(f"✗ 批量生成失败: {e}")
        return False


def generate_and_save_json():
    """生成并保存JSON文件"""
    print("规则生成器 - JSON文件生成")
    print("========================")

    # 检查环境配置
    if not DEEPSEEK_API_KEY:
        print("✗ DEEPSEEK_API_KEY环境变量未设置")
        return

    print("✓ API配置正常")

    try:
        generator = RuleGenerator(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

        # 测试用例1：简单筛选规则
        print("\n生成测试用例1：金额筛选规则")
        payload1 = generator.create_decision_knowledge_payload(
            id="filter-amount-001",
            name="金额筛选规则",
            ruleDescription="筛选出交易金额大于1000的记录"
        )

        # 保存JSON文件
        filename1 = "generated_rule_filter_amount.json"
        with open(filename1, 'w', encoding='utf-8') as f:
            json.dump(payload1, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON文件已保存: {filename1}")
        print(f"✓ 生成了 {len(payload1['ruleDefinition']['ruleContent'])} 个规则步骤")

        # 显示规则内容摘要
        for i, step in enumerate(payload1['ruleDefinition']['ruleContent'], 1):
            print(f"  步骤{i}: {step.get('type', 'UNKNOWN')}")

        # 测试用例2：分组聚合规则
        print("\n生成测试用例2：分组聚合规则")
        payload2 = generator.create_decision_knowledge_payload(
            id="group-aggregate-002",
            name="分组聚合规则",
            ruleDescription="按交易对手分组，计算每个对手的总交易金额，降序排列取前3名"
        )

        # 保存JSON文件
        filename2 = "generated_rule_group_aggregate.json"
        with open(filename2, 'w', encoding='utf-8') as f:
            json.dump(payload2, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON文件已保存: {filename2}")
        print(f"✓ 生成了 {len(payload2['ruleDefinition']['ruleContent'])} 个规则步骤")

        # 显示规则内容摘要
        for i, step in enumerate(payload2['ruleDefinition']['ruleContent'], 1):
            print(f"  步骤{i}: {step.get('type', 'UNKNOWN')}")

        # 测试用例3：复杂业务规则
        print("\n生成测试用例3：黑色金属支出TOP3规则")
        payload3 = generator.create_decision_knowledge_payload(
            id="black-metal-expense-003",
            name="黑色金属支出TOP3",
            ruleDescription="筛选出业务类型为'支出/经营/经营支出（黑色金属）'的交易记录，按交易对手分组，计算总支出金额，降序排序取前3名"
        )

        # 保存JSON文件
        filename3 = "generated_rule_black_metal_expense.json"
        with open(filename3, 'w', encoding='utf-8') as f:
            json.dump(payload3, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON文件已保存: {filename3}")
        print(f"✓ 生成了 {len(payload3['ruleDefinition']['ruleContent'])} 个规则步骤")

        # 显示规则内容摘要
        for i, step in enumerate(payload3['ruleDefinition']['ruleContent'], 1):
            print(f"  步骤{i}: {step.get('type', 'UNKNOWN')}")

        print("\n🎉 所有JSON文件生成完成！")
        print("📁 生成的文件：")
        print(f"   - {filename1}")
        print(f"   - {filename2}")
        print(f"   - {filename3}")
        print("\n💡 您可以打开这些JSON文件查看生成的完整规则内容")

        return True

    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='规则生成器测试脚本')
    parser.add_argument('--batch', '-b', type=str, help='批量处理模式：指定包含指标定义的CSV或Excel文件路径')
    parser.add_argument('--workers', '-w', type=int, default=3, help='并发数（默认3，避免API限流）')
    parser.add_argument('--skip-api', action='store_true', help='跳过API保存，只生成JSON文件')
    parser.add_argument('--legacy', '-l', action='store_true', help='运行传统测试模式（生成示例规则）')

    args = parser.parse_args()

    if args.batch:
        # 批量处理模式
        print(f"🚀 启动批量处理模式")
        print(f"📁 文件: {args.batch}")
        print(f"⚡ 并发数: {args.workers}")
        print(f"💾 跳过API: {args.skip_api}")

        success = generate_metrics_batch(
            file_path=args.batch,
            max_workers=args.workers,
            skip_api_save=args.skip_api
        )
        if success:
            print("\n✅ 批量指标规则生成成功！")
        else:
            print("\n❌ 批量指标规则生成失败！")
            sys.exit(1)
    else:
        # 默认传统测试模式
        success = generate_and_save_json()
        if success:
            print("\n✅ JSON文件生成成功！")
        else:
            print("\n❌ JSON文件生成失败！")
            sys.exit(1)


if __name__ == "__main__":
    main()
