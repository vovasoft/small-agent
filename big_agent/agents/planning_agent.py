"""
规划Agent (Planning Agent)
=========================

此Agent负责分析当前状态并做出智能决策，决定下一步行动。

核心功能：
1. 状态评估：分析大纲、指标计算进度和完整性
2. 决策制定：决定生成大纲、计算指标、完成报告或澄清需求
3. 优先级排序：确定最关键的任务和指标
4. 流程控制：管理整个报告生成工作流的执行顺序

决策逻辑：
- 大纲为空 → 生成大纲
- 指标覆盖率 < 80% → 计算指标
- 指标覆盖率 ≥ 80% → 生成报告
- 需求模糊 → 澄清需求

技术实现：
- 使用LangChain和结构化输出
- 支持异步处理
- 智能状态评估
- 灵活的决策机制

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-20
"""

from typing import List, Dict, Optional, Any, Union
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import json
import os
from datetime import datetime


# 数据模型定义
class ActionItem(BaseModel):
    """动作项定义"""
    action: str = Field(description="动作名称")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="动作参数")


class ClarificationRequest(BaseModel):
    """澄清请求结构化格式"""
    questions: List[str] = Field(description="需要澄清的问题列表")
    missing_fields: List[str] = Field(default_factory=list, description="缺少的字段或信息")


class PlanningDecision(BaseModel):
    """规划决策输出"""
    decision: str = Field(
        description="决策类型: generate_outline, compute_metrics, finalize_report, clarify_requirements"
    )
    reasoning: str = Field(description="详细推理过程")
    next_actions: List[Union[str, ActionItem]] = Field(
        default_factory=list,
        description="下一步动作列表"
    )
    metrics_to_compute: List[str] = Field(
        default_factory=list,
        description="待计算指标ID列表（如 ['total_income', 'avg_balance']）"
    )
    priority_metrics: List[str] = Field(
        default_factory=list,
        description="优先级高的指标ID"
    )
    additional_requirements: Optional[
        Union[Dict[str, Any], List[Any], ClarificationRequest]
    ] = Field(default=None, description="额外需求或澄清信息")


def normalize_requirements(req: Any) -> Optional[Dict[str, Any]]:
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


class PlanningAgent:
    """规划智能体：负责状态分析和决策制定"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化规划Agent

        Args:
            api_key: DeepSeek API密钥
            base_url: DeepSeek API基础URL
        """
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1
        )

        # 初始化API调用跟踪
        self.api_calls = []

    def create_planning_prompt(self) -> ChatPromptTemplate:
        """创建规划提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """你是报告规划总控智能体，核心职责是精准分析当前状态并决定下一步行动。

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

### 指标计算策略
- 优先计算上述8个核心指标

- 确保指标ID与大纲定义完全一致
- 计算失败的指标可以重试最多3次

### 输出字段说明
- decision: 决策字符串
- reasoning: 决策原因说明
- next_actions: 动作列表（可选）
- metrics_to_compute: 待计算指标ID列表（决策为compute_metrics时必须提供）
- priority_metrics: 优先级指标列表（前2-3个最重要的指标）
- additional_requirements: 额外需求（可选）

必须输出有效的JSON格式！"""),

            MessagesPlaceholder("messages"),

            ("user", "报告需求：{question}\n\n请输出决策结果。")
        ])

    async def make_decision(self, question: str, current_state: Dict[str, Any]) -> PlanningDecision:
        """
        根据当前状态做出规划决策

        Args:
            question: 用户查询
            current_state: 当前状态信息

        Returns:
            规划决策结果
        """
        planner = self.create_planning_prompt() | self.llm

        # 构建状态评估上下文
        status_info = self._build_status_context(current_state)

        # 记录大模型输入
        print("========================================")
        print("[AGENT] PlanningAgent (规划Agent)")
        print("[MODEL_INPUT] PlanningAgent:")
        print(f"[CONTEXT] 基于当前状态做出规划决策")
        print(f"Question: {question}")
        print(f"Status info: {status_info}")
        print("========================================")

        # 执行规划
        start_time = datetime.now()
        response = await planner.ainvoke({
            "question": question,
            "messages": [("system", status_info)]
        })
        end_time = datetime.now()

        # 解析JSON响应
        try:
            # 从响应中提取JSON内容
            content = response.content if hasattr(response, 'content') else str(response)
            # 尝试找到JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                decision_data = json.loads(json_str)

                # 预处理 additional_requirements 字段
                if "additional_requirements" in decision_data:
                    req = decision_data["additional_requirements"]
                    if isinstance(req, str):
                        # 如果是字符串，尝试将其转换为合适的格式
                        if req.strip():
                            # 将字符串包装为字典格式
                            decision_data["additional_requirements"] = {"raw_content": req}
                        else:
                            # 空字符串设为 None
                            decision_data["additional_requirements"] = None
                    elif isinstance(req, list):
                        # 如果是列表，转换为字典格式
                        decision_data["additional_requirements"] = {
                            "questions": [str(item) for item in req],
                            "missing_fields": []
                        }
                    # 如果已经是 dict 或其他允许的类型，保持不变

                decision = PlanningDecision(**decision_data)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            print(f"解析规划决策响应失败: {e}，使用默认决策")
            # 返回默认决策
            decision = PlanningDecision(
                decision="generate_outline",
                reasoning="解析响应失败，使用默认决策生成大纲",
                next_actions=["生成报告大纲"],
                metrics_to_compute=[],
                priority_metrics=[]
            )

        # 记录API调用结果
        content = response.content if hasattr(response, 'content') else str(response)
        call_id = f"api_mll_规划决策_{"{:.2f}".format((end_time - start_time).total_seconds())}"
        api_call_info = {
            "call_id": call_id,
            "timestamp": end_time.isoformat(),
            "agent": "PlanningAgent",
            "model": "deepseek-chat",
            "request": {
                "question": question,
                "status_info": status_info,
                "start_time": start_time.isoformat()
            },
            "response": {
                "content": content,
                "decision": decision.dict() if hasattr(decision, 'dict') else decision,
                "end_time": end_time.isoformat(),
                "duration": (end_time - start_time).total_seconds()
            },
            "success": True
        }
        self.api_calls.append(api_call_info)

        # 保存API结果到文件
        api_results_dir = "api_results"
        os.makedirs(api_results_dir, exist_ok=True)
        filename = f"{call_id}.json"
        filepath = os.path.join(api_results_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(api_call_info, f, ensure_ascii=False, indent=2)
            print(f"[API_RESULT] 保存API结果文件: {filepath}")
        except Exception as e:
            print(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

        # 记录大模型输出
        print(f"[MODEL_OUTPUT] PlanningAgent: {json.dumps(decision.dict() if hasattr(decision, 'dict') else decision, ensure_ascii=False)}")
        print("========================================")

        return decision

    def _build_status_context(self, state: Dict[str, Any]) -> str:
        """构建状态评估上下文"""
        required_count = len(state.get("metrics_requirements", []))
        computed_count = len(state.get("computed_metrics", {}))
        coverage = computed_count / required_count if required_count > 0 else 0

        # 计算失败统计
        failed_attempts = state.get("failed_metric_attempts", {})
        pending_ids = state.get("pending_metric_ids", [])

        # 过滤掉失败次数过多的指标
        max_retry = 3
        filtered_pending_ids = [
            mid for mid in pending_ids
            if failed_attempts.get(mid, 0) < max_retry
        ]

        return f"""当前状态评估：
- 规划步骤: {state.get('planning_step', 0)}
- 大纲版本: {state.get('outline_version', 0)}
- 大纲草稿存在: {state.get('outline_draft') is not None}
- 指标需求总数: {required_count}
- 已计算指标数: {computed_count}
- 指标覆盖率: {coverage:.2%}
- 待计算指标数: {len(pending_ids)}
- 有效待计算指标数: {len(filtered_pending_ids)}
- 失败尝试记录: {failed_attempts}

建议下一步: {"计算指标" if coverage < 0.8 else "生成报告"}"""


def analyze_current_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析当前状态，返回关键信息

    Args:
        state: 当前状态

    Returns:
        状态分析结果
    """
    required_metrics = state.get("metrics_requirements", [])
    computed_metrics = state.get("computed_metrics", {})

    # 计算覆盖率
    required_count = len(required_metrics)
    computed_count = len(computed_metrics)
    coverage = computed_count / required_count if required_count > 0 else 0

    # 找出未计算的指标
    computed_ids = set(computed_metrics.keys())
    pending_metrics = [
        m for m in required_metrics
        if m.metric_id not in computed_ids
    ]

    # 检查失败次数
    failed_attempts = state.get("failed_metric_attempts", {})
    max_retry = 3
    valid_pending_metrics = [
        m for m in pending_metrics
        if failed_attempts.get(m.metric_id, 0) < max_retry
    ]

    return {
        "has_outline": state.get("outline_draft") is not None,
        "required_count": required_count,
        "computed_count": computed_count,
        "coverage": coverage,
        "pending_metrics": pending_metrics,
        "valid_pending_metrics": valid_pending_metrics,
        "pending_ids": [m.metric_id for m in pending_metrics],
        "valid_pending_ids": [m.metric_id for m in valid_pending_metrics],
        "planning_step": state.get("planning_step", 0),
        "outline_version": state.get("outline_version", 0)
    }


async def plan_next_action(question: str, current_state: Dict[str, Any], api_key: str) -> PlanningDecision:
    """
    规划下一步行动的主函数

    Args:
        question: 用户查询
        current_state: 当前状态
        api_key: API密钥

    Returns:
        规划决策结果
    """
    agent = PlanningAgent(api_key)

    try:
        decision = await agent.make_decision(question, current_state)

        print(f"\n🧠 规划决策：{decision.decision}")
        print(f"   推理：{decision.reasoning[:100]}...")

        if decision.metrics_to_compute:
            print(f"   待计算指标：{decision.metrics_to_compute}")

        return decision

    except Exception as e:
        print(f"⚠️ 规划决策出错: {e}，使用默认决策")

        # 基于状态分析的默认决策
        state_analysis = analyze_current_state(current_state)

        if not state_analysis["has_outline"]:
            default_decision = PlanningDecision(
                decision="generate_outline",
                reasoning="大纲不存在，需要先生成大纲",
                next_actions=["生成报告大纲"],
                metrics_to_compute=[],
                priority_metrics=[]
            )
        elif state_analysis["coverage"] < 0.8 and state_analysis["valid_pending_metrics"]:
            # 计算指标
            metrics_to_compute = state_analysis["valid_pending_ids"][:5]  # 最多计算5个
            default_decision = PlanningDecision(
                decision="compute_metrics",
                reasoning=f"指标覆盖率{state_analysis['coverage']:.1%}，需要计算更多指标",
                next_actions=[f"计算指标: {', '.join(metrics_to_compute)}"],
                metrics_to_compute=metrics_to_compute,
                priority_metrics=metrics_to_compute[:2]  # 前2个为优先级
            )
        elif state_analysis["valid_pending_ids"]:
            # 还有指标但都失败了，生成报告
            default_decision = PlanningDecision(
                decision="finalize_report",
                reasoning="部分指标计算失败，但已有足够信息生成报告",
                next_actions=["生成最终报告"],
                metrics_to_compute=[],
                priority_metrics=[]
            )
        else:
            # 信息充足，生成报告
            default_decision = PlanningDecision(
                decision="finalize_report",
                reasoning="所有必要指标已计算完成",
                next_actions=["生成最终报告"],
                metrics_to_compute=[],
                priority_metrics=[]
            )

        return default_decision