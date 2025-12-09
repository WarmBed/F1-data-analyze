#!/usr/bin/env python3
"""
F1 Analysis Cache Service - 智能 JSON 搜尋服務
F1 賽車數據分析緩存服務 - 提供快速的 JSON 檔案搜尋與載入功能

版本: 1.0
作者: F1 Analysis Team
功能: 智能搜尋現有 JSON 分析結果，避免重複 CLI 執行
"""

import os
import glob
import json
import re
from typing import Optional, Dict, List, Any, Tuple, Union, Iterable
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
from collections import Counter

from api.models.function_specs import normalize_function_id


class F1AnalysisCacheService:
    """F1 分析緩存服務 - 智能 JSON 搜尋與管理"""
    
    def __init__(self, json_dir: str = "json/", cache_dir: str = "cache/"):
        """
        初始化緩存服務
        
        Args:
            json_dir: JSON 檔案目錄
            cache_dir: 快取檔案目錄
        """
        self.json_dir = json_dir
        self.cache_dir = cache_dir
        
        # 確保目錄存在
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 功能 ID 對應檔案名稱模式映射
        self.function_file_patterns = {
            "1": ["enhanced_rain_analysis", "rain_analysis"],
            "2": ["track_path_analysis", "track_position"],
            "3": ["driver_fastest_pitstop_ranking", "fastest_pitstop"],
            "4": ["team_pitstop_ranking", "pitstop_ranking"],
            "5": ["driver_detailed_pitstop_records", "detailed_pitstop", "pitstop_records"],
            "6": ["accident_statistics_summary", "accident_statistics"],
            "7": ["severity_distribution_analysis", "severity_analysis", "incident_severity"],
            "8": ["all_incidents_summary", "incidents_summary"],
            "9": ["special_incident_reports", "special_incidents", "notable_incidents"],
            "10": ["key_events_summary", "key_events", "race_key_events"],
            "11": ["single_driver_comprehensive", "driver_comprehensive"],
            "12": ["single_driver_telemetry", "telemetry_analysis", "all_drivers_telemetry"],
            "13": ["comparison_telemetry", "driver_comparison", "telemetry_comparison"],
            "14": ["race_position_changes", "position_changes"],
            "15": ["race_overtaking_statistics", "overtaking_statistics"],
            "16": ["single_driver_overtaking", "driver_overtaking"],
            "17": ["dynamic_corner_detection", "corner_detection"],
            "18": ["corner_detailed_analysis", "corner_analysis"],
            "19": ["single_driver_dnf", "driver_dnf"],
            "20": ["single_driver_all_corners", "all_corners"],
            "21": ["all_drivers_comprehensive", "all_drivers_analysis"],
            "22": ["corner_speed_analysis", "corner_speed"],
            "23": ["all_drivers_overtaking", "all_overtaking"],
            "24": ["all_drivers_dnf", "all_dnf"],
            "25": ["driver_race_position", "race_position"],
            "26": ["driver_tire_strategy", "tire_strategy"],
            "27": ["driver_fastest_lap_analysis", "fastest_lap"],
            "28": ["driver_lap_time_analysis", "laptime_analysis", "detailed_laptime"],
            "29": ["fia_parts_analysis"],  # ✅ Function 29 - FIA 部件變更分析 (簡化版)
            "14.1": ["driver_statistics_overview", "driver_summary"],
            "14.2": ["driver_telemetry_statistics", "telemetry_statistics"],
            "14.3": ["driver_overtaking_analysis", "overtaking_analysis"],
            "14.4": ["driver_fastest_lap_ranking", "fastest_lap_report"],
            "14.9": ["all_drivers_comprehensive", "driver_comprehensive_full"],
            "34": ["brake_performance", "all_drivers_brake_performance"],  # ✅ Function 34 - 全部車手煞車性能
            "47": ["all_drivers_cornering_analysis", "corner_performance", "cornering"],  # ✅ Function 47 - 全車手彎道性能分析
            "48": ["all_drivers_straight_line_speed", "straight_line_speed"],
            "53": ["ideal_lap_ranking", "ideal_lap"],
            "54": ["throttle_ratio", "throttle_box_plot", "lap_throttle_ratio"],
            "74": ["qualifying_prediction"],  # ✅ 添加 Function 74 - 排位賽預測 (v3.8)
            "79": ["qualifying_prediction"],  # ✅ Function 79 - FP3->Q 排位賽預測
            "80": ["race_prediction", "dynamic_team_rating"],  # ✅ Function 80 - Q->R 正賽預測
            "96": ["race_weather_forecast"],  # ✅ 添加 Function 96 - 賽事天氣預報
            "97": ["championship_standings"],  # ✅ 添加 Function 97 - 賽季積分榜 (車手/車隊)
            "98": ["team_colors"],  # ✅ 添加 Function 98 - 團隊顏色配置
            "99": ["season_calendar"],
            "100": ["historical_flags"],  # ✅ 添加 Function 100 - 歷年旗幟統計分析
        }
        
        # 賽事名稱標準化映射
        self.race_name_variants = {
            "japan": ["japan", "japanese", "japanese_grand_prix"],
            "china": ["china", "chinese", "chinese_grand_prix"],
            "australia": ["australia", "australian", "australian_grand_prix"],
            "bahrain": ["bahrain", "bahraini", "bahrain_grand_prix"],
            "saudi_arabia": ["saudi", "saudi_arabia", "saudi_arabian_grand_prix"],
            "italy": ["italy", "italian", "italian_grand_prix", "monza"],
            "monaco": ["monaco", "monaco_grand_prix"],
            "spain": ["spain", "spanish", "spanish_grand_prix", "barcelona"],
            "canada": ["canada", "canadian", "canadian_grand_prix"],
            "great_britain": ["great_britain", "british", "british_grand_prix", "silverstone"],
            "austria": ["austria", "austrian", "austrian_grand_prix"],
            "hungary": ["hungary", "hungarian", "hungarian_grand_prix"],
            "belgium": ["belgium", "belgian", "belgian_grand_prix", "spa"],
            "netherlands": ["netherlands", "dutch", "dutch_grand_prix"],
            "azerbaijan": ["azerbaijan", "azerbaijani", "azerbaijan_grand_prix", "baku"],
            "singapore": ["singapore", "singapore_grand_prix"],
            "united_states": ["united_states", "us", "american", "austin", "cota"],
            "mexico": ["mexico", "mexican", "mexican_grand_prix", "mexico city"],
            "brazil": ["brazil", "brazilian", "brazilian_grand_prix", "interlagos", "são paulo", "sao paulo"],
            "qatar": ["qatar", "qatari", "qatar_grand_prix"],
            "abu_dhabi": ["abu_dhabi", "uae", "abu_dhabi_grand_prix"],
            "las_vegas": ["las_vegas", "vegas", "las_vegas_grand_prix"],
            "miami": ["miami", "miami_grand_prix"],
            "emilia_romagna": ["emilia_romagna", "imola", "emilia_romagna_grand_prix"]
        }
        
        # 建立反向查找字典
        self.race_name_lookup = {}
        for standard_name, variants in self.race_name_variants.items():
            for variant in variants:
                self.race_name_lookup[variant.lower()] = standard_name
        
        print(f"[CACHE] F1 分析緩存服務已初始化")
        print(f"[CACHE] JSON 目錄: {os.path.abspath(self.json_dir)}")
        print(f"[CACHE] 支援 {len(self.function_file_patterns)} 種分析功能")
    
    def search_cached_analysis(self, function_id: Union[str, int], **params) -> Optional[Dict]:
        """
        搜尋現有的分析結果
        
        Args:
            function_id: 功能 ID (1-52)
            **params: 分析參數 (year, race, session, driver1, driver2 等)
            
        Returns:
            Dict: 找到的分析結果，或 None
        """
        normalized_id = normalize_function_id(function_id)
        print(f"[CACHE] 搜尋功能 {normalized_id} 的緩存結果...")
        print(f"[CACHE] 參數: {params}")
        
        # 🆕 只使用策略 1: 精確匹配（已禁用模糊匹配和相似匹配）
        exact_result = self._search_exact_match(normalized_id, **params)
        if exact_result:
            print(f"[CACHE] ✅ 精確匹配成功")
            return self._enhance_cache_result(exact_result, "exact_match")
        
        # ❌ 策略 2: 模糊匹配 - 已禁用（避免載入錯誤圈數）
        # fuzzy_result = self._search_fuzzy_match(normalized_id, **params)
        # if fuzzy_result:
        #     print(f"[CACHE] ✅ 模糊匹配成功")
        #     return self._enhance_cache_result(fuzzy_result, "fuzzy_match")
        
        # ❌ 策略 3: 相似分析 - 已禁用（避免載入錯誤圈數）
        # similar_result = self._search_similar_analysis(normalized_id, **params)
        # if similar_result:
        #     print(f"[CACHE] ✅ 相似匹配成功")
        #     return self._enhance_cache_result(similar_result, "similar_match")
        
        print(f"[CACHE] ❌ 未找到任何匹配的緩存結果（已禁用模糊匹配）")
        return None
    
    def _search_exact_match(self, function_id: str, **params) -> Optional[Dict]:
        """精確匹配搜尋"""
        patterns = self.function_file_patterns.get(function_id, [])
        if not patterns:
            return None

        year = params.get("year", "*")
        race_param = params.get("race", "*")
        session = params.get("session", "*")
        driver1 = params.get("driver1", "*")
        driver2 = params.get("driver2", "*")
        lap = params.get("lap")
        lap1 = params.get("lap1")
        lap2 = params.get("lap2")

        normalized_race = self._normalize_race_name(race_param)
        race_tokens = self._build_race_search_tokens(race_param)

        year_token = "*" if year in (None, "", "*") else str(year)
        session_token = "*" if session in (None, "", "*") else str(session)
        race = normalized_race
        
        for pattern_base in patterns:
            # 不同功能有不同的檔案命名模式
            if function_id == "13":  # 🔧 車手比較分析 - 精確圈數匹配
                # 🆕 根據 lap1/lap2 參數決定搜尋模式
                # 🔧 FIX: 支援多種賽事名稱格式 (United States vs united_states)
                race_variants = [
                    race,                                    # 原始格式 (united_states)
                    race.replace("_", " "),                  # 空格格式 (united states)  
                    race.replace("_", " ").title(),          # 首字母大寫 (United States)
                    race.title().replace("_", " "),          # 大寫空格 (United States)
                ]
                
                if lap1 is not None and lap2 is not None:
                    # 精確雙圈匹配模式
                    search_patterns = []
                    for race_variant in race_variants:
                        search_patterns.extend([
                            f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race_variant}_{session}_Lap{lap1}_Lap{lap2}.json",
                            f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race_variant}_{session}_Lap{lap2}_Lap{lap1}.json",  # 反向順序
                        ])
                    print(f"[CACHE] 🎯 精確雙圈匹配模式: Lap{lap1}_Lap{lap2}")
                elif lap1 is not None:
                    # 精確單圈匹配模式
                    search_patterns = []
                    for race_variant in race_variants:
                        search_patterns.extend([
                            f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race_variant}_{session}_Lap{lap1}.json",
                            f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race_variant}_{session}_Lap{lap1}.json",
                        ])
                    print(f"[CACHE] 🎯 精確單圈匹配模式: Lap{lap1}")
                else:
                    # ❌ 移除萬用字元模式（改為精確匹配或無圈數）
                    search_patterns = []
                    for race_variant in race_variants:
                        search_patterns.extend([
                            # 只搜尋沒有圈數後綴的檔案
                            f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race_variant}_{session}.json",
                            f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race_variant}_{session}.json",
                        ])
                    print(f"[CACHE] 🎯 無圈數模式")
            elif function_id in {"3", "4", "5"}:  # 進站相關分析
                # 🔧 FIX: Function 5 使用不同的檔案命名格式
                # Function 3/4: pitstop_analysis_{year}_{race}_Grand_Prix.json
                # Function 5: driver_detailed_pitstop_records_{year}_{race}_{session}.json
                race_full = self._get_race_full_name(race, year)
                
                if function_id == "5":
                    # Function 5: 包含 session 和空格/底線變體
                    race_with_space = race.replace("_", " ")
                    race_with_underscore = race.replace(" ", "_")
                    # 🔧 FIX: 小寫版本用於不區分大小寫匹配
                    race_lower = race.lower()
                    race_with_space_lower = race_with_space.lower()
                    race_with_underscore_lower = race_with_underscore.lower()
                    
                    search_patterns = [
                        f"{self.json_dir}{pattern_base}*{year}*{race_with_space}*{session}*.json",  # Abu Dhabi_R (精確)
                        f"{self.json_dir}{pattern_base}*{year}*{race_with_underscore}*{session}*.json",  # Abu_Dhabi_R (精確)
                        f"{self.json_dir}{pattern_base}*{year}*{race}*{session}*.json",  # 原始格式 (精確)
                        f"{self.json_dir}{pattern_base}*{year}*{race_with_space_lower}*{session.lower()}*.json",  # abu dhabi_r (小寫)
                        f"{self.json_dir}{pattern_base}*{year}*{race_with_underscore_lower}*{session.lower()}*.json",  # abu_dhabi_r (小寫)
                        f"{self.json_dir}{pattern_base}*{year}*{race_lower}*{session.lower()}*.json",  # 小寫原始格式
                        f"{self.json_dir}{pattern_base}*{year}*{race_full}*.json",  # 相容 Grand_Prix 格式
                    ]
                else:
                    # Function 3/4: 使用 Grand_Prix 格式
                    search_patterns = [
                        f"{self.json_dir}{pattern_base}*{year}*{race_full}*.json",
                        f"{self.json_dir}{pattern_base}*{year}*{race}*.json"
                    ]
            elif function_id == "99":  # 🔧 FIX: 賽季日曆 - 特殊處理多年 JSON
                search_patterns = [
                    f"{self.json_dir}season_calendar_multi_year_*.json",  # 優先多年格式
                    f"{self.json_dir}season_calendar_{year}_*.json",      # 單年格式
                    f"{self.json_dir}season_calendar_*.json"              # 任何賽季日曆
                ]
            elif function_id == "29":  # ✅ FIA 部件變更分析 (簡化版) - 僅 year 參數
                # 檔案格式: fia_parts_analysis_{year}.json 或帶過濾條件的變體
                # 範例: fia_parts_analysis_2025.json
                #       fia_parts_analysis_2025_team_McLaren.json
                #       fia_parts_analysis_2025_conf80.json
                team = params.get("team")
                driver = params.get("driver")
                race_filter = params.get("race")  # 注意：這是過濾條件，不是賽事參數
                change_type = params.get("change_type")
                min_confidence = params.get("min_confidence")
                
                search_patterns = []
                # 優先搜索完全匹配的檔案
                if team or driver or race_filter or change_type or min_confidence:
                    # 有過濾條件時，搜索帶過濾後綴的檔案
                    filter_suffix = ""
                    if team:
                        filter_suffix += f"_team_{team}"
                    if driver:
                        filter_suffix += f"_driver_{driver}"
                    if race_filter:
                        filter_suffix += f"_race_{race_filter}"
                    if change_type:
                        filter_suffix += f"_type_{change_type}"
                    if min_confidence:
                        conf_str = int(min_confidence * 100) if isinstance(min_confidence, float) else min_confidence
                        filter_suffix += f"_conf{conf_str}"
                    
                    search_patterns.append(f"{self.json_dir}fia_parts_analysis_{year}{filter_suffix}.json")
                
                # 備用：搜索基本檔案（無過濾）
                search_patterns.append(f"{self.json_dir}fia_parts_analysis_{year}.json")
                # 最後：搜索任何包含 year 的檔案
                search_patterns.append(f"{self.json_dir}fia_parts_analysis_{year}*.json")
                
            elif function_id == "98":  # ✅ 團隊顏色配置 - 特殊處理
                # 檔案格式: team_colors_{year}_{colormap}_{timestamp}.json
                # 預設 colormap = "fastf1"
                colormap = params.get("colormap", "fastf1")
                search_patterns = [
                    f"{self.json_dir}team_colors_{year}_{colormap}_*.json",  # 指定 colormap
                    f"{self.json_dir}team_colors_{year}_*.json",              # 任何 colormap
                ]
            elif function_id == "96":  # ✅ 天氣預報 - 在 weather/ 子目錄
                # 檔案格式: weather/race_weather_forecast_{year}_{race}_R.json
                # ⚠️ 注意：天氣預報固定使用 session='R'，忽略傳入的 session 參數
                # 使用遞迴搜尋找到子目錄中的檔案
                effective_tokens = race_tokens or ["*"]
                search_patterns = []
                for race_token in effective_tokens:
                    race_str = str(race_token)
                    # 使用 ** 遞迴搜尋 weather/ 子目錄，固定匹配 _R.json
                    search_patterns.extend([
                        f"{self.json_dir}**/race_weather_forecast*{year_token}*{race_str}*R*.json",
                    ])
            elif function_id == "100":  # ✅ 歷年旗幟統計 - 特殊處理
                # 檔案格式: historical_flags_{race}_{start_year}-{end_year}.json
                # ⚠️ 注意：檔案名不包含 session 和 timestamp（固定檔名，每次覆蓋）
                # 範例: historical_flags_Japan_2022-2025.json (首字母大寫)
                effective_tokens = race_tokens or ["*"]
                search_patterns = []
                print(f"[CACHE] 🏁 Function 100: 搜尋歷年旗幟統計")
                print(f"[CACHE]    賽道參數: {race_param}")
                print(f"[CACHE]    標準化賽道: {normalized_race}")
                print(f"[CACHE]    搜尋 tokens: {effective_tokens[:5]}")  # 顯示前5個
                
                for race_token in effective_tokens:
                    race_str = str(race_token)
                    # 🔧 搜尋多種大小寫變體（CLI 可能生成 Japan 或 japan）
                    search_patterns.extend([
                        f"{self.json_dir}historical_flags_{race_str}_*-*.json",  # 原始格式
                        f"{self.json_dir}historical_flags_{race_str.lower()}_*-*.json",  # 小寫
                        f"{self.json_dir}historical_flags_{race_str.title()}_*-*.json",  # 首字母大寫
                    ])
            elif function_id in {"79", "80"}:  # ✅ Function 79/80 - 預測分析
                # Function 79: FP3->Q 排位賽預測 - qualifying_prediction_{year}_{race}.json
                # Function 80: Q->R 正賽預測 - race_prediction_{year}_{race}.json
                effective_tokens = race_tokens or ["*"]
                search_patterns = []
                print(f"[CACHE] 🎯 Function {function_id}: 搜尋預測分析")
                print(f"[CACHE]    賽道參數: {race_param}")
                
                # 確定檔案前綴
                if function_id == "79":
                    prefix = "qualifying_prediction"
                else:  # function_id == "80"
                    prefix = "race_prediction"
                
                for race_token in effective_tokens:
                    race_str = str(race_token)
                    # 搜尋 prediction/ 子目錄（CLI 輸出位置）
                    search_patterns.extend([
                        f"{self.json_dir}prediction/{prefix}_{year_token}_{race_str}.json",
                        f"{self.json_dir}prediction/{prefix}_{year_token}_{race_str.replace(' ', '_')}.json",
                        f"{self.json_dir}prediction/{prefix}_{year_token}_{race_str.replace('_', ' ')}.json",
                        # 也搜尋根目錄（相容性）
                        f"{self.json_dir}{prefix}_{year_token}_{race_str}.json",
                        f"{self.json_dir}{prefix}_{year_token}_{race_str.replace(' ', '_')}.json",
                    ])
            else:  # 一般分析
                effective_tokens = race_tokens or ["*"]
                search_patterns = []
                for race_token in effective_tokens:
                    race_str = str(race_token)
                    search_patterns.extend({
                        f"{self.json_dir}{pattern_base}*{year_token}*{race_str}*{session_token}*.json",
                        f"{self.json_dir}*{pattern_base}*{year_token}*{race_str}*{session_token}*.json"
                    })
                    
                    # 🔧 FIX: Function 34/48 檔名不一致問題 - CLI 使用空格，API 預設底線
                    # 為 all_drivers 相關功能生成空格版本的搜索模式
                    if function_id in {"34", "48"} and "_" in race_str:
                        race_str_with_spaces = race_str.replace("_", " ")
                        search_patterns.extend({
                            f"{self.json_dir}{pattern_base}*{year_token}*{race_str_with_spaces}*{session_token}*.json",
                            f"{self.json_dir}*{pattern_base}*{year_token}*{race_str_with_spaces}*{session_token}*.json"
                        })
            
            for pattern in search_patterns:
                print(f"[CACHE] 🔍 搜尋模式: {os.path.basename(pattern)}")
                # 🔧 FIX: Function 96 使用遞迴搜尋（檔案在 weather/ 子目錄）
                use_recursive = function_id == "96" and "**" in pattern
                
                # 🔧 FIX: glob 區分大小寫，需要手動搜尋所有可能的大小寫組合
                files = []
                try:
                    files = glob.glob(pattern, recursive=use_recursive)
                except Exception as e:
                    print(f"[CACHE] ⚠️ glob 錯誤: {e}")
                
                # 🔧 FIX: 如果沒找到，嘗試不區分大小寫的搜尋
                if not files:
                    print(f"[CACHE] ⚠️ 精確匹配失敗，嘗試不區分大小寫搜尋...")
                    json_dir_path = Path(self.json_dir)
                    if json_dir_path.exists():
                        all_json_files = list(json_dir_path.glob("*.json"))
                        pattern_lower = os.path.basename(pattern).lower()
                        
                        for json_file in all_json_files:
                            if self._pattern_matches_case_insensitive(json_file.name, pattern_lower):
                                files.append(str(json_file))
                
                if not files:
                    print(f"[CACHE] ❌ 無匹配檔案")
                    continue
                
                print(f"[CACHE] ✅ 找到 {len(files)} 個匹配檔案")
                files = sorted(files, key=os.path.getmtime, reverse=True)
                for file_path in files:
                    # ✅ Function 79/80/96/97/98/99/100 跳過額外驗證（glob pattern 已足夠精確）
                    # Function 79/80: 預測分析 - 檔案名已包含 year 和 race
                    # Function 96: 天氣預報 - 已通過 glob pattern 精確匹配
                    # Function 97/98/99: 賽季級別分析 - 不需要 race/session
                    # Function 100: 歷年旗幟統計 - 檔案名不包含 session
                    if function_id not in {"79", "80", "96", "97", "98", "99", "100"}:
                        if not self._file_matches_race(file_path, race):
                            continue
                        if not self._file_matches_session(file_path, session):
                            continue

                    result = self._load_json_safely(file_path)
                    # ✅ Function 79/80: 預測分析 - 直接返回
                    if function_id in {"79", "80"}:
                        if result:
                            print(f"[CACHE] ✅ 找到預測結果: {os.path.basename(file_path)}")
                            return result
                    # ✅ Function 96: 天氣預報 - 直接返回（glob pattern 已精確匹配）
                    elif function_id == "96":
                        if result:
                            return result
                    # ✅ Function 97/98/99/100 使用特殊驗證邏輯
                    elif function_id in {"97", "98", "99", "100"}:
                        if result and self._season_level_result_matches(result, year, function_id, params):
                            return result
                    elif result and self._result_matches_params(result, year, race, session, driver1, driver2, lap, lap1, lap2):
                        return result
                    elif result and function_id == "2" and self._track_result_matches(file_path, result, year, race, session):
                        return result
        
        return None
    
    def _search_fuzzy_match(self, function_id: str, **params) -> Optional[Dict]:
        """模糊匹配搜尋 - 放寬條件"""
        patterns = self.function_file_patterns.get(function_id, [])
        if not patterns:
            return None
        
        year = params.get("year", "*")
        race = self._normalize_race_name(params.get("race", "*"))
        session = params.get("session")
        driver1 = params.get("driver1")
        driver2 = params.get("driver2")
        lap = params.get("lap")
        lap1 = params.get("lap1")
        lap2 = params.get("lap2")
        
        for pattern_base in patterns:
            # 放寬搜尋條件：只要功能和年份匹配
            search_patterns = [
                f"{self.json_dir}{pattern_base}*{year}*.json",
                f"{self.json_dir}*{pattern_base}*{year}*.json"
            ]
            
            # 如果有賽事資訊，也嘗試加入
            if race != "*":
                search_patterns.extend([
                    f"{self.json_dir}{pattern_base}*{year}*{race}*.json",
                    f"{self.json_dir}*{pattern_base}*{year}*{race}*.json"
                ])
            
            for pattern in search_patterns:
                files = glob.glob(pattern)
                if not files:
                    continue

                files = sorted(files, key=os.path.getmtime, reverse=True)
                for file_path in files:
                    if not self._file_matches_race(file_path, race):
                        continue

                    result = self._load_json_safely(file_path)
                    if result and self._result_matches_params(result, year, race, session, driver1, driver2, lap, lap1, lap2):
                        return result
                    if result and function_id == "2" and self._track_result_matches(file_path, result, year, race, session):
                        return result
        
        return None
    
    def _search_similar_analysis(self, function_id: str, **params) -> Optional[Dict]:
        """相似分析搜尋 - 最寬鬆條件"""
        patterns = self.function_file_patterns.get(function_id, [])
        if not patterns:
            return None
        
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")
        driver1 = params.get("driver1")
        driver2 = params.get("driver2")
        lap = params.get("lap")
        lap1 = params.get("lap1")
        lap2 = params.get("lap2")

        # 最寬鬆搜尋：只要功能類型匹配
        for pattern_base in patterns:
            search_patterns = [
                f"{self.json_dir}{pattern_base}*.json",
                f"{self.json_dir}*{pattern_base}*.json"
            ]
            
            all_files = []
            for pattern in search_patterns:
                all_files.extend(glob.glob(pattern))
            
            if all_files:
                unique_files = sorted(set(all_files), key=os.path.getmtime, reverse=True)
                for file_path in unique_files:
                    if not self._file_matches_race(file_path, race):
                        continue

                    result = self._load_json_safely(file_path)
                    if result and self._result_matches_params(result, year, race, session, driver1, driver2, lap, lap1, lap2):
                        return result
                    if result and function_id == "2" and self._track_result_matches(file_path, result, year, race, session):
                        return result
        
        return None
    
    def _normalize_race_name(self, race_name: str) -> str:
        """標準化賽事名稱"""
        if race_name == "*" or not race_name:
            return "*"
        
        race_lower = race_name.lower().replace(" ", "_").replace("-", "_")
        return self.race_name_lookup.get(race_lower, race_lower)
    
    def _pattern_matches_case_insensitive(self, filename: str, pattern_lower: str) -> bool:
        """
        不區分大小寫的模式匹配
        
        Args:
            filename: 實際檔案名稱
            pattern_lower: 小寫的搜尋模式（可能包含 * 萬用字元）
        
        Returns:
            bool: 是否匹配
        """
        filename_lower = filename.lower()
        
        # 將 glob 模式轉換為正則表達式
        import fnmatch
        pattern_regex = fnmatch.translate(pattern_lower)
        
        try:
            import re
            return re.match(pattern_regex, filename_lower) is not None
        except Exception as e:
            # 降級為簡單的字串包含檢查
            print(f"[CACHE] ⚠️ 正則表達式匹配失敗: {e}")
            pattern_clean = pattern_lower.replace("*", "").replace(".json", "")
            return pattern_clean in filename_lower

    def _build_race_search_tokens(self, race_value: Any) -> List[str]:
        """建立賽事名稱搜尋關鍵字，支援空白與底線格式，且不區分大小寫"""
        if race_value in (None, "", "*"):
            return ["*"]

        raw_text = str(race_value).strip()
        if not raw_text:
            return ["*"]

        tokens: List[str] = []
        candidates = {
            raw_text,                                    # ✅ 原始格式 "United States"
            raw_text.replace(" ", "_"),                  # ✅ 底線格式 "United_States"
            raw_text.replace(" ", "_").lower(),          # ✅ 小寫底線 "united_states"
            raw_text.lower(),                            # ✅ 小寫空白 "united states"
            raw_text.replace(" Grand Prix", "").strip(), # ✅ 僅國家名 "United States"
            # 🔧 FIX: 新增大小寫組合變體
            raw_text.title(),                            # ✅ 首字母大寫 "United States"
            raw_text.title().replace(" ", "_"),          # ✅ 首字母大寫 + 底線 "United_States"
        }

        normalized = self._normalize_race_name(raw_text)
        if normalized and normalized != "*":
            candidates.add(normalized)
            candidates.add(normalized.replace("_", " "))
            candidates.add(normalized.title())  # 🔧 FIX: 新增首字母大寫版本
            candidates.add(normalized.title().replace("_", " "))  # 🔧 FIX: 大寫 + 空格
            
            variants = self.race_name_variants.get(normalized, [])
            for variant in variants:
                variant_text = str(variant)
                candidates.add(variant_text)
                candidates.add(variant_text.replace(" ", "_"))
                candidates.add(variant_text.title())  # 🔧 FIX: 變體首字母大寫
                candidates.add(variant_text.title().replace("_", " "))

        for candidate in candidates:
            cleaned = str(candidate).strip()
            if not cleaned:
                continue
            tokens.append(cleaned)

        # 保持順序並去除重複
        return list(dict.fromkeys(tokens))
    
    def _get_race_full_name(self, race: str, year: int) -> str:
        """獲取賽事完整名稱"""
        race_full_names = {
            "japan": "Japanese_Grand_Prix",
            "china": "Chinese_Grand_Prix", 
            "australia": "Australian_Grand_Prix",
            "bahrain": "Bahrain_Grand_Prix",
            "saudi_arabia": "Saudi_Arabian_Grand_Prix",
            "italy": "Italian_Grand_Prix",
            "monaco": "Monaco_Grand_Prix",
            "spain": "Spanish_Grand_Prix",
            "canada": "Canadian_Grand_Prix",
            "great_britain": "British_Grand_Prix",
            "austria": "Austrian_Grand_Prix",
            "hungary": "Hungarian_Grand_Prix",
            "belgium": "Belgian_Grand_Prix",
            "netherlands": "Dutch_Grand_Prix",
        }
        
        normalized_race = self._normalize_race_name(race)
        return race_full_names.get(normalized_race, f"{race}_Grand_Prix")

    def _file_matches_race(self, file_path: str, race: str) -> bool:
        """
        檢查檔案名稱是否包含期望的賽事名稱
        
        ⚠️ 使用單詞邊界匹配，避免 "us" 匹配到 "australia" 的問題
        """
        if not race or race == "*":
            return True

        normalized_target = self._normalize_race_name(race)
        variants = set(self.race_name_variants.get(normalized_target, []))
        variants.add(normalized_target)
        file_name = os.path.basename(file_path).lower().replace("-", "_").replace(" ", "_")

        for variant in variants:
            token = variant.lower().replace(" ", "_")
            if not token:
                continue
            
            # 🔧 FIX: 使用單詞邊界匹配，避免 "us" 匹配到 "australia"
            # 檢查 token 是否作為獨立單詞出現（前後有分隔符或檔案開始/結束）
            import re
            # 建立正則表達式：token 前後必須是分隔符 (_) 或檔案開始/結束
            pattern = r'(?:^|_)' + re.escape(token) + r'(?:_|\.json$|$)'
            if re.search(pattern, file_name):
                return True

        return False

    def _track_result_matches(
        self,
        file_path: str,
        result: Dict[str, Any],
        year: Any,
        race: Any,
        session: Any
    ) -> bool:
        """Special-case matcher for legacy track analysis JSON lacking metadata."""

        function_id_value = result.get("function_id")
        if function_id_value is not None and str(function_id_value) not in {"2"}:
            return False

        file_name = os.path.basename(file_path).lower()

        if year not in (None, "*"):
            if str(year).lower() not in file_name:
                return False

        if race not in (None, "*"):
            normalized_race = self._normalize_race_name(race)
            if normalized_race and normalized_race not in file_name:
                return False

        if session not in (None, "*"):
            session_token = str(session).lower()
            if f"_{session_token}" not in file_name:
                return False

        metadata = result.setdefault("metadata", {}) if isinstance(result, dict) else {}
        if isinstance(metadata, dict):
            if year not in (None, "*"):
                metadata.setdefault("year", year)
            if race not in (None, "*"):
                metadata.setdefault("race", race)
            if session not in (None, "*"):
                metadata.setdefault("session", session)
            notes = metadata.setdefault("notes", [])
            if isinstance(notes, list) and "metadata-inferred-from-track-filename" not in notes:
                notes.append("metadata-inferred-from-track-filename")

        if isinstance(result, dict) and "function_id" not in result:
            result["function_id"] = "2"

        # 也補上 analysis_info，方便後續流程
        analysis_info = result.setdefault("analysis_info", {})
        if isinstance(analysis_info, dict):
            analysis_info.setdefault("year", metadata.get("year"))
            analysis_info.setdefault("race", metadata.get("race"))
            analysis_info.setdefault("session", metadata.get("session"))
            analysis_info.setdefault("function_id", "2")

        return True

    def _file_matches_session(self, file_path: str, session: str) -> bool:
        """簡單檢查檔名是否包含指定的賽段資訊"""
        if not session or session == "*":
            return True

        session_token = str(session).lower()
        file_name = os.path.basename(file_path).lower()
        return f"_{session_token}" in file_name or file_name.endswith(f"_{session_token}.json")

    def _season_level_result_matches(
        self,
        result: Dict[str, Any],
        year: Any,
        function_id: str,
        params: Dict[str, Any]
    ) -> bool:
        """
        驗證賽季級別分析結果 (Function 97, 98, 99, 100)
        
        這些功能不需要 race/session 參數，只驗證 year 和特定參數
        """
        if not isinstance(result, dict):
            return False
        
        # Function 100: Historical Flags Analysis - 驗證 race (不驗證 session)
        if function_id == "100":
            # 檢查 metadata 中的 race
            data = result.get("data", {})
            if not isinstance(data, dict):
                return False
            
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                return False
            
            # 驗證賽道名稱
            race_param = params.get("race")
            if race_param:
                circuit_name = metadata.get("circuit_name", "").lower()
                country = metadata.get("country", "").lower()
                race_lower = race_param.lower().replace("_", " ")
                
                # 🔧 FIX: 使用更寬鬆的匹配邏輯
                # 某些賽道名稱不一致，例如：
                # - "Abu Dhabi" / "Abu_Dhabi" 對應 circuit_name="Yas Island", country="United Arab Emirates"
                # - "Monaco" 對應 circuit_name="Circuit de Monaco", country="Monaco"
                # 方法：檢查檔案名是否包含 race_param（glob pattern 已精確匹配）
                # 如果 glob pattern 匹配成功，則信任該結果
                
                # 首先嘗試標準匹配
                matches = (
                    race_lower in circuit_name or 
                    race_lower in country or
                    circuit_name in race_lower or
                    country.split()[0] in race_lower  # 例如 "united" in "abu dhabi" 失敗
                )
                
                # 🔧 如果標準匹配失敗，使用寬鬆模式（信任 glob pattern 的匹配結果）
                # Function 100 的 glob pattern 已經精確匹配了 race 名稱在檔案名中
                # 例如: historical_flags_Abu_Dhabi_2022-2025.json
                if not matches:
                    print(f"[CACHE] ⚠️ Function 100: 賽道名稱標準匹配失敗")
                    print(f"[CACHE]    race_param='{race_param}' → race_lower='{race_lower}'")
                    print(f"[CACHE]    circuit_name='{circuit_name}', country='{country}'")
                    print(f"[CACHE]    採用寬鬆模式: 信任 glob pattern 的檔案名匹配結果")
                    # 不返回 False，繼續驗證其他條件
            
            # 驗證基本數據結構
            if not data.get("yearly_summary"):
                return False
            
            return True
        
        # Function 97: Championship Standings - 驗證 year
        elif function_id == "97":
            # 檢查 metadata 中的 year
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                result_year = metadata.get("season_year") or metadata.get("year") or metadata.get("season")
                if result_year and str(result_year) != str(year):
                    return False
            
            # 驗證基本數據結構
            data = result.get("data", {})
            if not isinstance(data, dict):
                return False
            
            # 應該包含 drivers 或 constructors
            if not data.get("drivers") and not data.get("constructors"):
                return False
            
            return True
        
        # Function 98: Team Colors - 驗證 year 和 colormap
        elif function_id == "98":
            # 檢查 metadata 中的 year
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                result_year = metadata.get("year") or metadata.get("season")
                if result_year and str(result_year) != str(year):
                    return False
            
            # 檢查 colormap (如果有指定)
            colormap = params.get("colormap")
            if colormap:
                result_colormap = metadata.get("colormap")
                if result_colormap and result_colormap != colormap:
                    return False
            
            # 驗證基本數據結構
            data = result.get("data", {})
            if not isinstance(data, dict):
                return False
            
            # 應該包含 teams 或 drivers
            if not data.get("teams") and not data.get("drivers"):
                return False
            
            return True
        
        # Function 99: Season Calendar - 驗證 year
        elif function_id == "99":
            data = result.get("data", {})
            
            # 多年格式: {"data": {"2024": [...], "2025": [...]}}
            if isinstance(data, dict) and str(year) in data:
                return True
            
            # 單年格式: 檢查 metadata
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                result_year = metadata.get("year") or metadata.get("season")
                if result_year and str(result_year) == str(year):
                    return True
            
            return False
        
        return False

    def _file_info_contains_lap(self, file_info: Optional[Dict[str, Any]], lap_value: Any, alias: Optional[str] = None) -> bool:
        if not file_info or not isinstance(file_info, dict):
            return False

        lap_norm = self._normalize_lap_value(lap_value)
        if not lap_norm:
            return False

        file_name = str(file_info.get("file_name", "")).lower()
        if not file_name:
            return False

        tokens = {
            f"lap{lap_norm}",
            f"lap_{lap_norm}",
            f"lap-{lap_norm}"
        }
        if alias:
            alias_token = alias.lower()
            tokens.add(alias_token)
            tokens.add(f"{alias_token}{lap_norm}")
            tokens.add(f"{alias_token}_{lap_norm}")

        return any(token in file_name for token in tokens)

    def _normalize_session_code(self, value: Any) -> str:
        if value is None:
            return ""

        text = str(value).strip().upper()
        if not text:
            return ""

        mapping = {
            "RACE": "R",
            "R": "R",
            "GRAND PRIX": "R",
            "QUALIFYING": "Q",
            "Q": "Q",
            "SPRINT": "S",
            "S": "S",
            "P1": "FP1",
            "P2": "FP2",
            "P3": "FP3",
            "PRACTICE 1": "FP1",
            "PRACTICE 2": "FP2",
            "PRACTICE 3": "FP3",
        }

        if text in mapping:
            return mapping[text]

        if text.startswith("FP"):
            return text

        if text.startswith("P") and len(text) == 2 and text[1].isdigit():
            return f"FP{text[1]}"

        return text

    def _normalize_lap_value(self, value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, (list, tuple, set)):
            for item in value:
                normalized = self._normalize_lap_value(item)
                if normalized:
                    return normalized
            return ""

        try:
            text = str(value).strip()
            if not text:
                return ""

            lowered = text.lower()
            for prefix in ("lap", "lap_", "lap-"):
                if lowered.startswith(prefix):
                    lowered = lowered[len(prefix):]
                    break

            cleaned = re.sub(r"[^0-9.]+", "", lowered)
            if not cleaned:
                cleaned = re.sub(r"[^0-9.]+", "", text)

            if not cleaned:
                return ""

            number = int(round(float(cleaned)))
            if number <= 0:
                return ""
            return str(number)
        except Exception:
            return ""

    def _file_info_matches_session(self, file_info: Optional[Dict[str, Any]], session: Any) -> bool:
        if not file_info or not isinstance(file_info, dict):
            return True

        file_name = str(file_info.get("file_name", ""))
        if not file_name:
            return True

        lowered = file_name.lower()
        expected_token = str(session).lower()

        known_tokens = ["_r", "_q", "_s", "_fp1", "_fp2", "_fp3", "_p1", "_p2", "_p3"]
        present_tokens = [token for token in known_tokens if token in lowered]

        if not present_tokens:
            return True  # 無法判定，視為匹配

        if f"_{expected_token}" in lowered or lowered.endswith(f"_{expected_token}"):
            return True

        return False

    def _file_info_matches_race(self, file_info: Optional[Dict[str, Any]], race: Any) -> bool:
        if not file_info or not isinstance(file_info, dict):
            return True
        file_name = str(file_info.get("file_name", "")).lower().replace("-", "_").replace(" ", "_")
        if not file_name:
            return False

        normalized = self._normalize_race_name(race)
        variants = set(self.race_name_variants.get(normalized, []))
        variants.add(normalized)

        for variant in variants:
            token = str(variant).lower().replace(" ", "_")
            if token and token in file_name:
                return True
        return False

    def _file_info_matches_year(self, file_info: Optional[Dict[str, Any]], year: Any) -> bool:
        if not file_info or not isinstance(file_info, dict):
            return True
        file_name = str(file_info.get("file_name", ""))
        if not file_name:
            return False
        pattern = rf"(?:^|[_\-]){re.escape(str(year))}(?:[_\-]|\.|$)"
        return re.search(pattern, file_name) is not None

    def _result_matches_params(
        self,
        result: Dict,
        year: Any,
        race: Any,
        session: Any,
        driver1: Any = None,
        driver2: Any = None,
        lap: Any = None,
        lap1: Any = None,
        lap2: Any = None,
    ) -> bool:
        """使用結果中的 metadata 再驗證一次參數是否符合"""

        if not isinstance(result, dict):
            return True

        metadata_candidates = self._collect_metadata_candidates(result)

        file_info = result.get("file_info") if isinstance(result, dict) else None

        if year not in (None, "*"):
            # 🔧 FIX: 特殊處理多年賽季日曆 JSON
            # 檢查 data 字段中是否有年份鍵 (如 data['2024'])
            data_field = result.get("data")
            if isinstance(data_field, dict) and str(year) in data_field:
                # 多年格式: {"data": {"2024": {...}, "2025": {...}}}
                pass  # 年份匹配成功
            else:
                # 標準格式: 檢查 metadata
                year_match = self._candidate_matches(
                    year,
                    metadata_candidates,
                    ["year", "season"],
                    normalize=lambda v: str(v),
                )
                if not year_match:
                    if not self._file_info_matches_year(file_info, year):
                        return False


        if session not in (None, "*"):
            session_match = self._candidate_matches(
                session,
                metadata_candidates,
                ["session", "session_type"],
                normalize=self._normalize_session_code,
            )
            if not session_match:
                if not self._file_info_matches_session(file_info, session):
                    return False

        if race not in (None, "*"):
            race_match = self._candidate_matches(
                race,
                metadata_candidates,
                ["race", "race_name", "event", "grand_prix"],
                normalize=self._normalize_race_name,
            )
            if not race_match:
                if not self._file_info_matches_race(file_info, race):
                    return False

        # 對於比較分析類型，也確認車手參數
        driver_match = True  # 預設通過（如果沒有 driver1/driver2 參數）
        if driver1 and driver2:
            expected_pair = [str(driver1).upper(), str(driver2).upper()]
            expected_counter = Counter(expected_pair)
            found_driver_metadata = False
            driver_match = False  # 初始設為不匹配

            def _collect_driver_codes(candidate: Dict[str, Any]) -> List[str]:
                codes: List[str] = []
                if not isinstance(candidate, dict):
                    return codes

                drivers_field = candidate.get("drivers")
                if isinstance(drivers_field, (list, tuple)):
                    for item in drivers_field:
                        code_value = None
                        if isinstance(item, dict):
                            for key in ("code", "driver_code", "driver", "name", "abbr"):
                                value = item.get(key)
                                if value:
                                    code_value = str(value).upper()
                                    break
                        elif item:
                            code_value = str(item).upper()

                        if code_value:
                            codes.append(code_value)
                        if len(codes) >= len(expected_pair):
                            break

                key_pairs = [
                    ("driver1", "driver2"),
                    ("driver_one", "driver_two"),
                    ("primary_driver", "secondary_driver"),
                    ("driver_a", "driver_b"),
                ]

                for first_key, second_key in key_pairs:
                    first_val = candidate.get(first_key)
                    second_val = candidate.get(second_key)
                    if first_val is not None or second_val is not None:
                        if first_val is not None:
                            codes.append(str(first_val).upper())
                        if second_val is not None:
                            codes.append(str(second_val).upper())
                        break

                return codes

            for candidate in metadata_candidates:
                candidate_codes = _collect_driver_codes(candidate)
                if not candidate_codes:
                    continue

                found_driver_metadata = True

                candidate_counter_raw = Counter(candidate_codes)
                filtered_counter = Counter({key: candidate_counter_raw[key] for key in expected_counter})

                if filtered_counter == expected_counter:
                    driver_match = True  # 找到匹配的 driver，但不直接返回
                    break

            # 如果找到 driver metadata 但不匹配，立即返回 False
            if found_driver_metadata and not driver_match:
                return False
        
        # 繼續檢查 lap 參數（不論 driver 是否匹配，都要檢查）

        def _match_lap(expected_value: Any, keys: List[str], alias: Optional[str], driver_hint: Optional[str] = None) -> bool:
            if expected_value in (None, "", "*"):
                return True

            normalized_expected = self._normalize_lap_value(expected_value)
            if not normalized_expected:
                return True

            if self._candidate_matches(
                normalized_expected,
                metadata_candidates,
                keys,
                normalize=self._normalize_lap_value,
            ):
                return True

            alt_keys = ["lap_numbers", "lap_map", "lap_data", "laps", "selected_laps", "lap_selection"]
            for candidate in metadata_candidates:
                if not isinstance(candidate, dict):
                    continue

                for alt_key in alt_keys:
                    alt_value = candidate.get(alt_key)
                    if isinstance(alt_value, dict):
                        if driver_hint and driver_hint in alt_value:
                            if self._normalize_lap_value(alt_value.get(driver_hint)) == normalized_expected:
                                return True
                        for item in alt_value.values():
                            if self._normalize_lap_value(item) == normalized_expected:
                                return True
                    elif isinstance(alt_value, (list, tuple, set)):
                        for item in alt_value:
                            if self._normalize_lap_value(item) == normalized_expected:
                                return True

            if self._file_info_contains_lap(file_info, normalized_expected, alias):
                return True

            return False

        if lap not in (None, "", "*"):
            if not _match_lap(lap, ["lap", "lap_number", "target_lap", "selected_lap"], "lap"):
                return False

        if lap1 not in (None, "", "*"):
            driver_hint = str(driver1).upper() if driver1 else None
            if not _match_lap(lap1, ["lap1", "lap_number1", "driver1_lap"], "lap1", driver_hint):
                return False

        if lap2 not in (None, "", "*"):
            driver_hint = str(driver2).upper() if driver2 else None
            if not _match_lap(lap2, ["lap2", "lap_number2", "driver2_lap"], "lap2", driver_hint):
                return False

        return True

    def _collect_metadata_candidates(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather possible metadata dictionaries from the result payload."""

        candidates: List[Dict[str, Any]] = []

        def _append_candidate(value: Any) -> None:
            if isinstance(value, dict) and value not in candidates:
                candidates.append(value)

        _append_candidate(result.get("metadata"))
        _append_candidate(result.get("analysis_info"))
        _append_candidate(result.get("analysis_metadata"))
        _append_candidate(result.get("analysis_meta"))

        # 有些分析結果會把資訊放在 summary 或 info 欄位
        possible_keys = ["info", "summary", "overview", "meta"]
        for key in possible_keys:
            value = result.get(key)
            if isinstance(value, dict):
                _append_candidate(value)

        # 如果最高層找不到，嘗試從 drivers_analysis 等結構中抓第一個子項的 analysis_info
        if not candidates:
            if isinstance(result.get("drivers_analysis"), dict):
                first_entry = next(iter(result["drivers_analysis"].values()), None)
                if isinstance(first_entry, dict):
                    _append_candidate(first_entry.get("analysis_info"))

        return candidates or [{}]

    def _candidate_matches(
        self,
        expected_value: Any,
        candidates: List[Dict[str, Any]],
        keys: List[str],
        normalize=lambda v: str(v)
    ) -> bool:
        """Check if any metadata candidate matches the expected value for provided keys."""

        expected_norm = normalize(expected_value)

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            for key in keys:
                if key in candidate and candidate[key] not in (None, ""):
                    for item in self._iterate_candidate_values(candidate[key]):
                        candidate_norm = normalize(item)
                        if candidate_norm == expected_norm:
                            return True

        return False

    def _iterate_candidate_values(self, value: Any) -> Iterable[Any]:
        if isinstance(value, dict):
            for item in value.values():
                yield item
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                yield item
        else:
            yield value
    
    def _load_json_safely(self, file_path: str) -> Optional[Dict]:
        """安全載入 JSON 檔案"""
        try:
            print(f"[CACHE] 載入檔案: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查檔案大小
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                print(f"[CACHE] ⚠️ 大型檔案警告: {file_size / 1024 / 1024:.1f} MB")
            
            # 添加檔案資訊
            file_info = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "created_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "is_recent": self._is_file_recent(file_path)
            }
            
            if isinstance(data, dict):
                data["file_info"] = file_info
            else:
                # 如果不是字典，包裝成字典
                data = {
                    "data": data,
                    "file_info": file_info
                }
            
            print(f"[CACHE] ✅ 成功載入 {file_info['file_size_mb']} MB")
            return data
            
        except json.JSONDecodeError as e:
            print(f"[CACHE] ❌ JSON 解析錯誤: {file_path}")
            print(f"[CACHE] 錯誤詳情: {e}")
            return None
        except FileNotFoundError:
            print(f"[CACHE] ❌ 檔案不存在: {file_path}")
            return None
        except PermissionError:
            print(f"[CACHE] ❌ 權限拒絕: {file_path}")
            return None
        except Exception as e:
            print(f"[CACHE] ❌ 未知錯誤載入檔案 {file_path}: {e}")
            return None
    
    def _is_file_recent(self, file_path: str, hours: int = 24) -> bool:
        """檢查檔案是否為最近創建"""
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            current_time = datetime.now()
            return (current_time - file_time) < timedelta(hours=hours)
        except:
            return False
    
    def _enhance_cache_result(self, result: Dict, match_type: str) -> Dict:
        """增強緩存結果資訊"""
        if not isinstance(result, dict):
            return result
        
        cache_info = {
            "cache_hit": True,
            "match_type": match_type,
            "response_source": "json_cache",
            "cache_timestamp": datetime.now().isoformat(),
            "match_description": {
                "exact_match": "完全匹配 - 所有參數完全符合",
                "fuzzy_match": "模糊匹配 - 功能和主要參數符合",
                "similar_match": "相似匹配 - 功能類型符合"
            }.get(match_type, "未知匹配類型")
        }
        
        # 如果結果中已有 cache_info，則合併
        if "cache_info" in result:
            result["cache_info"].update(cache_info)
        else:
            result["cache_info"] = cache_info
        
        return result
    
    def get_cache_statistics(self) -> Dict:
        """獲取緩存統計資訊"""
        print(f"[CACHE] 正在統計緩存資訊...")
        
        json_files = glob.glob(f"{self.json_dir}*.json")
        
        # 按功能分類統計
        function_stats = {}
        total_size = 0
        recent_files = []
        
        for file_path in json_files:
            file_name = os.path.basename(file_path)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                file_info = {
                    "name": file_name,
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "is_recent": self._is_file_recent(file_path)
                }
                
                if file_info["is_recent"]:
                    recent_files.append(file_info)
                
                # 識別功能類型
                function_type = "unknown"
                for fid, patterns in self.function_file_patterns.items():
                    for pattern in patterns:
                        if pattern in file_name.lower():
                            function_type = f"function_{fid}"
                            break
                    if function_type != "unknown":
                        break
                
                if function_type not in function_stats:
                    function_stats[function_type] = {
                        "count": 0,
                        "total_size_mb": 0,
                        "files": []
                    }
                
                function_stats[function_type]["count"] += 1
                function_stats[function_type]["total_size_mb"] += file_size / 1024 / 1024
                function_stats[function_type]["files"].append(file_name)
                
            except Exception as e:
                print(f"[CACHE] ⚠️ 處理檔案時出錯: {file_name}, 錯誤: {e}")
        
        # 排序近期檔案
        recent_files.sort(key=lambda x: x["modified"], reverse=True)
        
        stats = {
            "summary": {
                "total_files": len(json_files),
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "cache_directory": os.path.abspath(self.json_dir),
                "last_updated": datetime.now().isoformat(),
                "recent_files_count": len(recent_files)
            },
            "function_statistics": function_stats,
            "recent_files": recent_files[:10],  # 最近 10 個檔案
            "supported_functions": list(self.function_file_patterns.keys())
        }
        
        print(f"[CACHE] ✅ 統計完成: {stats['summary']['total_files']} 個檔案, {stats['summary']['total_size_mb']} MB")
        return stats
    
    def search_by_pattern(self, search_pattern: str) -> List[Dict]:
        """
        按模式搜尋檔案
        
        Args:
            search_pattern: 搜尋模式 (支援通配符)
            
        Returns:
            List[Dict]: 匹配的檔案資訊列表
        """
        print(f"[CACHE] 按模式搜尋: {search_pattern}")
        
        files = glob.glob(f"{self.json_dir}{search_pattern}")
        results = []
        
        for file_path in files:
            try:
                file_stat = os.stat(file_path)
                file_info = {
                    "file_name": os.path.basename(file_path),
                    "file_path": file_path,
                    "size_mb": round(file_stat.st_size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "is_recent": self._is_file_recent(file_path)
                }
                results.append(file_info)
            except Exception as e:
                print(f"[CACHE] ⚠️ 處理檔案時出錯: {file_path}, 錯誤: {e}")
        
        # 按修改時間排序
        results.sort(key=lambda x: x["modified"], reverse=True)
        
        print(f"[CACHE] 找到 {len(results)} 個匹配檔案")
        return results
    
    def clear_old_cache(self, days: int = 7) -> Dict:
        """
        清理舊的緩存檔案
        
        Args:
            days: 保留天數，超過此天數的檔案將被刪除
            
        Returns:
            Dict: 清理結果統計
        """
        print(f"[CACHE] 開始清理 {days} 天前的緩存檔案...")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        json_files = glob.glob(f"{self.json_dir}*.json")
        
        deleted_files = []
        deleted_size = 0
        
        for file_path in json_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_time:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    
                    deleted_files.append({
                        "file_name": os.path.basename(file_path),
                        "size_mb": round(file_size / 1024 / 1024, 2),
                        "last_modified": file_time.isoformat()
                    })
                    deleted_size += file_size
                    
            except Exception as e:
                print(f"[CACHE] ⚠️ 清理檔案時出錯: {file_path}, 錯誤: {e}")
        
        result = {
            "deleted_files_count": len(deleted_files),
            "deleted_size_mb": round(deleted_size / 1024 / 1024, 2),
            "cutoff_date": cutoff_time.isoformat(),
            "deleted_files": deleted_files
        }
        
        print(f"[CACHE] ✅ 清理完成: 刪除 {result['deleted_files_count']} 個檔案, 釋放 {result['deleted_size_mb']} MB")
        return result


# 測試函數
def test_cache_service():
    """測試緩存服務功能"""
    print("🧪 開始測試 F1 分析緩存服務...")
    
    cache_service = F1AnalysisCacheService()
    
    # 測試 1: 統計現有緩存
    print("\n📊 測試 1: 獲取緩存統計")
    stats = cache_service.get_cache_statistics()
    print(f"總檔案數: {stats['summary']['total_files']}")
    print(f"總大小: {stats['summary']['total_size_mb']} MB")
    
    # 測試 2: 搜尋特定分析
    print("\n🔍 測試 2: 搜尋特定分析")
    test_searches = [
        {"function_id": 13, "year": 2025, "race": "Japan", "session": "R", "driver1": "VER", "driver2": "LEC"},
        {"function_id": 12, "year": 2025, "race": "Japan", "session": "R"},
        {"function_id": 3, "year": 2025, "race": "Japan"},
        {"function_id": 999, "year": 2025, "race": "Japan"}  # 不存在的功能
    ]
    
    for search_params in test_searches:
        print(f"\n搜尋: {search_params}")
        result = cache_service.search_cached_analysis(**search_params)
        if result:
            print(f"✅ 找到結果: {result.get('cache_info', {}).get('match_type', 'unknown')}")
        else:
            print("❌ 未找到結果")
    
    # 測試 3: 模式搜尋
    print("\n🔍 測試 3: 模式搜尋")
    pattern_results = cache_service.search_by_pattern("*telemetry*.json")
    print(f"找到 {len(pattern_results)} 個遙測相關檔案")
    
    print("\n✅ 測試完成!")


if __name__ == "__main__":
    test_cache_service()
