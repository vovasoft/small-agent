from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
import numpy as np


# ============= 数据模型 =============

class MetricRequirement(BaseModel):
    """指标需求定义"""
    metric_id: str = Field(description="指标唯一标识，如 'total_income_jan'")
    metric_name: str = Field(description="指标中文名称")
    calculation_logic: str = Field(description="计算逻辑描述")
    required_fields: List[str] = Field(description="所需字段")
    dependencies: List[str] = Field(default_factory=list)


class ReportSection(BaseModel):
    """报告大纲章节"""
    section_id: str = Field(description="章节ID")
    title: str = Field(description="章节标题")
    description: str = Field(description="章节内容要求")
    metrics_needed: List[str] = Field(description="所需指标ID列表")


class ReportOutline(BaseModel):
    """完整报告大纲"""
    report_title: str
    sections: List[ReportSection]
    global_metrics: List[MetricRequirement]


# ============= 序列化工具函数 =============

def convert_numpy_types(obj: Any) -> Any:
    """
    递归转换所有numpy类型为Python原生类型
    关键修复：确保所有数据可序列化
    """
    if isinstance(obj, dict):
        return {str(k): convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, set):
        return {convert_numpy_types(item) for item in obj}
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif hasattr(obj, 'item') and hasattr(obj, 'dtype'):  # numpy scalar
        return convert_numpy_types(obj.item())
    else:
        return obj


def create_initial_state(question: str, data: List[Dict[str, Any]], session_id: str = None) -> Dict[str, Any]:
    """创建初始状态，确保所有数据已清理"""
    cleaned_data = convert_numpy_types(data)

    return {
        "question": str(question),
        "data_set": cleaned_data,
        "transactions_df": None,
        "planning_step": 0,
        "plan_history": [],
        "outline_draft": None,
        "outline_version": 0,
        "metrics_requirements": [],
        "computed_metrics": {},
        "metrics_cache": {},
        "pending_metric_ids": [],
        "failed_metric_attempts": {},
        "report_draft": {},
        "is_complete": False,
        "completeness_score": 0.0,
        "messages": [],
        "current_node": "start",
        "session_id": str(session_id) if session_id else "default_session",
        "next_route": "planning_node",
        "outline_ready": False,
        "metrics_ready": False,
        "last_decision": "init"
    }


# ============= 状态定义 =============

class AgentState(TypedDict):
    # === 输入层 ===
    question: str
    data_set: List[Dict[str, Any]]
    transactions_df: Optional[Any]

    # === 规划层 ===
    planning_step: int
    plan_history: List[str]

    # === 大纲层 ===
    outline_draft: Optional[ReportOutline]
    outline_version: int

    # === 指标层 ===
    metrics_requirements: List[MetricRequirement]
    computed_metrics: Dict[str, Any]
    metrics_cache: Dict[str, Any]
    pending_metric_ids: List[str]
    failed_metric_attempts: Dict[str, int]

    # === 结果层 ===
    report_draft: Dict[str, Any]
    is_complete: bool
    completeness_score: float

    # === 对话历史 ===
    messages: List[BaseMessage]
    current_node: str
    session_id: str
    next_route: str
    outline_ready: bool
    metrics_ready: bool
    last_decision: str