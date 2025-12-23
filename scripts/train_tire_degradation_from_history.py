#!/usr/bin/env python3
"""
訓練輪胎衰退模型 - 使用 Cappello & Hoegh 2025 圈速衰退分析法

基於論文的時變線性模型:
    corrected_lap_time = base_time + degradation_rate * tire_age

原始圈速需要校正:
    1. 燃油校正: 每圈燃油減少約 0.055 秒 (油耗約 1.8kg/lap，每 kg 約 0.03s)
    2. 暖胎圈: 前 3 圈忽略 (輪胎未達工作溫度)
    3. 進站圈/出站圈: 忽略 (會包含 pit lane 時間)
    4. Safety Car 圈: 忽略 (無法反映真實速度)

最佳換胎圈數判斷:
    當 累積圈速損失 > 進站時間損失 時應該進站
    即: degradation_rate * age² / 2 > pit_loss_time
    解得: optimal_age = sqrt(2 * pit_loss_time / degradation_rate)

使用方式:
    python scripts/train_tire_degradation_from_history.py
    python scripts/train_tire_degradation_from_history.py --debug-circuit Lusail

輸出:
    更新 config/tire_degradation_database.json
"""

import os
import sys
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

# 添加專案根目錄到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TireDegradationTrainer:
    """
    輪胎衰退訓練器 - 使用 Cappello & Hoegh 2025 圈速衰退分析法
    
    核心原理:
    1. 從 TimingData.json 提取每圈圈速
    2. 從 TyreStintSeries.json 提取輪胎 stint 信息
    3. 對每個 stint 進行燃油校正後的線性回歸
    4. 計算衰退率 (秒/圈)
    5. 根據衰退率計算最佳換胎圈數
    """
    
    def __init__(self):
        self.base_path = project_root
        self.livef1_path = self.base_path / "json" / "LiveF1"
        self.tire_db_path = self.base_path / "config" / "tire_degradation_database.json"
        self.pit_db_path = self.base_path / "config" / "pit_loss_database.json"
        self.fuel_db_path = self.base_path / "config" / "fuel_coefficients_database.json"
        
        # 載入現有資料庫
        self.tire_database = self._load_json(self.tire_db_path)
        self.pit_database = self._load_json(self.pit_db_path)
        self.fuel_database = self._load_json(self.fuel_db_path)
        
        # 賽事名稱到賽道代碼的映射
        self.race_to_circuit = {
            "Italian": "Monza", "Japanese": "Suzuka", "Austrian": "Spielberg",
            "Belgian": "Spa", "Monaco": "Monaco", "British": "Silverstone",
            "Australian": "Melbourne", "Dutch": "Zandvoort", "Hungarian": "Budapest",
            "Singapore": "Singapore", "United_States": "Austin", "Mexico_City": "Mexico",
            "São_Paulo": "Interlagos", "Las_Vegas": "Las_Vegas", "Abu_Dhabi": "Yas_Marina",
            "Qatar": "Lusail", "Spanish": "Barcelona", "Canadian": "Montreal",
            "Miami": "Miami", "Bahrain": "Bahrain", "Saudi_Arabian": "Jeddah",
            "Chinese": "Shanghai", "Emilia_Romagna": "Imola", "Azerbaijan": "Baku"
        }
        
        # 訓練參數
        self.warmup_laps = 2  # 忽略前 2 圈暖胎 (較保守)
        self.fuel_effect_per_lap = 0.055  # 每圈燃油效果 (秒)
        self.min_stint_laps = 6  # 最少需要 6 圈有效數據
        
        # 收集的訓練數據
        self.training_results: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    
    def _load_json(self, path: Path) -> Dict:
        """載入 JSON 檔案"""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[ERROR] 無法載入 {path}: {e}")
        return {}
    
    def _get_pit_loss_time(self, circuit: str) -> float:
        """獲取賽道的進站時間損失"""
        pit_data = self.pit_database.get("circuits", {}).get(circuit, {})
        return pit_data.get("pit_loss_time", 22.0)  # 預設 22 秒
    
    def _get_fuel_effect(self, circuit: str) -> float:
        """獲取賽道的每圈燃油效果"""
        fuel_data = self.fuel_database.get("circuits", {}).get(circuit, {})
        return fuel_data.get("fuel_effect_per_lap", self.fuel_effect_per_lap)
    
    def _extract_lap_times(self, timing_data: Dict) -> Dict[str, Dict[int, float]]:
        """
        從 TimingData.json 提取每圈圈速
        
        Returns:
            {driver_num: {lap_number: lap_time_seconds}}
        """
        driver_laps: Dict[str, Dict[int, float]] = defaultdict(dict)
        driver_current_lap: Dict[str, int] = {}
        
        records = timing_data.get("records", [])
        
        for rec in records:
            lines = rec.get("data", {}).get("Lines", {})
            
            for driver, info in lines.items():
                if not isinstance(info, dict):
                    continue
                
                # 追蹤圈數
                if "NumberOfLaps" in info:
                    driver_current_lap[driver] = info["NumberOfLaps"]
                
                # 提取圈速
                if "LastLapTime" in info:
                    lap_time = info["LastLapTime"]
                    if isinstance(lap_time, dict) and "Value" in lap_time:
                        val = lap_time["Value"]
                        if val and ":" in str(val):
                            try:
                                parts = str(val).split(":")
                                secs = int(parts[0]) * 60 + float(parts[1])
                                lap_num = driver_current_lap.get(driver, 1)
                                driver_laps[driver][lap_num] = secs
                            except (ValueError, IndexError):
                                pass
        
        return dict(driver_laps)
    
    def _extract_stint_info(self, tyre_series_data: Dict) -> Dict[str, List[Dict]]:
        """
        從 TyreStintSeries.json 提取 stint 信息
        
        Returns:
            {driver_num: [
                {"stint_num": 0, "compound": "MEDIUM", "start_lap": 1, "end_lap": 21},
                {"stint_num": 1, "compound": "HARD", "start_lap": 22, "end_lap": 53},
            ]}
        """
        final_stints: Dict[str, Dict[str, Dict]] = defaultdict(dict)
        
        records = tyre_series_data.get("records", [])
        
        for record in records:
            data = record.get("data", {})
            stints_data = data.get("Stints", {})
            
            if not isinstance(stints_data, dict):
                continue
            
            for driver_num, driver_stints in stints_data.items():
                if not isinstance(driver_stints, dict):
                    continue
                
                for stint_idx, stint_info in driver_stints.items():
                    if not isinstance(stint_info, dict):
                        continue
                    
                    # 更新 stint 資訊
                    if stint_idx not in final_stints[driver_num]:
                        final_stints[driver_num][stint_idx] = {}
                    final_stints[driver_num][stint_idx].update(stint_info)
        
        # 轉換為結構化的 stint 列表
        driver_stints: Dict[str, List[Dict]] = defaultdict(list)
        
        for driver_num, stints in final_stints.items():
            sorted_stints = sorted(stints.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
            
            current_lap = 1
            for stint_idx, stint_info in sorted_stints:
                compound = stint_info.get("Compound", "UNKNOWN").upper()
                total_laps = stint_info.get("TotalLaps", 0)
                start_laps = stint_info.get("StartLaps", 0)  # 舊胎已用圈數
                
                if compound in ["SOFT", "MEDIUM", "HARD"] and total_laps > 0:
                    start_lap = current_lap
                    end_lap = current_lap + total_laps - 1
                    
                    driver_stints[driver_num].append({
                        "stint_num": int(stint_idx) if stint_idx.isdigit() else 0,
                        "compound": compound,
                        "start_lap": start_lap,
                        "end_lap": end_lap,
                        "total_laps": total_laps,
                        "tire_start_age": start_laps  # 輪胎開始時的已用圈數
                    })
                    
                    current_lap = end_lap + 1
        
        return dict(driver_stints)
    
    def _extract_race_control_laps(self, race_control_data: Dict) -> set:
        """
        從 RaceControlMessages.json 提取需要忽略的圈數
        (Safety Car, VSC, Red Flag 等)
        
        Returns:
            set of lap numbers to ignore
        """
        ignore_laps = set()
        
        records = race_control_data.get("records", [])
        
        for record in records:
            data = record.get("data", {})
            messages = data.get("Messages", [])
            
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict):
                        flag = msg.get("Flag", "")
                        lap = msg.get("Lap")
                        
                        # Safety Car 或 VSC 期間的圈數應該忽略
                        if flag in ["YELLOW", "SC", "VSC", "RED"] and lap:
                            try:
                                ignore_laps.add(int(lap))
                                # 通常 SC 期間會持續 2-3 圈
                                ignore_laps.add(int(lap) + 1)
                                ignore_laps.add(int(lap) + 2)
                            except (ValueError, TypeError):
                                pass
        
        return ignore_laps
    
    def _calculate_degradation_rate(
        self, 
        lap_times: Dict[int, float], 
        stint_info: Dict,
        total_race_laps: int,
        fuel_effect: float,
        ignore_laps: set
    ) -> Optional[Dict]:
        """
        計算單個 stint 的衰退率
        
        使用 Cappello & Hoegh 2025 方法:
        1. 燃油校正: 每圈燃油減少約 fuel_effect 秒
        2. 線性回歸: corrected_time = base + degradation * tire_age
        
        Args:
            lap_times: {lap_number: lap_time_seconds}
            stint_info: stint 信息 (start_lap, end_lap, compound, etc.)
            total_race_laps: 比賽總圈數
            fuel_effect: 每圈燃油效果
            ignore_laps: 要忽略的圈數 (SC, pit lap 等)
        
        Returns:
            衰退分析結果或 None
        """
        start_lap = stint_info["start_lap"]
        end_lap = stint_info["end_lap"]
        tire_start_age = stint_info.get("tire_start_age", 0)
        
        # 收集有效圈速
        valid_laps = []
        
        for lap_num in range(start_lap, end_lap + 1):
            # 跳過暖胎圈
            tire_age = (lap_num - start_lap) + tire_start_age + 1
            if tire_age <= self.warmup_laps:
                continue
            
            # 跳過進站圈、出站圈
            if lap_num == start_lap or lap_num == end_lap:
                continue
            
            # 跳過 SC/VSC 圈
            if lap_num in ignore_laps:
                continue
            
            # 獲取圈速
            if lap_num not in lap_times:
                continue
            
            lap_time = lap_times[lap_num]
            
            # 基本有效性檢查 (排除異常慢圈)
            if lap_time > 200:  # 超過 200 秒肯定是異常
                continue
            
            # 燃油校正: 隨著比賽進行，燃油減少使車變快
            # 我們要「還原」這個效果，讓圈速反映純輪胎衰退
            # 
            # 相對於 stint 開始時:
            # 第 N 圈已消耗燃油 = (lap_num - start_lap) * fuel_per_lap
            # 這使圈速變快了 fuel_effect * (lap_num - start_lap) 秒
            # 校正: 加回這個「變快」的量
            laps_since_stint_start = lap_num - start_lap
            fuel_correction = fuel_effect * laps_since_stint_start
            
            # 校正後的圈速 = 原始圈速 + 燃油校正 
            # (移除燃油減少帶來的速度提升，還原純輪胎衰退效果)
            corrected_time = lap_time + fuel_correction
            
            valid_laps.append({
                "lap": lap_num,
                "tire_age": tire_age,
                "raw_time": lap_time,
                "corrected_time": corrected_time
            })
        
        # 需要足夠的樣本
        if len(valid_laps) < self.min_stint_laps:
            return None
        
        # 線性回歸: corrected_time = base + degradation * tire_age
        ages = [l["tire_age"] for l in valid_laps]
        times = [l["corrected_time"] for l in valid_laps]
        
        n = len(ages)
        sum_x = sum(ages)
        sum_y = sum(times)
        sum_xy = sum(a * t for a, t in zip(ages, times))
        sum_x2 = sum(a ** 2 for a in ages)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return None
        
        # 斜率 = 衰退率 (秒/圈)
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # 計算 R²
        y_mean = sum_y / n
        ss_tot = sum((t - y_mean) ** 2 for t in times)
        ss_res = sum((t - (intercept + slope * a)) ** 2 for a, t in zip(ages, times))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # 過濾低品質擬合
        # 降低門檻：輪胎衰退變化較小，R² 通常不會很高
        if r_squared < 0.15:  # R² < 0.15 表示擬合很差
            return None
        
        # 過濾負衰退或過小衰退 (理論上輪胎一定會衰退)
        if slope < 0.005:  # 至少每圈衰退 0.005 秒
            return None
        
        # 過濾異常高衰退 (可能是數據問題)
        if slope > 0.5:  # 每圈衰退超過 0.5 秒不合理
            return None
        
        return {
            "degradation_rate": slope,  # 秒/圈
            "base_time": intercept,
            "r_squared": r_squared,
            "sample_size": n,
            "tire_ages": ages,
            "max_tire_age": max(ages),
            "stint_length": end_lap - start_lap + 1
        }
    
    def _calculate_optimal_stint_length(
        self, 
        degradation_rate: float, 
        pit_loss_time: float,
        compound: str
    ) -> int:
        """
        計算最佳換胎圈數
        
        基於 Cappello & Hoegh 2025:
        累積圈速損失 ≈ degradation_rate * age² / 2
        當這個損失超過進站損失時，應該進站
        
        optimal_age = sqrt(2 * pit_loss_time / degradation_rate)
        
        但實際上這個公式給出的是「最晚」換胎時機
        車隊通常會提前 20-30% 進站以保持競爭力
        """
        if degradation_rate <= 0:
            return 25  # 預設值
        
        # 理論最佳換胎圈數
        theoretical_optimal = math.sqrt(2 * pit_loss_time / degradation_rate)
        
        # 考慮輪胎特性調整
        compound_factor = {
            "SOFT": 0.75,    # SOFT 輪胎應更早換
            "MEDIUM": 0.85,  # MEDIUM 適中
            "HARD": 0.95     # HARD 可以跑更久
        }
        
        adjusted_optimal = theoretical_optimal * compound_factor.get(compound, 0.85)
        
        # 限制在合理範圍
        min_stint = {"SOFT": 8, "MEDIUM": 12, "HARD": 15}.get(compound, 10)
        max_stint = {"SOFT": 25, "MEDIUM": 35, "HARD": 45}.get(compound, 35)
        
        return int(max(min_stint, min(adjusted_optimal, max_stint)))
    
    def process_race(self, year: int, race_folder: str) -> Dict[str, Any]:
        """處理單場比賽"""
        race_name = race_folder.replace("_Race", "")
        circuit = self.race_to_circuit.get(race_name, race_name)
        
        data_path = self.livef1_path / str(year) / race_folder
        
        # 載入所需數據
        timing_data = self._load_json(data_path / "TimingData.json")
        tyre_series_data = self._load_json(data_path / "TyreStintSeries.json")
        race_control_data = self._load_json(data_path / "RaceControlMessages.json")
        lap_count_data = self._load_json(data_path / "LapCount.json")
        
        if not timing_data.get("records") or not tyre_series_data.get("records"):
            return {"success": False, "error": "缺少數據"}
        
        # 獲取總圈數
        total_laps = 53  # 預設值
        for record in reversed(lap_count_data.get("records", [])):
            data = record.get("data", {})
            if isinstance(data, dict) and "TotalLaps" in data:
                total_laps = data.get("TotalLaps", 53)
                break
        
        # 提取數據
        driver_lap_times = self._extract_lap_times(timing_data)
        driver_stints = self._extract_stint_info(tyre_series_data)
        ignore_laps = self._extract_race_control_laps(race_control_data)
        
        # 獲取賽道參數
        fuel_effect = self._get_fuel_effect(circuit)
        pit_loss_time = self._get_pit_loss_time(circuit)
        
        # 分析每個車手的每個 stint
        results = {"SOFT": [], "MEDIUM": [], "HARD": []}
        
        for driver_num, stints in driver_stints.items():
            lap_times = driver_lap_times.get(driver_num, {})
            
            if not lap_times:
                continue
            
            for stint in stints:
                compound = stint["compound"]
                
                deg_result = self._calculate_degradation_rate(
                    lap_times, stint, total_laps, fuel_effect, ignore_laps
                )
                
                if deg_result:
                    results[compound].append({
                        "driver": driver_num,
                        "year": year,
                        "race": race_name,
                        "circuit": circuit,
                        "degradation_rate": deg_result["degradation_rate"],
                        "base_time": deg_result["base_time"],
                        "r_squared": deg_result["r_squared"],
                        "sample_size": deg_result["sample_size"],
                        "stint_length": deg_result["stint_length"],
                        "max_tire_age": deg_result["max_tire_age"]
                    })
        
        total_stints = sum(len(results[c]) for c in ["SOFT", "MEDIUM", "HARD"])
        
        return {
            "success": total_stints > 0,
            "circuit": circuit,
            "year": year,
            "race": race_name,
            "total_laps": total_laps,
            "pit_loss_time": pit_loss_time,
            "results": results,
            "total_stints": total_stints
        }
    
    def train_all(self, debug_circuit: str = None):
        """訓練所有可用的歷史數據"""
        print("=" * 70)
        print("輪胎衰退模型訓練器 - Cappello & Hoegh 2025 圈速衰退分析法")
        print("=" * 70)
        print("方法: 燃油校正後的圈速線性回歸分析")
        print("公式: corrected_time = base + degradation_rate * tire_age")
        print("最佳 stint = sqrt(2 * pit_loss_time / degradation_rate)")
        print("=" * 70)
        
        # 收集所有訓練數據
        circuit_data: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        circuit_pit_loss: Dict[str, float] = {}
        
        # 處理 2024 和 2025 年的數據
        for year in [2024, 2025]:
            year_path = self.livef1_path / str(year)
            if not year_path.exists():
                continue
            
            race_folders = [f.name for f in year_path.iterdir() if f.is_dir() and f.name.endswith("_Race")]
            
            print(f"\n[{year}] 處理 {len(race_folders)} 場比賽...")
            
            for race_folder in race_folders:
                result = self.process_race(year, race_folder)
                
                if result.get("success"):
                    circuit = result["circuit"]
                    circuit_pit_loss[circuit] = result.get("pit_loss_time", 22.0)
                    
                    for compound in ["SOFT", "MEDIUM", "HARD"]:
                        stints = result["results"].get(compound, [])
                        circuit_data[circuit][compound].extend(stints)
                    
                    print(f"  ✓ {race_folder}: {circuit} - {result['total_stints']} 有效 stints")
                else:
                    print(f"  ✗ {race_folder}: {result.get('error', '未知錯誤')}")
        
        # 計算各賽道各輪胎的衰退率和最佳 stint
        print("\n" + "=" * 70)
        print("計算各賽道輪胎衰退率和最佳換胎圈數...")
        print("=" * 70)
        
        updated_circuits = {}
        
        for circuit, compounds in circuit_data.items():
            pit_loss_time = circuit_pit_loss.get(circuit, 22.0)
            
            circuit_stats = {
                "degradation_rate": {},
                "optimal_stint_length": {},
                "sample_sizes": {},
                "avg_r_squared": {}
            }
            
            if debug_circuit and circuit != debug_circuit:
                continue
            
            print(f"\n[{circuit}] (pit loss: {pit_loss_time:.1f}s)")
            
            for compound in ["SOFT", "MEDIUM", "HARD"]:
                stints = compounds.get(compound, [])
                
                if len(stints) >= 3:
                    # 計算平均衰退率 (加權平均，樣本數越多權重越高)
                    total_weight = sum(s["sample_size"] for s in stints)
                    avg_deg_rate = sum(s["degradation_rate"] * s["sample_size"] for s in stints) / total_weight
                    avg_r_squared = sum(s["r_squared"] * s["sample_size"] for s in stints) / total_weight
                    
                    # 計算最佳換胎圈數
                    optimal = self._calculate_optimal_stint_length(avg_deg_rate, pit_loss_time, compound)
                    
                    circuit_stats["degradation_rate"][compound] = round(avg_deg_rate, 4)
                    circuit_stats["optimal_stint_length"][compound] = optimal
                    circuit_stats["sample_sizes"][compound] = len(stints)
                    circuit_stats["avg_r_squared"][compound] = round(avg_r_squared, 3)
                    
                    print(f"  {compound}: deg={avg_deg_rate:.4f} s/lap, optimal={optimal} laps (R2={avg_r_squared:.3f}, n={len(stints)})")
                    
                    if debug_circuit:
                        print(f"    詳細 stints:")
                        for s in stints[:5]:
                            print(f"      {s['year']} {s['race']}: deg={s['degradation_rate']:.4f}, R2={s['r_squared']:.3f}, len={s['stint_length']}")
                else:
                    print(f"  {compound}: 樣本不足 ({len(stints)} < 3)")
            
            if circuit_stats["optimal_stint_length"]:
                updated_circuits[circuit] = circuit_stats
        
        # 更新資料庫
        print("\n" + "=" * 70)
        print("更新資料庫...")
        print("=" * 70)
        
        circuits_db = self.tire_database.get("circuits", {})
        updated_count = 0
        
        for circuit, stats in updated_circuits.items():
            if circuit in circuits_db:
                # 更新衰退率
                if "base_degradation" not in circuits_db[circuit]:
                    circuits_db[circuit]["base_degradation"] = {}
                
                for compound in ["SOFT", "MEDIUM", "HARD"]:
                    if compound in stats["degradation_rate"]:
                        # 更新 base_degradation (衰退率)
                        circuits_db[circuit]["base_degradation"][compound] = stats["degradation_rate"][compound]
                        # 更新 optimal_stint_length
                        circuits_db[circuit]["optimal_stint_length"][compound] = stats["optimal_stint_length"][compound]
                
                circuits_db[circuit]["trained_from_data"] = True
                circuits_db[circuit]["training_method"] = "Cappello & Hoegh 2025 lap time degradation analysis"
                circuits_db[circuit]["training_samples"] = stats["sample_sizes"]
                circuits_db[circuit]["training_r_squared"] = stats["avg_r_squared"]
                circuits_db[circuit]["last_trained"] = datetime.now().isoformat()
                
                soft_opt = stats["optimal_stint_length"].get("SOFT", "?")
                med_opt = stats["optimal_stint_length"].get("MEDIUM", "?")
                hard_opt = stats["optimal_stint_length"].get("HARD", "?")
                print(f"  ✓ 更新 {circuit}: SOFT={soft_opt}, MEDIUM={med_opt}, HARD={hard_opt}")
                updated_count += 1
            else:
                print(f"  ✗ 跳過 {circuit} (不在資料庫中)")
        
        # 更新 metadata
        self.tire_database["_metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self.tire_database["_metadata"]["training_method"] = "Cappello & Hoegh 2025 lap time degradation analysis"
        total_stints = sum(
            len(stints) 
            for compounds in circuit_data.values() 
            for stints in compounds.values()
        )
        self.tire_database["_metadata"]["sources"] = [
            "Cappello & Hoegh 2025 - Tire degradation analysis",
            f"Fuel-corrected lap time linear regression",
            f"Total analyzed stints: {total_stints}"
        ]
        
        # 保存
        with open(self.tire_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.tire_database, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SUCCESS] 資料庫已更新: {self.tire_db_path}")
        print(f"[INFO] 更新了 {updated_count} 個賽道的數據")
        print(f"[INFO] 分析了 {total_stints} 個 stints")
        
        return updated_circuits


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="輪胎衰退模型訓練器")
    parser.add_argument("--debug-circuit", type=str, help="只分析指定賽道並顯示詳細信息")
    args = parser.parse_args()
    
    trainer = TireDegradationTrainer()
    trainer.train_all(debug_circuit=args.debug_circuit)


if __name__ == "__main__":
    main()
