# 流水分析Agent POC简要说明

## 项目概述

这是一个基于多智能体架构的银行流水分析POC（Proof of Concept）项目，实现了从用户需求到完整分析报告的自动化生成流程。

**核心目标：**
- 验证多智能体协作的可行性
- 实现银行流水数据的智能化分析
- 提供标准化的分析报告生成流程

**技术栈：**
- LangGraph: 工作流编排
- LangChain: LLM集成
- Pydantic: 数据验证
- 外部API: 计算服务集成

## 运行结果（日志截图）

### 1.指标计算通过codeagent

```bash
🚀 执行CompleteAgentFlow (No Rules Engine) 系统测试
============================================================
📊 测试数据: 1 条记录
🚀 启动完整智能体工作流...
问题：执行流水分析任务
数据条数：1
计算模式：标准模式
🧠 正在执行规划分析...
========================================
[AGENT] PlanningAgent (规划Agent)
[MODEL_INPUT] PlanningAgent:
[CONTEXT] 基于当前状态做出规划决策
Question: 执行流水分析任务
Status info: 当前状态评估：
- 规划步骤: 0
- 大纲版本: 0
- 大纲草稿存在: False
- 指标需求总数: 0
- 已计算指标数: 0
- 指标覆盖率: 0.00%
- 待计算指标数: 0
- 有效待计算指标数: 0
- 失败尝试记录: {}

建议下一步: 计算指标
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_6.32.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "generate_outline", "reasoning": "大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成或无效时，应选择generate_outline。", "next_actions": ["生成报告大纲，明确分析维度、指标需求和报告结构"], "metrics_to_compute": [], "priority_metrics": [], "additional_requirements": {"raw_content": "用户需求为'执行流水分析任务'，较为宽泛。建议在生成大纲前，可进一步明确分析范围（如特定业务板块、时间周期、关键分析维度等），但当前状态满足首先生成大纲的条件。"}}
========================================

🧠 规划决策：generate_outline
   推理：大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成或无效时，应选择generate_outline。...
✅ 规划决策完成：generate_outline

🔍 [路由决策] 步骤=1, 大纲=False, 指标需求=0
→ 路由到 outline_generator（生成大纲）
📝 正在生成报告大纲...
📝 开始生成报告大纲（最多重试 5 次）...
   尝试 1/5...
========================================
[AGENT] OutlineGeneratorAgent (大纲生成Agent)
[MODEL_INPUT] OutlineGeneratorAgent:
[CONTEXT] 基于用户需求和数据样本生成报告大纲
Question: 执行流水分析任务
Sample data count: 1
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_大纲生成_36.69.json
[MODEL_OUTPUT] OutlineGeneratorAgent: {"report_title": "黑色金属与农业行业银行流水经营分析报告", "sections": [{"section_id": "sec_1", "title": "黑色金属行业经营状况分析", "description": "本部分聚焦黑色金属行业，通过分析其总经营收入、总经营支出以及核心交易对手的收支排名，全面评估该行业的资金流动规模、主要合作伙伴及经营健康度。", "metrics_needed": ["black_metal_total_income", "black_metal_total_expense", "black_metal_income_top3", "black_metal_expense_top3"]}, {"section_id": "sec_2", "title": "农业行业经营状况分析", "description": "本部分聚焦农业行业，通过分析其总经营收入、总经营支出以及核心交易对手的收支排名，全面评估该行业的资金流动规模、主要合作伙伴及经营健康度。", "metrics_needed": ["agriculture_total_income", "agriculture_total_expense", "agriculture_income_top3", "agriculture_expense_top3"]}, {"section_id": "sec_3", "title": "跨行业对比与综合评估", "description": "本部分将黑色金属与农业两个行业的经营数据进行横向对比，分析其收入支出结构、交易对手集中度等差异，并基于此提供综合性的经营评估与风险提示。", "metrics_needed": ["black_metal_total_income", "black_metal_total_expense", "agriculture_total_income", "agriculture_total_expense", "black_metal_income_top3", "black_metal_expense_top3", "agriculture_income_top3", "agriculture_expense_top3"]}], "global_metrics": [{"metric_id": "black_metal_income_top3", "metric_name": "黑色金属-交易对手收入排名TOP3", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘收入’的记录，按交易对手分组汇总收入金额，并按汇总金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "black_metal_expense_top3", "metric_name": "黑色金属-交易对手支出排名TOP3", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘支出’的记录，按交易对手分组汇总支出金额，并按汇总金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "black_metal_total_income", "metric_name": "黑色金属-总经营收入", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘收入’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}, {"metric_id": "black_metal_total_expense", "metric_name": "黑色金属-总经营支出", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘支出’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}, {"metric_id": "agriculture_income_top3", "metric_name": "农业-交易对手收入排名TOP3", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘收入’的记录，按交易对手分组汇总收入金额，并按汇总金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "agriculture_expense_top3", "metric_name": "农业-交易对手支出排名TOP3", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘支出’的记录，按交易对手分组汇总支出金额，并按汇总金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "agriculture_total_income", "metric_name": "农业-总经营收入", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘收入’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}, {"metric_id": "agriculture_total_expense", "metric_name": "农业-总经营支出", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘支出’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}]}
========================================
.2f

📝 大纲生成成功：
   标题：黑色金属与农业行业银行流水经营分析报告
   章节数：3
   指标数：8
✅ 大纲生成完成：黑色金属与农业行业银行流水经营分析报告
   包含 3 个章节，8 个指标需求
🧠 正在执行规划分析...
========================================
[AGENT] PlanningAgent (规划Agent)
[MODEL_INPUT] PlanningAgent:
[CONTEXT] 基于当前状态做出规划决策
Question: 执行流水分析任务
Status info: 当前状态评估：
- 规划步骤: 1
- 大纲版本: 1
- 大纲草稿存在: True
- 指标需求总数: 8
- 已计算指标数: 0
- 指标覆盖率: 0.00%
- 待计算指标数: 8
- 有效待计算指标数: 8
- 失败尝试记录: {}

建议下一步: 计算指标
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_7.61.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "compute_metrics", "reasoning": "大纲草稿已存在（outline_draft存在），但指标覆盖率仅为0.00%（0/8），远低于80%的阈值。需要立即开始计算指标以满足报告生成要求。", "next_actions": ["调用指标计算服务处理待计算指标"], "metrics_to_compute": ["black_metal_income_top3", "black_metal_expense_top3", "black_metal_total_income", "black_metal_total_expense", "agriculture_income_top3", "agriculture_expense_top3", "agriculture_total_income", "agriculture_total_expense"], "priority_metrics": ["black_metal_income_top3", "black_metal_expense_top3", "agriculture_income_top3"], "additional_requirements": null}
========================================

🧠 规划决策：compute_metrics
   推理：大纲草稿已存在（outline_draft存在），但指标覆盖率仅为0.00%（0/8），远低于80%的阈值。需要立即开始计算指标以满足报告生成要求。...
   待计算指标：['black_metal_income_top3', 'black_metal_expense_top3', 'black_metal_total_income', 'black_metal_total_expense', 'agriculture_income_top3', 'agriculture_expense_top3', 'agriculture_total_income', 'agriculture_total_expense']
✅ 规划决策完成：compute_metrics

🔍 [路由决策] 步骤=2, 大纲=True, 指标需求=8
  指标覆盖率 = 0.00%
→ 路由到 metric_calculator（计算指标，覆盖率=0.00%）
🧮 正在执行传统引擎指标计算...
🧮 计算指标: black_metal_income_top3 - 黑色金属-交易对手收入排名TOP3
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-黑色金属-交易对手收入排名TOP3)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-黑色金属-交易对手收入排名TOP3_47.89.json
✅ 指标 black_metal_income_top3 计算成功
🧮 计算指标: black_metal_expense_top3 - 黑色金属-交易对手支出排名TOP3
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-黑色金属-交易对手支出排名TOP3)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-黑色金属-交易对手支出排名TOP3_57.15.json
✅ 指标 black_metal_expense_top3 计算成功
🧮 计算指标: black_metal_total_income - 黑色金属-总经营收入
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-黑色金属-总经营收入)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-黑色金属-总经营收入_22.33.json
✅ 指标 black_metal_total_income 计算成功
🧮 计算指标: black_metal_total_expense - 黑色金属-总经营支出
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-黑色金属-总经营支出)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-黑色金属-总经营支出_36.87.json
✅ 指标 black_metal_total_expense 计算成功
🧮 计算指标: agriculture_income_top3 - 农业-交易对手收入排名TOP3
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-农业-交易对手收入排名TOP3)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-农业-交易对手收入排名TOP3_83.61.json
✅ 指标 agriculture_income_top3 计算成功
🧮 计算指标: agriculture_expense_top3 - 农业-交易对手支出排名TOP3
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-农业-交易对手支出排名TOP3)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-农业-交易对手支出排名TOP3_70.66.json
✅ 指标 agriculture_expense_top3 计算成功
🧮 计算指标: agriculture_total_income - 农业-总经营收入
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-农业-总经营收入)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-农业-总经营收入_27.24.json
✅ 指标 agriculture_total_income 计算成功
🧮 计算指标: agriculture_total_expense - 农业-总经营支出
   使用传统引擎模式
🔄 API调用尝试 1/3 (配置: 指标计算-农业-总经营支出)
[API_RESULT] 保存API结果文件: api_results/api_指标计算-农业-总经营支出_46.98.json
✅ 指标 agriculture_total_expense 计算成功
✅ 传统引擎指标计算完成：8 成功，0 失败
🧠 正在执行规划分析...
========================================
[AGENT] PlanningAgent (规划Agent)
[MODEL_INPUT] PlanningAgent:
[CONTEXT] 基于当前状态做出规划决策
Question: 执行流水分析任务
Status info: 当前状态评估：
- 规划步骤: 2
- 大纲版本: 1
- 大纲草稿存在: True
- 指标需求总数: 8
- 已计算指标数: 8
- 指标覆盖率: 100.00%
- 待计算指标数: 0
- 有效待计算指标数: 0
- 失败尝试记录: {}

建议下一步: 生成报告
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_4.31.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "finalize_report", "reasoning": "大纲草稿已存在且指标覆盖率已达到100%（8/8），所有核心指标均已计算完成，信息充足，可以生成最终报告。", "next_actions": ["生成最终报告文档", "整合所有计算结果", "格式化报告输出"], "metrics_to_compute": [], "priority_metrics": [], "additional_requirements": null}
========================================

🧠 规划决策：finalize_report
   推理：大纲草稿已存在且指标覆盖率已达到100%（8/8），所有核心指标均已计算完成，信息充足，可以生成最终报告。...
✅ 规划决策完成：finalize_report

🔍 [路由决策] 步骤=3, 大纲=True, 指标需求=8
  指标覆盖率 = 100.00%
→ 路由到 report_finalizer（生成最终报告，覆盖率=100.00%）
📋 正在生成最终报告...
✅ 最终报告生成完成：黑色金属与农业行业银行流水经营分析报告
   章节数：3
   计算指标：8/8
.2%
✅ 工作流执行完成
📋 结果: ✅ 成功
   规划步骤: 3
   指标计算: 8
🎉 测试成功！
```

### 2.指标计算通过规则引擎

```bash
🚀 执行CompleteAgentFlow系统测试
==================================================
📊 测试数据: 1 条记录
🚀 启动完整智能体工作流...
问题：执行流水分析任务
数据条数：1
计算模式：标准模式
🧠 正在执行规划分析...
========================================
[AGENT] PlanningAgent (规划Agent)
[MODEL_INPUT] PlanningAgent:
[CONTEXT] 基于当前状态做出规划决策
Question: 执行流水分析任务
Status info: 当前状态评估：
- 规划步骤: 0
- 大纲版本: 0
- 大纲草稿存在: False
- 指标需求总数: 0
- 已计算指标数: 0
- 指标覆盖率: 0.00%
- 待计算指标数: 0
- 有效待计算指标数: 0
- 失败尝试记录: {}

建议下一步: 计算指标
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_6.48.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "generate_outline", "reasoning": "大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成或无效时，应选择generate_outline。", "next_actions": ["生成报告大纲，明确分析维度、指标需求和报告结构"], "metrics_to_compute": [], "priority_metrics": [], "additional_requirements": {"raw_content": "用户需求为'执行流水分析任务'，较为宽泛。建议在生成大纲前，可进一步明确分析范围（如特定业务板块、时间周期、关键分析维度等），但当前状态满足首先生成大纲的条件。"}}
========================================

🧠 规划决策：generate_outline
   推理：大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成或无效时，应选择generate_outline。...
✅ 规划决策完成：generate_outline

🔍 [路由决策] 步骤=1, 大纲=False, 指标需求=0
→ 路由到 outline_generator（生成大纲）
📝 正在生成报告大纲...
📝 开始生成报告大纲（最多重试 5 次）...
   尝试 1/5...
========================================
[AGENT] OutlineGeneratorAgent (大纲生成Agent)
[MODEL_INPUT] OutlineGeneratorAgent:
[CONTEXT] 基于用户需求和数据样本生成报告大纲
Question: 执行流水分析任务
Sample data count: 1
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_大纲生成_35.87.json
[MODEL_OUTPUT] OutlineGeneratorAgent: {"report_title": "黑色金属与农业行业银行流水经营分析报告", "sections": [{"section_id": "sec_1", "title": "黑色金属行业经营概况分析", "description": "本部分聚焦黑色金属行业，分析其总体经营规模、主要收入与支出交易对手，评估行业资金流动的健康度与集中度。", "metrics_needed": ["black_metal_total_income", "black_metal_total_expense", "black_metal_income_top3", "black_metal_expense_top3"]}, {"section_id": "sec_2", "title": "农业行业经营概况分析", "description": "本部分聚焦农业行业，分析其总体经营规模、主要收入与支出交易对手，评估行业资金流动的健康度与集中度。", "metrics_needed": ["agriculture_total_income", "agriculture_total_expense", "agriculture_income_top3", "agriculture_expense_top3"]}, {"section_id": "sec_3", "title": "跨行业对比与综合评估", "description": "综合对比黑色金属与农业两大行业的经营规模、资金流向及交易对手集中度，进行交叉分析，评估整体经营表现与潜在风险。", "metrics_needed": ["black_metal_total_income", "black_metal_total_expense", "agriculture_total_income", "agriculture_total_expense", "black_metal_income_top3", "black_metal_expense_top3", "agriculture_income_top3", "agriculture_expense_top3"]}], "global_metrics": [{"metric_id": "black_metal_income_top3", "metric_name": "黑色金属-交易对手收入排名TOP3", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘收入’的记录，按交易对手分组汇总收入金额，并按金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "black_metal_expense_top3", "metric_name": "黑色金属-交易对手支出排名TOP3", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘支出’的记录，按交易对手分组汇总支出金额，并按金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "black_metal_total_income", "metric_name": "黑色金属-总经营收入", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘收入’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}, {"metric_id": "black_metal_total_expense", "metric_name": "黑色金属-总经营支出", "calculation_logic": "筛选业务类型为‘黑色金属’且交易方向为‘支出’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}, {"metric_id": "agriculture_income_top3", "metric_name": "农业-交易对手收入排名TOP3", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘收入’的记录，按交易对手分组汇总收入金额，并按金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "agriculture_expense_top3", "metric_name": "农业-交易对手支出排名TOP3", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘支出’的记录，按交易对手分组汇总支出金额，并按金额降序排列，取前3名。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": []}, {"metric_id": "agriculture_total_income", "metric_name": "农业-总经营收入", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘收入’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}, {"metric_id": "agriculture_total_expense", "metric_name": "农业-总经营支出", "calculation_logic": "筛选业务类型为‘农业’且交易方向为‘支出’的记录，对所有记录的金额进行求和。", "required_fields": ["txAmount", "txDirection", "businessType"], "dependencies": []}]}
========================================
.2f

📝 大纲生成成功：
   标题：黑色金属与农业行业银行流水经营分析报告
   章节数：3
   指标数：8
✅ 大纲生成完成：黑色金属与农业行业银行流水经营分析报告
   包含 3 个章节，8 个指标需求
🧠 正在执行规划分析...
========================================
[AGENT] PlanningAgent (规划Agent)
[MODEL_INPUT] PlanningAgent:
[CONTEXT] 基于当前状态做出规划决策
Question: 执行流水分析任务
Status info: 当前状态评估：
- 规划步骤: 1
- 大纲版本: 1
- 大纲草稿存在: True
- 指标需求总数: 8
- 已计算指标数: 0
- 指标覆盖率: 0.00%
- 待计算指标数: 8
- 有效待计算指标数: 8
- 失败尝试记录: {}

建议下一步: 计算指标
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_7.56.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "compute_metrics", "reasoning": "大纲草稿已存在（outline_draft存在），但指标覆盖率仅为0.00%（0/8），远低于80%的阈值。需要立即开始计算指标以满足报告生成要求。", "next_actions": ["调用指标计算服务处理待计算指标"], "metrics_to_compute": ["black_metal_income_top3", "black_metal_expense_top3", "black_metal_total_income", "black_metal_total_expense", "agriculture_income_top3", "agriculture_expense_top3", "agriculture_total_income", "agriculture_total_expense"], "priority_metrics": ["black_metal_income_top3", "black_metal_expense_top3", "agriculture_income_top3"], "additional_requirements": null}
========================================

🧠 规划决策：compute_metrics
   推理：大纲草稿已存在（outline_draft存在），但指标覆盖率仅为0.00%（0/8），远低于80%的阈值。需要立即开始计算指标以满足报告生成要求。...
   待计算指标：['black_metal_income_top3', 'black_metal_expense_top3', 'black_metal_total_income', 'black_metal_total_expense', 'agriculture_income_top3', 'agriculture_expense_top3', 'agriculture_total_income', 'agriculture_total_expense']
✅ 规划决策完成：compute_metrics

🔍 [路由决策] 步骤=2, 大纲=True, 指标需求=8
  指标覆盖率 = 0.00%
→ 路由到 metric_calculator（计算指标，覆盖率=0.00%）
🧮 正在执行指标计算...
🧮 计算指标: black_metal_income_top3 - 黑色金属-交易对手收入排名TOP3
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-黑色金属-交易对手收入排名TOP3_0.13.json
✅ 指标 black_metal_income_top3 计算成功
🧮 计算指标: black_metal_expense_top3 - 黑色金属-交易对手支出排名TOP3
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-黑色金属-交易对手支出排名TOP3_0.12.json
✅ 指标 black_metal_expense_top3 计算成功
🧮 计算指标: black_metal_total_income - 黑色金属-总经营收入
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-黑色金属-总经营收入_0.12.json
✅ 指标 black_metal_total_income 计算成功
🧮 计算指标: black_metal_total_expense - 黑色金属-总经营支出
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-黑色金属-总经营支出_0.12.json
✅ 指标 black_metal_total_expense 计算成功
🧮 计算指标: agriculture_income_top3 - 农业-交易对手收入排名TOP3
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-农业-交易对手收入排名TOP3_0.13.json
✅ 指标 agriculture_income_top3 计算成功
🧮 计算指标: agriculture_expense_top3 - 农业-交易对手支出排名TOP3
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-农业-交易对手支出排名TOP3_0.12.json
✅ 指标 agriculture_expense_top3 计算成功
🧮 计算指标: agriculture_total_income - 农业-总经营收入
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-农业-总经营收入_0.13.json
✅ 指标 agriculture_total_income 计算成功
🧮 计算指标: agriculture_total_expense - 农业-总经营支出
[RULES_API_RESULT] 保存规则引擎API结果文件: api_results/rules_api_指标计算（规则引擎）-农业-总经营支出_0.11.json
✅ 指标 agriculture_total_expense 计算成功
✅ 指标计算完成：8 成功，0 失败
🧠 正在执行规划分析...
========================================
[AGENT] PlanningAgent (规划Agent)
[MODEL_INPUT] PlanningAgent:
[CONTEXT] 基于当前状态做出规划决策
Question: 执行流水分析任务
Status info: 当前状态评估：
- 规划步骤: 2
- 大纲版本: 1
- 大纲草稿存在: True
- 指标需求总数: 8
- 已计算指标数: 8
- 指标覆盖率: 100.00%
- 待计算指标数: 0
- 有效待计算指标数: 0
- 失败尝试记录: {}

建议下一步: 生成报告
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_3.79.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "finalize_report", "reasoning": "大纲草稿已存在且指标覆盖率已达到100%（8/8），所有核心指标均已计算完成，信息充足，可以生成最终报告。", "next_actions": ["生成最终报告文档", "整合所有计算结果", "格式化报告输出"], "metrics_to_compute": [], "priority_metrics": [], "additional_requirements": null}
========================================

🧠 规划决策：finalize_report
   推理：大纲草稿已存在且指标覆盖率已达到100%（8/8），所有核心指标均已计算完成，信息充足，可以生成最终报告。...
✅ 规划决策完成：finalize_report

🔍 [路由决策] 步骤=3, 大纲=True, 指标需求=8
  指标覆盖率 = 100.00%
→ 路由到 report_finalizer（生成最终报告，覆盖率=100.00%）
📋 正在生成最终报告...
✅ 最终报告生成完成：黑色金属与农业行业银行流水经营分析报告
   章节数：3
   计算指标：8/8
.2%
✅ 工作流执行完成
📋 结果: ✅ 成功
   规划步骤: 3
   指标计算: 8
🎉 测试成功！
```

## 核心Agent架构

### 1. PlanningAgent (规划智能体)
**职责：** 分析当前状态，做出决策，控制整体流程

**决策逻辑：**
- 大纲为空 → 生成大纲
- 指标覆盖率 < 80% → 计算指标
- 指标覆盖率 ≥ 80% → 生成报告
- 需求模糊 → 澄清需求

**核心指标优先级：**
黑色金属行业：收入/支出TOP3、总收入/支出
农业行业：收入/支出TOP3、总收入/支出

**提示词示例：**
```
你是报告规划总控智能体，核心职责是精准分析当前状态并决定下一步行动。

### 决策选项（四选一）
1. generate_outline：大纲未生成或大纲无效
2. compute_metrics：大纲已生成但指标未完成（覆盖率<80%）
3. finalize_report：指标覆盖率≥80%，信息充足
4. clarify_requirements：用户需求模糊，缺少关键信息

### 决策规则（按顺序检查）
1. 检查 outline_draft 是否为空 → 空则选择 generate_outline
2. 检查 metrics_requirements 是否为空 → 空则选择 generate_outline
3. 计算指标覆盖率 = 已计算指标 / 总需求指标
   - 覆盖率 < 0.8 → 选择 compute_metrics
   - 覆盖率 ≥ 0.8 → 选择 finalize_report
4. 如果无法理解需求 → 选择 clarify_requirements

### 重要原则
- 大纲草稿已存在时，不要重复生成大纲
- 决策为 compute_metrics 时，必须提供具体的指标ID列表
- 确保 metrics_to_compute 是字符串数组格式
- 优先计算关键指标，特别是以下核心指标：
  * black_metal_income_top3（黑色金属-交易对手收入排名TOP3）
  * black_metal_expense_top3（黑色金属-交易对手支出排名TOP3）
  * black_metal_total_income（黑色金属-总经营收入）
  * black_metal_total_expense（黑色金属-总经营支出）
  * agriculture_income_top3（农业-交易对手收入排名TOP3）
  * agriculture_expense_top3（农业-交易对手支出排名TOP3）
  * agriculture_total_income（农业-总经营收入）
  * agriculture_total_expense（农业-总经营支出）
```

### 2. OutlineGeneratorAgent (大纲生成智能体)
**职责：** 根据用户需求生成结构化的报告大纲

**生成规则：**
- 必须包含8个核心指标
- 至少3个章节结构
- 指标ID与计算逻辑严格对应
- 输出标准JSON格式

**提示词示例：**
```
你是银行流水报告大纲专家。根据用户需求和样本数据，生成专业、可执行的报告大纲。

需求分析：
{question}

可用字段：
{available_fields}

样本数据：
{sample_data}

=== 必须包含的指标列表 ===
系统要求报告必须包含以下8个核心指标：
1. 黑色金属-交易对手收入排名TOP3 (metric_id: "black_metal_income_top3")
2. 黑色金属-交易对手支出排名TOP3 (metric_id: "black_metal_expense_top3")
3. 黑色金属-总经营收入 (metric_id: "black_metal_total_income")
4. 黑色金属-总经营支出 (metric_id: "black_metal_total_expense")
5. 农业-交易对手收入排名TOP3 (metric_id: "agriculture_income_top3")
6. 农业-交易对手支出排名TOP3 (metric_id: "agriculture_expense_top3")
7. 农业-总经营收入 (metric_id: "agriculture_total_income")
8. 农业-总经营支出 (metric_id: "agriculture_total_expense")

=== 报告结构要求 ===
1. 报告必须包含至少3个章节
2. 每个章节必须合理分配上述指标
3. 确保所有8个指标都被包含在章节的metrics_needed中
4. 指标ID必须与上述定义完全一致

输出要求（必须生成有效的JSON）：
1. report_title: 报告标题（字符串）
2. sections: 章节列表
3. global_metrics: 全局指标列表
```

### 3. MetricCalculationAgent (调用CodeAgent指标计算智能体)
**职责：** 执行灵活的指标计算任务

**工作流程：**
1. 接收配置列表
2. 加载JSON配置文件
3. 读取question和prompt指令
4. 选择原始数据文件
5. 调用CodeAgent API计算
6. 返回JSON结果

### 4. RulesEngineMetricCalculationAgent (规则引擎指标计算智能体)
**职责：** 执行规则引擎指标计算任务

**工作流程：**
1. 接收配置列表
2. 加载规则引擎配置文件
3. 读取question和prompt指令
4. 选择原始数据文件
5. 调用规则引擎API计算
6. 返回JSON结果

## 工作流程

```
用户查询 → PlanningAgent决策 → OutlineGenerator生成大纲 →
指标评估 → CodeAgent/RulesEngine计算指标 →
PlanningAgent重新决策 → 最终报告生成
```

## 技术特点

- **动态配置：** 指标计算通过配置文件驱动，无需修改代码
- **容错机制：** 支持重试、错误处理、状态恢复
- **模块化设计：** Agent独立部署，可扩展
- **标准接口：** 统一的API调用和数据格式
- **状态管理：** 基于LangGraph的复杂状态流转

## 计算引擎对比分析

POC项目实现了两种指标计算引擎的对比验证：**规则引擎**和**CodeAgent计算引擎**。

### 规则引擎计算模式

**API端点：** `http://10.192.72.11:31809/api/rules/executeKnowledge`

**Agent：** RulesEngineMetricCalculationAgent

**特点：**
- **执行速度极快：** 单个指标计算耗时0.11-0.13秒
- **配置驱动：** 使用预定义规则模板，配置文件名包含"(规则引擎)"标识
- **请求结构：** `{"id": "demo-农业-0301", "input": {...}}`
- **规则化处理：** 通过预设规则自动执行数据筛选、分组、聚合计算
- **稳定性高：** 8个指标全部计算成功，无失败案例

**适用场景：**
- 标准化指标计算
- 规则明确的业务场景
- 对性能要求较高的实时计算

### CodeAgent计算引擎模式

**API端点：** `http://10.192.72.11:6300/api/data_analyst/full`

**Agent：** MetricCalculationAgent

**特点：**
- **执行时间较长：** 单个指标计算耗时20-80秒
- **指令驱动：** 通过自然语言描述计算逻辑，question字段包含详细计算指令
- **请求结构：** `{"question": "...", "prompt": "...", "documents": [...]}`
- **灵活性强：** 支持复杂的自然语言指令和动态计算逻辑
- **AI增强：** 利用大语言模型理解和执行复杂计算任务

**适用场景：**
- 复杂自定义指标计算
- 临时性分析需求
- 需要灵活调整计算逻辑的场景


### 性能对比总结

| 对比维度 | 规则引擎 | CodeAgent计算引擎 |
|---------|---------|------------------|
| **执行速度** | 0.11-0.13秒/指标 | 20-80秒/指标 |
| **成功率** | 100% (8/8) | 100% (8/8) |
| **配置复杂度** | 中等（规则模板） | 低（自然语言） |
| **灵活性** | 中等（预定义规则） | 高（指令驱动） |
| **维护成本** | 低（标准化，确定性强） | 中等（指令优化，需要不断优化提示词） |
| **开发模式** | 规则模板 | 代码生成 |

**技术选型建议：**
- **生产环境推荐：** 规则引擎（高性能、高稳定、标准化部署）
- **开发验证推荐：** CodeAgent计算引擎（高灵活、多轮交互）
- **混合使用：** 标准指标用规则引擎，复杂指标用CodeAgent引擎

## 数据支持

- **农业行业：** 交易对手分析、收入支出统计
- **黑色金属行业：** 交易对手分析、收入支出统计
- **数据源：** 原始流水数据，支持加工数据预处理

## POC验证结果

✅ 流水场景多智能体验证成功
✅ 8个核心指标计算准确
✅ 报告自动生成完整
✅ 错误处理和重试机制有效
✅ API集成稳定可靠

## POC经验沉淀与可复用资产

通过本次POC项目，我们识别并验证了多个可以沉淀为知识资产的内容，为后续项目和系统开发提供了宝贵的经验积累。

### 可复用的核心资产

1. **智能体提示词模板：**
   - PlanningAgent的决策规则提示词（4选1决策逻辑）
   - OutlineGeneratorAgent的报告结构生成提示词（8个核心指标要求）
   - 多智能体协作的工作流编排规则

2. **配置标准化方案：**
   - JSON格式的指标定义文件（包含question、prompt、字段映射）
   - 工作流参数配置（循环次数、超时时间、重试机制）
   - 数据文件映射和选择规则

   **配置文件示例：**
   ```json
   {
     "question": "计算农业交易对手的支出排名前3。具体要求如下：\n1. 筛选条件：交易方向(txDirection)等于'支出'且交易摘要(txSummary)包含农资采购关键词\n2. 分组与排序：按交易对手分组汇总支出金额\n3. 输出格式：返回标准JSON格式的排序结果",
     "prompt": "相关数据输出时无须转换单位，金额直接使用原始数值"
   }
   ```

3. **业务规则与计算逻辑：**
   - 农业和黑色金属行业的指标计算规则
   - 数据筛选、分组、聚合的标准逻辑
   - 交易对手分析的TOP N排名算法

   **计算逻辑示例：**
   ```sql
   -- 交易对手支出排名TOP3计算逻辑
   SELECT txCounterparty, SUM(txAmount) as total_expense
   FROM transactions
   WHERE txDirection = '支出'
     AND businessType LIKE '%黑色金属%'
   GROUP BY txCounterparty
   ORDER BY total_expense DESC
   LIMIT 3
   ```

4. **错误处理与容错机制：**
   - 多层级的异常捕获和处理策略
   - API调用超时和重试机制
   - 状态恢复和流程回滚方案

5. **架构设计模式：**
   - 基于LangGraph的状态机工作流
   - 多智能体协作的编排模式
   - 配置驱动的模块化设计

   **状态机工作流示例：**
   ```python
   workflow = StateGraph(IntegratedWorkflowState)
   
   # 添加节点
   workflow.add_node("planning_node", planning_agent)
   workflow.add_node("outline_generator", outline_agent)
   workflow.add_node("metric_calculator", calculator_agent)
   
   # 设置条件路由
   workflow.add_conditional_edges(
       "planning_node",
       route_based_on_decision,
       {
           "outline_generator": "outline_generator",
           "metric_calculator": "metric_calculator",
           END: END
       }
   )
   ```

### CodeAgent与智能体生态的协同模式

**CodeAgent作为计算执行引擎：**
- 专注于复杂计算逻辑的实现和执行
- 提供强大的AI理解和指令驱动能力
- 支持灵活的计算需求和动态调整

**智能体生态的互补优势：**

- CodeAgent提供智能化计算能力，智能体提供业务逻辑编排
- CodeAgent负责执行复杂度，智能体负责流程控制和决策
- 形成分工明确、协作高效的技术栈

### 未来可扩展的方向

基于POC验证的经验，后续可以进一步探索：

1. **计算逻辑标准化：**
   - 将验证通过的计算规则模板化
   - 建立计算逻辑的版本管理和审计机制
   - 实现计算结果的一致性验证

2. **配置智能化管理：**
   - 基于历史数据的配置优化建议
   - 支持配置的自动化测试和验证
   - 实现配置效果的监控和分析

3. **业务场景扩展：**
   - 将成熟的智能体组合封装为标准化服务
   - 支持更多行业和业务场景的快速接入
   - 构建完整的智能体应用生态
