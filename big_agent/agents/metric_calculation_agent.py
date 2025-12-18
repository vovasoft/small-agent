"""
指标计算Agent (Metric Calculation Agent)
====================================

此Agent负责根据意图识别结果执行具体的指标计算任务。

核心功能：
1. 配置文件加载：读取和解析JSON格式的指标计算配置文件
2. API调用管理：根据配置文件调用相应的计算API
3. 结果处理：处理API返回的数据，提取关键指标
4. 错误处理：处理API调用失败、网络异常等错误情况
5. 结果验证：验证计算结果的合理性和完整性

工作流程：
1. 接收意图识别结果和用户参数
2. 加载对应的指标计算配置文件
3. 构造API请求参数
4. 调用远程计算服务
5. 解析和验证返回结果
6. 返回结构化的计算结果

技术实现：
- 支持动态加载JSON配置文件
- 使用requests库进行HTTP API调用
- 集成LangChain用于复杂计算逻辑（可选）
- 完善的错误处理和超时机制
- 支持多种计算方法（标准、高级、自定义）

配置文件结构：
- api_config: API端点和认证信息
- param_mapping: 参数映射规则
- input_schema: 输入数据验证规则
- output_schema: 输出数据结构定义
- calculation_logic: 计算逻辑描述

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class MetricCalculationAgent:
    """远程指标计算Agent"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化指标计算Agent

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

        # 加载配置文件
        self.configs = self._load_configs()

    def _load_configs(self) -> Dict[str, Dict]:
        """加载所有配置文件"""
        configs = {}
        json_dir = "jsonFiles"

        if os.path.exists(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(json_dir, file), 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            key = file.replace('.json', '')
                            configs[key] = config
                    except Exception as e:
                        print(f"加载配置文件 {file} 失败: {e}")

        return configs

    async def calculate_metrics(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据意图识别结果进行指标计算

        Args:
            intent_result: 意图识别结果

        Returns:
            指标计算结果
        """
        try:
            results = []
            target_configs = intent_result.get("target_configs", [])

            if not target_configs:
                return {
                    "success": False,
                    "message": "没有找到需要调用的配置文件",
                    "results": []
                }

            for config_name in target_configs:
                if config_name in self.configs:
                    config = self.configs[config_name]
                    result = await self._call_metric_api(config, intent_result)
                    results.append({
                        "config_name": config_name,
                        "result": result
                    })
                else:
                    results.append({
                        "config_name": config_name,
                        "error": f"配置文件 {config_name} 不存在"
                    })

            return {
                "success": True,
                "results": results,
                "total_configs": len(target_configs),
                "successful_calculations": len([r for r in results if "result" in r])
            }

        except Exception as e:
            print(f"指标计算失败: {e}")
            return {
                "success": False,
                "message": f"指标计算过程中发生错误: {str(e)}",
                "results": []
            }

    async def _call_metric_api(self, config: Dict[str, Any], intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用具体的指标计算API

        Args:
            config: 配置文件
            intent_result: 意图识别结果

        Returns:
            API调用结果
        """
        try:
            # 获取API配置
            api_config = config.get("api_config", {})
            method = api_config.get("method", "POST")
            url = api_config.get("url", "")
            headers = api_config.get("headers", {})
            timeout = api_config.get("timeout", 30)

            # 准备请求数据
            request_data = self._prepare_request_data(config, intent_result)

            if not url:
                return {
                    "success": False,
                    "message": "配置文件中未指定API URL"
                }

            # 根据HTTP方法调用API
            if method.upper() == "GET":
                params = request_data.get("params", {})
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == "POST":
                json_data = request_data.get("json", {})
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            else:
                return {
                    "success": False,
                    "message": f"不支持的HTTP方法: {method}"
                }

            # 处理响应
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return {
                        "success": True,
                        "data": response_data,
                        "status_code": response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "data": response.text,
                        "status_code": response.status_code
                    }
            else:
                return {
                    "success": False,
                    "message": f"API调用失败，状态码: {response.status_code}",
                    "response": response.text
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "API调用超时"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"API调用异常: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"处理API调用时发生错误: {str(e)}"
            }

    def _prepare_request_data(self, config: Dict[str, Any], intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备API请求数据

        Args:
            config: 配置文件
            intent_result: 意图识别结果

        Returns:
            请求数据
        """
        # 从意图结果中提取参数
        key_parameters = intent_result.get("key_parameters", {})
        csv_data = intent_result.get("csv_data")

        # 获取配置中的参数映射
        param_mapping = config.get("param_mapping", {})

        # 构建请求数据
        request_data = {}

        # 处理参数映射
        for config_param, source in param_mapping.items():
            if source in key_parameters:
                request_data[config_param] = key_parameters[source]
            elif source == "csv_data" and csv_data:
                request_data[config_param] = csv_data

        # 如果没有参数映射，则使用默认逻辑
        if not request_data:
            request_data = {
                "parameters": key_parameters,
                "csv_data": csv_data,
                "intent_category": intent_result.get("intent_category")
            }

        return {"json": request_data}

    def get_available_configs(self) -> List[str]:
        """获取所有可用的配置文件名"""
        return list(self.configs.keys())

    def get_config_details(self, config_name: str) -> Optional[Dict]:
        """获取指定配置文件的详细信息"""
        return self.configs.get(config_name)
