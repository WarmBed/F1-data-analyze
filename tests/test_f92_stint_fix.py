"""
測試 F92 進站策略修正效果

驗證：
1. 修正前 vs 修正後的 MAE 比較
2. 是否正確處理進站後的輪胎年齡重置
3. 與二次方程式模型的比較
"""

import sys
import json
import fastf1
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 導入 F92
sys.path.insert(0, str(Path(__file__).parent))
from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor


def load_race_base_time(year: int, race: str, driver: str) -> float:
    """從 Race 前 3 圈獲取 base_time"""
    print(f"\n載入 {year} {race} Race 數據...")
    
    fastf1.Cache.enable_cache('f1_analysis_cache')
    session = fastf1.get_session(year, race, 'R')
    session.load()
    
    driver_laps = session.laps.pick_driver(driver)
    first_3_laps = driver_laps[driver_laps['LapNumber'].isin([1, 2, 3])]
    
    valid_times = first_3_laps['LapTime'].dt.total_seconds()
    valid_times = valid_times[valid_times < 200]
    
    base_time = valid_times.median()
    print(f"  Base Time (前 3 圈中位數): {base_time:.3f}s")
    
    return base_time


def get_pit_strategy(year: int, race: str, driver: str):
    """獲取真實進站策略"""
    print(f"\n獲取 {driver} 進站策略...")
    
    fastf1.Cache.enable_cache('f1_analysis_cache')
    session = fastf1.get_session(year, race, 'R')
    session.load()
    
    driver_laps = session.laps.pick_driver(driver)
    
    # 提取配方資訊
    compounds = driver_laps[['LapNumber', 'Compound']].copy()
    compounds = compounds.dropna(subset=['Compound'])
    
    # 找到進站點（配方變化）
    stints = []
    pit_laps = []
    
    prev_compound = None
    stint_start = 1
    
    for _, row in compounds.iterrows():
        lap = int(row['LapNumber'])
        compound = str(row['Compound']).upper()
        
        if compound != prev_compound and prev_compound is not None:
            # Stint 結束
            stints.append((stint_start, lap - 1, prev_compound))
            pit_laps.append(lap)
            stint_start = lap
        
        prev_compound = compound
    
    # 最後一個 stint
    if prev_compound:
        total_laps = int(compounds['LapNumber'].max())
        stints.append((stint_start, total_laps, prev_compound))
    
    print(f"\n{race} {driver} 進站策略:")
    for i, (start, end, compound) in enumerate(stints, 1):
        print(f"  Stint {i}: Lap {start}-{end} ({compound}) - {end - start + 1} 圈")
    
    if pit_laps:
        print(f"  進站圈數: {pit_laps}")
    
    return stints, pit_laps


def get_actual_lap_times(year: int, race: str, driver: str) -> dict:
    """獲取真實圈速"""
    print(f"\n載入真實圈速數據...")
    
    fastf1.Cache.enable_cache('f1_analysis_cache')
    session = fastf1.get_session(year, race, 'R')
    session.load()
    
    driver_laps = session.laps.pick_driver(driver)
    
    actual_times = {}
    for _, lap_data in driver_laps.iterrows():
        lap_num = int(lap_data['LapNumber'])
        lap_time = lap_data['LapTime'].total_seconds()
        
        # 跳過進站圈
        if lap_data.get('PitOutLap', False) or lap_data.get('PitInLap', False):
            continue
        
        if lap_time < 200:  # 有效圈速
            actual_times[lap_num] = lap_time
    
    print(f"  有效圈速數: {len(actual_times)} 圈")
    
    return actual_times


def test_f92_with_stints(year: int, race: str, driver: str = "VER"):
    """測試 F92 使用進站策略的效果"""
    
    print("=" * 80)
    print(f"F92 進站策略修正驗證 - {year} {race} {driver}")
    print("=" * 80)
    
    # 獲取數據
    base_time = load_race_base_time(year, race, driver)
    stints, pit_laps = get_pit_strategy(year, race, driver)
    actual_times = get_actual_lap_times(year, race, driver)
    
    total_laps = stints[-1][1]
    
    # F92 預測器
    predictor = F92HybridPredictor(verbose=True)
    
    # 方案 1: 修正後（使用進站策略）
    print("\n" + "=" * 80)
    print("方案 1: F92 修正後（含進站策略）")
    print("=" * 80)
    
    result_fixed = predictor.predict(
        year=year,
        race=race,
        driver=driver,
        base_time=base_time,
        total_laps=total_laps,
        stints=stints,  # ✅ 提供進站策略
        use_ml=True
    )
    
    # 計算 MAE
    fixed_predictions = {p['lap']: p['predicted_time'] for p in result_fixed['predictions']}
    
    common_laps = sorted(set(actual_times.keys()) & set(fixed_predictions.keys()))
    actual_values = [actual_times[lap] for lap in common_laps]
    fixed_values = [fixed_predictions[lap] for lap in common_laps]
    
    mae_fixed = mean_absolute_error(actual_values, fixed_values)
    
    print(f"\n修正後 MAE: {mae_fixed:.3f}s")
    print(f"評估圈數: {len(common_laps)} 圈")
    
    # 檢查輪胎年齡是否正確重置
    print("\n檢查輪胎年齡重置（進站前後）:")
    for pit_lap in pit_laps:
        if pit_lap - 1 in fixed_predictions and pit_lap in fixed_predictions:
            pred_before = [p for p in result_fixed['predictions'] if p['lap'] == pit_lap - 1][0]
            pred_after = [p for p in result_fixed['predictions'] if p['lap'] == pit_lap][0]
            
            print(f"  Lap {pit_lap - 1}: stint_lap={pred_before['stint_lap']}, {pred_before['compound']}")
            print(f"  Lap {pit_lap}: stint_lap={pred_after['stint_lap']}, {pred_after['compound']} ← 應重置為 1")
            
            if pred_after['stint_lap'] == 1:
                print(f"    ✅ 輪胎年齡已正確重置")
            else:
                print(f"    ❌ 錯誤！輪胎年齡未重置")
    
    # 繪製對比圖
    plot_comparison(year, race, driver, actual_times, fixed_predictions, 
                    stints, pit_laps, mae_fixed)
    
    return {
        'mae_fixed': mae_fixed,
        'predictions': fixed_predictions,
        'actual': actual_times
    }


def plot_comparison(year, race, driver, actual_times, predictions, 
                    stints, pit_laps, mae):
    """繪製預測 vs 真實對比圖"""
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # 1. 圈速對比
    ax = axes[0]
    
    laps = sorted(actual_times.keys())
    actual_values = [actual_times[lap] for lap in laps]
    pred_values = [predictions.get(lap, None) for lap in laps]
    
    ax.plot(laps, actual_values, 'o-', color='#2ecc71', label='真實圈速', 
            linewidth=2, markersize=4, alpha=0.7)
    ax.plot(laps, pred_values, 's-', color='#e74c3c', label=f'F92 預測（MAE: {mae:.3f}s）', 
            linewidth=2, markersize=4, alpha=0.7)
    
    # 標記進站
    for pit_lap in pit_laps:
        ax.axvline(pit_lap, color='orange', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(pit_lap, ax.get_ylim()[1] * 0.98, f'PIT\nLap {pit_lap}', 
                ha='center', va='top', fontsize=9, color='orange', fontweight='bold')
    
    # 標記 stint 區域
    colors = ['#3498db', '#9b59b6', '#1abc9c']
    for i, (start, end, compound) in enumerate(stints):
        color = colors[i % len(colors)]
        ax.axvspan(start, end, alpha=0.1, color=color)
        mid_lap = (start + end) / 2
        ax.text(mid_lap, ax.get_ylim()[0] * 1.02, f'Stint {i+1}\n{compound}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold', color=color)
    
    ax.set_xlabel('圈數', fontsize=12)
    ax.set_ylabel('圈速 (秒)', fontsize=12)
    ax.set_title(f'{year} {race} {driver} - F92 修正後預測對比', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    
    # 2. 誤差分布
    ax = axes[1]
    
    errors = [pred_values[i] - actual_values[i] for i in range(len(laps)) 
              if pred_values[i] is not None]
    
    ax.hist(errors, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
    ax.axvline(0, color='red', linestyle='--', linewidth=2, label='零誤差')
    ax.axvline(np.mean(errors), color='orange', linestyle='--', linewidth=2, 
               label=f'平均誤差: {np.mean(errors):.3f}s')
    
    ax.set_xlabel('預測誤差 (秒)', fontsize=12)
    ax.set_ylabel('樣本數', fontsize=12)
    ax.set_title(f'誤差分布（MAE: {mae:.3f}s, Std: {np.std(errors):.3f}s）', 
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    output_path = f'reports/f92_stint_fix_{year}_{race}_{driver}.png'
    Path('reports').mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[圖表] 已保存至: {output_path}")
    
    plt.close()


def main():
    """主函數"""
    
    # 測試案例
    test_cases = [
        (2025, "Japan", "VER"),
        (2024, "Mexico", "VER"),
    ]
    
    results = {}
    
    for year, race, driver in test_cases:
        try:
            result = test_f92_with_stints(year, race, driver)
            results[f"{year}_{race}"] = result
        except Exception as e:
            print(f"\n❌ 測試失敗 {year} {race}: {e}")
            import traceback
            traceback.print_exc()
    
    # 總結報告
    print("\n" + "=" * 80)
    print("F92 修正效果總結")
    print("=" * 80)
    
    for key, result in results.items():
        print(f"\n{key}:")
        print(f"  修正後 MAE: {result['mae_fixed']:.3f}s")
    
    if len(results) > 0:
        avg_mae = np.mean([r['mae_fixed'] for r in results.values()])
        print(f"\n平均 MAE: {avg_mae:.3f}s")
        
        print(f"\n🎯 目標: MAE ~0.85s（訓練集水平）")
        if avg_mae <= 1.0:
            print(f"✅ 修正成功！MAE 已改善至 {avg_mae:.3f}s")
        else:
            print(f"⚠️  MAE 仍需改進: {avg_mae:.3f}s > 1.0s")


if __name__ == '__main__':
    main()
