#!/usr/bin/env python3
"""
F1 Analysis API 主路由模組
整合所有 API 端點的路由

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import time

from ..services.simple_analysis_service import SimpleF1AnalysisService
from ..models.requests import AnalysisRequest, CacheRequest
from ..models.responses import AnalysisResponse

# 初始化路由器
router = APIRouter()

# 初始化服務 (單例模式)
_analysis_service: Optional[SimpleF1AnalysisService] = None

def get_analysis_service() -> SimpleF1AnalysisService:
    """獲取分析服務實例 (單例模式)"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = SimpleF1AnalysisService()
    return _analysis_service


@router.get("/", 
    summary="API 根路徑",
    description="獲取 API 基本信息和狀態",
    response_model=Dict[str, Any])
async def root():
    """API 根路徑 - 返回基本信息"""
    return {
        "api_name": "F1 Analysis API",
        "version": "2.0.0",
        "status": "running",
        "description": "Formula 1 遙測分析 REST API",
        "endpoints": {
            "health": "/health",
            "cache_status": "/cache/status", 
            "cache_search": "/cache/search",
            "analyze": "/analyze",
            "functions": "/functions",
            "docs": "/docs"
        },
        "performance": {
            "cache_enabled": True,
            "average_response_time": "<10ms",
            "supported_functions": "28+"
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


@router.get("/health",
    summary="健康檢查", 
    description="檢查 API 服務和各組件的健康狀態",
    response_model=Dict[str, Any])
async def health_check():
    """健康檢查端點"""
    try:
        service = get_analysis_service()
        result = await service.health_check()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")


@router.get("/cache/status",
    summary="緩存狀態",
    description="獲取緩存系統的詳細狀態信息", 
    response_model=Dict[str, Any])
async def get_cache_status():
    """獲取緩存狀態"""
    try:
        service = get_analysis_service()
        result = await service.get_cache_status()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"緩存狀態獲取失敗: {str(e)}")


@router.get("/cache/search",
    summary="緩存搜尋",
    description="搜尋緩存中的分析結果",
    response_model=Dict[str, Any])
async def search_cache(
    function_id: int = Query(..., description="功能 ID (1-52)", ge=1, le=52),
    year: int = Query(..., description="賽季年份", ge=2024, le=2025),
    race: str = Query(..., description="賽事名稱", min_length=3, max_length=50),
    session: str = Query(..., description="會話類型 (R/Q/FP1/FP2/FP3/S/SQ)", 
                        regex="^(R|Q|FP1|FP2|FP3|S|SQ)$"),
    driver1: Optional[str] = Query(None, description="車手1代碼", regex="^[A-Z]{3}$"),
    driver2: Optional[str] = Query(None, description="車手2代碼", regex="^[A-Z]{3}$")
):
    """搜尋緩存中的分析結果"""
    try:
        service = get_analysis_service()
        
        # 使用緩存服務搜尋
        cache_result = service.cache_service.search_cached_analysis(
            function_id=function_id,
            year=year,
            race=race,
            session=session,
            driver1=driver1,
            driver2=driver2
        )
        
        if cache_result:
            return {
                "success": True,
                "message": "緩存搜尋成功",
                "cache_hit": True,
                "search_params": {
                    "function_id": function_id,
                    "year": year,
                    "race": race,
                    "session": session,
                    "driver1": driver1,
                    "driver2": driver2
                },
                "data_size": len(str(cache_result)),
                "data": cache_result,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "success": True,
                "message": "緩存搜尋完成，未找到匹配結果",
                "cache_hit": False,
                "search_params": {
                    "function_id": function_id,
                    "year": year,
                    "race": race,
                    "session": session,
                    "driver1": driver1,
                    "driver2": driver2
                },
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"緩存搜尋失敗: {str(e)}")


@router.post("/analyze",
    summary="執行分析",
    description="執行指定的 F1 數據分析功能",
    response_model=Dict[str, Any])
async def execute_analysis(request: AnalysisRequest):
    """執行 F1 分析"""
    try:
        service = get_analysis_service()
        
        # 轉換請求參數
        params = {
            "year": request.year,
            "race": request.race.lower(),
            "session": request.session.value if hasattr(request.session, 'value') else str(request.session)
        }
        
        # 添加可選參數
        if request.driver1:
            params["driver1"] = request.driver1
        if request.driver2:
            params["driver2"] = request.driver2
        if request.force_refresh:
            params["force_refresh"] = request.force_refresh
        if request.include_telemetry:
            params["include_telemetry"] = request.include_telemetry
        
        # 執行分析
        result = await service.execute_analysis(request.function_id, **params)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析執行失敗: {str(e)}")


@router.get("/functions",
    summary="支持的功能",
    description="獲取所有支持的分析功能列表",
    response_model=Dict[str, Any])
async def get_supported_functions():
    """獲取支持的功能列表"""
    try:
        service = get_analysis_service()
        
        # 從緩存服務獲取支持的功能
        cache_stats = service.cache_service.get_cache_statistics()
        supported_functions = cache_stats.get("supported_functions", {})
        
        # 功能分類
        function_categories = {
            "基礎分析": ["降雨分析", "事故分析", "進站分析", "賽道分析"],
            "遙測分析": ["車手遙測", "車手比較", "圈速分析", "超車分析"],
            "策略分析": ["輪胎策略", "燃料分析", "進站策略", "賽事策略"],
            "統計分析": ["年度統計", "車隊統計", "車手排名", "歷史數據"]
        }
        
        return {
            "success": True,
            "message": "功能列表獲取成功",
            "total_functions": len(supported_functions),
            "categories": function_categories,
            "supported_functions": supported_functions,
            "function_range": "1-52",
            "cache_based_functions": list(supported_functions.keys()),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"功能列表獲取失敗: {str(e)}")


# 錯誤處理中間件將在 middleware 中定義
