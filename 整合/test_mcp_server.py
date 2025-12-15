#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 数学服务器单元测试
"""
import unittest
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_math_server import calculate_expression, add, multiply


class TestMCPMathServer(unittest.TestCase):
    """测试MCP数学服务器的工具函数"""

    def test_add_function(self):
        """测试加法函数"""
        result = add(15.0, 27.0)
        self.assertEqual(result, "15.0 + 27.0 = 42.0")

        result = add(0, 0)
        self.assertEqual(result, "0.0 + 0.0 = 0.0")

        result = add(-5, 10)
        self.assertEqual(result, "-5.0 + 10.0 = 5.0")

    def test_multiply_function(self):
        """测试乘法函数"""
        result = multiply(8.0, 9.0)
        self.assertEqual(result, "8.0 × 9.0 = 72.0")

        result = multiply(0, 100)
        self.assertEqual(result, "0.0 × 100.0 = 0.0")

        result = multiply(-3, 4)
        self.assertEqual(result, "-3.0 × 4.0 = -12.0")

    def test_calculate_expression_valid(self):
        """测试有效的数学表达式"""
        test_cases = [
            ("15 + 27", "表达式 '15 + 27' 的计算结果是: 42"),
            ("8 * 9", "表达式 '8 * 9' 的计算结果是: 72"),
            ("(20 - 5) * 3 / 2", "表达式 '(20 - 5) * 3 / 2' 的计算结果是: 22.5"),
            ("10 + 5 * 2", "表达式 '10 + 5 * 2' 的计算结果是: 20"),
            ("100 / 4", "表达式 '100 / 4' 的计算结果是: 25.0"),
        ]

        for expression, expected in test_cases:
            with self.subTest(expression=expression):
                result = calculate_expression(expression)
                self.assertEqual(result, expected)

    def test_calculate_expression_invalid(self):
        """测试无效的数学表达式"""
        invalid_cases = [
            "import os",
            "eval('1+1')",
            "exec('print(1)')",
            "__import__('os')",
            "open('/etc/passwd')",
            "1 + 'string'",  # 类型错误
            "a + b",  # 未定义变量
        ]

        for expression in invalid_cases:
            with self.subTest(expression=expression):
                result = calculate_expression(expression)
                self.assertTrue(
                    result.startswith("计算表达式时出错:") or
                    result.startswith("表达式包含不允许的字符:") or
                    result.startswith("未知错误:")
                )

    def test_calculate_expression_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            ("", "表达式不能为空"),
            ("   ", "表达式不能为空"),
            ("1.5 + 2.5", "表达式 '1.5 + 2.5' 的计算结果是: 4.0"),
            ("-10 + 5", "表达式 '-10 + 5' 的计算结果是: -5"),
        ]

        for expression, expected_start in edge_cases:
            with self.subTest(expression=expression):
                result = calculate_expression(expression)
                self.assertTrue(result.startswith(expected_start))


if __name__ == '__main__':
    print("开始运行MCP数学服务器单元测试...")
    unittest.main(verbosity=2)
