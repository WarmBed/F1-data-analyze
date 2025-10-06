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
from api.models.function_specs import (
    FUNCTION_SPECS,
    function_id_sort_key,
    normalize_function_id,
)

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


SUPPORTED_FUNCTION_IDS = sorted(FUNCTION_SPECS.keys(), key=function_id_sort_key)


@router.post("/execute")
async def execute_analysis(
    function_id: str = Query(..., description="分析功能 ID"),
    year: int = Query(..., ge=2020, le=2025, description="賽季年份 (2020-2025)"),
    race: Optional[str] = Query(None, min_length=3, description="賽事名稱"),
    session: Optional[str] = Query(None, description="會話類型 (R/Q/FP1/FP2/FP3)"),
    driver1: Optional[str] = Query(None, min_length=3, max_length=3, description="主要車手代碼"),
    driver2: Optional[str] = Query(None, min_length=3, max_length=3, description="比較車手代碼"),
    force_refresh: bool = Query(False, description="強制重新執行分析"),
    lap: Optional[int] = Query(None, ge=1, description="統一圈數參數 (單圈分析)"),
    lap1: Optional[int] = Query(None, ge=1, description="車手1圈數 (遙測比較)"),
    lap2: Optional[int] = Query(None, ge=1, description="車手2圈數 (遙測比較)")
) -> Dict[str, Any]:
    """
    執行 F1 分析功能
    
    - **function_id**: 分析功能 ID (1-52)
    - **year**: 賽季年份 (2020-2025，與 CLI 功能一致)
    - **race**: 賽事名稱 (例如: Japan, Italy)
    - **session**: 會話類型 (R=正賽, Q=排位賽, FP1/2/3=練習賽)
    - **driver1**: 主要車手代碼 (3字母, 例如: VER)
    - **driver2**: 比較車手代碼 (用於車手比較分析)
    - **force_refresh**: 是否強制重新執行 (忽略緩存)
    """
    
    try:
        normalized_id = normalize_function_id(function_id)

        if normalized_id not in FUNCTION_SPECS:
            raise HTTPException(status_code=400, detail={
                "error": "unsupported_function",
                "message": f"function_id {function_id} 尚未透過 API 支援",
                "supported": SUPPORTED_FUNCTION_IDS,
            })

        # 建構參數
        params = {"year": year}

        if race:
            params["race"] = race
        if session:
            params["session"] = session
        
        if driver1:
            params["driver1"] = driver1.upper()
        if driver2:
            params["driver2"] = driver2.upper()
        if force_refresh:
            params["force_refresh"] = True
        if lap:
            params["lap"] = lap
        if lap1:
            params["lap1"] = lap1
        if lap2:
            params["lap2"] = lap2
            
        # 執行分析
        result = await analysis_service.execute_analysis(normalized_id, **params)

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_parameters",
                "message": str(exc),
                "function_id": function_id,
            },
        )

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
    try:
        functions = {
            spec.function_id: {
                "name": spec.name,
                "description": spec.description,
                "required_params": spec.required_params,
                "optional_params": spec.optional_params,
                "cache_patterns": spec.cache_patterns,
                "notes": spec.notes,
            }
            for spec in FUNCTION_SPECS.values()
        }

        return {
            "success": True,
            "message": "目前 API 支援的分析功能",
            "total_functions": len(functions),
            "functions": functions,
            "supported_function_ids": SUPPORTED_FUNCTION_IDS,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "功能列表獲取失敗",
                "message": str(e),
                "timestamp": time.time()
            }
        )


@router.get("/status")
async def get_analysis_status() -> Dict[str, Any]:
    """
    獲取分析服務狀態
    
    返回服務健康狀態和性能指標
    """
    
    try:
        health_result = await analysis_service.health_check()
        cache_result = await analysis_service.get_cache_status()
        runtime_state = analysis_service.get_runtime_state()
        service_status = "busy" if runtime_state.get("busy") else health_result.get("status", "unknown")
        
        return {
            "success": True,
            "message": "分析服務狀態",
            "status": service_status,
            "service_health": health_result,
            "cache_status": cache_result,
            "runtime": runtime_state,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "狀態檢查失敗",
            "error": str(e),
            "timestamp": time.time()
        }
