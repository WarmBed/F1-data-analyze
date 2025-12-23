"""
測試 F86 近距離接觸預測 - TSU vs NOR (Abu Dhabi 2025)
"""
from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import CloseCombatPredictor

print("=" * 70)
print("F86: 近距離接觸預測測試")
print("案例: TSU vs NOR (Abu Dhabi 2025, Lap 18-22)")
print("=" * 70)

# 初始化預測器
predictor = CloseCombatPredictor(verbose=True)

# 根據用戶提供的真實數據
test_cases = [
    {"lap": 19, "gap": 3.5, "description": "Lap 19: TSU 落後 NOR 3.5s"},
    {"lap": 20, "gap": 2.5, "description": "Lap 20: 縮小到 2.5s"},
    {"lap": 21, "gap": 1.6, "description": "Lap 21: 縮小到 1.6s"},
    {"lap": 22, "gap": 0.6, "description": "Lap 22: 縮小到 0.6s（即將超車）"},
]

print("\n測試預測（使用預設特徵值）:")
print("-" * 70)

for case in test_cases:
    # 使用預設特徵值進行預測
    result = predictor.predict(
        gap_seconds=case["gap"],
        gap_delta=-0.1,  # 假設持續縮小
        is_catching=True,
        drs_available=True,
        attacker_tyre='SOFT',
        defender_tyre='MEDIUM',
        tyre_age_diff=5,
        track_status_green=True,
        attacker_position=11,
        race_progress=0.35,
        gap_trend_3lap=-0.3,  # 3 圈趨勢
        min_gap_last_5lap=case["gap"] * 0.8,
        consecutive_catching_laps=3
    )
    
    probability = result.probability
    
    print(f"\n{case['description']}")
    print(f"  Gap: {case['gap']:.1f}s")
    print(f"  預測: 未來 5 圈追近到 0.2-0.3s 的機率 = {probability:.1%}")
    
    if probability > 0.7:
        print(f"  結論: ✅ 高機率追近（{probability:.1%}）")
    elif probability > 0.5:
        print(f"  結論: ⚠️ 中等機率追近（{probability:.1%}）")
    else:
        print(f"  結論: ❌ 低機率追近（{probability:.1%}）")

print("\n" + "=" * 70)
print("✅ 測試完成")
print("=" * 70)
