"""
整合的工作流状态定义
===================

此文件定义了整合了多个Agent的工作流状态，兼容现有的Big Agent状态管理和新增的报告生成Agent状态。

状态层次：
1. 输入层：用户查询和数据
2. 意图层：意图识别结果
3. 规划层：规划决策和大纲生成
4. 计算层：指标计算结果
5. 结果层：最终报告生成
6. 对话层：消息历史和错误处理

兼容性：
- 兼容现有的Big Agent WorkflowState
- 整合来自other_agents的AgentState
- 支持扩展新的Agent状态需求

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-20
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


# ============= 数据模型 =============

class MetricRequirement(BaseModel):
    """指标需求定义"""
    metric_id: str = Field(description="指标唯一标识，如 'total_income_jan'")
    metric_name: str = Field(description="指标中文名称")
    calculation_logic: str = Field(description="计算逻辑描述")
    required_fields: List[str] = Field(description="所需字段")
    dependencies: List[str] = Field(default_factory=list, description="依赖的其他指标ID")


class ReportSection(BaseModel):
    """报告大纲章节"""
    section_id: str = Field(description="章节ID")
    title: str = Field(description="章节标题")
    description: str = Field(description="章节内容要求")
    metrics_needed: List[str] = Field(description="所需指标ID列表")


class ReportOutline(BaseModel):
    """完整报告大纲"""
    report_title: str = Field(description="报告标题")
    sections: List[ReportSection] = Field(description="章节列表")
    global_metrics: List[MetricRequirement] = Field(description="全局指标列表")


# ============= 序列化工具函数 =============

def convert_numpy_types(obj: Any) -> Any:
    """
    递归转换所有numpy类型为Python原生类型
    确保所有数据可序列化
    """
    if isinstance(obj, dict):
        return {str(k): convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, set):
        return {convert_numpy_types(item) for item in obj}
    elif hasattr(obj, 'item') and hasattr(obj, 'dtype'):  # numpy scalar
        return convert_numpy_types(obj.item())
    else:
        return obj


# ============= 整合的工作流状态定义 =============

class IntegratedWorkflowState(TypedDict):
    """整合的工作流状态定义 - 兼容多个Agent系统"""

    # === 基础输入层 (兼容Big Agent) ===
    user_input: str
    question: str  # 别名，兼容报告生成Agent

    industry: str  # 行业

    # === 数据层 ===
    data_set: List[Dict[str, Any]]  # 报告生成Agent的数据格式
    transactions_df: Optional[Any]  # 可选的数据框格式

    # === 意图识别层 (Big Agent原有) ===
    intent_result: Optional[Dict[str, Any]]

    # === 规划和大纲层 (新增) ===
    planning_step: int
    plan_history: List[str]
    outline_draft: Optional[ReportOutline]
    outline_version: int
    outline_ready: bool

    # === 指标计算层 ===
    metrics_requirements: List[MetricRequirement]  # 报告生成Agent格式
    computed_metrics: Dict[str, Any]  # 计算结果
    metrics_cache: Dict[str, Any]  # 缓存
    pending_metric_ids: List[str]  # 待计算指标ID
    failed_metric_attempts: Dict[str, int]  # 失败统计
    calculation_results: Optional[Dict[str, Any]]  # Big Agent格式的计算结果

    # === 结果层 ===
    report_draft: Dict[str, Any]  # 报告草稿
    knowledge_result: Optional[Dict[str, Any]]  # Big Agent知识沉淀结果
    is_complete: bool
    completeness_score: float
    answer: Optional[str]  # 最终答案

    # === 对话和消息层 ===
    messages: List[Dict[str, Any]]  # Big Agent消息格式
    current_node: str
    session_id: str
    next_route: str

    # === 错误处理层 ===
    errors: List[str]
    last_decision: str

    # === 时间跟踪层 ===
    start_time: str
    end_time: Optional[str]
    api_result: Dict[str, Any]  # 存储所有API调用结果


# ============= 状态创建和初始化函数 =============

def create_initial_integrated_state(question: str, industry: str, data: List[Dict[str, Any]], session_id: str = None) -> IntegratedWorkflowState:
    """
    创建初始的整合状态

    Args:
        question: 用户查询
        data: 数据集
        session_id: 会话ID

    Returns:
        初始化后的状态
    """
    current_time = datetime.now().isoformat()
    session = session_id or f"session_{int(datetime.now().timestamp())}"

    return {
        # 基础输入
        "user_input": question,
        "question": question,
        "industry": industry,

        # 数据层
        "data_set": convert_numpy_types(data),
        "transactions_df": None,

        # 意图识别层
        "intent_result": None,

        # 规划和大纲层
        "planning_step": 0,
        "plan_history": [],
        "outline_draft": None,
        "outline_version": 0,
        "outline_ready": False,

        # 指标计算层
        "metrics_requirements": [],
        "computed_metrics": {},
        "metrics_cache": {},
        "pending_metric_ids": [],
        "failed_metric_attempts": {},
        "calculation_results": None,

        # 结果层
        "report_draft": {},
        "knowledge_result": None,
        "is_complete": False,
        "completeness_score": 0.0,
        "answer": None,

        # 对话和消息层
        "messages": [{
            "role": "user",
            "content": question,
            "timestamp": current_time
        }],
        "current_node": "start",
        "session_id": session,
        "next_route": "planning_node",

        # 错误处理层
        "errors": [],
        "last_decision": "init",

        # 时间跟踪层
        "start_time": current_time,
        "end_time": None,
        "api_result": {},  # 存储所有API调用结果

        # 计算模式配置层
        "use_rules_engine_only": False,
        "use_traditional_engine_only": False
    }


def is_state_ready_for_calculation(state: IntegratedWorkflowState) -> bool:
    """
    检查状态是否准备好进行指标计算

    Args:
        state: 当前状态

    Returns:
        是否准备好
    """
    return (
        state.get("outline_draft") is not None and
        len(state.get("metrics_requirements", [])) > 0 and
        len(state.get("pending_metric_ids", [])) > 0
    )


def get_calculation_progress(state: IntegratedWorkflowState) -> Dict[str, Any]:
    """
    获取指标计算进度信息

    Args:
        state: 当前状态

    Returns:
        进度信息
    """
    required = len(state.get("metrics_requirements", []))
    computed = len(state.get("computed_metrics", {}))
    pending = len(state.get("pending_metric_ids", []))

    return {
        "required_count": required,
        "computed_count": computed,
        "pending_count": pending,
        "coverage_rate": computed / required if required > 0 else 0,
        "is_complete": computed >= required * 0.8  # 80%覆盖率视为完成
    }


def update_state_with_outline_generation(state: IntegratedWorkflowState, outline: ReportOutline) -> IntegratedWorkflowState:
    """
    使用大纲生成结果更新状态

    Args:
        state: 当前状态
        outline: 生成的大纲

    Returns:
        更新后的状态
    """
    new_state = state.copy()
    new_state["outline_draft"] = outline
    new_state["outline_version"] += 1
    new_state["outline_ready"] = True
    new_state["metrics_requirements"] = outline.global_metrics
    new_state["pending_metric_ids"] = [m.metric_id for m in outline.global_metrics]

    # 添加消息
    new_state["messages"].append({
        "role": "assistant",
        "content": f"✅ 大纲生成完成 v{new_state['outline_version']}：{outline.report_title}",
        "timestamp": datetime.now().isoformat()
    })

    return new_state


def update_state_with_planning_decision(state: IntegratedWorkflowState, decision: Dict[str, Any]) -> IntegratedWorkflowState:
    """
    使用规划决策结果更新状态

    Args:
        state: 当前状态
        decision: 规划决策

    Returns:
        更新后的状态
    """
    new_state = state.copy()
    new_state["planning_step"] += 1
    new_state["last_decision"] = decision.get("decision", "unknown")
    new_state["next_route"] = decision.get("next_route", "planning_node")

    # 如果有待计算指标，更新待计算列表
    if decision.get("metrics_to_compute"):
        new_state["pending_metric_ids"] = decision["metrics_to_compute"]

    # 添加规划历史
    new_state["plan_history"].append(
        f"Step {new_state['planning_step']}: {decision.get('decision', 'unknown')}"
    )

    return new_state


def finalize_state_with_report(state: IntegratedWorkflowState, final_report: Dict[str, Any]) -> IntegratedWorkflowState:
    """
    使用最终报告完成状态

    Args:
        state: 当前状态
        final_report: 最终报告

    Returns:
        完成的状态
    """
    new_state = state.copy()
    new_state["report_draft"] = final_report
    new_state["is_complete"] = True
    new_state["answer"] = final_report
    new_state["end_time"] = datetime.now().isoformat()

    # 计算完整性分数
    progress = get_calculation_progress(new_state)
    new_state["completeness_score"] = progress["coverage_rate"]

    return new_state