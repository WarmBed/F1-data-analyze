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
            "analyze_v2": "/api/v2/analysis/execute",  # ✅ 新版端點
            "analyze_deprecated": "/analyze",  # ⚠️ 已棄用
            "functions": "/functions",
            "docs": "/docs"
        },
        "deprecation_warnings": {
            "deprecated_endpoints": [
                {
                    "endpoint": "/analyze",
                    "status": "DEPRECATED",
                    "reason": "不支援 Pydantic 驗證，缺少統一錯誤處理",
                    "replacement": "/api/v2/analysis/execute",
                    "http_status": "410 Gone",
                    "action_required": "請更新客戶端代碼使用新版 API"
                }
            ]
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
    function_id: int = Query(..., description="功能 ID (1-200)", ge=1, le=200),
    year: int = Query(..., description="賽季年份 (2020-2025)", ge=2020, le=2025),
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
    deprecated=True,
    summary="⚠️ 已棄用 - 執行分析（舊版端點）",
    description="""
    ⚠️ **此端點已棄用，請使用新版端點 `/api/v2/analysis/execute`**
    
    **棄用原因**：
    - 不支援 Pydantic 請求驗證
    - 缺少統一的錯誤處理
    - 與新版 API 架構不一致
    
    **遷移指南**：
    - 舊版：`POST /analyze` (body: {function_id, year, race, session})
    - 新版：`POST /api/v2/analysis/execute?function_id=X&year=Y&race=Z&session=S`
    
    **此端點將在未來版本中移除。**
    """,
    response_model=Dict[str, Any])
async def execute_analysis_deprecated(request: AnalysisRequest):
    """
    ⚠️ 已棄用的 F1 分析端點
    
    請改用 `/api/v2/analysis/execute` 端點
    """
    # ⚠️ 強制返回錯誤，禁止使用舊版 API
    raise HTTPException(
        status_code=410,  # 410 Gone - 資源已永久移除
        detail={
            "error": "API_ENDPOINT_DEPRECATED",
            "message": "⚠️ 此 API 端點已棄用且已禁用",
            "deprecated_endpoint": "/analyze",
            "new_endpoint": "/api/v2/analysis/execute",
            "migration_guide": {
                "old_usage": "POST /analyze (body: {function_id, year, race, session})",
                "new_usage": "POST /api/v2/analysis/execute?function_id=X&year=Y&race=Z&session=S",
                "example": "POST /api/v2/analysis/execute?function_id=120&year=2025&race=Japan&session=R"
            },
            "documentation": "/docs",
            "contact": "請更新您的客戶端代碼以使用新版 API"
        }
    )
    
    # ⚠️ 以下代碼已停用（保留供參考）
    # try:
    #     service = get_analysis_service()
    #     
    #     # 轉換請求參數
    #     params = {
    #         "year": request.year,
    #         "race": request.race.lower(),
    #         "session": request.session.value if hasattr(request.session, 'value') else str(request.session)
    #     }
    #     
    #     # 添加可選參數
    #     if request.driver1:
    #         params["driver1"] = request.driver1
    #     if request.driver2:
    #         params["driver2"] = request.driver2
    #     if request.force_refresh:
    #         params["force_refresh"] = request.force_refresh
    #     if request.include_telemetry:
    #         params["include_telemetry"] = request.include_telemetry
    #     
    #     # 執行分析
    #     result = await service.execute_analysis(request.function_id, **params)
    #     return result
    #     
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"分析執行失敗: {str(e)}")


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
