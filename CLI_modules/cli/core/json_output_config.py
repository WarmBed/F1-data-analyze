#!/usr/bin/env python3
"""
JSON 輸出配置模組
==================

統一管理 F1 分析系統的 JSON 檔案輸出路徑和目錄結構。

功能:
- 分析類型到子目錄的映射
- 自動識別檔案名稱對應的分析類型
- 動態生成完整輸出路徑
- 支援環境變數覆蓋基礎目錄

設計原則:
1. 零假設編程: 基於實際 CLI 分析器的檔案命名模式
2. 集中式配置: 一次修改全系統生效
3. 向後相容: 支援舊路徑和新分類路徑

Author: F1T Development Team
Date: 2025-10-10
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import Dict, Optional

# ========== 環境變數配置 ==========

# 基礎 JSON 目錄 (支援環境變數覆蓋)
BASE_JSON_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")

# ========== 分析類型目錄映射 ==========

# 分析類型到子目錄的映射表
# 基於實際 CLI 分析器的檔案命名模式 (2025-10-10 深度分析)
ANALYSIS_TYPE_DIRECTORIES: Dict[str, str] = {
    # 遙測分析 (功能 12, 13)
    "comparison_telemetry": "telemetry",
    "all_drivers_telemetry": "telemetry",
    "telemetry_analysis": "telemetry",
    "driver_telemetry_statistics": "telemetry",
    
    # 事故與事件 (功能 6, 7, 8, 9, 10)
    "all_incidents_summary": "incidents",
    "accident_statistics": "incidents",
    "severity_distribution": "incidents",
    "severity_analysis": "incidents",
    "special_incident": "incidents",
    "notable_incidents": "incidents",
    "key_events": "incidents",
    "race_key_events": "incidents",
    
    # 進站分析 (功能 3, 4, 5)
    "driver_detailed_pitstop": "pitstops",
    "driver_fastest_pitstop": "pitstops",
    "team_pitstop": "pitstops",
    "pitstop_records": "pitstops",
    "pitstop_ranking": "pitstops",
    "detailed_pitstop": "pitstops",
    "fastest_pitstop": "pitstops",
    
    # 天氣分析 (功能 1)
    "enhanced_rain_analysis": "weather",
    "rain_analysis": "weather",
    "raw_data_rain": "weather",
    "rain_intensity": "weather",
    "race_weather_forecast": "weather",
    
    # 圈速分析 (功能 28, 53)
    "detailed_laptime_analysis": "lap_analysis",
    "ideal_lap_ranking": "lap_analysis",
    "ideal_lap_analysis": "lap_analysis",
    "fastest_lap": "lap_analysis",
    "lap_time_analysis": "lap_analysis",
    "laptime_analysis": "lap_analysis",
    
    # 賽道位置 (功能 2)
    "track_position_analysis": "track_position",
    "raw_data_track_position": "track_position",
    "track_path": "track_position",
    
    # 輪胎策略 (功能 26)
    "tire_strategy": "tire_strategy",
    "driver_tire_strategy": "tire_strategy",
    
    # 油門分析 (功能 54)
    "throttle_ratio": "throttle",
    "lap_throttle": "throttle",
    "throttle_box_plot": "throttle",
    
    # DNF 統計 (功能 19, 24)
    "all_drivers_annual_dnf": "statistics",
    "all_drivers_dnf": "statistics",
    "annual_dnf": "statistics",
    "single_driver_dnf": "statistics",
    "driver_dnf": "statistics",
    
    # 超車分析 (功能 15, 16, 23)
    "overtaking_statistics": "overtaking",
    "overtaking_analysis": "overtaking",
    "all_drivers_overtaking": "overtaking",
    "all_overtaking": "overtaking",
    "overtaking_performance": "overtaking",
    "overtaking_trends": "overtaking",
    "overtaking_visualization": "overtaking",
    "single_driver_overtaking": "overtaking",
    "driver_overtaking": "overtaking",
    "race_overtaking": "overtaking",
    
    # 彎道分析 (功能 17, 18, 20, 22)
    "corner_detailed_analysis": "corner_analysis",
    "corner_analysis": "corner_analysis",
    "corner_speed": "corner_analysis",
    "single_driver_corner": "corner_analysis",
    "all_corners": "corner_analysis",
    "dynamic_corner_detection": "corner_analysis",
    "corner_detection": "corner_analysis",
    
    # 車手分析 (功能 14.x)
    "driver_statistics_overview": "driver_analysis",
    "driver_summary": "driver_analysis",
    "driver_comprehensive": "driver_analysis",
    "all_drivers_comprehensive": "driver_analysis",
    "single_driver_comprehensive": "driver_analysis",
    
    # 賽事分析 (功能 14, 25)
    "race_position_changes": "race_analysis",
    "position_changes": "race_analysis",
    "driver_race_position": "race_analysis",
    
    # 元數據 (功能 99)
    "team_colors": "metadata",
    "season_calendar": "metadata",
}

# ========== 核心函數 ==========

def get_analysis_type_from_filename(filename: str) -> str:
    """
    從檔案名稱自動識別分析類型
    
    Args:
        filename: JSON 檔案名稱 (例如: "comparison_telemetry_VER_LEC_2025_Japan_R.json")
        
    Returns:
        str: 分析類型關鍵字 (例如: "comparison_telemetry")
        
    Algorithm:
        1. 移除 .json 副檔名
        2. 按照關鍵字長度降序排列 (優先匹配長關鍵字)
        3. 返回第一個匹配的類型
        4. 若無匹配，返回 "unknown"
        
    Example:
        >>> get_analysis_type_from_filename("comparison_telemetry_VER_LEC.json")
        'comparison_telemetry'
        >>> get_analysis_type_from_filename("ideal_lap_ranking_2025_Italy_R.json")
        'ideal_lap_ranking'
    """
    # 移除副檔名和空白
    name = filename.replace(".json", "").strip().lower()
    
    # 按照關鍵字長度降序排列 (避免短關鍵字誤匹配)
    # 例如: "all_drivers_telemetry" 應該優先於 "telemetry"
    sorted_types = sorted(ANALYSIS_TYPE_DIRECTORIES.keys(), key=len, reverse=True)
    
    for analysis_type in sorted_types:
        if analysis_type.lower() in name:
            return analysis_type
    
    # 未識別的檔案類型
    return "unknown"


def get_json_output_path(analysis_type: str, filename: str) -> Path:
    """
    根據分析類型生成完整的 JSON 輸出路徑
    
    Args:
        analysis_type: 分析類型關鍵字 (可從檔案名稱提取)
        filename: JSON 檔案名稱
        
    Returns:
        Path: 完整的輸出路徑 (自動創建目錄)
        
    Process:
        1. 查找分析類型對應的子目錄
        2. 若找不到，使用 "other" 目錄
        3. 構建完整路徑: {BASE_JSON_DIR}/{subdirectory}/{filename}
        4. 自動創建目錄 (mkdir -p)
        
    Example:
        >>> path = get_json_output_path("comparison_telemetry", "comparison_telemetry_VER_LEC.json")
        >>> print(path)
        json/telemetry/comparison_telemetry_VER_LEC.json
        
        >>> path = get_json_output_path("ideal_lap_ranking", "ideal_lap_ranking_2025_Italy_R.json")
        >>> print(path)
        json/lap_analysis/ideal_lap_ranking_2025_Italy_R.json
    """
    # 查找匹配的子目錄
    subdirectory = None
    
    # 直接匹配分析類型
    if analysis_type in ANALYSIS_TYPE_DIRECTORIES:
        subdirectory = ANALYSIS_TYPE_DIRECTORIES[analysis_type]
    else:
        # 嘗試從檔案名稱中自動識別
        detected_type = get_analysis_type_from_filename(filename)
        if detected_type in ANALYSIS_TYPE_DIRECTORIES:
            subdirectory = ANALYSIS_TYPE_DIRECTORIES[detected_type]
            print(f"[JSON_CONFIG] 📝 自動識別分析類型: {detected_type} → {subdirectory}/")
    
    # 若仍找不到，使用 "other" 目錄
    if subdirectory is None:
        subdirectory = "other"
        print(f"[JSON_CONFIG] ⚠️ 未識別的分析類型: {analysis_type}，使用 'other' 目錄")
        print(f"[JSON_CONFIG] 💡 提示: 檔案名稱 = {filename}")
    
    # 構建完整路徑
    output_dir = Path(BASE_JSON_DIR) / subdirectory
    
    # 自動創建目錄
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 返回完整檔案路徑
    full_path = output_dir / filename
    
    # 除錯日誌
    print(f"[JSON_CONFIG] ✅ 輸出路徑: {full_path}")
    
    return full_path


def get_subdirectory_for_type(analysis_type: str) -> str:
    """
    獲取分析類型對應的子目錄名稱
    
    Args:
        analysis_type: 分析類型關鍵字
        
    Returns:
        str: 子目錄名稱 (例如: "telemetry", "weather")
        
    Example:
        >>> get_subdirectory_for_type("comparison_telemetry")
        'telemetry'
        >>> get_subdirectory_for_type("enhanced_rain_analysis")
        'weather'
    """
    return ANALYSIS_TYPE_DIRECTORIES.get(analysis_type, "other")


def list_all_analysis_types() -> Dict[str, str]:
    """
    列出所有已註冊的分析類型及其子目錄
    
    Returns:
        Dict[str, str]: {分析類型: 子目錄} 映射
        
    Example:
        >>> types = list_all_analysis_types()
        >>> print(types["ideal_lap_ranking"])
        'lap_analysis'
    """
    return ANALYSIS_TYPE_DIRECTORIES.copy()


def get_base_json_directory() -> Path:
    """
    獲取基礎 JSON 目錄路徑
    
    Returns:
        Path: 基礎 JSON 目錄 (支援環境變數覆蓋)
        
    Example:
        >>> dir = get_base_json_directory()
        >>> print(dir)
        json
    """
    return Path(BASE_JSON_DIR)


# ========== 向後相容性工具 ==========

def ensure_backward_compatibility(filename: str) -> Path:
    """
    確保向後相容性: 優先返回新路徑，但保留舊路徑搜尋
    
    Args:
        filename: JSON 檔案名稱
        
    Returns:
        Path: 新分類路徑 (自動創建目錄)
        
    Note:
        API Server 會透過遞迴搜尋找到舊路徑的檔案
    """
    analysis_type = get_analysis_type_from_filename(filename)
    return get_json_output_path(analysis_type, filename)


# ========== 模組初始化 ==========

if __name__ == "__main__":
    # 測試模組功能
    print("=" * 60)
    print("JSON 輸出配置模組測試")
    print("=" * 60)
    
    # 測試檔案名稱識別
    test_files = [
        "comparison_telemetry_VER_LEC_2025_Japan_R.json",
        "enhanced_rain_analysis_2025_Japan_R.json",
        "ideal_lap_ranking_2025_Italy_R.json",
        "driver_detailed_pitstop_records_2025_Japan.json",
        "all_incidents_summary_2025_Japan_R.json",
        "throttle_ratio_2025_japan_R.json",
    ]
    
    print("\n📝 檔案名稱識別測試:")
    for filename in test_files:
        analysis_type = get_analysis_type_from_filename(filename)
        subdirectory = get_subdirectory_for_type(analysis_type)
        print(f"  {filename}")
        print(f"    → 類型: {analysis_type}")
        print(f"    → 目錄: {subdirectory}/")
    
    # 測試路徑生成
    print("\n📂 路徑生成測試:")
    for filename in test_files[:3]:
        analysis_type = get_analysis_type_from_filename(filename)
        path = get_json_output_path(analysis_type, filename)
        print(f"  {path}")
    
    # 列出所有分析類型
    print(f"\n📊 已註冊的分析類型數量: {len(ANALYSIS_TYPE_DIRECTORIES)}")
    print(f"📁 基礎 JSON 目錄: {get_base_json_directory()}")
    
    print("\n✅ 配置模組測試完成")
