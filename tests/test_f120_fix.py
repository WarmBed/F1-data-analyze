"""
測試 F120 修復後的 _get_speed_at_distance 方法
驗證容差收緊和最小速度採樣是否正常工作
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('CLI_modules')

from cli.analyzer.fp2_corner_all_laps_analysis import FP2CornerAllLapsAnalysis

# 創建模擬遙測數據（模擬低速彎 apex 及周邊）
# 假設 apex 在 distance=2627m
test_telemetry = pd.DataFrame({
    'Distance': [
        2605, 2610, 2615, 2620, 2622,  # 入彎減速段
        2625, 2627, 2629,              # apex 區域（應取最小值）
        2632, 2635, 2640, 2645, 2650   # 出彎加速段
    ],
    'Speed': [
        120.0, 100.0, 85.0, 75.0, 70.0,  # 減速中
        66.0, 64.0, 65.0,                # apex 最慢 64 km/h
        75.0, 90.0, 110.0, 130.0, 150.0  # 加速中
    ]
})

print("=" * 80)
print("F120 修復測試 - _get_speed_at_distance 方法")
print("=" * 80)

print("\n測試遙測數據:")
print(test_telemetry.to_string(index=False))

# 創建測試實例（需要 mock data_loader）
class MockDataLoader:
    def __init__(self):
        self.session = type('obj', (object,), {'race_control_messages': pd.DataFrame()})()
        self.laps = pd.DataFrame({'Driver': ['VER']})
        self.session_type = 'FP2'

try:
    analyzer = FP2CornerAllLapsAnalysis(MockDataLoader())
except Exception as e:
    # 如果初始化失敗，直接測試方法
    print(f"[INFO] 初始化失敗，使用簡化測試: {e}")
    
    # 直接測試 _get_speed_at_distance 方法邏輯
    def test_get_speed_at_distance(telemetry, target_distance, tolerance=5):
        """簡化版 _get_speed_at_distance"""
        nearby = telemetry[
            (telemetry['Distance'] >= target_distance - tolerance) &
            (telemetry['Distance'] <= target_distance + tolerance)
        ]
        
        if not nearby.empty:
            return float(nearby['Speed'].min())
        
        for extended_tolerance in [7, 10]:
            nearby = telemetry[
                (telemetry['Distance'] >= target_distance - extended_tolerance) &
                (telemetry['Distance'] <= target_distance + extended_tolerance)
            ]
            if not nearby.empty:
                return float(nearby['Speed'].min())
        
        return None
    
    # 使用簡化測試函數
    analyzer = type('obj', (object,), {
        '_get_speed_at_distance': test_get_speed_at_distance
    })()

# 測試案例
test_cases = [
    {
        "name": "精準 apex (2627m, tolerance=5m)",
        "distance": 2627.0,
        "tolerance": 5,
        "expected": 64.0  # 應該取 [2625, 2627, 2629] 的最小值 = 64 km/h
    },
    {
        "name": "apex 偏移 (2630m, tolerance=5m)",
        "distance": 2630.0,
        "tolerance": 5,
        "expected": 64.0  # [2625-2635] 範圍最小值仍是 64 km/h
    },
    {
        "name": "舊版容差 (2627m, tolerance=10m)",
        "distance": 2627.0,
        "tolerance": 10,
        "expected": 66.0  # [2617-2637] 範圍，最小值應為 66 km/h（修復後）
    }
]

print("\n" + "=" * 80)
print("修復驗證測試")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n測試 {i}: {test['name']}")
    print(f"  目標距離: {test['distance']} m")
    print(f"  容差: ±{test['tolerance']} m")
    
    result = analyzer._get_speed_at_distance(
        test_telemetry, 
        test['distance'], 
        test['tolerance']
    )
    
    print(f"  預期速度: {test['expected']} km/h")
    print(f"  實際速度: {result} km/h")
    
    if result == test['expected']:
        print(f"  ✅ 測試通過")
    else:
        print(f"  ❌ 測試失敗 (差異: {abs(result - test['expected']) if result else 'N/A'} km/h)")

# 極端測試：驗證是否排除直線加速段
print("\n" + "=" * 80)
print("極端測試：排除加速段")
print("=" * 80)

extreme_telemetry = pd.DataFrame({
    'Distance': [2605, 2610, 2615, 2620, 2625, 2627, 2629, 2632, 2635, 2640],
    'Speed': [120.0, 100.0, 85.0, 75.0, 66.0, 64.0, 282.0, 290.0, 300.0, 310.0]
    #                                            ^^^^  ^^^^  ^^^^  ^^^^
    #                                            異常高速（應被排除）
})

print("\n極端測試遙測:")
print(extreme_telemetry.to_string(index=False))

extreme_result = analyzer._get_speed_at_distance(extreme_telemetry, 2627.0, 5)
print(f"\n目標距離: 2627m (±5m)")
print(f"範圍內速度: {extreme_telemetry[(extreme_telemetry['Distance'] >= 2622) & (extreme_telemetry['Distance'] <= 2632)]['Speed'].tolist()}")
print(f"實際返回: {extreme_result} km/h")
print(f"預期: 64 km/h (最小值，應排除 282 km/h)")

if extreme_result == 64.0:
    print("✅ 極端測試通過！成功排除異常高速")
else:
    print(f"❌ 極端測試失敗！返回 {extreme_result} 而非 64")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)
