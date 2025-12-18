"""
模拟API服务器 (Mock API Server)
=============================

这是一个基于FastAPI的模拟农业指标计算API服务器，用于开发和测试环境。

核心功能：
1. 农业支出指标计算API
   - 模拟生产资料支出、劳动力支出、土地租金等成本计算
   - 支持多种计算方法（标准、高级、自定义）
   - 返回详细的成本结构分析

2. 农业收入指标计算API
   - 模拟农产品销售收入、补贴收入等收益计算
   - 支持国内市场和出口市场区分
   - 包含政府补贴和扶持资金

3. 健康检查API
   - 服务器状态监控
   - 服务可用性检查
   - 基本系统信息

技术实现：
- 使用FastAPI框架构建RESTful API
- Pydantic数据验证和序列化
- 模拟数据生成器（基于随机算法）
- 异步请求处理
- CORS跨域支持

API端点：
- POST /agriculture/expense-calculation  - 支出指标计算
- POST /agriculture/income-calculation   - 收入指标计算
- GET /health                           - 健康检查

模拟数据特点：
- 结果具有随机性但保持合理性
- 包含置信度评分和元数据
- 支持参数化查询
- 模拟网络延迟和处理时间

使用场景：
- 开发环境测试（替代真实API）
- 演示系统功能
- 单元测试和集成测试
- API接口验证

注意事项：
- 此服务器仅用于开发和测试
- 生产环境应使用真实的计算服务
- 数据为模拟生成，不具备实际参考价值

作者: Big Agent Team
版本: 1.0.0
创建时间: 2024-12-18
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import time
from typing import Dict, Any, Optional
from datetime import datetime


app = FastAPI(
    title="农业指标计算API",
    description="模拟农业总支出和总收入指标计算服务",
    version="1.0.0"
)


# 请求模型
class ExpenseCalculationRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = {}
    csv_data: Optional[Dict[str, Any]] = {}
    time_period: Optional[str] = "2023"
    region: Optional[str] = "全国"
    crop_type: Optional[str] = "粮食作物"
    calculation_method: Optional[str] = "standard"


class IncomeCalculationRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = {}
    csv_data: Optional[Dict[str, Any]] = {}
    time_period: Optional[str] = "2023"
    region: Optional[str] = "全国"
    crop_type: Optional[str] = "粮食作物"
    market_type: Optional[str] = "both"
    include_subsidies: Optional[bool] = True


# 模拟数据生成器
def generate_expense_data(time_period: str, region: str, crop_type: str) -> Dict[str, Any]:
    """生成模拟的农业支出数据"""

    # 基础数据范围
    base_expense = {
        "粮食作物": {"min": 8000, "max": 12000},
        "经济作物": {"min": 15000, "max": 25000},
        "蔬菜": {"min": 20000, "max": 35000},
        "水果": {"min": 25000, "max": 45000}
    }

    crop_data = base_expense.get(crop_type, base_expense["粮食作物"])

    # 根据地区调整系数
    region_multiplier = {
        "全国": 1.0,
        "东部": 1.2,
        "中部": 0.9,
        "西部": 0.8
    }.get(region, 1.0)

    # 根据时间周期调整
    year = int(time_period.split('-')[0]) if '-' in time_period else int(time_period)
    time_multiplier = 1.0 + (year - 2020) * 0.05  # 每年上涨5%

    base_total = random.uniform(crop_data["min"], crop_data["max"]) * region_multiplier * time_multiplier

    # 分项支出
    production_materials = base_total * random.uniform(0.35, 0.45)
    labor_cost = base_total * random.uniform(0.25, 0.35)
    land_rent = base_total * random.uniform(0.15, 0.25)
    equipment_depreciation = base_total * random.uniform(0.08, 0.12)
    other_costs = base_total * random.uniform(0.02, 0.08)

    # 调整以确保总和正确
    total_calculated = production_materials + labor_cost + land_rent + equipment_depreciation + other_costs
    adjustment_factor = base_total / total_calculated

    production_materials *= adjustment_factor
    labor_cost *= adjustment_factor
    land_rent *= adjustment_factor
    equipment_depreciation *= adjustment_factor
    other_costs *= adjustment_factor

    return {
        "total_expense": round(base_total, 2),
        "expense_breakdown": {
            "production_materials": round(production_materials, 2),
            "labor_cost": round(labor_cost, 2),
            "land_rent": round(land_rent, 2),
            "equipment_depreciation": round(equipment_depreciation, 2),
            "other_costs": round(other_costs, 2)
        },
        "calculation_metadata": {
            "method_used": "standard_simulation",
            "data_sources": ["农业统计年鉴", "农产品价格监测系统"],
            "confidence_level": round(random.uniform(0.85, 0.95), 2),
            "calculation_time": datetime.now().isoformat(),
            "region": region,
            "crop_type": crop_type,
            "time_period": time_period
        }
    }


def generate_income_data(time_period: str, region: str, crop_type: str,
                        market_type: str, include_subsidies: bool) -> Dict[str, Any]:
    """生成模拟的农业收入数据"""

    # 基础收入范围
    base_income = {
        "粮食作物": {"min": 10000, "max": 18000},
        "经济作物": {"min": 20000, "max": 40000},
        "蔬菜": {"min": 30000, "max": 60000},
        "水果": {"min": 35000, "max": 70000}
    }

    crop_data = base_income.get(crop_type, base_income["粮食作物"])

    # 根据地区调整系数
    region_multiplier = {
        "全国": 1.0,
        "东部": 1.3,
        "中部": 0.95,
        "西部": 0.85
    }.get(region, 1.0)

    # 根据市场类型调整
    market_multiplier = {
        "domestic": 0.9,
        "export": 1.4,
        "both": 1.0
    }.get(market_type, 1.0)

    # 根据时间周期调整
    year = int(time_period.split('-')[0]) if '-' in time_period else int(time_period)
    time_multiplier = 1.0 + (year - 2020) * 0.03  # 每年上涨3%

    base_total = random.uniform(crop_data["min"], crop_data["max"]) * region_multiplier * market_multiplier * time_multiplier

    # 分项收入
    crop_sales = base_total * random.uniform(0.7, 0.85)
    livestock_sales = base_total * random.uniform(0.05, 0.15) if random.random() > 0.7 else 0
    subsidy_income = random.uniform(1000, 5000) if include_subsidies else 0
    other_income = base_total * random.uniform(0.02, 0.08)

    # 调整以确保总和正确
    total_calculated = crop_sales + livestock_sales + subsidy_income + other_income
    if total_calculated > 0:
        adjustment_factor = base_total / total_calculated
        crop_sales *= adjustment_factor
        livestock_sales *= adjustment_factor
        other_income *= adjustment_factor
        # 补贴不调整

    # 盈利能力指标
    total_cost = base_total * random.uniform(0.7, 0.9)  # 假设成本占收入的70-90%
    gross_profit = base_total - total_cost
    gross_profit_margin = gross_profit / base_total if base_total > 0 else 0
    net_profit = gross_profit * random.uniform(0.8, 0.95)  # 扣除税费等
    net_profit_margin = net_profit / base_total if base_total > 0 else 0

    return {
        "total_income": round(base_total, 2),
        "income_breakdown": {
            "crop_sales": round(crop_sales, 2),
            "livestock_sales": round(livestock_sales, 2),
            "subsidy_income": round(subsidy_income, 2),
            "other_income": round(other_income, 2)
        },
        "profitability_metrics": {
            "gross_profit_margin": round(gross_profit_margin, 4),
            "net_profit_margin": round(net_profit_margin, 4),
            "return_on_investment": round(net_profit / total_cost if total_cost > 0 else 0, 4)
        },
        "calculation_metadata": {
            "method_used": "advanced_simulation",
            "data_sources": ["农业农村部统计数据", "农产品批发市场价格", "财政补贴发放系统"],
            "confidence_level": round(random.uniform(0.88, 0.96), 2),
            "calculation_time": datetime.now().isoformat(),
            "region": region,
            "crop_type": crop_type,
            "market_type": market_type,
            "include_subsidies": include_subsidies,
            "time_period": time_period
        }
    }


@app.post("/agriculture/expense-calculation")
async def calculate_expense(request: ExpenseCalculationRequest):
    """农业总支出指标计算API"""
    try:
        # 模拟处理时间
        time.sleep(random.uniform(0.5, 1.5))

        # 提取参数
        time_period = request.time_period or request.parameters.get("time_period", "2023")
        region = request.region or request.parameters.get("region", "全国")
        crop_type = request.crop_type or request.parameters.get("crop_type", "粮食作物")

        # 生成模拟数据
        result = generate_expense_data(time_period, region, crop_type)

        return {
            "success": True,
            "data": result,
            "request_id": f"expense_{int(time.time())}_{random.randint(1000, 9999)}",
            "processing_time": round(random.uniform(0.5, 1.5), 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@app.post("/agriculture/income-calculation")
async def calculate_income(request: IncomeCalculationRequest):
    """农业总收入指标计算API"""
    try:
        # 模拟处理时间
        time.sleep(random.uniform(0.8, 2.0))

        # 提取参数
        time_period = request.time_period or request.parameters.get("time_period", "2023")
        region = request.region or request.parameters.get("region", "全国")
        crop_type = request.crop_type or request.parameters.get("crop_type", "粮食作物")
        market_type = request.market_type or request.parameters.get("market_type", "both")
        include_subsidies = request.include_subsidies if request.include_subsidies is not None else request.parameters.get("include_subsidies", True)

        # 生成模拟数据
        result = generate_income_data(time_period, region, crop_type, market_type, include_subsidies)

        return {
            "success": True,
            "data": result,
            "request_id": f"income_{int(time.time())}_{random.randint(1000, 9999)}",
            "processing_time": round(random.uniform(0.8, 2.0), 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": ["expense-calculation", "income-calculation"]
    }


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "农业指标计算API服务",
        "version": "1.0.0",
        "endpoints": [
            "/agriculture/expense-calculation (POST)",
            "/agriculture/income-calculation (POST)",
            "/health (GET)"
        ],
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    print("启动模拟API服务器...")
    print("访问 http://localhost:8000/docs 查看API文档")
    print("访问 http://localhost:8000/health 检查服务状态")
    uvicorn.run(app, host="127.0.0.1", port=8000)
