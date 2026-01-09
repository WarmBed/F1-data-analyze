"""
測試模擬器差距參數是否接近真實數據
基於 2023-2025 共 24 場完整比賽的分析結果

真實數據基準：
- P5 與 P1 平均差距: 65.0s (範圍 7.7s ~ 271.5s)
- P10 與 P1 平均差距: 110.8s (範圍 21.6s ~ 338.9s)
- P20 與 P1 平均差距: 92.2s (範圍 81.6s ~ 109.8s)
- 平均比賽圈數: 56 圈
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategy_simulator.core.race_simulator import FullRaceSimulator, SimulationParams
import random

def test_simulated_gaps():
    """測試模擬差距是否接近真實數據"""
    
    # 建立模擬車手數據（類似 FP2 預測格式）
    fp2_predictions = []
    base_time = 92.0  # 類似 Japan 2025 的 Q 時間
    
    for i in range(1, 21):
        driver_code = f"D{i:02d}"
        # Q 時間隨位置遞增（每位置約 0.1s）
        q_time = base_time + (i - 1) * 0.1
        fp2_predictions.append({
            'driver': driver_code,
            'team': f'Team{(i-1)//2 + 1}',
            'rank': i,
            'predicted_time': q_time
        })
    
    # 執行多次模擬
    num_simulations = 10
    all_gaps = {f"P{i}": [] for i in range(2, 21)}
    
    print("執行模擬測試...")
    print("=" * 60)
    
    for sim_num in range(num_simulations):
        # 每次使用不同的隨機種子
        random.seed(sim_num * 12345 + 67890)
        
        params = SimulationParams(
            race_laps=56,
            base_lap_time=92.0,
            pit_loss_green=22.0,
            fuel_effect_coefficient=0.05
        )
        
        simulator = FullRaceSimulator(
            sim_params=params,
            simple_mode=True,  # 使用簡單模式測試差距
            track_name="Japan",
            year=2025
        )
        simulator.load_drivers(fp2_predictions)  # 正確的方法名
        
        # 設定基本策略
        for i, pred in enumerate(fp2_predictions):
            simulator._strategies[pred['driver']] = simulator._create_stints_from_sequence(
                ['M', 'H'], pred['driver']
            )
        
        # 執行模擬 (使用正確的方法名)
        result = simulator.simulate_race(seed=sim_num)
        
        if not result or not result.final_standings:
            print(f"模擬 {sim_num + 1} 失敗")
            continue
        
        # 找出 P1 的時間
        p1_driver = result.final_standings[0]
        p1_total_time = p1_driver.total_time
        
        # 計算各位置差距
        for rank, driver in enumerate(result.final_standings[1:], 2):
            gap = driver.total_time - p1_total_time
            if f"P{rank}" in all_gaps:
                all_gaps[f"P{rank}"].append(gap)
        
        if sim_num == 0:
            print(f"\n模擬 {sim_num + 1} 結果 (56 圈):")
            for rank, driver in enumerate(result.final_standings[:10], 1):
                gap = driver.total_time - p1_total_time
                gap_str = f"+{gap:.1f}s" if gap > 0 else "Leader"
                print(f"  P{rank} {driver.driver_code}: {driver.total_time:.1f}s ({gap_str})")
    
    # 統計分析
    print("\n" + "=" * 60)
    print("模擬結果統計:")
    print("=" * 60)
    
    print("\n位置 | 模擬平均 | 模擬範圍 | 真實平均 | 比較")
    print("-" * 60)
    
    real_gaps = {
        "P2": 42.5, "P3": 52.2, "P4": 60.1, "P5": 65.0,
        "P6": 76.8, "P7": 82.1, "P8": 88.7, "P9": 93.7, "P10": 110.8,
        "P11": 115.7, "P12": 124.1, "P13": 134.7, "P14": 141.0, "P15": 134.5,
        "P16": 125.8, "P17": 133.3, "P18": 166.8, "P19": 104.8, "P20": 92.2
    }
    
    for pos in ["P2", "P5", "P10", "P15", "P20"]:
        if pos in all_gaps and all_gaps[pos]:
            gaps = all_gaps[pos]
            avg = sum(gaps) / len(gaps)
            min_g = min(gaps)
            max_g = max(gaps)
            real = real_gaps.get(pos, 0)
            diff = avg - real
            status = "[OK]" if abs(diff) < real * 0.5 else "[X]"  # 允許 50% 誤差
            print(f"{pos:4} | {avg:7.1f}s | {min_g:5.1f}-{max_g:5.1f}s | {real:7.1f}s | {status} ({diff:+.1f}s)")
    
    print("\n" + "=" * 60)
    print("結論:")
    print("=" * 60)
    
    # 檢查是否在合理範圍內
    if all_gaps["P10"]:
        avg_p10 = sum(all_gaps["P10"]) / len(all_gaps["P10"])
        if 50 < avg_p10 < 200:
            print("[OK] P10 差距在合理範圍 (50s-200s)")
        else:
            print(f"[X] P10 差距 {avg_p10:.1f}s 超出合理範圍")
    
    if all_gaps["P20"]:
        avg_p20 = sum(all_gaps["P20"]) / len(all_gaps["P20"])
        if 80 < avg_p20 < 300:
            print("[OK] P20 差距在合理範圍 (80s-300s)")
        else:
            print(f"[X] P20 差距 {avg_p20:.1f}s 超出合理範圍")

if __name__ == "__main__":
    test_simulated_gaps()
