"""
測試墨西哥站 F92 修正效果
"""

import sys
import fastf1
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error

sys.path.insert(0, str(Path(__file__).parent))
from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor
from smart_base_time_extractor import extract_base_time_robust


def test_mexico():
    """測試 Mexico 2024"""
    
    print("=" * 80)
    print("F92 修正驗證 - 2024 Mexico VER")
    print("=" * 80)
    
    # 使用智能 base_time 提取（自動過濾 SC）
    base_time, info = extract_base_time_robust(2024, "Mexico", "VER")
    print(f"\n✅ 智能提取 base_time: {base_time:.3f}s")
    print(f"   移除 SC 圈: {info['sc_laps_removed']}")
    print(f"   使用樣本: {info['sample_count']} 圈")
    
    # 載入數據
    fastf1.Cache.enable_cache('f1_analysis_cache')
    session = fastf1.get_session(2024, "Mexico", 'R')
    session.load()
    
    driver_laps = session.laps.pick_driver("VER")
    
    # 獲取進站策略
    compounds = driver_laps[['LapNumber', 'Compound']].copy()
    compounds = compounds.dropna(subset=['Compound'])
    
    stints = []
    prev_compound = None
    stint_start = 1
    
    for _, row in compounds.iterrows():
        lap = int(row['LapNumber'])
        compound = str(row['Compound']).upper()
        
        if compound != prev_compound and prev_compound is not None:
            stints.append((stint_start, lap - 1, prev_compound))
            stint_start = lap
        
        prev_compound = compound
    
    if prev_compound:
        total_laps = int(compounds['LapNumber'].max())
        stints.append((stint_start, total_laps, prev_compound))
    
    print("\n進站策略:")
    for i, (start, end, compound) in enumerate(stints, 1):
        print(f"  Stint {i}: Lap {start}-{end} ({compound}) - {end - start + 1} 圈")
    
    # 真實圈速
    actual_times = {}
    for _, lap in driver_laps.iterrows():
        lap_num = int(lap['LapNumber'])
        if lap.get('PitOutLap', False) or lap.get('PitInLap', False):
            continue
        lap_time = lap['LapTime'].total_seconds()
        if lap_time < 200:
            actual_times[lap_num] = lap_time
    
    print(f"有效圈速數: {len(actual_times)} 圈")
    
    # F92 預測（修正後）
    print("\n執行 F92 預測...")
    predictor = F92HybridPredictor(verbose=True)
    result = predictor.predict(
        year=2024,
        race="Mexico",
        driver="VER",
        base_time=base_time,
        total_laps=total_laps,
        stints=stints,
        use_ml=True
    )
    
    # 計算 MAE
    predictions = {p['lap']: p['predicted_time'] for p in result['predictions']}
    common_laps = sorted(set(actual_times.keys()) & set(predictions.keys()))
    
    actual_values = [actual_times[lap] for lap in common_laps]
    pred_values = [predictions[lap] for lap in common_laps]
    
    mae = mean_absolute_error(actual_values, pred_values)
    
    print(f"\n" + "=" * 80)
    print("測試結果")
    print("=" * 80)
    print(f"評估圈數: {len(common_laps)} 圈")
    print(f"MAE: {mae:.3f}s")
    
    # 檢查進站後輪胎年齡重置
    print("\n檢查進站重置:")
    for i in range(len(stints) - 1):
        stint1_end = stints[i][1]
        stint2_start = stints[i + 1][0]
        
        if stint1_end in predictions and stint2_start in predictions:
            lap_before = [p for p in result['predictions'] if p['lap'] == stint1_end][0]
            lap_after = [p for p in result['predictions'] if p['lap'] == stint2_start][0]
            
            print(f"  Lap {stint1_end}: stint_lap={lap_before['stint_lap']}, {lap_before['compound']}")
            print(f"  Lap {stint2_start}: stint_lap={lap_after['stint_lap']}, {lap_after['compound']}")
            
            if lap_after['stint_lap'] == 1:
                print(f"    ✅ 輪胎年齡已正確重置")
            else:
                print(f"    ❌ 錯誤！輪胎年齡={lap_after['stint_lap']}，應該是 1")
    
    # 與之前的二次方程式比較
    print(f"\n對比二次方程式模型:")
    print(f"  二次方程式 MAE: 1.294s（之前測試）")
    print(f"  F92 修正後 MAE: {mae:.3f}s")
    
    if mae < 1.294:
        improvement = (1.294 - mae) / 1.294 * 100
        print(f"  ✅ F92 贏了！改善 {improvement:.1f}%")
    else:
        degradation = (mae - 1.294) / 1.294 * 100
        print(f"  ❌ F92 輸了！差距 {degradation:.1f}%")
    
    # 分析誤差分布
    errors = [pred_values[i] - actual_values[i] for i in range(len(common_laps))]
    
    print(f"\n誤差分析:")
    print(f"  平均誤差: {np.mean(errors):.3f}s")
    print(f"  標準差: {np.std(errors):.3f}s")
    print(f"  最大正誤差: {np.max(errors):.3f}s")
    print(f"  最大負誤差: {np.min(errors):.3f}s")
    
    # 找出誤差最大的圈
    max_error_idx = np.argmax(np.abs(errors))
    max_error_lap = common_laps[max_error_idx]
    max_error_actual = actual_values[max_error_idx]
    max_error_pred = pred_values[max_error_idx]
    
    print(f"\n最大誤差圈:")
    print(f"  Lap {max_error_lap}: 真實={max_error_actual:.3f}s, 預測={max_error_pred:.3f}s, 誤差={errors[max_error_idx]:.3f}s")
    
    return mae


if __name__ == '__main__':
    test_mexico()
