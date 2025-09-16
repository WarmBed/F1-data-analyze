#!/usr/bin/env python3
"""
F1 Analysis API - 分析相關路由
處理所有分析執行相關的端點

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import time

# 導入服務
from api.services.simple_analysis_service import SimpleF1AnalysisService

# 創建路由器
router = APIRouter(
    prefix="/analysis",
    tags=["分析執行"],
    responses={
        404: {"description": "分析功能不存在"},
        500: {"description": "服務器內部錯誤"}
    }
)

# 初始化服務
analysis_service = SimpleF1AnalysisService()


@router.post("/execute")
async def execute_analysis(
    function_id: int = Query(..., ge=1, le=52, description="分析功能 ID (1-52)"),
    year: int = Query(..., ge=2024, le=2025, description="賽季年份"),
    race: str = Query(..., min_length=3, description="賽事名稱"),
    session: str = Query(..., description="會話類型 (R/Q/FP1/FP2/FP3)"),
    driver1: Optional[str] = Query(None, min_length=3, max_length=3, description="主要車手代碼"),
    driver2: Optional[str] = Query(None, min_length=3, max_length=3, description="比較車手代碼"),
    force_refresh: bool = Query(False, description="強制重新執行分析")
) -> Dict[str, Any]:
    """
    執行 F1 分析功能
    
    - **function_id**: 分析功能 ID (1-52)
    - **year**: 賽季年份 (2024-2025)
    - **race**: 賽事名稱 (例如: Japan, Italy)
    - **session**: 會話類型 (R=正賽, Q=排位賽, FP1/2/3=練習賽)
    - **driver1**: 主要車手代碼 (3字母, 例如: VER)
    - **driver2**: 比較車手代碼 (用於車手比較分析)
    - **force_refresh**: 是否強制重新執行 (忽略緩存)
    """
    
    try:
        # 建構參數
        params = {
            "year": year,
            "race": race,
            "session": session
        }
        
        if driver1:
            params["driver1"] = driver1.upper()
        if driver2:
            params["driver2"] = driver2.upper()
        if force_refresh:
            params["force_refresh"] = True
            
        # 執行分析
        result = await analysis_service.execute_analysis(function_id, **params)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "分析執行失敗",
                "message": str(e),
                "function_id": function_id,
                "timestamp": time.time()
            }
        )


@router.get("/functions")
async def get_supported_functions() -> Dict[str, Any]:
    """
    獲取支持的分析功能列表
    
    返回所有可用的分析功能及其描述
    """
    
    functions = {
        "basic_analysis": {
            "name": "基礎分析",
            "functions": {
                1: "降雨分析",
                3: "車手成績分析", 
                4: "車隊積分統計",
                6: "進站策略分析"
            }
        },
        "telemetry_analysis": {
            "name": "遙測分析", 
            "functions": {
                12: "全車手遙測分析",
                13: "車手遙測比較",
                14: "詳細單圈分析",
                15: "超車統計分析"
            }
        },
        "pitstop_analysis": {
            "name": "進站分析",
            "functions": {
                16: "車手詳細進站記錄",
                17: "車手最快進站排名", 
                18: "車隊進站排名",
                19: "輪胎策略分析"
            }
        },
        "race_analysis": {
            "name": "賽事分析",
            "functions": {
                20: "事故分析",
                21: "賽道邊界違規",
                22: "處罰統計",
                23: "安全車分析"
            }
        }
    }
    
    return {
        "success": True,
        "message": "支持的分析功能",
        "total_functions": sum(len(cat["functions"]) for cat in functions.values()),
        "categories": len(functions),
        "functions": functions,
        "function_range": "1-52",
        "timestamp": time.time()
    }


@router.get("/status")
async def get_analysis_status() -> Dict[str, Any]:
    """
    獲取分析服務狀態
    
    返回服務健康狀態和性能指標
    """
    
    try:
        health_result = await analysis_service.health_check()
        cache_result = await analysis_service.get_cache_status()
        
        return {
            "success": True,
            "message": "分析服務狀態",
            "service_health": health_result,
            "cache_status": cache_result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "狀態檢查失敗",
            "error": str(e),
            "timestamp": time.time()
        }
