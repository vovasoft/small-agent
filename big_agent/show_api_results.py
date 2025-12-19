"""
API结果查看工具
===============

此脚本用于查看保存在api_results文件夹中的所有API调用结果。

功能：
1. 列出所有API结果文件
2. 显示每个文件的摘要信息
3. 可以查看详细的API调用信息

使用方法：
python3 show_api_results.py
"""

import os
import json
from pathlib import Path
from datetime import datetime


def list_api_results():
    """列出所有API结果文件"""
    api_results_dir = Path("api_results")

    if not api_results_dir.exists():
        print("❌ api_results目录不存在")
        return []

    files = list(api_results_dir.glob("*.json"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # 按修改时间倒序

    return files


def show_file_summary(filepath, index):
    """显示文件摘要信息"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        call_id = data.get('call_id', 'unknown')
        agent = data.get('agent', 'unknown')
        success = data.get('success', False)
        duration = data.get('response', {}).get('duration', 0)
        timestamp = data.get('timestamp', '')

        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = timestamp[:19] if timestamp else 'unknown'

        status_icon = "✅" if success else "❌"
        print(f"{index:2d}. {status_icon} {call_id:<35} {agent:<20} {time_str} {duration:6.2f}s")
    except Exception as e:
        print(f"❌ 读取文件失败 {filepath.name}: {str(e)}")


def show_detailed_info(filepath):
    """显示详细的API调用信息"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\n📄 详细API调用信息 - {filepath.name}")
        print("=" * 60)

        # 基本信息
        print(f"调用ID: {data.get('call_id', 'unknown')}")
        print(f"时间戳: {data.get('timestamp', 'unknown')}")
        print(f"Agent: {data.get('agent', 'unknown')}")
        print(f"成功: {data.get('success', False)}")

        # 请求信息
        request = data.get('request', {})
        if data.get('agent') == 'IntentRecognitionAgent':
            print(f"模型: {data.get('model', 'unknown')}")
            prompt = request.get('prompt', '')
            print(f"提示词长度: {len(prompt)} 字符")
        elif data.get('agent') == 'MetricCalculationAgent':
            print(f"API端点: {data.get('api_endpoint', 'unknown')}")
            print(f"配置名: {data.get('config_name', 'unknown')}")
            print(f"HTTP方法: {request.get('method', 'unknown')}")

        # 响应信息
        response = data.get('response', {})
        duration = response.get('duration', 0)
        print(f"耗时: {duration:.2f}秒")
        if data.get('agent') == 'MetricCalculationAgent':
            status_code = response.get('status_code', 'unknown')
            print(f"HTTP状态码: {status_code}")

        print()

    except Exception as e:
        print(f"❌ 读取详细文件信息失败 {filepath.name}: {str(e)}")


def main():
    """主函数"""
    print("🚀 API结果查看工具")
    print("=" * 50)

    files = list_api_results()

    if not files:
        print("📂 api_results目录中没有找到API结果文件")
        return

    print(f"📊 找到 {len(files)} 个API结果文件:")
    print()

    # 显示文件列表
    for i, filepath in enumerate(files, 1):
        show_file_summary(filepath, i)

    print("\n" + "=" * 50)
    print("💡 提示：所有API调用结果已保存为JSON文件，可直接查看")
    print("\n📂 文件位置: api_results/ 目录")
    print("📄 文件格式: JSON")
    print("🏷️ 命名规则: ")
    print("   - 大模型API: api_mll_{序号}.json")
    print("   - 指标计算API: api_{配置名}_{时间戳}.json")

    print("\n👋 API结果查看完成！")


if __name__ == "__main__":
    main()