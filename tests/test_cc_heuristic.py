# -*- coding: utf-8 -*-
"""
測試混合邏輯的 CC% 預測

驗證啟發式規則在 TSU vs NOR 場景下的表現

Author: F1T Team
Date: 2025-12-10
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("CC% 混合邏輯測試（模型 + 啟發式規則）")
print("=" * 80)

# TSU vs NOR 追逐場景
scenarios = [
    {
        "lap": 19,
        "gap": 3.5,
        "gap_trend": -1.0,
        "gap_trend_3lap": 0.0,
        "min_gap_last_5lap": 3.5,
        "consecutive_catching_laps": 1,
        "drs": False,
        "description": "開始追近（gap 3.5s，追近 1.0s/lap）"
    },
    {
        "lap": 20,
        "gap": 2.5,
        "gap_trend": -1.0,
        "gap_trend_3lap": -1.0,
        "min_gap_last_5lap": 2.5,
        "consecutive_catching_laps": 2,
        "drs": False,
        "description": "持續追近（gap 2.5s，連續 2 圈）"
    },
    {
        "lap": 21,
        "gap": 1.6,
        "gap_trend": -0.9,
        "gap_trend_3lap": -0.97,
        "min_gap_last_5lap": 1.6,
        "consecutive_catching_laps": 3,
        "drs": False,
        "description": "接近中（gap 1.6s，連續 3 圈追近）"
    },
    {
        "lap": 22,
        "gap": 0.6,
        "gap_trend": -1.0,
        "gap_trend_3lap": -0.97,
        "min_gap_last_5lap": 0.6,
        "consecutive_catching_laps": 4,
        "drs": True,
        "description": "極近距離（gap 0.6s，DRS 開啟）"
    }
]

print("\n場景模擬：2025 Abu Dhabi TSU vs NOR")
print("-" * 80)

try:
    from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import CloseCombatPredictor
    
    predictor = CloseCombatPredictor(verbose=False)
    
    if predictor.model is None:
        print("❌ F85 模型未載入")
        sys.exit(1)
    
    print(f"✅ F85 模型已載入 (v{predictor.model_version})\n")
    
    print(f"{'Lap':>3} | {'Gap':>5} | {'Trend':>6} | {'3Lap':>6} | {'Min5':>5} | "
          f"{'Cons':>4} | {'DRS':>3} | {'Base%':>6} | {'Boost':>6} | {'Final%':>7} | 規則")
    print("-" * 120)
    
    for s in scenarios:
        # 基礎預測
        result = predictor.predict(
            gap_seconds=s['gap'],
            gap_delta=s['gap_trend'],
            is_catching=True,
            drs_available=s['drs'],
            attacker_tyre='SOFT',
            defender_tyre='MEDIUM',
            tyre_age_diff=-5,
            track_status_green=True,
            attacker_position=2,
            race_progress=0.36,
            gap_trend_3lap=s['gap_trend_3lap'],
            min_gap_last_5lap=s['min_gap_last_5lap'],
            consecutive_catching_laps=s['consecutive_catching_laps']
        )
        
        base_prob = result.probability
        boost = 0.0
        rule = "無"
        
        # 應用啟發式規則（複製 data_manager.py 的邏輯）
        gap = s['gap']
        trend = s['gap_trend']
        trend_3lap = s['gap_trend_3lap']
        min_gap = s['min_gap_last_5lap']
        cons_laps = s['consecutive_catching_laps']
        drs = s['drs']
        
        # 規則 1: 極近距離 + DRS + 強力追近
        if gap < 1.0 and drs and trend < -0.3:
            boost = 0.6
            rule = "規則1: 極近+DRS+強追"
        
        # 規則 2: 持續強力追近（3+ 圈，平均 > 0.5s/lap）
        elif cons_laps >= 3 and trend_3lap < -0.5:
            boost = 0.4
            rule = "規則2: 3圈強追"
        
        # 規則 3: 中距離但趨勢極強
        elif 1.0 <= gap < 2.0 and trend < -0.8:
            boost = 0.35
            rule = "規則3: 中距強勢"
        
        # 規則 4: 曾經很接近且仍在追近
        elif min_gap < 1.0 and trend < -0.2:
            boost = 0.25
            rule = "規則4: 曾近仍追"
        
        # 規則 5: 近距離且穩定追近
        elif gap < 1.5 and cons_laps >= 2 and trend < -0.15:
            boost = 0.20
            rule = "規則5: 近距穩追"
        
        final_prob = min(1.0, base_prob + boost)
        
        print(f"{s['lap']:3d} | {gap:5.1f} | {trend:+6.2f} | {trend_3lap:+6.2f} | "
              f"{min_gap:5.1f} | {cons_laps:4d} | {'✓' if drs else '✗':>3} | "
              f"{base_prob*100:5.1f}% | {boost*100:+5.1f}% | {final_prob*100:6.1f}% | {rule}")
    
    print("\n" + "=" * 80)
    print("規則說明")
    print("=" * 80)
    print("規則1: gap < 1.0 & DRS & trend < -0.3       → +60% (極近距離激戰)")
    print("規則2: cons >= 3 & trend_3lap < -0.5        → +40% (持續強力追近)")
    print("規則3: 1.0 ≤ gap < 2.0 & trend < -0.8       → +35% (中距離爆發)")
    print("規則4: min_gap < 1.0 & trend < -0.2         → +25% (曾接近仍追)")
    print("規則5: gap < 1.5 & cons >= 2 & trend < -0.15 → +20% (穩定施壓)")
    
    print("\n" + "=" * 80)
    print("結果分析")
    print("=" * 80)
    print("✅ Lap 19 (3.5s): 無規則觸發，保持模型原始預測")
    print("✅ Lap 20 (2.5s): 無規則觸發（連續圈數不足）")
    print("✅ Lap 21 (1.6s): 觸發規則2（3圈強追）或規則5（近距穩追），CC% 提升")
    print("✅ Lap 22 (0.6s): 觸發規則1（極近+DRS），CC% 大幅提升至 60%+")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
