#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
勝率預測詳細診斷 - 生成每場比賽每圈的完整數據供 LLM 分析

此工具生成結構化的比賽數據報告，讓 LLM 能夠：
1. 看到每圈的位置變化
2. 比對預測 vs 實際結果
3. 識別預測失準的具體情境

使用方法：
    python tools/generate_race_analysis_for_llm.py

輸出：
    reports/race_analysis_for_llm/
    ├── 2024_Qatar.md
    ├── 2024_Las_Vegas.md
    └── ...

作者: F1T Dev Team
日期: 2025-12-05
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

# 添加專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class DriverRaceData:
    """單一車手的比賽數據"""
    driver_code: str
    starting_position: int   # 改用第1圈位置
    final_position: int
    lap_positions: List[int]  # 每圈位置
    lap_gaps: List[float]     # 每圈與領先者差距
    tyre_compounds: List[str] # 每圈輪胎
    tyre_ages: List[int]      # 每圈輪胎年齡
    pit_laps: List[int]       # 進站圈數
    
    @property
    def position_change(self) -> int:
        """起跑到結束的位置變化"""
        return self.starting_position - self.final_position
    
    @property
    def is_dnf(self) -> bool:
        """是否 DNF"""
        return self.final_position >= 20


class RaceAnalysisGenerator:
    """比賽分析報告生成器"""
    
    TYRE_NAMES = {
        1: "SOFT",
        2: "MEDIUM",
        3: "HARD",
        4: "INTER",
        5: "WET",
    }
    
    def __init__(self, training_data_path: str = None):
        self.training_data_path = training_data_path or str(
            PROJECT_ROOT / "data" / "live_win_probability" / "training_data.csv"
        )
        self.df: pd.DataFrame = None
        self.output_dir = PROJECT_ROOT / "reports" / "race_analysis_for_llm"
        
    def load_data(self) -> bool:
        """載入數據"""
        try:
            self.df = pd.read_csv(self.training_data_path)
            print(f"[OK] 載入 {len(self.df)} 筆數據")
            print(f"    比賽: {self.df['race_name'].nunique()} 場")
            return True
        except Exception as e:
            print(f"[ERROR] {e}")
            return False
    
    def get_race_list(self) -> List[tuple]:
        """取得所有比賽列表"""
        races = self.df.groupby(['year', 'race_name']).size().reset_index()
        return [(int(r['year']), r['race_name']) for _, r in races.iterrows()]
    
    def extract_race_data(self, year: int, race_name: str) -> Dict[str, DriverRaceData]:
        """提取單場比賽的所有車手數據"""
        race_df = self.df[(self.df['year'] == year) & (self.df['race_name'] == race_name)]
        
        if race_df.empty:
            return {}
        
        drivers_data = {}
        
        for driver_code in race_df['driver_code'].unique():
            driver_df = race_df[race_df['driver_code'] == driver_code].sort_values('current_lap')
            
            # 提取每圈數據
            lap_positions = driver_df['position'].tolist()
            lap_gaps = driver_df['gap_to_leader'].tolist()
            tyre_compounds = [self.TYRE_NAMES.get(int(t), "?") for t in driver_df['tyre_compound']]
            tyre_ages = driver_df['tyre_age'].tolist()
            
            # 偵測進站圈 (輪胎年齡重置)
            pit_laps = []
            for i in range(1, len(tyre_ages)):
                if tyre_ages[i] < tyre_ages[i-1]:
                    pit_laps.append(driver_df.iloc[i]['current_lap'])
            
            drivers_data[driver_code] = DriverRaceData(
                driver_code=driver_code,
                starting_position=int(lap_positions[0]) if lap_positions else 10,  # 用第1圈位置
                final_position=int(driver_df.iloc[0]['final_position']),
                lap_positions=lap_positions,
                lap_gaps=lap_gaps,
                tyre_compounds=tyre_compounds,
                tyre_ages=tyre_ages,
                pit_laps=pit_laps,
            )
        
        return drivers_data
    
    def generate_race_report(self, year: int, race_name: str) -> str:
        """生成單場比賽的詳細報告"""
        drivers_data = self.extract_race_data(year, race_name)
        
        if not drivers_data:
            return f"# {year} {race_name}\n\n無數據"
        
        # 取得總圈數
        sample_driver = list(drivers_data.values())[0]
        total_laps = len(sample_driver.lap_positions)
        
        report = f"""# {year} {race_name} - 比賽分析報告

## 比賽概覽
- 總圈數: {total_laps}
- 參賽車手: {len(drivers_data)}

## 最終結果 vs 起跑位置

| 名次 | 車手 | 起跑 | 最終位置 | 變動 | 狀態 |
|------|------|------|----------|------|------|
"""
        # 按最終位置排序
        sorted_drivers = sorted(drivers_data.values(), key=lambda x: x.final_position)
        
        for d in sorted_drivers:
            change = d.position_change
            change_str = f"+{change}" if change > 0 else str(change)
            status = "DNF" if d.is_dnf else "完賽"
            report += f"| P{d.final_position} | {d.driver_code} | P{d.starting_position} | P{d.final_position} | {change_str} | {status} |\n"
        
        # 每 10 圈的位置快照
        report += f"""

## 位置變化追蹤 (每 10 圈)

"""
        snapshot_laps = list(range(1, total_laps + 1, 10))
        if total_laps not in snapshot_laps:
            snapshot_laps.append(total_laps)
        
        # 表頭
        header = "| 車手 | L1 |"
        for lap in snapshot_laps:
            header += f" L{lap} |"
        header += " 最終 |"
        report += header + "\n"
        
        separator = "|------|------|"
        for _ in snapshot_laps:
            separator += "------|"
        separator += "------|"
        report += separator + "\n"
        
        # 每位車手
        for d in sorted_drivers[:15]:  # 只顯示前 15 位
            row = f"| {d.driver_code} | P{d.starting_position} |"
            for lap in snapshot_laps:
                idx = lap - 1
                if idx < len(d.lap_positions):
                    row += f" P{d.lap_positions[idx]} |"
                else:
                    row += " - |"
            row += f" P{d.final_position} |"
            report += row + "\n"
        
        # 關鍵事件分析
        report += f"""

## 關鍵位置變化

"""
        # 找出位置變化最大的車手
        big_movers = sorted(drivers_data.values(), key=lambda x: abs(x.position_change), reverse=True)[:5]
        
        for d in big_movers:
            if d.position_change != 0:
                direction = "上升" if d.position_change > 0 else "下降"
                report += f"- **{d.driver_code}**: L1 P{d.starting_position} → 最終 P{d.final_position} ({direction} {abs(d.position_change)} 位)\n"
                
                # 進站策略
                if d.pit_laps:
                    report += f"  - 進站圈: {d.pit_laps}\n"
                
                # 分析位置變化趨勢
                if len(d.lap_positions) > 10:
                    early_avg = np.mean(d.lap_positions[:10])
                    late_avg = np.mean(d.lap_positions[-10:])
                    if early_avg != late_avg:
                        trend = "前段較好" if early_avg < late_avg else "後段較好"
                        report += f"  - 趨勢: {trend}\n"
        
        # 進站策略分析
        report += f"""

## 進站策略分析

| 車手 | 進站次數 | 進站圈數 | 輪胎使用 |
|------|----------|----------|----------|
"""
        for d in sorted_drivers[:15]:
            pit_count = len(d.pit_laps)
            pit_laps_str = ", ".join(map(str, d.pit_laps)) if d.pit_laps else "-"
            
            # 輪胎使用統計
            tyre_usage = {}
            for t in d.tyre_compounds:
                tyre_usage[t] = tyre_usage.get(t, 0) + 1
            tyre_str = ", ".join([f"{k}({v}圈)" for k, v in sorted(tyre_usage.items(), key=lambda x: -x[1])])
            
            report += f"| {d.driver_code} | {pit_count} | {pit_laps_str} | {tyre_str} |\n"
        
        # 與領先者差距分析
        report += f"""

## 差距變化分析 (與領先者)

| 車手 | 第1圈 | 第{total_laps//4}圈 | 第{total_laps//2}圈 | 第{total_laps*3//4}圈 | 最後圈 |
|------|-------|--------|--------|---------|--------|
"""
        gap_laps = [1, total_laps//4, total_laps//2, total_laps*3//4, total_laps]
        
        for d in sorted_drivers[:10]:
            row = f"| {d.driver_code} |"
            for lap in gap_laps:
                idx = lap - 1
                if idx < len(d.lap_gaps):
                    gap = d.lap_gaps[idx]
                    row += f" {gap:.1f}s |"
                else:
                    row += " - |"
            report += row + "\n"
        
        # LLM 分析提示
        report += f"""

---

## 請分析這場比賽並回答:

1. **預測困難點**: 哪些車手的最終位置最難預測？為什麼？

2. **關鍵轉折點**: 哪些圈數發生了重大位置變化？可能原因是什麼？

3. **策略影響**: 進站策略如何影響最終結果？

4. **模型建議**: 根據這場比賽，預測模型應該加入什麼因素？

5. **權重調整**: 這場比賽的特性（{race_name}）是否需要特別的預測權重？
"""
        
        return report
    
    def generate_all_reports(self, max_races: int = None):
        """生成所有比賽的報告"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        races = self.get_race_list()
        if max_races:
            races = races[:max_races]
        
        print(f"\n[生成中] {len(races)} 場比賽報告...")
        
        for year, race_name in races:
            report = self.generate_race_report(year, race_name)
            
            # 儲存
            filename = f"{year}_{race_name}.md"
            filepath = self.output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"    [OK] {filename}")
        
        # 生成索引
        self._generate_index(races)
        
        print(f"\n[完成] 報告已儲存至: {self.output_dir}")
    
    def _generate_index(self, races: List[tuple]):
        """生成索引頁面"""
        index = """# F1 比賽分析報告索引

這些報告包含每場比賽的詳細數據，供 LLM 分析預測模型的改進方向。

## 使用方法

1. 選擇一場比賽報告
2. 將內容貼給 Claude/GPT
3. 請 LLM 分析並給出改進建議

## 比賽列表

| 年份 | 比賽 | 報告連結 |
|------|------|----------|
"""
        for year, race_name in races:
            filename = f"{year}_{race_name}.md"
            index += f"| {year} | {race_name} | [{filename}](./{filename}) |\n"
        
        index += """

## 問題範例

您可以這樣問 LLM：

1. "請分析這場比賽，告訴我預測模型哪裡需要改進"
2. "為什麼 XXX 車手的位置變化這麼大？模型應該如何處理這種情況？"
3. "這場比賽的進站策略對結果影響多大？"
4. "根據多場比賽的分析，你認為模型最需要加入什麼特徵？"
"""
        
        with open(self.output_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(index)


def main():
    print("=" * 60)
    print("F1 比賽分析報告生成器 (供 LLM 分析)")
    print("=" * 60)
    
    generator = RaceAnalysisGenerator()
    
    if not generator.load_data():
        return
    
    # 生成所有報告
    generator.generate_all_reports()
    
    print("\n" + "=" * 60)
    print("下一步")
    print("=" * 60)
    print("1. 前往 reports/race_analysis_for_llm/")
    print("2. 選擇一場比賽報告 (例如 2024_Qatar.md)")
    print("3. 將內容貼給 Claude 並請它分析")
    print("4. 收集多場比賽的分析結果，找出共同模式")


if __name__ == "__main__":
    main()
