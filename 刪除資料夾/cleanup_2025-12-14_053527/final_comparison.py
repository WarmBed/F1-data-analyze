"""
F92 vs 二次方程完整比較 - 簡化版
Japan 2025 + Mexico 2024
"""
import sys
import fastf1
import numpy as np

sys.path.insert(0, 'CLI_modules/cli/prediction')
from f92_hybrid_predictor import F92HybridPredictor
from smart_base_time_extractor import extract_base_time_robust

fastf1.Cache.enable_cache('f1_analysis_cache/')


def quadratic_degradation(tyre_age, compound, circuit):
    """
    二次方程輪胎降解計算
    degradation = base_rate * t + 0.5 * acceleration * t^2
    """
    # 賽道參數（來自 F92 的預設值）
    params = {
        'Suzuka': {
            'MEDIUM': {'base_rate': 0.039, 'acceleration': 0.0015},
            'HARD': {'base_rate': 0.032, 'acceleration': 0.0012}
        },
        'Autódromo Hermanos Rodríguez': {
            'MEDIUM': {'base_rate': 0.042, 'acceleration': 0.0016},
            'HARD': {'base_rate': 0.035, 'acceleration': 0.0013}
        }
    }
    
    circuit_params = params.get(circuit, {})
    compound_params = circuit_params.get(compound, {'base_rate': 0.045, 'acceleration': 0.0015})
    
    base_rate = compound_params['base_rate']
    accel = compound_params['acceleration']
    
    return base_rate * tyre_age + 0.5 * accel * (tyre_age ** 2)


def compare_race(year, race, driver, stints, circuit_name):
    """比較單場賽事"""
    print("\n" + "="*100)
    print(f"{year} {race} {driver}")
    print("="*100)
    
    # 提取 base_time
    print("\n[1/3] 提取智能 base_time...")
    base_time, info = extract_base_time_robust(year, race, driver)
    skip_laps = info.get('sc_laps', [])
    
    print(f"  Base Time: {base_time:.3f}s")
    print(f"  SC Laps: {skip_laps} (共 {len(skip_laps)} 圈)")
    
    # F92 預測
    print("\n[2/3] F92 混合模型...")
    f92 = F92HybridPredictor()
    f92_result = f92.predict(
        year=year, race=race, driver=driver,
        base_time=base_time,
        stints=stints,
        skip_laps=skip_laps,
        use_ml=True
    )
    
    if not f92_result:
        print("  ❌ F92 失敗")
        return None
    
    f92_mae = f92_result.get('mae', 999)
    f92_bias = f92_result.get('mean_error', 0)
    print(f"  ✅ F92 MAE: {f92_mae:.3f}s, Bias: {f92_bias:+.3f}s")
    
    # 二次方程預測
    print("\n[3/3] 二次方程模型...")
    session = fastf1.get_session(year, race, 'R')
    session.load()
    driver_laps = session.laps.pick_driver(driver)
    driver_laps = driver_laps[driver_laps['LapTime'].notna()]
    driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
    
    errors = []
    total_laps = stints[-1][1]
    
    for lap in range(3, total_laps + 1):
        if lap in skip_laps:
            continue
        
        # 找當前 stint
        current_compound = None
        tyre_age = 0
        for stint_start, stint_end, compound in stints:
            if stint_start <= lap <= stint_end:
                current_compound = compound
                tyre_age = lap - stint_start + 1
                break
        
        if not current_compound:
            continue
        
        # 二次方程降解
        degradation = quadratic_degradation(tyre_age, current_compound, circuit_name)
        predicted_time = base_time + degradation
        
        # 實際圈速
        actual_lap = driver_laps[driver_laps['LapNumber'] == lap]
        if actual_lap.empty:
            continue
        
        actual_time = actual_lap['LapTimeSeconds'].iloc[0]
        
        # 跳過異常圈
        if actual_time > 120:
            continue
        
        error = predicted_time - actual_time
        errors.append(error)
    
    quad_mae = np.mean([abs(e) for e in errors])
    quad_bias = np.mean(errors)
    
    print(f"  ✅ 二次方程 MAE: {quad_mae:.3f}s, Bias: {quad_bias:+.3f}s")
    
    # 比較
    print(f"\n  比較:")
    print(f"    F92:      MAE={f92_mae:.3f}s, Bias={f92_bias:+.3f}s")
    print(f"    二次方程: MAE={quad_mae:.3f}s, Bias={quad_bias:+.3f}s")
    print(f"    差距:     {f92_mae - quad_mae:+.3f}s")
    
    if f92_mae < quad_mae:
        advantage = ((quad_mae - f92_mae) / quad_mae) * 100
        print(f"\n  ✅ F92 勝出！優勢 {advantage:.1f}%")
        winner = 'F92'
    elif quad_mae < f92_mae:
        advantage = ((f92_mae - quad_mae) / f92_mae) * 100
        print(f"\n  ✅ 二次方程勝出！優勢 {advantage:.1f}%")
        winner = 'Quadratic'
    else:
        print(f"\n  ⚖️ 平手")
        winner = 'Tie'
        advantage = 0
    
    return {
        'race': f"{year} {race}",
        'f92_mae': f92_mae,
        'f92_bias': f92_bias,
        'quad_mae': quad_mae,
        'quad_bias': quad_bias,
        'winner': winner,
        'advantage': advantage
    }


def main():
    """主程式"""
    print("="*100)
    print("F92 vs 二次方程模型 - 完整比較測試")
    print("="*100)
    
    results = []
    
    # 測試 1: Japan 2025
    japan = compare_race(
        year=2025,
        race="Japan",
        driver="VER",
        stints=[(1, 21, "MEDIUM"), (22, 53, "HARD")],
        circuit_name="Suzuka"
    )
    if japan:
        results.append(japan)
    
    # 測試 2: Mexico 2024
    mexico = compare_race(
        year=2024,
        race="Mexico",
        driver="VER",
        stints=[(1, 26, "MEDIUM"), (27, 71, "HARD")],
        circuit_name="Autódromo Hermanos Rodríguez"
    )
    if mexico:
        results.append(mexico)
    
    # 總結
    print("\n" + "="*100)
    print("總結報告")
    print("="*100)
    
    if results:
        print(f"\n  {'賽事':<20} {'F92 MAE':>10} {'二次方程 MAE':>12} {'差距':>10} {'勝者':>10}")
        print(f"  {'-'*70}")
        
        for r in results:
            diff = r['f92_mae'] - r['quad_mae']
            print(f"  {r['race']:<20} {r['f92_mae']:>9.3f}s {r['quad_mae']:>11.3f}s {diff:>+9.3f}s {r['winner']:>10}")
        
        print(f"  {'-'*70}")
        
        # 平均
        avg_f92 = np.mean([r['f92_mae'] for r in results])
        avg_quad = np.mean([r['quad_mae'] for r in results])
        
        print(f"  {'平均':<20} {avg_f92:>9.3f}s {avg_quad:>11.3f}s {avg_f92 - avg_quad:>+9.3f}s")
        
        # 總評
        print(f"\n  總體評估:")
        f92_wins = sum(1 for r in results if r['winner'] == 'F92')
        quad_wins = sum(1 for r in results if r['winner'] == 'Quadratic')
        
        print(f"    F92 勝場: {f92_wins}/{len(results)}")
        print(f"    二次方程勝場: {quad_wins}/{len(results)}")
        
        if avg_f92 < avg_quad:
            overall_adv = ((avg_quad - avg_f92) / avg_quad) * 100
            print(f"\n  ✅ F92 整體表現更佳！平均優勢 {overall_adv:.1f}%")
        elif avg_quad < avg_f92:
            overall_adv = ((avg_f92 - avg_quad) / avg_f92) * 100
            print(f"\n  ✅ 二次方程整體表現更佳！平均優勢 {overall_adv:.1f}%")
        else:
            print(f"\n  ⚖️ 兩模型整體表現相當")
    
    print(f"\n{'='*100}")
    print("✅ 比較完成")
    print("="*100)


if __name__ == "__main__":
    main()
