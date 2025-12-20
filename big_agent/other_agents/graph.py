from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from llmops.agents.state import AgentState, convert_numpy_types
from llmops.agents.planning_agent import planning_node
from llmops.agents.outline_agent import outline_node
from llmops.agents.metrics_agent import metrics_node


def create_report_generation_graph():
    """构建报告生成图"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("planning_node", planning_node)
    workflow.add_node("outline_generator", outline_node)
    workflow.add_node("metrics_calculator", metrics_node)
    workflow.add_node("report_compiler", compile_final_report)
    workflow.add_node("clarify_node", handle_clarification)

    # 设置入口
    workflow.add_edge(START, "planning_node")

    # 条件边：根据规划节点返回的状态路由
    workflow.add_conditional_edges(
        "planning_node",
        route_from_planning,
        {
            "outline_generator": "outline_generator",
            "metrics_calculator": "metrics_calculator",
            "report_compiler": "report_compiler",
            "clarify_node": "clarify_node",
            "planning_node": "planning_node",  # 继续循环
            "END": END
        }
    )

    # 返回规划节点重新决策
    workflow.add_edge("outline_generator", "planning_node")
    workflow.add_edge("metrics_calculator", "planning_node")
    workflow.add_edge("clarify_node", "planning_node")

    # 报告编译后结束
    workflow.add_edge("report_compiler", END)

    # 编译图
    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[],
        interrupt_after=[]
    )


def route_from_planning(state: AgentState) -> str:
    """
    从规划节点路由到下一个节点
    返回目标节点名称
    """
    print(f"\n🔍 [路由决策] 步骤={state['planning_step']}, "
          f"大纲版本={state['outline_version']}, "
          f"大纲已生成={state.get('outline_draft') is not None}, "
          f"指标需求={len(state.get('metrics_requirements', []))}, "
          f"已计算={len(state.get('computed_metrics', {}))}")

    # 新增：防止无限循环
    if state['planning_step'] > 50:
        print("⚠️ 规划步骤超过50次，强制终止并生成报告")
        return "report_compiler"

    # 如果大纲为空 → 生成大纲
    if not state.get("outline_draft"):
        print("→ 路由到 outline_generator（大纲为空）")
        return "outline_generator"

    # 如果指标需求为空 → 重新生成大纲
    if not state.get("metrics_requirements"):
        print("→ 路由到 outline_generator（指标需求为空）")
        return "outline_generator"

    # 计算覆盖率
    required = len(state["metrics_requirements"])
    computed = len(state["computed_metrics"])
    coverage = computed / required if required > 0 else 0

    print(f"  指标覆盖率 = {computed}/{required} = {coverage:.2%}")

    # 新增：如果规划步骤过多且覆盖率超过50%，强制生成报告
    if state['planning_step'] > 30 and coverage > 0.5:
        print(f"→ 路由到 report_compiler（步骤过多，强制终止，覆盖率={coverage:.2%}）")
        return "report_compiler"

    # 如果覆盖率 < 80% → 计算指标
    if coverage < 0.8:
        print(f"→ 路由到 metrics_calculator（覆盖率={coverage:.2%} < 80%）")
        return "metrics_calculator"

    # 如果覆盖率 ≥ 80% → 生成报告
    print(f"→ 路由到 report_compiler（覆盖率={coverage:.2%} ≥ 80%）")
    return "report_compiler"


def compile_final_report(state: AgentState) -> AgentState:
    """报告编译节点：整合所有结果"""

    # 关键修复：将Pydantic模型转换为字典
    outline = state["outline_draft"]
    if hasattr(outline, 'dict'):
        outline_dict = outline.dict()
    else:
        outline_dict = outline

    metrics = state["computed_metrics"]

    # 按章节组织内容
    sections = []
    for section in outline_dict["sections"]:
        section_metrics = {
            mid: metrics.get(mid, "数据缺失")
            for mid in section["metrics_needed"]
        }
        sections.append({
            "title": section["title"],
            "description": section["description"],
            "metrics": section_metrics
        })

    final_report = {
        "title": outline_dict["report_title"],
        "sections": sections,
        "summary": {
            "total_metrics": len(metrics),
            "required_metrics": len(outline_dict["global_metrics"]),
            "coverage_rate": float(state["completeness_score"]),
            "planning_iterations": int(state["planning_step"])
        }
    }

    result_state = {
        **state,
        "answer": final_report,
        "status": "success",
        "messages": state["messages"] + [("ai", f"🎉 报告生成完成：{outline_dict['report_title']}")]
    }

    # 关键修复：返回前清理状态
    return convert_numpy_types(result_state)


def handle_clarification(state: AgentState) -> AgentState:
    """澄清处理节点"""
    result_state = {
        **state,
        "status": "clarifying",
        "is_complete": True,
        "answer": "需要更多信息，请明确您的报告需求"
    }

    # 关键修复：返回前清理状态
    return convert_numpy_types(result_state)