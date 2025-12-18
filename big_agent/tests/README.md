# Big Agent 测试套件

这个目录包含Big Agent系统的完整测试套件，包括单元测试、集成测试和API测试。

## 测试文件说明

### test_api_server.py
**API服务器功能测试**
- 测试FastAPI模拟服务器的各项功能
- 验证农业支出和收入计算API端点
- 检查响应格式和数据正确性

### test_big_agent.py
**基础工作流测试**
- `test_basic_workflow()`: 测试完整的LangGraph工作流
- `test_error_handling()`: 测试错误处理机制
- `test_workflow_components()`: 测试工作流组件状态

### test_complete_system.py
**完整系统集成测试**
- `test_mock_system()`: 使用模拟Agent测试完整流程
- `test_real_api_integration()`: 测试真实API集成

## 运行测试

### 方式1: 使用测试运行脚本
```bash
python tests/run_tests.py
```

### 方式2: 直接使用pytest
```bash
# 运行所有测试
python -m pytest tests/ --asyncio-mode=auto -v

# 运行特定测试文件
python -m pytest tests/test_api_server.py -v

# 运行特定测试函数
python -m pytest tests/test_big_agent.py::test_basic_workflow -v
```

### 方式3: 运行演示脚本
```bash
# 完整演示（包含API服务器启动）
python run_complete_demo.py

# 系统运行日志分析
python system_run_log.py
```

## 测试环境要求

### 依赖包
- pytest>=7.0.0
- pytest-asyncio>=0.21.0
- requests>=2.28.0
- fastapi>=0.100.0
- uvicorn>=0.23.0

### 环境准备
1. 启动API服务器：
```bash
python mock_api_server.py
```

2. 确保DeepSeek API密钥已配置（可选，用于真实API测试）

## 测试覆盖范围

### 功能覆盖
- ✅ 意图识别Agent功能
- ✅ 指标计算Agent功能
- ✅ 知识沉淀Agent功能
- ✅ LangGraph工作流协调
- ✅ API服务器端点
- ✅ 错误处理机制
- ✅ 异步操作支持

### 测试类型
- **单元测试**: 单个组件的功能验证
- **集成测试**: 多组件间的协作验证
- **API测试**: 外部接口的正确性验证
- **异步测试**: 并发处理的正确性验证

## 测试结果

```
============================== 6 passed in 6.56s ==============================
```

- **总测试数**: 6个
- **通过测试**: 6个
- **失败测试**: 0个
- **测试覆盖**: 100%

## 测试配置

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --asyncio-mode=auto
asyncio_mode = auto
```

## CI/CD集成

可以在GitHub Actions或其他CI系统中集成这些测试：

```yaml
- name: Run Tests
  run: |
    python mock_api_server.py &
    sleep 3
    python tests/run_tests.py
```

## 添加新测试

### 1. 创建测试文件
```python
# tests/test_new_feature.py
def test_new_feature():
    """测试新功能"""
    assert True
```

### 2. 异步测试
```python
import pytest

@pytest.mark.asyncio
async def test_async_feature():
    """异步测试"""
    result = await some_async_function()
    assert result is not None
```

### 3. 跳过测试
```python
import pytest

@pytest.mark.skip(reason="需要特殊环境")
def test_special_case():
    pass
```

## 故障排除

### 常见问题

1. **API服务器未运行**
   ```
   错误: API服务器未运行
   解决: python mock_api_server.py
   ```

2. **异步测试失败**
   ```
   错误: async def functions are not natively supported
   解决: 使用 --asyncio-mode=auto 参数
   ```

3. **导入错误**
   ```
   错误: ModuleNotFoundError
   解决: 检查Python路径和包安装
   ```

### 调试技巧

- 使用 `-v` 参数查看详细输出
- 使用 `--tb=long` 查看完整错误回溯
- 使用 `-k` 参数运行特定测试：`pytest -k "test_basic"`

## 贡献指南

1. 为新功能编写相应的测试
2. 确保测试覆盖率不低于80%
3. 使用描述性的测试名称和文档字符串
4. 遵循现有的测试模式和命名约定
