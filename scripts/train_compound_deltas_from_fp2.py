#!/usr/bin/env python3
"""
配方速度差異訓練器 - 使用 FP2 Long Run 數據

使用 FP2 練習賽的 Long Run 數據來訓練配方速度差異，
避免正賽中的策略和塞車影響。

關鍵改進：
1. 使用 Long Run Loader 的自動偵測邏輯
2. 只使用穩定的 Long Run stint（非衝刺圈）
3. 使用燃油校正後的圈速
4. FP2 數據較少受策略影響

Author: F1T Team
Date: 2025-12-31
"""

import sys
import os
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategy_simulator.data.longrun_loader import (
    LongRunLoader, 
    LongRunCalculator,
    LapData,
    StintInfo,
    DriverFuelSettings
)


@dataclass
class CompoundDelta:
    """配方差異結果"""
    circuit: str
    year: int
    soft_vs_medium: Optional[float] = None
    hard_vs_medium: Optional[float] = None
    soft_samples: int = 0
    medium_samples: int = 0
    hard_samples: int = 0


class FP2CompoundDeltaTrainer:
    """使用 FP2 Long Run 數據訓練配方差異"""
    
    # 要處理的年份
    YEARS = [2023, 2024, 2025]
    
    # Long Run 最小圈數
    MIN_LONG_RUN_LAPS = 5
    
    # 燃油校正參數
    FUEL_EFFECT_PER_KG = 0.030  # 每公斤燃油影響的圈速
    FUEL_KG_PER_LAP = 1.70  # 每圈油耗
    
    def __init__(self, json_root: str = None, debug: bool = False):
        self.json_root = Path(json_root) if json_root else Path("json/LiveF1")
        self.debug = debug
        self.results: List[CompoundDelta] = []
        
        # Race to circuit mapping
        self.race_to_circuit = {
            "Abu_Dhabi": "Yas_Marina",
            "Australian": "Melbourne",
            "Austrian": "Spielberg",
            "Azerbaijan": "Baku",
            "Bahrain": "Bahrain",
            "Belgian": "Spa",
            "British": "Silverstone",
            "Canadian": "Montreal",
            "Chinese": "Shanghai",
            "Dutch": "Zandvoort",
            "Emilia_Romagna": "Imola",
            "Hungarian": "Budapest",
            "Italian": "Monza",
            "Japanese": "Suzuka",
            "Las_Vegas": "Las_Vegas",
            "Mexico_City": "Mexico",
            "Miami": "Miami",
            "Monaco": "Monaco",
            "Qatar": "Lusail",
            "Saudi_Arabian": "Jeddah",
            "Singapore": "Singapore",
            "Spanish": "Barcelona",
            "São_Paulo": "Interlagos",
            "United_States": "Austin",
        }
    
    def _log(self, msg: str):
        """輸出日誌"""
        print(msg)
    
    def find_fp2_folders(self, year: int) -> List[Path]:
        """找到所有 FP2 資料夾"""
        year_folder = self.json_root / str(year)
        if not year_folder.exists():
            return []
        
        fp2_folders = []
        for folder in year_folder.iterdir():
            if not folder.is_dir():
                continue
            
            folder_name = folder.name.lower()
            
            # 檢查是否是 FP2 資料夾
            # 格式: "Abu_Dhabi_Practice_2" 或 "Japanese_Practice_2"
            if "practice_2" in folder_name or "fp2" in folder_name:
                fp2_folders.append(folder)
        
        return sorted(fp2_folders)
    
    def load_timing_data(self, fp2_folder: Path) -> Optional[Dict]:
        """載入 FP2 Timing 數據"""
        timing_file = fp2_folder / "TimingData.json"
        if not timing_file.exists():
            return None
        
        try:
            with open(timing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if self.debug:
                self._log(f"  [ERROR] 載入 TimingData 失敗: {e}")
            return None
    
    def load_tyre_data(self, fp2_folder: Path) -> Optional[Dict]:
        """載入輪胎數據"""
        tyre_file = fp2_folder / "TyreStintSeries.json"
        if not tyre_file.exists():
            return None
        
        try:
            with open(tyre_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if self.debug:
                self._log(f"  [ERROR] 載入 TyreStintSeries 失敗: {e}")
            return None
    
    def extract_lap_times(self, timing_data: Dict) -> Dict[str, Dict[int, float]]:
        """提取每位車手的圈速"""
        driver_laps: Dict[str, Dict[int, float]] = {}
        
        records = timing_data.get("records", [])
        for record in records:
            data = record.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # FP2 數據在 Lines 裡面
            lines = data.get("Lines", data)
            if not isinstance(lines, dict):
                continue
            
            for driver_num, driver_data in lines.items():
                if not isinstance(driver_data, dict):
                    continue
                
                # 嘗試兩種格式
                lap_data = driver_data.get("LastLapTime", {})
                if isinstance(lap_data, dict):
                    time_str = lap_data.get("Value", "")
                    if time_str and ":" in time_str:
                        try:
                            parts = time_str.split(":")
                            lap_time = float(parts[0]) * 60 + float(parts[1])
                            
                            # 獲取圈數
                            lap_num = driver_data.get("NumberOfLaps")
                            if lap_num is not None:
                                if driver_num not in driver_laps:
                                    driver_laps[driver_num] = {}
                                driver_laps[driver_num][int(lap_num)] = lap_time
                        except:
                            pass
        
        return driver_laps
    
    def extract_stints(self, tyre_data: Dict) -> Dict[str, List[Dict]]:
        """提取每位車手的 stint 資訊"""
        driver_stints: Dict[str, List[Dict]] = {}
        
        records = tyre_data.get("records", [])
        for record in records:
            data = record.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # FP2 數據可能在 Lines 裡面
            lines = data.get("Lines", data)
            if not isinstance(lines, dict):
                continue
            
            for driver_num, driver_info in lines.items():
                if not isinstance(driver_info, dict):
                    continue
                
                stints = driver_info.get("Stints", {})
                if not stints:
                    continue
                
                if driver_num not in driver_stints:
                    driver_stints[driver_num] = []
                
                # 處理每個 stint
                for stint_id, stint_info in stints.items():
                    if not isinstance(stint_info, dict):
                        continue
                    
                    compound = stint_info.get("Compound", "UNKNOWN").upper()
                    start_lap = stint_info.get("StartLaps")
                    total_laps = stint_info.get("TotalLaps", stint_info.get("LapNumber"))
                    
                    if start_lap is not None and total_laps is not None:
                        stint_data = {
                            "stint_id": int(stint_id),
                            "compound": compound,
                            "start_lap": int(start_lap) + 1,  # 0-indexed to 1-indexed
                            "end_lap": int(start_lap) + int(total_laps),
                        }
                        
                        # 避免重複
                        exists = any(
                            s["stint_id"] == stint_data["stint_id"] and 
                            s["start_lap"] == stint_data["start_lap"]
                            for s in driver_stints[driver_num]
                        )
                        if not exists:
                            driver_stints[driver_num].append(stint_data)
        
        # 排序
        for driver_num in driver_stints:
            driver_stints[driver_num].sort(key=lambda x: x["start_lap"])
        
        return driver_stints
    
    def detect_long_runs(
        self, 
        lap_times: Dict[int, float], 
        stint: Dict,
        min_laps: int = 5
    ) -> Optional[Tuple[float, int]]:
        """
        偵測並計算 Long Run 平均圈速
        
        Long Run 定義：
        1. 至少連續 min_laps 圈
        2. 圈速標準差小於 1.5 秒
        3. 沒有異常慢圈（outlap）
        
        Returns:
            (average_lap_time, lap_count) or None
        """
        start_lap = stint["start_lap"]
        end_lap = stint["end_lap"]
        stint_length = end_lap - start_lap + 1
        
        if stint_length < min_laps:
            return None
        
        # 收集 stint 內的圈速
        valid_times = []
        valid_laps = []
        
        for lap_num in range(start_lap, end_lap + 1):
            # 跳過第一圈（outlap）
            if lap_num == start_lap:
                continue
            
            if lap_num not in lap_times:
                continue
            
            lap_time = lap_times[lap_num]
            
            # 過濾異常慢圈（可能是塞車或失誤）
            if lap_time > 300:  # 5分鐘以上肯定有問題
                continue
            
            valid_times.append(lap_time)
            valid_laps.append(lap_num)
        
        if len(valid_times) < min_laps - 1:
            return None
        
        # 計算中位數，過濾異常值
        median_time = statistics.median(valid_times)
        
        # 過濾超過中位數 5 秒的圈（衝刺圈或失誤圈）
        filtered_times = [
            t for t in valid_times 
            if abs(t - median_time) < 5.0
        ]
        
        if len(filtered_times) < min_laps - 1:
            return None
        
        # 計算標準差
        if len(filtered_times) > 1:
            stddev = statistics.stdev(filtered_times)
            
            # Long Run 的標準差應該較小（穩定的節奏圈）
            # 如果標準差太大，可能是衝刺圈混入
            if stddev > 1.5:
                if self.debug:
                    print(f"      [SKIP] 標準差過大: {stddev:.3f}s")
                return None
        
        # 使用燃油校正
        # 假設 FP2 開始時油量約 60kg，每圈消耗 1.7kg
        # 將圈速標準化到 "滿油" 狀態
        corrected_times = []
        for i, lap_time in enumerate(filtered_times):
            # 估算當時的油量
            estimated_laps_run = i + 2  # 包含 outlap
            fuel_consumed = estimated_laps_run * self.FUEL_KG_PER_LAP
            fuel_correction = fuel_consumed * self.FUEL_EFFECT_PER_KG
            
            corrected_time = lap_time + fuel_correction
            corrected_times.append(corrected_time)
        
        return (statistics.mean(corrected_times), len(corrected_times))
    
    def process_fp2(self, fp2_folder: Path, year: int) -> Optional[CompoundDelta]:
        """處理單場 FP2"""
        # 從資料夾名稱提取賽事名稱
        # 格式: "Abu_Dhabi_Practice_2" -> "Abu_Dhabi"
        folder_name = fp2_folder.name
        race_name = folder_name.replace("_Practice_2", "").replace("_FP2", "")
        circuit = self.race_to_circuit.get(race_name, race_name.replace("_", " "))
        
        self._log(f"\n[{year}] {race_name.replace('_', ' ')} ({circuit}) - FP2")
        
        # 載入數據
        timing_data = self.load_timing_data(fp2_folder)
        tyre_data = self.load_tyre_data(fp2_folder)
        
        if not timing_data or not tyre_data:
            self._log(f"  [SKIP] 缺少必要數據")
            return None
        
        # 提取圈速和 stint
        driver_laps = self.extract_lap_times(timing_data)
        driver_stints = self.extract_stints(tyre_data)
        
        self._log(f"  車手數: {len(driver_laps)}")
        
        # 收集每個配方的 Long Run 平均圈速
        compound_times: Dict[str, List[float]] = {
            "SOFT": [],
            "MEDIUM": [],
            "HARD": []
        }
        
        for driver_num, stints in driver_stints.items():
            if driver_num not in driver_laps:
                continue
            
            lap_times = driver_laps[driver_num]
            
            for stint in stints:
                compound = stint["compound"]
                if compound not in compound_times:
                    continue
                
                result = self.detect_long_runs(
                    lap_times, stint, 
                    min_laps=self.MIN_LONG_RUN_LAPS
                )
                
                if result:
                    avg_time, lap_count = result
                    compound_times[compound].append(avg_time)
                    
                    if self.debug:
                        self._log(f"    [{driver_num}] {compound}: {avg_time:.3f}s ({lap_count} laps)")
        
        # 計算配方差異
        result = CompoundDelta(
            circuit=circuit,
            year=year,
            soft_samples=len(compound_times["SOFT"]),
            medium_samples=len(compound_times["MEDIUM"]),
            hard_samples=len(compound_times["HARD"]),
        )
        
        # 需要至少有 MEDIUM 作為基準
        if not compound_times["MEDIUM"]:
            self._log(f"  [SKIP] 沒有 MEDIUM Long Run 數據")
            return None
        
        medium_avg = statistics.mean(compound_times["MEDIUM"])
        
        # SOFT vs MEDIUM
        if compound_times["SOFT"]:
            soft_avg = statistics.mean(compound_times["SOFT"])
            result.soft_vs_medium = soft_avg - medium_avg
            self._log(f"  SOFT vs MEDIUM: {result.soft_vs_medium:+.3f}s "
                     f"(SOFT: {soft_avg:.3f}s, MEDIUM: {medium_avg:.3f}s)")
        
        # HARD vs MEDIUM
        if compound_times["HARD"]:
            hard_avg = statistics.mean(compound_times["HARD"])
            result.hard_vs_medium = hard_avg - medium_avg
            self._log(f"  HARD vs MEDIUM: {result.hard_vs_medium:+.3f}s "
                     f"(HARD: {hard_avg:.3f}s, MEDIUM: {medium_avg:.3f}s)")
        
        return result
    
    def train(self) -> Dict:
        """執行訓練"""
        self._log("=" * 60)
        self._log("配方速度差異訓練器 - 使用 FP2 Long Run 數據")
        self._log("=" * 60)
        self._log(f"數據年份: {self.YEARS}")
        self._log(f"數據來源: {self.json_root.absolute()}")
        
        all_soft_vs_medium = []
        all_hard_vs_medium = []
        circuit_results: Dict[str, List[CompoundDelta]] = {}
        
        for year in self.YEARS:
            fp2_folders = self.find_fp2_folders(year)
            self._log(f"\n年份 {year}: 找到 {len(fp2_folders)} 場 FP2")
            
            for fp2_folder in fp2_folders:
                result = self.process_fp2(fp2_folder, year)
                
                if result:
                    self.results.append(result)
                    
                    if result.soft_vs_medium is not None:
                        all_soft_vs_medium.append(result.soft_vs_medium)
                    if result.hard_vs_medium is not None:
                        all_hard_vs_medium.append(result.hard_vs_medium)
                    
                    # 按賽道分組
                    if result.circuit not in circuit_results:
                        circuit_results[result.circuit] = []
                    circuit_results[result.circuit].append(result)
        
        # 生成報告
        self._log("\n" + "=" * 60)
        self._log("訓練結果摘要")
        self._log("=" * 60)
        
        if all_soft_vs_medium:
            self._log(f"\nSOFT vs MEDIUM:")
            self._log(f"  Mean:   {statistics.mean(all_soft_vs_medium):.3f}s")
            self._log(f"  Median: {statistics.median(all_soft_vs_medium):.3f}s")
            if len(all_soft_vs_medium) > 1:
                self._log(f"  Std:    {statistics.stdev(all_soft_vs_medium):.3f}s")
            self._log(f"  樣本數: {len(all_soft_vs_medium)}")
        
        if all_hard_vs_medium:
            self._log(f"\nHARD vs MEDIUM:")
            self._log(f"  Mean:   {statistics.mean(all_hard_vs_medium):.3f}s")
            self._log(f"  Median: {statistics.median(all_hard_vs_medium):.3f}s")
            if len(all_hard_vs_medium) > 1:
                self._log(f"  Std:    {statistics.stdev(all_hard_vs_medium):.3f}s")
            self._log(f"  樣本數: {len(all_hard_vs_medium)}")
        
        # 生成資料庫
        database = self._generate_database(
            all_soft_vs_medium, 
            all_hard_vs_medium, 
            circuit_results
        )
        
        return database
    
    def _generate_database(
        self,
        all_soft_vs_medium: List[float],
        all_hard_vs_medium: List[float],
        circuit_results: Dict[str, List[CompoundDelta]]
    ) -> Dict:
        """生成配方差異資料庫"""
        from datetime import datetime
        
        database = {
            "_metadata": {
                "version": "2.0.0",
                "description": "輪胎配方速度差異資料庫 - 從 FP2 Long Run 數據訓練",
                "last_updated": datetime.now().isoformat(),
                "training_method": "FP2 Long Run analysis with fuel correction",
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
        if all_soft_vs_medium:
            database["global_averages"]["SOFT_vs_MEDIUM"] = {
                "mean": round(statistics.mean(all_soft_vs_medium), 4),
                "median": round(statistics.median(all_soft_vs_medium), 4),
                "std": round(statistics.stdev(all_soft_vs_medium), 4) if len(all_soft_vs_medium) > 1 else 0,
                "min": round(min(all_soft_vs_medium), 4),
                "max": round(max(all_soft_vs_medium), 4),
                "samples": len(all_soft_vs_medium)
            }
        
        if all_hard_vs_medium:
            database["global_averages"]["HARD_vs_MEDIUM"] = {
                "mean": round(statistics.mean(all_hard_vs_medium), 4),
                "median": round(statistics.median(all_hard_vs_medium), 4),
                "std": round(statistics.stdev(all_hard_vs_medium), 4) if len(all_hard_vs_medium) > 1 else 0,
                "min": round(min(all_hard_vs_medium), 4),
                "max": round(max(all_hard_vs_medium), 4),
                "samples": len(all_hard_vs_medium)
            }
        
        # 計算全局配方差異（用於策略模擬器）
        soft_delta = statistics.median(all_soft_vs_medium) if all_soft_vs_medium else 0.0
        hard_delta = statistics.median(all_hard_vs_medium) if all_hard_vs_medium else 0.0
        
        self._log(f"\n📊 策略模擬器配方差異:")
        self._log(f"  SOFT:   {soft_delta:.3f}s")
        self._log(f"  MEDIUM: 0.0s")
        self._log(f"  HARD:   {hard_delta:.3f}s")
        
        # 每個賽道的配方差異
        for circuit, results in circuit_results.items():
            soft_deltas = [r.soft_vs_medium for r in results if r.soft_vs_medium is not None]
            hard_deltas = [r.hard_vs_medium for r in results if r.hard_vs_medium is not None]
            
            circuit_data = {
                "compound_deltas": {
                    "SOFT": round(statistics.mean(soft_deltas), 3) if soft_deltas else soft_delta,
                    "MEDIUM": 0.0,
                    "HARD": round(statistics.mean(hard_deltas), 3) if hard_deltas else hard_delta
                },
                "statistics": {}
            }
            
            if soft_deltas:
                circuit_data["statistics"]["SOFT_vs_MEDIUM"] = {
                    "mean": round(statistics.mean(soft_deltas), 4),
                    "std": round(statistics.stdev(soft_deltas), 4) if len(soft_deltas) > 1 else 0,
                    "samples": len(soft_deltas)
                }
            
            if hard_deltas:
                circuit_data["statistics"]["HARD_vs_MEDIUM"] = {
                    "mean": round(statistics.mean(hard_deltas), 4),
                    "std": round(statistics.stdev(hard_deltas), 4) if len(hard_deltas) > 1 else 0,
                    "samples": len(hard_deltas)
                }
            
            database["circuits"][circuit] = circuit_data
        
        # 保存資料庫
        output_path = Path("config/compound_delta_database_fp2.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        self._log(f"\n✅ 資料庫已保存: {output_path.absolute()}")
        
        return database


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="使用 FP2 Long Run 數據訓練配方差異")
    parser.add_argument("--debug", action="store_true", help="顯示詳細輸出")
    parser.add_argument("--json-root", default="json/LiveF1", help="JSON 數據根目錄")
    
    args = parser.parse_args()
    
    trainer = FP2CompoundDeltaTrainer(
        json_root=args.json_root,
        debug=args.debug
    )
    
    trainer.train()


if __name__ == "__main__":
    main()
