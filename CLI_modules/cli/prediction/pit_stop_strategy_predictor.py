#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F58 - 進站策略預測器 (Pit Stop Strategy Predictor)

功能:
    58.1 進站時機預測 - 預測每位車手的最佳進站圈數
    58.2 策略組合優化 - 比較 1-stop / 2-stop / 3-stop 策略
    58.3 Undercut/Overcut 警告 - 實時偵測對手策略威脅

原理:
    基於 F55 (燃油校正) + F56 (輪胎衰退) 進行策略分析
    
    進站決策點: 當累計輪胎衰退損失 > 進站時間損失時，應該進站
    
    crossover_lap 計算:
    - 累計衰退 = base_rate * n + 0.5 * accel * n^2
    - 當累計衰退 = pit_loss 時，求解 n

數據來源:
    - F56: 輪胎衰退分析結果
    - config/tire_degradation_database.json
    - config/pit_loss_database.json
    - config/fuel_coefficients_database.json
    
輸出:
    - 每位車手的最佳進站窗口
    - 策略組合比較 (1-stop vs 2-stop)
    - Undercut/Overcut 威脅評估

學術參考:
    - Sasikumar et al. 2025: Data-driven pit stop decision support using Bi-LSTM (F1-score: 0.81)
    - Thomas et al. 2025: Explainable RL for F1 Race Strategy (Mercedes)
    - Cappello & Hoegh 2025: A State-Space Approach to Modeling Tire Degradation

版本: 1.0.0
作者: F1 Analysis Team
日期: 2025-12-04
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class PitStopStrategyPredictor:
    """F58 進站策略預測器 - 整合輪胎衰退與策略分析"""
    
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
        self.tire_db_path = self.base_path / "config" / "tire_degradation_database.json"
        self.pit_loss_db_path = self.base_path / "config" / "pit_loss_database.json"
        self.fuel_db_path = self.base_path / "config" / "fuel_coefficients_database.json"
        
        # 載入資料庫
        self.tire_database = self._load_json_database(self.tire_db_path)
        self.pit_loss_database = self._load_json_database(self.pit_loss_db_path)
        self.fuel_database = self._load_json_database(self.fuel_db_path)
        
        # 預設參數
        self.default_tire_params = {
            "base_degradation": {"SOFT": 0.065, "MEDIUM": 0.045, "HARD": 0.030},
            "degradation_acceleration": {"SOFT": 0.0025, "MEDIUM": 0.0015, "HARD": 0.0009},
            "optimal_stint_length": {"SOFT": 20, "MEDIUM": 30, "HARD": 45}
        }
        
        self.default_pit_loss = 22.0  # 預設進站損失 (秒)
        
        # Undercut 窗口參數
        self.undercut_window = (1.5, 3.5)  # 秒
        self.undercut_tire_age_threshold = 5  # 圈

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
        # 從 pit_loss_database 的 aliases 進行轉換
        aliases = self.pit_loss_database.get("aliases", {})
        if race in aliases:
            return aliases[race]
        
        # 從 tire_database 的 aliases 進行轉換
        tire_aliases = self.tire_database.get("aliases", {})
        if race in tire_aliases:
            return tire_aliases[race]
        
        return race
    
    def _get_pit_loss(self, circuit: str, track_status: str = "green_flag") -> float:
        """取得特定賽道的進站損失時間"""
        circuit_name = self._get_circuit_name(circuit)
        circuits = self.pit_loss_database.get("circuits", {})
        
        if circuit_name in circuits:
            pit_times = circuits[circuit_name].get("pit_loss_times", {})
            return pit_times.get(track_status, self.default_pit_loss)
        
        # 嘗試預設值
        default = self.pit_loss_database.get("default", {})
        default_times = default.get("pit_loss_times", {})
        return default_times.get(track_status, self.default_pit_loss)
    
    def _get_tire_params(self, circuit: str) -> Dict[str, Any]:
        """取得特定賽道的輪胎參數"""
        circuit_name = self._get_circuit_name(circuit)
        circuits = self.tire_database.get("circuits", {})
        
        if circuit_name in circuits:
            return circuits[circuit_name]
        
        return self.default_tire_params
    
    def _get_total_laps(self, circuit: str) -> int:
        """取得賽道總圈數"""
        circuit_name = self._get_circuit_name(circuit)
        circuits = self.tire_database.get("circuits", {})
        
        if circuit_name in circuits:
            return circuits[circuit_name].get("typical_race_laps", 53)
        
        return 53  # 預設值
    
    # =========================================================================
    # 58.1 進站時機預測
    # =========================================================================
    
    def calculate_crossover_lap(self, circuit: str, compound: str, 
                                 track_status: str = "green_flag") -> int:
        """
        計算輪胎最佳進站圈數
        
        原理 (修正版):
            使用資料庫中的 optimal_stint_length 作為主要依據，
            並根據進站損失進行微調。
            
            實務上的進站決策考量:
            1. 輪胎性能懸崖 (cliff) - 當輪胎衰退過多，圈速急劇下降
            2. 策略優勢 - 在對手進站窗口內或外進站
            3. 累計損失 vs 進站損失 - 經濟學權衡
            
        Args:
            circuit: 賽道名稱
            compound: 輪胎配方 (SOFT/MEDIUM/HARD)
            track_status: 賽道狀態 (green_flag/safety_car/virtual_safety_car)
            
        Returns:
            crossover_lap: 最佳進站圈數
        """
        tire_params = self._get_tire_params(circuit)
        
        # 主要依據: 資料庫中的最佳 stint 長度
        optimal_stint = tire_params.get("optimal_stint_length", self.default_tire_params["optimal_stint_length"])
        base_optimal = optimal_stint.get(compound, 25)
        
        # 根據賽道磨耗等級調整
        abrasiveness_multiplier = tire_params.get("abrasiveness_multiplier", 1.0)
        adjusted_optimal = int(base_optimal / abrasiveness_multiplier)
        
        # Safety Car 期間可以適當延長 stint
        if track_status == "safety_car":
            adjusted_optimal = int(adjusted_optimal * 1.15)
        elif track_status == "virtual_safety_car":
            adjusted_optimal = int(adjusted_optimal * 1.10)
        
        return max(8, adjusted_optimal)  # 至少 8 圈
    
    def predict_pit_window(self, circuit: str, compound: str, 
                           current_lap: int = 1,
                           track_status: str = "green_flag") -> Dict[str, Any]:
        """
        預測單一 stint 的最佳進站窗口
        
        Args:
            circuit: 賽道名稱
            compound: 當前輪胎配方
            current_lap: 當前已使用圈數
            track_status: 賽道狀態
            
        Returns:
            pit_window: 包含開始、結束、最佳圈的進站窗口
        """
        crossover = self.calculate_crossover_lap(circuit, compound, track_status)
        
        # 進站窗口 = crossover ± 調整
        window_early = max(1, crossover - 3)
        window_late = crossover + 2
        
        # 計算信心度
        confidence = 0.85 if track_status == "green_flag" else 0.70
        
        # 建議下一個輪胎
        compound_order = ["SOFT", "MEDIUM", "HARD"]
        current_idx = compound_order.index(compound) if compound in compound_order else 1
        if current_idx < 2:
            recommended_next = compound_order[current_idx + 1]
        else:
            recommended_next = "MEDIUM"
        
        return {
            "current_compound": compound,
            "crossover_lap": crossover,
            "optimal_pit_window": {
                "start_lap": window_early,
                "end_lap": window_late,
                "optimal_lap": crossover
            },
            "recommended_next_compound": recommended_next,
            "confidence": confidence,
            "reason": f"基於 {circuit} 賽道特性和 {compound} 輪胎的最佳 stint 長度 ({crossover} 圈)"
        }
    
    def predict_all_drivers_pit_windows(self, race_data: Dict[str, Any], 
                                         circuit: str) -> Dict[str, Any]:
        """
        預測所有車手的進站窗口
        
        Args:
            race_data: 包含所有車手輪胎狀態的比賽數據
            circuit: 賽道名稱
            
        Returns:
            all_pit_windows: 所有車手的進站窗口預測
        """
        pit_windows = {}
        
        drivers = race_data.get("drivers", {})
        for driver_code, driver_data in drivers.items():
            compound = driver_data.get("compound", "MEDIUM")
            tire_age = driver_data.get("tire_age", 0)
            stint = driver_data.get("stint", 1)
            
            window = self.predict_pit_window(circuit, compound)
            window["tire_age"] = tire_age
            window["current_stint"] = stint
            
            pit_windows[driver_code] = window
        
        return {"pit_window_predictions": pit_windows}
    
    # =========================================================================
    # 58.2 策略組合優化
    # =========================================================================
    
    def _calculate_stint_time(self, circuit: str, compound: str, 
                               stint_laps: int, start_fuel_kg: float,
                               base_lap_time: float = 90.0) -> float:
        """
        計算單一 stint 的總時間
        
        Args:
            circuit: 賽道名稱
            compound: 輪胎配方
            stint_laps: stint 圈數
            start_fuel_kg: 開始時的燃油量
            base_lap_time: 基準圈速
            
        Returns:
            total_time: stint 總時間 (秒)
        """
        tire_params = self._get_tire_params(circuit)
        base_deg = tire_params.get("base_degradation", self.default_tire_params["base_degradation"])
        accel = tire_params.get("degradation_acceleration", self.default_tire_params["degradation_acceleration"])
        
        base = base_deg.get(compound, 0.045)
        acceleration = accel.get(compound, 0.0015)
        
        # 輪胎配方速度優勢
        compound_advantage = {
            "SOFT": -0.5,
            "MEDIUM": -0.25,
            "HARD": 0.0
        }
        
        # 燃油效應
        fuel_effect_per_lap = 0.030  # 秒/公斤
        fuel_consumption_per_lap = 1.75  # 公斤/圈
        
        total_time = 0
        current_fuel = start_fuel_kg
        
        for lap in range(1, stint_laps + 1):
            # 輪胎衰退
            tire_deg = base * lap + 0.5 * acceleration * lap**2
            
            # 燃油效應
            fuel_effect = (start_fuel_kg - current_fuel) * fuel_effect_per_lap
            current_fuel -= fuel_consumption_per_lap
            
            # 單圈時間
            lap_time = base_lap_time + compound_advantage.get(compound, 0) + tire_deg - fuel_effect
            total_time += lap_time
        
        return total_time
    
    def compare_strategies(self, circuit: str, total_laps: int = None,
                            start_fuel_kg: float = 110.0,
                            base_lap_time: float = 90.0) -> Dict[str, Any]:
        """
        比較不同進站策略的預測總時間
        
        Args:
            circuit: 賽道名稱
            total_laps: 總圈數 (如果為 None，從資料庫獲取)
            start_fuel_kg: 起步燃油量
            base_lap_time: 基準圈速
            
        Returns:
            strategy_comparison: 策略比較結果
        """
        if total_laps is None:
            total_laps = self._get_total_laps(circuit)
        
        pit_loss = self._get_pit_loss(circuit)
        
        # 定義策略組合
        strategies = [
            # 1-stop 策略
            {
                "name": "1-Stop (M→H)",
                "stops": 1,
                "stints": [
                    {"compound": "MEDIUM", "laps": int(total_laps * 0.45)},
                    {"compound": "HARD", "laps": int(total_laps * 0.55)}
                ]
            },
            {
                "name": "1-Stop (S→M)",
                "stops": 1,
                "stints": [
                    {"compound": "SOFT", "laps": int(total_laps * 0.35)},
                    {"compound": "MEDIUM", "laps": int(total_laps * 0.65)}
                ]
            },
            {
                "name": "1-Stop (S→H)",
                "stops": 1,
                "stints": [
                    {"compound": "SOFT", "laps": int(total_laps * 0.30)},
                    {"compound": "HARD", "laps": int(total_laps * 0.70)}
                ]
            },
            # 2-stop 策略
            {
                "name": "2-Stop (S→M→S)",
                "stops": 2,
                "stints": [
                    {"compound": "SOFT", "laps": int(total_laps * 0.28)},
                    {"compound": "MEDIUM", "laps": int(total_laps * 0.40)},
                    {"compound": "SOFT", "laps": int(total_laps * 0.32)}
                ]
            },
            {
                "name": "2-Stop (M→H→M)",
                "stops": 2,
                "stints": [
                    {"compound": "MEDIUM", "laps": int(total_laps * 0.30)},
                    {"compound": "HARD", "laps": int(total_laps * 0.38)},
                    {"compound": "MEDIUM", "laps": int(total_laps * 0.32)}
                ]
            },
        ]
        
        results = []
        
        for strategy in strategies:
            total_time = 0
            remaining_fuel = start_fuel_kg
            fuel_per_lap = 1.75
            
            for i, stint in enumerate(strategy["stints"]):
                stint_time = self._calculate_stint_time(
                    circuit, 
                    stint["compound"], 
                    stint["laps"],
                    remaining_fuel,
                    base_lap_time
                )
                total_time += stint_time
                remaining_fuel -= stint["laps"] * fuel_per_lap
                
                # 加上進站時間 (最後一個 stint 除外)
                if i < len(strategy["stints"]) - 1:
                    total_time += pit_loss
            
            results.append({
                "strategy_name": strategy["name"],
                "stops": strategy["stops"],
                "stints": strategy["stints"],
                "predicted_total_time_seconds": total_time,
                "predicted_total_time_formatted": self._format_time(total_time),
                "pit_loss_total": pit_loss * strategy["stops"]
            })
        
        # 排序找最佳
        results.sort(key=lambda x: x["predicted_total_time_seconds"])
        
        # 計算與最佳策略的差距
        best_time = results[0]["predicted_total_time_seconds"]
        for result in results:
            result["gap_to_optimal"] = result["predicted_total_time_seconds"] - best_time
            result["gap_to_optimal_formatted"] = f"+{result['gap_to_optimal']:.3f}s"
        
        return {
            "circuit": circuit,
            "total_laps": total_laps,
            "pit_loss_seconds": pit_loss,
            "recommended_strategy": results[0],
            "all_strategies": results,
            "analysis_notes": self._generate_strategy_notes(results, circuit)
        }
    
    def _format_time(self, seconds: float) -> str:
        """將秒數轉換為 H:MM:SS.mmm 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:06.3f}"
    
    def _generate_strategy_notes(self, results: List[Dict], circuit: str) -> str:
        """產生策略分析備註"""
        best = results[0]
        if best["stops"] == 1:
            return f"1-stop 策略在 {circuit} 較有優勢，建議使用 {best['strategy_name']}"
        else:
            gap = results[0]["predicted_total_time_seconds"] - results[1]["predicted_total_time_seconds"] if len(results) > 1 else 0
            if abs(gap) < 5:
                return f"1-stop 和 2-stop 策略差距很小 ({abs(gap):.1f}s)，需視比賽情況調整"
            return f"2-stop 策略在 {circuit} 較有優勢，但需注意賽道位置損失"
    
    # =========================================================================
    # 58.3 Undercut/Overcut 警告
    # =========================================================================
    
    def check_undercut_threat(self, driver: str, rival: str, 
                               gap_seconds: float,
                               driver_tire_age: int,
                               rival_tire_age: int,
                               circuit: str) -> Dict[str, Any]:
        """
        檢測 undercut 威脅
        
        Undercut 條件:
        1. 對手輪胎較舊 (更多衰退)
        2. 差距在 undercut 窗口內 (通常 1.5-3.5 秒)
        3. 對手尚未進站
        
        Args:
            driver: 車手代碼
            rival: 對手代碼
            gap_seconds: 車手與對手的差距 (正數表示在前)
            driver_tire_age: 車手輪胎圈數
            rival_tire_age: 對手輪胎圈數
            circuit: 賽道名稱
            
        Returns:
            threat_assessment: 威脅評估結果
        """
        tire_age_diff = rival_tire_age - driver_tire_age
        abs_gap = abs(gap_seconds)
        
        # 判斷威脅等級
        threat_level = "LOW"
        recommendation = "維持當前策略"
        
        # 車手在前方
        if gap_seconds > 0:
            # 對手可能 undercut
            if self.undercut_window[0] <= abs_gap <= self.undercut_window[1]:
                if tire_age_diff > self.undercut_tire_age_threshold:
                    threat_level = "HIGH"
                    recommendation = f"警告: {rival} 可能在下 1-2 圈執行 undercut，考慮提前進站"
                elif tire_age_diff > 2:
                    threat_level = "MEDIUM"
                    recommendation = f"注意: {rival} 有 undercut 潛力，監控其動態"
            elif abs_gap < self.undercut_window[0]:
                threat_level = "MEDIUM"
                recommendation = f"{rival} 差距過近，undercut 效果有限但仍需注意"
        else:
            # 車手在後方，可以考慮 undercut
            if self.undercut_window[0] <= abs_gap <= self.undercut_window[1]:
                if driver_tire_age > rival_tire_age + self.undercut_tire_age_threshold:
                    threat_level = "OPPORTUNITY"
                    recommendation = f"機會: 可考慮 undercut {rival}，輪胎優勢 {tire_age_diff} 圈"
        
        return {
            "driver": driver,
            "rival": rival,
            "alert_type": "UNDERCUT_THREAT" if gap_seconds > 0 else "UNDERCUT_OPPORTUNITY",
            "threat_level": threat_level,
            "gap_seconds": gap_seconds,
            "tire_age_difference": tire_age_diff,
            "undercut_window": list(self.undercut_window),
            "recommendation": recommendation,
            "analysis": {
                "is_in_undercut_window": self.undercut_window[0] <= abs_gap <= self.undercut_window[1],
                "tire_advantage": tire_age_diff > 0,
                "estimated_undercut_gain": self._estimate_undercut_gain(tire_age_diff, circuit)
            }
        }
    
    def _estimate_undercut_gain(self, tire_age_diff: int, circuit: str) -> float:
        """估計 undercut 可能帶來的時間優勢"""
        tire_params = self._get_tire_params(circuit)
        base_deg = tire_params.get("base_degradation", self.default_tire_params["base_degradation"])
        
        # 使用 MEDIUM 作為估計基準
        deg_per_lap = base_deg.get("MEDIUM", 0.045)
        
        # 新胎 out-lap 優勢約 1.5-2.5 秒
        out_lap_advantage = 2.0
        
        # 估計 undercut 增益 = out-lap 優勢 + 輪胎新舊差異
        estimated_gain = out_lap_advantage + (tire_age_diff * deg_per_lap * 0.5)
        
        return round(estimated_gain, 2)
    
    def analyze_tactical_situation(self, race_state: Dict[str, Any], 
                                    target_driver: str,
                                    circuit: str) -> List[Dict[str, Any]]:
        """
        分析特定車手的戰術情況
        
        Args:
            race_state: 當前比賽狀態
            target_driver: 目標車手
            circuit: 賽道名稱
            
        Returns:
            tactical_alerts: 戰術警告列表
        """
        alerts = []
        
        drivers = race_state.get("drivers", {})
        gaps = race_state.get("gaps", {})
        
        if target_driver not in drivers:
            return alerts
        
        target_data = drivers[target_driver]
        target_tire_age = target_data.get("tire_age", 0)
        
        # 檢查與前後車的 undercut 關係
        target_gaps = gaps.get(target_driver, {})
        
        for rival, gap in target_gaps.items():
            if rival == target_driver:
                continue
            
            rival_data = drivers.get(rival, {})
            rival_tire_age = rival_data.get("tire_age", 0)
            
            threat = self.check_undercut_threat(
                target_driver, rival, gap, 
                target_tire_age, rival_tire_age, 
                circuit
            )
            
            if threat["threat_level"] in ["HIGH", "MEDIUM", "OPPORTUNITY"]:
                alerts.append(threat)
        
        # 按威脅等級排序
        priority_order = {"HIGH": 0, "OPPORTUNITY": 1, "MEDIUM": 2, "LOW": 3}
        alerts.sort(key=lambda x: priority_order.get(x["threat_level"], 99))
        
        return alerts
    
    # =========================================================================
    # 主執行函數
    # =========================================================================
    
    def run_analysis(self, year: int, race: str, session: str = "R",
                      drivers: List[str] = None,
                      show_detailed_output: bool = True) -> Dict[str, Any]:
        """
        執行完整的進站策略分析
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            drivers: 特定車手列表 (可選)
            show_detailed_output: 是否顯示詳細輸出
            
        Returns:
            analysis_result: 完整分析結果
        """
        circuit = self._get_circuit_name(race)
        total_laps = self._get_total_laps(circuit)
        pit_loss = self._get_pit_loss(circuit)
        
        if show_detailed_output:
            print(f"\n{'='*60}")
            print(f"F58 進站策略預測器 - {year} {race} GP ({session})")
            print(f"{'='*60}")
            print(f"賽道: {circuit} | 總圈數: {total_laps} | 進站損失: {pit_loss:.1f}s")
            print(f"{'='*60}\n")
        
        result = {
            "metadata": {
                "function_id": "58",
                "function_name": "Pit Stop Strategy Predictor",
                "year": year,
                "race": race,
                "circuit": circuit,
                "session": session,
                "generated_at": datetime.now().isoformat(),
                "total_laps": total_laps,
                "pit_loss_seconds": pit_loss
            },
            "pit_window_predictions": {},
            "strategy_comparison": {},
            "tactical_alerts": []
        }
        
        # 58.1 進站時機預測
        compounds = ["SOFT", "MEDIUM", "HARD"]
        for compound in compounds:
            window = self.predict_pit_window(circuit, compound)
            result["pit_window_predictions"][compound] = window
            
            if show_detailed_output:
                print(f"[{compound}] 最佳進站圈: {window['crossover_lap']} "
                      f"(窗口: {window['optimal_pit_window']['start_lap']}-{window['optimal_pit_window']['end_lap']})")
        
        if show_detailed_output:
            print()
        
        # 58.2 策略比較
        strategy_comparison = self.compare_strategies(circuit, total_laps)
        result["strategy_comparison"] = strategy_comparison
        
        if show_detailed_output:
            print("\n策略比較:")
            print("-" * 50)
            for i, strat in enumerate(strategy_comparison["all_strategies"]):
                marker = "[推薦]" if i == 0 else ""
                print(f"  {marker} {strat['strategy_name']}: {strat['predicted_total_time_formatted']} "
                      f"({strat['gap_to_optimal_formatted']})")
        
        # 儲存 JSON
        self._save_result_json(result, year, race, session)
        
        return result
    
    def _save_result_json(self, result: Dict[str, Any], 
                           year: int, race: str, session: str):
        """儲存分析結果為 JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pit_stop_strategy_{year}_{race}_{session}_{timestamp}.json"
            output_path = self.json_output_path / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n[SUCCESS] 分析結果已儲存: {output_path}")
        except Exception as e:
            print(f"[WARNING] 無法儲存 JSON: {e}")


def run_pit_stop_strategy_prediction(
    data_loader=None,
    year: int = None,
    race: str = None,
    session: str = "R",
    drivers: List[str] = None,
    show_detailed_output: bool = True
) -> Dict[str, Any]:
    """
    F58 進站策略預測的入口函數
    
    Args:
        data_loader: 數據載入器 (可選)
        year: 年份
        race: 賽事名稱
        session: 會話類型
        drivers: 車手列表 (可選)
        show_detailed_output: 是否顯示詳細輸出
        
    Returns:
        analysis_result: 分析結果
    """
    # 如果沒有提供年份/賽事，嘗試從 data_loader 獲取
    if year is None and data_loader and hasattr(data_loader, "year"):
        year = data_loader.year
    if race is None and data_loader and hasattr(data_loader, "race_name"):
        race = data_loader.race_name
    if session == "R" and data_loader and hasattr(data_loader, "session_type"):
        session = data_loader.session_type
    
    # 預設值
    if year is None:
        year = datetime.now().year
    if race is None:
        race = "Austrian"
    
    predictor = PitStopStrategyPredictor()
    
    return predictor.run_analysis(
        year=year,
        race=race,
        session=session,
        drivers=drivers,
        show_detailed_output=show_detailed_output
    )


# 命令行測試
if __name__ == "__main__":
    import sys
    
    year = 2025
    race = "Japan"
    session = "R"
    
    if len(sys.argv) > 1:
        race = sys.argv[1]
    if len(sys.argv) > 2:
        year = int(sys.argv[2])
    
    result = run_pit_stop_strategy_prediction(
        year=year,
        race=race,
        session=session,
        show_detailed_output=True
    )
    
    print("\n" + "=" * 60)
    print("分析完成!")
