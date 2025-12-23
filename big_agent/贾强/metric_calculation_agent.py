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
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import re


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
                        # 提取文件名中的关键词，用于匹配配置文件
                        key = file.replace('原始数据-流水分析-', '').replace('.json', '')
                        data_files[key] = os.path.join(data_dir, file)
                    except Exception as e:
                        print(f"处理数据文件 {file} 失败: {e}")

        return data_files

    def _select_data_file(self, config_name: str) -> Optional[str]:
        """
        根据配置文件名选择对应的数据文件

        Args:
            config_name: 配置文件名

        Returns:
            数据文件路径，如果找不到则返回None
        """
        # 配置文件名模式：指标计算-{category}-{metric}.json
        # 数据文件名模式：原始数据-流水分析-{category}.json

        # 从配置文件名中提取类别信息
        match = re.search(r'指标计算-(.+?)-', config_name)
        if match:
            category = match.group(1)

            # 优先选择原始数据文件
            # 1. 首先查找完全匹配的原始数据文件
            if category in self.data_files:
                file_path = self.data_files[category]
                if '原始数据' in file_path:
                    return file_path

            # 2. 如果没有完全匹配，查找包含类别的原始数据文件
            for key, file_path in self.data_files.items():
                if category in key and '原始数据' in file_path:
                    return file_path

        # 如果找不到匹配的文件，返回默认的农业原始数据文件（如果存在）
        if '农业' in self.data_files:
            return self.data_files['农业']

        return None

    def _load_table_data(self, data_file_path: str) -> List[Dict]:
        """加载数据文件中的表格数据"""
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"加载数据文件 {data_file_path} 失败: {e}")
            return []

    def _load_configs(self) -> Dict[str, Dict]:
        """加载所有配置文件"""
        configs = {}
        json_dir = "json_files"

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
                    result = await self._call_metric_api(config, intent_result, config_name)
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

    async def _call_metric_api(self, config: Dict[str, Any], intent_result: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """
        调用具体的指标计算API

        Args:
            config: 配置文件
            intent_result: 意图识别结果

        Returns:
            API调用结果
        """
        try:
            # 记录API调用开始
            start_time = datetime.now()

            # 使用真实API服务的配置
            method = "POST"
            url = "http://10.192.72.11:6300/api/data_analyst/full"  # 真实API服务地址
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0"
            }
            timeout = 600  # 10分钟超时，给慢API更多时间

            # 添加重试机制，最多重试3次
            max_retries = 3
            retry_delay = 5  # 每次重试间隔5秒

            for attempt in range(max_retries):
                try:
                    print(f"🔄 API调用尝试 {attempt + 1}/{max_retries} (配置: {config_name})")

                    # 准备请求数据
                    request_data = self._prepare_request_data(config, intent_result, config_name)

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

                            # 检查API响应结构并提取结果
                            extracted_result = None
                            if isinstance(response_data, dict):
                                # 检查是否有code字段和data.result结构
                                if response_data.get("code") == 0 and "data" in response_data:
                                    data = response_data["data"]
                                    if "result" in data:
                                        # 从result字段中提取JSON
                                        extracted_result = self._extract_json_from_result(data["result"])

                            # 记录API调用结果
                            end_time = datetime.now()
                            call_id = f"api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                            api_call_info = {
                                "call_id": call_id,
                                "timestamp": end_time.isoformat(),
                                "agent": "MetricCalculationAgent",
                                "api_endpoint": url,
                                "config_name": config_name,
                                "request": {
                                    "method": method,
                                    "url": url,
                                    "headers": headers,
                                    "json_data": json_data if method.upper() == "POST" else None,
                                    "params": params if method.upper() == "GET" else None,
                                    "start_time": start_time.isoformat()
                                },
                                "response": {
                                    "status_code": response.status_code,
                                    "data": response_data,
                                    "extracted_result": extracted_result,
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

                            return {
                                "success": True,
                                "data": response_data,
                                "extracted_result": extracted_result,
                                "status_code": response.status_code
                            }
                        except json.JSONDecodeError:
                            # 记录API调用结果（JSON解析失败）
                            end_time = datetime.now()
                            call_id = f"api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                            api_call_info = {
                                "call_id": call_id,
                                "timestamp": end_time.isoformat(),
                                "agent": "MetricCalculationAgent",
                                "api_endpoint": url,
                                "config_name": config_name,
                                "request": {
                                    "method": method,
                                    "url": url,
                                    "headers": headers,
                                    "json_data": json_data if method.upper() == "POST" else None,
                                    "params": params if method.upper() == "GET" else None,
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
                            filename = f"{call_id}.json"
                            filepath = os.path.join(api_results_dir, filename)

                            try:
                                with open(filepath, 'w', encoding='utf-8') as f:
                                    json.dump(api_call_info, f, ensure_ascii=False, indent=2)
                                print(f"[API_RESULT] 保存API结果文件: {filepath}")
                            except Exception as e:
                                print(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

                            return {
                                "success": True,
                                "data": response.text,
                                "extracted_result": None,
                                "status_code": response.status_code
                            }
                    else:
                        # 记录API调用结果（HTTP错误）
                        end_time = datetime.now()
                        call_id = f"api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                        api_call_info = {
                            "call_id": call_id,
                            "timestamp": end_time.isoformat(),
                            "agent": "MetricCalculationAgent",
                            "api_endpoint": url,
                            "config_name": config_name,
                            "request": {
                                "method": method,
                                "url": url,
                                "headers": headers,
                                "json_data": json_data if method.upper() == "POST" else None,
                                "params": params if method.upper() == "GET" else None,
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
                            print(f"[API_RESULT] 保存API结果文件: {filepath}")
                        except Exception as e:
                            print(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

                        return {
                            "success": False,
                            "message": f"API调用失败，状态码: {response.status_code}",
                            "response": response.text
                        }

                    # 如果执行到这里，说明本次尝试成功，跳出重试循环
                    break

                except requests.exceptions.Timeout:
                    # 记录API调用结果（超时）
                    end_time = datetime.now()
                    call_id = f"api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "MetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": config_name,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data if method.upper() == "POST" else None,
                            "params": params if method.upper() == "GET" else None,
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
                        print(f"[API_RESULT] 保存API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        print(f"⏳ API调用超时，{retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "message": "API调用超时"
                        }
                except requests.exceptions.RequestException as e:
                    # 记录API调用结果（请求异常）
                    end_time = datetime.now()
                    call_id = f"api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "MetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": config_name,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data if method.upper() == "POST" else None,
                            "params": params if method.upper() == "GET" else None,
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
                        print(f"[API_RESULT] 保存API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        print(f"❌ API调用异常: {str(e)}，{retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "message": f"API调用异常: {str(e)}"
                        }
                except Exception as e:
                    # 记录API调用结果（其他异常）
                    end_time = datetime.now()
                    call_id = f"api_{config_name}_{'{:.2f}'.format((end_time - start_time).total_seconds())}"
                    api_call_info = {
                        "call_id": call_id,
                        "timestamp": end_time.isoformat(),
                        "agent": "MetricCalculationAgent",
                        "api_endpoint": url,
                        "config_name": config_name,
                        "request": {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "json_data": json_data if method.upper() == "POST" else None,
                            "params": params if method.upper() == "GET" else None,
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
                        print(f"[API_RESULT] 保存API结果文件: {filepath}")
                    except Exception as e:
                        print(f"[ERROR] 保存API结果文件失败: {filepath}, 错误: {str(e)}")

                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        print(f"❌ 其他异常: {str(e)}，{retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "message": f"API调用异常: {str(e)}"
                        }
        except Exception as e:
            # 处理所有未捕获的异常
            print(f"❌ API调用过程中发生未预期的错误: {str(e)}")
            return {
                "success": False,
                "message": f"API调用过程中发生未预期的错误: {str(e)}"
            }

    def _prepare_request_data(self, config: Dict[str, Any], intent_result: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """
        准备API请求数据

        Args:
            config: 配置文件
            intent_result: 意图识别结果
            config_name: 配置文件名

        Returns:
            请求数据
        """
        # 从配置文件中获取question和prompt
        question = config.get("question", "")
        prompt = config.get("prompt", "")

        # 选择对应的数据文件
        data_file_path = self._select_data_file(config_name)
        table_data = []

        if data_file_path:
            table_data = self._load_table_data(data_file_path)
        else:
            print(f"警告：找不到配置文件 {config_name} 对应的数据文件")

        # 构造documents数组
        documents = []
        if table_data:
            # 使用数据文件名作为标题
            title = f"数据表-{config_name}"
            if data_file_path:
                title = os.path.basename(data_file_path).replace('.json', '')

            documents.append({
                "id": 1,
                "title": title,
                "text": "",
                "table": table_data
            })

        # 构造API请求体
        request_data = {
            "disable_planning": False,
            "question": question,
            "prompt": prompt,
            "documents": documents
        }

        return {"json": request_data}

    def _extract_json_from_result(self, result_text: str) -> Dict[str, Any]:
        """
        从API结果文本中提取JSON内容

        Args:
            result_text: API返回的result字段内容

        Returns:
            提取的JSON对象
        """
        import re
        import json

        try:
            # 查找```json和```之间的内容
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)

            # 如果没有```json标记，查找大括号包围的内容
            brace_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if brace_match:
                json_str = brace_match.group(0).strip()
                return json.loads(json_str)

            # 如果都找不到，尝试直接解析整个文本
            return json.loads(result_text.strip())

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error": f"无法解析JSON结果: {str(e)}", "raw_result": result_text}

    def get_available_configs(self) -> List[str]:
        """获取所有可用的配置文件名"""
        return list(self.configs.keys())

    def get_config_details(self, config_name: str) -> Optional[Dict]:
        """获取指定配置文件的详细信息"""
        return self.configs.get(config_name)
