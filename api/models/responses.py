#!/usr/bin/env python3
"""
F1 Analysis API 響應資料模型
定義所有 API 響應的輸出格式和結構

版本: 1.0
作者: F1 Analysis Team
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """響應狀態枚舉"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PROCESSING = "processing"


class DataSource(str, Enum):
    """數據來源枚舉"""
    EXACT_CACHE = "exact_cache"
    FUZZY_CACHE = "fuzzy_cache"
    SIMILAR_CACHE = "similar_cache"
    CLI_GENERATED = "cli_generated"
    FALLBACK_CACHE = "fallback_cache"


class CacheInfo(BaseModel):
    """緩存資訊模型"""
    
    cache_hit: bool = Field(
        ...,
        description="是否命中緩存"
    )
    
    match_type: Optional[str] = Field(
        None,
        description="匹配類型：exact_match, fuzzy_match, similar_match"
    )
    
    response_source: str = Field(
        ...,
        description="數據來源：json_cache, cli_generated, fallback_cache"
    )
    
    cache_timestamp: datetime = Field(
        ...,
        description="緩存時間戳"
    )
    
    match_description: Optional[str] = Field(
        None,
        description="匹配類型說明"
    )
    
    file_name: Optional[str] = Field(
        None,
        description="緩存檔案名稱"
    )
    
    file_size_mb: Optional[float] = Field(
        None,
        description="檔案大小 (MB)"
    )


class PerformanceInfo(BaseModel):
    """效能資訊模型"""
    
    data_source: DataSource = Field(
        ...,
        description="數據來源"
    )
    
    execution_time: str = Field(
        ...,
        description="執行時間"
    )
    
    strategy: str = Field(
        ...,
        description="執行策略說明"
    )
    
    is_cached: bool = Field(
        ...,
        description="是否來自緩存"
    )
    
    response_time: Optional[str] = Field(
        None,
        description="API 響應時間"
    )
    
    warning: Optional[str] = Field(
        None,
        description="效能警告"
    )


class FileInfo(BaseModel):
    """檔案資訊模型"""
    
    file_path: str = Field(
        ...,
        description="檔案路徑"
    )
    
    file_name: str = Field(
        ...,
        description="檔案名稱"
    )
    
    file_size_mb: float = Field(
        ...,
        description="檔案大小 (MB)"
    )
    
    modified_time: datetime = Field(
        ...,
        description="修改時間"
    )
    
    created_time: Optional[datetime] = Field(
        None,
        description="創建時間"
    )
    
    is_recent: bool = Field(
        ...,
        description="是否為近期檔案"
    )


class AnalysisResponse(BaseModel):
    """分析響應模型"""
    
    success: bool = Field(
        ...,
        description="請求是否成功"
    )
    
    message: str = Field(
        ...,
        description="響應訊息"
    )
    
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="分析結果數據"
    )
    
    cache_info: Optional[CacheInfo] = Field(
        None,
        description="緩存資訊"
    )
    
    performance: Optional[PerformanceInfo] = Field(
        None,
        description="效能資訊"
    )
    
    performance_info: Optional[Dict[str, Any]] = Field(
        None,
        description="效能資訊 (字典格式)"
    )
    
    error_type: Optional[str] = Field(
        None,
        description="錯誤類型"
    )
    
    file_info: Optional[FileInfo] = Field(
        None,
        description="檔案資訊"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="響應時間戳"
    )
    
    function_id: Optional[int] = Field(
        None,
        description="執行的功能 ID"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="請求 ID (用於追蹤)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "車手比較分析完成",
                "data": {
                    "analysis_type": "two_driver_telemetry_comparison",
                    "metadata": {
                        "year": 2025,
                        "race": "Japan",
                        "session": "R",
                        "driver1": "VER",
                        "driver2": "LEC"
                    },
                    "results": "..."
                },
                "cache_info": {
                    "cache_hit": True,
                    "match_type": "exact_match",
                    "response_source": "json_cache",
                    "cache_timestamp": "2025-09-17T10:30:00",
                    "match_description": "完全匹配 - 所有參數完全符合"
                },
                "performance": {
                    "data_source": "exact_cache",
                    "execution_time": "0.003s",
                    "strategy": "精確匹配緩存 - 最快",
                    "is_cached": True
                },
                "timestamp": "2025-09-17T10:30:00",
                "function_id": 13
            }
        }


class ErrorResponse(BaseModel):
    """錯誤響應模型"""
    
    success: bool = Field(
        False,
        description="請求是否成功 (錯誤時為 False)"
    )
    
    error: str = Field(
        ...,
        description="錯誤類型"
    )
    
    message: str = Field(
        ...,
        description="錯誤訊息"
    )
    
    details: Optional[str] = Field(
        None,
        description="錯誤詳細資訊"
    )
    
    function_id: Optional[int] = Field(
        None,
        description="出錯的功能 ID"
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="導致錯誤的請求參數"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="錯誤發生時間"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="請求 ID"
    )
    
    suggestions: Optional[List[str]] = Field(
        None,
        description="錯誤修復建議"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "ValidationError",
                "message": "請求參數驗證失敗",
                "details": "功能 ID 必須在 1-52 範圍內",
                "function_id": 999,
                "parameters": {
                    "function_id": 999,
                    "year": 2025,
                    "race": "Japan"
                },
                "timestamp": "2025-09-17T10:30:00",
                "suggestions": [
                    "請使用 1-52 範圍內的功能 ID",
                    "可以透過 GET /api/v1/functions 查看可用功能"
                ]
            }
        }


class CacheStatusResponse(BaseModel):
    """緩存狀態響應模型"""
    
    success: bool = Field(
        True,
        description="請求是否成功"
    )
    
    summary: Dict[str, Any] = Field(
        ...,
        description="緩存摘要資訊"
    )
    
    function_statistics: Dict[str, Any] = Field(
        ...,
        description="按功能分類的統計"
    )
    
    recent_files: List[Dict[str, Any]] = Field(
        ...,
        description="最近的檔案列表"
    )
    
    supported_functions: List[int] = Field(
        ...,
        description="支援的功能 ID 列表"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="統計時間"
    )


class FunctionListResponse(BaseModel):
    """功能列表響應模型"""
    
    success: bool = Field(
        True,
        description="請求是否成功"
    )
    
    available_functions: List[int] = Field(
        ...,
        description="可用的功能 ID 列表"
    )
    
    function_descriptions: Dict[str, str] = Field(
        ...,
        description="功能描述"
    )
    
    categories: Dict[str, List[int]] = Field(
        ...,
        description="功能分類"
    )
    
    deprecated_functions: Optional[List[int]] = Field(
        None,
        description="已棄用的功能列表"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="響應時間"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "available_functions": [1, 2, 3, 12, 13],
                "function_descriptions": {
                    "1": "降雨強度分析",
                    "12": "單一車手詳細遙測分析", 
                    "13": "雙車手比較分析"
                },
                "categories": {
                    "basic": [1, 2, 3],
                    "telemetry": [12, 13],
                    "pitstop": [3, 4, 5]
                }
            }
        }


class BatchAnalysisResponse(BaseModel):
    """批量分析響應模型"""
    
    success: bool = Field(
        ...,
        description="批量請求是否成功"
    )
    
    total_requests: int = Field(
        ...,
        description="總請求數"
    )
    
    successful_requests: int = Field(
        ...,
        description="成功請求數"
    )
    
    failed_requests: int = Field(
        ...,
        description="失敗請求數"
    )
    
    results: List[Union[AnalysisResponse, ErrorResponse]] = Field(
        ...,
        description="各個分析的結果"
    )
    
    execution_summary: Dict[str, Any] = Field(
        ...,
        description="執行摘要"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="批量分析完成時間"
    )


class HealthCheckResponse(BaseModel):
    """健康檢查響應模型"""
    
    success: bool = Field(
        ...,
        description="健康檢查是否成功"
    )
    
    healthy: bool = Field(
        ...,
        description="服務是否健康"
    )
    
    message: str = Field(
        ...,
        description="健康檢查訊息"
    )
    
    uptime_seconds: Optional[float] = Field(
        None,
        description="服務運行時間（秒）"
    )
    
    components: Optional[Dict[str, Any]] = Field(
        None,
        description="各組件健康狀態"
    )
    
    statistics: Optional[Dict[str, Any]] = Field(
        None,
        description="服務統計資訊"
    )
    
    timestamp: str = Field(
        ...,
        description="檢查時間"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-09-17T10:30:00",
                "version": "1.0.0",
                "uptime": "2 hours 15 minutes",
                "cache_status": {
                    "total_files": 9,
                    "total_size_mb": 2.31,
                    "recent_files_count": 9
                }
            }
        }


class PaginatedResponse(BaseModel):
    """分頁響應模型"""
    
    success: bool = Field(
        True,
        description="請求是否成功"
    )
    
    data: List[Any] = Field(
        ...,
        description="分頁數據"
    )
    
    pagination: Dict[str, Any] = Field(
        ...,
        description="分頁資訊"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="響應時間"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": ["item1", "item2"],
                "pagination": {
                    "page": 1,
                    "size": 20,
                    "total": 100,
                    "pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


# 響應建構輔助函數
def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    function_id: Optional[int] = None,
    **kwargs
) -> AnalysisResponse:
    """建構成功響應"""
    return AnalysisResponse(
        success=True,
        message=message,
        data=data,
        function_id=function_id,
        timestamp=datetime.now(),
        **kwargs
    )


def create_error_response(
    error: str,
    message: str,
    details: Optional[str] = None,
    function_id: Optional[int] = None,
    parameters: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
    **kwargs
) -> ErrorResponse:
    """建構錯誤響應"""
    return ErrorResponse(
        success=False,
        error=error,
        message=message,
        details=details,
        function_id=function_id,
        parameters=parameters,
        suggestions=suggestions,
        timestamp=datetime.now(),
        **kwargs
    )


def create_cache_response(
    cache_stats: Dict[str, Any]
) -> CacheStatusResponse:
    """建構緩存狀態響應"""
    return CacheStatusResponse(
        success=True,
        summary=cache_stats.get("summary", {}),
        function_statistics=cache_stats.get("function_statistics", {}),
        recent_files=cache_stats.get("recent_files", []),
        supported_functions=cache_stats.get("supported_functions", []),
        timestamp=datetime.now()
    )


def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: str = "操作成功",
    performance_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AnalysisResponse:
    """建構成功響應"""
    return AnalysisResponse(
        success=True,
        message=message,
        data=data,
        performance_info=performance_info,
        **kwargs
    )


def error_response(
    message: str,
    error_type: str = "unknown",
    data: Optional[Dict[str, Any]] = None,
    performance_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AnalysisResponse:
    """建構錯誤響應"""
    return AnalysisResponse(
        success=False,
        message=message,
        data=data,
        error_type=error_type,
        performance_info=performance_info,
        **kwargs
    )
