from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json  # 确保导入json
import uuid

from llmops.agents.state import AgentState, ReportOutline, ReportSection, MetricRequirement, convert_numpy_types
from llmops.agents.datadev.llm import get_llm


class OutlineGenerator:
    """大纲生成智能体：将报告需求转化为结构化大纲"""

    def __init__(self, llm):
        self.llm = llm.with_structured_output(ReportOutline)

    def create_prompt(self, question: str, sample_data: List[Dict]) -> str:
        """创建大纲生成提示"""

        available_fields = list(sample_data[0].keys()) if sample_data else []
        sample_str = json.dumps(sample_data[:2], ensure_ascii=False, indent=2)

        # 关键修复：提供详细的字段说明和示例
        return f"""你是银行流水报告大纲专家。根据用户需求和样本数据，生成专业、可执行的报告大纲。

需求分析：
{question}

可用字段：
{', '.join(available_fields)}

样本数据：
{sample_str}

输出要求（必须生成有效的JSON）：
1. report_title: 报告标题（字符串）
2. sections: 章节列表，每个章节必须包含：
   - section_id: 章节唯一ID（如"sec_1", "sec_2"）
   - title: 章节标题
   - description: 章节描述
   - metrics_needed: 所需指标ID列表（字符串数组，可为空）
3. global_metrics: 全局指标列表，每个指标必须包含：
   - metric_id: 指标唯一ID（如"total_income", "avg_balance"）
   - metric_name: 指标名称
   - calculation_logic: 计算逻辑描述
   - required_fields: 所需字段列表
   - dependencies: 依赖的其他指标ID（可为空）

重要提示：
- 必须生成section_id，格式为"sec_1", "sec_2"等
- 必须生成metric_id，格式为字母+下划线+描述
- metrics_needed必须是字符串数组
- 确保所有字段都存在，不能缺失

输出示例：
{{
  "report_title": "2024年第三季度分析报告",
  "sections": [
    {{
      "section_id": "sec_1",
      "title": "收入概览",
      "description": "分析收入总额",
      "metrics_needed": ["total_income", "avg_income"]
    }}
  ],
  "global_metrics": [
    {{
      "metric_id": "total_income",
      "metric_name": "总收入",
      "calculation_logic": "sum of all income transactions",
      "required_fields": ["txAmount", "txDirection"],
      "dependencies": []
    }}
  ]
}}"""

    async def generate(self, state: AgentState) -> ReportOutline:
        """异步生成大纲（修复版：自动补全缺失字段）"""
        prompt = self.create_prompt(
            question=state["question"],
            sample_data=state["data_set"][:2]
        )

        messages = [
            ("system", "你是一名专业的报告大纲生成专家，必须输出完整、有效的JSON格式，包含所有必需字段。"),
            ("user", prompt)
        ]

        outline = await self.llm.ainvoke(messages)

        # 关键修复：后处理，补全缺失的section_id和metric_id
        outline = self._post_process_outline(outline)

        return outline

    def _post_process_outline(self, outline: ReportOutline) -> ReportOutline:
        """
        后处理大纲，自动补全缺失的必需字段
        """
        # 为章节补全section_id
        for idx, section in enumerate(outline.sections):
            if not section.section_id:
                section.section_id = f"sec_{idx + 1}"

            # 确保metrics_needed是列表
            if not isinstance(section.metrics_needed, list):
                section.metrics_needed = []

        # 为指标补全metric_id和dependencies
        for idx, metric in enumerate(outline.global_metrics):
            if not metric.metric_id:
                metric.metric_id = f"metric_{idx + 1}"

            # 确保dependencies是列表
            if not isinstance(metric.dependencies, list):
                metric.dependencies = []

            # 推断required_fields（如果为空）
            if not metric.required_fields:
                metric.required_fields = self._infer_required_fields(
                    metric.calculation_logic
                )

        return outline

    def _infer_required_fields(self, logic: str) -> List[str]:
        """从计算逻辑推断所需字段"""
        field_mapping = {
            "收入": ["txAmount", "txDirection"],
            "支出": ["txAmount", "txDirection"],
            "余额": ["txBalance"],
            "对手方": ["txCounterparty"],
            "日期": ["txDate"],
            "时间": ["txTime", "txDate"],
            "摘要": ["txSummary"],
            "创建时间": ["createdAt"]
        }

        fields = []
        for keyword, field_list in field_mapping.items():
            if keyword in logic:
                fields.extend(field_list)

        return list(set(fields))


async def outline_node(state: AgentState) -> AgentState:
    """大纲生成节点：设置成功标志，防止重复生成"""

    llm = get_llm()
    generator = OutlineGenerator(llm)

    try:
        # 异步生成大纲
        outline = await generator.generate(state)

        # 更新状态
        new_state = state.copy()
        new_state["outline_draft"] = outline
        new_state["outline_version"] += 1

        # 防护：设置成功标志
        new_state["outline_ready"] = True  # 明确标志：大纲已就绪

        new_state["metrics_requirements"] = outline.global_metrics
        new_state["metrics_pending"] = outline.global_metrics.copy()  # 待计算指标
        new_state["messages"].append(
            ("ai", f"✅ 大纲生成完成 v{new_state['outline_version']}：{outline.report_title}")
        )

        print(f"\n📝 大纲已生成：{outline.report_title}")
        print(f"   章节数：{len(outline.sections)}")
        print(f"   指标数：{len(outline.global_metrics)}")

        # 新增：详细打印大纲内容
        print("\n" + "=" * 70)
        print("📋 详细大纲内容")
        print("=" * 70)
        print(json.dumps(outline.dict(), ensure_ascii=False, indent=2))
        print("=" * 70)

        # 关键修复：返回前清理状态
        return convert_numpy_types(new_state)

    except Exception as e:
        print(f"⚠️ 大纲生成出错: {e}，使用默认结构")

        # 创建默认大纲
        default_outline = ReportOutline(
            report_title="默认交易分析报告",
            sections=[
                ReportSection(
                    section_id="sec_1",
                    title="交易概览",
                    description="基础交易情况分析",
                    metrics_needed=["total_transactions", "total_income", "total_expense"]
                )
            ],
            global_metrics=[
                MetricRequirement(
                    metric_id="total_transactions",
                    metric_name="总交易笔数",
                    calculation_logic="count all transactions",
                    required_fields=["txId"],
                    dependencies=[]
                ),
                MetricRequirement(
                    metric_id="total_income",
                    metric_name="总收入",
                    calculation_logic="sum of income transactions",
                    required_fields=["txAmount", "txDirection"],
                    dependencies=[]
                )
            ]
        )

        new_state = state.copy()
        new_state["outline_draft"] = default_outline
        new_state["outline_version"] += 1
        new_state["outline_ready"] = True  # 即使默认也标记为就绪
        new_state["metrics_requirements"] = default_outline.global_metrics
        new_state["messages"].append(
            ("ai", f"⚠️ 使用默认大纲 v{new_state['outline_version']}")
        )

        # 新增：详细打印默认大纲内容
        print("\n" + "=" * 70)
        print("📋 默认大纲内容")
        print("=" * 70)
        print(json.dumps(default_outline.dict(), ensure_ascii=False, indent=2))
        print("=" * 70)

        # 关键修复：返回前清理状态
        return convert_numpy_types(new_state)