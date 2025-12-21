#!/usr/bin/env python3
"""
測試 F92 修正後的邏輯 vs DriverStrategy 二次方程式
- F92: base_time 從 Race 前3圈獲取 + FP2 校正 + ML 殘差
- DriverStrategy: 二次方程式輪胎衰退模型（LiveTiming 使用）
"""

import fastf1
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

def load_race_base_time(year: int, race: str, driver: str = "VER") -> float:
    """從 Race 前3圈獲取 base_time（中位數）"""
    print(f"\n{'='*60}")
    print(f"載入 Race 前3圈數據: {year} {race}")
    print(f"{'='*60}")
    
    session = fastf1.get_session(year, race, 'R')
    session.load(laps=True, telemetry=False)
    
    # 獲取車手的前3圈
    driver_laps = session.laps.pick_drivers(driver)
    first_3_laps = driver_laps[driver_laps['LapNumber'] <= 3]
    
    # 過濾有效圈速
    valid_laps = first_3_laps[first_3_laps['LapTime'].notna()]
    lap_times = valid_laps['LapTime'].dt.total_seconds().tolist()
    
    if not lap_times:
        raise ValueError(f"找不到 {driver} 的前3圈有效圈速")
    
    base_time = np.median(lap_times)
    print(f"  車手: {driver}")
    print(f"  前3圈圈速: {[f'{t:.3f}s' for t in lap_times]}")
    print(f"  base_time (中位數): {base_time:.3f}s")
    
    return base_time


def load_real_race_data(year: int, race: str, driver: str = "VER"):
    """載入真實正賽數據"""
    session = fastf1.get_session(year, race, 'R')
    session.load(laps=True, telemetry=False)
    
    driver_laps = session.laps.pick_drivers(driver)
    valid_laps = driver_laps[driver_laps['LapTime'].notna()].copy()
    
    lap_numbers = valid_laps['LapNumber'].tolist()
    lap_times = valid_laps['LapTime'].dt.total_seconds().tolist()
    
    return lap_numbers, lap_times


def get_pit_strategy(year: int, race: str, driver: str = "VER"):
    """獲取真實進站策略"""
    session = fastf1.get_session(year, race, 'R')
    session.load(laps=True, telemetry=False)
    
    driver_laps = session.laps.pick_drivers(driver)
    
    # 找出進站圈
    pit_laps = driver_laps[driver_laps['PitInTime'].notna()]['LapNumber'].tolist()
    
    # 建立 stint 結構: [(start_lap, end_lap, compound), ...]
    stints = []
    compounds = driver_laps[['LapNumber', 'Compound']].dropna()
    
    prev_compound = None
    stint_start = 1
    
    for idx, row in compounds.iterrows():
        lap = int(row['LapNumber'])
        compound = row['Compound']
        
        if compound != prev_compound and prev_compound is not None:
            # Stint 結束
            stints.append((stint_start, lap - 1, prev_compound))
            stint_start = lap
        
        prev_compound = compound
    
    # 最後一個 stint
    if prev_compound:
        total_laps = int(compounds['LapNumber'].max())
        stints.append((stint_start, total_laps, prev_compound))
    
    print(f"\n{race} {driver} 進站策略:")
    for i, (start, end, compound) in enumerate(stints, 1):
        print(f"  Stint {i}: Lap {start}-{end} ({compound}) - {end - start + 1} 圈")
    
    return stints, pit_laps


def predict_quadratic_model(base_time: float, total_laps: int, 
                            stints: list, circuit: str) -> tuple:
    """
    DriverStrategy 的二次方程式模型（含進站策略）
    degradation(t) = base_rate * tyre_age + 0.5 * acceleration * tyre_age^2
    
    Args:
        stints: [(start_lap, end_lap, compound), ...]
    """
    # 載入輪胎衰退資料庫
    db_path = Path('config/tire_degradation_database.json')
    if not db_path.exists():
        # 使用預設值
        deg_params = {
            'SOFT': {'base_rate': 0.065, 'acceleration': 0.0025},
            'MEDIUM': {'base_rate': 0.045, 'acceleration': 0.0015},
            'HARD': {'base_rate': 0.030, 'acceleration': 0.0009}
        }
    else:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
            circuits = db.get('circuits', {})
            circuit_data = circuits.get(circuit, {})
            
            base_deg = circuit_data.get('base_degradation', {})
            accel_deg = circuit_data.get('degradation_acceleration', {})
            
            deg_params = {
                'SOFT': {
                    'base_rate': base_deg.get('SOFT', 0.065),
                    'acceleration': accel_deg.get('SOFT', 0.0025)
                },
                'MEDIUM': {
                    'base_rate': base_deg.get('MEDIUM', 0.045),
                    'acceleration': accel_deg.get('MEDIUM', 0.0015)
                },
                'HARD': {
                    'base_rate': base_deg.get('HARD', 0.030),
                    'acceleration': accel_deg.get('HARD', 0.0009)
                }
            }
    
    # 燃油效應（固定係數）
    fuel_coef = 0.030
    fuel_kg_per_lap = 1.75
    
    predictions = []
    laps = []
    
    for lap in range(3, total_laps + 1):
        # 找到這一圈屬於哪個 stint
        current_stint = None
        for stint_start, stint_end, compound in stints:
            if stint_start <= lap <= stint_end:
                current_stint = (stint_start, stint_end, compound)
                break
        
        if not current_stint:
            continue
        
        stint_start, stint_end, compound = current_stint
        tyre_age = lap - stint_start + 1  # ✅ 換胎後重置為 1
        
        # 取得該配方的參數
        params = deg_params.get(compound.upper(), deg_params['MEDIUM'])
        base_rate = params['base_rate']
        acceleration = params['acceleration']
        
        # 二次方程式輪胎衰退
        tyre_deg = base_rate * tyre_age + 0.5 * acceleration * (tyre_age ** 2)
        
        # 燃油效應（負值 = 車變輕 = 更快）
        fuel_consumed = lap * fuel_kg_per_lap
        fuel_effect = -fuel_coef * fuel_consumed
        
        predicted = base_time + tyre_deg + fuel_effect
        predictions.append(predicted)
        laps.append(lap)
    
    return laps, predictions


def test_race(year: int, race: str, driver: str = "VER", compound: str = "MEDIUM"):
    """測試單場比賽 - 比較 F92 vs Quadratic Model（含真實進站策略）"""
    print(f"\n{'='*60}")
    print(f"測試: {year} {race}")
    print(f"{'='*60}")
    
    try:
        # 步驟 1: 從 Race 前3圈獲取 base_time
        base_time = load_race_base_time(year, race, driver)
        
        # 步驟 2: 載入真實數據
        real_laps, real_times = load_real_race_data(year, race, driver)
        total_laps = int(max(real_laps))
        
        # 步驟 3: 獲取真實進站策略
        stints, pit_laps = get_pit_strategy(year, race, driver)
        
        # 賽道名稱映射
        circuit_map = {
            "Japan": "Suzuka",
            "Mexico": "Mexico_City",
            "Abu Dhabi": "Yas_Island"
        }
        circuit = circuit_map.get(race, race)
        
        # 步驟 4: F92 預測（Race base_time + FP2 校正 + ML 殘差）
        predictor = F92HybridPredictor(verbose=True)
        f92_result = predictor.predict(
            year=year,
            race=race,
            driver=driver,
            compound=compound,
            total_laps=total_laps,
            base_time=base_time,
            use_ml=True
        )
        
        # 步驟 5: Quadratic Model 預測（二次方程式 + 真實進站策略）
        quad_laps, quad_times = predict_quadratic_model(
            base_time, total_laps, stints, circuit
        )
        
        # 步驟 6: 計算誤差
        f92_laps = [p['lap'] for p in f92_result['predictions']]
        f92_times = [p['predicted_time'] for p in f92_result['predictions']]
        
        # F92 誤差
        f92_errors = []
        quad_errors = []
        common_laps = sorted(set(f92_laps) & set(real_laps) & set(quad_laps))
        
        for lap in common_laps:
            real_idx = real_laps.index(lap)
            f92_idx = f92_laps.index(lap)
            quad_idx = quad_laps.index(lap)
            
            f92_errors.append(abs(f92_times[f92_idx] - real_times[real_idx]))
            quad_errors.append(abs(quad_times[quad_idx] - real_times[real_idx]))
        
        f92_mae = np.mean(f92_errors)
        quad_mae = np.mean(quad_errors)
        
        print(f"\n{'='*60}")
        print(f"結果:")
        print(f"  F92 MAE: {f92_mae:.3f}s")
        print(f"  Quadratic Model MAE: {quad_mae:.3f}s")
        print(f"  差異: {abs(f92_mae - quad_mae):.3f}s")
        if f92_mae < quad_mae:
            print(f"  ✅ F92 優於二次方程式 ({((quad_mae - f92_mae) / quad_mae * 100):.1f}%)")
        else:
            print(f"  ❌ 二次方程式優於 F92 ({((f92_mae - quad_mae) / f92_mae * 100):.1f}%)")
        print(f"{'='*60}")
        
        return {
            'race': race,
            'base_time': base_time,
            'stints': stints,
            'pit_laps': pit_laps,
            'f92_laps': f92_laps,
            'f92_times': f92_times,
            'quad_laps': quad_laps,
            'quad_times': quad_times,
            'real_laps': real_laps,
            'real_times': real_times,
            'f92_mae': f92_mae,
            'quad_mae': quad_mae
        }
        
    except Exception as e:
        print(f"[錯誤] {e}")
        import traceback
        traceback.print_exc()
        return None


def create_comparison_chart(results: list):
    """生成三方比較圖表: Real vs F92 vs Quadratic（含進站標記）"""
    n_races = len(results)
    fig, axes = plt.subplots(1, n_races, figsize=(10*n_races, 7))
    if n_races == 1:
        axes = [axes]
    
    for idx, result in enumerate(results):
        ax = axes[idx]
        
        # 繪製真實 vs F92 vs Quadratic
        ax.plot(result['real_laps'], result['real_times'], 
                'o-', label='真實圈速', color='#00D9FF', alpha=0.8, linewidth=2, markersize=5)
        ax.plot(result['f92_laps'], result['f92_times'], 
                's--', label=f'F92 預測 (MAE={result["f92_mae"]:.3f}s)', 
                color='#FF4444', alpha=0.7, linewidth=2, markersize=4)
        ax.plot(result['quad_laps'], result['quad_times'], 
                '^:', label=f'二次方程式 (MAE={result["quad_mae"]:.3f}s)', 
                color='#44FF44', alpha=0.7, linewidth=2, markersize=4)
        
        # 標記進站圈
        for pit_lap in result.get('pit_laps', []):
            ax.axvline(x=pit_lap, color='orange', linestyle='--', alpha=0.5, linewidth=1.5)
            ax.text(pit_lap, ax.get_ylim()[1], f' PIT', 
                   rotation=90, verticalalignment='top', fontsize=9, color='orange')
        
        # 標記 stint 資訊
        stint_info = []
        for i, (start, end, compound) in enumerate(result.get('stints', []), 1):
            stint_info.append(f"S{i}: L{start}-{end} ({compound})")
        
        ax.set_xlabel('圈數', fontsize=13, fontweight='bold')
        ax.set_ylabel('圈速 (秒)', fontsize=13, fontweight='bold')
        
        winner = "F92" if result['f92_mae'] < result['quad_mae'] else "Quadratic"
        improvement = abs(result['f92_mae'] - result['quad_mae']) / max(result['f92_mae'], result['quad_mae']) * 100
        
        ax.set_title(
            f"{result['race']}\n"
            f"base_time={result['base_time']:.3f}s | " + ' | '.join(stint_info) + f"\n"
            f"優勝: {winner} (優勢 {improvement:.1f}%)", 
            fontsize=12, fontweight='bold'
        )
        ax.legend(fontsize=10, loc='upper left')
        ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # 儲存
    output_path = Path('reports/f92_vs_quadratic_with_pitstops.png')
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n圖表已保存: {output_path}")
    
    return output_path


if __name__ == "__main__":
    # 測試配置
    test_cases = [
        {"year": 2025, "race": "Japan", "driver": "VER", "compound": "MEDIUM"},
        {"year": 2025, "race": "Mexico", "driver": "VER", "compound": "MEDIUM"},
    ]
    
    results = []
    for case in test_cases:
        result = test_race(**case)
        if result:
            results.append(result)
    
    if results:
        print(f"\n{'='*60}")
        print("三方驗證總結: Real vs F92 vs Quadratic")
        print(f"{'='*60}")
        for result in results:
            winner = "✅ F92" if result['f92_mae'] < result['quad_mae'] else "❌ Quadratic"
            diff = abs(result['f92_mae'] - result['quad_mae'])
            print(f"  {result['race']}:")
            print(f"    F92: {result['f92_mae']:.3f}s")
            print(f"    二次方程式: {result['quad_mae']:.3f}s")
            print(f"    優勝: {winner} (差距 {diff:.3f}s)")
        
        avg_f92_mae = np.mean([r['f92_mae'] for r in results])
        avg_quad_mae = np.mean([r['quad_mae'] for r in results])
        print(f"\n  平均 F92 MAE: {avg_f92_mae:.3f}s")
        print(f"  平均 Quadratic MAE: {avg_quad_mae:.3f}s")
        
        if avg_f92_mae < avg_quad_mae:
            improvement = (avg_quad_mae - avg_f92_mae) / avg_quad_mae * 100
            print(f"  🎯 F92 整體優勢: {improvement:.1f}%")
        else:
            decline = (avg_f92_mae - avg_quad_mae) / avg_f92_mae * 100
            print(f"  ⚠️ F92 整體劣勢: {decline:.1f}%")
        
        # 生成圖表
        chart_path = create_comparison_chart(results)
        
        # 打開圖表
        import subprocess
        subprocess.run(['powershell', 'Start-Process', str(chart_path)], 
                      capture_output=True)
