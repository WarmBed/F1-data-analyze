#!/usr/bin/env python3
"""
訓練 Throttle Baseline 資料庫 - 使用 LiveF1 CarData.json

原理:
    每個賽道的「正常全油門比例」不同，取決於:
    1. 賽道特性 (直道比例、彎道數量)
    2. 賽道長度
    3. 空氣動力學需求
    
    通過分析歷史數據，建立每個賽道的 full_throttle_ratio 基準值
    當實時數據低於基準值時，才判斷為「省胎」

數據來源:
    json/LiveF1/{year}/{race}/CarData.json
    
    CarData.json 結構:
    - Channels["4"]: Throttle (0-100, 百分比)
    - Channels["5"]: Brake (0-100, 百分比)

輸出:
    config/throttle_baseline_database.json

使用方式:
    python scripts/train_throttle_baseline_from_history.py
    python scripts/train_throttle_baseline_from_history.py --debug
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import statistics

# 添加專案根目錄到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ThrottleBaselineTrainer:
    """
    Throttle Baseline 訓練器 - 從 LiveF1 歷史數據建立賽道基準值
    
    核心原理:
    1. 從 CarData.json 提取每個採樣點的 Throttle 值
    2. 計算 full_throttle_ratio = count(throttle >= 95) / total_samples
    3. 對每個賽道統計 mean, std, percentiles
    4. 用作省胎判斷的基準值
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.base_path = project_root
        self.livef1_path = self.base_path / "json" / "LiveF1"
        self.output_path = self.base_path / "config" / "throttle_baseline_database.json"
        
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
        
        # 收集的訓練數據
        # {circuit: [session_results, ...]}
        self.training_results: Dict[str, List[Dict]] = defaultdict(list)
        
        # 閾值設定
        self.full_throttle_threshold = 95  # Throttle >= 95% 視為全油門
        self.min_samples_per_session = 1000  # 每場比賽至少需要 1000 個樣本
    
    def _log(self, msg: str, level: str = "INFO"):
        """輸出日誌"""
        if level == "DEBUG" and not self.debug:
            return
        print(f"[{level}] {msg}")
    
    def _extract_race_name(self, folder_name: str) -> Optional[str]:
        """
        從資料夾名稱提取賽事名稱
        
        Examples:
            "Italian_Race" -> "Italian"
            "Abu_Dhabi_Race" -> "Abu_Dhabi"
        """
        match = re.match(r"(.+?)_Race$", folder_name)
        if match:
            return match.group(1)
        return None
    
    def _get_circuit_name(self, race_name: str) -> str:
        """從賽事名稱獲取賽道名稱"""
        return self.race_to_circuit.get(race_name, race_name)
    
    def _load_car_data(self, car_data_path: Path) -> Optional[List[Dict]]:
        """
        載入 CarData.json
        
        Returns:
            List of records with timestamp and car data
        """
        try:
            with open(car_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # LiveF1 格式: {"metadata": {...}, "records": [...]}
            if isinstance(data, dict) and "records" in data:
                return data["records"]
            # 直接是列表格式
            elif isinstance(data, list):
                return data
            else:
                return [data]
                
        except json.JSONDecodeError as e:
            self._log(f"JSON 解析錯誤 {car_data_path}: {e}", "DEBUG")
            return None
        except MemoryError:
            self._log(f"檔案太大無法載入 {car_data_path}", "DEBUG")
            return None
        except Exception as e:
            self._log(f"無法載入 {car_data_path}: {e}", "DEBUG")
            return None
    
    def _extract_throttle_samples(self, car_data: List[Dict]) -> Dict[str, List[int]]:
        """
        從 CarData 提取每個車手的 Throttle 採樣值
        
        Args:
            car_data: CarData.json 的內容
            
        Returns:
            {driver_num: [throttle_values]}
        """
        driver_samples: Dict[str, List[int]] = defaultdict(list)
        
        for record in car_data:
            # 處理不同的資料結構
            data = record.get("data", record)
            entries = data.get("Entries", [])
            
            if not isinstance(entries, list):
                entries = [entries]
            
            for entry in entries:
                cars = entry.get("Cars", {})
                
                for driver_num, car_info in cars.items():
                    if not isinstance(car_info, dict):
                        continue
                    
                    channels = car_info.get("Channels", {})
                    
                    # Channel 4 = Throttle (0-100)
                    throttle = channels.get("4")
                    
                    if throttle is not None:
                        try:
                            throttle_val = int(throttle)
                            # 有效範圍檢查
                            if 0 <= throttle_val <= 104:  # 允許一點容差
                                driver_samples[driver_num].append(min(throttle_val, 100))
                        except (ValueError, TypeError):
                            pass
        
        return dict(driver_samples)
    
    def _calculate_session_stats(
        self, 
        driver_samples: Dict[str, List[int]]
    ) -> Optional[Dict]:
        """
        計算單場比賽的 Throttle 統計
        
        Returns:
            {
                "total_samples": int,
                "drivers_analyzed": int,
                "full_throttle_ratio": float,  # 全油門比例
                "avg_throttle": float,  # 平均油門
                "driver_stats": {...}
            }
        """
        all_samples = []
        driver_stats = {}
        
        for driver_num, samples in driver_samples.items():
            if len(samples) < 100:  # 每個車手至少 100 個樣本
                continue
            
            # 計算該車手的統計
            full_throttle_count = sum(1 for t in samples if t >= self.full_throttle_threshold)
            full_throttle_ratio = full_throttle_count / len(samples)
            avg_throttle = sum(samples) / len(samples)
            
            driver_stats[driver_num] = {
                "samples": len(samples),
                "full_throttle_ratio": round(full_throttle_ratio, 4),
                "avg_throttle": round(avg_throttle, 2)
            }
            
            all_samples.extend(samples)
        
        if len(all_samples) < self.min_samples_per_session:
            return None
        
        # 計算整場比賽的統計 (使用高效計算)
        full_throttle_count = sum(1 for t in all_samples if t >= self.full_throttle_threshold)
        total = len(all_samples)
        avg = sum(all_samples) / total
        
        # 計算標準差 (使用 Welford's algorithm 避免大數問題)
        # 簡化：直接用基本公式但限制樣本大小
        sample_for_std = all_samples[:50000] if len(all_samples) > 50000 else all_samples
        if len(sample_for_std) > 1:
            mean_s = sum(sample_for_std) / len(sample_for_std)
            variance = sum((x - mean_s) ** 2 for x in sample_for_std) / (len(sample_for_std) - 1)
            std = variance ** 0.5
        else:
            std = 0
        
        return {
            "total_samples": total,
            "drivers_analyzed": len(driver_stats),
            "full_throttle_ratio": round(full_throttle_count / total, 4),
            "avg_throttle": round(avg, 2),
            "throttle_std": round(std, 2),
            "driver_stats": driver_stats
        }
    
    def train_from_race(self, race_path: Path, year: int) -> bool:
        """
        從單場比賽訓練
        
        Args:
            race_path: 比賽資料夾路徑 (例如 json/LiveF1/2024/Italian_Race)
            year: 年份
            
        Returns:
            是否成功
        """
        race_name = self._extract_race_name(race_path.name)
        if not race_name:
            self._log(f"無法解析賽事名稱: {race_path.name}", "DEBUG")
            return False
        
        circuit = self._get_circuit_name(race_name)
        car_data_file = race_path / "CarData.json"
        
        if not car_data_file.exists():
            self._log(f"找不到 CarData.json: {car_data_file}", "DEBUG")
            return False
        
        self._log(f"處理 {year} {race_name} ({circuit})...", "INFO")
        
        # 載入 CarData
        car_data = self._load_car_data(car_data_file)
        if not car_data:
            return False
        
        # 提取 Throttle 採樣
        driver_samples = self._extract_throttle_samples(car_data)
        
        if not driver_samples:
            self._log(f"  無法提取 Throttle 數據", "DEBUG")
            return False
        
        # 計算統計
        stats = self._calculate_session_stats(driver_samples)
        
        if not stats:
            self._log(f"  樣本數量不足", "DEBUG")
            return False
        
        # 記錄結果
        session_result = {
            "year": year,
            "race": race_name,
            "circuit": circuit,
            **stats
        }
        
        self.training_results[circuit].append(session_result)
        
        self._log(f"  全油門比例: {stats['full_throttle_ratio']:.2%}, "
                  f"平均油門: {stats['avg_throttle']:.1f}%, "
                  f"樣本數: {stats['total_samples']}", "INFO")
        
        return True
    
    def train_all(self):
        """
        訓練所有可用的比賽數據
        """
        self._log("=" * 60)
        self._log("開始訓練 Throttle Baseline 資料庫")
        self._log("=" * 60)
        
        total_races = 0
        successful_races = 0
        
        # 遍歷所有年份
        if not self.livef1_path.exists():
            self._log(f"找不到 LiveF1 資料夾: {self.livef1_path}", "ERROR")
            return
        
        for year_folder in sorted(self.livef1_path.iterdir()):
            if not year_folder.is_dir():
                continue
            
            try:
                year = int(year_folder.name)
            except ValueError:
                continue
            
            self._log(f"\n處理 {year} 賽季...")
            
            # 遍歷該年的所有比賽
            for race_folder in sorted(year_folder.iterdir()):
                if not race_folder.is_dir():
                    continue
                
                if not race_folder.name.endswith("_Race"):
                    continue
                
                total_races += 1
                if self.train_from_race(race_folder, year):
                    successful_races += 1
        
        self._log(f"\n訓練完成: {successful_races}/{total_races} 場比賽成功")
    
    def aggregate_results(self) -> Dict:
        """
        聚合訓練結果，生成最終資料庫
        
        Returns:
            完整的 throttle_baseline_database
        """
        circuits_data = {}
        
        for circuit, sessions in self.training_results.items():
            if not sessions:
                continue
            
            # 收集所有 session 的 full_throttle_ratio
            ratios = [s["full_throttle_ratio"] for s in sessions]
            avg_throttles = [s["avg_throttle"] for s in sessions]
            
            # 計算統計
            mean_ratio = statistics.mean(ratios)
            std_ratio = statistics.stdev(ratios) if len(ratios) > 1 else 0
            
            # Percentiles
            sorted_ratios = sorted(ratios)
            p25 = sorted_ratios[int(len(sorted_ratios) * 0.25)] if len(sorted_ratios) >= 4 else min(sorted_ratios)
            p50 = sorted_ratios[int(len(sorted_ratios) * 0.50)]
            p75 = sorted_ratios[int(len(sorted_ratios) * 0.75)] if len(sorted_ratios) >= 4 else max(sorted_ratios)
            
            circuits_data[circuit] = {
                "full_throttle_ratio": {
                    "mean": round(mean_ratio, 4),
                    "std": round(std_ratio, 4),
                    "min": round(min(ratios), 4),
                    "max": round(max(ratios), 4),
                    "p25": round(p25, 4),
                    "p50": round(p50, 4),
                    "p75": round(p75, 4)
                },
                "avg_throttle": {
                    "mean": round(statistics.mean(avg_throttles), 2),
                    "std": round(statistics.stdev(avg_throttles), 2) if len(avg_throttles) > 1 else 0
                },
                "sessions_analyzed": len(sessions),
                "years": sorted(set(s["year"] for s in sessions)),
                "total_samples": sum(s["total_samples"] for s in sessions)
            }
        
        # 計算全局基準值 (用於未知賽道)
        all_ratios = []
        all_avg_throttles = []
        for sessions in self.training_results.values():
            for s in sessions:
                all_ratios.append(s["full_throttle_ratio"])
                all_avg_throttles.append(s["avg_throttle"])
        
        global_baseline = {
            "full_throttle_ratio": {
                "mean": round(statistics.mean(all_ratios), 4) if all_ratios else 0.55,
                "std": round(statistics.stdev(all_ratios), 4) if len(all_ratios) > 1 else 0.05
            },
            "avg_throttle": {
                "mean": round(statistics.mean(all_avg_throttles), 2) if all_avg_throttles else 50.0,
                "std": round(statistics.stdev(all_avg_throttles), 2) if len(all_avg_throttles) > 1 else 5.0
            }
        }
        
        return {
            "_metadata": {
                "version": "1.0.0",
                "description": "F1 Throttle Baseline Database - 用於省胎行為分析",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "sources": ["LiveF1 Historical CarData.json"],
                "training_method": "Statistical analysis of full throttle ratio",
                "full_throttle_threshold": self.full_throttle_threshold,
                "notes": {
                    "full_throttle_ratio": "Throttle >= 95% 的採樣比例",
                    "avg_throttle": "平均油門值 (%)",
                    "usage": "當 current_ratio < baseline_mean - 2*std 時判斷為省胎"
                }
            },
            "global_baseline": global_baseline,
            "circuits": circuits_data
        }
    
    def save_database(self, database: Dict):
        """
        儲存資料庫到 JSON 檔案
        """
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        self._log(f"\n資料庫已儲存到: {self.output_path}")
    
    def run(self):
        """
        執行完整的訓練流程
        """
        self.train_all()
        
        if not self.training_results:
            self._log("沒有成功訓練任何數據", "ERROR")
            return
        
        database = self.aggregate_results()
        self.save_database(database)
        
        # 輸出摘要
        self._log("\n" + "=" * 60)
        self._log("訓練摘要")
        self._log("=" * 60)
        
        for circuit, data in sorted(database["circuits"].items()):
            ratio = data["full_throttle_ratio"]["mean"]
            std = data["full_throttle_ratio"]["std"]
            sessions = data["sessions_analyzed"]
            self._log(f"  {circuit}: {ratio:.2%} +/- {std:.2%} ({sessions} sessions)")
        
        global_ratio = database["global_baseline"]["full_throttle_ratio"]["mean"]
        self._log(f"\n全局基準: {global_ratio:.2%}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="訓練 Throttle Baseline 資料庫")
    parser.add_argument("--debug", action="store_true", help="顯示除錯訊息")
    args = parser.parse_args()
    
    trainer = ThrottleBaselineTrainer(debug=args.debug)
    trainer.run()


if __name__ == "__main__":
    main()
