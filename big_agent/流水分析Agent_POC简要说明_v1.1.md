# 流水分析Agent POC简要说明

## 一、项目概述

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

## 二、运行结果日志截图

### 大纲生成提示词

```bash
你是银行流水报告大纲专家。根据用户需求、行业和样本数据，生成专业、可执行的报告大纲。

            需求分析：
            {question}
            
            行业:
            {industry}
            
            可用字段：
            {', '.join(available_fields)}

            样本数据：
            {sample_str}
            
            === 大纲模板 ====
            # 流水数据分析报告

## 综合分析总结

本部分对账户的整体财务状况进行概括性描述，包括总收入与总支出的核心构成、分析所覆盖的账户数量，并对整体收支的健康度、稳定性和风险点进行初步评估。

## 流入流出分析：趋势图描述

本部分通过时间序列图表，直观展示分析周期内资金流入与流出的整体趋势、波动规律及季节性特征，揭示资金运动的宏观规律。

## 收入分析

本部分详细拆解收入来源，统计各类收入（如稳定、经营、投资等）的笔数与金额，分析收入结构的稳定性、多样性及主要贡献来源。

## 支出分析

本部分系统梳理支出去向，分类统计各项支出（如异常、投资、医疗等）的规模与分布，并通过图表展示支出结构，评估消费习惯与财务压力。

## 负债分析

本部分聚焦于偿债性支出，统计房贷、车贷、信用卡等显性负债的还款情况，并尝试识别与评估可能的隐藏负债，分析整体负债水平与偿债能力。

## 异常/可疑交易

本部分识别并汇总分析周期内不符合常规交易模式或存在可疑特征的流水记录，统计其笔数与金额，为风险控制提供线索。

## 用车特征分析

本部分专门针对与车辆使用相关的消费流水进行分析，统计停车、通行等费用的支出情况，以反映用车成本与习惯。

## 电核问题建议

本部分基于上述所有分析发现，提炼出在电话核实（电核）过程中需要向账户持有人重点询问和确认的具体问题列表，以验证数据真实性或获取进一步解释。
            === 报告结构要求 ===
            1. 报告必须包含至少3个章节
            2. 每个章节必须合理分配上述指标
            3. 确保所有8个指标都被包含在章节的metrics_needed中
            4. 指标ID必须与上述定义完全一致

            输出要求（必须生成有效的JSON）：
            1. report_title: 报告标题（字符串）
            2. sections: 章节列表，每个章节必须包含：
               - section_id: 章节唯一ID（如"sec_1", "sec_2"）
               - title: 章节标题
               - description: 章节描述
               - metrics_needed: 所需指标ID列表（字符串数组，必须包含上述指标）
            3. global_metrics: 全局指标列表，必须包含上述8个指标，每个指标必须包含：
               - metric_id: 指标唯一ID（必须与上述定义一致）
               - metric_name: 指标名称（必须与上述定义一致）
               - calculation_logic: 计算逻辑描述
               - required_fields: 所需字段列表
               - dependencies: 依赖的其他指标ID（可为空）

            重要提示：
            - 必须生成section_id，格式为"sec_1", "sec_2"等
            - 必须使用上述定义的metric_id，不能修改
            - metrics_needed必须是字符串数组且包含所有必需指标
            - 确保所有字段都存在，不能缺失
            - 报告标题应该体现对黑xxxx和农业行业的分析

            输出示例：
            {{
              "report_title": "黑色金属和农业行业经营分析报告",
              "sections": [
                {{
                  "section_id": "sec_1",
                  "title": "黑色金属行业分析",
                  "description": "分析黑色金属行业的收入和支出情况",
                  "metrics_needed": ["black_metal_income_top3", "black_metal_expense_top3", "black_metal_total_income", "black_metal_total_expense"]
                }},
                {{
                  "section_id": "sec_2",
                  "title": "农业行业分析",
                  "description": "分析农业行业的收入和支出情况",
                  "metrics_needed": ["agriculture_income_top3", "agriculture_expense_top3", "agriculture_total_income", "agriculture_total_expense"]
                }}
              ],
              "global_metrics": [
                {{
                  "metric_id": "black_metal_income_top3",
                  "metric_name": "黑色金属-交易对手收入排名TOP3",
                  "calculation_logic": "根据交易对手分组计算收入总额，取前3名",
                  "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"],
                  "dependencies": []
                }}
              ]
            }}"""
```

### 1.1大纲生成日志（黑色金属）

```bash
🚀 执行CompleteAgentFlow系统测试
==================================================
📊 测试数据: 1 条记录
🚀 启动完整智能体工作流...
问题：执行流水分析任务
行业：黑色金属
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
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_6.41.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "generate_outline", "reasoning": "大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成时，应首先生成大纲。", "next_actions": ["生成报告大纲，明确分析框架和关键指标"], "metrics_to_compute": [], "priority_metrics": [], "additional_requirements": {"raw_content": "需要明确'执行流水分析任务'的具体范围、分析维度（如时间、资源、效率）、关键绩效指标（KPIs）以及期望的报告格式。"}}
========================================

🧠 规划决策：generate_outline
   推理：大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成时，应首先生成大纲。...
✅ 规划决策完成：generate_outline

🔍 [路由决策] 步骤=1, 大纲=False, 指标需求=0
→ 路由到 outline_generator（生成大纲）
📝 正在生成报告大纲...
📝 开始生成报告大纲（最多重试 1 次）...
   尝试 1/1...
========================================
[AGENT] OutlineGeneratorAgent (大纲生成Agent)
[MODEL_INPUT] OutlineGeneratorAgent:
[CONTEXT] 基于用户需求和数据样本生成报告大纲
Question: 执行流水分析任务
Sample data count: 1
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_大纲生成_42.16.json
[MODEL_OUTPUT] OutlineGeneratorAgent: {"report_title": "黑色金属行业企业银行流水专项分析报告", "sections": [{"section_id": "sec_1", "title": "综合分析总结", "description": "本部分对账户的整体财务状况进行概括性描述，包括总收入与总支出的核心构成、分析所覆盖的账户数量，并对整体收支的健康度、稳定性和风险点进行初步评估。", "metrics_needed": ["total_income", "total_expense", "income_structure_stability", "expense_structure_analysis", "liability_analysis", "anomaly_suspicious_transactions", "vehicle_usage_characteristics", "telephone_verification_questions"]}, {"section_id": "sec_2", "title": "资金流动与收支结构深度分析", "description": "本部分通过时间序列图表直观展示资金流入与流出的整体趋势、波动规律及季节性特征，并详细拆解收入来源与支出去向，分析收入结构的稳定性、多样性及主要贡献来源，评估消费习惯与财务压力。", "metrics_needed": ["total_income", "total_expense", "income_structure_stability", "expense_structure_analysis", "vehicle_usage_characteristics"]}, {"section_id": "sec_3", "title": "风险识别与偿债能力评估", "description": "本部分聚焦于偿债性支出，分析整体负债水平与偿债能力，并识别汇总分析周期内不符合常规交易模式或存在可疑特征的流水记录，为风险控制提供线索。", "metrics_needed": ["liability_analysis", "anomaly_suspicious_transactions", "telephone_verification_questions"]}], "global_metrics": [{"metric_id": "total_income", "metric_name": "总收入", "calculation_logic": "统计分析周期内所有流入交易（txDirection为'IN'）的金额总和。", "required_fields": ["txAmount", "txDirection"], "dependencies": []}, {"metric_id": "total_expense", "metric_name": "总支出", "calculation_logic": "统计分析周期内所有流出交易（txDirection为'OUT'）的金额总和。", "required_fields": ["txAmount", "txDirection"], "dependencies": []}, {"metric_id": "income_structure_stability", "metric_name": "收入结构稳定性分析", "calculation_logic": "根据交易对手（txCounterparty）和业务类型（businessType）对收入进行分类（如：核心客户销售收入、其他经营收入、投资收入等），统计各类收入的笔数、金额及占比，计算主要收入来源的集中度（如CR3），评估收入多样性。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": ["total_income"]}, {"metric_id": "expense_structure_analysis", "metric_name": "支出结构分析", "calculation_logic": "根据交易对手（txCounterparty）和业务类型（businessType）对支出进行分类（如：原材料采购、能源费用、人员薪酬、税费、异常/可疑支出等），统计各类支出的笔数、金额及占比，通过图表展示支出结构。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType"], "dependencies": ["total_expense"]}, {"metric_id": "liability_analysis", "metric_name": "负债分析", "calculation_logic": "识别并汇总分析周期内与偿债相关的支出（如：交易对手为银行/金融机构，业务类型或摘要包含'贷款'、'利息'、'信用卡'等关键词），统计其笔数与总金额。结合行业特点，评估可能的供应链金融负债或隐性负债。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType", "txAbstract"], "dependencies": ["total_expense"]}, {"metric_id": "anomaly_suspicious_transactions", "metric_name": "异常/可疑交易识别", "calculation_logic": "基于预设规则（如：交易时间异常、交易对手为高风险名单、金额为整数大额、频繁小额试探性交易、摘要信息模糊等）筛选流水记录，统计可疑交易的笔数、总金额，并列出明细。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType", "txTime", "txAbstract"], "dependencies": []}, {"metric_id": "vehicle_usage_characteristics", "metric_name": "用车特征分析", "calculation_logic": "识别与车辆使用相关的支出（如：交易对手为加油站、停车场、高速公路公司、车辆维修店，或摘要包含相关关键词），统计此类支出的总金额、笔数及月度分布，反映用车成本。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "businessType", "txAbstract"], "dependencies": ["total_expense"]}, {"metric_id": "telephone_verification_questions", "metric_name": "电核问题建议", "calculation_logic": "基于上述所有分析发现（如大额异常交易、特定交易对手频繁往来、收入集中度风险、偿债压力迹象等），提炼出在电话核实时需要向账户持有人重点询问和确认的具体问题列表。", "required_fields": [], "dependencies": ["income_structure_stability", "expense_structure_analysis", "liability_analysis", "anomaly_suspicious_transactions", "vehicle_usage_characteristics"]}]}
========================================
.2f

📝 大纲生成成功：
   标题：黑色金属行业企业银行流水专项分析报告
   章节数：3
   指标数：8
✅ 大纲生成完成：黑色金属行业企业银行流水专项分析报告
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
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_6.68.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "compute_metrics", "reasoning": "大纲草稿已存在（大纲版本：1），但指标覆盖率为0.00%（0/8），远低于80%的阈值。需要开始计算指标以推进报告生成。", "next_actions": ["调用指标计算模块处理待计算指标"], "metrics_to_compute": ["metric_1", "metric_2", "metric_3", "metric_4", "metric_5", "metric_6", "metric_7", "metric_8"], "priority_metrics": ["metric_1", "metric_2", "metric_3"], "additional_requirements": null}
========================================

🧠 规划决策：compute_metrics
   推理：大纲草稿已存在（大纲版本：1），但指标覆盖率为0.00%（0/8），远低于80%的阈值。需要开始计算指标以推进报告生成。...
   待计算指标：['metric_1', 'metric_2', 'metric_3', 'metric_4', 'metric_5', 'metric_6', 'metric_7', 'metric_8']
✅ 规划决策完成：compute_metrics

🔍 [路由决策] 步骤=2, 大纲=True, 指标需求=8
  指标覆盖率 = 0.00%
→ 路由到 metric_calculator（计算指标，覆盖率=0.00%）
🧮 正在执行指标计算...
⚠️ 找不到指标 metric_1 的需求信息，跳过
⚠️ 找不到指标 metric_2 的需求信息，跳过
⚠️ 找不到指标 metric_3 的需求信息，跳过
⚠️ 找不到指标 metric_4 的需求信息，跳过
⚠️ 找不到指标 metric_5 的需求信息，跳过
⚠️ 找不到指标 metric_6 的需求信息，跳过
⚠️ 找不到指标 metric_7 的需求信息，跳过
⚠️ 找不到指标 metric_8 的需求信息，跳过
✅ 指标计算完成：0 成功，0 失败
🧠 正在执行规划分析...
```



### 1.2大纲生成日志（农业）

```bash
 执行CompleteAgentFlow系统测试
==================================================
📊 测试数据: 1 条记录
🚀 启动完整智能体工作流...
问题：执行流水分析任务
行业：农业
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
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_6.23.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "generate_outline", "reasoning": "大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成时，应首先生成大纲。", "next_actions": ["生成报告大纲，明确分析框架和关键指标"], "metrics_to_compute": [], "priority_metrics": [], "additional_requirements": {"raw_content": "需要明确'执行流水分析任务'的具体范围、分析维度（如时间、资源、效率、瓶颈）、关键绩效指标（KPIs）以及报告的目标受众，以便生成针对性的大纲。"}}
========================================

🧠 规划决策：generate_outline
   推理：大纲草稿不存在（outline_draft存在性为False），且指标需求总数为0，表明尚未生成报告大纲。根据决策规则，当大纲未生成时，应首先生成大纲。...
✅ 规划决策完成：generate_outline

🔍 [路由决策] 步骤=1, 大纲=False, 指标需求=0
→ 路由到 outline_generator（生成大纲）
📝 正在生成报告大纲...
📝 开始生成报告大纲（最多重试 1 次）...
   尝试 1/1...
========================================
[AGENT] OutlineGeneratorAgent (大纲生成Agent)
[MODEL_INPUT] OutlineGeneratorAgent:
[CONTEXT] 基于用户需求和数据样本生成报告大纲
Question: 执行流水分析任务
Sample data count: 1
========================================
[API_RESULT] 保存API结果文件: api_results/api_mll_大纲生成_49.41.json
[MODEL_OUTPUT] OutlineGeneratorAgent: {"report_title": "农业经营主体银行流水分析报告", "sections": [{"section_id": "sec_1", "title": "农业经营主体财务状况综合分析", "description": "本部分对农业经营主体的整体财务状况进行概括性描述，包括总收入与总支出的核心构成、分析所覆盖的账户数量，并对整体收支的健康度、稳定性和风险点进行初步评估。同时，通过时间序列图表，直观展示分析周期内资金流入与流出的整体趋势、波动规律及季节性特征，揭示资金运动的宏观规律。", "metrics_needed": ["overall_income_expense_summary", "inflow_outflow_trend_chart", "income_analysis", "expense_analysis", "liability_analysis", "abnormal_suspicious_transactions", "vehicle_usage_analysis", "telephone_verification_questions"]}, {"section_id": "sec_2", "title": "农业经营收支与负债专项分析", "description": "本部分详细拆解农业经营相关的收入来源与支出去向。收入方面，统计各类收入（如农产品销售收入、政府补贴、其他经营收入等）的笔数与金额，分析收入结构的稳定性、多样性及主要贡献来源。支出方面，系统梳理各项支出（如农资采购、人工成本、设备维护、异常支出等）的规模与分布，并通过图表展示支出结构，评估经营成本与财务压力。同时，聚焦于偿债性支出，统计贷款、信用卡等负债的还款情况，并尝试识别与评估可能的隐藏负债，分析整体负债水平与偿债能力。", "metrics_needed": ["income_analysis", "expense_analysis", "liability_analysis"]}, {"section_id": "sec_3", "title": "风险识别与电核建议", "description": "本部分识别并汇总分析周期内不符合常规交易模式或存在可疑特征的流水记录，统计其笔数与金额，为风险控制提供线索。同时，专门针对与车辆使用相关的消费流水进行分析，统计停车、通行、加油等费用的支出情况，以反映用车成本与习惯。最后，基于上述所有分析发现，提炼出在电话核实（电核）过程中需要向账户持有人重点询问和确认的具体问题列表，以验证数据真实性或获取进一步解释。", "metrics_needed": ["abnormal_suspicious_transactions", "vehicle_usage_analysis", "telephone_verification_questions"]}], "global_metrics": [{"metric_id": "overall_income_expense_summary", "metric_name": "整体收支概况", "calculation_logic": "计算分析周期内所有账户的总流入金额、总流出金额、净流入/流出金额、分析账户数量，并对收支健康度（如收支比）、稳定性（如月度波动率）进行初步评估。", "required_fields": ["txAmount", "txDirection", "txDate", "accountNumber"], "dependencies": []}, {"metric_id": "inflow_outflow_trend_chart", "metric_name": "流入流出趋势图", "calculation_logic": "按日/周/月等时间维度聚合计算流入总额和流出总额，生成时间序列折线图或面积图，以展示趋势、波动及季节性特征。", "required_fields": ["txAmount", "txDirection", "txDate"], "dependencies": []}, {"metric_id": "income_analysis", "metric_name": "收入分析", "calculation_logic": "根据交易对手、摘要、金额等字段，对流入交易进行分类（如：农产品销售、政府补贴、经营收入、投资收入等），统计各类收入的笔数、总金额、占比，并识别主要收入来源。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "txRemark", "txDate"], "dependencies": []}, {"metric_id": "expense_analysis", "metric_name": "支出分析", "calculation_logic": "根据交易对手、摘要、金额等字段，对流出交易进行分类（如：农资采购、人工薪酬、设备购置/维护、生活消费、医疗、投资、异常支出等），统计各类支出的笔数、总金额、占比，并通过饼图或条形图展示支出结构。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "txRemark", "txDate"], "dependencies": []}, {"metric_id": "liability_analysis", "metric_name": "负债分析", "calculation_logic": "识别并汇总流向银行、金融机构或特定贷款机构的定期、定额流出交易（如房贷、车贷、经营贷、信用卡还款等），计算月均/年均还款额、占总支出比例。结合收入分析，评估偿债能力（如债务收入比）。尝试识别非固定但可能为隐性负债的支出模式。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "txRemark", "txDate"], "dependencies": ["income_analysis", "expense_analysis"]}, {"metric_id": "abnormal_suspicious_transactions", "metric_name": "异常/可疑交易", "calculation_logic": "基于规则（如大额整数交易、非营业时间交易、高频小额试探性交易、对手方为高风险行业或地区、摘要信息模糊等）筛选流水记录，统计可疑交易的笔数、总金额，并进行简要描述。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "txRemark", "txDate", "txTime"], "dependencies": []}, {"metric_id": "vehicle_usage_analysis", "metric_name": "用车特征分析", "calculation_logic": "筛选交易对手或摘要中包含“加油站”、“停车”、“ETC”、“洗车”、“维修”、“保险”（车险）等关键词的支出记录，统计相关费用的总金额、笔数、月度平均支出，以分析用车频率和成本。", "required_fields": ["txAmount", "txDirection", "txCounterparty", "txRemark"], "dependencies": []}, {"metric_id": "telephone_verification_questions", "metric_name": "电核问题建议", "calculation_logic": "基于收入、支出、负债、异常交易等分析结果，提炼出需要向客户核实的具体问题，例如：确认大额收入/支出的具体背景、解释异常交易模式、核实负债情况、确认用车相关支出是否合理等。", "required_fields": [], "dependencies": ["income_analysis", "expense_analysis", "liability_analysis", "abnormal_suspicious_transactions", "vehicle_usage_analysis"]}]}
========================================
.2f

📝 大纲生成成功：
   标题：农业经营主体银行流水分析报告
   章节数：3
   指标数：8
✅ 大纲生成完成：农业经营主体银行流水分析报告
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
[API_RESULT] 保存API结果文件: api_results/api_mll_规划决策_6.31.json
[MODEL_OUTPUT] PlanningAgent: {"decision": "compute_metrics", "reasoning": "大纲草稿已存在（大纲版本：1），但指标覆盖率为0.00%（0/8），远低于80%的阈值。需要开始计算指标以推进报告生成。", "next_actions": ["调用指标计算模块处理待计算指标"], "metrics_to_compute": ["metric_1", "metric_2", "metric_3", "metric_4", "metric_5", "metric_6", "metric_7", "metric_8"], "priority_metrics": ["metric_1", "metric_2", "metric_3"], "additional_requirements": null}
========================================

🧠 规划决策：compute_metrics
   推理：大纲草稿已存在（大纲版本：1），但指标覆盖率为0.00%（0/8），远低于80%的阈值。需要开始计算指标以推进报告生成。...
   待计算指标：['metric_1', 'metric_2', 'metric_3', 'metric_4', 'metric_5', 'metric_6', 'metric_7', 'metric_8']
✅ 规划决策完成：compute_metrics

🔍 [路由决策] 步骤=2, 大纲=True, 指标需求=8
  指标覆盖率 = 0.00%
→ 路由到 metric_calculator（计算指标，覆盖率=0.00%）
🧮 正在执行指标计算...
⚠️ 找不到指标 metric_1 的需求信息，跳过
⚠️ 找不到指标 metric_2 的需求信息，跳过
⚠️ 找不到指标 metric_3 的需求信息，跳过
⚠️ 找不到指标 metric_4 的需求信息，跳过
⚠️ 找不到指标 metric_5 的需求信息，跳过
⚠️ 找不到指标 metric_6 的需求信息，跳过
⚠️ 找不到指标 metric_7 的需求信息，跳过
⚠️ 找不到指标 metric_8 的需求信息，跳过
✅ 指标计算完成：0 成功，0 失败
```

### 2.1指标计算日志（codeagent）

```bash
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

### 2.2指标计算日志（规则引擎）

```bash
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

## 三、核心Agent架构

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

### 2. OutlineGeneratorAgent (大纲生成智能体)
**职责：** 根据用户需求生成结构化的报告大纲

**生成规则：**
- 必须包含8个核心指标
- 至少3个章节结构
- 指标ID与计算逻辑严格对应
- 输出标准JSON格式

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

## 四、工作流程

```
用户查询 → PlanningAgent决策 → OutlineGenerator生成大纲 →
指标评估 → CodeAgent/RulesEngine计算指标 →
PlanningAgent重新决策 → 最终报告生成
```

## 五、计算引擎对比分析

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
| **配置复杂度** | 中等（规则模板） | 低（自然语言）支出 |
| **灵活性** | 中等（预定义规则） | 高（指令驱动） |
| **开发模式** | 规则模板 | 大模型代码生成 |

## 六、POC涉及的知识沉淀

#### 1、大纲模板知识

```bash
# 流水数据分析报告

## 综合分析总结

本部分对账户的整体财务状况进行概括性描述，包括总收入与总支出的核心构成、分析所覆盖的账户数量，并对整体收支的健康度、稳定性和风险点进行初步评估。

## 流入流出分析：趋势图描述

本部分通过时间序列图表，直观展示分析周期内资金流入与流出的整体趋势、波动规律及季节性特征，揭示资金运动的宏观规律。

## 收入分析

本部分详细拆解收入来源，统计各类收入（如稳定、经营、投资等）的笔数与金额，分析收入结构的稳定性、多样性及主要贡献来源。

## 支出分析

本部分系统梳理支出去向，分类统计各项支出（如异常、投资、医疗等）的规模与分布，并通过图表展示支出结构，评估消费习惯与财务压力。

## 负债分析

本部分聚焦于偿债性支出，统计房贷、车贷、信用卡等显性负债的还款情况，并尝试识别与评估可能的隐藏负债，分析整体负债水平与偿债能力。

## 异常/可疑交易

本部分识别并汇总分析周期内不符合常规交易模式或存在可疑特征的流水记录，统计其笔数与金额，为风险控制提供线索。

## 用车特征分析

本部分专门针对与车辆使用相关的消费流水进行分析，统计停车、通行等费用的支出情况，以反映用车成本与习惯。

## 电核问题建议

本部分基于上述所有分析发现，提炼出在电话核实（电核）过程中需要向账户持有人重点询问和确认的具体问题列表，以验证数据真实性或获取进一步解释。
```

#### 2、引擎规则知识

```bash
{
  "description": "因子概述：针对办理经营贷业务，且客户所属行业为黑色金属的流水分析指标计算环节，可通过该知识因子对其中交易对手经营收入top3进行分组筛选。",
 "id": "demo-黑色金属-0302",
"input": "加工数据-流水分析-黑色金属打标.json"
}
```

#### 3、codeagent提示词知识

```bash
{
  "description": "因子概述：针对办理经营贷业务，且客户所属行业为黑色金属的流水分析指标计算环节，可通过该知识因子对其中交易对手经营收入top3进行分组筛选。",
  "question": "计算黑色金属交易对手的经营收入排名前3。具体要求如下：\n1. 筛选条件：交易方向(`txDirection`)为“收入”，并且交易摘要(`txSummary`)同时满足以下两点：\n   a) 包含“铁精粉”或“铁矿石”中的至少一个关键词。\n   b) 包含“销售”这个关键词。\n2. 处理逻辑：将筛选后的数据，按照交易对手(`txCounterparty`)进行分组，并汇总每个公司的总收入(`txAmount`)。\n3. 输出要求：将分组汇总结果按照总收入从高到低进行排序，取前3名。如果符合条件的公司不足3家，则列出所有符合条件的公司。\n4. 返回一个标准的JSON对象，结构必须严格遵循：`{\"sortResult\": [{\"totalIncome\": 数值, \"txCounterparty\": \"公司名\"}, ...]}`。\n5. 所有文本内容使用UTF-8编码。",
  "prompt": "请严格按照以下要求处理数据并生成输出：\n1. **数据筛选**：仅处理`txDirection`字段值为“收入”的记录。在这些记录中，`txSummary`字段必须包含“销售”字样，并且还必须包含“铁精粉”或“铁矿石”中的至少一个。\n2. **计算与排序**：对筛选出的记录，按`txCounterparty`分组，计算每组`txAmount`的总和，即为该公司的总收入。然后按总收入**降序**排列。\n3. **输出格式**：\n   - 生成一个JSON对象，根键名为`\"sortResult\"`，其值是一个数组。\n   - 数组中的每个元素是一个对象，包含且仅包含两个键值对：`\"totalIncome\"`（数值类型，表示总收入）和`\"txCounterparty\"`（字符串类型，表示公司名称）。\n   - 金额(`totalIncome`)保持原始数据中的数值格式（单位：万元），无需转换或格式化。例如，182.0或182都是可接受的。\n   - 确保JSON是有效的，并且字符串使用双引号。\n4. **边界情况**：如果没有记录满足筛选条件，则`\"sortResult\"`对应的值应为空数组`[]`。\n5. **编码**：最终输出的所有字符串内容必须使用UTF-8编码。"
}
```

## 七、POC验证结果

✅ 流水场景多智能体验证成功
✅ 8个核心指标计算准确
✅ 错误处理和重试机制有效
✅ API集成稳定可靠

## 八、POC经验沉淀与可复用资产

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

1. 
