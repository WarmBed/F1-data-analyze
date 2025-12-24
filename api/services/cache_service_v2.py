#!/usr/bin/env python3
"""
F1 Analysis Cache Service V2 - 優化版 JSON 搜尋服務
===================================================

優化重點:
1. 精確檔名格式映射 - 每個 function_id 只搜尋 1-2 種格式
2. 檔案索引快取 - 啟動時建立索引，避免重複掃描
3. 減少 glob 調用 - 直接使用 os.path.exists()
4. 賽事名稱正規化 - 統一處理空格/底線問題

版本: 2.0
作者: F1 Analysis Team
"""

import os
import json
import time
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache

from api.models.function_specs import normalize_function_id


@dataclass
class FileNameSpec:
    """CLI JSON 檔案命名規格"""
    prefix: str                     # 檔名前綴 (e.g., "detailed_laptime_analysis")
    template: str                   # 完整模板 (e.g., "{prefix}_{year}_{race}_{session}_all_drivers.json")
    requires_year: bool = True
    requires_race: bool = True
    requires_session: bool = True
    requires_driver1: bool = False
    requires_driver2: bool = False
    requires_lap: bool = False
    suffix: str = ""                # 可選後綴 (e.g., "_all_drivers")
    has_timestamp: bool = False     # 是否包含時間戳


# ========== CLI JSON 標準命名格式定義 ==========
# 根據實際 CLI 輸出分析得出

FILE_SPECS: Dict[str, FileNameSpec] = {
    # === 基礎分析 (1-10) ===
    "1": FileNameSpec(
        prefix="enhanced_rain_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "2": FileNameSpec(
        prefix="track_position_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "3": FileNameSpec(
        prefix="driver_fastest_pitstop_ranking",
        template="{prefix}_{year}_{race_gp}.json",
        requires_session=False
    ),
    "4": FileNameSpec(
        prefix="team_pitstop_ranking",
        template="{prefix}_{year}_{race_gp}.json",
        requires_session=False
    ),
    "5": FileNameSpec(
        prefix="driver_detailed_pitstop_records",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "6": FileNameSpec(
        prefix="accident_statistics_summary",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "7": FileNameSpec(
        prefix="severity_distribution",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "8": FileNameSpec(
        prefix="all_incidents_summary",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    
    # === 進階分析 (11-28) ===
    "12": FileNameSpec(
        prefix="single_driver_telemetry",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "13": FileNameSpec(
        prefix="comparison_telemetry",
        template="comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2}.json",
        requires_driver1=True,
        requires_driver2=True,
        requires_lap=True
    ),
    "25": FileNameSpec(
        prefix="driver_race_position",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "26": FileNameSpec(
        prefix="tire_strategy",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "28": FileNameSpec(
        prefix="detailed_laptime_analysis",
        template="{prefix}_{year}_{race}_{session}_all_drivers.json",
        suffix="_all_drivers"
    ),
    "29": FileNameSpec(
        prefix="fia_parts_analysis",
        template="{prefix}_{year}.json",
        requires_race=False,
        requires_session=False
    ),
    
    # === 全車手分析 (34, 47, 48, 53, 54) ===
    "34": FileNameSpec(
        prefix="brake_performance",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "47": FileNameSpec(
        prefix="all_drivers_cornering_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "48": FileNameSpec(
        prefix="all_drivers_straight_line_speed",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "53": FileNameSpec(
        prefix="ideal_lap_ranking",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "54": FileNameSpec(
        prefix="driver_throttle_ratio",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    
    # === 預測系統 (74, 75, 76, 79, 80) ===
    "74": FileNameSpec(
        prefix="qualifying_prediction",
        template="{prefix}_{year}_{race}.json",
        requires_session=False
    ),
    "75": FileNameSpec(
        prefix="race_prediction",
        template="{prefix}_{year}_{race}.json",
        requires_session=False
    ),
    "76": FileNameSpec(
        prefix="fp2_qualifying_prediction",
        template="{prefix}_{year}_{race}.json",
        requires_session=False
    ),
    "79": FileNameSpec(
        prefix="qualifying_prediction",
        template="prediction/{prefix}_{year}_{race}.json",
        requires_session=False
    ),
    "80": FileNameSpec(
        prefix="race_prediction",
        template="prediction/{prefix}_{year}_{race}.json",
        requires_session=False
    ),
    
    # === 賽季級別 (96-100) ===
    "96": FileNameSpec(
        prefix="race_weather_forecast",
        template="weather/{prefix}_{year}_{race}_{session}.json"
    ),
    "97": FileNameSpec(
        prefix="championship_standings",
        template="{prefix}_{year}.json",
        requires_race=False,
        requires_session=False,
        has_timestamp=True
    ),
    "98": FileNameSpec(
        prefix="team_colors",
        template="{prefix}_{year}.json",
        requires_race=False,
        requires_session=False,
        has_timestamp=True
    ),
    "99": FileNameSpec(
        prefix="season_calendar_multi_year",
        template="{prefix}*.json",  # multi_year 格式帶時間戳
        requires_year=False,  # multi_year 包含多年數據
        requires_race=False,
        requires_session=False,
        has_timestamp=True
    ),
    "100": FileNameSpec(
        prefix="historical_flags",
        template="{prefix}_{race}_2022-2025.json",  # 固定年份範圍 (CLI 預設)
        requires_year=False,
        requires_session=False
    ),
    "101": FileNameSpec(
        prefix="F101_season_start_reaction",
        template="{prefix}_{year}.json",
        requires_race=False,
        requires_session=False
    ),
    
    # === 新功能 (120-125) ===
    "120": FileNameSpec(
        prefix="F120_corner_all_laps_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "121": FileNameSpec(
        prefix="fp2_straight_line_all_laps_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "122": FileNameSpec(
        prefix="brake_all_laps_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "125": FileNameSpec(
        prefix="vehicle_performance_analysis",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    
    # === Live Timing 功能 (126-127) ===
    "126": FileNameSpec(
        prefix="live_timing_weather",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
    "127": FileNameSpec(
        prefix="live_timing_traffic_distance",
        template="{prefix}_{year}_{race}_{session}.json"
    ),
}


class F1AnalysisCacheServiceV2:
    """F1 分析緩存服務 V2 - 優化版"""
    
    def __init__(self, json_dir: str = "json/", cache_dir: str = "cache/"):
        self.json_dir = json_dir
        self.cache_dir = cache_dir
        
        # 確保目錄存在
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 檔案索引 (啟動時建立)
        self._file_index: Dict[str, List[str]] = {}
        self._index_timestamp: float = 0
        self._index_max_age: float = 300  # 5 分鐘後重建索引
        
        # 統計
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "glob_calls": 0,
            "direct_hits": 0
        }
        
        print(f"[CACHE_V2] 初始化完成 - JSON 目錄: {os.path.abspath(self.json_dir)}")
    
    def _normalize_race(self, race: str) -> Tuple[str, str]:
        """
        正規化賽事名稱，返回 (空格版本, 底線版本)
        
        CLI 輸出可能使用空格或底線，API 請求可能使用任一格式
        """
        if not race or race == "*":
            return ("*", "*")
        
        race = race.strip()
        race_with_space = race.replace("_", " ")
        race_with_underscore = race.replace(" ", "_")
        
        return (race_with_space, race_with_underscore)
    
    def _build_exact_paths(self, function_id: str, **params) -> List[str]:
        """
        根據 function_id 和參數，建立精確的檔案路徑清單
        
        返回: 最多 2-4 個精確路徑 (比舊版 30+ 個大幅減少)
        """
        spec = FILE_SPECS.get(function_id)
        if not spec:
            return []
        
        year = str(params.get("year", "*"))
        race = params.get("race", "*")
        session = params.get("session", "*")
        driver1 = params.get("driver1", "")
        driver2 = params.get("driver2", "")
        lap1 = params.get("lap1", params.get("lap", ""))
        lap2 = params.get("lap2", "")
        
        # 正規化賽事名稱
        race_space, race_underscore = self._normalize_race(race)
        
        paths = []
        
        # 建立替換字典
        def build_path(race_variant: str) -> str:
            replacements = {
                "{prefix}": spec.prefix,
                "{year}": year,
                "{race}": race_variant,
                "{race_gp}": f"{race_variant.replace(' ', '_')}_Grand_Prix",
                "{session}": session,
                "{driver1}": driver1,
                "{driver2}": driver2,
                "{lap1}": str(lap1) if lap1 else "",
                "{lap2}": str(lap2) if lap2 else ""
            }
            
            path = spec.template
            for key, value in replacements.items():
                path = path.replace(key, value)
            
            return os.path.join(self.json_dir, path)
        
        # 嘗試空格版本和底線版本
        if race_space != "*":
            paths.append(build_path(race_space))
            if race_underscore != race_space:
                paths.append(build_path(race_underscore))
        else:
            paths.append(build_path("*"))
        
        return paths
    
    def search_cached_analysis(self, function_id: str, **params) -> Optional[Dict]:
        """
        搜尋現有的分析結果 (V2 優化版)
        
        優化策略:
        1. 先嘗試精確路徑匹配 (os.path.exists)
        2. 如果失敗，使用索引搜尋
        3. 最後才使用 glob (並更新索引)
        """
        normalized_id = normalize_function_id(function_id)
        print(f"[CACHE_V2] 搜尋功能 {normalized_id}")
        print(f"[CACHE_V2] 參數: {params}")
        
        start_time = time.time()
        
        # 策略 1: 精確路徑匹配
        exact_paths = self._build_exact_paths(normalized_id, **params)
        for path in exact_paths:
            if "*" not in path and os.path.exists(path):
                result = self._load_json_safely(path)
                if result:
                    self._stats["direct_hits"] += 1
                    self._stats["cache_hits"] += 1
                    elapsed = time.time() - start_time
                    print(f"[CACHE_V2] ✅ 直接命中: {os.path.basename(path)} ({elapsed:.3f}s)")
                    return self._enhance_result(result, path, "direct")
        
        # 策略 2: 索引搜尋
        result = self._search_by_index(normalized_id, **params)
        if result:
            self._stats["cache_hits"] += 1
            elapsed = time.time() - start_time
            print(f"[CACHE_V2] ✅ 索引命中 ({elapsed:.3f}s)")
            return result
        
        # 策略 3: Glob 搜尋 (最後手段)
        result = self._search_by_glob(normalized_id, exact_paths, **params)
        if result:
            self._stats["cache_hits"] += 1
            elapsed = time.time() - start_time
            print(f"[CACHE_V2] ✅ Glob 命中 ({elapsed:.3f}s)")
            return result
        
        self._stats["cache_misses"] += 1
        elapsed = time.time() - start_time
        print(f"[CACHE_V2] ❌ 未找到緩存 ({elapsed:.3f}s)")
        return None
    
    def _search_by_index(self, function_id: str, **params) -> Optional[Dict]:
        """使用檔案索引搜尋"""
        # 確保索引是最新的
        self._ensure_index_fresh()
        
        spec = FILE_SPECS.get(function_id)
        if not spec:
            return None
        
        prefix = spec.prefix.lower()
        year = str(params.get("year", ""))
        race_space, race_underscore = self._normalize_race(params.get("race", ""))
        session = params.get("session", "")
        
        # 搜尋索引
        candidates = []
        for filename, filepath in self._file_index.items():
            filename_lower = filename.lower()
            
            # 檢查前綴
            if not filename_lower.startswith(prefix.lower()):
                continue
            
            # 檢查年份 - 使用精確模式匹配，避免時間戳記誤匹配
            # 例如: "2025" 應該匹配 "prefix_2025_..." 但不匹配 "prefix_2024_...20251222..."
            if year:
                # 模式: _YYYY_ 或 _YYYY. 或以 YYYY_ 開頭（在前綴之後）
                year_patterns = [
                    f"_{year}_",  # 例如: prefix_2025_race
                    f"_{year}.",  # 例如: prefix_2025.json
                ]
                year_matched = any(pattern in filename for pattern in year_patterns)
                if not year_matched:
                    continue
            
            # 檢查賽事 (空格或底線版本)
            if race_space and race_space != "*":
                race_match = (
                    race_space.lower() in filename_lower or
                    race_underscore.lower() in filename_lower
                )
                if not race_match:
                    continue
            
            # 檢查賽段
            if session and spec.requires_session:
                # 處理 session 在檔名中的位置
                session_pattern = f"_{session}." if session else ""
                if session_pattern and session_pattern.lower() not in filename_lower:
                    # 也嘗試 _all_drivers 後綴
                    session_pattern2 = f"_{session}_"
                    if session_pattern2.lower() not in filename_lower:
                        continue
            
            candidates.append(filepath)
        
        if not candidates:
            return None
        
        # 按修改時間排序，返回最新的
        candidates.sort(key=os.path.getmtime, reverse=True)
        
        for filepath in candidates:
            result = self._load_json_safely(filepath)
            if result:
                return self._enhance_result(result, filepath, "index")
        
        return None
    
    def _search_by_glob(self, function_id: str, patterns: List[str], **params) -> Optional[Dict]:
        """使用 glob 搜尋 (最後手段)"""
        import glob
        
        self._stats["glob_calls"] += 1
        year = str(params.get("year", ""))
        
        for pattern in patterns:
            # 如果模式不包含萬用字元，跳過 (已在直接匹配中處理)
            if "*" not in pattern:
                continue
            
            try:
                files = glob.glob(pattern)
                if files:
                    # 過濾年份 - 使用精確模式匹配
                    if year:
                        year_patterns = [f"_{year}_", f"_{year}."]
                        files = [f for f in files if any(p in os.path.basename(f) for p in year_patterns)]
                    
                    if not files:
                        continue
                    
                    # 按修改時間排序
                    files.sort(key=os.path.getmtime, reverse=True)
                    
                    for filepath in files:
                        result = self._load_json_safely(filepath)
                        if result:
                            # 更新索引
                            self._add_to_index(filepath)
                            return self._enhance_result(result, filepath, "glob")
            except Exception as e:
                print(f"[CACHE_V2] ⚠️ Glob 錯誤: {e}")
        
        return None
    
    def _ensure_index_fresh(self):
        """確保索引是最新的"""
        current_time = time.time()
        
        if current_time - self._index_timestamp > self._index_max_age:
            self._rebuild_index()
    
    def _rebuild_index(self):
        """重建檔案索引"""
        print("[CACHE_V2] 🔄 重建檔案索引...")
        start_time = time.time()
        
        self._file_index = {}
        json_path = Path(self.json_dir)
        
        if json_path.exists():
            for filepath in json_path.rglob("*.json"):
                self._file_index[filepath.name] = str(filepath)
        
        self._index_timestamp = time.time()
        elapsed = time.time() - start_time
        print(f"[CACHE_V2] ✅ 索引重建完成: {len(self._file_index)} 個檔案 ({elapsed:.3f}s)")
    
    def _add_to_index(self, filepath: str):
        """添加單個檔案到索引"""
        filename = os.path.basename(filepath)
        self._file_index[filename] = filepath
    
    def _load_json_safely(self, filepath: str) -> Optional[Dict]:
        """安全載入 JSON 檔案"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"[CACHE_V2] 載入: {os.path.basename(filepath)} ({size_mb:.2f} MB)")
            
            return data
        except Exception as e:
            print(f"[CACHE_V2] ⚠️ 載入失敗: {filepath} - {e}")
            return None
    
    def _enhance_result(self, data: Dict, filepath: str, match_type: str) -> Dict:
        """增強結果，添加緩存元數據"""
        if isinstance(data, dict):
            data["_cache_metadata"] = {
                "source_file": os.path.basename(filepath),
                "match_type": match_type,
                "loaded_at": datetime.now().isoformat(),
                "file_size_bytes": os.path.getsize(filepath)
            }
        return data
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        hit_rate = (self._stats["cache_hits"] / total * 100) if total > 0 else 0
        
        return {
            **self._stats,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "index_size": len(self._file_index),
            "index_age_seconds": time.time() - self._index_timestamp
        }
    
    def invalidate_cache(self, function_id: str = None):
        """清除緩存索引"""
        self._file_index = {}
        self._index_timestamp = 0
        print(f"[CACHE_V2] 🗑️ 緩存索引已清除")


# ========== 兼容性包裝器 ==========
# 提供與舊版 cache_service.py 相同的接口

def create_cache_service(json_dir: str = "json/", cache_dir: str = "cache/") -> F1AnalysisCacheServiceV2:
    """創建緩存服務實例"""
    return F1AnalysisCacheServiceV2(json_dir, cache_dir)


# ========== 測試代碼 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("F1 Analysis Cache Service V2 - 測試")
    print("=" * 60)
    
    service = F1AnalysisCacheServiceV2()
    
    # 測試 1: Function 28 (詳細圈速分析)
    print("\n[測試 1] Function 28 - 詳細圈速分析")
    result = service.search_cached_analysis("28", year=2025, race="Japan", session="R")
    print(f"結果: {'找到' if result else '未找到'}")
    
    # 測試 2: Function 54 (油門比例)
    print("\n[測試 2] Function 54 - 油門比例")
    result = service.search_cached_analysis("54", year=2025, race="Abu Dhabi", session="R")
    print(f"結果: {'找到' if result else '未找到'}")
    
    # 測試 3: Function 2 (賽道位置)
    print("\n[測試 3] Function 2 - 賽道位置分析")
    result = service.search_cached_analysis("2", year=2025, race="United States", session="R")
    print(f"結果: {'找到' if result else '未找到'}")
    
    # 顯示統計
    print("\n" + "=" * 60)
    print("統計資訊:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
