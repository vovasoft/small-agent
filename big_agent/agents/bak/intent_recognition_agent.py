"""
意图识别Agent (Intent Recognition Agent)
=======================================

此Agent负责分析用户输入的自然语言查询，识别用户的真实意图和需求。

核心功能：
1. 意图分类：判断用户是想要计算指标、查询数据还是其他操作
2. 配置文件匹配：根据意图从JSON配置文件库中选择最相关的指标计算配置
3. 参数提取：从用户查询中提取关键参数（如时间范围、地域等）
4. CSV数据检测：识别用户是否提供了CSV数据或其他结构化数据

工作流程：
1. 接收用户自然语言输入
2. 分析查询类型（纯文本 or 包含数据）
3. 加载可用的指标计算配置文件
4. 使用LLM分析意图并匹配配置
5. 返回结构化的意图分析结果

技术实现：
- 使用LangChain + OpenAI兼容接口调用大语言模型
- 基于提示工程设计意图识别prompt模板
- 支持JSON格式的结构化输出
- 集成详细的日志记录功能

配置要求：
- 需要有效的DeepSeek API密钥
- 依赖jsonFiles目录下的配置文件

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
from langchain_core.output_parsers import JsonOutputParser

# 创建专用的日志器，用于跟踪意图识别过程
logger = logging.getLogger("intent_recognition_agent")

# 数据处理库导入
import pandas as pd


class IntentRecognitionAgent:
    """意图识别Agent"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化意图识别Agent

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

        # 获取可用的指标配置文件
        self.available_configs = self._load_available_configs()

        # 初始化API调用跟踪
        self.api_calls = []

    def _load_available_configs(self) -> Dict[str, Dict]:
        """加载可用的指标配置文件"""
        configs = {}
        json_dir = "json_files"

        if os.path.exists(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(json_dir, file), 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            # 使用文件名作为key，去掉.json后缀
                            key = file.replace('.json', '')
                            configs[key] = config
                    except Exception as e:
                        print(f"加载配置文件 {file} 失败: {e}")

        return configs

    def _create_intent_prompt(self) -> ChatPromptTemplate:
        """创建意图识别提示模板"""
        template = """你是一个专业的意图识别助手。请分析用户的输入，识别其意图并确定需要调用的指标计算服务。

用户输入可能包含：
1. 纯语言描述：如"我想计算农业相关指标"
2. 语言描述+CSV数据：用户可能上传了CSV文件并描述了需求

你的任务是：
1. 判断输入类型（纯语言描述或包含CSV数据）
2. 分析用户想要计算什么类型的指标
3. 从可用的配置文件中选择最相关的指标计算文件
4. 判断使用哪种计算模式：普通指标计算或规则引擎计算
5. 提取关键信息和参数

可用配置文件：
{available_configs}

计算模式说明：
- 普通指标计算：使用标准API接口，配置文件名不包含"规则引擎"
- 规则引擎计算：使用规则引擎API接口，配置文件名包含"规则引擎"

请以JSON格式返回以下信息：
- input_type: "text_only" 或 "text_with_csv"
- intent_category: 用户意图的类别（如"农业"、"经济"等）
- calculation_mode: "standard" 或 "rules_engine"（计算模式）
- target_configs: 数组，包含需要调用的配置文件名（不含.json后缀）
- key_parameters: 对象，包含提取的关键参数
- confidence: 置信度（0-1之间）

用户输入：
{user_input}

请仔细分析并返回JSON结果："""

        return ChatPromptTemplate.from_template(template)

    def _analyze_csv_if_present(self, user_input: str) -> Optional[pd.DataFrame]:
        """如果输入包含CSV数据，则分析CSV"""
        # 这里可以扩展为实际的CSV解析逻辑
        # 目前先返回None，表示没有CSV数据
        return None

    async def recognize_intent(self, user_input: str) -> Dict[str, Any]:
        """
        识别用户意图

        Args:
            user_input: 用户输入文本

        Returns:
            包含意图分析结果的字典
        """
        try:
            # 分析是否包含CSV数据
            csv_data = self._analyze_csv_if_present(user_input)

            # 创建提示
            prompt = self._create_intent_prompt()

            # 格式化可用配置信息
            configs_info = "\n".join([
                f"- {name}: {config.get('description', '无描述')}"
                for name, config in self.available_configs.items()
            ])

            # 创建解析器
            parser = JsonOutputParser()

            # 创建链
            chain = prompt | self.llm | parser

            # 记录大模型输入
            full_prompt = f"""Available configs:
{configs_info}

User input: {user_input}"""

            logger.info("========================================")
            logger.info("[AGENT] IntentRecognitionAgent (意图识别Agent) - Agent 1/3")
            logger.info("[MODEL_INPUT] IntentRecognitionAgent:")
            logger.info(f"[CONTEXT] 系统当前有 {len(self.available_configs)} 个可用配置文件")
            logger.info(f"{full_prompt}")
            logger.info("========================================")

            # 执行推理
            start_time = datetime.now()
            result = await chain.ainvoke({
                "available_configs": configs_info,
                "user_input": user_input
            })
            end_time = datetime.now()

            # 记录API调用结果
            call_id = f"api_mll_意图识别_{end_time.isoformat()}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "IntentRecognitionAgent",
                "model": "deepseek-chat",
                "request": {
                    "prompt": full_prompt,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "result": result,
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
            logger.info(f"[MODEL_OUTPUT] IntentRecognitionAgent: {json.dumps(result, ensure_ascii=False)}")
            logger.info(f"[RESULT] 识别出 {len(result.get('target_configs', []))} 个目标配置")
            logger.info("========================================")

            # 确保返回calculation_mode字段
            if "calculation_mode" not in result:
                # 根据target_configs中的文件名判断计算模式
                target_configs = result.get("target_configs", [])
                has_rules_engine = any("规则引擎" in config for config in target_configs)
                result["calculation_mode"] = "rules_engine" if has_rules_engine else "standard"

            # 添加CSV数据信息
            result["has_csv_data"] = csv_data is not None
            result["csv_data"] = csv_data.to_dict() if csv_data is not None else None

            return result

        except Exception as e:
            print(f"意图识别失败: {e}")
            # 返回默认结果
            return {
                "input_type": "text_only",
                "intent_category": "unknown",
                "calculation_mode": "standard",
                "target_configs": [],
                "key_parameters": {},
                "confidence": 0.0,
                "has_csv_data": False,
                "csv_data": None,
                "error": str(e)
            }

    def get_config_details(self, config_name: str) -> Optional[Dict]:
        """获取指定配置文件的详细信息"""
        return self.available_configs.get(config_name)
