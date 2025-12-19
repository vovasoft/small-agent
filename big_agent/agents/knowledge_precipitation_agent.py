"""
知识沉淀Agent (Knowledge Precipitation Agent)
==========================================

此Agent负责分析和总结整个Big Agent工作流的执行过程，将经验教训沉淀为结构化知识。

核心功能：
1. 工作流分析：分析完整的用户查询->意图识别->指标计算->结果输出的过程
2. 知识抽取：从执行过程中提取关键模式、规律和经验教训
3. 文档生成：生成结构化的知识文档，包含：
   - 执行总结
   - 关键发现
   - 模式识别
   - 建议和教训
4. 知识存储：将生成的知识文档保存到知识库供后续复用

工作流程：
1. 接收完整的工作流执行数据
2. 分析用户意图和系统响应
3. 识别执行过程中的关键模式
4. 生成结构化的知识文档
5. 保存到知识库并建立索引

知识文档结构：
- title: 文档标题
- summary: 执行过程总结
- key_findings: 关键发现和数据洞察
- patterns_identified: 识别出的模式和规律
- recommendations: 改进建议和优化方案
- lessons_learned: 经验教训和最佳实践
- prompts_extracted: 可复用的提示词模板
- keywords: 相关关键词
- metadata: 元数据信息

技术实现：
- 使用LLM进行深度分析和知识抽取
- 支持多种输出格式（JSON、Markdown等）
- 集成版本控制和元数据管理
- 支持知识检索和复用

价值体现：
- 持续学习：系统通过每次执行积累经验
- 质量提升：基于历史知识优化后续执行
- 模式识别：发现用户行为和系统性能模式
- 知识复用：避免重复问题，提供标准解决方案

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 创建日志器
logger = logging.getLogger("knowledge_precipitation_agent")


class KnowledgePrecipitationAgent:
    """知识沉淀Agent"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化知识沉淀Agent

        Args:
            api_key: DeepSeek API密钥
            base_url: DeepSeek API基础URL
        """
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            temperature=0.3  # 稍微提高创造性以生成更好的文档
        )

        # 知识库存储路径
        self.knowledge_base_path = "knowledge_base"
        os.makedirs(self.knowledge_base_path, exist_ok=True)

        # 初始化API调用跟踪
        self.api_calls = []

    async def precipitate_knowledge(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从工作流数据中沉淀知识

        Args:
            workflow_data: 包含完整工作流信息的字典

        Returns:
            知识沉淀结果
        """
        try:
            # 提取关键信息
            extracted_info = self._extract_key_information(workflow_data)

            # 生成知识文档
            knowledge_doc = await self._generate_knowledge_document(extracted_info)

            # 保存知识文档
            saved_path = self._save_knowledge_document(knowledge_doc, workflow_data)

            return {
                "success": True,
                "knowledge_document": knowledge_doc,
                "saved_path": saved_path,
                "extracted_info": extracted_info
            }

        except Exception as e:
            print(f"知识沉淀失败: {e}")
            return {
                "success": False,
                "message": f"知识沉淀过程中发生错误: {str(e)}"
            }

    def _extract_key_information(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从工作流数据中提取关键信息

        Args:
            workflow_data: 工作流数据

        Returns:
            提取的关键信息
        """
        extracted = {
            "timestamp": datetime.now().isoformat(),
            "user_input": workflow_data.get("user_input", ""),
            "intent_recognition": workflow_data.get("intent_result", {}),
            "metric_calculations": workflow_data.get("calculation_results", []),
            "conversation_flow": [],
            "key_insights": [],
            "prompts_used": [],
            "api_calls": [],
            "errors": []
        }

        # 提取对话流程
        if "messages" in workflow_data:
            for message in workflow_data["messages"]:
                extracted["conversation_flow"].append({
                    "role": message.get("role", "unknown"),
                    "content": message.get("content", "")[:500],  # 限制长度
                    "timestamp": message.get("timestamp", "")
                })

        # 提取API调用信息
        calculations = workflow_data.get("calculation_results", [])
        if isinstance(calculations, dict) and "results" in calculations:
            for result in calculations["results"]:
                if "result" in result and isinstance(result["result"], dict):
                    api_info = {
                        "config_name": result.get("config_name", ""),
                        "success": result["result"].get("success", False),
                        "status_code": result["result"].get("status_code"),
                        "response_size": len(str(result["result"].get("data", "")))
                    }
                    extracted["api_calls"].append(api_info)

        # 提取错误信息
        for key, value in workflow_data.items():
            if "error" in key.lower() and value:
                extracted["errors"].append({
                    "stage": key,
                    "message": str(value)
                })

        return extracted

    async def _generate_knowledge_document(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成结构化的知识文档

        Args:
            extracted_info: 提取的信息

        Returns:
            知识文档
        """
        try:
            prompt = self._create_knowledge_prompt()

            # 准备输入数据
            input_data = {
                "user_input": extracted_info["user_input"],
                "intent_category": extracted_info["intent_recognition"].get("intent_category", "unknown"),
                "target_configs": extracted_info["intent_recognition"].get("target_configs", []),
                "calculation_results": json.dumps(extracted_info["metric_calculations"], ensure_ascii=False, indent=2),
                "api_calls_count": len(extracted_info["api_calls"]),
                "errors": json.dumps(extracted_info["errors"], ensure_ascii=False, indent=2)
            }

            # 记录大模型输入
            logger.info("========================================")
            logger.info("[AGENT] KnowledgePrecipitationAgent (知识沉淀Agent) - Agent 3/3")
            logger.info("[MODEL_INPUT] KnowledgePrecipitationAgent:")
            logger.info(f"[CONTEXT] 基于意图识别结果生成结构化知识文档")
            logger.info(f"{json.dumps(input_data, ensure_ascii=False, indent=2)}")
            logger.info("========================================")

            # 生成知识文档
            start_time = datetime.now()
            chain = prompt | self.llm

            response = await chain.ainvoke(input_data)
            end_time = datetime.now()

            # 解析响应
            content = response.content if hasattr(response, 'content') else str(response)

            # 记录API调用结果
            call_id = f"api_mll_{len(self.api_calls) + 2}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "KnowledgePrecipitationAgent",
                "model": "deepseek-chat",
                "request": {
                    "input_data": input_data,
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
                logger.info(f"[API_RESULT] 保存API结果文件: {filepath}")
            except Exception as e:
                logger.error(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

            # 记录大模型输出
            logger.info(f"[MODEL_OUTPUT] KnowledgePrecipitationAgent: {content}")
            logger.info("[RESULT] 知识文档生成完成")
            logger.info("========================================")

            # 尝试解析为JSON，如果失败则返回文本格式
            try:
                knowledge_doc = json.loads(content)
            except json.JSONDecodeError:
                knowledge_doc = {
                    "title": f"用户查询知识沉淀 - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "summary": content,
                    "generated_at": datetime.now().isoformat(),
                    "type": "text_document"
                }

            # 添加元数据
            knowledge_doc.update({
                "metadata": {
                    "created_at": extracted_info["timestamp"],
                    "source": "big_agent_workflow",
                    "version": "1.0"
                },
                "raw_data": extracted_info
            })

            return knowledge_doc

        except Exception as e:
            print(f"生成知识文档失败: {e}")
            return {
                "title": "知识沉淀失败",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "raw_data": extracted_info
            }

    def _create_knowledge_prompt(self) -> ChatPromptTemplate:
        """创建知识沉淀提示模板"""
        template = """你是一个专业的知识分析师。请基于用户查询的完整流程，生成结构化的知识文档。

用户原始输入：{user_input}

意图识别结果：
- 意图类别：{intent_category}
- 目标配置文件：{target_configs}

指标计算结果：
{calculation_results}

API调用次数：{api_calls_count}

错误信息：
{errors}

请生成一个JSON格式的知识文档，包含以下字段：
- title: 文档标题
- summary: 简要总结这次查询的要点
- key_findings: 关键发现和结果
- patterns_identified: 识别出的模式或规律
- prompts_extracted: 从对话中提取的有用提示词或模板
- keywords: 提取的关键名词和关键词
- recommendations: 基于这次经验的建议
- lessons_learned: 学到的经验教训

请确保内容客观、准确，并突出可复用的知识："""

        return ChatPromptTemplate.from_template(template)

    def _save_knowledge_document(self, knowledge_doc: Dict[str, Any], workflow_data: Dict[str, Any]) -> str:
        """
        保存知识文档到文件

        Args:
            knowledge_doc: 知识文档
            workflow_data: 原始工作流数据

        Returns:
            保存的文件路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"knowledge_{timestamp}.json"
            filepath = os.path.join(self.knowledge_base_path, filename)

            # 保存完整的知识文档
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(knowledge_doc, f, ensure_ascii=False, indent=2)

            return filepath

        except Exception as e:
            print(f"保存知识文档失败: {e}")
            return ""

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        在知识库中搜索相关知识

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            相关的知识文档列表
        """
        try:
            results = []
            if not os.path.exists(self.knowledge_base_path):
                return results

            for filename in os.listdir(self.knowledge_base_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.knowledge_base_path, filename), 'r', encoding='utf-8') as f:
                            doc = json.load(f)

                        # 简单的关键词匹配
                        content = json.dumps(doc, ensure_ascii=False).lower()
                        if query.lower() in content:
                            results.append({
                                "filename": filename,
                                "document": doc,
                                "relevance_score": 1.0  # 简化版本，实际可以计算更复杂的相关性
                            })

                    except Exception as e:
                        print(f"读取知识文档 {filename} 失败: {e}")

            # 按相关性排序并限制数量
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"搜索知识库失败: {e}")
            return []

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            if not os.path.exists(self.knowledge_base_path):
                return {"total_documents": 0, "total_size": 0}

            files = [f for f in os.listdir(self.knowledge_base_path) if f.endswith('.json')]
            total_size = sum(
                os.path.getsize(os.path.join(self.knowledge_base_path, f))
                for f in files
            )

            return {
                "total_documents": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }

        except Exception as e:
            print(f"获取知识库统计失败: {e}")
            return {"error": str(e)}
