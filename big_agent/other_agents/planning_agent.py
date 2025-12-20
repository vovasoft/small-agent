from typing import List, Dict, Optional, Any, Union
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import json

from llmops.agents.state import AgentState, MetricRequirement, convert_numpy_types
from llmops.agents.datadev.llm import get_llm


class ActionItem(BaseModel):
    """动作项定义"""
    action: str = Field(description="动作名称")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ClarificationRequest(BaseModel):
    """澄清请求结构化格式"""
    questions: List[str] = Field(description="需要澄清的问题列表")
    missing_fields: List[str] = Field(default_factory=list, description="缺少的字段或信息")


class PlanningOutput(BaseModel):
    """规划决策输出 - 支持灵活格式"""
    decision: str = Field(
        description="决策类型: generate_outline, compute_metrics, finalize, clarify"
    )
    reasoning: str = Field(description="详细推理过程")
    next_actions: List[Union[str, ActionItem]] = Field(
        default_factory=list,
        description="下一步动作列表"
    )
    # 关键修复：明确传递待计算指标ID列表
    metrics_to_compute: List[str] = Field(
        default_factory=list,
        description="待计算指标ID列表（如 ['total_income', 'avg_balance']）"
    )
    additional_requirements: Optional[
        Union[Dict[str, Any], List[Any], ClarificationRequest]
    ] = Field(default=None, description="额外需求或澄清信息")


def normalize_additional_requirements(req: Any) -> Optional[Dict[str, Any]]:
    """
    规范化 additional_requirements
    将列表转换为字典格式
    """
    if req is None:
        return None

    if isinstance(req, dict):
        return req

    if isinstance(req, list):
        # 如果LLM错误地返回了列表，转换为字典格式
        return {
            "questions": [str(item) for item in req],
            "missing_fields": []
        }

    return {"raw": str(req)}


def create_planning_agent(llm, state: AgentState):
    """创建规划智能体（修复版：移除JSON示例，避免变量冲突）"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是报告规划总控智能体，核心职责是精准分析当前状态并决定下一步行动。

### 决策选项（四选一）
1. generate_outline：大纲未生成或大纲无效
2. compute_metrics：大纲已生成但指标未完成（覆盖率<80%）
3. finalize：指标覆盖率≥80%，信息充足
4. clarify：用户需求模糊，缺少关键信息

### 决策规则（按顺序检查）
1. 检查 outline_draft 是否为空 → 空则选择 generate_outline
2. 检查 metrics_requirements 是否为空 → 空则选择 generate_outline
3. 计算指标覆盖率 = 已计算指标 / 总需求指标
   - 覆盖率 < 0.8 → 选择 compute_metrics
   - 覆盖率 ≥ 0.8 → 选择 finalize
4. 如果无法理解需求 → 选择 clarify

### 重要原则
- 大纲草稿已存在时，不要重复生成大纲
- 决策为 compute_metrics 时，必须提供具体的指标ID列表
- 确保 metrics_to_compute 是字符串数组格式

### 输出字段说明
- decision: 决策字符串
- reasoning: 决策原因说明
- next_actions: 动作列表（可选）
- metrics_to_compute: 待计算指标ID列表（决策为compute_metrics时必须提供）
- additional_requirements: 额外需求（可选）

必须输出有效的JSON格式！"""),

    MessagesPlaceholder("messages"),

    ("user", "报告需求：{question}\n\n请输出决策结果。")
    ])

    return prompt | llm.with_structured_output(PlanningOutput)


async def planning_node(state: AgentState) -> AgentState:
    """规划节点：正确识别待计算指标并传递"""
    llm = get_llm()
    planner = create_planning_agent(llm, state)

    # 构建完整的状态评估上下文
    required_count = len(state["metrics_requirements"])
    computed_count = len(state["computed_metrics"])
    coverage = computed_count / required_count if required_count > 0 else 0

    # 新增：跟踪失败次数，避免无限循环
    failed_attempts = state.get("failed_metric_attempts", {})
    pending_ids = state.get("pending_metric_ids", [])

    # 过滤掉失败次数过多的指标
    max_retry = 3
    filtered_pending_ids = [
        mid for mid in pending_ids
        if failed_attempts.get(mid, 0) < max_retry
    ]

    status_snapshot = f"""当前状态评估：
- 规划步骤: {state['planning_step']}
- 大纲版本: {state['outline_version']}
- 大纲草稿存在: {state['outline_draft'] is not None}
- 指标需求总数: {required_count}
- 已计算指标数: {computed_count}
- 指标覆盖率: {coverage:.2%}
- 待计算指标数: {len(pending_ids)}
- 有效待计算指标数: {len(filtered_pending_ids)}
- 失败尝试记录: {failed_attempts}

建议下一步: {"计算指标" if coverage < 0.8 else "生成报告"}"""

    # 执行规划
    result = await planner.ainvoke({
        "question": state["question"],
        "messages": [("system", status_snapshot)]
    })

    # 规范化结果
    normalized_req = normalize_additional_requirements(result.additional_requirements)

    # 找出所有未计算的指标
    computed_ids = set(state["computed_metrics"].keys())
    required_metrics = state["metrics_requirements"]

    pending_metrics = [
        m for m in required_metrics
        if m.metric_id not in computed_ids
    ]

    # 关键：使用 LLM 返回的指标ID，如果没有则使用全部待计算指标
    if result.metrics_to_compute:
        pending_ids = result.metrics_to_compute
        valid_ids = [m.metric_id for m in pending_metrics]
        pending_metrics = [m for m in pending_metrics if m.metric_id in pending_ids and m.metric_id in valid_ids]

    # 更新状态
    new_state = state.copy()
    new_state["plan_history"].append(
        f"Step {new_state['planning_step']}: {result.decision}"
    )
    new_state["planning_step"] += 1
    new_state["additional_requirements"] = normalized_req

    # 关键：保存待计算指标ID列表
    if pending_metrics:
        pending_ids = [m.metric_id for m in pending_metrics]
        new_state["pending_metric_ids"] = pending_ids
        new_state["metrics_to_compute"] = pending_metrics  # 保存完整对象

    # 设置路由标志
    if result.decision == "generate_outline":
        new_state["messages"].append(
            ("ai", f"📋 规划决策：生成大纲 (v{new_state['outline_version'] + 1})")
        )
        new_state["next_route"] = "outline_generator"
    elif result.decision == "compute_metrics":
        # 修复：确保显示正确的数量
        if not pending_metrics:
            # 如果没有待计算指标但有需求，则计算所有未完成的
            computed_ids = set(state["computed_metrics"].keys())
            pending_metrics = [m for m in required_metrics if m.metric_id not in computed_ids]

        # 新增：如果有效待计算指标为空但还有指标未计算，说明都失败了太多次
        if not filtered_pending_ids and pending_ids:
            new_state["messages"].append(
                ("ai", f"⚠️ 剩余 {len(pending_ids)} 个指标已多次计算失败，将跳过这些指标直接生成报告")
            )
            new_state["next_route"] = "report_compiler"
            # 关键修复：返回前清理状态
            return convert_numpy_types(new_state)

        new_state["messages"].append(
            ("ai", f"🧮 规划决策：计算 {len(pending_metrics)} 个指标 ({[m.metric_id for m in pending_metrics]})")
        )
        new_state["next_route"] = "metrics_calculator"
    elif result.decision == "finalize":
        new_state["is_complete"] = True
        new_state["messages"].append(
            ("ai", f"✅ 规划决策：信息充足，生成最终报告（覆盖率 {coverage:.2%}）")
        )
        new_state["next_route"] = "report_compiler"
    elif result.decision == "clarify":
        questions = []
        if normalized_req and "questions" in normalized_req:
            questions = normalized_req["questions"]

        new_state["messages"].append(
            ("ai", f"❓ 需要澄清：{'；'.join(questions) if questions else '请提供更详细的需求'}")
        )
        new_state["next_route"] = "clarify_node"

    # 关键修复：返回前清理状态
    return convert_numpy_types(new_state)