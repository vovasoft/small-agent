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
import requests
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

        # 获取可用的知识元数据
        self.available_knowledge = self._load_available_knowledge()



    def _convert_new_format_to_outline(self, new_format_data: Dict[str, Any]) -> Dict[str, Any]:
        """将新的JSON格式转换为原来的ReportOutline格式"""

        # 转换sections
        sections = []
        for section_data in new_format_data.get("sections", []):
            # 从metrics中提取指标名称
            metrics_needed = []
            for metric_type in ["calculation_metrics", "statistical_metrics", "analysis_metrics"]:
                for metric in section_data.get("metrics", {}).get(metric_type, []):
                    # 这里可以根据metric_name映射到实际的metric_id
                    # 暂时使用metric_name作为metric_id
                    metrics_needed.append(metric.get("metric_name", ""))

            section = {
                "section_id": section_data.get("section_id", ""),
                "title": section_data.get("section_title", ""),
                "description": section_data.get("section_description", ""),
                "metrics_needed": metrics_needed
            }
            sections.append(section)

        # 生成global_metrics：使用知识ID进行匹配，并强制添加更多农业相关指标
        global_metrics = []
        used_knowledge_ids = set()

        # 首先处理LLM生成的指标
        for section in sections:
            for metric_name in section["metrics_needed"]:
                # 查找对应的指标描述（从原始数据中获取）
                metric_description = ""
                for section_data in new_format_data.get("sections", []):
                    for metric_type in ["calculation_metrics", "statistical_metrics", "analysis_metrics"]:
                        for metric in section_data.get("metrics", {}).get(metric_type, []):
                            if metric.get("metric_name") == metric_name:
                                metric_description = metric.get("metric_description", "")
                                break
                        if metric_description:
                            break
                    if metric_description:
                        break

                # 使用知识ID匹配算法找到最佳匹配
                knowledge_id = self._match_metric_to_knowledge(metric_name, metric_description)

                # 如果找到匹配的知识ID，使用它作为metric_id
                if knowledge_id and knowledge_id not in used_knowledge_ids:
                    global_metrics.append({
                        "metric_id": knowledge_id,  # 使用知识ID作为metric_id
                        "metric_name": metric_name,
                        "calculation_logic": f"使用规则引擎计算{metric_name}: {metric_description}",
                        "required_fields": ["transactions"],  # 规则引擎使用transactions数据
                        "dependencies": []
                    })
                    used_knowledge_ids.add(knowledge_id)
                else:
                    # 如果没有找到匹配的知识ID，生成一个基本的MetricRequirement作为备选
                    if not any(m.get("metric_id") == metric_name for m in global_metrics):
                        print(f"⚠️ 指标 '{metric_name}' 未找到匹配的知识ID，使用默认配置")
                        global_metrics.append({
                            "metric_id": metric_name,
                            "metric_name": metric_name,
                            "calculation_logic": f"计算{metric_name}: {metric_description}",
                            "required_fields": ["txAmount", "txDirection"],
                            "dependencies": []
                        })

        # 完全依赖LLM生成包含所有必需指标的大纲
        print(f"🤖 大模型生成 {len(global_metrics)} 个指标")

        return {
            "report_title": new_format_data.get("chapter_title", "流水分析报告"),
            "sections": sections,
            "global_metrics": global_metrics
        }

    def create_prompt(self, question: str, industry: str) -> str:
        """创建大纲生成提示"""

        # 从API动态获取可用的指标列表
        available_metrics = self._load_available_metrics()

        # 构建指标列表文本
        metrics_list_text = "指标名称\t指标类型\t指标描述\n"
        for metric in available_metrics:
            metrics_list_text += f"{metric['name']}\t{metric.get('type', '计算型指标')}\t{metric.get('description', '')}\n"

        # 构建基础提示词
        base_prompt = f"""[角色定义]
你的角色是: 流水分析报告的大纲生成模块。
你的目标是:{question},生成一份针对{industry}行业的全面的流水分析报告大纲。
生成结构清晰、可被程序解析的JSON格式大纲，明确每个章节及其下属分析主题所需的分析指标。

[职责边界]
你只能完成以下事项:
1.确定{industry}流水分析报告应包含的章节结构
2.明确每个章节下需要覆盖的分析主题
3.为每个分析主题列出所需的计算指标、统计指标或分析指标

你不得做以下任何事情:
1.不得计算任何指标
2.不得对流水数据进行分析
3.不得判断交易是否异常或存在风险
4.不得生成任何分析结论、判断性描述或报告正文
5.不得决定分析执行顺序或分析方法

你输出的内容仅是"分析需求清单"，而不是"分析结果"。

[可用指标总览]
系统当前支持 {len(available_metrics)} 个指标。
指标内容为{available_metrics}

[重要要求]
请根据用户需求和可用指标列表，从上述指标中选择最相关的指标。必须基于用户查询的具体需求进行智能匹配，确保选择的指标能够充分满足分析需求。

[强制要求]
生成大纲时，请：
1. 仔细分析用户查询，识别所有提到的分析需求点
2. 从可用指标中选择能够满足这些需求的完整指标组合
3. 基于语义相关性进行指标筛选，不要过于保守
4. 在各章节的metrics对象中，按照指标类型(calculation_metrics/statistical_metrics/analysis_metrics)列出选定的指标
5. 为每个指标提供metric_name和metric_description字段
6. 优先选择与用户查询直接相关的指标

[可选择的指标列表]
{metrics_list_text}

[重要说明]
请确保：
- 从提供的可用指标列表中选择最相关的指标
- 为每个选定的指标提供清晰的名称和描述
- 输出格式必须严格遵循上述JSON结构
- 确保选择的指标能够满足用户查询的具体分析需求

[输出格式要求]
你必须且只能以 JSON 字符串 形式输出分析大纲，不得输出任何解释性自然语言。
JSON 必须严格遵循以下结构约定:
{{
  "chapter_title": "string",
  "sections": [
    {{
      "section_id": "string",
      "section_title": "string",
      "section_description": "string",
      "metrics": {{
        "calculation_metrics": [
          {{
            "metric_name": "string",
            "metric_description": "string"
          }}
        ],
        "statistical_metrics": [
          {{
            "metric_name": "string",
            "metric_description": "string"
          }}
        ],
        "analysis_metrics": [
          {{
            "metric_name": "string",
            "metric_description": "string"
          }}
        ]
      }}
    }}
  ]
}}"""

        return base_prompt

        print(f"📊 最终生成 {len(global_metrics)} 个指标")

        return {
            "report_title": new_format_data.get("chapter_title", "流水分析报告"),
            "sections": sections,
            "global_metrics": global_metrics
        }


    async def generate_outline(self, question: str, industry: str, sample_data: List[Dict[str, Any]]) -> ReportOutline:
        """异步生成大纲（修复版：自动补全缺失字段）"""
        prompt = self.create_prompt(question, industry)

        # 在prompt末尾添加业务背景信息
        full_prompt = f"""{prompt}

【业务背景信息】
行业：{industry}
产品类型：经营贷
客群类型：小微企业"""

        messages = [
            ("system", "你是一名专业的报告大纲生成专家，必须输出完整、有效的JSON格式，包含所有必需字段。"),
            ("user", full_prompt)
        ]

        # 记录大模型输入
        print("========================================")
        print("[AGENT] OutlineGeneratorAgent (大纲生成Agent)")
        print(f"[KNOWLEDGE_BASE] 已加载 {len(self.available_knowledge)} 个知识元数据")
        if self.available_knowledge:
            sample_knowledge = self.available_knowledge[:3]  # 显示前3个作为示例
            print(f"[KNOWLEDGE_SAMPLE] 示例知识: {[k.get('id', '') for k in sample_knowledge]}")
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

                # 转换新的JSON格式为原来的ReportOutline格式
                converted_data = self._convert_new_format_to_outline(outline_data)
                outline = ReportOutline(**converted_data)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            print(f"解析大纲响应失败: {e}，使用默认大纲")
            # 不在这里创建大纲，在函数末尾统一处理

        # 记录API调用结果
        call_id = f"api_mll_大纲生成_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{call_id}.json"
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
        outline = self._post_process_outline(outline, question, industry)

        return outline

    def _post_process_outline(self, outline: ReportOutline, question: str, industry: str) -> ReportOutline:
        """
        后处理大纲，自动补全缺失的必需字段，并基于查询优化指标
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

        # 基于用户查询进行指标优化筛选
        if hasattr(outline, 'global_metrics') and outline.global_metrics:
            print(f"📊 AI选择了 {len(outline.global_metrics)} 个指标，进行智能优化...")
            outline = self._optimize_metrics_by_query(outline, question, industry)

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

    def _optimize_metrics_by_query(self, outline: ReportOutline, question: str, industry: str) -> ReportOutline:
        """
        基于用户查询进行智能指标优化
        """
        # 获取所有可用指标
        available_metrics = self._load_available_metrics()

        # 已选择的指标名称集合
        selected_metric_names = {m.metric_name for m in outline.global_metrics}

        # 基于用户查询进行语义匹配，找出缺失的关键指标
        query_keywords = self._extract_query_keywords(question, industry)
        missing_key_metrics = self._find_missing_key_metrics(
            available_metrics, selected_metric_names, query_keywords
        )

        # 补充缺失的关键指标
        supplemented_count = 0
        for metric_name in missing_key_metrics:
            # 找到对应的可用指标信息
            available_metric = next((m for m in available_metrics if m['name'] == metric_name), None)
            if available_metric:
                # 创建MetricRequirement对象
                metric_req = MetricRequirement(
                    metric_id=f"metric-{metric_name}",
                    metric_name=metric_name,
                    calculation_logic=f"使用规则引擎计算{metric_name}",
                    required_fields=["transactions"],
                    dependencies=[]
                )
                outline.global_metrics.append(metric_req)
                supplemented_count += 1
                print(f"  补充关键指标: {metric_name}")

        if supplemented_count > 0:
            print(f"✅ 基于查询分析补充了 {supplemented_count} 个关键指标，总计 {len(outline.global_metrics)} 个指标")

        # 智能分配章节指标需求
        self._smart_assign_section_metrics(outline)

        return outline

    def _extract_query_keywords(self, question: str, industry: str) -> List[str]:
        """
        通过大模型从用户查询中提取关键词

        Args:
            question: 用户查询
            industry: 行业信息

        Returns:
            关键词列表
        """
        try:
            keyword_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的关键词提取专家，需要从用户查询中提取关键的分析指标和业务术语。

请分析查询内容，识别出用户关心的核心指标、分析维度和业务概念。

返回格式：
请以逗号分隔的关键词列表形式返回，不要其他解释。

示例：
收入分析, 支出统计, 交易对手, 时间趋势, 占比分析"""),
                ("human", """用户查询：{question}
行业背景：{industry}

请提取这个查询中的关键分析指标和业务术语。""")
            ])

            chain = keyword_prompt | self.llm
            result = chain.invoke({
                "question": question,
                "industry": industry
            })

            keywords_text = result.content.strip()
            # 按逗号分割并清理空白
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]

            print(f"🔍 提取到查询关键词: {keywords}")
            return keywords

        except Exception as e:
            print(f"⚠️ 关键词提取失败，使用简单分词: {str(e)}")
            # 备选方案：简单的文本分词
            import re
            # 移除标点符号，提取中文词组
            text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', ' ', question)
            words = [w for w in text.split() if len(w) > 1]
            print(f"🔄 备选关键词: {words}")
            return words

    def _find_missing_key_metrics(self, available_metrics: List[Dict], selected_metric_names: set,
                                  query_keywords: List[str]) -> List[str]:
        """
        基于查询关键词找出缺失的关键指标

        Args:
            available_metrics: 所有可用指标
            selected_metric_names: 已选择的指标名称集合
            query_keywords: 查询关键词

        Returns:
            缺失的关键指标名称列表
        """
        if not query_keywords or not available_metrics:
            return []

        try:
            missing_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的指标推荐专家，需要根据用户查询的关键词，识别出可能缺失的关键指标。

请分析：
1. 用户关心的分析维度（收入、支出、排名、趋势等）
2. 已选择的指标
3. 可用的指标库

推荐一些重要的缺失指标，帮助完善分析报告。

返回格式：
只返回指标名称列表，用换行符分隔，不要其他解释。

示例：
总收入分析
支出占比统计
交易对手排名"""),
                ("human", """查询关键词：{keywords}

已选择的指标：
{selected_metrics}

可用指标库：
{available_metrics}

请推荐一些重要的缺失指标。""")
            ])

            # 格式化输入
            selected_list = '\n'.join(selected_metric_names) if selected_metric_names else '无'
            available_list = '\n'.join([m.get('name', '') for m in available_metrics if m.get('name')])

            chain = missing_prompt | self.llm
            result = chain.invoke({
                "keywords": ', '.join(query_keywords),
                "selected_metrics": selected_list,
                "available_metrics": available_list
            })

            # 解析结果
            recommended_metrics = []
            for line in result.content.strip().split('\n'):
                metric_name = line.strip()
                if metric_name and metric_name not in selected_metric_names:
                    # 验证指标是否存在于可用指标库中
                    if any(m.get('name') == metric_name for m in available_metrics):
                        recommended_metrics.append(metric_name)

            print(f"📊 推荐缺失指标: {recommended_metrics}")
            return recommended_metrics

        except Exception as e:
            print(f"⚠️ 指标推荐失败: {str(e)}")
            return []

    def _smart_assign_section_metrics(self, outline: ReportOutline) -> None:
        """
        智能分配章节指标需求

        Args:
            outline: 报告大纲对象，会被原地修改
        """
        if not outline.sections or not outline.global_metrics:
            return

        try:
            # 获取所有可用的指标ID
            available_metric_ids = {m.metric_id for m in outline.global_metrics}

            assign_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的报告结构专家，需要将全局指标智能分配到各个章节。

分配原则：
1. 每个章节分配3-5个最相关的指标
2. 指标应与章节内容高度相关
3. 避免重复分配相同的指标
4. 优先分配核心指标到主要章节

返回格式：
为每个章节返回指标ID列表，用分号分隔章节，格式如下：
章节ID:指标ID1,指标ID2,指标ID3

示例：
sec_1:metric-total_income,metric-expense_trend,metric-profit_margin
sec_2:metric-customer_analysis,metric-market_share"""),
                ("human", """报告标题：{report_title}

章节列表：
{sections}

可用指标：
{available_metrics}

请为每个章节分配最合适的指标ID。""")
            ])

            # 格式化输入
            sections_text = '\n'.join([
                f"{section.section_id}: {section.title} - {section.description}"
                for section in outline.sections
            ])

            available_metrics_text = '\n'.join([
                f"{m.metric_id}: {m.metric_name} - {m.calculation_logic}"
                for m in outline.global_metrics
            ])

            chain = assign_prompt | self.llm
            result = chain.invoke({
                "report_title": outline.report_title,
                "sections": sections_text,
                "available_metrics": available_metrics_text
            })

            # 解析结果并分配指标
            lines = result.content.strip().split('\n')
            assigned_metrics = set()  # 避免重复分配

            for line in lines:
                if ':' not in line:
                    continue

                section_id, metrics_str = line.split(':', 1)
                section_id = section_id.strip()

                # 找到对应的章节
                section = next((s for s in outline.sections if s.section_id == section_id), None)
                if not section:
                    continue

                # 解析指标ID列表
                metric_ids = [mid.strip() for mid in metrics_str.split(',') if mid.strip()]

                # 验证指标ID并分配（避免重复）
                valid_metrics = []
                for metric_id in metric_ids:
                    if metric_id in available_metric_ids and metric_id not in assigned_metrics:
                        valid_metrics.append(metric_id)
                        assigned_metrics.add(metric_id)

                    # 每个章节最多分配5个指标
                    if len(valid_metrics) >= 5:
                        break

                section.metrics_needed = valid_metrics
                print(f"📋 章节 '{section.title}' 分配了 {len(valid_metrics)} 个指标: {valid_metrics}")

            # 检查是否有章节没有分配到指标，如果有则平均分配剩余指标
            unassigned_sections = [s for s in outline.sections if not s.metrics_needed]
            remaining_metrics = [m.metric_id for m in outline.global_metrics if m.metric_id not in assigned_metrics]

            if unassigned_sections and remaining_metrics:
                print(f"🔄 为 {len(unassigned_sections)} 个未分配章节平均分配剩余指标")
                metrics_per_section = max(1, len(remaining_metrics) // len(unassigned_sections))

                for i, section in enumerate(unassigned_sections):
                    start_idx = i * metrics_per_section
                    end_idx = min(start_idx + metrics_per_section, len(remaining_metrics))
                    section.metrics_needed = remaining_metrics[start_idx:end_idx]
                    print(f"📋 章节 '{section.title}' 分配了 {len(section.metrics_needed)} 个指标: {section.metrics_needed}")

        except Exception as e:
            print(f"⚠️ 智能指标分配失败，使用平均分配: {str(e)}")
            # 备选方案：平均分配所有指标到各个章节
            if outline.sections and outline.global_metrics:
                all_metric_ids = [m.metric_id for m in outline.global_metrics]
                metrics_per_section = max(1, len(all_metric_ids) // len(outline.sections))

                for i, section in enumerate(outline.sections):
                    start_idx = i * metrics_per_section
                    end_idx = min(start_idx + metrics_per_section, len(all_metric_ids))
                    section.metrics_needed = all_metric_ids[start_idx:end_idx]
                    print(f"🔄 备选分配 - 章节 '{section.title}' 分配了 {len(section.metrics_needed)} 个指标")

   
   

    def _load_available_knowledge(self) -> List[Dict[str, Any]]:
        """
        从规则引擎获取可用的知识元数据

        Returns:
            知识元数据列表，包含id和description
        """
        try:
            url = "http://localhost:8081/api/rules/getKnowledgeMeta"
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0"
            }

            response = requests.post(url, headers=headers, json={}, timeout=30)

            if response.status_code == 200:
                knowledge_meta = response.json()
                if isinstance(knowledge_meta, list):
                    print(f"✅ 成功获取 {len(knowledge_meta)} 个知识元数据")
                    return knowledge_meta
                else:
                    print(f"⚠️ 知识元数据格式异常: {knowledge_meta}")
                    return []
            else:
                print(f"❌ 获取知识元数据失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return []

        except Exception as e:
            print(f"❌ 获取知识元数据时发生错误: {str(e)}")
            return []

    def _load_available_metrics(self) -> List[Dict[str, str]]:
        """
        从知识库中提取可用的指标列表

        Returns:
            指标列表，包含name和description字段
        """
        knowledge_list = self._load_available_knowledge()

        metrics = []
        for knowledge in knowledge_list:
            knowledge_id = knowledge.get("id", "")
            description = knowledge.get("description", "")

            # 从知识ID中提取指标名称
            if knowledge_id.startswith("metric-"):
                metric_name = knowledge_id.replace("metric-", "")

                # 从描述中提取更简洁的指标描述
                short_description = self._extract_metric_description(description)

                metrics.append({
                    "name": metric_name,
                    "description": short_description,
                    "type": self._classify_metric_type(metric_name, description)
                })

        print(f"✅ 从知识库中提取了 {len(metrics)} 个可用指标")
        return metrics

    def _extract_metric_description(self, full_description: str) -> str:
        """从完整描述中提取简洁的指标描述"""
        # 移除"因子概述："等前缀
        description = full_description.replace("因子概述：", "").strip()

        # 如果描述太长，取前50个字符
        if len(description) > 50:
            description = description[:50] + "..."

        return description

    def _classify_metric_type(self, metric_name: str, description: str) -> str:
        """根据指标名称和描述分类指标类型"""
        if any(keyword in metric_name for keyword in ["收入", "支出", "金额", "交易笔数"]):
            return "基础统计指标"
        elif any(keyword in metric_name for keyword in ["时间范围", "时间跨度"]):
            return "时间分析指标"
        elif any(keyword in metric_name for keyword in ["比例", "占比", "构成"]):
            return "结构分析指标"
        elif any(keyword in metric_name for keyword in ["排名", "TOP", "前三"]):
            return "专项分析指标"
        elif any(keyword in metric_name for keyword in ["账户", "数量"]):
            return "账户分析指标"
        else:
            return "其他指标"

    def _match_metric_to_knowledge(self, metric_name: str, metric_description: str) -> str:
        """
        通过大模型判断指标是否与可用知识匹配

        Args:
            metric_name: 指标名称
            metric_description: 指标描述

        Returns:
            匹配的知识ID，如果没有找到则返回空字符串
        """
        if not self.available_knowledge:
            return ""

        # 首先尝试精确匹配：直接用指标名称匹配知识ID
        for knowledge in self.available_knowledge:
            knowledge_id = knowledge.get("id", "")
            # 去掉前缀匹配，如 "metric-分析账户数量" 匹配 "分析账户数量"
            if knowledge_id.startswith("metric-") and knowledge_id.replace("metric-", "") == metric_name:
                print(f"🔗 精确匹配指标 '{metric_name}' -> 知识ID: {knowledge_id}")
                return knowledge_id

        # 使用大模型进行语义匹配
        match_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的指标匹配专家，需要根据指标名称和描述，从提供的知识库中找到最合适的匹配项。

请分析指标的语义含义和计算逻辑，判断哪个知识项最匹配。

返回格式：
如果找到匹配：返回知识ID
如果未找到匹配：返回空字符串 ""

只返回知识ID或空字符串，不要其他解释。"""),
            ("human", """指标信息：
名称：{metric_name}
描述：{metric_description}

可用知识库：
{knowledge_list}

请判断这个指标是否与知识库中的某个项目匹配。如果匹配，返回对应的知识ID；如果不匹配，返回空字符串。""")
        ])

        # 构建知识库描述
        knowledge_list = "\n".join([
            f"ID: {k.get('id', '')}\n描述: {k.get('description', '')}"
            for k in self.available_knowledge
        ])

        try:
            # 调用大模型进行匹配
            chain = match_prompt | self.llm
            result = chain.invoke({
                "metric_name": metric_name,
                "metric_description": metric_description or "无描述",
                "knowledge_list": knowledge_list
            })

            matched_knowledge_id = result.content.strip()

            # 验证返回的知识ID是否存在于可用知识中
            if matched_knowledge_id and any(k.get("id") == matched_knowledge_id for k in self.available_knowledge):
                print(f"🤖 大模型匹配指标 '{metric_name}' -> 知识ID: {matched_knowledge_id}")
                return matched_knowledge_id
            else:
                print(f"❌ 大模型未找到指标 '{metric_name}' 的匹配项")
                return ""

        except Exception as e:
            print(f"⚠️ 大模型匹配失败，使用备选方案: {str(e)}")
            # 备选方案：简单的关键词匹配（不包含特定业务逻辑）
            for knowledge in self.available_knowledge:
                knowledge_id = knowledge.get("id", "")
                knowledge_desc = knowledge.get("description", "").lower()

                # 检查指标名称是否在知识描述中出现
                if metric_name.lower() in knowledge_desc:
                    print(f"🔄 备选匹配指标 '{metric_name}' -> 知识ID: {knowledge_id}")
                    return knowledge_id

            print(f"❌ 指标 '{metric_name}' 未找到匹配的知识ID")
            return ""


async def generate_report_outline(question: str, industry: str, sample_data: List[Dict[str, Any]], api_key: str, max_retries: int = 3, retry_delay: float = 2.0) -> ReportOutline:
    """
    生成报告大纲的主函数，支持重试机制

    Args:
        question: 用户查询问题
        industry: 行业
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

            outline = await agent.generate_outline(question, industry, sample_data)

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

    # 获取实际可用的指标来构建默认大纲
    available_metrics = self._load_available_metrics()

    # 选择一些基础指标作为默认值
    default_metric_ids = []
    default_global_metrics = []

    # 优先选择基础统计指标
    base_metrics = [m for m in available_metrics if m.get('type') == '基础统计指标']
    if base_metrics:
        # 选择前3个基础指标
        for metric in base_metrics[:3]:
            metric_name = metric['name']
            knowledge_id = f"metric-{metric_name}"
            default_metric_ids.append(knowledge_id)
            default_global_metrics.append(MetricRequirement(
                metric_id=knowledge_id,
                metric_name=metric_name,
                calculation_logic=f"使用规则引擎计算{metric_name}: {metric.get('description', '')}",
                required_fields=["transactions"],
                dependencies=[]
            ))

    # 如果基础指标不够，补充其他类型的指标
    if len(default_metric_ids) < 3:
        other_metrics = [m for m in available_metrics if m.get('type') != '基础统计指标']
        for metric in other_metrics[:3-len(default_metric_ids)]:
            metric_name = metric['name']
            knowledge_id = f"metric-{metric_name}"
            default_metric_ids.append(knowledge_id)
            default_global_metrics.append(MetricRequirement(
                metric_id=knowledge_id,
                metric_name=metric_name,
                calculation_logic=f"使用规则引擎计算{metric_name}: {metric.get('description', '')}",
                required_fields=["transactions"],
                dependencies=[]
            ))

    # 创建使用实际指标的默认大纲
    default_outline = ReportOutline(
        report_title="默认交易分析报告",
        sections=[
            ReportSection(
                section_id="sec_1",
                title="交易概览",
                description="基础交易情况分析",
                metrics_needed=default_metric_ids
            )
        ],
        global_metrics=default_global_metrics
    )
    return default_outline
