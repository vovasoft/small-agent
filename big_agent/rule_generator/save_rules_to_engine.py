#!/usr/bin/env python3
"""
批量保存规则到规则引擎
===================

将生成的JSON规则文件批量保存到规则引擎API
"""

import json
import os
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def save_single_rule(json_file_path, api_url="http://localhost:8081"):
    """
    保存单个规则到规则引擎

    Args:
        json_file_path: JSON文件路径
        api_url: API基础URL

    Returns:
        保存结果字典
    """
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        rule_name = payload['decisionKnowledge']['name']
        rule_id = payload['decisionKnowledge']['id']

        # 构建API URL
        url = f"{api_url}/api/rules/saveDecisionKnowledge"

        # 设置请求头
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanRuntime-ApipostRuntime/1.1.0'
        }

        # 发送请求
        print(f"📤 正在保存规则: {rule_name} (ID: {rule_id})")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            print(f"✅ 规则保存成功: {rule_name}")
            return {
                'success': True,
                'rule_name': rule_name,
                'rule_id': rule_id,
                'file_path': json_file_path,
                'response': response.text
            }
        else:
            print(f"❌ 规则保存失败 [{response.status_code}]: {rule_name}")
            return {
                'success': False,
                'rule_name': rule_name,
                'rule_id': rule_id,
                'file_path': json_file_path,
                'error': f"HTTP {response.status_code}: {response.text}"
            }

    except Exception as e:
        rule_name = Path(json_file_path).stem.replace('rule_', '')
        print(f"❌ 处理异常: {rule_name} - {e}")
        return {
            'success': False,
            'rule_name': rule_name,
            'file_path': json_file_path,
            'error': str(e)
        }


def save_rules_batch(rules_dir, api_url="http://localhost:8081", max_workers=2):
    """
    批量保存规则到规则引擎

    Args:
        rules_dir: 包含规则JSON文件的目录
        api_url: API基础URL
        max_workers: 最大并发数
    """
    print("🚀 批量保存规则到规则引擎")
    print("=" * 50)
    print(f"📁 规则目录: {rules_dir}")
    print(f"🌐 API地址: {api_url}")
    print(f"⚡ 并发数: {max_workers}")

    # 检查目录是否存在
    if not os.path.exists(rules_dir):
        print(f"❌ 目录不存在: {rules_dir}")
        return

    # 查找所有JSON文件
    json_files = list(Path(rules_dir).glob("*.json"))
    if not json_files:
        print(f"❌ 未找到JSON文件在目录: {rules_dir}")
        return

    total_files = len(json_files)
    print(f"📊 发现 {total_files} 个规则文件")
    print()

    # 开始批量保存
    success_count = 0
    failed_rules = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(save_single_rule, str(json_file), api_url): json_file
            for json_file in json_files
        }

        # 处理完成的任务
        for future in as_completed(future_to_file):
            json_file = future_to_file[future]
            try:
                result = future.result()
                if result['success']:
                    success_count += 1
                else:
                    failed_rules.append(result)
            except Exception as e:
                failed_rules.append({
                    'rule_name': Path(json_file).stem.replace('rule_', ''),
                    'file_path': str(json_file),
                    'error': str(e)
                })

    # 输出统计结果
    print("\n" + "=" * 50)
    print("📊 保存结果统计")
    print(f"✅ 成功保存: {success_count}/{total_files}")
    print(f"❌ 保存失败: {len(failed_rules)}/{total_files}")

    if failed_rules:
        print("\n❌ 失败的规则:")
        for failed in failed_rules:
            print(f"   - {failed['rule_name']}: {failed.get('error', '未知错误')}")

    return success_count, failed_rules


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='批量保存规则到规则引擎')
    parser.add_argument('--rules-dir', '-d', default='generated_metrics_rules',
                       help='包含规则JSON文件的目录')
    parser.add_argument('--api-url', '-u', default='http://localhost:8081',
                       help='规则引擎API基础URL')
    parser.add_argument('--workers', '-w', type=int, default=2,
                       help='并发保存数（默认2，避免API过载）')

    args = parser.parse_args()

    success_count, failed_rules = save_rules_batch(
        rules_dir=args.rules_dir,
        api_url=args.api_url,
        max_workers=args.workers
    )

    if success_count > 0:
        print(f"\n🎉 批量保存完成！成功保存 {success_count} 个规则")
    else:
        print("\n❌ 批量保存失败！")
        exit(1)


if __name__ == "__main__":
    main()
