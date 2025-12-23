#!/usr/bin/env python3
"""
规则生成器
===========

此脚本用于生成数据处理规则，包括：
1. 使用DeepSeek大模型生成规则内容(ruleContent)
2. 调用规则引擎API保存生成的决策知识

作者: Big Agent Team
版本: 1.0.0
"""

import json
import os
import sys
import requests
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


class RuleGenerator:
    """规则生成器：使用大模型生成数据处理规则"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化规则生成器

        Args:
            api_key: DeepSeek API密钥
            base_url: DeepSeek API基础URL
        """
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY环境变量未设置")

        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1
        )

    def generate_rule_content(self, requirement_description: str) -> List[Dict[str, Any]]:
        """
        使用大模型生成规则内容

        Args:
            requirement_description: 规则要求的自然语言描述

        Returns:
            规则内容JSON数组
        """
        prompt_template = """
请根据以下规范，生成一个数据处理规则的 JSON 数组 `ruleContent`。

**规则链说明**：
数据在处理链中流动。第一个操作的 sourceField 通常是 "transactions"（原始交易数据），后续操作的 sourceField 是前一个操作的 resultField。请确保字段名前后连贯。

**重要字段名规范**：
- 交易方向: "txDirection" ("收入"或"支出")
- 交易金额: "txAmount" (正数为收入，负数为支出)
- 交易摘要: "txSummary"
- 交易对手: "txCounterparty"
- 交易日期: "txDate"
- 交易时间: "txTime"
- 交易ID: "txId"
- 账户余额: "txBalance"

**可用操作类型 (type)**:
- `ADDTAG`: 添加业务标签，根据条件为数据添加业务类型标签
- `CONDITIONAL`: 条件过滤，根据条件筛选数据
- `GROUP_BY`: 分组聚合，按指定字段分组并进行聚合计算
- `SORT`: 排序操作，按指定字段和方向排序
- `TIME_RANGE`: 时间范围统计，计算数据的时间范围
- `PROPORTION`: 占比分析，计算各类别的占比情况

**字段说明**:
- `type`: 操作类型
- `sourceField`: 输入数据源字段名
- `resultField`: 输出结果字段名
- `primaryValue`: 主要配置值（根据操作类型含义不同）
- `secondaryValue`: 辅助配置值（根据操作类型含义不同）
- `configuration`: 扩展配置Map（用于复杂配置）

**各操作类型详细配置**:

**ADDTAG** (添加标签):
- `primaryValue`: 标签值（如"收入/经营/经营收入（农业）"）
- `secondaryValue`: 空字符串 ""
- `configuration.tagField`: 标签字段名（如"businessType"）
- `configuration.conditionGroups`: 条件组数组，每个条件组包含logic("AND"/"OR")和conditions数组
- `conditions`格式: {{"field": "字段名", "operator": "操作符", "value": "比较值"}}

**CONDITIONAL** (条件过滤):
- `configuration.conditionGroups`: 条件组数组，格式同ADDTAG

**GROUP_BY** (分组聚合):
- `configuration.groupByFields`: 分组字段数组（如["txCounterparty"]）
- `configuration.groupAggregations`: 聚合操作数组，每个包含type("AGGREGATE")、primaryValue("SUM"等)、sourceField、resultField

**SORT** (排序):
- `primaryValue`: 排序字段名
- `secondaryValue`: 排序方向（1升序，-1降序）

**TIME_RANGE** (时间范围):
- `primaryValue`: 时间字段名（如"txDate"）

**PROPORTION** (占比分析):
- `primaryValue`: 数值字段名（如"txAmount"）
- `secondaryValue`: 分类字段名（如"txDirection"）
- `configuration`: 可选，用于复杂占比分析

**操作符**: `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `GREATER_THAN`, `LESS_THAN`, `GREATER_THAN_OR_EQUAL`, `LESS_THAN_OR_EQUAL`, `REGEX_MATCH`

**生成要求**:
请根据以下自然语言描述生成规则链：
{requirement_description}

**输出格式**:
只输出JSON数组，不要包含其他解释文字。确保生成的JSON符合上述结构规范。
"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        parser = JsonOutputParser()

        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({"requirement_description": requirement_description})
            return result
        except Exception as e:
            print(f"生成规则内容失败: {e}")
            return []

    def create_decision_knowledge_payload(self,
                                        id: str,
                                        name: str,
                                        ruleDescription: str,
                                        zone_id: str = "kz_third_001",
                                        system_id: str = "ks_001",
                                        tree_id: str = "kt_second_001") -> Dict[str, Any]:
        """
        创建决策知识保存的payload

        Args:
            id: 决策知识和规则的ID
            name: 决策知识和规则的名称
            ruleDescription: 规则描述（同时作为规则要求的自然语言描述）
            zone_id: 区域ID
            system_id: 系统ID
            tree_id: 树ID

        Returns:
            API调用的完整payload
        """

        # 生成规则内容
        rule_content = self.generate_rule_content(ruleDescription)

        if not rule_content:
            raise ValueError("生成规则内容失败")

        # 获取最后一个操作的resultField作为outputSchema
        last_operation = rule_content[-1] if rule_content else {}
        output_field = last_operation.get("resultField", "result")

        payload = {
            "decisionKnowledge": {
                "id": id,
                "name": name,
                "zoneId": zone_id,
                "systemId": system_id,
                "treeId": tree_id,
                "factorDescription": f"基于{ruleDescription[:20]}...的银行流水分类决策因子",
                "businessTags": "打标,分类",
                "version": "v1.0",
                "supportKnowledgeRefs": [
                    "经营贷",
                    "分组计算"
                ],
                "publisher": "system",
                "status": 2,
                "applicationStatus": 2,
                "operator": "system"
            },
            "ruleDefinition": {
                "name": f"rule-{name}",
                "ruleType": 1,
                "ruleDescription": ruleDescription,
                "inputSchema": [
                    "input"
                ],
                "outputSchema": [
                    output_field
                ],
                "ruleContent": rule_content,
                "priority": 1,
                "enabled": True,
                "version": "v1.0",
                "status": 2,
                "operator": "system",
                "isDeleted": 0
            }
        }

        return payload

    def save_decision_knowledge(self, payload: Dict[str, Any], api_url: str = "http://localhost:8081") -> bool:
        """
        保存决策知识到规则引擎

        Args:
            payload: 决策知识payload
            api_url: API基础URL

        Returns:
            保存是否成功
        """
        url = f"{api_url}/api/rules/saveDecisionKnowledge"

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanRuntime-ApipostRuntime/1.1.0'
        }

        try:
            print(f"正在保存决策知识: {payload['decisionKnowledge']['id']}")
            print(f"API URL: {url}")

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            print(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                print("决策知识保存成功!")
                return True
            else:
                print(f"保存失败: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"API调用失败: {e}")
            return False


def main():
    """主函数：演示如何使用规则生成器"""

    # 初始化规则生成器
    try:
        generator = RuleGenerator(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
    except ValueError as e:
        print(f"初始化失败: {e}")
        return

    # 示例：生成黑色金属经营支出TOP3规则
    requirement_description = """
    筛选出业务类型为"支出/经营/经营支出（黑色金属）"的交易记录，
    按交易对手(txCounterparty)分组，
    计算每个交易对手的总支出金额(txAmount求和)，
    按总支出金额降序排序，取前3名
    """

    try:
        # 创建payload
        payload = generator.create_decision_knowledge_payload(
            id="demo-黑色金属-0302",
            name="demo-黑色金属-0302",
            ruleDescription="筛选出业务类型为'支出/经营/经营支出（黑色金属）'的交易记录，按交易对手分组，计算总支出金额，降序排序取前3名"
        )

        # 打印生成的规则内容
        print("生成的规则内容:")
        print(json.dumps(payload["ruleDefinition"]["ruleContent"], ensure_ascii=False, indent=2))

        # 保存到规则引擎
        success = generator.save_decision_knowledge(payload)

        if success:
            print("规则生成和保存完成!")
        else:
            print("规则保存失败，请检查规则引擎服务是否运行")

    except Exception as e:
        print(f"生成规则失败: {e}")


if __name__ == "__main__":
    main()
