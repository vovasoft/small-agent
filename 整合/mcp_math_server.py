# mcp_math_server.py
import sys
import json

# 设置标准输出的编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from mcp.server.fastmcp import FastMCP

# 创建 FastMCP 服务器实例
mcp = FastMCP("MathTools")

@mcp.tool()
def add(a: float, b: float) -> str:
    """将两个数字相加。"""
    result = a + b
    return f"{a:.1f} + {b:.1f} = {result:.1f}"

@mcp.tool()
def multiply(a: float, b: float) -> str:
    """将两个数字相乘。"""
    result = a * b
    return f"{a:.1f} × {b:.1f} = {result:.1f}"

@mcp.tool()
def calculate_expression(expression: str) -> str:
    """计算一个简单的数学表达式。

    支持：数字、加减乘除、括号、小数点
    不支持：变量、函数调用、字符串操作等
    """
    try:
        import re
        import ast
        import operator

        # 检查表达式安全性 - 只允许数字、运算符、括号、小数点、空格
        if not expression.strip():
            return "表达式不能为空"

        if not re.match(r'^[0-9+\-*/().\s]+$', expression):
            return f"表达式包含不允许的字符: {expression}"

        # 使用ast.literal_eval进行更安全的计算（但literal_eval不支持运算）
        # 所以我们使用一个简单的递归求值器
        def safe_eval(expr):
            # 移除所有空格
            expr = expr.replace(' ', '')

            # 基本的安全检查
            if any(char in expr for char in ['__', 'import', 'exec', 'eval', 'open', 'file']):
                raise ValueError("包含不允许的操作")

            # 使用更简单但仍然安全的方法进行计算
            # 通过正则表达式预检查，然后使用受限的eval
            try:
                # 再次检查安全性（虽然前面已经检查过）
                if any(keyword in expr.lower() for keyword in ['import', 'exec', 'eval', 'open', '__']):
                    raise ValueError("包含危险关键字")

                # 使用非常受限的环境进行计算
                safe_dict = {
                    "__builtins__": {},
                    # 不添加任何内置函数，只允许基本的数学运算
                }

                # 编译并执行
                code = compile(expr, '<string>', 'eval')
                return eval(code, safe_dict)

            except SyntaxError as e:
                raise ValueError(f"语法错误: {e}")
            except NameError as e:
                raise ValueError(f"不允许使用变量或函数: {e}")
            except Exception as e:
                raise ValueError(f"计算错误: {e}")

        result = safe_eval(expression)
        return f"表达式 '{expression}' 的计算结果是: {result}"

    except ValueError as e:
        return f"计算表达式时出错: {str(e)}"
    except Exception as e:
        return f"未知错误: {str(e)}"

if __name__ == "__main__":
    print("🚀 MCP 数学工具服务器已启动 (UTF-8 编码)", file=sys.stderr)
    mcp.run(transport="stdio")
