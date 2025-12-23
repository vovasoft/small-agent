#!/usr/bin/env python3
"""
测试规则执行
===========

使用 /api/rules/executeKnowledge 接口测试已保存的规则
"""

import json
import os
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def load_test_data(data_file_path):
    """
    加载测试数据

    Args:
        data_file_path: 测试数据文件路径

    Returns:
        测试数据
    """
    try:
        with open(data_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取resultTag数组作为测试数据
        if isinstance(data, dict) and 'resultTag' in data:
            test_data = data['resultTag']
        elif isinstance(data, list):
            test_data = data
        else:
            test_data = [data]

        print(f"✅ 成功加载 {len(test_data)} 条测试数据")
        return test_data

    except Exception as e:
        print(f"❌ 加载测试数据失败: {e}")
        return None


def execute_single_rule(rule_id, test_data, api_url="http://localhost:8081"):
    """
    执行单个规则测试

    Args:
        rule_id: 规则ID
        test_data: 测试数据
        api_url: API基础URL

    Returns:
        执行结果字典
    """
    try:
        # 构建API URL
        url = f"{api_url}/api/rules/executeKnowledge"

        # 构建请求头
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanRuntime-ApipostRuntime/1.1.0'
        }

        # 构建请求体
        payload = {
            "id": rule_id,
            "input": {
                "transactions": test_data
            }
        }

        # 发送请求
        print(f"🚀 正在测试规则: {rule_id}")
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ 规则 {rule_id} 执行成功 ({elapsed_time:.2f}s)")

                return {
                    'success': True,
                    'rule_id': rule_id,
                    'elapsed_time': elapsed_time,
                    'result': result,
                    'response': response.text
                }
            except json.JSONDecodeError:
                print(f"⚠️ 规则 {rule_id} 返回非JSON格式 ({elapsed_time:.2f}s)")
                return {
                    'success': True,
                    'rule_id': rule_id,
                    'elapsed_time': elapsed_time,
                    'result': None,
                    'response': response.text
                }
        else:
            print(f"❌ 规则 {rule_id} 执行失败 [{response.status_code}] ({elapsed_time:.2f}s)")
            return {
                'success': False,
                'rule_id': rule_id,
                'elapsed_time': elapsed_time,
                'error': f"HTTP {response.status_code}: {response.text}",
                'response': response.text
            }

    except Exception as e:
        print(f"❌ 规则 {rule_id} 测试异常: {e}")
        return {
            'success': False,
            'rule_id': rule_id,
            'elapsed_time': 0,
            'error': str(e),
            'response': None
        }


def save_execution_result(rule_id, result, output_dir):
    """
    保存执行结果到文件

    Args:
        rule_id: 规则ID
        result: 执行结果
        output_dir: 输出目录
    """
    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 构建文件名
        safe_rule_id = rule_id.replace('-', '_')
        filename = f"{output_dir}/execution_result_{safe_rule_id}.json"

        # 构建输出数据
        output_data = {
            'rule_id': rule_id,
            'execution_time': result.get('elapsed_time', 0),
            'success': result.get('success', False),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'result': result.get('result'),
            'error': result.get('error'),
            'raw_response': result.get('response')
        }

        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"💾 结果已保存: {filename}")
        return filename

    except Exception as e:
        print(f"❌ 保存结果失败: {rule_id} - {e}")
        return None


def test_rules_execution(test_data_file, output_dir="execution_results", api_url="http://localhost:8081", max_workers=2):
    """
    批量测试规则执行

    Args:
        test_data_file: 测试数据文件路径
        output_dir: 输出目录
        api_url: API基础URL
        max_workers: 最大并发数
    """
    print("🧪 批量测试规则执行")
    print("=" * 50)
    print(f"📁 测试数据: {test_data_file}")
    print(f"📂 输出目录: {output_dir}")
    print(f"🌐 API地址: {api_url}")
    print(f"⚡ 并发数: {max_workers}")

    # 加载测试数据
    test_data = load_test_data(test_data_file)
    if not test_data:
        return

    # 定义要测试的规则ID列表
    rule_ids = [
        "metric-总收入",
        "metric-收入笔数",
        "metric-收入数据时间范围",
        "metric-各类型收入占总收入比例",
        "metric-总支出",
        "metric-支出笔数",
        "metric-支出数据时间范围",
        "metric-各类型支出占总支出比例",
        "metric-分析账户数量",
        "metric-各账户交易时间范围",
        "metric-流入流出月度统计",
        "metric-分月按交易渠道总明细收入",
        "metric-分月按交易渠道总明细支出",
        "metric-分月总收入",
        "metric-分月总支出"
    ]

    print(f"📊 准备测试 {len(rule_ids)} 个规则")
    print()

    # 开始批量测试
    success_count = 0
    total_time = 0
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有测试任务
        future_to_rule = {
            executor.submit(execute_single_rule, rule_id, test_data, api_url): rule_id
            for rule_id in rule_ids
        }

        # 处理完成的任务
        for future in as_completed(future_to_rule):
            rule_id = future_to_rule[future]
            try:
                result = future.result()
                results.append(result)

                if result['success']:
                    success_count += 1
                    total_time += result.get('elapsed_time', 0)

                # 保存结果到文件
                save_execution_result(rule_id, result, output_dir)

            except Exception as e:
                print(f"❌ 处理结果异常: {rule_id} - {e}")

    # 输出统计结果
    print("\n" + "=" * 50)
    print("📊 测试结果统计")
    print(f"✅ 执行成功: {success_count}/{len(rule_ids)}")
    print(f"❌ 执行失败: {len(rule_ids) - success_count}/{len(rule_ids)}")
    print(f"⏱️ 平均耗时: {total_time/max(success_count, 1):.2f}秒/规则")
    print(f"📁 输出目录: {output_dir}")

    if success_count > 0:
        print("\n📋 成功的规则:")
        for result in results:
            if result['success']:
                print(".2f")

    failed_count = len(rule_ids) - success_count
    if failed_count > 0:
        print("\n❌ 失败的规则:")
        for result in results:
            if not result['success']:
                print(f"   - {result['rule_id']}: {result.get('error', '未知错误')}")

    return success_count, results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='测试规则执行')
    parser.add_argument('--data-file', '-d',
                       default='../data_files/加工数据-流水分析-农业打标.json',
                       help='测试数据文件路径')
    parser.add_argument('--output-dir', '-o', default='execution_results',
                       help='执行结果输出目录')
    parser.add_argument('--api-url', '-u', default='http://localhost:8081',
                       help='规则引擎API基础URL')
    parser.add_argument('--workers', '-w', type=int, default=2,
                       help='并发测试数')

    args = parser.parse_args()

    success_count, results = test_rules_execution(
        test_data_file=args.data_file,
        output_dir=args.output_dir,
        api_url=args.api_url,
        max_workers=args.workers
    )

    if success_count > 0:
        print(f"\n🎉 规则测试完成！{success_count} 个规则执行成功")
    else:
        print("\n❌ 所有规则测试失败！")
        exit(1)


if __name__ == "__main__":
    main()
