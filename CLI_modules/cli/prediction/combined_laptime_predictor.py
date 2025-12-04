#!/usr/bin/env python3
"""
F57 - 綜合圈速預測器 (Combined Laptime Predictor)

功能:
    整合 F55 (燃油校正) + F56 (輪胎衰退) 進行綜合圈速預測
    
原理:
    predicted_time = base_time + fuel_effect + tire_degradation
    
    其中:
    - fuel_effect = fuel_effect_coefficient * fuel_consumed (來自 F55)
    - tire_degradation = base_rate * stint_lap + 0.5 * acceleration * stint_lap² (來自 F56)
    
數據來源:
    - F55: 燃油校正圈速分析結果
    - F56: 輪胎衰退分析結果
    - config/fuel_coefficients_database.json
    - config/tire_degradation_database.json
    
輸出:
    - 每圈預測圈速 vs 實際圈速
    - 燃油效應分解
    - 輪胎衰退效應分解
    - 預測準確度統計
    - 策略模擬 (不同進站策略的圈速預測)

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
import math


class CombinedLaptimePredictor:
    """F57 綜合圈速預測器 - 整合燃油校正與輪胎衰退"""
    
    def __init__(self, base_path: str = None):
        """
        初始化預測器
        
        Args:
            base_path: 專案根目錄路徑
        """
        if base_path is None:
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent.parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.livef1_path = self.base_path / "json" / "LiveF1"
        self.json_output_path = self.base_path / "json"
        
        # 資料庫路徑
        self.fuel_db_path = self.base_path / "config" / "fuel_coefficients_database.json"
        self.tire_db_path = self.base_path / "config" / "tire_degradation_database.json"
        
        # 載入資料庫
        self.fuel_database = self._load_json_database(self.fuel_db_path)
        self.tire_database = self._load_json_database(self.tire_db_path)
        
        # 預設參數
        self.default_fuel_params = {
            "fuel_kg_per_lap": 1.75,
            "fuel_effect_coefficient": 0.030,
            "start_fuel_kg": 110
        }
        
        self.default_tire_params = {
            "base_degradation": {"SOFT": 0.065, "MEDIUM": 0.045, "HARD": 0.030},
            "degradation_acceleration": {"SOFT": 0.0025, "MEDIUM": 0.0015, "HARD": 0.0009}
        }
    
    def _load_json_database(self, db_path: Path) -> Dict[str, Any]:
        """載入 JSON 資料庫"""
        try:
            if db_path.exists():
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[WARNING] Database not found: {db_path}")
                return {}
        except Exception as e:
            print(f"[ERROR] Failed to load database: {e}")
            return {}
    
    def _get_circuit_name(self, race: str) -> str:
        """將賽事名稱對應到資料庫中的賽道名稱"""
        race_to_circuit = {
            "Bahrain": "Bahrain", "Saudi Arabia": "Jeddah", "Australia": "Melbourne",
            "Japan": "Suzuka", "China": "Shanghai", "Miami": "Miami",
            "Emilia Romagna": "Imola", "Monaco": "Monaco", "Canada": "Montreal",
            "Spain": "Barcelona", "Austria": "Spielberg", "Austrian": "Spielberg",
            "Great Britain": "Silverstone", "Hungary": "Budapest", "Belgium": "Spa",
            "Netherlands": "Zandvoort", "Italy": "Monza", "Italian": "Monza",
            "Azerbaijan": "Baku", "Singapore": "Singapore", "United States": "Austin",
            "Mexico": "Mexico", "Brazil": "Interlagos", "Las Vegas": "Las_Vegas",
            "Qatar": "Lusail", "Abu Dhabi": "Yas_Marina"
        }
        return race_to_circuit.get(race, race)
    
    def _get_fuel_params(self, circuit_name: str) -> Dict[str, float]:
        """取得賽道燃油參數"""
        circuits = self.fuel_database.get("circuits", {})
        if circuit_name in circuits:
            circuit_data = circuits[circuit_name]
            return {
                "fuel_kg_per_lap": circuit_data.get("fuel_kg_per_lap", self.default_fuel_params["fuel_kg_per_lap"]),
                "fuel_effect_coefficient": circuit_data.get("fuel_effect_coefficient", self.default_fuel_params["fuel_effect_coefficient"]),
                "start_fuel_kg": circuit_data.get("start_fuel_kg", self.default_fuel_params["start_fuel_kg"])
            }
        return self.default_fuel_params
    
    def _get_tire_params(self, circuit_name: str) -> Dict[str, Any]:
        """取得賽道輪胎參數"""
        circuits = self.tire_database.get("circuits", {})
        if circuit_name in circuits:
            circuit_data = circuits[circuit_name]
            return {
                "base_degradation": circuit_data.get("base_degradation", self.default_tire_params["base_degradation"]),
                "degradation_acceleration": circuit_data.get("degradation_acceleration", self.default_tire_params["degradation_acceleration"]),
                "abrasiveness": circuit_data.get("abrasiveness", "medium")
            }
        return self.default_tire_params
    
    def _calculate_fuel_effect(self, lap_number: int, fuel_params: Dict[str, float]) -> float:
        """
        計算燃油效應 (車輛變輕帶來的圈速增益)
        
        燃油減少 → 車輛變輕 → 圈速變快 (負值表示增益)
        
        Returns:
            fuel_effect: 燃油效應 (秒)，負值表示圈速增益
        """
        fuel_consumed = lap_number * fuel_params["fuel_kg_per_lap"]
        fuel_consumed = min(fuel_consumed, fuel_params["start_fuel_kg"] - 5)  # 保留最低燃油
        
        # 燃油減少帶來的圈速增益 (負值)
        fuel_effect = -fuel_params["fuel_effect_coefficient"] * fuel_consumed
        return fuel_effect
    
    def _calculate_tire_degradation(self, stint_lap: int, compound: str, 
                                     tire_params: Dict[str, Any]) -> float:
        """
        計算輪胎衰退效應 (時變線性模型)
        
        公式: total_degradation = base_rate * laps + 0.5 * acceleration * laps²
        
        Returns:
            degradation: 輪胎衰退效應 (秒)，正值表示圈速變慢
        """
        compound = compound.upper() if compound else "MEDIUM"
        
        base_deg = tire_params.get("base_degradation", self.default_tire_params["base_degradation"])
        accel_deg = tire_params.get("degradation_acceleration", self.default_tire_params["degradation_acceleration"])
        
        base_rate = base_deg.get(compound, 0.045)
        acceleration = accel_deg.get(compound, 0.0015)
        
        # 時變線性模型: 累積衰退
        degradation = base_rate * stint_lap + 0.5 * acceleration * (stint_lap ** 2)
        
        return degradation
    
    def _calculate_predicted_laptime(self, base_time: float, lap_number: int, 
                                      stint_lap: int, compound: str,
                                      fuel_params: Dict[str, float],
                                      tire_params: Dict[str, Any]) -> Dict[str, float]:
        """
        計算預測圈速
        
        公式: predicted_time = base_time + fuel_effect + tire_degradation
        
        Returns:
            Dict with predicted_time, fuel_effect, tire_degradation
        """
        fuel_effect = self._calculate_fuel_effect(lap_number, fuel_params)
        tire_degradation = self._calculate_tire_degradation(stint_lap, compound, tire_params)
        
        predicted_time = base_time + fuel_effect + tire_degradation
        
        return {
            "predicted_time": predicted_time,
            "fuel_effect": fuel_effect,
            "tire_degradation": tire_degradation,
            "net_effect": fuel_effect + tire_degradation
        }
    
    def _find_livef1_data_path(self, year: int, race: str, session: str) -> Optional[Path]:
        """尋找 LiveF1 數據目錄"""
        session_mapping = {
            "R": "Race", "Q": "Qualifying", 
            "FP1": "Practice_1", "FP2": "Practice_2", "FP3": "Practice_3"
        }
        session_name = session_mapping.get(session, session)
        
        # 嘗試不同的命名格式
        patterns = [
            f"{race}_{session_name}",
            f"{race}_{session}",
            f"{race.replace(' ', '_')}_{session_name}",
        ]
        
        year_path = self.livef1_path / str(year)
        if not year_path.exists():
            return None
        
        for pattern in patterns:
            data_path = year_path / pattern
            if data_path.exists():
                return data_path
        
        # 模糊匹配
        for item in year_path.iterdir():
            if item.is_dir() and race.lower() in item.name.lower():
                return item
        
        return None
    
    def _load_timing_data(self, data_path: Path) -> Dict[str, Any]:
        """載入 TimingData.json"""
        timing_file = data_path / "TimingData.json"
        if not timing_file.exists():
            return {}
        
        try:
            with open(timing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load TimingData: {e}")
            return {}
    
    def _load_timing_app_data(self, data_path: Path) -> Dict[str, Any]:
        """載入 TimingAppData.json (包含 stint 和配方資訊)"""
        timing_app_file = data_path / "TimingAppData.json"
        if not timing_app_file.exists():
            return {}
        
        try:
            with open(timing_app_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load TimingAppData: {e}")
            return {}
    
    def _parse_lap_time(self, time_str: str) -> Optional[float]:
        """解析圈速字串為秒數"""
        if not time_str or time_str in ["", "N/A", "null", "None"]:
            return None
        
        try:
            if ":" in str(time_str):
                parts = str(time_str).split(":")
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            else:
                return float(time_str)
        except (ValueError, TypeError):
            return None
    
    def _extract_driver_laps(self, timing_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """從 TimingData 提取各車手的圈速數據"""
        driver_laps = {}
        
        records = timing_data.get("records", [])
        if isinstance(timing_data, list):
            records = timing_data
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            data = record.get("data", record)
            lines = data.get("Lines", {})
            
            for driver_num, driver_data in lines.items():
                if driver_num not in driver_laps:
                    driver_laps[driver_num] = []
                
                # 檢查是否有圈速數據
                lap_time = driver_data.get("LastLapTime", {})
                if isinstance(lap_time, dict):
                    time_value = lap_time.get("Value")
                else:
                    time_value = lap_time
                
                number_of_laps = driver_data.get("NumberOfLaps")
                
                if time_value and number_of_laps:
                    parsed_time = self._parse_lap_time(time_value)
                    if parsed_time and 60 < parsed_time < 180:
                        # 避免重複
                        existing_laps = [l["lap_number"] for l in driver_laps[driver_num]]
                        if number_of_laps not in existing_laps:
                            driver_laps[driver_num].append({
                                "lap_number": number_of_laps,
                                "lap_time": parsed_time
                            })
        
        # 排序
        for driver_num in driver_laps:
            driver_laps[driver_num].sort(key=lambda x: x["lap_number"])
        
        return driver_laps
    
    def _extract_driver_stints(self, timing_app_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """從 TimingAppData 提取各車手的 stint 資訊"""
        driver_stints = {}
        
        records = timing_app_data.get("records", [])
        if isinstance(timing_app_data, list):
            records = timing_app_data
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            data = record.get("data", record)
            lines = data.get("Lines", {})
            
            for driver_num, driver_data in lines.items():
                if driver_num not in driver_stints:
                    driver_stints[driver_num] = {}
                
                stints = driver_data.get("Stints", {})
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
                            "total_laps": 0,
                            "start_lap": None
                        }
                    
                    stint_record = driver_stints[driver_num][stint_key]
                    
                    if "Compound" in stint_data and stint_data["Compound"] != "UNKNOWN":
                        stint_record["compound"] = stint_data["Compound"]
                    if "New" in stint_data:
                        stint_record["new"] = stint_data["New"] == "true" or stint_data["New"] == True
                    if "TotalLaps" in stint_data:
                        stint_record["total_laps"] = max(stint_record["total_laps"], stint_data["TotalLaps"])
                    if "StartLaps" in stint_data:
                        stint_record["start_lap"] = stint_data["StartLaps"]
        
        # 轉換為列表並排序
        result = {}
        for driver_num, stints_dict in driver_stints.items():
            stints_list = list(stints_dict.values())
            stints_list.sort(key=lambda x: x["stint_number"])
            result[driver_num] = stints_list
        
        return result
    
    def _get_stint_for_lap(self, lap_number: int, stints: List[Dict]) -> Tuple[Optional[Dict], int]:
        """
        根據圈數找到對應的 stint 資訊
        
        Returns:
            (stint_info, stint_lap): stint 資訊和該圈在 stint 中的圈數
        """
        if not stints:
            return None, lap_number
        
        cumulative_laps = 0
        for stint in stints:
            stint_laps = stint.get("total_laps", 0)
            if lap_number <= cumulative_laps + stint_laps:
                stint_lap = lap_number - cumulative_laps
                return stint, stint_lap
            cumulative_laps += stint_laps
        
        # 如果超出已知 stint，使用最後一個 stint
        last_stint = stints[-1]
        return last_stint, lap_number - cumulative_laps + last_stint.get("total_laps", 0)
    
    def predict(self, year: int, race: str, session: str = "R",
                drivers: List[str] = None,
                show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        執行綜合圈速預測
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 場次類型
            drivers: 指定車手列表 (None = 全部)
            show_detailed_output: 是否顯示詳細輸出
        
        Returns:
            預測結果字典
        """
        print("\n" + "=" * 70)
        print("[F57] Combined Laptime Prediction - Fuel + Tire Degradation Model")
        print("=" * 70)
        print(f"[INFO] Year: {year} | Race: {race} | Session: {session}")
        print(f"[MODEL] predicted_time = base_time + fuel_effect + tire_degradation")
        
        # 取得賽道參數
        circuit_name = self._get_circuit_name(race)
        fuel_params = self._get_fuel_params(circuit_name)
        tire_params = self._get_tire_params(circuit_name)
        
        print(f"[TRACK] Circuit: {circuit_name}")
        print(f"[FUEL] Consumption: {fuel_params['fuel_kg_per_lap']} kg/lap, Effect: {fuel_params['fuel_effect_coefficient']} s/kg")
        print(f"[TIRE] Abrasiveness: {tire_params.get('abrasiveness', 'medium')}")
        
        # 尋找數據目錄
        data_path = self._find_livef1_data_path(year, race, session)
        if not data_path:
            error_msg = f"No LiveF1 data found for {year} {race} {session}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "message": error_msg, "data": None}
        
        print(f"[DATA] Found data at: {data_path}")
        
        # 載入數據
        timing_data = self._load_timing_data(data_path)
        timing_app_data = self._load_timing_app_data(data_path)
        
        if not timing_data and not timing_app_data:
            error_msg = "No timing data available"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "message": error_msg, "data": None}
        
        # 提取圈速和 stint 資訊
        driver_laps = self._extract_driver_laps(timing_data)
        driver_stints = self._extract_driver_stints(timing_app_data)
        
        print(f"[INFO] Found {len(driver_laps)} drivers with lap data")
        
        # 計算基準圈速 (使用所有車手的最快圈)
        all_lap_times = []
        for driver_num, laps in driver_laps.items():
            for lap in laps:
                all_lap_times.append(lap["lap_time"])
        
        if not all_lap_times:
            error_msg = "No valid lap times found"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "message": error_msg, "data": None}
        
        # 計算全局基準圈速 (用於參考)
        all_lap_times.sort()
        base_time_index = max(0, int(len(all_lap_times) * 0.10))
        global_base_time = all_lap_times[base_time_index]
        
        print(f"[BASE] Global reference lap time: {global_base_time:.3f}s ({global_base_time//60:.0f}:{global_base_time%60:.3f})")
        print(f"[MODE] Using per-driver personal best as individual base time")
        
        # 進行預測
        print(f"\n[PREDICT] Calculating predictions...")
        
        results = {
            "metadata": {
                "year": year,
                "race": race,
                "session": session,
                "circuit_name": circuit_name,
                "global_base_time": global_base_time,
                "prediction_mode": "per_driver_personal_best",
                "fuel_params": fuel_params,
                "tire_params": {
                    "base_degradation": tire_params.get("base_degradation", {}),
                    "degradation_acceleration": tire_params.get("degradation_acceleration", {}),
                    "abrasiveness": tire_params.get("abrasiveness", "medium")
                },
                "model_formula": "predicted_time = personal_best + fuel_effect + tire_degradation",
                "analysis_timestamp": datetime.now().isoformat(),
                "data_source": "F1 Official Live Timing"
            },
            "drivers": {},
            "statistics": {}
        }
        
        total_predictions = 0
        total_error = 0
        total_error_squared = 0
        all_errors = []
        
        for driver_num, laps in driver_laps.items():
            if drivers and driver_num not in drivers:
                continue
            
            if not laps:
                continue
            
            stints = driver_stints.get(driver_num, [])
            
            # 計算車手個人最快圈作為基準 (排除第一圈和進站圈)
            valid_laps = [l["lap_time"] for l in laps if l["lap_number"] > 1]
            if not valid_laps:
                valid_laps = [l["lap_time"] for l in laps]
            
            # 使用第 10 百分位作為個人基準圈速
            valid_laps.sort()
            personal_base_index = max(0, int(len(valid_laps) * 0.10))
            driver_base_time = valid_laps[personal_base_index]
            
            driver_result = {
                "total_laps": len(laps),
                "stints": len(stints),
                "personal_base_time": round(driver_base_time, 3),
                "predictions": []
            }
            
            for lap in laps:
                lap_number = lap["lap_number"]
                actual_time = lap["lap_time"]
                
                # 找到對應的 stint
                stint_info, stint_lap = self._get_stint_for_lap(lap_number, stints)
                compound = stint_info.get("compound", "MEDIUM") if stint_info else "MEDIUM"
                stint_number = stint_info.get("stint_number", 0) if stint_info else 0
                
                # 使用車手個人最快圈計算預測圈速
                prediction = self._calculate_predicted_laptime(
                    driver_base_time, lap_number, stint_lap, compound,
                    fuel_params, tire_params
                )
                
                predicted_time = prediction["predicted_time"]
                error = actual_time - predicted_time
                
                lap_prediction = {
                    "lap_number": lap_number,
                    "stint_number": stint_number,
                    "stint_lap": stint_lap,
                    "compound": compound,
                    "actual_time": actual_time,
                    "predicted_time": round(predicted_time, 3),
                    "fuel_effect": round(prediction["fuel_effect"], 3),
                    "tire_degradation": round(prediction["tire_degradation"], 3),
                    "net_effect": round(prediction["net_effect"], 3),
                    "error": round(error, 3)
                }
                
                driver_result["predictions"].append(lap_prediction)
                
                total_predictions += 1
                total_error += abs(error)
                total_error_squared += error ** 2
                all_errors.append(error)
            
            # 計算車手統計
            if driver_result["predictions"]:
                driver_errors = [p["error"] for p in driver_result["predictions"]]
                driver_result["statistics"] = {
                    "mean_error": round(sum(driver_errors) / len(driver_errors), 3),
                    "mae": round(sum(abs(e) for e in driver_errors) / len(driver_errors), 3),
                    "rmse": round(math.sqrt(sum(e**2 for e in driver_errors) / len(driver_errors)), 3)
                }
            
            results["drivers"][driver_num] = driver_result
        
        # 計算全局統計
        if total_predictions > 0:
            mae = total_error / total_predictions
            rmse = math.sqrt(total_error_squared / total_predictions)
            mean_error = sum(all_errors) / len(all_errors)
            
            results["statistics"] = {
                "total_drivers": len(results["drivers"]),
                "total_predictions": total_predictions,
                "mean_absolute_error": round(mae, 3),
                "root_mean_squared_error": round(rmse, 3),
                "mean_error": round(mean_error, 3),
                "accuracy_within_0.5s": round(sum(1 for e in all_errors if abs(e) < 0.5) / len(all_errors) * 100, 1),
                "accuracy_within_1.0s": round(sum(1 for e in all_errors if abs(e) < 1.0) / len(all_errors) * 100, 1)
            }
        
        # 顯示結果
        if show_detailed_output:
            self._print_results(results)
        
        print(f"\n[SUCCESS] F57 Combined Laptime Prediction completed")
        print("=" * 70)
        
        return {"success": True, "message": "Combined laptime prediction completed", "data": results}
    
    def _print_results(self, results: Dict[str, Any]):
        """印出分析結果"""
        stats = results.get("statistics", {})
        
        print("\n" + "=" * 70)
        print("Combined Laptime Prediction Results")
        print("=" * 70)
        
        print("\n[ACCURACY STATISTICS]")
        print("-" * 70)
        print(f"  Total Drivers Analyzed: {stats.get('total_drivers', 0)}")
        print(f"  Total Lap Predictions: {stats.get('total_predictions', 0)}")
        print(f"  Mean Absolute Error (MAE): {stats.get('mean_absolute_error', 0):.3f}s")
        print(f"  Root Mean Squared Error (RMSE): {stats.get('root_mean_squared_error', 0):.3f}s")
        print(f"  Mean Error (Bias): {stats.get('mean_error', 0):+.3f}s")
        print(f"  Accuracy within 0.5s: {stats.get('accuracy_within_0.5s', 0):.1f}%")
        print(f"  Accuracy within 1.0s: {stats.get('accuracy_within_1.0s', 0):.1f}%")
        
        print("\n[PER-DRIVER SUMMARY]")
        print("-" * 70)
        print(f"{'Driver':<10} | {'Laps':<6} | {'MAE':<8} | {'RMSE':<8} | {'Bias':<8}")
        print("-" * 70)
        
        for driver_num, driver_data in sorted(results.get("drivers", {}).items(), key=lambda x: x[0]):
            driver_stats = driver_data.get("statistics", {})
            laps = driver_data.get("total_laps", 0)
            mae = driver_stats.get("mae", 0)
            rmse = driver_stats.get("rmse", 0)
            bias = driver_stats.get("mean_error", 0)
            print(f"  {driver_num:<8} | {laps:<6} | {mae:>6.3f}s | {rmse:>6.3f}s | {bias:>+6.3f}s")
        
        print("-" * 70)
    
    def export_results(self, results: Dict[str, Any]) -> str:
        """導出結果到 JSON 檔案"""
        if not results.get("success"):
            return None
        
        data = results.get("data", {})
        metadata = data.get("metadata", {})
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"combined_laptime_{metadata.get('year', 'unknown')}_{metadata.get('race', 'unknown')}_{metadata.get('session', 'R')}_{timestamp}.json"
        
        output_path = self.json_output_path / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[EXPORT] Results saved to: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"[ERROR] Failed to export: {e}")
            return None


def run_combined_laptime_prediction(
    data_loader=None,
    year: int = None,
    race: str = None,
    session: str = "R",
    drivers: List[str] = None,
    show_detailed_output: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    F57 綜合圈速預測的入口函數
    
    Args:
        data_loader: 數據載入器 (可選)
        year: 年份
        race: 賽事名稱
        session: 場次類型
        drivers: 指定車手列表
        show_detailed_output: 是否顯示詳細輸出
    
    Returns:
        分析結果字典
    """
    # 從 data_loader 獲取參數
    if year is None and data_loader:
        year = getattr(data_loader, 'year', None)
    if race is None and data_loader:
        race = getattr(data_loader, 'race_name', None)
    if session is None and data_loader:
        session = getattr(data_loader, 'session_type', 'R')
    
    # 預設值
    if year is None:
        year = datetime.now().year
    if race is None:
        race = "Austrian"
    if session is None:
        session = "R"
    
    # 建立預測器並執行
    predictor = CombinedLaptimePredictor()
    results = predictor.predict(
        year=year,
        race=race,
        session=session,
        drivers=drivers,
        show_detailed_output=show_detailed_output
    )
    
    # 導出結果
    if results.get("success"):
        predictor.export_results(results)
    
    return results


# 測試入口
if __name__ == "__main__":
    result = run_combined_laptime_prediction(
        year=2025,
        race="Austrian",
        session="R",
        show_detailed_output=True
    )
    print(f"\nFinal Result: Success={result.get('success')}")
