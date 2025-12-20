"""
报告大纲生成Agent (Report Outline Generation Agent)
===============================================

此Agent负责根据用户需求和数据样本，生成专业的报告大纲结构。

核心功能：
1. 分析用户需求：理解报告目标和关键指标
2. 数据结构分析：识别可用字段和数据特征
3. 大纲生成：创建结构化的报告章节和指标需求
4. 智能推断：自动推断所需字段和计算逻辑

工作流程：
1. 接收用户查询和数据样本
2. 分析数据结构和可用字段
3. 生成报告标题和章节结构
4. 定义全局指标需求
5. 返回结构化的大纲对象

技术实现：
- 使用LangChain和结构化输出
- 支持异步处理
- 自动字段推断和补全
- 错误处理和默认值提供

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-20
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import os
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# 数据模型定义（与现有项目兼容）
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


class OutlineGeneratorAgent:
    """大纲生成智能体：将报告需求转化为结构化大纲"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化大纲生成Agent

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

    def create_prompt(self, question: str, sample_data: List[Dict]) -> str:
        """创建大纲生成提示"""

        available_fields = list(sample_data[0].keys()) if sample_data else []
        sample_str = json.dumps(sample_data[:2], ensure_ascii=False, indent=2)

        return f"""你是银行流水报告大纲专家。根据用户需求和样本数据，生成专业、可执行的报告大纲。

需求分析：
{question}

可用字段：
{', '.join(available_fields)}


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
- 报告标题应该体现对黑色金属和农业行业的分析

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

    async def generate_outline(self, question: str, sample_data: List[Dict[str, Any]]) -> ReportOutline:
        """异步生成大纲（修复版：自动补全缺失字段）"""
        prompt = self.create_prompt(question=question, sample_data=sample_data)

        messages = [
            ("system", "你是一名专业的报告大纲生成专家，必须输出完整、有效的JSON格式，包含所有必需字段。"),
            ("user", prompt)
        ]

        # 记录大模型输入
        print("========================================")
        print("[AGENT] OutlineGeneratorAgent (大纲生成Agent)")
        print("[MODEL_INPUT] OutlineGeneratorAgent:")
        print(f"[CONTEXT] 基于用户需求和数据样本生成报告大纲")
        print(f"Question: {question}")
        print(f"Sample data count: {len(sample_data)}")
        print("========================================")

        # 执行API调用
        start_time = datetime.now()
        response = await self.llm.ainvoke(messages)
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
                outline_data = json.loads(json_str)
                outline = ReportOutline(**outline_data)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            print(f"解析大纲响应失败: {e}，使用默认大纲")
            # 返回默认大纲
            outline = ReportOutline(
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

        # 记录API调用结果
        call_id = f"api_mll_大纲生成_{"{:.2f}".format((end_time - start_time).total_seconds())}"
        api_call_info = {
            "call_id": call_id,
            "timestamp": end_time.isoformat(),
            "agent": "OutlineGeneratorAgent",
            "model": "deepseek-chat",
            "request": {
                "question": question,
                "sample_data_count": len(sample_data),
                "prompt": prompt,
                "start_time": start_time.isoformat()
            },
            "response": {
                "content": content,
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
        print(f"[MODEL_OUTPUT] OutlineGeneratorAgent: {json.dumps(outline.dict() if hasattr(outline, 'dict') else outline, ensure_ascii=False)}")
        print("========================================")

        # 后处理，补全缺失的section_id和metric_id
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


async def generate_report_outline(question: str, sample_data: List[Dict[str, Any]], api_key: str, max_retries: int = 3, retry_delay: float = 2.0) -> ReportOutline:
    """
    生成报告大纲的主函数，支持重试机制

    Args:
        question: 用户查询问题
        sample_data: 数据样本
        api_key: API密钥
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试间隔时间（秒），默认2秒

    Returns:
        生成的报告大纲
    """
    import asyncio
    import time

    agent = OutlineGeneratorAgent(api_key)

    print(f"📝 开始生成报告大纲（最多重试 {max_retries} 次）...")

    for attempt in range(max_retries):
        try:
            print(f"   尝试 {attempt + 1}/{max_retries}...")
            start_time = time.time()

            outline = await agent.generate_outline(question, sample_data)

            elapsed_time = time.time() - start_time
            print(".2f")
            print("\n📝 大纲生成成功：")
            print(f"   标题：{outline.report_title}")
            print(f"   章节数：{len(outline.sections)}")
            print(f"   指标数：{len(outline.global_metrics)}")

            return outline

        except Exception as e:
            elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
            print(".2f")
            print(f"   错误详情: {str(e)}")

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                print(f"   ⏳ {retry_delay} 秒后进行第 {attempt + 2} 次重试...")
                await asyncio.sleep(retry_delay)
                # 增加重试间隔，避免频繁调用
                retry_delay = min(retry_delay * 1.5, 10.0)  # 最多等待10秒
            else:
                print(f"   ❌ 已达到最大重试次数 ({max_retries})，使用默认结构")

    # 所有重试都失败后，使用默认结构
    print("⚠️ 所有重试均失败，使用默认大纲结构")

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
                    metric_name="总收入（规则引擎）",
                    calculation_logic="sum of income transactions using rules engine",
                    required_fields=["txAmount", "txDirection"],
                    dependencies=[]
                ),
                MetricRequirement(
                    metric_id="total_expense",
                    metric_name="总支出",
                    calculation_logic="sum of expense transactions",
                    required_fields=["txAmount", "txDirection"],
                    dependencies=[]
                )
            ]
        )

    return default_outline