# MCP + LangChain 智能体集成演示

这是一个完整的 MCP (Model Context Protocol) 与 LangChain 智能体的集成演示项目。

## 项目结构

```
整合/
├── langchain_mcp_agent.py    # 主要的智能体实现
├── mcp_math_server.py       # MCP数学工具服务器
├── run_test.py              # 集成测试脚本
├── debug_test.py            # 调试和开发测试脚本
├── test_mcp_server.py      # 单元测试
├── CONFIG.md                # 配置说明
├── requirements.txt         # Python依赖
└── README.md               # 本文件
```

## 功能特性

### MCP 数学工具服务器
- **add(a, b)**: 两个数字相加
- **multiply(a, b)**: 两个数字相乘
- **calculate_expression(expr)**: 计算数学表达式（安全版本）

### LangChain 智能体
- 使用 DeepSeek 语言模型
- 集成 MCP 工具
- 支持复杂的数学推理和计算

## 安装和设置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置环境变量
```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
```

### 3. 获取 API 密钥
访问 [DeepSeek 官网](https://platform.deepseek.com/) 注册并获取 API 密钥。

## 使用方法

### 运行集成测试
```bash
python3 run_test.py
```

### 运行单元测试
```bash
python3 test_mcp_server.py
```

### 运行调试测试
```bash
python3 debug_test.py
```

## 测试用例

智能体可以处理以下类型的查询：

1. **简单加法**: "Calculate 15 plus 27"
2. **乘法**: "What is 8 multiplied by 9?"
3. **复杂计算**: "First calculate 3 plus 5, then multiply the result by 12"
4. **表达式计算**: "What is the result of (20 - 5) * 3 / 2?"

## 安全特性

- MCP 服务器中的表达式计算经过安全检查
- 只允许基本的数学运算（+、-、*、/、括号）
- 禁止使用危险的关键字和函数
- API 密钥通过环境变量设置，不在代码中硬编码

## 技术实现

### 核心问题解决

1. **工具格式兼容性**: LangChain-MCP-Adapter 返回字典列表格式，但 LangGraph 期望字符串。通过创建工具包装器解决。

2. **API 密钥安全**: 移除硬编码密钥，使用环境变量。

3. **表达式安全计算**: 使用 AST 解析和受限环境进行安全的数学表达式计算。

### 架构设计

```
用户查询 → LangChain 智能体 → MCP 客户端 → MCP 数学服务器
                                      ↓
工具调用结果 ← 工具包装器 ← 原始 MCP 工具返回格式
```

## 开发和调试

项目包含完整的调试工具和测试套件：

- **debug_test.py**: 逐步调试 MCP 和智能体集成
- **test_mcp_server.py**: MCP 服务器的单元测试
- **run_test.py**: 端到端集成测试

## 依赖版本

- langchain-mcp-adapters: 0.2.1
- langchain-openai: 1.1.3
- langgraph: 1.0.5
- mcp: 1.24.0
- Python: 3.12+

## 许可证

本项目仅用于学习和演示目的。
