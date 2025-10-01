#!/usr/bin/env python3
"""
F1 Analysis API 請求資料模型
定義所有 API 請求的輸入格式和驗證規則

版本: 1.0
作者: F1 Analysis Team
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from enum import Enum
import re


class SessionType(str, Enum):
    """會話類型枚舉"""
    RACE = "R"
    QUALIFYING = "Q"
    PRACTICE_1 = "FP1"
    PRACTICE_2 = "FP2" 
    PRACTICE_3 = "FP3"
    SPRINT = "S"
    SPRINT_QUALIFYING = "SQ"


class SupportedYear(int, Enum):
    """支援的賽季年份"""
    YEAR_2024 = 2024
    YEAR_2025 = 2025


class AnalysisRequest(BaseModel):
    """F1 分析請求模型"""
    
    function_id: int = Field(
        ...,
        ge=1,
        le=52,
        description="分析功能 ID (1-52)",
        examples=[13]
    )
    
    year: int = Field(
        ..., 
        ge=2024, 
        le=2025,
        description="賽季年份",
        examples=[2025]
    )
    
    race: str = Field(
        ..., 
        min_length=3,
        max_length=50,
        description="賽事名稱",
        examples=["Japan"]
    )
    
    session: SessionType = Field(
        ...,
        description="會話類型：R(正賽), Q(排位賽), FP1/2/3(練習賽), S(衝刺賽), SQ(衝刺排位)",
        examples=["R"]
    )
    
    driver1: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="主要車手代碼 (3字母)",
        examples=["VER"]
    )
    
    driver2: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3, 
        description="比較車手代碼 (3字母，用於車手比較分析)",
        examples=["LEC"]
    )
    
    force_refresh: Optional[bool] = Field(
        False,
        description="強制重新生成分析，忽略緩存"
    )
    
    include_telemetry: Optional[bool] = Field(
        True,
        description="是否包含遙測數據"
    )

    lap: Optional[int] = Field(
        None,
        ge=1,
        description="統一圈數參數 (單圈分析)"
    )

    lap1: Optional[int] = Field(
        None,
        ge=1,
        description="車手1圈數 (遙測比較分析用)"
    )

    lap2: Optional[int] = Field(
        None,
        ge=1,
        description="車手2圈數 (遙測比較分析用)"
    )
    
    @field_validator('driver1', 'driver2', mode='before')
    @classmethod
    def validate_driver_code(cls, v):
        """驗證車手代碼格式"""
        if v is not None:
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError('車手代碼必須是3個大寫字母，例如: VER, LEC, HAM')
        return v
    
    @field_validator('race', mode='before')
    @classmethod
    def validate_race_name(cls, v):
        """驗證賽事名稱"""
        # 支援的賽事名稱列表
        valid_races = {
            'australia', 'bahrain', 'china', 'japan', 'saudi_arabia', 'miami',
            'emilia_romagna', 'monaco', 'spain', 'canada', 'austria', 
            'great_britain', 'hungary', 'belgium', 'netherlands', 'italy',
            'azerbaijan', 'singapore', 'united_states', 'mexico', 'brazil',
            'las_vegas', 'qatar', 'abu_dhabi'
        }
        
        race_lower = v.lower().replace(' ', '_').replace('-', '_')
        
        # 允許常見的別名
        race_aliases = {
            'silverstone': 'great_britain',
            'spa': 'belgium', 
            'monza': 'italy',
            'monaco': 'monaco',
            'interlagos': 'brazil',
            'suzuka': 'japan',
            'imola': 'emilia_romagna',
            'vegas': 'las_vegas',
            'us': 'united_states',
            'usa': 'united_states',
            'uk': 'great_britain',
            'british': 'great_britain'
        }
        
        if race_lower in race_aliases:
            return race_aliases[race_lower]
        elif race_lower in valid_races:
            return race_lower
        else:
            # 不強制限制，允許新的賽事名稱
            return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "function_id": 13,
                "year": 2025,
                "race": "Japan",
                "session": "R",
                "driver1": "VER",
                "driver2": "LEC",
                "lap1": 1,
                "lap2": 1,
                "force_refresh": False,
                "include_telemetry": True
            }
        }


class CacheRequest(BaseModel):
    """緩存管理請求模型"""
    
    action: str = Field(
        "status",
        description="緩存操作類型",
        pattern="^(status|clear|search|statistics)$"
    )
    
    pattern: Optional[str] = Field(
        None,
        description="搜尋模式 (用於 search 操作)",
        examples=["*telemetry*.json"]
    )
    
    older_than_days: Optional[int] = Field(
        None,
        ge=1,
        description="清理多少天前的緩存 (用於 clear 操作)"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "action": "status",
                    "description": "獲取緩存狀態"
                },
                {
                    "action": "search", 
                    "pattern": "*telemetry*.json",
                    "description": "搜尋遙測相關檔案"
                },
                {
                    "action": "clear",
                    "older_than_days": 7,
                    "description": "清理7天前的緩存"
                }
            ]
        }


class FunctionListRequest(BaseModel):
    """功能列表請求模型"""
    
    category: Optional[str] = Field(
        None,
        description="功能分類篩選",
        pattern="^(basic|telemetry|pitstop|incident|comparison|advanced)$"
    )
    
    include_deprecated: Optional[bool] = Field(
        False,
        description="是否包含已棄用的功能"
    )
    
    detailed: Optional[bool] = Field(
        False,
        description="是否返回詳細資訊"
    )


class BatchAnalysisRequest(BaseModel):
    """批量分析請求模型"""
    
    requests: List[AnalysisRequest] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="批量分析請求列表 (最多10個)"
    )
    
    max_concurrent: Optional[int] = Field(
        3,
        ge=1,
        le=5,
        description="最大並發執行數 (1-5)"
    )
    
    stop_on_error: Optional[bool] = Field(
        False,
        description="遇到錯誤時是否停止後續分析"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "requests": [
                    {
                        "function_id": 12,
                        "year": 2025,
                        "race": "Japan",
                        "session": "R"
                    },
                    {
                        "function_id": 13,
                        "year": 2025,
                        "race": "Japan", 
                        "session": "R",
                        "driver1": "VER",
                        "driver2": "LEC"
                    }
                ],
                "max_concurrent": 3,
                "stop_on_error": False
            }
        }


class HealthCheckRequest(BaseModel):
    """健康檢查請求模型"""
    
    include_cache_stats: Optional[bool] = Field(
        True,
        description="是否包含緩存統計"
    )
    
    include_system_info: Optional[bool] = Field(
        False,
        description="是否包含系統資訊"
    )
    
    test_cli: Optional[bool] = Field(
        False,
        description="是否測試 CLI 執行器"
    )


# 通用查詢參數模型
class PaginationParams(BaseModel):
    """分頁參數模型"""
    
    page: int = Field(
        1,
        ge=1,
        description="頁碼 (從1開始)"
    )
    
    size: int = Field(
        20,
        ge=1,
        le=100,
        description="每頁數量 (1-100)"
    )


class SortParams(BaseModel):
    """排序參數模型"""
    
    sort_by: Optional[str] = Field(
        None,
        description="排序欄位"
    )
    
    order: Optional[str] = Field(
        "asc",
        pattern="^(asc|desc)$",
        description="排序順序: asc(升序) 或 desc(降序)"
    )


# 驗證輔助函數
def validate_function_id(function_id: int) -> int:
    """驗證功能 ID"""
    if not (1 <= function_id <= 52):
        raise ValueError(f"功能 ID 必須在 1-52 範圍內，收到: {function_id}")
    return function_id


def validate_driver_codes(driver1: Optional[str], driver2: Optional[str]) -> tuple:
    """驗證車手代碼組合"""
    if driver1 and driver2 and driver1 == driver2:
        raise ValueError("driver1 和 driver2 不能是同一個車手")
    
    return driver1, driver2


# 常用常數
SUPPORTED_YEARS = [2024, 2025]
SUPPORTED_SESSIONS = ["R", "Q", "FP1", "FP2", "FP3", "S", "SQ"]
VALID_FUNCTION_IDS = list(range(1, 53))  # 1-52
