# Big Agent - 多Agent LangGraph框架

基于LangGraph的智能多Agent系统，包含意图识别、指标计算和知识沉淀三个核心Agent。

## 📋 项目特性

- ✅ **代码质量**: 详细的文档注释和类型注解
- ✅ **模块化设计**: 清晰的代码结构和职责分离
- ✅ **鲁棒性测试**: 包含干扰项的JSON配置文件测试
- ✅ **日志追踪**: 完整的Agent交互日志记录
- ✅ **配置驱动**: 灵活的JSON配置文件系统

## 功能特性

- **意图识别Agent**: 分析用户输入，识别意图并选择合适的指标计算配置
- **远程指标计算Agent**: 根据意图调用相应的API进行指标计算
- **知识沉淀Agent**: 收集整个流程信息，生成结构化知识文档
- **完整的LangGraph工作流**: 协调各个Agent的执行流程

## 安装和配置

### 1. 创建Conda环境

```bash
conda create -n big_agent python=3.10 -y
conda activate big_agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install langgraph langchain langchain-community langchain-openai python-dotenv requests pandas fastapi uvicorn
```

### 3. 配置环境变量

创建 `.env` 文件并设置DeepSeek API密钥：

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 4. 启动模拟API服务器

```bash
# 在后台启动API服务器（用于测试）
python mock_api_server.py

# API文档访问: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```

## 项目结构

```
big_agent/
├── agents/                          # Agent模块
│   ├── intent_recognition_agent.py # 意图识别Agent
│   ├── metric_calculation_agent.py # 指标计算Agent
│   └── knowledge_precipitation_agent.py # 知识沉淀Agent
├── jsonFiles/                      # 指标计算配置文件
│   ├── 农业总支出指标计算.json
│   └── 农业总收入指标计算.json
├── knowledge_base/                 # 知识库存储目录
├── config.py                       # 配置文件
├── complete_agent_flow.py         # 主工作流
├── test_big_agent.py              # 测试脚本
└── README.md                      # 说明文档
```

## 使用方法

### 快速开始

#### 1. 运行完整演示

```bash
python run_complete_demo.py
```

这个脚本会自动启动模拟API服务器并运行完整演示，所有日志会记录到`logs/`文件夹。

#### 2. 查看系统日志

```bash
# 查看最近的日志
python view_logs.py

# 查看最近50行日志
python view_logs.py 50

# 查看日志统计信息
python view_logs.py stats
```

#### 3. 运行单元测试

```bash
# 使用测试运行脚本（推荐）
python tests/run_tests.py

# 或直接使用pytest
python -m pytest tests/ --asyncio-mode=auto -v
```

#### 4. 基本使用

```python
import asyncio
from complete_agent_flow import run_complete_agent_flow

# 设置API密钥
api_key = "your_deepseek_api_key"

# 准备数据
data = [
    {"field1": "value1", "field2": "value2"},
    # ... 更多数据
]

# 运行工作流
async def main():
    result = await run_complete_agent_flow("生成农业指标分析报告", data, api_key)
    print(result)

asyncio.run(main())
```

#### 5. 其他功能演示

```bash
# 系统运行日志分析
python system_run_log.py

# 功能演示
python demo.py

# API服务器单独测试
python test_api_server.py

# 系统状态检查
python status_check.py
```

## 配置文件说明

### 指标计算配置 (jsonFiles/*.json)

每个配置文件包含以下字段：

- `name`: 配置名称
- `description`: 配置描述
- `api_config`: API调用配置
  - `method`: HTTP方法
  - `url`: API地址
  - `headers`: 请求头
  - `timeout`: 超时时间
- `param_mapping`: 参数映射
- `input_schema`: 输入数据结构
- `output_schema`: 输出数据结构
- `calculation_logic`: 计算逻辑
- `data_sources`: 数据源
- `validation_rules`: 验证规则

### 示例配置

农业总支出指标计算配置示例：

```json
{
  "name": "农业总支出指标计算",
  "description": "计算农业领域的各项支出指标",
  "api_config": {
    "method": "POST",
    "url": "https://api.example.com/agriculture/expense-calculation",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer YOUR_API_TOKEN"
    }
  },
  "param_mapping": {
    "time_period": "time_period",
    "region": "region"
  }
}
```

## 工作流流程

1. **意图识别**: 分析用户输入，确定意图类别和目标配置
2. **指标计算**: 调用相应的API进行指标计算
3. **知识沉淀**: 整理流程信息，生成知识文档
4. **错误处理**: 处理各环节的异常情况

## API服务器

系统包含一个完整的FastAPI模拟服务器 (`mock_api_server.py`)，用于测试和演示。

### 可用端点

- `GET /` - API根路径和信息
- `GET /health` - 健康检查
- `POST /agriculture/expense-calculation` - 农业支出指标计算
- `POST /agriculture/income-calculation` - 农业收入指标计算

### 请求示例

```bash
# 支出计算
curl -X POST "http://localhost:8000/agriculture/expense-calculation" \
     -H "Content-Type: application/json" \
     -d '{
       "time_period": "2023",
       "region": "全国",
       "crop_type": "粮食作物"
     }'

# 收入计算
curl -X POST "http://localhost:8000/agriculture/income-calculation" \
     -H "Content-Type: application/json" \
     -d '{
       "time_period": "2023",
       "region": "全国",
       "crop_type": "粮食作物",
       "include_subsidies": true
     }'
```

## 扩展开发

### 添加新的指标计算配置

1. 在 `jsonFiles/` 目录下创建新的JSON配置文件
2. 定义API接口和参数映射
3. 系统会自动识别并加载新配置

### 自定义Agent行为

修改相应Agent类的实现：

- `IntentRecognitionAgent`: 自定义意图识别逻辑
- `MetricCalculationAgent`: 自定义API调用逻辑
- `KnowledgePrecipitationAgent`: 自定义知识沉淀逻辑

### 添加新的工作流节点

在 `complete_agent_flow.py` 中：

1. 定义新的节点函数
2. 在工作流图中添加节点
3. 配置边的连接关系

### 扩展API服务器

在 `mock_api_server.py` 中添加新的端点和处理逻辑：

```python
@app.post("/your/new/endpoint")
async def new_calculation(request: YourRequestModel):
    # 实现新的计算逻辑
    return {"success": True, "data": result}
```

## 注意事项

- 确保DeepSeek API密钥有效且有足够的使用额度
- API调用可能产生费用，请注意成本控制
- 知识文档会持续积累，定期清理不需要的文档
- 生产环境使用时请配置适当的日志和监控

## 许可证

本项目采用MIT许可证。
