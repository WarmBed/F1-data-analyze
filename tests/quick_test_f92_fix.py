"""
快速測試 F92 修正效果 - 僅 Japan 2025
"""

import sys
import fastf1
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error

sys.path.insert(0, str(Path(__file__).parent))
from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor


def quick_test_japan():
    """快速測試 Japan 2025"""
    
    print("=" * 80)
    print("F92 修正驗證 - 2025 Japan VER")
    print("=" * 80)
    
    # 載入數據
    fastf1.Cache.enable_cache('f1_analysis_cache')
    session = fastf1.get_session(2025, "Japan", 'R')
    session.load()
    
    driver_laps = session.laps.pick_driver("VER")
    
    # Base time
    first_3 = driver_laps[driver_laps['LapNumber'].isin([1, 2, 3])]
    base_time = first_3['LapTime'].dt.total_seconds().median()
    
    # 進站策略
    stints = [(1, 21, "MEDIUM"), (22, 53, "HARD")]
    
    # 真實圈速
    actual_times = {}
    for _, lap in driver_laps.iterrows():
        lap_num = int(lap['LapNumber'])
        if lap.get('PitOutLap', False) or lap.get('PitInLap', False):
            continue
        lap_time = lap['LapTime'].total_seconds()
        if lap_time < 200:
            actual_times[lap_num] = lap_time
    
    # F92 預測
    predictor = F92HybridPredictor(verbose=False)
    result = predictor.predict(
        year=2025,
        race="Japan",
        driver="VER",
        base_time=base_time,
        total_laps=53,
        stints=stints,
        use_ml=True
    )
    
    # 計算 MAE
    predictions = {p['lap']: p['predicted_time'] for p in result['predictions']}
    common_laps = sorted(set(actual_times.keys()) & set(predictions.keys()))
    
    actual_values = [actual_times[lap] for lap in common_laps]
    pred_values = [predictions[lap] for lap in common_laps]
    
    mae = mean_absolute_error(actual_values, pred_values)
    
    print(f"\n✅ 測試完成!")
    print(f"   Base Time: {base_time:.3f}s")
    print(f"   進站策略: 2 個 stint (MEDIUM 1-21, HARD 22-53)")
    print(f"   評估圈數: {len(common_laps)} 圈")
    print(f"   MAE: {mae:.3f}s")
    
    # 檢查進站後輪胎年齡重置
    lap21 = [p for p in result['predictions'] if p['lap'] == 21][0]
    lap22 = [p for p in result['predictions'] if p['lap'] == 22][0]
    
    print(f"\n檢查進站重置:")
    print(f"   Lap 21: stint_lap={lap21['stint_lap']}, {lap21['compound']}")
    print(f"   Lap 22: stint_lap={lap22['stint_lap']}, {lap22['compound']}")
    
    if lap22['stint_lap'] == 1:
        print(f"   ✅ 輪胎年齡已正確重置")
    else:
        print(f"   ❌ 錯誤！輪胎年齡={lap22['stint_lap']}，應該是 1")
    
    print(f"\n🎯 修正目標: MAE ~0.85s")
    if mae <= 1.0:
        print(f"   ✅ 成功！MAE {mae:.3f}s <= 1.0s")
    elif mae <= 1.5:
        print(f"   ⚠️  改善中，MAE {mae:.3f}s")
    else:
        print(f"   ❌ 需要進一步優化，MAE {mae:.3f}s")
    
    return mae


if __name__ == '__main__':
    quick_test_japan()
