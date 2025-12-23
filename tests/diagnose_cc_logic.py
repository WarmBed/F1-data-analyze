# -*- coding: utf-8 -*-
"""
診斷 CC% 預測邏輯問題

用戶場景：2025 Abu Dhabi Lap 22 TSU vs NOR
- Lap 19: 3.5s
- Lap 20: 2.5s (追近 1.0s/lap)
- Lap 21: 1.6s (追近 0.9s/lap)
- Lap 22: 0.6s (追近 1.0s/lap)
- Lap 22: 直線超車

問題：CC% 只有個位數，但明顯在追近！

Author: F1T Team
Date: 2025-12-10
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("CC% 預測邏輯診斷")
print("=" * 80)

# 測試場景
test_scenarios = [
    {
        "lap": 19,
        "gap": 3.5,
        "gap_trend": -1.0,  # 追近 1.0s/lap
        "gap_trend_3lap": 0,  # 第一圈，無歷史
        "min_gap_last_5lap": 3.5,
        "consecutive_catching_laps": 1
    },
    {
        "lap": 20,
        "gap": 2.5,
        "gap_trend": -1.0,
        "gap_trend_3lap": -1.0,  # 開始有趨勢
        "min_gap_last_5lap": 2.5,
        "consecutive_catching_laps": 2
    },
    {
        "lap": 21,
        "gap": 1.6,
        "gap_trend": -0.9,
        "gap_trend_3lap": -0.95,
        "min_gap_last_5lap": 1.6,
        "consecutive_catching_laps": 3
    },
    {
        "lap": 22,
        "gap": 0.6,
        "gap_trend": -1.0,
        "gap_trend_3lap": -0.97,
        "min_gap_last_5lap": 0.6,
        "consecutive_catching_laps": 4
    }
]

print("\n[1] 標籤定義分析")
print("-" * 80)
print("✅ close_combat_happened = 1 的條件：")
print("   → 未來 5 圈內 gap 進入 [0.2s, 0.3s] 區間")
print("\n❌ 問題發現：")
print("   → 0.2-0.3s 是「極窄範圍」（只有 0.1s 寬度）")
print("   → 訓練數據中大部分情況不會進入這個區間")
print("   → 即使 gap 0.6s 並持續追近，模型也認為「進入 0.2-0.3s」的機率很低")

print("\n[2] 模擬預測分析")
print("-" * 80)

try:
    from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import CloseCombatPredictor
    
    predictor = CloseCombatPredictor(verbose=False)
    
    if predictor.model is None:
        print("❌ 模型未載入，無法模擬預測")
    else:
        print(f"✅ F85 模型已載入 (v{predictor.model_version})")
        print("\n模擬 TSU vs NOR 追逐場景：\n")
        
        for scenario in test_scenarios:
            result = predictor.predict(
                gap_seconds=scenario['gap'],
                gap_delta=scenario['gap_trend'],
                is_catching=True,
                drs_available=(scenario['gap'] < 1.0),
                attacker_tyre='SOFT',
                defender_tyre='MEDIUM',
                tyre_age_diff=-5,  # TSU 輪胎新 5 圈
                track_status_green=True,
                attacker_position=2,
                race_progress=0.36,  # 22/58 laps
                gap_trend_3lap=scenario['gap_trend_3lap'],
                min_gap_last_5lap=scenario['min_gap_last_5lap'],
                consecutive_catching_laps=scenario['consecutive_catching_laps']
            )
            
            print(f"Lap {scenario['lap']:2d} | Gap: {scenario['gap']:.1f}s | "
                  f"Trend: {scenario['gap_trend']:+.2f}s/lap | "
                  f"CC%: {result.probability*100:5.1f}% | "
                  f"信心: {result.confidence}")
            
except Exception as e:
    print(f"❌ 預測測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n[3] 根本問題分析")
print("-" * 80)
print("❌ 標籤定義過於嚴格：")
print("   → close_combat_happened 要求 gap ∈ [0.2, 0.3]")
print("   → 實際戰鬥範圍應該是 [0.2, 1.0] 或更寬")
print("   → 0.6s 已經是「極近距離」，但標籤仍為 0")
print()
print("❌ 預測目標錯位：")
print("   → 訓練目標：「會進入 0.2-0.3s」（極窄範圍）")
print("   → 用戶期望：「會發生近距離戰鬥」（0.2-1.5s 都算）")
print("   → Gap 0.6s 時，下一圈可能直接超車，根本不會進入 0.2-0.3s")

print("\n[4] 訓練數據統計分析")
print("-" * 80)

try:
    training_file = project_root / "data" / "overtake_prediction" / "training_samples.csv"
    if training_file.exists():
        import pandas as pd
        df = pd.read_csv(training_file)
        
        # 分析 close_combat_happened 分佈
        cc_count = df['close_combat_happened'].sum()
        total_count = len(df)
        cc_rate = cc_count / total_count * 100
        
        print(f"✅ 訓練樣本總數: {total_count:,}")
        print(f"✅ close_combat_happened=1: {cc_count:,} ({cc_rate:.2f}%)")
        print(f"✅ close_combat_happened=0: {total_count - cc_count:,} ({100-cc_rate:.2f}%)")
        
        # 分析不同 gap 範圍的標籤分佈
        print("\n不同 gap 範圍的 CC 標籤分佈：")
        gap_ranges = [
            (0.0, 0.5, "0.0-0.5s"),
            (0.5, 1.0, "0.5-1.0s"),
            (1.0, 2.0, "1.0-2.0s"),
            (2.0, 3.0, "2.0-3.0s"),
            (3.0, 5.0, "3.0-5.0s")
        ]
        
        for low, high, label in gap_ranges:
            subset = df[(df['gap_seconds'] >= low) & (df['gap_seconds'] < high)]
            if len(subset) > 0:
                cc_in_range = subset['close_combat_happened'].sum()
                rate_in_range = cc_in_range / len(subset) * 100
                print(f"  {label:12s}: {len(subset):6,} 樣本, CC=1: {cc_in_range:5,} ({rate_in_range:5.2f}%)")
        
        print("\n❌ 關鍵發現：")
        print("   → 即使 gap 在 0.5-1.0s，CC=1 的比例也很低")
        print("   → 因為標籤要求「未來進入 0.2-0.3s」，而非「當前接近」")
    else:
        print("⚠️  找不到訓練數據檔案")
except Exception as e:
    print(f"❌ 分析失敗: {e}")

print("\n[5] 解決方案建議")
print("-" * 80)
print("✅ 方案 1：放寬標籤定義（推薦）")
print("   → close_combat_happened = 1 當「未來 5 圈 gap < 1.0s」")
print("   → 或「未來 5 圈 gap < 當前 gap * 0.5」（追近超過一半）")
print()
print("✅ 方案 2：修改預測閾值")
print("   → 當 gap < 1.5s 且 gap_trend < -0.5 時，強制 CC% >= 50%")
print("   → 當 gap < 1.0s 且 consecutive_catching_laps >= 3 時，強制 CC% >= 70%")
print()
print("✅ 方案 3：創建新標籤 'intense_battle'")
print("   → intense_battle = 1 當「gap < 1.5s 且持續追近」")
print("   → 訓練新模型 F85v2 使用這個更寬鬆的定義")

print("\n" + "=" * 80)
print("診斷完成")
print("=" * 80)
