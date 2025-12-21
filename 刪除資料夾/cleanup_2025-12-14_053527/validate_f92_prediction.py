#!/usr/bin/env python3
"""
F92 驗證腳本 - 生成 F92 預測 vs 真實圈速比較圖

功能:
    1. 載入 F92 預測結果
    2. 載入真實正賽圈速
    3. 生成多賽事比較圖 (類似 F91 vs Real)
    4. 計算 MAE 準確度

使用:
    python validate_f92_prediction.py

輸出:
    reports/f92_vs_real_comparison.png

日期: 2025-12-13
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# 專案路徑
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 導入 F92 預測器
try:
    from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor
except ImportError:
    # 如果在專案根目錄執行
    sys.path.insert(0, str(PROJECT_ROOT.parent.parent.parent.parent))
    from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_real_race_data(year: int, race: str, driver: str = "VER") -> Optional[List[Dict]]:
    """
    載入真實正賽圈速數據
    
    從 LiveF1 或 FastF1 緩存載入
    """
    project_root = Path(__file__).parent
    livef1_dir = project_root / "json" / "LiveF1" / str(year)
    
    # 嘗試多種命名格式
    possible_names = [
        f"{race}_Race",
        f"{race.replace(' ', '_')}_Race",
        f"{race}ian_Race" if race == "Japan" else None,
    ]
    
    for name in possible_names:
        if name is None:
            continue
        race_path = livef1_dir / name / "TimingData.json"
        if race_path.exists():
            return parse_timing_data(race_path, driver)
    
    # 嘗試從 FastF1 緩存載入
    try:
        import fastf1
        cache_dir = project_root / "cache"
        if cache_dir.exists():
            fastf1.Cache.enable_cache(str(cache_dir))
        
        session = fastf1.get_session(year, race, 'R')
        session.load(laps=True, telemetry=False)  # 禁用 telemetry 以避免錯誤
        
        driver_laps = session.laps.pick_driver(driver)
        lap_data = []
        
        for _, lap in driver_laps.iterrows():
            lap_time = lap['LapTime']
            if pd.notna(lap_time):
                lap_data.append({
                    'lap': int(lap['LapNumber']),
                    'time': lap_time.total_seconds()
                })
        
        return lap_data
    except Exception as e:
        print(f"[WARNING] FastF1 載入失敗: {e}")
        return None


def parse_timing_data(timing_file: Path, driver: str) -> List[Dict]:
    """解析 TimingData.json"""
    lap_data = []
    
    try:
        with open(timing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            for drv, drv_data in data.items():
                if driver.upper() in drv.upper():
                    if isinstance(drv_data, dict) and 'Lines' in drv_data:
                        for lap_num, lap_info in drv_data.get('Lines', {}).items():
                            if isinstance(lap_info, dict):
                                lap_time = lap_info.get('LastLapTime', {})
                                if isinstance(lap_time, dict):
                                    time_str = lap_time.get('Value', '')
                                    parsed = parse_lap_time_string(time_str)
                                    if parsed and 60 < parsed < 180:
                                        lap_data.append({
                                            'lap': int(lap_num),
                                            'time': parsed
                                        })
    except Exception as e:
        print(f"[ERROR] 解析失敗: {e}")
    
    return sorted(lap_data, key=lambda x: x['lap'])


def parse_lap_time_string(time_str: str) -> Optional[float]:
    """解析圈速字串"""
    if not time_str or not isinstance(time_str, str):
        return None
    
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(time_str)
    except:
        return None


def calculate_mae(predicted: List[float], actual: List[float]) -> float:
    """計算 MAE"""
    if len(predicted) != len(actual):
        min_len = min(len(predicted), len(actual))
        predicted = predicted[:min_len]
        actual = actual[:min_len]
    
    return np.mean(np.abs(np.array(predicted) - np.array(actual)))


def generate_comparison_chart(races: List[Dict], output_path: Path,
                               title: str = "F92 預測 vs 真實圈速對比"):
    """
    生成多賽事比較圖
    
    races 格式:
    [
        {
            "name": "日本站",
            "year": 2025,
            "race": "Japan",
            "predicted": [...],
            "actual": [...],
            "mae": 1.5
        }
    ]
    """
    n_races = len(races)
    fig, axes = plt.subplots(1, n_races, figsize=(6 * n_races, 5))
    
    if n_races == 1:
        axes = [axes]
    
    for idx, race_data in enumerate(races):
        ax = axes[idx]
        
        name = race_data['name']
        predicted = race_data['predicted']
        actual = race_data['actual']
        mae = race_data['mae']
        
        # 對齊長度
        min_len = min(len(predicted), len(actual))
        laps = list(range(3, 3 + min_len))
        predicted = predicted[:min_len]
        actual = actual[:min_len]
        
        # 繪製曲線
        ax.plot(laps, actual, 'b-o', markersize=3, linewidth=1.5, 
                label='真實圈速', alpha=0.8)
        ax.plot(laps, predicted, 'r--s', markersize=3, linewidth=1.5,
                label=f'F92 預測 (MAE={mae:.3f}s)', alpha=0.8)
        
        # 平均線
        actual_mean = np.mean(actual)
        pred_mean = np.mean(predicted)
        ax.axhline(y=actual_mean, color='blue', linestyle=':', alpha=0.5,
                   label=f'真實平均: {actual_mean:.3f}s')
        ax.axhline(y=pred_mean, color='red', linestyle=':', alpha=0.5,
                   label=f'預測平均: {pred_mean:.3f}s')
        
        # 標題和標籤
        ax.set_title(f"{name}\nVER 圈速對比 ({len(laps)} 圈)", fontsize=12)
        ax.set_xlabel('圈數')
        ax.set_ylabel('圈速 (秒)')
        ax.legend(fontsize=8, loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Y 軸範圍
        all_times = actual + predicted
        y_min = min(all_times) - 2
        y_max = max(all_times) + 2
        ax.set_ylim(y_min, y_max)
    
    # 總標題
    year = races[0]['year'] if races else 2025
    fig.suptitle(f"F92 預測 vs 真實圈速對比 ({year} 賽季 - VER)", fontsize=14, y=1.02)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n圖表已保存: {output_path}")
    plt.close()


def run_validation(races_to_validate: List[Dict], driver: str = "VER"):
    """
    執行驗證
    
    races_to_validate 格式:
    [
        {"year": 2025, "race": "Japan", "name": "日本站", "total_laps": 53, "base_time": 92.9},
        {"year": 2025, "race": "Abu Dhabi", "name": "阿布達比站", "total_laps": 56, "base_time": 89.0},
    ]
    """
    predictor = F92HybridPredictor(verbose=True)
    
    results = []
    
    for race_info in races_to_validate:
        year = race_info['year']
        race = race_info['race']
        name = race_info['name']
        total_laps = race_info.get('total_laps', 53)
        base_time = race_info.get('base_time')
        
        print(f"\n{'='*60}")
        print(f"驗證: {year} {race}")
        print(f"{'='*60}")
        
        # 載入真實數據
        real_data = load_real_race_data(year, race, driver)
        if real_data is None or len(real_data) < 10:
            print(f"[跳過] 無法載入真實數據")
            continue
        
        # 從真實數據計算 base_time (前3圈中位數)
        first_3 = [d['time'] for d in real_data if d['lap'] <= 3]
        if first_3 and base_time is None:
            base_time = np.median(first_3)
        
        # F92 預測
        prediction = predictor.predict(
            year=year,
            race=race,
            driver=driver,
            compound="MEDIUM",  # 假設主要使用 MEDIUM
            total_laps=total_laps,
            base_time=base_time,
            use_ml=True
        )
        
        # 提取預測圈速
        pred_times = [p['predicted_time'] for p in prediction['predictions']]
        
        # 對齊真實數據 (從第3圈開始)
        actual_times = [d['time'] for d in real_data if d['lap'] >= 3]
        
        # 計算 MAE
        min_len = min(len(pred_times), len(actual_times))
        mae = calculate_mae(pred_times[:min_len], actual_times[:min_len])
        
        print(f"\n結果:")
        print(f"  預測圈數: {len(pred_times)}")
        print(f"  真實圈數: {len(actual_times)}")
        print(f"  MAE: {mae:.3f}s")
        
        results.append({
            "name": name,
            "year": year,
            "race": race,
            "predicted": pred_times,
            "actual": actual_times[:min_len],
            "mae": mae,
            "base_time": base_time
        })
    
    # 生成比較圖
    if results:
        project_root = Path(__file__).parent
        output_path = project_root / "reports" / f"f92_vs_real_{len(results)}_races_comparison.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        generate_comparison_chart(results, output_path)
        
        # 輸出總結
        print(f"\n{'='*60}")
        print("驗證總結")
        print(f"{'='*60}")
        total_mae = np.mean([r['mae'] for r in results])
        for r in results:
            print(f"  {r['name']}: MAE = {r['mae']:.3f}s")
        print(f"\n  平均 MAE: {total_mae:.3f}s")
    
    return results


def main():
    """主程式"""
    # 要驗證的賽事
    races_to_validate = [
        {"year": 2025, "race": "Japan", "name": "日本站 (鈴鹿)", "total_laps": 53, "base_time": None},
        {"year": 2025, "race": "Abu Dhabi", "name": "阿布達比站", "total_laps": 56, "base_time": None},
        {"year": 2025, "race": "Mexico", "name": "墨西哥站", "total_laps": 56, "base_time": None},
    ]
    
    results = run_validation(races_to_validate, driver="VER")
    
    return results


if __name__ == "__main__":
    main()
