"""
測試 F83 (OT%) 和 F85 (CC%) 雙模型預測
案例: TSU vs NOR (Abu Dhabi 2025, Lap 18-22)
"""
from CLI_modules.cli.prediction.overtake_prediction.predictor import OvertakePredictor
from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import CloseCombatPredictor

print("=" * 70)
print("F83 (OT%) + F85 (CC%) 雙模型預測測試")
print("案例: TSU vs NOR (Abu Dhabi 2025, Lap 18-22)")
print("=" * 70)

# 初始化兩個預測器
ot_predictor = OvertakePredictor(verbose=False)
cc_predictor = CloseCombatPredictor(verbose=False)

# 測試數據
test_cases = [
    {"lap": 19, "gap": 3.5, "description": "Lap 19: TSU 落後 NOR 3.5s"},
    {"lap": 20, "gap": 2.5, "description": "Lap 20: 縮小到 2.5s"},
    {"lap": 21, "gap": 1.6, "description": "Lap 21: 縮小到 1.6s"},
    {"lap": 22, "gap": 0.6, "description": "Lap 22: 縮小到 0.6s（即將超車）"},
]

print("\n雙模型預測對比:")
print("-" * 70)

for case in test_cases:
    # F83 預測 (OT%)
    ot_result = ot_predictor.predict(
        gap_seconds=case["gap"],
        gap_delta=-0.1,
        is_catching=True,
        drs_available=True,
        attacker_tyre='SOFT',
        defender_tyre='MEDIUM',
        tyre_age_diff=5,
        track_status_green=True,
        attacker_position=11,
        race_progress=0.35
    )
    
    # F85 預測 (CC%)
    cc_result = cc_predictor.predict(
        gap_seconds=case["gap"],
        gap_delta=-0.1,
        is_catching=True,
        drs_available=True,
        attacker_tyre='SOFT',
        defender_tyre='MEDIUM',
        tyre_age_diff=5,
        track_status_green=True,
        attacker_position=11,
        race_progress=0.35,
        gap_trend_3lap=-0.3,
        min_gap_last_5lap=case["gap"] * 0.8,
        consecutive_catching_laps=3
    )
    
    ot_prob = ot_result.probability
    cc_prob = cc_result.probability
    
    print(f"\n{case['description']}")
    print(f"  Gap: {case['gap']:.1f}s")
    print(f"  ├─ F85 (CC%) 追近到 0.2-0.3s: {cc_prob:6.1%}  {'✅' if cc_prob > 0.5 else '⚠️' if cc_prob > 0.3 else '❌'}")
    print(f"  └─ F83 (OT%) 完成超車:       {ot_prob:6.1%}  {'✅' if ot_prob > 0.5 else '⚠️' if ot_prob > 0.3 else '❌'}")
    
    # 結論
    if cc_prob > 0.6 and ot_prob > 0.4:
        print(f"  💡 結論: 高機率追近且有機會超車")
    elif cc_prob > 0.5 and ot_prob < 0.2:
        print(f"  💡 結論: 會進入纏鬥但難以完成超車")
    elif cc_prob < 0.3:
        print(f"  💡 結論: 追不近，無超車機會")

print("\n" + "=" * 70)
print("✅ 測試完成")
print("=" * 70)
print("\n說明:")
print("  F85 (CC%): 預測未來 5 圈內追近到 0.2-0.3s 的機率")
print("  F83 (OT%): 預測發生超車的機率")
