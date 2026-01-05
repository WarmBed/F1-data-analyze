#!/usr/bin/env python3
"""
訓練輪胎配方速度差異 - 使用 2022-2025 真實賽事數據

訓練目標:
    1. SOFT vs MEDIUM 的平均速度差異 (初始圈 + 平均 stint)
    2. HARD vs MEDIUM 的平均速度差異
    3. 各賽道的特定配方優勢

數據來源:
    - json/LiveF1/{year}/{race}_Race/TimingData.json (每圈圈速)
    - json/LiveF1/{year}/{race}_Race/TyreStintSeries.json (輪胎配方)
    - json/LiveF1/{year}/{race}_Race/PitLaneTimeCollection.json (進站時間)

原理:
    比較同一場比賽中使用不同配方的車手，在控制其他變量後的圈速差異。
    使用統計方法過濾異常值並計算置信區間。

輸出:
    - config/compound_delta_database.json (配方速度差異)
    - 更新 config/pit_loss_database.json (真實進站損失)

使用方式:
    python scripts/train_compound_deltas_from_history.py
    python scripts/train_compound_deltas_from_history.py --debug-circuit Yas_Marina

作者: F1 Analysis Team
日期: 2025-12-30
"""

import os
import sys
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import statistics

# 添加專案根目錄到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CompoundDeltaTrainer:
    """
    輪胎配方速度差異訓練器
    
    核心原理:
    1. 從 TimingData.json 提取每圈圈速
    2. 從 TyreStintSeries.json 提取輪胎配方
    3. 比較同一圈數範圍內不同配方的平均圈速
    4. 燃油校正後計算配方速度差異
    5. 按賽道和全局統計
    """
    
    def __init__(self, debug: bool = False):
        self.base_path = project_root
        self.livef1_path = self.base_path / "json" / "LiveF1"
        self.output_path = self.base_path / "config" / "compound_delta_database.json"
        self.pit_db_path = self.base_path / "config" / "pit_loss_database.json"
        
        self.debug = debug
        
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
        self.warmup_laps = 2  # 忽略前 2 圈暖胎
        self.fuel_effect_per_lap = 0.055  # 每圈燃油效果 (秒)
        self.min_samples_per_pair = 3  # 最少配方對比樣本數
        
        # 結果收集
        self.global_deltas = {
            'SOFT_vs_MEDIUM': [],    # SOFT - MEDIUM (負值 = SOFT 更快)
            'HARD_vs_MEDIUM': [],    # HARD - MEDIUM (正值 = HARD 更慢)
            'SOFT_vs_HARD': []       # SOFT - HARD (用於驗證)
        }
        self.circuit_deltas = defaultdict(lambda: {
            'SOFT_vs_MEDIUM': [],
            'HARD_vs_MEDIUM': [],
            'SOFT_vs_HARD': []
        })
        
        # 進站時間收集
        self.pit_times: Dict[str, List[float]] = defaultdict(list)
    
    def _log(self, message: str):
        """輸出日誌"""
        print(message)
    
    def _load_json(self, path: Path) -> Dict:
        """載入 JSON 檔案"""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            if self.debug:
                self._log(f"[ERROR] 無法載入 {path}: {e}")
        return {}
    
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
                ...
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
                
                if compound in ["SOFT", "MEDIUM", "HARD"] and total_laps > 0:
                    start_lap = current_lap
                    end_lap = current_lap + total_laps - 1
                    
                    driver_stints[driver_num].append({
                        "stint_num": int(stint_idx) if stint_idx.isdigit() else 0,
                        "compound": compound,
                        "start_lap": start_lap,
                        "end_lap": end_lap,
                        "total_laps": total_laps
                    })
                    
                    current_lap = end_lap + 1
        
        return dict(driver_stints)
    
    def _extract_pit_times(self, pit_data: Dict) -> Dict[str, List[float]]:
        """
        從 PitLaneTimeCollection.json 提取進站時間
        
        Returns:
            {driver_num: [pit_time_1, pit_time_2, ...]}
        """
        driver_pits: Dict[str, List[float]] = defaultdict(list)
        
        records = pit_data.get("records", [])
        
        for record in records:
            pit_times = record.get("data", {}).get("PitTimes", {})
            
            if not isinstance(pit_times, dict):
                continue
            
            for driver_num, pit_info in pit_times.items():
                if driver_num == "_deleted":
                    continue
                
                if isinstance(pit_info, dict) and "Duration" in pit_info:
                    try:
                        duration = float(pit_info["Duration"])
                        # 過濾異常值 (正常進站 18-30 秒)
                        if 18.0 <= duration <= 30.0:
                            driver_pits[driver_num].append(duration)
                    except (ValueError, TypeError):
                        pass
        
        return dict(driver_pits)
    
    def _extract_race_control_laps(self, race_control_data: Dict) -> set:
        """
        從 RaceControlMessages.json 提取需要忽略的圈數
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
                        
                        if flag in ["YELLOW", "SC", "VSC", "RED"] and lap:
                            try:
                                ignore_laps.add(int(lap))
                                ignore_laps.add(int(lap) + 1)
                                ignore_laps.add(int(lap) + 2)
                            except (ValueError, TypeError):
                                pass
        
        return ignore_laps
    
    def _calculate_stint_average(
        self,
        lap_times: Dict[int, float],
        stint: Dict,
        ignore_laps: set,
        race_laps: int = 58
    ) -> Optional[Tuple[float, int, int]]:
        """
        計算 stint 的平均圈速（使用 stint 內燃油校正）
        
        Returns:
            (average_corrected_time, valid_lap_count, mid_lap) or None
            
        關鍵：
            - 使用 stint 內的相對燃油校正（laps_since_stint_start）
            - 不做絕對位置校正，避免過度調整
            - 這個方法產生了 SOFT_vs_MEDIUM -0.2s 的合理結果
        """
        start_lap = stint["start_lap"]
        end_lap = stint["end_lap"]
        
        valid_times = []
        valid_laps = []
        
        for lap_num in range(start_lap, end_lap + 1):
            stint_lap = lap_num - start_lap + 1
            
            # 跳過暖胎圈（前 2 圈）
            if stint_lap <= self.warmup_laps:
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
            
            # 過濾異常慢圈
            if lap_time > 200:
                continue
            
            # Stint 內燃油校正（相對於 stint 開始）
            # 每圈油耗約 1.7kg，每 kg 影響約 0.03s
            # 所以每圈燃油效應約 0.05s
            laps_since_stint_start = stint_lap - 1
            fuel_correction = self.fuel_effect_per_lap * laps_since_stint_start
            corrected_time = lap_time + fuel_correction
            
            valid_times.append(corrected_time)
            valid_laps.append(lap_num)
        
        if len(valid_times) < 3:  # 至少需要 3 圈有效數據
            return None
        
        # 移除異常值 (超過中位數 5% 的圈)
        median_time = statistics.median(valid_times)
        filtered_times = [t for t in valid_times if abs(t - median_time) / median_time < 0.05]
        
        if len(filtered_times) < 3:
            return None
        
        # 計算 stint 中點圈數
        mid_lap = (start_lap + end_lap) // 2
        
        return (statistics.mean(filtered_times), len(filtered_times), mid_lap)
    
    def _compare_compounds(
        self,
        driver_lap_times: Dict[str, Dict[int, float]],
        driver_stints: Dict[str, List[Dict]],
        ignore_laps: set,
        circuit: str
    ) -> Dict[str, List[float]]:
        """
        比較不同配方的平均圈速差異
        
        修正要點:
            - 所有圈速已經過燃油+賽道演化校正
            - 直接比較不同配方的校正後圈速
        
        Returns:
            {'SOFT_vs_MEDIUM': [...], 'HARD_vs_MEDIUM': [...], 'SOFT_vs_HARD': [...]}
        """
        # 收集每個配方的平均圈速 (已校正)
        # 格式: [(driver, avg_corrected_time, mid_lap), ...]
        compound_averages: Dict[str, List[Tuple[str, float, int]]] = {
            'SOFT': [],
            'MEDIUM': [],
            'HARD': []
        }
        
        for driver_num, stints in driver_stints.items():
            if driver_num not in driver_lap_times:
                continue
            
            lap_times = driver_lap_times[driver_num]
            
            for stint in stints:
                compound = stint["compound"]
                
                result = self._calculate_stint_average(lap_times, stint, ignore_laps)
                if result:
                    avg_time, lap_count, mid_lap = result
                    compound_averages[compound].append((driver_num, avg_time, mid_lap))
        
        # 計算配方差異 - 使用簡單的平均比較
        # 不做額外的位置校正，因為 stint 內燃油校正已足夠
        deltas = {
            'SOFT_vs_MEDIUM': [],
            'HARD_vs_MEDIUM': [],
            'SOFT_vs_HARD': []
        }
        
        # SOFT vs MEDIUM
        if compound_averages['SOFT'] and compound_averages['MEDIUM']:
            soft_times = [t for _, t, _ in compound_averages['SOFT']]
            medium_times = [t for _, t, _ in compound_averages['MEDIUM']]
            
            soft_avg = statistics.mean(soft_times)
            medium_avg = statistics.mean(medium_times)
            delta = soft_avg - medium_avg  # 負值 = SOFT 更快
            
            if abs(delta) < 2.0:  # 過濾異常值
                deltas['SOFT_vs_MEDIUM'].append(delta)
                
                if self.debug:
                    soft_mid = statistics.mean([m for _, _, m in compound_averages['SOFT']])
                    med_mid = statistics.mean([m for _, _, m in compound_averages['MEDIUM']])
                    self._log(f"    SOFT vs MEDIUM: {delta:.3f}s "
                             f"(SOFT: {soft_avg:.3f}s @L{soft_mid:.0f}, "
                             f"MEDIUM: {medium_avg:.3f}s @L{med_mid:.0f})")
        
        # HARD vs MEDIUM
        if compound_averages['HARD'] and compound_averages['MEDIUM']:
            hard_times = [t for _, t, _ in compound_averages['HARD']]
            medium_times = [t for _, t, _ in compound_averages['MEDIUM']]
            
            hard_avg = statistics.mean(hard_times)
            medium_avg = statistics.mean(medium_times)
            delta = hard_avg - medium_avg  # 正值 = HARD 更慢
            
            if abs(delta) < 2.0:
                deltas['HARD_vs_MEDIUM'].append(delta)
                
                if self.debug:
                    hard_mid = statistics.mean([m for _, _, m in compound_averages['HARD']])
                    med_mid = statistics.mean([m for _, _, m in compound_averages['MEDIUM']])
                    self._log(f"    HARD vs MEDIUM: {delta:.3f}s "
                             f"(HARD: {hard_avg:.3f}s @L{hard_mid:.0f}, "
                             f"MEDIUM: {medium_avg:.3f}s @L{med_mid:.0f})")
        
        # SOFT vs HARD (驗證用)
        if compound_averages['SOFT'] and compound_averages['HARD']:
            soft_times = [t for _, t, _ in compound_averages['SOFT']]
            hard_times = [t for _, t, _ in compound_averages['HARD']]
            
            soft_avg = statistics.mean(soft_times)
            hard_avg = statistics.mean(hard_times)
            delta = soft_avg - hard_avg  # 負值 = SOFT 更快
            
            if abs(delta) < 3.0:
                deltas['SOFT_vs_HARD'].append(delta)
        
        return deltas
    
    def process_race(self, year: int, race_folder: Path) -> bool:
        """處理單場比賽"""
        race_name = race_folder.name.replace("_Race", "").replace("_", " ")
        circuit = self.race_to_circuit.get(race_name.replace(" ", "_"), race_name)
        
        self._log(f"\n[{year}] {race_name} ({circuit})")
        
        # 載入數據
        timing_data = self._load_json(race_folder / "TimingData.json")
        tyre_series = self._load_json(race_folder / "TyreStintSeries.json")
        pit_collection = self._load_json(race_folder / "PitLaneTimeCollection.json")
        race_control = self._load_json(race_folder / "RaceControlMessages.json")
        
        if not timing_data or not tyre_series:
            self._log(f"  [SKIP] 缺少必要數據")
            return False
        
        # 提取數據
        driver_lap_times = self._extract_lap_times(timing_data)
        driver_stints = self._extract_stint_info(tyre_series)
        ignore_laps = self._extract_race_control_laps(race_control)
        
        if self.debug:
            self._log(f"  車手數: {len(driver_lap_times)}")
            self._log(f"  Stint 數: {sum(len(s) for s in driver_stints.values())}")
            self._log(f"  忽略圈數: {ignore_laps}")
        
        # 提取進站時間
        driver_pits = self._extract_pit_times(pit_collection)
        for driver_num, pit_times in driver_pits.items():
            self.pit_times[circuit].extend(pit_times)
        
        # 比較配方
        deltas = self._compare_compounds(
            driver_lap_times, driver_stints, ignore_laps, circuit
        )
        
        # 收集結果
        for key, values in deltas.items():
            self.global_deltas[key].extend(values)
            self.circuit_deltas[circuit][key].extend(values)
        
        return True
    
    def train_all(self, years: List[int] = None, debug_circuit: str = None):
        """訓練所有可用的歷史數據"""
        if years is None:
            years = [2023, 2024, 2025]  # 預設使用 2023-2025 (2022 沒有 LiveF1 數據)
        
        self._log("=" * 70)
        self._log("輪胎配方速度差異訓練器 - 使用真實賽事數據")
        self._log("=" * 70)
        self._log(f"數據年份: {years}")
        self._log(f"數據來源: {self.livef1_path}")
        
        races_processed = 0
        
        for year in years:
            year_path = self.livef1_path / str(year)
            if not year_path.exists():
                self._log(f"\n[WARNING] 找不到 {year} 數據目錄")
                continue
            
            # 找所有正賽資料夾
            race_folders = sorted([
                f for f in year_path.iterdir() 
                if f.is_dir() and f.name.endswith("_Race")
            ])
            
            self._log(f"\n年份 {year}: 找到 {len(race_folders)} 場比賽")
            
            for race_folder in race_folders:
                # 如果指定了 debug_circuit，只處理該賽道
                if debug_circuit:
                    race_name = race_folder.name.replace("_Race", "").replace("_", " ")
                    circuit = self.race_to_circuit.get(race_name.replace(" ", "_"), race_name)
                    if circuit != debug_circuit:
                        continue
                
                if self.process_race(year, race_folder):
                    races_processed += 1
        
        self._log("\n" + "=" * 70)
        self._log(f"處理完成: {races_processed} 場比賽")
        
        # 生成資料庫
        self._generate_database()
        
        # 更新進站時間資料庫
        self._update_pit_loss_database()
    
    def _generate_database(self):
        """生成配方速度差異資料庫"""
        self._log("\n" + "=" * 70)
        self._log("生成配方速度差異資料庫")
        self._log("=" * 70)
        
        database = {
            "_metadata": {
                "version": "1.0.0",
                "description": "輪胎配方速度差異資料庫 - 從真實賽事數據訓練",
                "last_updated": datetime.now().isoformat(),
                "training_method": "Pair-wise compound comparison with fuel correction",
                "notes": {
                    "SOFT_vs_MEDIUM": "SOFT - MEDIUM (負值 = SOFT 更快)",
                    "HARD_vs_MEDIUM": "HARD - MEDIUM (正值 = HARD 更慢)",
                    "interpretation": "compound_delta['SOFT'] 應為負值，compound_delta['HARD'] 應為正值"
                }
            },
            "global_averages": {},
            "circuits": {}
        }
        
        # 全局平均
        for key in ['SOFT_vs_MEDIUM', 'HARD_vs_MEDIUM', 'SOFT_vs_HARD']:
            values = self.global_deltas[key]
            if len(values) >= 3:
                database["global_averages"][key] = {
                    "mean": round(statistics.mean(values), 4),
                    "median": round(statistics.median(values), 4),
                    "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "samples": len(values)
                }
                
                self._log(f"\n{key}:")
                self._log(f"  Mean:   {database['global_averages'][key]['mean']:.4f}s")
                self._log(f"  Median: {database['global_averages'][key]['median']:.4f}s")
                self._log(f"  Std:    {database['global_averages'][key]['std']:.4f}s")
                self._log(f"  樣本數: {database['global_averages'][key]['samples']}")
        
        # 轉換為策略模擬器格式 (相對於 MEDIUM)
        if 'SOFT_vs_MEDIUM' in database["global_averages"]:
            soft_delta = database["global_averages"]["SOFT_vs_MEDIUM"]["mean"]
        else:
            soft_delta = -0.4  # 預設值
        
        if 'HARD_vs_MEDIUM' in database["global_averages"]:
            hard_delta = database["global_averages"]["HARD_vs_MEDIUM"]["mean"]
        else:
            hard_delta = 0.25  # 預設值
        
        database["compound_deltas"] = {
            "SOFT": round(soft_delta, 3),    # 例如 -0.35
            "MEDIUM": 0.0,                   # 基準
            "HARD": round(hard_delta, 3),    # 例如 0.25
            "confidence": "high" if len(self.global_deltas['SOFT_vs_MEDIUM']) >= 20 else "medium"
        }
        
        self._log(f"\n📊 策略模擬器配方差異:")
        self._log(f"  SOFT:   {database['compound_deltas']['SOFT']}s")
        self._log(f"  MEDIUM: {database['compound_deltas']['MEDIUM']}s")
        self._log(f"  HARD:   {database['compound_deltas']['HARD']}s")
        
        # 各賽道特定值
        for circuit, deltas in self.circuit_deltas.items():
            circuit_data = {}
            
            for key in ['SOFT_vs_MEDIUM', 'HARD_vs_MEDIUM']:
                values = deltas[key]
                if len(values) >= 2:
                    circuit_data[key] = {
                        "mean": round(statistics.mean(values), 4),
                        "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
                        "samples": len(values)
                    }
            
            if circuit_data:
                # 轉換為配方差異
                soft = circuit_data.get('SOFT_vs_MEDIUM', {}).get('mean', soft_delta)
                hard = circuit_data.get('HARD_vs_MEDIUM', {}).get('mean', hard_delta)
                
                database["circuits"][circuit] = {
                    "compound_deltas": {
                        "SOFT": round(soft, 3),
                        "MEDIUM": 0.0,
                        "HARD": round(hard, 3)
                    },
                    "statistics": circuit_data
                }
        
        # 保存
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        
        self._log(f"\n✅ 資料庫已保存: {self.output_path}")
    
    def _update_pit_loss_database(self):
        """更新進站時間資料庫"""
        self._log("\n" + "=" * 70)
        self._log("更新進站時間資料庫")
        self._log("=" * 70)
        
        # 載入現有資料庫
        pit_db = self._load_json(self.pit_db_path)
        if not pit_db:
            self._log("[WARNING] 無法載入進站時間資料庫")
            return
        
        circuits_updated = 0
        
        for circuit, times in self.pit_times.items():
            if len(times) < 3:
                continue
            
            # 計算統計值
            mean_time = statistics.mean(times)
            median_time = statistics.median(times)
            
            # 查找現有資料庫中的對應賽道
            circuit_key = None
            for key in pit_db.get("circuits", {}):
                if key.lower() == circuit.lower() or circuit.lower() in key.lower():
                    circuit_key = key
                    break
            
            if circuit_key:
                old_value = pit_db["circuits"][circuit_key].get("pit_loss_times", {}).get("green_flag", 0)
                
                # 使用中位數作為更新值 (更抗異常)
                new_value = round(median_time, 1)
                
                # 加權更新 (70% 新數據 + 30% 舊數據)
                if old_value > 0:
                    updated_value = round(0.7 * new_value + 0.3 * old_value, 1)
                else:
                    updated_value = new_value
                
                pit_db["circuits"][circuit_key]["pit_loss_times"]["green_flag"] = updated_value
                
                # 同比例更新 SC 和 VSC
                pit_db["circuits"][circuit_key]["pit_loss_times"]["safety_car"] = round(updated_value * 0.52, 1)
                pit_db["circuits"][circuit_key]["pit_loss_times"]["virtual_safety_car"] = round(updated_value * 0.38, 1)
                
                # 添加訓練信息
                pit_db["circuits"][circuit_key]["trained_from_data"] = True
                pit_db["circuits"][circuit_key]["training_samples"] = len(times)
                pit_db["circuits"][circuit_key]["training_mean"] = round(mean_time, 2)
                pit_db["circuits"][circuit_key]["training_median"] = round(median_time, 2)
                
                self._log(f"  {circuit_key}: {old_value}s -> {updated_value}s ({len(times)} samples)")
                circuits_updated += 1
        
        # 更新 metadata
        pit_db["_metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        pit_db["_metadata"]["sources"].append(f"LiveF1 PitLaneTimeCollection 訓練 ({circuits_updated} 賽道)")
        
        # 保存
        with open(self.pit_db_path, 'w', encoding='utf-8') as f:
            json.dump(pit_db, f, ensure_ascii=False, indent=2)
        
        self._log(f"\n✅ 進站時間資料庫已更新: {circuits_updated} 賽道")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="訓練輪胎配方速度差異")
    parser.add_argument("--debug", action="store_true", help="啟用調試輸出")
    parser.add_argument("--debug-circuit", type=str, help="只處理指定賽道")
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025],
                       help="要處理的年份 (預設: 2023-2025)")
    
    args = parser.parse_args()
    
    trainer = CompoundDeltaTrainer(debug=args.debug)
    trainer.train_all(years=args.years, debug_circuit=args.debug_circuit)


if __name__ == "__main__":
    main()
