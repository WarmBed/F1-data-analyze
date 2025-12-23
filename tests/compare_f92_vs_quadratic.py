"""
完整比較: F92 vs 二次方程模型
測試: Japan 2025, Mexico 2024
"""
import sys
import fastf1
import pandas as pd
import numpy as np
from typing import List, Tuple

# 導入模組
sys.path.insert(0, 'CLI_modules/cli/prediction')
sys.path.insert(0, 'CLI_modules/cli/strategy')
from f92_hybrid_predictor import F92HybridPredictor
from driver_strategy import DriverStrategy
from smart_base_time_extractor import extract_base_time_robust

fastf1.Cache.enable_cache('f1_analysis_cache/')


class QuadraticModel:
    """二次方程輪胎降解模型"""
    
    def __init__(self):
        self.strategy = DriverStrategy()
        
    def predict(self, year: int, race: str, driver: str, 
                base_time: float, stints: List[Tuple[int, int, str]],
                skip_laps: List[int] = None) -> dict:
        """
        使用二次方程模型預測
        
        Returns:
            dict: {
                'predictions': [...],
                'mae': float,
                'mean_error': float
            }
        """
        if skip_laps is None:
            skip_laps = []
        
        # 載入實際數據
        session = fastf1.get_session(year, race, 'R')
        session.load()
        driver_laps = session.laps.pick_driver(driver)
        driver_laps = driver_laps[driver_laps['LapTime'].notna()]
        driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
        
        # 賽道名稱映射
        circuit_map = {
            'Japan': 'Suzuka',
            'Mexico': 'Autódromo Hermanos Rodríguez'
        }
        circuit_name = circuit_map.get(race, race)
        
        predictions = []
        errors = []
        
        total_laps = stints[-1][1]
        
        for lap in range(3, total_laps + 1):
            # 跳過 SC 圈
            if lap in skip_laps:
                continue
            
            # 找當前 stint
            current_stint = None
            stint_idx = 0
            for idx, (start, end, compound) in enumerate(stints):
                if start <= lap <= end:
                    current_stint = (start, end, compound)
                    stint_idx = idx
                    break
            
            if not current_stint:
                continue
            
            stint_start, stint_end, compound = current_stint
            tyre_age = lap - stint_start + 1
            
            # 二次方程降解
            degradation = self.strategy.calculate_tire_degradation(
                circuit_name=circuit_name,
                compound=compound,
                tyre_age=tyre_age
            )
            
            predicted_time = base_time + degradation
            
            # 找實際圈速
            actual_lap = driver_laps[driver_laps['LapNumber'] == lap]
            if actual_lap.empty:
                continue
            
            actual_time = actual_lap['LapTimeSeconds'].iloc[0]
            
            # 跳過異常圈
            if actual_time > 120:
                continue
            
            error = predicted_time - actual_time
            
            predictions.append({
                'lap': lap,
                'stint_lap': tyre_age,
                'compound': compound,
                'predicted_time': predicted_time,
                'actual_time': actual_time,
                'error': error,
                'degradation': degradation
            })
            
            errors.append(abs(error))
        
        mae = np.mean(errors) if errors else 0
        mean_error = np.mean([p['error'] for p in predictions]) if predictions else 0
        
        return {
            'predictions': predictions,
            'mae': mae,
            'mean_error': mean_error,
            'model': 'Quadratic'
        }


def compare_models(year: int, race: str, driver: str, 
                   stints: List[Tuple[int, int, str]]):
    """
    比較兩個模型
    """
    print("\n" + "="*100)
    print(f"比較測試: {year} {race} {driver}")
    print("="*100)
    
    # 1. 提取 base_time
    print("\n[1/4] 提取智能 base_time...")
    base_time, info = extract_base_time_robust(year, race, driver)
    skip_laps = info.get('sc_laps', [])
    
    print(f"  Base Time: {base_time:.3f}s")
    print(f"  SC Laps: {skip_laps} (共 {len(skip_laps)} 圈)")
    
    # 2. F92 預測
    print("\n[2/4] 執行 F92 混合模型...")
    f92 = F92HybridPredictor()
    f92_result = f92.predict(
        year=year, race=race, driver=driver,
        base_time=base_time,
        stints=stints,
        skip_laps=skip_laps,
        use_ml=True
    )
    
    if f92_result:
        print(f"  ✅ F92 MAE: {f92_result.get('mae', 'N/A'):.3f}s")
        print(f"  ✅ F92 Bias: {f92_result.get('mean_error', 0):+.3f}s")
    else:
        print("  ❌ F92 預測失敗")
        return None
    
    # 3. 二次方程預測
    print("\n[3/4] 執行二次方程模型...")
    quad = QuadraticModel()
    quad_result = quad.predict(
        year=year, race=race, driver=driver,
        base_time=base_time,
        stints=stints,
        skip_laps=skip_laps
    )
    
    if quad_result:
        print(f"  ✅ 二次方程 MAE: {quad_result.get('mae', 'N/A'):.3f}s")
        print(f"  ✅ 二次方程 Bias: {quad_result.get('mean_error', 0):+.3f}s")
    else:
        print("  ❌ 二次方程預測失敗")
        return None
    
    # 4. 比較
    print("\n[4/4] 比較結果")
    print("="*100)
    
    f92_mae = f92_result.get('mae', 0)
    quad_mae = quad_result.get('mae', 0)
    
    f92_bias = f92_result.get('mean_error', 0)
    quad_bias = quad_result.get('mean_error', 0)
    
    print(f"\n  模型對比:")
    print(f"  {'模型':<15} {'MAE':>10} {'Bias':>10} {'狀態'}")
    print(f"  {'-'*50}")
    print(f"  {'F92 混合':<15} {f92_mae:>9.3f}s {f92_bias:>+9.3f}s")
    print(f"  {'二次方程':<15} {quad_mae:>9.3f}s {quad_bias:>+9.3f}s")
    print(f"  {'-'*50}")
    
    # 計算優勢
    if f92_mae < quad_mae:
        advantage = ((quad_mae - f92_mae) / quad_mae) * 100
        print(f"\n  ✅ F92 勝出！優勢 {advantage:.1f}% ({quad_mae - f92_mae:.3f}s)")
        winner = 'F92'
    elif quad_mae < f92_mae:
        advantage = ((f92_mae - quad_mae) / f92_mae) * 100
        print(f"\n  ✅ 二次方程勝出！優勢 {advantage:.1f}% ({f92_mae - quad_mae:.3f}s)")
        winner = 'Quadratic'
    else:
        print(f"\n  ⚖️  平手")
        advantage = 0
        winner = 'Tie'
    
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
    print("\n" + "="*100)
    print("F92 vs 二次方程模型 - 完整比較測試")
    print("="*100)
    
    results = []
    
    # 測試 1: Japan 2025
    japan_result = compare_models(
        year=2025,
        race="Japan",
        driver="VER",
        stints=[
            (1, 21, "MEDIUM"),
            (22, 53, "HARD")
        ]
    )
    if japan_result:
        results.append(japan_result)
    
    # 測試 2: Mexico 2024
    mexico_result = compare_models(
        year=2024,
        race="Mexico",
        driver="VER",
        stints=[
            (1, 26, "MEDIUM"),
            (27, 71, "HARD")
        ]
    )
    if mexico_result:
        results.append(mexico_result)
    
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
        
        # 平均表現
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
            overall_advantage = ((avg_quad - avg_f92) / avg_quad) * 100
            print(f"\n  ✅ F92 整體表現更佳！平均優勢 {overall_advantage:.1f}%")
        elif avg_quad < avg_f92:
            overall_advantage = ((avg_f92 - avg_quad) / avg_f92) * 100
            print(f"\n  ✅ 二次方程整體表現更佳！平均優勢 {overall_advantage:.1f}%")
        else:
            print(f"\n  ⚖️  兩模型整體表現相當")
    
    print(f"\n{'='*100}")
    print("✅ 比較測試完成")
    print("="*100)


if __name__ == "__main__":
    main()
