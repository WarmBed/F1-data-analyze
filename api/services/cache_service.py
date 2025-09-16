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
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
import hashlib
from pathlib import Path


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
            1: ["rain_intensity_analysis", "rain_analysis"],
            2: ["track_path_analysis", "track_position"],
            3: ["driver_fastest_pitstop_ranking", "fastest_pitstop"],
            4: ["team_pitstop_ranking", "pitstop_ranking"],
            5: ["driver_detailed_pitstop_records", "detailed_pitstop", "pitstop_records"],
            6: ["accident_statistics_summary", "accident_statistics"],
            7: ["severity_distribution_analysis", "severity_analysis"],
            8: ["all_incidents_summary", "incidents_summary"],
            9: ["special_incident_reports", "special_incidents"],
            10: ["key_events_summary", "key_events"],
            11: ["single_driver_comprehensive", "driver_comprehensive"],
            12: ["single_driver_telemetry", "telemetry_analysis", "all_drivers_telemetry"],
            13: ["comparison_telemetry", "driver_comparison", "telemetry_comparison"],
            14: ["race_position_changes", "position_changes"],
            15: ["race_overtaking_statistics", "overtaking_statistics"],
            16: ["single_driver_overtaking", "driver_overtaking"],
            17: ["dynamic_corner_detection", "corner_detection"],
            18: ["corner_detailed_analysis", "corner_analysis"],
            19: ["single_driver_dnf", "driver_dnf"],
            20: ["single_driver_all_corners", "all_corners"],
            21: ["all_drivers_comprehensive", "all_drivers_analysis"],
            22: ["corner_speed_analysis", "corner_speed"],
            23: ["all_drivers_overtaking", "all_overtaking"],
            24: ["all_drivers_dnf", "all_dnf"],
            25: ["driver_race_position", "race_position"],
            26: ["driver_tire_strategy", "tire_strategy"],
            27: ["driver_fastest_lap_analysis", "fastest_lap"],
            28: ["driver_lap_time_analysis", "laptime_analysis", "detailed_laptime"],
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
            "mexico": ["mexico", "mexican", "mexican_grand_prix"],
            "brazil": ["brazil", "brazilian", "brazilian_grand_prix", "interlagos"],
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
    
    def search_cached_analysis(self, function_id: int, **params) -> Optional[Dict]:
        """
        搜尋現有的分析結果
        
        Args:
            function_id: 功能 ID (1-52)
            **params: 分析參數 (year, race, session, driver1, driver2 等)
            
        Returns:
            Dict: 找到的分析結果，或 None
        """
        print(f"[CACHE] 搜尋功能 {function_id} 的緩存結果...")
        print(f"[CACHE] 參數: {params}")
        
        # 策略 1: 精確匹配
        exact_result = self._search_exact_match(function_id, **params)
        if exact_result:
            print(f"[CACHE] ✅ 精確匹配成功")
            return self._enhance_cache_result(exact_result, "exact_match")
        
        # 策略 2: 模糊匹配 (同功能、同賽事)
        fuzzy_result = self._search_fuzzy_match(function_id, **params)
        if fuzzy_result:
            print(f"[CACHE] ✅ 模糊匹配成功")
            return self._enhance_cache_result(fuzzy_result, "fuzzy_match")
        
        # 策略 3: 相似分析 (同功能、類似參數)
        similar_result = self._search_similar_analysis(function_id, **params)
        if similar_result:
            print(f"[CACHE] ✅ 相似匹配成功")
            return self._enhance_cache_result(similar_result, "similar_match")
        
        print(f"[CACHE] ❌ 未找到任何匹配的緩存結果")
        return None
    
    def _search_exact_match(self, function_id: int, **params) -> Optional[Dict]:
        """精確匹配搜尋"""
        patterns = self.function_file_patterns.get(function_id, [])
        if not patterns:
            return None
        
        year = params.get("year", "*")
        race = self._normalize_race_name(params.get("race", "*"))
        session = params.get("session", "*")
        driver1 = params.get("driver1", "*")
        driver2 = params.get("driver2", "*")
        
        for pattern_base in patterns:
            # 不同功能有不同的檔案命名模式
            if function_id == 13:  # 車手比較分析
                search_patterns = [
                    f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_*.json",
                    f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race}_{session}_*.json",  # 反向順序
                    f"{self.json_dir}{pattern_base}*{driver1}*{driver2}*{year}*{race}*{session}*.json",
                    f"{self.json_dir}{pattern_base}*{driver2}*{driver1}*{year}*{race}*{session}*.json"
                ]
            elif function_id in [3, 4, 5]:  # 進站相關分析
                race_full = self._get_race_full_name(race, year)
                search_patterns = [
                    f"{self.json_dir}{pattern_base}*{year}*{race_full}*.json",
                    f"{self.json_dir}{pattern_base}*{year}*{race}*.json"
                ]
            else:  # 一般分析
                search_patterns = [
                    f"{self.json_dir}{pattern_base}*{year}*{race}*{session}*.json",
                    f"{self.json_dir}*{pattern_base}*{year}*{race}*{session}*.json"
                ]
            
            for pattern in search_patterns:
                files = glob.glob(pattern)
                if files:
                    # 返回最新的檔案
                    latest_file = max(files, key=os.path.getmtime)
                    result = self._load_json_safely(latest_file)
                    if result:
                        return result
        
        return None
    
    def _search_fuzzy_match(self, function_id: int, **params) -> Optional[Dict]:
        """模糊匹配搜尋 - 放寬條件"""
        patterns = self.function_file_patterns.get(function_id, [])
        if not patterns:
            return None
        
        year = params.get("year", "*")
        race = self._normalize_race_name(params.get("race", "*"))
        
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
                if files:
                    # 根據檔案修改時間排序，返回最新的
                    latest_file = max(files, key=os.path.getmtime)
                    result = self._load_json_safely(latest_file)
                    if result:
                        return result
        
        return None
    
    def _search_similar_analysis(self, function_id: int, **params) -> Optional[Dict]:
        """相似分析搜尋 - 最寬鬆條件"""
        patterns = self.function_file_patterns.get(function_id, [])
        if not patterns:
            return None
        
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
                # 去重並按修改時間排序
                unique_files = list(set(all_files))
                latest_file = max(unique_files, key=os.path.getmtime)
                result = self._load_json_safely(latest_file)
                if result:
                    return result
        
        return None
    
    def _normalize_race_name(self, race_name: str) -> str:
        """標準化賽事名稱"""
        if race_name == "*" or not race_name:
            return "*"
        
        race_lower = race_name.lower().replace(" ", "_").replace("-", "_")
        return self.race_name_lookup.get(race_lower, race_lower)
    
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
