"""
Big Agent LangGraph 工作流引擎
=============================

这是一个基于LangGraph的多Agent协作系统，实现了智能农业指标计算的完整工作流。

核心功能：
1. 意图识别 (IntentRecognitionAgent)
   - 分析用户自然语言查询
   - 识别计算意图和所需指标类型
   - 匹配对应的配置文件

2. 指标计算 (MetricCalculationAgent)
   - 根据意图识别结果选择配置文件
   - 调用相应的API进行指标计算
   - 处理计算结果和错误情况

3. 知识沉淀 (KnowledgePrecipitationAgent)
   - 分析完整的计算过程和结果
   - 生成结构化的知识文档
   - 保存到知识库以供后续复用

工作流架构：
- 使用LangGraph的状态图管理Agent间的协作
- 每个节点代表一个Agent的执行步骤
- 边表示Agent间的依赖关系和数据流转

技术特点：
- 异步执行：支持并发处理提高效率
- 错误处理：完善的异常捕获和恢复机制
- 日志记录：详细的执行过程记录
- 配置驱动：灵活的JSON配置文件系统

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

import os
import asyncio
from typing import Dict, Any, TypedDict, Optional, List
from datetime import datetime

# LangGraph 核心组件
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# Big Agent 各模块导入
from agents.intent_recognition_agent import IntentRecognitionAgent
from agents.metric_calculation_agent import MetricCalculationAgent
from agents.rules_engine_metric_calculation_agent import RulesEngineMetricCalculationAgent
from agents.knowledge_precipitation_agent import KnowledgePrecipitationAgent


class WorkflowState(TypedDict):
    """工作流状态定义"""
    user_input: str
    intent_result: Optional[Dict[str, Any]]
    calculation_results: Optional[Dict[str, Any]]
    knowledge_result: Optional[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    errors: List[str]
    start_time: str
    end_time: Optional[str]
    api_result: Dict[str, Any]  # 存储所有API调用结果


class BigAgentWorkflow:
    """Big Agent完整工作流"""

    def __init__(self, deepseek_api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化工作流

        Args:
            deepseek_api_key: DeepSeek API密钥
            base_url: DeepSeek API基础URL
        """
        self.api_key = deepseek_api_key
        self.base_url = base_url

        # 初始化各个Agent
        self.intent_agent = IntentRecognitionAgent(deepseek_api_key, base_url)
        self.calculation_agent = MetricCalculationAgent(deepseek_api_key, base_url)
        self.rules_engine_agent = RulesEngineMetricCalculationAgent(deepseek_api_key, base_url)
        self.knowledge_agent = KnowledgePrecipitationAgent(deepseek_api_key, base_url)

        # 创建工作流图
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """创建LangGraph工作流"""
        # 创建状态图
        workflow = StateGraph(WorkflowState)

        # 添加节点
        workflow.add_node("intent_recognition", self._intent_recognition_node)
        workflow.add_node("metric_calculation", self._metric_calculation_node)
        workflow.add_node("knowledge_precipitation", self._knowledge_precipitation_node)
        workflow.add_node("error_handler", self._error_handler_node)

        # 设置入口点
        workflow.set_entry_point("intent_recognition")

        # 添加边 - 简化为线性执行
        workflow.add_edge("intent_recognition", "metric_calculation")
        workflow.add_edge("metric_calculation", "knowledge_precipitation")
        workflow.add_edge("knowledge_precipitation", END)

        return workflow

    async def _intent_recognition_node(self, state: WorkflowState) -> Dict[str, Any]:
        """意图识别节点"""
        try:
            print("正在执行意图识别...")

            # 创建新的状态副本
            new_state = state.copy()

            # 记录开始时间
            new_state["start_time"] = datetime.now().isoformat()

            # 初始化消息列表如果不存在
            if "messages" not in new_state:
                new_state["messages"] = []

            # 添加用户消息到对话历史
            new_state["messages"] = new_state["messages"] + [{
                "role": "user",
                "content": new_state["user_input"],
                "timestamp": datetime.now().isoformat()
            }]

            # 执行意图识别
            intent_result = await self.intent_agent.recognize_intent(new_state["user_input"])

            # 将API调用结果保存到api_result
            for api_call in self.intent_agent.api_calls:
                new_state["api_result"][api_call["call_id"]] = api_call

            # 添加AI响应到对话历史
            new_state["messages"] = new_state["messages"] + [{
                "role": "assistant",
                "content": f"意图识别完成：类别-{intent_result.get('intent_category', 'unknown')}，"
                          f"置信度-{intent_result.get('confidence', 0):.2f}",
                "timestamp": datetime.now().isoformat()
            }]

            # 更新状态
            new_state["intent_result"] = intent_result

            print(f"意图识别完成：{intent_result.get('intent_category', 'unknown')}")

            return new_state

        except Exception as e:
            error_msg = f"意图识别节点错误: {str(e)}"
            print(error_msg)

            new_state = state.copy()
            if "errors" not in new_state:
                new_state["errors"] = []
            new_state["errors"] = new_state["errors"] + [error_msg]

            return new_state

    async def _metric_calculation_node(self, state: WorkflowState) -> Dict[str, Any]:
        """指标计算节点"""
        try:
            print("正在执行指标计算...")

            new_state = state.copy()
            intent_result = new_state.get("intent_result")
            if not intent_result:
                raise ValueError("没有意图识别结果")

            # 根据计算模式选择对应的Agent
            calculation_mode = intent_result.get("calculation_mode", "standard")
            print(f"使用计算模式: {calculation_mode}")

            if calculation_mode == "rules_engine":
                # 使用规则引擎计算Agent
                calculation_results = await self.rules_engine_agent.calculate_metrics(intent_result)
                api_calls_source = self.rules_engine_agent.api_calls
                agent_name = "规则引擎指标计算"
            else:
                # 使用标准指标计算Agent
                calculation_results = await self.calculation_agent.calculate_metrics(intent_result)
                api_calls_source = self.calculation_agent.api_calls
                agent_name = "标准指标计算"

            # 将API调用结果保存到api_result
            for api_call in api_calls_source:
                new_state["api_result"][api_call["call_id"]] = api_call

            # 添加到对话历史
            successful_count = calculation_results.get("successful_calculations", 0)
            total_count = calculation_results.get("total_configs", 0)

            new_state["messages"] = new_state["messages"] + [{
                "role": "assistant",
                "content": f"{agent_name}完成：成功 {successful_count}/{total_count} 个配置",
                "timestamp": datetime.now().isoformat()
            }]

            # 更新状态
            new_state["calculation_results"] = calculation_results

            print(f"{agent_name}完成：{successful_count}/{total_count} 成功")

            return new_state

        except Exception as e:
            error_msg = f"指标计算节点错误: {str(e)}"
            print(error_msg)

            new_state = state.copy()
            new_state["errors"] = new_state["errors"] + [error_msg]
            return new_state

    async def _knowledge_precipitation_node(self, state: WorkflowState) -> Dict[str, Any]:
        """知识沉淀节点"""
        try:
            print("正在执行知识沉淀...")

            new_state = state.copy()

            # 准备工作流数据用于知识沉淀
            workflow_data = {
                "user_input": new_state["user_input"],
                "intent_result": new_state.get("intent_result"),
                "calculation_results": new_state.get("calculation_results"),
                "messages": new_state["messages"],
                "errors": new_state["errors"],
                "start_time": new_state["start_time"],
                "end_time": datetime.now().isoformat()
            }

            # 执行知识沉淀
            knowledge_result = await self.knowledge_agent.precipitate_knowledge(workflow_data)

            # 将API调用结果保存到api_result
            for api_call in self.knowledge_agent.api_calls:
                new_state["api_result"][api_call["call_id"]] = api_call

            # 添加到对话历史
            new_state["messages"] = new_state["messages"] + [{
                "role": "assistant",
                "content": "知识沉淀完成，已生成知识文档",
                "timestamp": datetime.now().isoformat()
            }]

            # 更新状态
            new_state["knowledge_result"] = knowledge_result
            new_state["end_time"] = workflow_data["end_time"]

            print("知识沉淀完成")

            return new_state

        except Exception as e:
            error_msg = f"知识沉淀节点错误: {str(e)}"
            print(error_msg)

            new_state = state.copy()
            new_state["errors"] = new_state["errors"] + [error_msg]
            return new_state

    async def _error_handler_node(self, state: WorkflowState) -> Dict[str, Any]:
        """错误处理节点"""
        try:
            print("正在执行错误处理...")

            new_state = state.copy()

            # 汇总所有错误
            all_errors = new_state.get("errors", [])
            error_summary = "\n".join(f"- {error}" for error in all_errors)

            # 添加错误处理消息
            new_state["messages"] = new_state["messages"] + [{
                "role": "assistant",
                "content": f"工作流执行中遇到错误：\n{error_summary}",
                "timestamp": datetime.now().isoformat()
            }]

            # 设置结束时间
            new_state["end_time"] = datetime.now().isoformat()

            print("错误处理完成")

            return new_state

        except Exception as e:
            error_msg = f"错误处理节点异常: {str(e)}"
            print(error_msg)
            return state.copy()

    def _should_continue_after_intent(self, state: WorkflowState) -> str:
        """判断意图识别后是否继续"""
        intent_result = state.get("intent_result")
        errors = state.get("errors", [])

        # 如果有严重错误或意图识别失败，不继续
        if errors or not intent_result or intent_result.get("confidence", 0) < 0.3:
            return "error"

        return "continue"

    def _should_continue_after_calculation(self, state: WorkflowState) -> str:
        """判断指标计算后是否继续"""
        calculation_results = state.get("calculation_results")
        errors = state.get("errors", [])

        # 如果有严重错误，不继续
        if errors:
            return "error"

        # 如果计算完全失败，也标记为错误
        if calculation_results and calculation_results.get("successful_calculations", 0) == 0:
            return "error"

        return "continue"

    async def run_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        运行完整的工作流

        Args:
            user_input: 用户输入

        Returns:
            工作流执行结果
        """
        try:
            # 初始化状态
            initial_state: WorkflowState = {
                "user_input": user_input,
                "intent_result": None,
                "calculation_results": None,
                "knowledge_result": None,
                "messages": [],
                "errors": [],
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "api_result": {}
            }

            # 编译并运行工作流
            app = self.workflow.compile()

            # 执行工作流
            result = await app.ainvoke(initial_state)

            print("工作流执行完成")

            return {
                "success": len(result.get("errors", [])) == 0,
                "result": result,
                "execution_time": self._calculate_execution_time(result)
            }

        except Exception as e:
            error_msg = f"工作流执行失败: {str(e)}"
            print(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "result": None
            }

    def _calculate_execution_time(self, result: WorkflowState) -> Optional[float]:
        """计算执行时间（秒）"""
        try:
            start_time = result.get("start_time")
            end_time = result.get("end_time")

            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                return (end_dt - start_dt).total_seconds()

            return None

        except Exception:
            return None

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态信息"""
        return {
            "available_configs": {
                "standard": self.calculation_agent.get_available_configs(),
                "rules_engine": self.rules_engine_agent.get_available_configs()
            },
            "knowledge_stats": self.knowledge_agent.get_knowledge_stats(),
            "workflow_nodes": ["intent_recognition", "metric_calculation", "knowledge_precipitation"]
        }


# 便捷函数
async def run_big_agent(user_input: str, api_key: str) -> Dict[str, Any]:
    """
    运行Big Agent的便捷函数

    Args:
        user_input: 用户输入
        api_key: DeepSeek API密钥

    Returns:
        执行结果
    """
    workflow = BigAgentWorkflow(api_key)
    return await workflow.run_workflow(user_input)
