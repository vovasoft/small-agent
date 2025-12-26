"""
规则引擎指标计算Agent (Rules Engine Metric Calculation Agent)
===========================================================

此Agent负责根据意图识别结果执行规则引擎模式的指标计算任务。

核心功能：
1. 配置文件加载：读取和解析规则引擎指标计算配置文件
2. API调用管理：根据配置文件调用规则引擎API
3. 结果处理：处理API返回的数据，提取关键指标
4. 错误处理：处理API调用失败、网络异常等错误情况
5. 结果验证：验证计算结果的合理性和完整性

工作流程：
1. 接收意图识别结果和用户参数
2. 加载对应的规则引擎指标计算配置文件
3. 构造API请求参数（id和input）
4. 调用远程规则引擎服务
5. 解析和验证返回结果
6. 返回结构化的计算结果

技术实现：
- 支持动态加载JSON配置文件
- 使用requests库进行HTTP API调用
- 集成LangChain用于复杂计算逻辑（可选）
- 完善的错误处理和超时机制
- 支持多种计算方法（标准、高级、自定义）

配置文件结构：
- id: 规则引擎执行ID
- input: 数据文件路径
- description: 规则描述

API接口：
POST http://localhost:8081/api/rules/executeKnowledge
请求体：
{
    "id": "知识ID",
    "input": {
        "动态字段名": [...]  // 根据知识的inputField字段动态确定，如"transactions"或"resultTag"
    }
}

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-19
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import re


class RulesEngineMetricCalculationAgent:
    """规则引擎指标计算Agent"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化规则引擎指标计算Agent

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

        # 获取可用的知识元数据
        self.available_knowledge = self._load_available_knowledge()

        # 加载数据文件映射
        self.data_files = self._load_data_files()

        # 初始化API调用跟踪
        self.api_calls = []

    def _load_data_files(self) -> Dict[str, str]:
        """加载数据文件映射"""
        data_files = {}
        data_dir = "data_files"

        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.json'):
                    try:
                        # 提取文件名，用于匹配配置文件
                        key = file.replace('.json', '')
                        data_files[key] = os.path.join(data_dir, file)
                    except Exception as e:
                        print(f"处理数据文件 {file} 失败: {e}")

        return data_files

    def _select_data_file(self, input_filename: str) -> Optional[str]:
        """
        根据输入文件名选择对应的数据文件

        Args:
            input_filename: 配置文件中的input字段值

        Returns:
            数据文件路径，如果找不到则返回None
        """
        # input字段直接指定数据文件名
        if input_filename in self.data_files:
            return self.data_files[input_filename]

        # 如果找不到精确匹配，尝试模糊匹配
        for key, file_path in self.data_files.items():
            if input_filename in key or key in input_filename:
                return file_path

        return None

    def _load_table_data(self, data_file_path: str) -> List[Dict[str, Any]]:
        """加载数据文件中的JSON数据"""
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # 如果是字典，尝试提取其中的数组数据
                    for key, value in data.items():
                        if isinstance(value, list):
                            return value
                    return []
                else:
                    return []
        except Exception as e:
            print(f"加载数据文件 {data_file_path} 失败: {e}")
            return []

    def _load_configs(self) -> Dict[str, Dict]:
        """加载所有规则引擎配置文件"""
        configs = {}
        json_dir = "json_files"

        if os.path.exists(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith('.json') and '规则引擎' in file:
                    try:
                        with open(os.path.join(json_dir, file), 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            key = file.replace('.json', '')
                            configs[key] = config
                    except Exception as e:
                        print(f"加载规则引擎配置文件 {file} 失败: {e}")

        return configs

    def _load_available_knowledge(self) -> List[Dict[str, Any]]:
        """
        从规则引擎获取可用的知识元数据

        Returns:
            知识元数据列表，包含id、description和inputField
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

    def _get_input_field_for_knowledge(self, knowledge_id: str) -> str:
        """
        根据知识ID获取对应的inputField字段名

        Args:
            knowledge_id: 知识ID

        Returns:
            inputField字段名，默认为"transactions"
        """
        for knowledge in self.available_knowledge:
            if knowledge.get("id") == knowledge_id:
                input_field = knowledge.get("inputField", "transactions")
                print(f"🔗 知识 {knowledge_id} 使用输入字段: {input_field}")
                return input_field
        print(f"⚠️ 未找到知识 {knowledge_id} 的输入字段，使用默认值: transactions")
        return "transactions"  # 默认值

    async def calculate_metrics(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据意图识别结果进行规则引擎指标计算

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
                    # 使用传统的JSON配置文件方式
                    config = self.configs[config_name]
                    result = await self._call_rules_engine_api(config, intent_result, config_name)
                    results.append({
                        "config_name": config_name,
                        "result": result
                    })
                elif config_name.startswith("metric-"):
                    # 直接使用知识ID调用API，无需配置文件
                    result = await self._call_rules_engine_api_by_knowledge_id(config_name, intent_result)
                    results.append({
                        "config_name": config_name,
                        "result": result
                    })
                else:
                    results.append({
                        "config_name": config_name,
                        "error": f"配置文件 {config_name} 不存在，且不是有效的知识ID"
                    })

            return {
                "success": True,
                "results": results,
                "total_configs": len(target_configs),
                "successful_calculations": len([r for r in results if "result" in r])
            }

        except Exception as e:
            print(f"规则引擎指标计算失败: {e}")
            return {
                "success": False,
                "message": f"规则引擎指标计算过程中发生错误: {str(e)}",
                "results": []
            }

    async def _call_rules_engine_api(self, config: Dict[str, Any], intent_result: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """
        调用规则引擎API

        Args:
            config: 配置文件
            intent_result: 意图识别结果

        Returns:
            API调用结果
        """
        try:
            # 记录API调用开始
            start_time = datetime.now()

            # 规则引擎API配置
            method = "POST"
            url = "http://localhost:8081/api/rules/executeKnowledge"
            # url = "http://10.192.72.11:31809/api/rules/executeKnowledge"
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0"
            }
            timeout = 180  # 3分钟超时

            # 准备请求数据
            request_data = self._prepare_rules_engine_request_data(config, intent_result, config_name)

            # 调用API
            json_data = request_data.get("json", {})
            response = requests.post(url, headers=headers, json=json_data, timeout=timeout)

            # 处理响应
            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # 记录API调用结果
                    end_time = datetime.now()
                    call_id = f"rules_api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "RulesEngineMetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": config_name,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data,
                            "start_time": start_time.isoformat()
                        },
                        "response": {
                            "status_code": response.status_code,
                            "data": response_data,
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
                        print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

                    return {
                        "success": True,
                        "data": response_data,
                        "status_code": response.status_code
                    }
                except json.JSONDecodeError:
                    # 记录API调用结果（JSON解析失败）
                    end_time = datetime.now()
                    call_id = f"rules_api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "RulesEngineMetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": config_name,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data,
                            "start_time": start_time.isoformat()
                        },
                        "response": {
                            "status_code": response.status_code,
                            "data": response.text,
                            "error": "JSON解析失败",
                            "end_time": end_time.isoformat(),
                            "duration": (end_time - start_time).total_seconds()
                        },
                        "success": False
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
                        print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

                    return {
                        "success": True,
                        "data": response.text,
                        "status_code": response.status_code
                    }
            else:
                # 记录API调用结果（HTTP错误）
                end_time = datetime.now()
                call_id = f"rules_api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                api_call_info = {
                    "call_id": call_id,
                    "timestamp": end_time.isoformat(),
                    "agent": "RulesEngineMetricCalculationAgent",
                    "api_endpoint": url,
                    "config_name": config_name,
                    "request": {
                        "method": method,
                        "url": url,
                        "headers": headers,
                        "json_data": json_data,
                        "start_time": start_time.isoformat()
                    },
                    "response": {
                        "status_code": response.status_code,
                        "error": response.text,
                        "end_time": end_time.isoformat(),
                        "duration": (end_time - start_time).total_seconds()
                    },
                    "success": False
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
                    print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
                except Exception as e:
                    print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

                return {
                    "success": False,
                    "message": f"规则引擎API调用失败，状态码: {response.status_code}",
                    "response": response.text
                }

        except requests.exceptions.Timeout:
            # 记录API调用结果（超时）
            end_time = datetime.now()
            call_id = f"rules_api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "RulesEngineMetricCalculationAgent",
                "api_endpoint": url,
                "config_name": config_name,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json_data": json_data if 'json_data' in locals() else None,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "error": "API调用超时",
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds()
                },
                "success": False
            }
            self.api_calls.append(api_call_info)

            return {
                "success": False,
                "message": "规则引擎API调用超时"
            }
        except requests.exceptions.RequestException as e:
            # 记录API调用结果（请求异常）
            end_time = datetime.now()
            call_id = f"rules_api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "RulesEngineMetricCalculationAgent",
                "api_endpoint": url,
                "config_name": config_name,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json_data": json_data if 'json_data' in locals() else None,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "error": str(e),
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds()
                },
                "success": False
            }
            self.api_calls.append(api_call_info)

            return {
                "success": False,
                "message": f"规则引擎API调用异常: {str(e)}"
            }
        except Exception as e:
            # 记录API调用结果（其他异常）
            end_time = datetime.now()
            call_id = f"rules_api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "RulesEngineMetricCalculationAgent",
                "api_endpoint": url,
                "config_name": config_name,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json_data": json_data if 'json_data' in locals() else None,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "error": str(e),
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds()
                },
                "success": False
            }
            self.api_calls.append(api_call_info)

            return {
                "success": False,
                "message": f"处理规则引擎API调用时发生错误: {str(e)}"
            }

    def _prepare_rules_engine_request_data(self, config: Dict[str, Any], intent_result: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """
        准备规则引擎API请求数据

        Args:
            config: 配置文件
            intent_result: 意图识别结果
            config_name: 配置文件名

        Returns:
            请求数据
        """
        # 从配置文件中获取id和input
        request_id = config.get("id", "")
        input_filename = config.get("input", "")

        # 加载对应的数据文件
        input_data = {}
        if input_filename:
            data_file_path = self._select_data_file(input_filename)
            if data_file_path:
                input_data = self._load_table_data(data_file_path)
            else:
                print(f"警告：找不到配置文件 {config_name} 对应的数据文件: {input_filename}")

        # 构造API请求体
        request_data = {
            "id": request_id,
            "input": input_data
        }

        return {"json": request_data}

    async def _call_rules_engine_api_by_knowledge_id(self, knowledge_id: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        直接通过知识ID调用规则引擎API

        Args:
            knowledge_id: 知识ID，如 "metric-分析账户数量"
            intent_result: 意图识别结果（用于获取数据文件信息）

        Returns:
            API调用结果
        """
        # 记录API调用开始
        start_time = datetime.now()

        # 规则引擎API配置
        method = "POST"
        url = "http://localhost:8081/api/rules/executeKnowledge"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0"
        }
        timeout = 180  # 3分钟超时

        try:
            # 根据知识ID获取正确的输入字段名
            input_field_name = self._get_input_field_for_knowledge(knowledge_id)

            # 构造请求数据 - 直接使用默认数据文件
            # 从intent_result中获取数据文件名，如果没有则使用默认的农业数据
            input_filename = intent_result.get("data_file", "加工数据-流水分析-农业打标.json")

            # 加载对应的数据文件
            input_data = {}
            if input_filename:
                data_file_path = self._select_data_file(input_filename)
                if data_file_path:
                    raw_data = self._load_table_data(data_file_path)
                    # 使用正确的字段名包装数据
                    input_data = {input_field_name: raw_data}
                else:
                    print(f"警告：找不到数据文件: {input_filename}")
                    input_data = {input_field_name: []}

            # 构造API请求体
            request_data = {
                "id": knowledge_id,  # 直接使用知识ID
                "input": input_data
            }

            # 调用API
            json_data = request_data
            response = requests.post(url, headers=headers, json=json_data, timeout=timeout)

            # 处理响应（复用现有的响应处理逻辑）
            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # 记录API调用结果
                    end_time = datetime.now()
                    call_id = f"rules_api_{knowledge_id}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "RulesEngineMetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": knowledge_id,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data,
                            "start_time": start_time.isoformat()
                        },
                        "response": {
                            "status_code": response.status_code,
                            "data": response_data,
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
                        print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

                    return {
                        "success": True,
                        "data": response_data,
                        "status_code": response.status_code
                    }
                except json.JSONDecodeError:
                    # 记录JSON解析失败的API调用
                    end_time = datetime.now()
                    call_id = f"rules_api_{knowledge_id}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "RulesEngineMetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": knowledge_id,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data,
                            "start_time": start_time.isoformat()
                        },
                        "response": {
                            "status_code": response.status_code,
                            "data": response.text,
                            "error": "JSON解析失败",
                            "end_time": end_time.isoformat(),
                            "duration": (end_time - start_time).total_seconds()
                        },
                        "success": False
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
                        print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

                    return {
                        "success": True,
                        "data": response.text,
                        "status_code": response.status_code
                    }
            else:
                # 记录失败的API调用
                end_time = datetime.now()
                call_id = f"rules_api_{knowledge_id}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                api_call_info = {
                    "call_id": call_id,
                    "timestamp": end_time.isoformat(),
                    "agent": "RulesEngineMetricCalculationAgent",
                    "api_endpoint": url,
                    "config_name": knowledge_id,
                    "request": {
                        "method": method,
                        "url": url,
                        "headers": headers,
                        "json_data": json_data,
                        "start_time": start_time.isoformat()
                    },
                    "response": {
                        "status_code": response.status_code,
                        "error": response.text,
                        "end_time": end_time.isoformat(),
                        "duration": (end_time - start_time).total_seconds()
                    },
                    "success": False
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
                    print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
                except Exception as e:
                    print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

                return {
                    "success": False,
                    "message": f"规则引擎API调用失败，状态码: {response.status_code}",
                    "response": response.text
                }

        except requests.exceptions.Timeout:
            # 记录API调用结果（超时）
            end_time = datetime.now()
            call_id = f"rules_api_{knowledge_id}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "RulesEngineMetricCalculationAgent",
                "api_endpoint": url,
                "config_name": knowledge_id,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json_data": json_data if 'json_data' in locals() else None,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "error": "API调用超时",
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds()
                },
                "success": False
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
                print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
            except Exception as e:
                print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

            return {
                "success": False,
                "message": "规则引擎API调用超时"
            }
        except requests.exceptions.RequestException as e:
            # 记录API调用结果（请求异常）
            end_time = datetime.now()
            call_id = f"rules_api_{knowledge_id}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "RulesEngineMetricCalculationAgent",
                "api_endpoint": url,
                "config_name": knowledge_id,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json_data": json_data if 'json_data' in locals() else None,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "error": str(e),
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds()
                },
                "success": False
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
                print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
            except Exception as e:
                print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

            return {
                "success": False,
                "message": f"规则引擎API调用异常: {str(e)}"
            }
        except Exception as e:
            # 记录API调用结果（其他异常）
            end_time = datetime.now()
            call_id = f"rules_api_{knowledge_id}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
            api_call_info = {
                "call_id": call_id,
                "timestamp": end_time.isoformat(),
                "agent": "RulesEngineMetricCalculationAgent",
                "api_endpoint": url,
                "config_name": knowledge_id,
                "request": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "json_data": json_data if 'json_data' in locals() else None,
                    "start_time": start_time.isoformat()
                },
                "response": {
                    "error": str(e),
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds()
                },
                "success": False
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
                print(f"[RULES_API_RESULT] 保存规则引擎API结果文件: {filepath}")
            except Exception as e:
                print(f"[ERROR] 保存规则引擎API结果文件失败: {filepath}, 错误: {str(e)}")

            return {
                "success": False,
                "message": f"处理规则引擎API调用时发生错误: {str(e)}"
            }

    def get_available_configs(self) -> List[str]:
        """获取所有可用的规则引擎配置文件名"""
        return list(self.configs.keys())

    def get_config_details(self, config_name: str) -> Optional[Dict]:
        """获取指定配置文件的详细信息"""
        return self.configs.get(config_name)