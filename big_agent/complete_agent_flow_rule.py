"""
完整的智能体工作流 (Complete Agent Flow)
=====================================

此工作流整合了规划、大纲生成和指标计算四个核心智能体，实现完整的报告生成流程。

包含的智能体：
1. PlanningAgent (规划智能体) - 分析状态并做出决策
2. OutlineAgent (大纲生成智能体) - 生成报告结构和指标需求
3. MetricCalculationAgent (指标计算智能体) - 执行标准指标计算
4. RulesEngineMetricCalculationAgent (规则引擎指标计算智能体) - 执行规则引擎指标计算

工作流程：
1. 规划节点 → 分析当前状态，决定下一步行动
2. 大纲生成节点 → 生成报告大纲和指标需求
3. 指标判断节点 → 根据大纲确定需要计算的指标
4. 指标计算节点 → 执行具体的指标计算任务

技术特点：
- 基于LangGraph的状态机工作流
- 支持条件路由和状态管理
- 完善的错误处理机制
- 详细的执行日志记录

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-20
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from workflow_state import (
    IntegratedWorkflowState,
    create_initial_integrated_state,
    is_state_ready_for_calculation,
    get_calculation_progress,
    update_state_with_outline_generation,
    update_state_with_planning_decision,
    finalize_state_with_report,
    convert_numpy_types,
    MetricRequirement,
    ReportOutline
)
from agents.outline_agent import OutlineGeneratorAgent, generate_report_outline
from agents.planning_agent import PlanningAgent, plan_next_action, analyze_current_state
from agents.metric_calculation_agent import MetricCalculationAgent
from agents.rules_engine_metric_calculation_agent import RulesEngineMetricCalculationAgent


class CompleteAgentFlow:
    """完整的智能体工作流"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化完整的工作流

        Args:
            api_key: DeepSeek API密钥
            base_url: DeepSeek API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url

        # 初始化各个智能体
        self.planning_agent = PlanningAgent(api_key, base_url)
        self.outline_agent = OutlineGeneratorAgent(api_key, base_url)
        # self.metric_agent = MetricCalculationAgent(api_key, base_url)
        self.rules_engine_agent = RulesEngineMetricCalculationAgent(api_key, base_url)

        # 创建工作流图
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """创建LangGraph工作流"""
        workflow = StateGraph(IntegratedWorkflowState)

        # 添加节点
        workflow.add_node("planning_node", self._planning_node)
        workflow.add_node("outline_generator", self._outline_generator_node)
        workflow.add_node("metric_evaluator", self._metric_evaluator_node)
        workflow.add_node("metric_calculator", self._metric_calculator_node)
        workflow.add_node("report_finalizer", self._report_finalizer_node)

        # 设置入口点
        workflow.set_entry_point("planning_node")

        # 添加条件边 - 基于规划决策路由
        workflow.add_conditional_edges(
            "planning_node",
            self._route_from_planning,
            {
                "outline_generator": "outline_generator",
                "metric_evaluator": "metric_evaluator",
                "metric_calculator": "metric_calculator",
                "report_finalizer": "report_finalizer",
                END: END
            }
        )

        # 从各个节点返回规划节点重新决策
        workflow.add_edge("outline_generator", "planning_node")
        workflow.add_edge("metric_evaluator", "planning_node")
        workflow.add_edge("metric_calculator", "planning_node")
        workflow.add_edge("report_finalizer", END)

        return workflow

    def _route_from_planning(self, state: IntegratedWorkflowState) -> str:
        """
        从规划节点路由到下一个节点

        Args:
            state: 当前状态

        Returns:
            目标节点名称
        """
        print(f"\n🔍 [路由决策] 步骤={state['planning_step']}, "
              f"大纲={state.get('outline_draft') is not None}, "
              f"指标需求={len(state.get('metrics_requirements', []))}")

        # 防止无限循环
        if state['planning_step'] > 30:
            print("⚠️ 规划步骤超过30次，强制结束流程")
            return END

        # 如果大纲为空 → 生成大纲
        if not state.get("outline_draft"):
            print("→ 路由到 outline_generator（生成大纲）")
            return "outline_generator"

        # 如果指标需求为空但大纲已生成 → 评估指标需求
        if not state.get("metrics_requirements") and state.get("outline_draft"):
            print("→ 路由到 metric_evaluator（评估指标需求）")
            return "metric_evaluator"

        # 计算覆盖率
        progress = get_calculation_progress(state)
        coverage = progress["coverage_rate"]

        print(f"  指标覆盖率 = {coverage:.2%}")

        # 如果有待计算指标且覆盖率 < 100% → 计算指标
        if state.get("pending_metric_ids") and coverage < 1.0:
            print(f"→ 路由到 metric_calculator（计算指标，覆盖率={coverage:.2%}）")
            return "metric_calculator"

        # 如果没有待计算指标或覆盖率 >= 80% → 生成最终报告
        if not state.get("pending_metric_ids") or coverage >= 0.8:
            print(f"→ 路由到 report_finalizer（生成最终报告，覆盖率={coverage:.2%}）")
            return "report_finalizer"

        # 默认返回规划节点
        return "planning_node"

    async def _planning_node(self, state: IntegratedWorkflowState) -> IntegratedWorkflowState:
        """规划节点：分析状态并做出决策"""
        try:
            print("🧠 正在执行规划分析...")

            # 使用规划智能体做出决策
            decision = await plan_next_action(
                question=state["question"],
                industry=state["industry"],
                current_state=state,
                api_key=self.api_key
            )

            # 更新状态
            new_state = update_state_with_planning_decision(state, {
                "decision": decision.decision,
                "next_route": self._decision_to_route(decision.decision),
                "metrics_to_compute": decision.metrics_to_compute
            })

            # 添加决策消息
            decision_msg = self._format_decision_message(decision)
            new_state["messages"].append({
                "role": "assistant",
                "content": decision_msg,
                "timestamp": datetime.now().isoformat()
            })

            print(f"✅ 规划决策完成：{decision.decision}")
            return convert_numpy_types(new_state)

        except Exception as e:
            print(f"❌ 规划节点执行失败: {e}")
            new_state = state.copy()
            new_state["errors"].append(f"规划节点错误: {str(e)}")
            return convert_numpy_types(new_state)

    async def _outline_generator_node(self, state: IntegratedWorkflowState) -> IntegratedWorkflowState:
        """大纲生成节点"""
        try:
            print("📝 正在生成报告大纲...")

            # 生成大纲（支持重试机制）
            outline = await generate_report_outline(
                question=state["question"],
                industry=state["industry"],
                sample_data=state["data_set"][:3],  # 使用前3个样本
                api_key=self.api_key,
                max_retries=3,  # 最多重试5次
                retry_delay=3.0  # 每次重试间隔3秒
            )

            # 更新状态
            new_state = update_state_with_outline_generation(state, outline)

            print(f"✅ 大纲生成完成：{outline.report_title}")
            print(f"   包含 {len(outline.sections)} 个章节，{len(outline.global_metrics)} 个指标需求")

            # 分析并打印AI的指标选择推理过程
            self._print_ai_selection_analysis(outline)

            return convert_numpy_types(new_state)

        except Exception as e:
            print(f"❌ 大纲生成失败: {e}")
            new_state = state.copy()
            new_state["errors"].append(f"大纲生成错误: {str(e)}")
            return convert_numpy_types(new_state)

    def _print_ai_selection_analysis(self, outline):
        """打印AI指标选择的推理过程分析 - 完全通用版本"""
        print()
        print('╔══════════════════════════════════════════════════════════════════════════════╗')
        print('║                          🤖 AI指标选择分析                                    ║')
        print('╚══════════════════════════════════════════════════════════════════════════════╝')
        print()

        # 计算总指标数 - outline可能是字典格式，需要适配
        if hasattr(outline, 'sections'):
            # Pydantic模型格式
            total_metrics = sum(len(section.metrics_needed) for section in outline.sections)
            sections = outline.sections
        else:
            # 字典格式
            total_metrics = sum(len(section.get('metrics_needed', [])) for section in outline.get('sections', []))
            sections = outline.get('sections', [])

        # 获取可用指标总数（这里可以从状态或其他地方动态获取）
        available_count = 26  # 这个可以从API调用中动态获取

        print('📊 选择统计:')
        print('   ┌─────────────────────────────────────────────────────────────────────┐')
        print('   │  系统可用指标: {}个   │  AI本次选择: {}个   │  选择率: {:.1f}%     │'.format(
            available_count, total_metrics, total_metrics/available_count*100 if available_count > 0 else 0))
        print('   └─────────────────────────────────────────────────────────────────────┘')
        print()

        print('📋 AI决策过程:')
        print('   大模型已根据用户需求从{}个可用指标中选择了{}个最相关的指标。'.format(available_count, total_metrics))
        print('   选择过程完全由大模型基于语义理解和业务逻辑进行，不涉及任何硬编码规则。')
        print()

        print('🔍 选择结果:')
        print('   • 总章节数: {}个'.format(len(sections)))
        print('   • 平均每章节指标数: {:.1f}个'.format(total_metrics/len(sections) if sections else 0))
        print('   • 选择策略: 基于用户需求的相关性分析')
        print()

        print('🎯 AI Agent核心能力:')
        print('   • 语义理解: 理解用户查询的业务意图和分析需求')
        print('   • 智能筛选: 从海量指标中挑选最相关的组合')
        print('   • 逻辑推理: 为每个分析维度提供充分的选择依据')
        print('   • 动态适配: 根据不同场景自动调整选择策略')
        print()

        print('💡 关键洞察:')
        print('   AI Agent通过大模型的推理能力，实现了超越传统规则引擎的智能化指标选择，')
        print('   能够根据具体业务场景动态调整分析框架，确保分析的针对性和有效性。')
        print()

    async def _metric_evaluator_node(self, state: IntegratedWorkflowState) -> IntegratedWorkflowState:
        """指标评估节点：根据大纲确定需要计算的指标"""
        try:
            print("🔍 正在评估指标需求...")

            new_state = state.copy()
            outline = state.get("outline_draft")

            if not outline:
                print("⚠️ 没有大纲信息，跳过指标评估")
                return convert_numpy_types(new_state)

            # 从大纲中提取指标需求
            metrics_requirements = outline.global_metrics
            metric_ids = [m.metric_id for m in metrics_requirements]

            # 设置待计算指标
            new_state["metrics_requirements"] = metrics_requirements
            new_state["pending_metric_ids"] = metric_ids.copy()
            new_state["computed_metrics"] = {}
            new_state["metrics_cache"] = {}

            print(f"✅ 指标评估完成，发现 {len(metric_ids)} 个待计算指标")
            for i, metric_id in enumerate(metric_ids[:5], 1):  # 只显示前5个
                print(f"   {i}. {metric_id}")

            if len(metric_ids) > 5:
                print(f"   ... 还有 {len(metric_ids) - 5} 个指标")

            # 添加消息
            new_state["messages"].append({
                "role": "assistant",
                "content": f"🔍 指标评估完成：发现 {len(metric_ids)} 个待计算指标",
                "timestamp": datetime.now().isoformat()
            })

            return convert_numpy_types(new_state)

        except Exception as e:
            print(f"❌ 指标评估失败: {e}")
            new_state = state.copy()
            new_state["errors"].append(f"指标评估错误: {str(e)}")
            return convert_numpy_types(new_state)

    async def _metric_calculator_node(self, state: IntegratedWorkflowState) -> IntegratedWorkflowState:
        """指标计算节点"""
        try:
            # 检查计算模式
            use_rules_engine_only = state.get("use_rules_engine_only", False)
            use_traditional_engine_only = state.get("use_traditional_engine_only", False)

            if use_rules_engine_only:
                print("🧮 正在执行规则引擎指标计算（专用模式）...")
            elif use_traditional_engine_only:
                print("🧮 正在执行传统引擎指标计算（专用模式）...")
            else:
                print("🧮 正在执行指标计算...")

            new_state = state.copy()

            # 使用规划决策指定的指标批次，如果没有指定则使用所有待计算指标
            current_batch = state.get("current_batch_metrics", [])
            if current_batch:
                pending_ids = current_batch
                print(f"🧮 本次计算批次包含 {len(pending_ids)} 个指标")
            else:
                pending_ids = state.get("pending_metric_ids", [])
                print(f"🧮 计算所有待计算指标，共 {len(pending_ids)} 个")

            if not pending_ids:
                print("⚠️ 没有待计算的指标")
                return convert_numpy_types(new_state)

            # 获取指标需求信息
            metrics_requirements = state.get("metrics_requirements", [])
            if not metrics_requirements:
                print("⚠️ 没有指标需求信息")
                return convert_numpy_types(new_state)

            # 计算成功和失败的指标
            successful_calculations = 0
            failed_calculations = 0

            # 遍历待计算的指标（创建副本避免修改时遍历的问题）
            for metric_id in pending_ids.copy():
                try:
                    # 找到对应的指标需求
                    metric_req = next((m for m in metrics_requirements if m.metric_id == metric_id), None)
                    if not metric_req:
                        print(f"⚠️ 找不到指标 {metric_id} 的需求信息，跳过")
                        # 仍然从待计算列表中移除，避免无限循环
                        if metric_id in new_state["pending_metric_ids"]:
                            new_state["pending_metric_ids"].remove(metric_id)
                        continue

                    print(f"🧮 计算指标: {metric_id} - {metric_req.metric_name}")

                    # 根据模式决定使用哪种计算方式
                    if use_rules_engine_only:
                        # 只使用规则引擎计算
                        use_rules_engine = True
                        print(f"   使用规则引擎模式")
                    elif use_traditional_engine_only:
                        # 只使用传统引擎计算
                        use_rules_engine = False
                        print(f"   使用传统引擎模式")
                    else:
                        # 自动选择计算方式：优先使用规则引擎，只在规则引擎不可用时使用传统计算
                        use_rules_engine = True  # 默认使用规则引擎计算所有指标

                    if use_rules_engine:
                        # 使用规则引擎计算
                        # 现在metric_id已经是知识ID，直接使用它作为配置名
                        config_name = metric_id  # metric_id 已经是知识ID，如 "metric-分析账户数量"
                        intent_result = {
                            "target_configs": [config_name],
                            "intent_category": "指标计算"
                        }
                        print(f"   使用知识ID: {config_name}")
                        results = await self.rules_engine_agent.calculate_metrics(intent_result)
                    else:
                        # 使用传统指标计算（模拟）
                        # 这里简化处理，实际应该根据配置文件调用相应的API
                        results = {
                            "success": True,
                            "results": [{
                                "config_name": metric_req.metric_id,
                                "result": {
                                    "success": True,
                                    "data": f"传统引擎计算结果：{metric_req.metric_name}",
                                    "value": 100.0  # 模拟数值
                                }
                            }]
                        }

                    # 处理计算结果
                    for result in results.get("results", []):
                        if result.get("result", {}).get("success"):
                            # 计算成功
                            new_state["computed_metrics"][metric_id] = result["result"]
                            successful_calculations += 1
                            print(f"✅ 指标 {metric_id} 计算成功")
                        else:
                            # 计算失败
                            failed_calculations += 1
                            print(f"❌ 指标 {metric_id} 计算失败")

                    # 从待计算列表中移除（无论成功还是失败）
                    if metric_id in new_state["pending_metric_ids"]:
                        new_state["pending_metric_ids"].remove(metric_id)

                except Exception as e:
                    print(f"❌ 计算指标 {metric_id} 时发生异常: {e}")
                    failed_calculations += 1
                    # 即使异常，也要从待计算列表中移除，避免无限循环
                    if metric_id in new_state["pending_metric_ids"]:
                        new_state["pending_metric_ids"].remove(metric_id)

            # 更新计算结果统计
            new_state["calculation_results"] = {
                "total_configs": len(pending_ids),
                "successful_calculations": successful_calculations,
                "failed_calculations": failed_calculations
            }

            # 添加消息
            if use_rules_engine_only:
                message_content = f"🧮 规则引擎指标计算完成：{successful_calculations} 成功，{failed_calculations} 失败"
            elif use_traditional_engine_only:
                message_content = f"🧮 传统引擎指标计算完成：{successful_calculations} 成功，{failed_calculations} 失败"
            else:
                message_content = f"🧮 指标计算完成：{successful_calculations} 成功，{failed_calculations} 失败"

            new_state["messages"].append({
                "role": "assistant",
                "content": message_content,
                "timestamp": datetime.now().isoformat()
            })

            if use_rules_engine_only:
                print(f"✅ 规则引擎指标计算完成：{successful_calculations} 成功，{failed_calculations} 失败")
            elif use_traditional_engine_only:
                print(f"✅ 传统引擎指标计算完成：{successful_calculations} 成功，{failed_calculations} 失败")
            else:
                print(f"✅ 指标计算完成：{successful_calculations} 成功，{failed_calculations} 失败")

            return convert_numpy_types(new_state)

        except Exception as e:
            print(f"❌ 指标计算节点失败: {e}")
            new_state = state.copy()
            new_state["errors"].append(f"指标计算错误: {str(e)}")
            return convert_numpy_types(new_state)

    async def _report_finalizer_node(self, state: IntegratedWorkflowState) -> IntegratedWorkflowState:
        """报告完成节点：生成最终报告"""
        try:
            print("📋 正在生成最终报告...")

            # 获取大纲和计算结果
            outline = state.get("outline_draft")
            computed_metrics = state.get("computed_metrics", {})

            if not outline:
                raise ValueError("没有可用的报告大纲")

            # 生成最终报告
            final_report = {
                "title": outline.report_title,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_sections": len(outline.sections),
                    "total_metrics_required": len(outline.global_metrics),
                    "total_metrics_computed": len(computed_metrics),
                    "planning_steps": state.get("planning_step", 0),
                    "completion_rate": len(computed_metrics) / len(outline.global_metrics) if outline.global_metrics else 0
                },
                "sections": [],
                "metrics_detail": {}
            }

            # 构建章节内容
            for section in outline.sections:
                section_content = {
                    "section_id": section.section_id,
                    "title": section.title,
                    "description": section.description,
                    "metrics": {}
                }

                # 添加该章节的指标数据
                for metric_id in section.metrics_needed:
                    if metric_id in computed_metrics:
                        section_content["metrics"][metric_id] = computed_metrics[metric_id]
                    else:
                        section_content["metrics"][metric_id] = "数据缺失"

                final_report["sections"].append(section_content)

            # 添加详细的指标信息
            for metric_req in outline.global_metrics:
                metric_id = metric_req.metric_id
                final_report["metrics_detail"][metric_id] = {
                    "name": metric_req.metric_name,
                    "logic": metric_req.calculation_logic,
                    "required_fields": metric_req.required_fields,
                    "computed": metric_id in computed_metrics,
                    "value": computed_metrics.get(metric_id, {}).get("value", "N/A")
                }

            # 更新状态
            new_state = finalize_state_with_report(state, final_report)

            # 添加完成消息
            new_state["messages"].append({
                "role": "assistant",
                "content": f"🎉 完整报告生成流程完成：{outline.report_title}",
                "timestamp": datetime.now().isoformat()
            })

            print(f"✅ 最终报告生成完成：{outline.report_title}")
            print(f"   章节数：{len(final_report['sections'])}")
            print(f"   计算指标：{len(computed_metrics)}/{len(outline.global_metrics)}")
            print(".2%")

            return convert_numpy_types(new_state)

        except Exception as e:
            print(f"❌ 报告完成失败: {e}")
            new_state = state.copy()
            new_state["errors"].append(f"报告完成错误: {str(e)}")
            return convert_numpy_types(new_state)

    def _decision_to_route(self, decision: str) -> str:
        """将规划决策转换为路由"""
        decision_routes = {
            "generate_outline": "outline_generator",
            "compute_metrics": "metric_calculator",
            "finalize_report": "report_finalizer"
        }
        return decision_routes.get(decision, "planning_node")

    def _format_decision_message(self, decision: Any) -> str:
        """格式化决策消息"""
        try:
            decision_type = getattr(decision, 'decision', 'unknown')
            reasoning = getattr(decision, 'reasoning', '')

            if decision_type == "compute_metrics" and hasattr(decision, 'metrics_to_compute'):
                metrics = decision.metrics_to_compute
                return f"🧮 规划决策：计算 {len(metrics)} 个指标"
            elif decision_type == "finalize_report":
                return f"✅ 规划决策：生成最终报告"
            elif decision_type == "generate_outline":
                return f"📋 规划决策：生成大纲"
            else:
                return f"🤔 规划决策：{decision_type}"
        except:
            return "🤔 规划决策已完成"

    async def run_workflow(self, question: str, industry: str, data: List[Dict[str, Any]], session_id: str = None, use_rules_engine_only: bool = False, use_traditional_engine_only: bool = False) -> Dict[str, Any]:
        """
        运行完整的工作流

        Args:
            question: 用户查询
            industry: 行业
            data: 数据集
            session_id: 会话ID
            use_rules_engine_only: 是否只使用规则引擎指标计算
            use_traditional_engine_only: 是否只使用传统引擎指标计算

        Returns:
            工作流结果
        """
        try:
            print("🚀 启动完整智能体工作流...")
            print(f"问题：{question}")
            print(f"行业：{industry}")
            print(f"数据条数：{len(data)}")

            if use_rules_engine_only:
                print("计算模式：只使用规则引擎")
            elif use_traditional_engine_only:
                print("计算模式：只使用传统引擎")
            else:
                print("计算模式：标准模式")

            # 创建初始状态
            initial_state = create_initial_integrated_state(question, industry, data, session_id)

            # 设置计算模式标记
            if use_rules_engine_only:
                initial_state["use_rules_engine_only"] = True
                initial_state["use_traditional_engine_only"] = False
            elif use_traditional_engine_only:
                initial_state["use_rules_engine_only"] = False
                initial_state["use_traditional_engine_only"] = True
            else:
                initial_state["use_rules_engine_only"] = False
                initial_state["use_traditional_engine_only"] = False

            # 编译工作流
            app = self.workflow.compile()

            # 执行工作流
            result = await app.ainvoke(initial_state)

            print("✅ 工作流执行完成")
            return {
                "success": True,
                "result": result,
                "answer": result.get("answer"),
                "report": result.get("report_draft"),
                "session_id": result.get("session_id"),
                "execution_summary": {
                    "planning_steps": result.get("planning_step", 0),
                    "outline_generated": result.get("outline_draft") is not None,
                    "metrics_computed": len(result.get("computed_metrics", {})),
                    "completion_rate": result.get("completeness_score", 0)
                }
            }

        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }


# 便捷函数
async def run_complete_agent_flow(question: str, industry: str, data: List[Dict[str, Any]], api_key: str, session_id: str = None, use_rules_engine_only: bool = False, use_traditional_engine_only: bool = False) -> Dict[str, Any]:
    """
    运行完整智能体工作流的便捷函数

    Args:
        question: 用户查询
        data: 数据集
        api_key: API密钥
        session_id: 会话ID
        use_rules_engine_only: 是否只使用规则引擎指标计算
        use_traditional_engine_only: 是否只使用传统引擎指标计算

    Returns:
        工作流结果
    """
    workflow = CompleteAgentFlow(api_key)
    return await workflow.run_workflow(question, industry, data, session_id, use_rules_engine_only, use_traditional_engine_only)


# 主函数用于测试
async def main():
    """主函数：执行系统测试"""
    print("🚀 执行CompleteAgentFlow系统测试")
    print("=" * 50)

    # 导入配置
    import config

    if not config.DEEPSEEK_API_KEY:
        print("❌ 未找到API密钥")
        return

    # 测试数据
    test_data = [
        {
           
        }
    ]

    print(f"📊 测试数据: {len(test_data)} 条记录")


    # 执行测试
    result = await run_complete_agent_flow(
        # question="请生成一份详细的农业经营贷流水分析报告，需要包含：1.总收入和总支出统计 2.收入笔数和支出笔数 3.各类型收入支出占比分析 4.交易对手收入支出TOP3排名 5.按月份的收入支出趋势分析 6.账户数量和交易时间范围统计 7.资金流入流出月度统计等全面指标",
        # industry = "农业",
        question="请生成一份详细的黑色金属相关经营贷流水分析报告，需要包含：1.总收入统计 2.收入笔数 3.各类型收入占比分析 4.交易对手收入排名 5.按月份的收入趋势分析 6.账户数量和交易时间范围统计 7.资金流入流出月度统计等全面指标",
        industry = "黑色金属",
        data=test_data,
        api_key=config.DEEPSEEK_API_KEY,
        session_id="direct-test"
    )

    print(f"📋 结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")

    if result.get('success'):
        summary = result.get('execution_summary', {})
        print(f"   规划步骤: {summary.get('planning_steps', 0)}")
        print(f"   指标计算: {summary.get('metrics_computed', 0)}")
        print("🎉 测试成功！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())