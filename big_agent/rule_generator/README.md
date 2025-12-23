# 规则生成器 (Rule Generator)

这个目录包含了用于生成数据处理规则的脚本和工具。

## 文件说明

- `rule_generator.py`: 主要的规则生成脚本
- `test_rule_generator.py`: 规则生成器功能测试脚本
- `README.md`: 使用说明文档

## 功能特性

1. **大模型规则生成**: 使用DeepSeek大模型根据自然语言描述自动生成规则内容
2. **API集成**: 自动调用规则引擎API保存生成的决策知识
3. **灵活配置**: 支持自定义规则参数和描述

## 使用方法

### 环境准备

确保已配置好以下环境变量：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `DEEPSEEK_BASE_URL`: DeepSeek API基础URL（可选，默认使用官方地址）

### 基本用法

```python
from rule_generator import RuleGenerator

# 初始化生成器
generator = RuleGenerator(api_key="your_deepseek_api_key")

# 创建决策知识payload（只需要三个参数）
payload = generator.create_decision_knowledge_payload(
    id="demo-黑色金属-0302",
    name="demo-黑色金属-0302",
    ruleDescription="筛选出业务类型为'支出/经营/经营支出（黑色金属）'的交易记录，按交易对手分组，计算总支出金额，降序排序取前3名"
)

# 保存到规则引擎
success = generator.save_decision_knowledge(payload)
```

### 命令行运行

```bash
cd rule_generator
python rule_generator.py
```

这将运行一个示例，生成黑色金属经营支出TOP3的规则。

### 运行测试

```bash
cd rule_generator
python test_rule_generator.py
```

这将运行完整的功能测试，包括规则内容生成和payload构建验证。

### 批量处理指标

支持从CSV或Excel文件批量导入指标定义并生成规则：

```bash
# 基本批量处理（推荐）
cd rule_generator
python test_rule_generator.py --batch metrics_definitions.csv

# 自定义并发数
python test_rule_generator.py --batch metrics_definitions.csv --workers 2

# 跳过API保存（只生成JSON文件，性能更好）
python test_rule_generator.py --batch metrics_definitions.csv --skip-api
```

#### CSV文件格式

CSV文件必须包含以下两列：
- `指标名称`: 指标的名称
- `指标描述`: 指标的详细描述

示例：
```csv
指标名称,指标描述
总收入,统计期内全部收入金额 其中收入字段是tx_direction 金额字段是tx_amount
收入笔数,流水数据中类型为收入的总数 其中收入字段是tx_direction
```

#### 性能优化

- **并发处理**: 默认使用3个并发线程，可通过 `--workers` 参数调整
- **跳过API保存**: 使用 `--skip-api` 跳过规则引擎API调用，大幅提升性能
- **智能限流**: 避免过多并发导致API限流

#### 性能对比

- **串行处理**: 每个指标约3-5秒，总耗时随指标数量线性增长
- **并发处理**: 3个并发时，理论加速比约3倍
- **跳过API保存**: 可节省额外的网络请求时间

### 基本用法

```python
from rule_generator.generator import RuleGenerator

# 初始化生成器
generator = RuleGenerator(api_key="your_deepseek_api_key")

# 创建payload（只需要三个参数）
payload = generator.create_decision_knowledge_payload(
    id="your-id",
    name="your-name",
    ruleDescription="用自然语言描述你想要的规则逻辑"
)

# 保存到规则引擎
success = generator.save_decision_knowledge(payload)
```

## 规则内容格式

生成的规则内容遵循以下结构：

```json
[
  {
    "type": "CONDITIONAL|GROUP_BY|SORT|...",
    "sourceField": "输入字段名",
    "resultField": "输出字段名",
    // 其他类型特定参数...
  }
]
```

### 支持的操作类型

- `FILTER`: 数据筛选
- `CONDITIONAL`: 条件过滤
- `AGGREGATE`: 数据聚合
- `GROUP_BY`: 分组操作
- `SORT`: 排序操作
- `ADDTAG`: 添加标签

### 支持的操作符

- `EQUALS`: 等于
- `NOT_EQUALS`: 不等于
- `CONTAINS`: 包含
- `GREATER_THAN`: 大于
- `LESS_THAN`: 小于
- `GREATER_THAN_OR_EQUAL`: 大于等于
- `LESS_THAN_OR_EQUAL`: 小于等于
- `REGEX_MATCH`: 正则匹配

## API接口

脚本调用规则引擎的 `/api/rules/saveDecisionKnowledge` 接口，包含以下数据结构：

### decisionKnowledge
- `id`: 决策知识唯一标识
- `name`: 决策知识名称
- `zoneId`: 区域ID
- `systemId`: 系统ID
- `treeId`: 树ID
- `factorDescription`: 因子描述
- `businessTags`: 业务标签
- `version`: 版本号
- `supportKnowledgeRefs`: 支持的知识引用
- `publisher`: 发布者
- `status`: 状态
- `applicationStatus`: 应用状态
- `operator`: 操作者

### ruleDefinition
- `id`: 规则唯一标识
- `name`: 规则名称
- `ruleType`: 规则类型
- `ruleDescription`: 规则描述
- `inputSchema`: 输入模式
- `outputSchema`: 输出模式
- `ruleContent`: 规则内容（大模型生成）
- `priority`: 优先级
- `enabled`: 是否启用
- `version`: 版本号
- `status`: 状态
- `operator`: 操作者
- `isDeleted`: 删除标记

## 注意事项

1. 确保规则引擎服务在 `http://localhost:8081` 运行
2. 确保DeepSeek API密钥正确配置
3. 规则内容由大模型生成，请检查生成结果的准确性
4. 网络超时时间设置为30秒，如需调整请修改代码

## 故障排除

- **API密钥错误**: 检查环境变量 `DEEPSEEK_API_KEY` 是否正确设置
- **网络连接失败**: 检查网络连接和规则引擎服务状态
- **规则生成失败**: 检查自然语言描述是否清晰明确
- **API调用失败**: 查看控制台输出的错误信息和HTTP状态码
