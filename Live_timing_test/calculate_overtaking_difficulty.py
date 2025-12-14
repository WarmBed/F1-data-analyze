#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
賽道超車難度指數計算器
========================

基於 2023-2024 歷史數據計算每個賽道的超車難度指數。

方法:
1. 統計每場比賽的總超車次數
2. 計算每圈平均超車次數
3. 考慮 DRS 區域數量
4. 綜合計算難度指數 (0-1, 1=最難超車)

輸出:
- json/track_overtaking_difficulty.json

作者: F1 Telemetry Station Pro
日期: 2025-11-26
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import statistics

from core.logger import get_logger


logger = get_logger(component="gui")


class OvertakingDifficultyCalculator:
    """賽道超車難度計算器"""
    
    # 已知的 DRS 區域數量 (手動維護)
    DRS_ZONES = {
        "Abu_Dhabi": 2,
        "Australian": 3,
        "Austrian": 2,
        "Azerbaijan": 2,
        "Bahrain": 3,
        "Belgian": 2,
        "British": 2,
        "Canadian": 3,
        "Chinese": 2,
        "Dutch": 1,
        "Emilia_Romagna": 1,
        "Hungarian": 1,
        "Italian": 2,
        "Japanese": 1,
        "Las_Vegas": 2,
        "Mexico_City": 2,
        "Miami": 3,
        "Monaco": 1,
        "Qatar": 2,
        "Saudi_Arabian": 3,
        "Singapore": 2,
        "Spanish": 2,
        "São_Paulo": 2,
        "United_States": 2,
    }
    
    # 已知賽道圈數
    RACE_LAPS = {
        "Abu_Dhabi": 58,
        "Australian": 58,
        "Austrian": 71,
        "Azerbaijan": 51,
        "Bahrain": 57,
        "Belgian": 44,
        "British": 52,
        "Canadian": 70,
        "Chinese": 56,
        "Dutch": 72,
        "Emilia_Romagna": 63,
        "Hungarian": 70,
        "Italian": 53,
        "Japanese": 53,
        "Las_Vegas": 50,
        "Mexico_City": 71,
        "Miami": 57,
        "Monaco": 78,
        "Qatar": 57,
        "Saudi_Arabian": 50,
        "Singapore": 62,
        "Spanish": 66,
        "São_Paulo": 69,
        "United_States": 56,
    }
    
    def __init__(self, base_path: str = "json/LiveF1"):
        self.base_path = base_path
        self.results = {}
        
    def calculate_all(self, years: List[str] = ["2023", "2024"]) -> Dict:
        """計算所有賽道的超車難度"""
        
        # 收集每個賽道的超車數據
        track_overtakes = defaultdict(list)  # {track_name: [overtake_counts]}
        track_position_changes = defaultdict(list)  # {track_name: [total_position_changes]}
        
        for year in years:
            year_path = os.path.join(self.base_path, year)
            if not os.path.exists(year_path):
                logger.warning(f"找不到 {year} 數據")
                continue
                
            races = [r for r in os.listdir(year_path) if "_Race" in r]
            
            for race in races:
                track_name = race.replace("_Race", "")
                race_path = os.path.join(year_path, race)
                
                logger.info(f"處理 {year} {track_name}...")
                
                # 計算超車次數
                overtakes, position_changes = self._analyze_race(race_path)
                
                if overtakes is not None:
                    track_overtakes[track_name].append(overtakes)
                if position_changes is not None:
                    track_position_changes[track_name].append(position_changes)
        
        # 計算每個賽道的難度指數
        difficulty_scores = {}
        
        for track_name in set(track_overtakes.keys()) | set(track_position_changes.keys()):
            overtakes_list = track_overtakes.get(track_name, [])
            changes_list = track_position_changes.get(track_name, [])
            
            # 平均超車次數
            avg_overtakes = statistics.mean(overtakes_list) if overtakes_list else 0
            
            # 平均位置變化
            avg_position_changes = statistics.mean(changes_list) if changes_list else 0
            
            # 每圈超車次數
            race_laps = self.RACE_LAPS.get(track_name, 55)
            overtakes_per_lap = avg_overtakes / race_laps if race_laps > 0 else 0
            
            # DRS 區域數量
            drs_zones = self.DRS_ZONES.get(track_name, 2)
            
            difficulty_scores[track_name] = {
                "avg_overtakes": round(avg_overtakes, 2),
                "avg_position_changes": round(avg_position_changes, 2),
                "overtakes_per_lap": round(overtakes_per_lap, 3),
                "drs_zones": drs_zones,
                "race_laps": race_laps,
                "races_analyzed": len(overtakes_list),
            }
        
        # 計算標準化難度指數 (0-1)
        self._calculate_difficulty_index(difficulty_scores)
        
        self.results = difficulty_scores
        return difficulty_scores
    
    def _analyze_race(self, race_path: str) -> Tuple[Optional[int], Optional[int]]:
        """分析單場比賽的超車數據"""
        
        timing_path = os.path.join(race_path, "TimingData.json")
        position_path = os.path.join(race_path, "Position.json")
        
        # 方法 1: 從 Position.json 計算位置變化
        total_position_changes = 0
        total_overtakes = 0
        
        if os.path.exists(position_path):
            try:
                with open(position_path, 'r', encoding='utf-8') as f:
                    pos_data = json.load(f)
                
                records = pos_data.get('records', [])
                
                # 追蹤每位車手的位置變化
                driver_positions = {}  # {driver_num: [positions]}
                
                for rec in records:
                    data = rec.get('data', {})
                    if isinstance(data, dict) and 'Position' in data:
                        positions = data['Position']
                        if isinstance(positions, list):
                            for entry in positions:
                                if isinstance(entry, dict):
                                    driver = entry.get('Racing Number', entry.get('RacingNumber'))
                                    pos = entry.get('Position')
                                    if driver and pos:
                                        if driver not in driver_positions:
                                            driver_positions[driver] = []
                                        driver_positions[driver].append(int(pos))
                
                # 計算位置變化次數 (超車 = 位置提升)
                for driver, positions in driver_positions.items():
                    for i in range(1, len(positions)):
                        if positions[i] < positions[i-1]:  # 位置提升 = 超車
                            total_overtakes += 1
                        if positions[i] != positions[i-1]:  # 任何位置變化
                            total_position_changes += 1
                
            except Exception as e:
                logger.error(f"Position.json 解析錯誤: {e}")
        
        # 方法 2: 從 TimingData.json 補充
        if os.path.exists(timing_path) and total_overtakes == 0:
            try:
                with open(timing_path, 'r', encoding='utf-8') as f:
                    timing_data = json.load(f)
                
                records = timing_data.get('records', [])
                
                # 追蹤位置變化
                driver_last_pos = {}
                
                for rec in records:
                    data = rec.get('data', {})
                    if isinstance(data, dict) and 'Lines' in data:
                        lines = data['Lines']
                        for driver, info in lines.items():
                            if isinstance(info, dict) and 'Position' in info:
                                pos = info['Position']
                                if driver in driver_last_pos:
                                    if pos != driver_last_pos[driver]:
                                        total_position_changes += 1
                                        if int(pos) < int(driver_last_pos[driver]):
                                            total_overtakes += 1
                                driver_last_pos[driver] = pos
                
            except Exception as e:
                logger.error(f"TimingData.json 解析錯誤: {e}")
        
        logger.info(f"  超車次數: {total_overtakes}, 位置變化: {total_position_changes}")
        
        return total_overtakes if total_overtakes > 0 else None, \
               total_position_changes if total_position_changes > 0 else None
    
    def _calculate_difficulty_index(self, scores: Dict):
        """計算標準化難度指數 (0-1, 1=最難超車)"""
        
        # 收集所有超車率
        overtake_rates = [
            s["overtakes_per_lap"] 
            for s in scores.values() 
            if s["overtakes_per_lap"] > 0
        ]
        
        if not overtake_rates:
            return
        
        max_rate = max(overtake_rates)
        min_rate = min(overtake_rates)
        rate_range = max_rate - min_rate if max_rate != min_rate else 1
        
        for track_name, data in scores.items():
            rate = data["overtakes_per_lap"]
            
            # 超車率越高 → 難度越低
            # 標準化到 0-1，然後反轉
            if rate > 0:
                normalized = (rate - min_rate) / rate_range
                difficulty = 1 - normalized  # 反轉: 高超車率 = 低難度
            else:
                difficulty = 0.8  # 無數據時假設中等偏難
            
            # DRS 區域調整 (DRS 越多 → 難度越低)
            drs_factor = 1 - (data["drs_zones"] - 1) * 0.05  # 每多一個 DRS 區 -5%
            
            # 最終難度指數
            final_difficulty = min(1.0, max(0.0, difficulty * drs_factor))
            
            data["difficulty_index"] = round(final_difficulty, 3)
            data["difficulty_category"] = self._categorize_difficulty(final_difficulty)
    
    def _categorize_difficulty(self, index: float) -> str:
        """分類難度等級"""
        if index >= 0.8:
            return "極難超車"
        elif index >= 0.6:
            return "困難"
        elif index >= 0.4:
            return "中等"
        elif index >= 0.2:
            return "容易"
        else:
            return "非常容易"
    
    def save_results(self, output_path: str = "json/track_overtaking_difficulty.json"):
        """保存結果到 JSON"""
        
        output = {
            "metadata": {
                "description": "賽道超車難度指數",
                "calculation_method": "基於 2023-2024 歷史超車數據統計",
                "difficulty_index_range": "0-1 (1=最難超車)",
                "data_sources": ["LiveF1 Position.json", "LiveF1 TimingData.json"],
            },
            "tracks": self.results
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n[SUCCESS] 結果已保存到: {output_path}")
        
        return output_path
    
    def print_summary(self):
        """打印摘要"""
        
        logger.info("\n" + "=" * 60)
        logger.info("賽道超車難度指數 (2023-2024 統計)")
        logger.info("=" * 60)
        
        # 按難度排序
        sorted_tracks = sorted(
            self.results.items(),
            key=lambda x: x[1].get("difficulty_index", 0),
            reverse=True
        )
        
        logger.info(f"{'賽道':<20} {'難度指數':<10} {'等級':<12} {'平均超車':<10} {'DRS區':<6}")
        logger.info("-" * 60)
        
        for track, data in sorted_tracks:
            logger.info(
                f"{track:<20} {data.get('difficulty_index', 0):<10.3f} "
                f"{data.get('difficulty_category', 'N/A'):<12} "
                f"{data.get('avg_overtakes', 0):<10.1f} "
                f"{data.get('drs_zones', 0):<6}"
            )


def main():
    """主函數"""
    
    logger.info("=" * 60)
    logger.info("F1 賽道超車難度計算器")
    logger.info("=" * 60)
    
    # 設定路徑
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "LiveF1")
    
    calculator = OvertakingDifficultyCalculator(base_path)
    
    # 計算所有賽道
    results = calculator.calculate_all(years=["2023", "2024"])
    
    # 打印摘要
    calculator.print_summary()
    
    # 保存結果
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "track_overtaking_difficulty.json")
    calculator.save_results(output_path)
    
    return results


if __name__ == "__main__":
    main()
