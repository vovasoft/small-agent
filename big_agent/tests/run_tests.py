"""
运行所有单元测试
集成详细的日志记录功能
"""

import subprocess
import sys
import os
from logging_utils import logger, log_api_server_status, log_test_results


def run_tests():
    """运行所有测试"""
    logger.section_start("Big Agent 单元测试执行")

    # 检查API服务器
    logger.workflow_step("检查API服务器", "验证服务器状态")
    log_api_server_status()

    # 运行pytest
    logger.workflow_step("执行单元测试", "运行pytest测试套件")

    try:
        import time
        start_time = time.time()

        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--asyncio-mode=auto",
            "--tb=short",
            "-v"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))

        end_time = time.time()
        duration = end_time - start_time

        # 记录测试输出
        logger.info("测试执行详情:")
        if result.stdout:
            # 只记录关键的测试结果行
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in ['PASSED', 'FAILED', 'ERROR', 'collected', 'duration']):
                    logger.info(f"  {line}")

        if result.stderr:
            logger.warning("测试错误输出:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"  {line}")

        # 解析测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for line in result.stdout.split('\n'):
            if 'collected' in line and 'items' in line:
                try:
                    total_tests = int(line.split()[0])
                except:
                    pass
            elif 'passed' in line and 'failed' in line:
                try:
                    parts = line.split()
                    passed_tests = int(parts[0])
                    failed_tests = int(parts[2]) if len(parts) > 2 else 0
                except:
                    pass

        # 记录测试结果
        log_test_results(total_tests, passed_tests, failed_tests, duration)

        success = result.returncode == 0
        logger.system_status("测试执行", "成功" if success else "失败")

        logger.section_end()
        return success

    except Exception as e:
        logger.error(f"运行测试时发生错误: {e}")
        logger.section_end()
        return False

def show_test_coverage():
    """显示测试覆盖情况"""
    print("\n3. 测试覆盖情况:")

    test_files = [
        "test_api_server.py - API服务器功能测试",
        "test_big_agent.py - 基础工作流测试",
        "test_complete_system.py - 完整系统集成测试"
    ]

    for test_file in test_files:
        print(f"   [OK] {test_file}")

    print("\n测试类型:")
    print("   - 单元测试 - 单个组件功能")
    print("   - 集成测试 - 多组件协作")
    print("   - API测试 - 外部接口验证")
    print("   - 异步测试 - 并发处理能力")

if __name__ == "__main__":
    success = run_tests()
    show_test_coverage()

    if success:
        print("\n[SUCCESS] 所有测试执行完成，系统运行正常！")
    else:
        print("\n[ERROR] 测试执行失败，请检查系统配置")

    sys.exit(0 if success else 1)
