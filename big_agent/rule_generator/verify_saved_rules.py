#!/usr/bin/env python3
"""
验证已保存的规则
==============

查询规则引擎中已保存的规则信息
"""

import requests
import json


def query_saved_rules(api_url="http://localhost:8081"):
    """
    查询已保存的规则
    """
    print("🔍 查询已保存的规则")
    print("=" * 40)

    try:
        # 构建查询URL（根据实际API接口调整）
        url = f"{api_url}/api/rules/listDecisionKnowledge"

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanRuntime-ApipostRuntime/1.1.0'
        }

        # 发送查询请求
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ 查询成功")

                # 尝试解析返回的数据
                if isinstance(result, dict) and 'data' in result:
                    rules = result['data']
                elif isinstance(result, list):
                    rules = result
                else:
                    rules = result

                # 过滤出我们刚保存的metric规则
                metric_rules = []
                if isinstance(rules, list):
                    for rule in rules:
                        if isinstance(rule, dict) and rule.get('id', '').startswith('metric-'):
                            metric_rules.append({
                                'id': rule.get('id'),
                                'name': rule.get('name'),
                                'status': rule.get('status'),
                                'applicationStatus': rule.get('applicationStatus')
                            })

                print(f"📊 找到 {len(metric_rules)} 个metric相关规则:")
                for rule in metric_rules:
                    status_text = "✅ 已发布" if rule.get('status') == 2 else "⏳ 草稿"
                    app_status_text = "✅ 已启用" if rule.get('applicationStatus') == 2 else "⏸️ 未启用"
                    print(f"   - {rule['name']} ({rule['id']}) - {status_text} {app_status_text}")

                return len(metric_rules)

            except json.JSONDecodeError:
                print(f"📄 返回原始内容: {response.text[:200]}...")
                return 0
        else:
            print(f"❌ 查询失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return 0

    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return 0


def test_single_rule(rule_id, api_url="http://localhost:8081"):
    """
    测试单个规则
    """
    print(f"\n🧪 测试规则: {rule_id}")

    try:
        # 构建测试URL
        url = f"{api_url}/api/rules/executeRule"

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanRuntime-ApipostRuntime/1.1.0'
        }

        # 构建测试payload
        payload = {
            "ruleId": rule_id,
            "inputData": {
                "transactions": [
                    {
                        "txId": "TX202301050001",
                        "txDate": "2023-01-05",
                        "txAmount": 1000,
                        "txDirection": "收入",
                        "txSummary": "销售收入",
                        "txCounterparty": "客户A"
                    }
                ]
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            print(f"✅ 规则 {rule_id} 执行成功")
            return True
        else:
            print(f"⚠️ 规则 {rule_id} 执行失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 规则 {rule_id} 测试异常: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='验证已保存的规则')
    parser.add_argument('--api-url', '-u', default='http://localhost:8081',
                       help='规则引擎API基础URL')
    parser.add_argument('--test-rules', action='store_true',
                       help='测试规则执行')

    args = parser.parse_args()

    # 查询已保存的规则
    rule_count = query_saved_rules(args.api_url)

    if rule_count > 0 and args.test_rules:
        print("\n🧪 开始测试规则执行...")
        # 这里可以添加具体的规则ID进行测试
        test_rule_ids = [
            "metric-总收入",
            "metric-总支出"
        ]

        for rule_id in test_rule_ids:
            test_single_rule(rule_id, args.api_url)

    print(f"\n🎉 验证完成！共发现 {rule_count} 个已保存的规则")


if __name__ == "__main__":
    main()
