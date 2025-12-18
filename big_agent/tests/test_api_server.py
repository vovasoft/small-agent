"""
测试API服务器
"""

import requests
import time

def test_api_server():
    """测试API服务器"""
    base_url = "http://127.0.0.1:8000"

    print("测试API服务器...")

    # 等待服务器启动
    time.sleep(2)

    try:
        # 测试健康检查
        print("1. 测试健康检查...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   [SUCCESS] 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"   [ERROR] 健康检查失败: {response.status_code}")

        # 测试农业支出计算
        print("\n2. 测试农业支出计算...")
        expense_data = {
            "time_period": "2023",
            "region": "全国",
            "crop_type": "粮食作物"
        }
        response = requests.post(f"{base_url}/agriculture/expense-calculation", json=expense_data)
        if response.status_code == 200:
            print("   [SUCCESS] 支出计算成功")
            result = response.json()
            data = result.get("data", {})
            print(f"   总支出: {data.get('total_expense', 'N/A')}元")
            print(f"   置信度: {data.get('calculation_metadata', {}).get('confidence_level', 'N/A')}")
        else:
            print(f"   [ERROR] 支出计算失败: {response.status_code}")
            print(f"   错误: {response.text}")

        # 测试农业收入计算
        print("\n3. 测试农业收入计算...")
        income_data = {
            "time_period": "2023",
            "region": "全国",
            "crop_type": "粮食作物",
            "market_type": "both",
            "include_subsidies": True
        }
        response = requests.post(f"{base_url}/agriculture/income-calculation", json=income_data)
        if response.status_code == 200:
            print("   [SUCCESS] 收入计算成功")
            result = response.json()
            data = result.get("data", {})
            print(f"   总收入: {data.get('total_income', 'N/A')}元")
            print(f"   净利润率: {data.get('profitability_metrics', {}).get('net_profit_margin', 'N/A')}")
        else:
            print(f"   [ERROR] 收入计算失败: {response.status_code}")
            print(f"   错误: {response.text}")

        print("\n[SUCCESS] API服务器测试完成")

    except requests.exceptions.ConnectionError:
        print("[ERROR] 无法连接到API服务器，请确保服务器正在运行")
        print("运行: python mock_api_server.py")
    except Exception as e:
        print(f"[ERROR] 测试过程中发生异常: {str(e)}")

if __name__ == "__main__":
    test_api_server()
