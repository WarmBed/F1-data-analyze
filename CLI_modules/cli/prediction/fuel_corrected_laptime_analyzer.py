#!/usr/bin/env python3
"""
F53 - 燃油校正圈速分析器 (Fuel-Corrected Lap Time Analyzer)

功能:
    使用 LiveF1 (OpenF1 API) 數據進行燃油影響校正的圈速分析
    
原理:
    T_corrected = T_actual + fuel_effect_coef * fuel_consumed
    fuel_remaining = start_fuel - (lap * fuel_per_lap)
    fuel_consumed = start_fuel - fuel_remaining
    
數據來源:
    - json/LiveF1/{year}/{race}_{session}/TimingData.json (F1 官方 Live Timing)
    - json/LiveF1/{year}/{race}_{session}/TyreStintSeries.json (F1 官方 Live Timing)
    - config/fuel_coefficients_database.json (燃油效率係數)
    
注意: LiveF1 資料夾存放的是 F1 官方 Live Timing 數據，非 OpenF1 API
    
輸出:
    - 每圈原始圈速 vs 校正圈速
    - 燃油影響量化分析
    - 車手真實配速對比

版本: 1.0.0
作者: F1 Analysis Team
日期: 2025-12-03
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class FuelCorrectedLaptimeAnalyzer:
    """F53 燃油校正圈速分析器"""
    
    def __init__(self, base_path: str = None):
        """
        初始化分析器
        
        Args:
            base_path: 專案根目錄路徑
        """
        if base_path is None:
            # 自動偵測專案根目錄
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent.parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.livef1_path = self.base_path / "json" / "LiveF1"
        self.fuel_db_path = self.base_path / "config" / "fuel_coefficients_database.json"
        
        # 載入燃油係數資料庫
        self.fuel_database = self._load_fuel_database()
        
        # 預設燃油參數 (當無賽道數據時使用)
        self.default_fuel_params = {
            "fuel_kg_per_lap": 1.75,
            "fuel_effect_coefficient": 0.030,
            "start_fuel_kg": 110
        }
    
    def _load_fuel_database(self) -> Dict[str, Any]:
        """載入燃油係數資料庫"""
        try:
            if self.fuel_db_path.exists():
                with open(self.fuel_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[WARNING] 找不到燃油係數資料庫: {self.fuel_db_path}")
                return {"circuits": {}}
        except Exception as e:
            print(f"[ERROR] 載入燃油係數資料庫失敗: {e}")
            return {"circuits": {}}
    
    def _get_track_fuel_params(self, race_name: str) -> Dict[str, float]:
        """
        獲取特定賽道的燃油參數
        
        Args:
            race_name: 賽事名稱 (e.g., "Italian", "Japanese")
            
        Returns:
            燃油參數字典
        """
        circuits = self.fuel_database.get("circuits", {})
        
        # 賽事名稱到賽道代碼的映射
        race_to_circuit = {
            "Italian": "Monza",
            "Japanese": "Suzuka",
            "Belgian": "Spa",
            "Monaco": "Monaco",
            "British": "Silverstone",
            "Australian": "Melbourne",
            "Austrian": "Spielberg",
            "Dutch": "Zandvoort",
            "Hungarian": "Budapest",
            "Singapore": "Singapore",
            "United_States": "Austin",
            "Mexico_City": "Mexico",
            "São_Paulo": "Interlagos",
            "Las_Vegas": "Las_Vegas",
            "Abu_Dhabi": "Yas_Marina",
            "Qatar": "Lusail",
            "Spanish": "Barcelona",
            "Canadian": "Montreal",
            "Miami": "Miami",
            "Bahrain": "Bahrain",
            "Saudi_Arabian": "Jeddah",
            "Chinese": "Shanghai",
            "Emilia_Romagna": "Imola",
            "Azerbaijan": "Baku"
        }
        
        circuit_name = race_to_circuit.get(race_name, race_name)
        
        if circuit_name in circuits:
            circuit_data = circuits[circuit_name]
            return {
                "fuel_kg_per_lap": circuit_data.get("fuel_kg_per_lap", self.default_fuel_params["fuel_kg_per_lap"]),
                "fuel_effect_coefficient": circuit_data.get("fuel_effect_coefficient", self.default_fuel_params["fuel_effect_coefficient"]),
                "start_fuel_kg": circuit_data.get("start_fuel_kg", self.default_fuel_params["start_fuel_kg"]),
                "track_name": circuit_data.get("official_name", circuit_name),
                "typical_race_laps": circuit_data.get("typical_race_laps", 60)
            }
        else:
            print(f"[WARNING] 找不到 {race_name} ({circuit_name}) 的燃油數據，使用預設值")
            return {**self.default_fuel_params, "track_name": race_name, "typical_race_laps": 60}
    
    def _find_livef1_data(self, year: int, race: str, session: str) -> Optional[Path]:
        """
        尋找 LiveF1 數據目錄
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽事類型 (R, Q, FP1, FP2, FP3)
            
        Returns:
            數據目錄路徑，若找不到返回 None
        """
        year_path = self.livef1_path / str(year)
        if not year_path.exists():
            print(f"[ERROR] 找不到年份目錄: {year_path}")
            return None
        
        # 構建可能的目錄名稱模式
        session_map = {"R": "Race", "Q": "Qualifying", "FP1": "FP1", "FP2": "FP2", "FP3": "FP3"}
        session_suffix = session_map.get(session, session)
        
        # 嘗試不同的命名格式
        possible_patterns = [
            f"{race}_{session_suffix}",
            f"{race.replace(' ', '_')}_{session_suffix}",
            race
        ]
        
        for pattern in possible_patterns:
            for dir_path in year_path.iterdir():
                if dir_path.is_dir() and pattern.lower() in dir_path.name.lower():
                    print(f"[INFO] 找到 LiveF1 數據目錄: {dir_path}")
                    return dir_path
        
        # 列出可用目錄供參考
        available_dirs = [d.name for d in year_path.iterdir() if d.is_dir()]
        print(f"[WARNING] 找不到匹配的目錄，可用目錄: {available_dirs}")
        return None
    
    def _parse_lap_time(self, time_str: str) -> Optional[float]:
        """
        解析圈速字串為秒數
        
        Args:
            time_str: 圈速字串 (e.g., "1:25.116", "85.116")
            
        Returns:
            圈速秒數，無效時返回 None
        """
        if not time_str or time_str == "" or time_str == "null":
            return None
        
        try:
            # 格式 1: "M:SS.mmm" (e.g., "1:25.116")
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            
            # 格式 2: "SS.mmm" (e.g., "85.116")
            return float(time_str)
        except (ValueError, TypeError):
            return None
    
    def _load_timing_data(self, data_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        載入 TimingData.json 並提取各車手的圈速數據
        
        Args:
            data_path: LiveF1 數據目錄路徑
            
        Returns:
            車手號碼 -> 圈速列表的字典
        """
        timing_file = data_path / "TimingData.json"
        if not timing_file.exists():
            print(f"[ERROR] 找不到 TimingData.json: {timing_file}")
            return {}
        
        try:
            with open(timing_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] 載入 TimingData.json 失敗: {e}")
            return {}
        
        driver_laps = {}
        
        # 處理新格式: {"metadata": ..., "records": [...]}
        if isinstance(raw_data, dict) and "records" in raw_data:
            records = raw_data.get("records", [])
        elif isinstance(raw_data, list):
            # 舊格式: 直接是列表
            records = raw_data
        else:
            print(f"[ERROR] 未知的 TimingData 格式")
            return {}
        
        # 處理 TimingData 格式
        for entry in records:
            # 處理新格式: {"timestamp": ..., "data": {"Lines": ...}}
            if isinstance(entry, dict):
                if "data" in entry:
                    data = entry.get("data", {})
                    lines = data.get("Lines", {})
                    timestamp = entry.get("timestamp", "")
                else:
                    lines = entry.get("Lines", {})
                    timestamp = entry.get("Utc", "")
            else:
                continue
            
            for driver_num, driver_data in lines.items():
                if driver_num not in driver_laps:
                    driver_laps[driver_num] = []
                
                # 提取圈速和圈數
                last_lap_time = driver_data.get("LastLapTime", {})
                if isinstance(last_lap_time, dict):
                    lap_time_value = last_lap_time.get("Value", "")
                else:
                    lap_time_value = None
                
                number_of_laps = driver_data.get("NumberOfLaps")
                
                if lap_time_value and number_of_laps:
                    parsed_time = self._parse_lap_time(lap_time_value)
                    if parsed_time and parsed_time > 60 and parsed_time < 180:  # 合理圈速範圍
                        # 避免重複添加
                        if not driver_laps[driver_num] or \
                           driver_laps[driver_num][-1]["lap_number"] != number_of_laps:
                            driver_laps[driver_num].append({
                                "lap_number": number_of_laps,
                                "lap_time": parsed_time,
                                "lap_time_str": lap_time_value,
                                "timestamp": timestamp
                            })
        
        # 排序各車手的圈速
        for driver_num in driver_laps:
            driver_laps[driver_num].sort(key=lambda x: x["lap_number"])
        
        return driver_laps
    
    def _load_tyre_data(self, data_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        載入 TyreStintSeries.json 並提取輪胎策略數據
        
        Args:
            data_path: LiveF1 數據目錄路徑
            
        Returns:
            車手號碼 -> 輪胎資訊列表
        """
        tyre_file = data_path / "TyreStintSeries.json"
        if not tyre_file.exists():
            print(f"[WARNING] 找不到 TyreStintSeries.json")
            return {}
        
        try:
            with open(tyre_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] 載入 TyreStintSeries.json 失敗: {e}")
            return {}
        
        driver_tyres = {}
        
        # 處理新格式: {"metadata": ..., "records": [...]}
        if isinstance(raw_data, dict) and "records" in raw_data:
            records = raw_data.get("records", [])
        elif isinstance(raw_data, list):
            records = raw_data
        else:
            print(f"[WARNING] 未知的 TyreStintSeries 格式")
            return {}
        
        for entry in records:
            # 處理新格式: {"timestamp": ..., "data": {"Stints": ...}}
            if isinstance(entry, dict):
                if "data" in entry:
                    data = entry.get("data", {})
                    stints = data.get("Stints", {})
                else:
                    stints = entry.get("Stints", {})
            else:
                continue
            
            for driver_num, stint_data in stints.items():
                if driver_num not in driver_tyres:
                    driver_tyres[driver_num] = []
                
                # 處理不同的 stint 格式
                if isinstance(stint_data, list):
                    for stint in stint_data:
                        if isinstance(stint, dict):
                            driver_tyres[driver_num].append({
                                "compound": stint.get("Compound", "UNKNOWN"),
                                "total_laps": stint.get("TotalLaps", 0),
                                "new": stint.get("New", True),
                                "start_laps": stint.get("StartLaps", 0)
                            })
                elif isinstance(stint_data, dict):
                    # 格式: {"1": {"TotalLaps": 39}, "2": {"TotalLaps": 18}}
                    for stint_num, stint_info in stint_data.items():
                        if isinstance(stint_info, dict):
                            total_laps = stint_info.get("TotalLaps", 0)
                            if total_laps > 0:
                                # 檢查是否已存在相同的 stint
                                existing_stints = [s.get("stint_number") for s in driver_tyres[driver_num]]
                                if stint_num not in existing_stints:
                                    driver_tyres[driver_num].append({
                                        "stint_number": stint_num,
                                        "compound": stint_info.get("Compound", "UNKNOWN"),
                                        "total_laps": total_laps,
                                        "new": stint_info.get("New", True)
                                    })
        
        return driver_tyres
    
    def _calculate_fuel_correction(
        self, 
        lap_number: int, 
        actual_time: float, 
        fuel_params: Dict[str, float]
    ) -> Dict[str, float]:
        """
        計算燃油校正後的圈速
        
        公式: T_corrected = T_actual + fuel_effect_coef * fuel_consumed
        
        Args:
            lap_number: 圈數
            actual_time: 實際圈速 (秒)
            fuel_params: 燃油參數
            
        Returns:
            包含校正結果的字典
        """
        start_fuel = fuel_params["start_fuel_kg"]
        fuel_per_lap = fuel_params["fuel_kg_per_lap"]
        fuel_effect = fuel_params["fuel_effect_coefficient"]
        
        # 計算該圈剩餘燃油
        fuel_remaining = start_fuel - (lap_number * fuel_per_lap)
        fuel_remaining = max(fuel_remaining, 5.0)  # 最低安全燃油量
        
        # 計算已消耗燃油
        fuel_consumed = start_fuel - fuel_remaining
        
        # 燃油影響 (重車慢多少秒)
        fuel_penalty = fuel_effect * (start_fuel - fuel_remaining)
        
        # 將當前圈速校正到滿油狀態
        # 由於滿油時會慢，所以實際計算真實配速需要將當前快速加上燃油損失
        corrected_time = actual_time + fuel_effect * fuel_remaining
        
        # 計算等效空車配速 (用於比較真實能力)
        equivalent_empty_time = actual_time - fuel_penalty
        
        return {
            "actual_time": actual_time,
            "corrected_time": corrected_time,
            "equivalent_empty_time": equivalent_empty_time,
            "fuel_remaining_kg": fuel_remaining,
            "fuel_consumed_kg": fuel_consumed,
            "fuel_penalty_seconds": fuel_penalty,
            "correction_applied_seconds": fuel_effect * fuel_remaining
        }
    
    def analyze(
        self, 
        year: int, 
        race: str, 
        session: str = "R",
        drivers: List[str] = None,
        show_detailed_output: bool = True
    ) -> Dict[str, Any]:
        """
        執行燃油校正圈速分析
        
        Args:
            year: 年份
            race: 賽事名稱 (e.g., "Italian", "Japanese")
            session: 賽事類型 (R, Q, FP1, FP2, FP3)
            drivers: 指定車手號碼列表，None 表示分析所有車手
            show_detailed_output: 是否顯示詳細輸出
            
        Returns:
            分析結果字典
        """
        print(f"\n{'='*60}")
        print(f"[F53] 燃油校正圈速分析 - Fuel-Corrected Lap Time Analysis")
        print(f"{'='*60}")
        print(f"[INFO] 年份: {year} | 賽事: {race} | 場次: {session}")
        
        # 獲取燃油參數
        fuel_params = self._get_track_fuel_params(race)
        print(f"[FUEL] 賽道: {fuel_params['track_name']}")
        print(f"[FUEL] 每圈燃油消耗: {fuel_params['fuel_kg_per_lap']} kg/lap")
        print(f"[FUEL] 燃油影響係數: {fuel_params['fuel_effect_coefficient']} s/kg")
        print(f"[FUEL] 起跑燃油量: {fuel_params['start_fuel_kg']} kg")
        
        # 尋找 LiveF1 數據
        data_path = self._find_livef1_data(year, race, session)
        if not data_path:
            return {
                "success": False,
                "error": f"找不到 LiveF1 數據: {year}/{race}/{session}",
                "function_id": "53"
            }
        
        # 載入圈速數據
        print(f"[LOAD] 載入 TimingData.json...")
        driver_laps = self._load_timing_data(data_path)
        if not driver_laps:
            return {
                "success": False,
                "error": "無法載入圈速數據",
                "function_id": "53"
            }
        
        print(f"[INFO] 找到 {len(driver_laps)} 位車手的圈速數據")
        
        # 載入輪胎數據
        print(f"[LOAD] 載入 TyreStintSeries.json...")
        driver_tyres = self._load_tyre_data(data_path)
        
        # 過濾車手 (如果指定)
        if drivers:
            driver_laps = {k: v for k, v in driver_laps.items() if k in drivers}
        
        # 進行燃油校正分析
        results = {
            "metadata": {
                "year": year,
                "race": race,
                "session": session,
                "track_name": fuel_params["track_name"],
                "fuel_params": fuel_params,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_source": "LiveF1 (OpenF1 API)"
            },
            "drivers": {},
            "summary": {}
        }
        
        print(f"\n[ANALYZE] 進行燃油校正分析...")
        
        for driver_num, laps in driver_laps.items():
            if len(laps) < 3:  # 至少需要 3 圈數據
                continue
            
            driver_results = {
                "total_laps": len(laps),
                "laps": [],
                "statistics": {}
            }
            
            corrected_times = []
            actual_times = []
            fuel_penalties = []
            
            for lap_data in laps:
                lap_num = lap_data["lap_number"]
                actual_time = lap_data["lap_time"]
                
                # 計算燃油校正
                correction = self._calculate_fuel_correction(
                    lap_num, actual_time, fuel_params
                )
                
                driver_results["laps"].append({
                    "lap_number": lap_num,
                    "actual_time": round(actual_time, 3),
                    "actual_time_str": lap_data["lap_time_str"],
                    "corrected_time": round(correction["corrected_time"], 3),
                    "equivalent_empty_time": round(correction["equivalent_empty_time"], 3),
                    "fuel_remaining_kg": round(correction["fuel_remaining_kg"], 1),
                    "fuel_penalty_seconds": round(correction["fuel_penalty_seconds"], 3)
                })
                
                corrected_times.append(correction["corrected_time"])
                actual_times.append(actual_time)
                fuel_penalties.append(correction["fuel_penalty_seconds"])
            
            # 計算統計數據
            if corrected_times:
                driver_results["statistics"] = {
                    "avg_actual_time": round(sum(actual_times) / len(actual_times), 3),
                    "avg_corrected_time": round(sum(corrected_times) / len(corrected_times), 3),
                    "best_actual_time": round(min(actual_times), 3),
                    "best_corrected_time": round(min(corrected_times), 3),
                    "avg_fuel_penalty": round(sum(fuel_penalties) / len(fuel_penalties), 3),
                    "max_fuel_penalty": round(max(fuel_penalties), 3),
                    "improvement_from_fuel": round(
                        sum(corrected_times) / len(corrected_times) - 
                        sum(actual_times) / len(actual_times), 3
                    )
                }
            
            # 添加輪胎資訊
            if driver_num in driver_tyres:
                driver_results["tyre_stints"] = driver_tyres[driver_num]
            
            results["drivers"][driver_num] = driver_results
        
        # 生成總結
        if results["drivers"]:
            all_corrected_bests = [
                d["statistics"]["best_corrected_time"] 
                for d in results["drivers"].values() 
                if d.get("statistics")
            ]
            all_actual_bests = [
                d["statistics"]["best_actual_time"] 
                for d in results["drivers"].values() 
                if d.get("statistics")
            ]
            
            if all_corrected_bests:
                # 找出校正後最快的車手
                best_driver = min(
                    results["drivers"].items(),
                    key=lambda x: x[1]["statistics"].get("best_corrected_time", 999)
                )
                
                results["summary"] = {
                    "total_drivers_analyzed": len(results["drivers"]),
                    "best_corrected_lap_driver": best_driver[0],
                    "best_corrected_lap_time": best_driver[1]["statistics"]["best_corrected_time"],
                    "field_best_actual": round(min(all_actual_bests), 3),
                    "field_best_corrected": round(min(all_corrected_bests), 3),
                    "avg_fuel_correction_benefit": round(
                        sum([
                            d["statistics"]["improvement_from_fuel"] 
                            for d in results["drivers"].values() 
                            if d.get("statistics")
                        ]) / len(results["drivers"]), 3
                    )
                }
        
        # 顯示結果 (如果啟用詳細輸出)
        if show_detailed_output:
            self._print_analysis_results(results)
        
        print(f"\n[SUCCESS] F53 燃油校正圈速分析完成")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "data": results,
            "function_id": "53"
        }
    
    def _print_analysis_results(self, results: Dict[str, Any]) -> None:
        """格式化輸出分析結果"""
        print(f"\n{'='*60}")
        print("燃油校正圈速分析結果")
        print(f"{'='*60}")
        
        # 總結
        summary = results.get("summary", {})
        if summary:
            print(f"\n[SUMMARY] 分析總結:")
            print(f"  - 分析車手數: {summary.get('total_drivers_analyzed', 0)}")
            print(f"  - 全場最快實際圈速: {summary.get('field_best_actual', 'N/A')} 秒")
            print(f"  - 全場最快校正圈速: {summary.get('field_best_corrected', 'N/A')} 秒")
            print(f"  - 平均燃油校正影響: +{summary.get('avg_fuel_correction_benefit', 0):.3f} 秒")
            print(f"  - 校正後最快車手: #{summary.get('best_corrected_lap_driver', 'N/A')}")
        
        # 各車手數據 (前5名)
        print(f"\n[DRIVERS] 各車手分析結果 (依校正後最快圈速排序):")
        print("-" * 70)
        print(f"{'車手':^6} | {'圈數':^4} | {'最快實際':^10} | {'最快校正':^10} | {'燃油影響':^10}")
        print("-" * 70)
        
        sorted_drivers = sorted(
            results["drivers"].items(),
            key=lambda x: x[1]["statistics"].get("best_corrected_time", 999)
        )
        
        for driver_num, data in sorted_drivers[:10]:
            stats = data.get("statistics", {})
            print(f"  #{driver_num:>3} | {data['total_laps']:>4} | "
                  f"{stats.get('best_actual_time', 'N/A'):>10.3f} | "
                  f"{stats.get('best_corrected_time', 'N/A'):>10.3f} | "
                  f"+{stats.get('avg_fuel_penalty', 0):>8.3f}s")
        
        print("-" * 70)
    
    def export_to_json(self, results: Dict[str, Any], output_path: str = None) -> str:
        """
        將分析結果導出為 JSON 檔案
        
        Args:
            results: 分析結果
            output_path: 輸出路徑，None 則自動生成
            
        Returns:
            輸出檔案路徑
        """
        if not results.get("success"):
            print("[ERROR] 無法導出失敗的分析結果")
            return None
        
        metadata = results.get("data", {}).get("metadata", {})
        
        if output_path is None:
            json_dir = self.base_path / "json"
            json_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fuel_corrected_laptime_{metadata.get('year', 'unknown')}_{metadata.get('race', 'unknown')}_{metadata.get('session', 'R')}_{timestamp}.json"
            output_path = json_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results.get("data", {}), f, ensure_ascii=False, indent=2)
        
        print(f"[EXPORT] 結果已導出至: {output_path}")
        return str(output_path)


def run_fuel_corrected_analysis(
    data_loader = None,
    year: int = None,
    race: str = None,
    session: str = "R",
    drivers: List[str] = None,
    show_detailed_output: bool = True
) -> Dict[str, Any]:
    """
    執行 F53 燃油校正圈速分析的入口函數
    
    Args:
        data_loader: 數據載入器 (可選)
        year: 年份
        race: 賽事名稱
        session: 賽事類型
        drivers: 指定車手列表
        show_detailed_output: 顯示詳細輸出
        
    Returns:
        分析結果
    """
    # 從 data_loader 獲取參數 (如果提供)
    if data_loader is not None:
        year = year or getattr(data_loader, 'year', 2024)
        race = race or getattr(data_loader, 'race_name', 'Italian')
        session = session or getattr(data_loader, 'session_type', 'R')
    
    # 使用預設值
    year = year or 2024
    race = race or "Italian"
    session = session or "R"
    
    analyzer = FuelCorrectedLaptimeAnalyzer()
    results = analyzer.analyze(
        year=year,
        race=race,
        session=session,
        drivers=drivers,
        show_detailed_output=show_detailed_output
    )
    
    # 導出 JSON
    if results.get("success"):
        analyzer.export_to_json(results)
    
    return results


if __name__ == "__main__":
    """直接執行測試"""
    import argparse
    
    parser = argparse.ArgumentParser(description="F53 燃油校正圈速分析")
    parser.add_argument("-y", "--year", type=int, default=2024, help="年份")
    parser.add_argument("-r", "--race", type=str, default="Italian", help="賽事名稱")
    parser.add_argument("-s", "--session", type=str, default="R", help="賽事類型")
    parser.add_argument("-d", "--drivers", nargs="+", help="指定車手號碼")
    parser.add_argument("-q", "--quiet", action="store_true", help="安靜模式")
    
    args = parser.parse_args()
    
    result = run_fuel_corrected_analysis(
        year=args.year,
        race=args.race,
        session=args.session,
        drivers=args.drivers,
        show_detailed_output=not args.quiet
    )
    
    if result.get("success"):
        print("\n[COMPLETE] 分析成功完成")
    else:
        print(f"\n[FAILED] 分析失敗: {result.get('error', '未知錯誤')}")
