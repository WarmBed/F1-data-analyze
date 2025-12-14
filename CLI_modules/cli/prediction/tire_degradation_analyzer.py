#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F56 - 輪胎衰退分析器 (Tire Degradation Analyzer)

功能:
    使用 F1 Official Live Timing 數據進行輪胎衰退分析
    採用時變線性模型: degradation(t) = base_rate + acceleration * tire_age
    
原理 (基於 Cappello & Hoegh 2025 論文):
    - 觀測方程: y_t = alpha_t + gamma * fuel_t + epsilon_t
    - 過程方程: alpha_{t+1} = (1-I_pit) * (alpha_t + nu[compound]) + I_pit * alpha_reset + eta_t
    - 時變衰退: nu_{t+1} = nu_t + beta[compound]
    
簡化實用公式:
    total_degradation = base_rate * laps + 0.5 * acceleration * laps^2
    
數據來源:
    - json/LiveF1/{year}/{race}_{session}/TimingAppData.json (F1 官方 Live Timing)
    - json/LiveF1/{year}/{race}_{session}/TimingData.json (圈速數據)
    - config/tire_degradation_database.json (賽道衰退係數)
    
注意: LiveF1 資料夾存放的是 F1 官方 Live Timing 數據 (livetiming.formula1.com)
    
輸出:
    - 各配方衰退率統計
    - 最佳 stint 長度建議
    - 衰退趨勢分析

版本: 1.0.0
作者: F1 Analysis Team
日期: 2025-12-03
參考: Cappello & Hoegh 2025 - A State-Space Approach to Modeling Tire Degradation in Formula 1 Racing
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import math


class TireDegradationAnalyzer:
    """F56 輪胎衰退分析器 - 時變線性模型"""
    
    def __init__(self, base_path: str = None):
        """
        初始化分析器
        
        Args:
            base_path: 專案根目錄路徑
        """
        if base_path is None:
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent.parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.livef1_path = self.base_path / "json" / "LiveF1"
        self.tire_db_path = self.base_path / "config" / "tire_degradation_database.json"
        self.fuel_db_path = self.base_path / "config" / "fuel_coefficients_database.json"
        
        # 載入資料庫
        self.tire_database = self._load_tire_database()
        self.fuel_database = self._load_fuel_database()
        
        # 預設衰退參數
        self.default_degradation = {
            "SOFT": {"base": 0.065, "acceleration": 0.0028},
            "MEDIUM": {"base": 0.045, "acceleration": 0.0017},
            "HARD": {"base": 0.030, "acceleration": 0.0010}
        }
        
        # 暖胎圈數
        self.warmup_laps = 3
    
    def _load_tire_database(self) -> Dict[str, Any]:
        """載入輪胎衰退係數資料庫"""
        try:
            if self.tire_db_path.exists():
                with open(self.tire_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[WARNING] 找不到輪胎衰退資料庫: {self.tire_db_path}")
                return {"circuits": {}, "default_values": {}}
        except Exception as e:
            print(f"[ERROR] 載入輪胎衰退資料庫失敗: {e}")
            return {"circuits": {}, "default_values": {}}
    
    def _load_fuel_database(self) -> Dict[str, Any]:
        """載入燃油係數資料庫 (用於燃油校正)"""
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
    
    def _get_track_degradation_params(self, race_name: str) -> Dict[str, Any]:
        """
        獲取特定賽道的輪胎衰退參數
        
        Args:
            race_name: 賽事名稱 (e.g., "Austrian", "Italian")
            
        Returns:
            輪胎衰退參數字典
        """
        circuits = self.tire_database.get("circuits", {})
        
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
                "track_name": circuit_data.get("official_name", circuit_name),
                "abrasiveness": circuit_data.get("abrasiveness", "medium"),
                "abrasiveness_multiplier": circuit_data.get("abrasiveness_multiplier", 1.0),
                "base_degradation": circuit_data.get("base_degradation", self.default_degradation),
                "degradation_acceleration": circuit_data.get("degradation_acceleration", {}),
                "optimal_stint_length": circuit_data.get("optimal_stint_length", {}),
                "typical_race_laps": circuit_data.get("typical_race_laps", 60)
            }
        else:
            print(f"[WARNING] 找不到 {race_name} ({circuit_name}) 的輪胎衰退數據，使用預設值")
            defaults = self.tire_database.get("default_values", {})
            return {
                "track_name": race_name,
                "abrasiveness": "medium",
                "abrasiveness_multiplier": 1.0,
                "base_degradation": defaults.get("base_degradation", 
                    {"SOFT": 0.065, "MEDIUM": 0.045, "HARD": 0.030}),
                "degradation_acceleration": defaults.get("degradation_acceleration",
                    {"SOFT": 0.0028, "MEDIUM": 0.0017, "HARD": 0.0010}),
                "optimal_stint_length": defaults.get("optimal_stint_length",
                    {"SOFT": 18, "MEDIUM": 28, "HARD": 40}),
                "typical_race_laps": 60
            }
    
    def _get_fuel_params(self, race_name: str) -> Dict[str, float]:
        """獲取燃油參數用於校正"""
        circuits = self.fuel_database.get("circuits", {})
        
        race_to_circuit = {
            "Italian": "Monza", "Japanese": "Suzuka", "Austrian": "Spielberg",
            "Belgian": "Spa", "Monaco": "Monaco", "British": "Silverstone",
            "Australian": "Melbourne", "Dutch": "Zandvoort", "Hungarian": "Budapest",
            "Singapore": "Singapore", "United_States": "Austin", "Mexico_City": "Mexico",
            "São_Paulo": "Interlagos", "Las_Vegas": "Las_Vegas", "Abu_Dhabi": "Yas_Marina",
            "Qatar": "Lusail", "Spanish": "Barcelona", "Canadian": "Montreal",
            "Miami": "Miami", "Bahrain": "Bahrain", "Saudi_Arabian": "Jeddah",
            "Chinese": "Shanghai", "Emilia_Romagna": "Imola", "Azerbaijan": "Baku"
        }
        
        circuit_name = race_to_circuit.get(race_name, race_name)
        
        if circuit_name in circuits:
            return {
                "fuel_kg_per_lap": circuits[circuit_name].get("fuel_kg_per_lap", 1.75),
                "fuel_effect_coefficient": circuits[circuit_name].get("fuel_effect_coefficient", 0.030),
                "start_fuel_kg": circuits[circuit_name].get("start_fuel_kg", 110)
            }
        return {"fuel_kg_per_lap": 1.75, "fuel_effect_coefficient": 0.030, "start_fuel_kg": 110}
    
    def _find_livef1_data(self, year: int, race: str, session: str) -> Optional[Path]:
        """尋找 LiveF1 數據目錄"""
        year_path = self.livef1_path / str(year)
        if not year_path.exists():
            print(f"[ERROR] 找不到年份目錄: {year_path}")
            return None
        
        session_map = {"R": "Race", "Q": "Qualifying", "FP1": "FP1", "FP2": "FP2", "FP3": "FP3"}
        session_suffix = session_map.get(session, session)
        
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
        
        available_dirs = [d.name for d in year_path.iterdir() if d.is_dir()]
        print(f"[WARNING] 找不到匹配的目錄，可用目錄: {available_dirs}")
        return None
    
    def _parse_lap_time(self, time_str: str) -> Optional[float]:
        """解析圈速字串為秒數"""
        if not time_str or time_str == "" or time_str == "null":
            return None
        
        try:
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            return float(time_str)
        except (ValueError, TypeError):
            return None
    
    def _load_timing_app_data(self, data_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        載入 TimingAppData.json 並提取各車手的輪胎 stint 數據
        
        Returns:
            車手號碼 -> stint 列表的字典
        """
        timing_app_file = data_path / "TimingAppData.json"
        if not timing_app_file.exists():
            print(f"[ERROR] 找不到 TimingAppData.json: {timing_app_file}")
            return {}
        
        try:
            with open(timing_app_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # 處理可能的 JSON 格式問題
                if content.startswith('['):
                    raw_data = json.loads(content)
                else:
                    raw_data = json.loads(content)
        except Exception as e:
            print(f"[ERROR] 載入 TimingAppData.json 失敗: {e}")
            return {}
        
        driver_stints = {}
        
        # 處理 records 格式
        if isinstance(raw_data, dict) and "records" in raw_data:
            records = raw_data.get("records", [])
        elif isinstance(raw_data, list):
            records = raw_data
        else:
            print(f"[ERROR] 未知的 TimingAppData 格式")
            return {}
        
        for entry in records:
            if not isinstance(entry, dict):
                continue
            
            timestamp = entry.get("timestamp", "")
            data = entry.get("data", entry)
            lines = data.get("Lines", {})
            
            for driver_num, driver_data in lines.items():
                if driver_num not in driver_stints:
                    driver_stints[driver_num] = {}
                
                stints = driver_data.get("Stints", {})
                # 處理 Stints 可能是空列表的情況
                if isinstance(stints, list):
                    continue  # 跳過空列表
                if not isinstance(stints, dict):
                    continue
                    
                for stint_num, stint_data in stints.items():
                    if not isinstance(stint_data, dict):
                        continue
                    
                    stint_key = stint_num
                    if stint_key not in driver_stints[driver_num]:
                        driver_stints[driver_num][stint_key] = {
                            "stint_number": int(stint_num),
                            "compound": None,
                            "new": None,
                            "laps": [],
                            "total_laps": 0
                        }
                    
                    stint_record = driver_stints[driver_num][stint_key]
                    
                    # 更新 compound 和 new
                    if "Compound" in stint_data and stint_data["Compound"] != "UNKNOWN":
                        stint_record["compound"] = stint_data["Compound"]
                    if "New" in stint_data:
                        stint_record["new"] = stint_data["New"] == "true" or stint_data["New"] == True
                    if "TotalLaps" in stint_data:
                        stint_record["total_laps"] = max(stint_record["total_laps"], stint_data["TotalLaps"])
                    
                    # 記錄圈速
                    if "LapTime" in stint_data and "LapNumber" in stint_data:
                        lap_time = self._parse_lap_time(stint_data["LapTime"])
                        lap_number = stint_data["LapNumber"]
                        if lap_time and lap_time > 60 and lap_time < 180:
                            # 避免重複
                            existing_laps = [l["lap_number"] for l in stint_record["laps"]]
                            if lap_number not in existing_laps:
                                stint_record["laps"].append({
                                    "lap_number": lap_number,
                                    "lap_time": lap_time,
                                    "timestamp": timestamp
                                })
        
        # 轉換為列表格式並排序
        result = {}
        for driver_num, stints_dict in driver_stints.items():
            stints_list = list(stints_dict.values())
            stints_list.sort(key=lambda x: x["stint_number"])
            # 對每個 stint 的圈速排序
            for stint in stints_list:
                stint["laps"].sort(key=lambda x: x["lap_number"])
            result[driver_num] = stints_list
        
        return result
    
    def _load_timing_data(self, data_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """載入 TimingData.json 獲取更完整的圈速數據"""
        timing_file = data_path / "TimingData.json"
        if not timing_file.exists():
            return {}
        
        try:
            with open(timing_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"[WARNING] 載入 TimingData.json 失敗: {e}")
            return {}
        
        driver_laps = {}
        
        if isinstance(raw_data, dict) and "records" in raw_data:
            records = raw_data.get("records", [])
        elif isinstance(raw_data, list):
            records = raw_data
        else:
            return {}
        
        for entry in records:
            if not isinstance(entry, dict):
                continue
            
            data = entry.get("data", entry)
            lines = data.get("Lines", {})
            timestamp = entry.get("timestamp", "")
            
            for driver_num, driver_data in lines.items():
                if driver_num not in driver_laps:
                    driver_laps[driver_num] = []
                
                last_lap_time = driver_data.get("LastLapTime", {})
                if isinstance(last_lap_time, dict):
                    lap_time_value = last_lap_time.get("Value", "")
                else:
                    lap_time_value = None
                
                number_of_laps = driver_data.get("NumberOfLaps")
                
                if lap_time_value and number_of_laps:
                    parsed_time = self._parse_lap_time(lap_time_value)
                    if parsed_time and parsed_time > 60 and parsed_time < 180:
                        existing = [l["lap_number"] for l in driver_laps[driver_num]]
                        if number_of_laps not in existing:
                            driver_laps[driver_num].append({
                                "lap_number": number_of_laps,
                                "lap_time": parsed_time,
                                "timestamp": timestamp
                            })
        
        for driver_num in driver_laps:
            driver_laps[driver_num].sort(key=lambda x: x["lap_number"])
        
        return driver_laps
    
    def _calculate_stint_degradation(
        self, 
        stint_laps: List[Dict[str, Any]], 
        compound: str,
        fuel_params: Dict[str, float],
        track_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        計算單個 stint 的輪胎衰退統計
        
        使用時變線性模型: degradation(t) = base_rate + acceleration * t
        
        Args:
            stint_laps: stint 內的圈速列表
            compound: 輪胎配方
            fuel_params: 燃油參數
            track_params: 賽道衰退參數
            
        Returns:
            衰退統計字典
        """
        if len(stint_laps) < 3:
            return {"valid": False, "reason": "圈數不足"}
        
        # 獲取預設衰退參數
        base_deg = track_params.get("base_degradation", {})
        accel_deg = track_params.get("degradation_acceleration", {})
        
        expected_base = base_deg.get(compound, 0.05)
        expected_accel = accel_deg.get(compound, 0.002)
        
        # 燃油校正
        fuel_per_lap = fuel_params["fuel_kg_per_lap"]
        fuel_effect = fuel_params["fuel_effect_coefficient"]
        start_fuel = fuel_params["start_fuel_kg"]
        
        corrected_laps = []
        for lap_data in stint_laps:
            lap_num = lap_data["lap_number"]
            actual_time = lap_data["lap_time"]
            
            # 估算該圈剩餘燃油
            fuel_remaining = max(start_fuel - lap_num * fuel_per_lap, 5.0)
            fuel_consumed = start_fuel - fuel_remaining
            
            # 燃油校正: 將圈速校正到滿油狀態
            # 燃油減少會使車輛變輕、圈速變快
            # 要校正到滿油狀態，需要把已消耗燃油帶來的時間增益加回去
            corrected_time = actual_time + fuel_effect * fuel_consumed
            
            corrected_laps.append({
                "lap_number": lap_num,
                "actual_time": actual_time,
                "corrected_time": corrected_time,
                "fuel_correction": fuel_effect * fuel_consumed
            })
        
        # 跳過暖胎圈 (前 N 圈)
        analysis_laps = corrected_laps[min(self.warmup_laps, len(corrected_laps)-1):]
        
        if len(analysis_laps) < 2:
            return {"valid": False, "reason": "分析圈數不足"}
        
        # 計算衰退率 (簡單線性回歸)
        n = len(analysis_laps)
        sum_x = sum(i for i in range(n))
        sum_y = sum(lap["corrected_time"] for lap in analysis_laps)
        sum_xy = sum(i * lap["corrected_time"] for i, lap in enumerate(analysis_laps))
        sum_x2 = sum(i * i for i in range(n))
        
        # 線性回歸斜率 = 衰退率
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return {"valid": False, "reason": "回歸計算失敗"}
        
        observed_degradation_rate = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - observed_degradation_rate * sum_x) / n
        
        # 計算 R² (決定係數)
        mean_y = sum_y / n
        ss_tot = sum((lap["corrected_time"] - mean_y) ** 2 for lap in analysis_laps)
        ss_res = sum((lap["corrected_time"] - (intercept + observed_degradation_rate * i)) ** 2 
                     for i, lap in enumerate(analysis_laps))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # 計算二次項係數 (衰退加速度)
        # 使用差分法估算加速度
        if len(analysis_laps) >= 4:
            first_half_deg = (analysis_laps[len(analysis_laps)//2]["corrected_time"] - 
                             analysis_laps[0]["corrected_time"]) / (len(analysis_laps)//2)
            second_half_deg = (analysis_laps[-1]["corrected_time"] - 
                              analysis_laps[len(analysis_laps)//2]["corrected_time"]) / (len(analysis_laps) - len(analysis_laps)//2)
            observed_acceleration = (second_half_deg - first_half_deg) / (len(analysis_laps)//2)
        else:
            observed_acceleration = expected_accel
        
        return {
            "valid": True,
            "total_laps": len(stint_laps),
            "analysis_laps": len(analysis_laps),
            "warmup_laps_skipped": min(self.warmup_laps, len(stint_laps)-1),
            "observed_degradation_rate": round(observed_degradation_rate, 4),
            "observed_acceleration": round(observed_acceleration, 5),
            "expected_degradation_rate": expected_base,
            "expected_acceleration": expected_accel,
            "rate_difference": round(observed_degradation_rate - expected_base, 4),
            "base_lap_time": round(intercept, 3),
            "best_corrected_time": round(min(lap["corrected_time"] for lap in corrected_laps), 3),
            "worst_corrected_time": round(max(lap["corrected_time"] for lap in corrected_laps), 3),
            "total_degradation": round(max(lap["corrected_time"] for lap in corrected_laps) - 
                                      min(lap["corrected_time"] for lap in corrected_laps), 3),
            "r_squared": round(r_squared, 4),
            "lap_details": corrected_laps
        }
    
    def _aggregate_track_statistics(
        self, 
        all_stints: Dict[str, List[Dict[str, Any]]],
        track_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        彙總所有車手的 stint 數據，生成賽道級統計
        
        Args:
            all_stints: 所有車手的 stint 分析結果
            track_params: 賽道參數
            
        Returns:
            賽道級統計
        """
        compound_stats = {"SOFT": [], "MEDIUM": [], "HARD": []}
        
        for driver_num, stints in all_stints.items():
            for stint in stints:
                compound = stint.get("compound")
                analysis = stint.get("analysis", {})
                
                if compound and compound in compound_stats and analysis.get("valid"):
                    compound_stats[compound].append({
                        "driver": driver_num,
                        "stint_number": stint.get("stint_number"),
                        "degradation_rate": analysis["observed_degradation_rate"],
                        "acceleration": analysis["observed_acceleration"],
                        "total_laps": analysis["total_laps"],
                        "r_squared": analysis["r_squared"]
                    })
        
        # 計算各配方統計
        track_statistics = {}
        for compound, stints in compound_stats.items():
            if not stints:
                track_statistics[compound] = {
                    "sample_size": 0,
                    "avg_degradation_rate": track_params["base_degradation"].get(compound, 0.05),
                    "avg_acceleration": track_params["degradation_acceleration"].get(compound, 0.002),
                    "data_source": "database_default"
                }
                continue
            
            avg_deg = sum(s["degradation_rate"] for s in stints) / len(stints)
            avg_accel = sum(s["acceleration"] for s in stints) / len(stints)
            avg_laps = sum(s["total_laps"] for s in stints) / len(stints)
            avg_r2 = sum(s["r_squared"] for s in stints) / len(stints)
            
            # 計算標準差
            if len(stints) > 1:
                std_deg = math.sqrt(sum((s["degradation_rate"] - avg_deg) ** 2 for s in stints) / (len(stints) - 1))
            else:
                std_deg = 0
            
            # 計算最佳 stint 長度 (基於衰退率)
            # 當累計衰退 > 進站損失時應該換胎
            pit_loss = 25  # 假設進站損失 25 秒
            if avg_deg > 0:
                optimal_stint = int(math.sqrt(2 * pit_loss / avg_deg))
            else:
                optimal_stint = track_params["optimal_stint_length"].get(compound, 25)
            
            track_statistics[compound] = {
                "sample_size": len(stints),
                "avg_degradation_rate": round(avg_deg, 4),
                "std_degradation_rate": round(std_deg, 4),
                "avg_acceleration": round(avg_accel, 5),
                "avg_stint_length": round(avg_laps, 1),
                "optimal_stint_length": min(optimal_stint, 50),  # 上限 50 圈
                "avg_r_squared": round(avg_r2, 3),
                "expected_rate": track_params["base_degradation"].get(compound, 0.05),
                "rate_vs_expected": round(avg_deg - track_params["base_degradation"].get(compound, 0.05), 4),
                "data_source": "observed",
                "stints": stints
            }
        
        return track_statistics
    
    def analyze(
        self, 
        year: int, 
        race: str, 
        session: str = "R",
        drivers: List[str] = None,
        show_detailed_output: bool = True
    ) -> Dict[str, Any]:
        """
        執行 F56 輪胎衰退分析
        
        Args:
            year: 年份
            race: 賽事名稱 (e.g., "Austrian", "Italian")
            session: 賽事類型 (R, Q, FP1, FP2, FP3)
            drivers: 指定車手號碼列表，None 表示分析所有車手
            show_detailed_output: 是否顯示詳細輸出
            
        Returns:
            分析結果字典
        """
        print(f"\n{'='*70}")
        print(f"[F56] 輪胎衰退分析 - Tire Degradation Analysis (Time-Varying Linear Model)")
        print(f"{'='*70}")
        print(f"[INFO] 年份: {year} | 賽事: {race} | 場次: {session}")
        print(f"[MODEL] 公式: degradation(t) = base_rate + acceleration * tire_age")
        
        # 獲取賽道參數
        track_params = self._get_track_degradation_params(race)
        fuel_params = self._get_fuel_params(race)
        
        print(f"[TRACK] 賽道: {track_params['track_name']}")
        print(f"[TRACK] 路面粗糙度: {track_params['abrasiveness']} (x{track_params['abrasiveness_multiplier']})")
        print(f"[TIRE] 預設衰退率 - SOFT: {track_params['base_degradation'].get('SOFT', 'N/A')} s/lap")
        print(f"[TIRE] 預設衰退率 - MEDIUM: {track_params['base_degradation'].get('MEDIUM', 'N/A')} s/lap")
        print(f"[TIRE] 預設衰退率 - HARD: {track_params['base_degradation'].get('HARD', 'N/A')} s/lap")
        
        # 尋找 LiveF1 數據
        data_path = self._find_livef1_data(year, race, session)
        if not data_path:
            return {
                "success": False,
                "error": f"找不到 LiveF1 數據: {year}/{race}/{session}",
                "function_id": "56"
            }
        
        # 載入 stint 數據
        print(f"[LOAD] 載入 TimingAppData.json...")
        driver_stints = self._load_timing_app_data(data_path)
        if not driver_stints:
            return {
                "success": False,
                "error": "無法載入輪胎 stint 數據",
                "function_id": "56"
            }
        
        print(f"[INFO] 找到 {len(driver_stints)} 位車手的 stint 數據")
        
        # 過濾車手
        if drivers:
            driver_stints = {k: v for k, v in driver_stints.items() if k in drivers}
        
        # 分析各車手的 stint
        print(f"\n[ANALYZE] 進行輪胎衰退分析...")
        
        analyzed_stints = {}
        for driver_num, stints in driver_stints.items():
            analyzed_stints[driver_num] = []
            
            for stint in stints:
                compound = stint.get("compound")
                laps = stint.get("laps", [])
                
                if not compound or compound == "UNKNOWN" or len(laps) < 3:
                    analyzed_stints[driver_num].append({
                        **stint,
                        "analysis": {"valid": False, "reason": "數據不足或配方未知"}
                    })
                    continue
                
                # 計算衰退
                analysis = self._calculate_stint_degradation(
                    laps, compound, fuel_params, track_params
                )
                
                analyzed_stints[driver_num].append({
                    **stint,
                    "analysis": analysis
                })
        
        # 生成賽道級統計
        track_statistics = self._aggregate_track_statistics(analyzed_stints, track_params)
        
        # 構建結果
        results = {
            "metadata": {
                "year": year,
                "race": race,
                "session": session,
                "track_name": track_params["track_name"],
                "abrasiveness": track_params["abrasiveness"],
                "model_type": "time_varying_linear",
                "model_formula": "degradation(t) = base_rate + acceleration * tire_age",
                "analysis_timestamp": datetime.now().isoformat(),
                "data_source": "F1 Official Live Timing (livetiming.formula1.com)",
                "reference": "Cappello & Hoegh 2025 - State-Space Model for Tire Degradation"
            },
            "track_parameters": {
                "base_degradation": track_params["base_degradation"],
                "degradation_acceleration": track_params["degradation_acceleration"],
                "optimal_stint_length": track_params["optimal_stint_length"]
            },
            "track_statistics": track_statistics,
            "drivers": analyzed_stints,
            "summary": {}
        }
        
        # 生成總結
        total_stints = sum(len(stints) for stints in analyzed_stints.values())
        valid_stints = sum(
            1 for stints in analyzed_stints.values() 
            for s in stints if s.get("analysis", {}).get("valid")
        )
        
        results["summary"] = {
            "total_drivers_analyzed": len(analyzed_stints),
            "total_stints": total_stints,
            "valid_stints": valid_stints,
            "compound_usage": {
                compound: stats.get("sample_size", 0) 
                for compound, stats in track_statistics.items()
            },
            "recommendations": self._generate_recommendations(track_statistics, track_params)
        }
        
        # 顯示結果
        if show_detailed_output:
            self._print_analysis_results(results)
        
        print(f"\n[SUCCESS] F56 輪胎衰退分析完成")
        print(f"{'='*70}\n")
        
        return {
            "success": True,
            "data": results,
            "function_id": "56"
        }
    
    def _generate_recommendations(
        self, 
        track_statistics: Dict[str, Any],
        track_params: Dict[str, Any]
    ) -> List[str]:
        """生成策略建議"""
        recommendations = []
        
        for compound, stats in track_statistics.items():
            if stats.get("sample_size", 0) == 0:
                continue
            
            observed_rate = stats.get("avg_degradation_rate", 0)
            expected_rate = stats.get("expected_rate", 0)
            optimal_stint = stats.get("optimal_stint_length", 25)
            
            if observed_rate > expected_rate * 1.2:
                recommendations.append(
                    f"{compound}: 衰退率高於預期 ({observed_rate:.3f} vs {expected_rate:.3f})，建議縮短 stint 至 {optimal_stint} 圈"
                )
            elif observed_rate < expected_rate * 0.8:
                recommendations.append(
                    f"{compound}: 衰退率低於預期 ({observed_rate:.3f} vs {expected_rate:.3f})，可延長 stint 長度"
                )
            else:
                recommendations.append(
                    f"{compound}: 衰退符合預期，建議 stint 長度 {optimal_stint} 圈"
                )
        
        return recommendations
    
    def _print_analysis_results(self, results: Dict[str, Any]) -> None:
        """格式化輸出分析結果"""
        print(f"\n{'='*70}")
        print("輪胎衰退分析結果 - Track-Level Statistics")
        print(f"{'='*70}")
        
        track_stats = results.get("track_statistics", {})
        
        print(f"\n[COMPOUND STATISTICS]")
        print("-" * 70)
        print(f"{'配方':^8} | {'樣本數':^6} | {'衰退率':^10} | {'加速度':^10} | {'最佳 stint':^10} | {'R²':^6}")
        print("-" * 70)
        
        for compound in ["SOFT", "MEDIUM", "HARD"]:
            stats = track_stats.get(compound, {})
            if stats.get("sample_size", 0) > 0:
                print(f" {compound:^7} | {stats['sample_size']:^6} | "
                      f"{stats['avg_degradation_rate']:>8.4f}s | "
                      f"{stats['avg_acceleration']:>9.5f} | "
                      f"{stats['optimal_stint_length']:>8} 圈 | "
                      f"{stats.get('avg_r_squared', 0):>5.3f}")
            else:
                expected = results.get("track_parameters", {}).get("base_degradation", {}).get(compound, "N/A")
                print(f" {compound:^7} | {'N/A':^6} | {expected if expected != 'N/A' else 'N/A':>8}s | {'(預設)':^10} | {'N/A':^10} | {'N/A':^6}")
        
        print("-" * 70)
        
        # 總結
        summary = results.get("summary", {})
        print(f"\n[SUMMARY]")
        print(f"  - 分析車手數: {summary.get('total_drivers_analyzed', 0)}")
        print(f"  - 總 stint 數: {summary.get('total_stints', 0)}")
        print(f"  - 有效分析: {summary.get('valid_stints', 0)}")
        
        print(f"\n[RECOMMENDATIONS]")
        for rec in summary.get("recommendations", []):
            print(f"  - {rec}")
    
    def export_to_json(self, results: Dict[str, Any], output_path: str = None) -> str:
        """將分析結果導出為 JSON 檔案"""
        if not results.get("success"):
            print("[ERROR] 無法導出失敗的分析結果")
            return None
        
        metadata = results.get("data", {}).get("metadata", {})
        
        if output_path is None:
            json_dir = self.base_path / "json"
            json_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tire_degradation_{metadata.get('year', 'unknown')}_{metadata.get('race', 'unknown')}_{metadata.get('session', 'R')}_{timestamp}.json"
            output_path = json_dir / filename
        
        # 移除詳細圈速數據以減少檔案大小
        export_data = results.get("data", {}).copy()
        for driver_num, stints in export_data.get("drivers", {}).items():
            for stint in stints:
                if "analysis" in stint and "lap_details" in stint["analysis"]:
                    del stint["analysis"]["lap_details"]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"[EXPORT] 結果已導出至: {output_path}")
        return str(output_path)
    
    def update_database_from_analysis(self, results: Dict[str, Any]) -> bool:
        """
        根據分析結果更新資料庫 (即時學習功能)
        
        Args:
            results: 分析結果
            
        Returns:
            是否成功更新
        """
        if not results.get("success"):
            return False
        
        data = results.get("data", {})
        metadata = data.get("metadata", {})
        track_stats = data.get("track_statistics", {})
        
        race = metadata.get("race", "")
        if not race:
            return False
        
        # 賽事名稱到賽道代碼的映射
        race_to_circuit = {
            "Italian": "Monza", "Japanese": "Suzuka", "Austrian": "Spielberg",
            "Belgian": "Spa", "Monaco": "Monaco", "British": "Silverstone",
            "Australian": "Melbourne", "Dutch": "Zandvoort", "Hungarian": "Budapest",
            "Singapore": "Singapore", "United_States": "Austin", "Mexico_City": "Mexico",
            "São_Paulo": "Interlagos", "Las_Vegas": "Las_Vegas", "Abu_Dhabi": "Yas_Marina",
            "Qatar": "Lusail", "Spanish": "Barcelona", "Canadian": "Montreal",
            "Miami": "Miami", "Bahrain": "Bahrain", "Saudi_Arabian": "Jeddah",
            "Chinese": "Shanghai", "Emilia_Romagna": "Imola", "Azerbaijan": "Baku"
        }
        
        circuit_name = race_to_circuit.get(race, race)
        
        if circuit_name not in self.tire_database.get("circuits", {}):
            print(f"[WARNING] 賽道 {circuit_name} 不在資料庫中，跳過更新")
            return False
        
        # 更新係數 (使用加權平均)
        weight_new = 0.3  # 新數據權重
        weight_old = 0.7  # 舊數據權重
        
        circuit_data = self.tire_database["circuits"][circuit_name]
        updated = False
        
        for compound in ["SOFT", "MEDIUM", "HARD"]:
            stats = track_stats.get(compound, {})
            if stats.get("sample_size", 0) >= 3 and stats.get("avg_r_squared", 0) > 0.6:
                # 只有當樣本足夠且擬合良好時才更新
                old_base = circuit_data["base_degradation"].get(compound, 0.05)
                new_base = stats["avg_degradation_rate"]
                updated_base = weight_old * old_base + weight_new * new_base
                
                old_accel = circuit_data["degradation_acceleration"].get(compound, 0.002)
                new_accel = stats["avg_acceleration"]
                updated_accel = weight_old * old_accel + weight_new * new_accel
                
                circuit_data["base_degradation"][compound] = round(updated_base, 4)
                circuit_data["degradation_acceleration"][compound] = round(updated_accel, 5)
                circuit_data["optimal_stint_length"][compound] = stats["optimal_stint_length"]
                
                print(f"[UPDATE] {circuit_name} {compound}: base={updated_base:.4f}, accel={updated_accel:.5f}")
                updated = True
        
        if updated:
            # 保存更新後的資料庫
            circuit_data["last_updated_from_data"] = datetime.now().isoformat()
            
            try:
                with open(self.tire_db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.tire_database, f, ensure_ascii=False, indent=2)
                print(f"[SUCCESS] 資料庫已更新: {self.tire_db_path}")
                return True
            except Exception as e:
                print(f"[ERROR] 保存資料庫失敗: {e}")
                return False
        
        return False


def run_tire_degradation_analysis(
    data_loader=None,
    year: int = None,
    race: str = None,
    session: str = "R",
    drivers: List[str] = None,
    show_detailed_output: bool = True,
    update_database: bool = False
) -> Dict[str, Any]:
    """
    執行 F56 輪胎衰退分析的入口函數
    
    Args:
        data_loader: 數據載入器 (可選)
        year: 年份
        race: 賽事名稱
        session: 賽事類型
        drivers: 指定車手列表
        show_detailed_output: 顯示詳細輸出
        update_database: 是否根據分析結果更新資料庫
        
    Returns:
        分析結果
    """
    # 從 data_loader 獲取參數 (如果提供)
    if data_loader is not None:
        year = year or getattr(data_loader, 'year', 2025)
        race = race or getattr(data_loader, 'race_name', 'Austrian')
        session = session or getattr(data_loader, 'session_type', 'R')
    
    # 使用預設值
    year = year or 2025
    race = race or "Austrian"
    session = session or "R"
    
    analyzer = TireDegradationAnalyzer()
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
        
        # 可選: 更新資料庫
        if update_database:
            analyzer.update_database_from_analysis(results)
    
    return results


if __name__ == "__main__":
    """直接執行測試"""
    import argparse
    
    parser = argparse.ArgumentParser(description="F56 輪胎衰退分析")
    parser.add_argument("-y", "--year", type=int, default=2025, help="年份")
    parser.add_argument("-r", "--race", type=str, default="Austrian", help="賽事名稱")
    parser.add_argument("-s", "--session", type=str, default="R", help="賽事類型")
    parser.add_argument("-d", "--drivers", nargs="+", help="指定車手號碼")
    parser.add_argument("-q", "--quiet", action="store_true", help="安靜模式")
    parser.add_argument("-u", "--update", action="store_true", help="更新資料庫")
    
    args = parser.parse_args()
    
    result = run_tire_degradation_analysis(
        year=args.year,
        race=args.race,
        session=args.session,
        drivers=args.drivers,
        show_detailed_output=not args.quiet,
        update_database=args.update
    )
    
    if result.get("success"):
        print("\n[COMPLETE] 分析成功完成")
    else:
        print(f"\n[FAILED] 分析失敗: {result.get('error', '未知錯誤')}")
