"""
Mexico 2024 SC Skip 測試
"""
import sys
import fastf1
import pandas as pd
from smart_base_time_extractor import extract_base_time_robust

sys.path.insert(0, 'CLI_modules/cli/prediction')
from f92_hybrid_predictor import F92HybridPredictor

fastf1.Cache.enable_cache('f1_analysis_cache/')

print("="*80)
print("Mexico 2024 VER - SC Skip 測試")
print("="*80)

# 提取 base_time 和 SC 圈
base_time, info = extract_base_time_robust(2024, "Mexico", "VER")
sc_laps = info.get('sc_laps', [])

print(f"\n基礎資訊:")
print(f"  Base Time: {base_time:.3f}s")
print(f"  SC Laps: {sc_laps}")
print(f"  SC 圈數: {len(sc_laps)}")

# 進站策略
stints = [(1, 26, "MEDIUM"), (27, 71, "HARD")]

# 測試 1: 不跳過 SC 圈（舊版行為）
print(f"\n{'='*80}")
print("測試 1: 不跳過 SC 圈（舊版）")
print("="*80)

f92 = F92HybridPredictor()
result_old = f92.predict(
    year=2024, race="Mexico", driver="VER",
    base_time=base_time,
    stints=stints,
    skip_laps=[],  # ← 不跳過
    use_ml=True
)

if result_old:
    print(f"  MAE:  {result_old.get('mae', 'N/A'):.3f}s")
    print(f"  Bias: {result_old.get('mean_error', 0):+.3f}s")
    print(f"  預測圈數: {len(result_old.get('predictions', []))}")

# 測試 2: 跳過 SC 圈（新版）
print(f"\n{'='*80}")
print("測試 2: 跳過 SC 圈（新版）")
print("="*80)

result_new = f92.predict(
    year=2024, race="Mexico", driver="VER",
    base_time=base_time,
    stints=stints,
    skip_laps=sc_laps,  # ← 跳過 SC 圈
    use_ml=True
)

if result_new:
    print(f"  MAE:  {result_new.get('mae', 'N/A'):.3f}s")
    print(f"  Bias: {result_new.get('mean_error', 0):+.3f}s")
    print(f"  預測圈數: {len(result_new.get('predictions', []))}")

# 比較
print(f"\n{'='*80}")
print("比較結果")
print("="*80)

if result_old and result_new:
    mae_old = result_old.get('mae', 0)
    mae_new = result_new.get('mae', 0)
    improvement = ((mae_old - mae_new) / mae_old) * 100
    
    print(f"  舊版 MAE: {mae_old:.3f}s")
    print(f"  新版 MAE: {mae_new:.3f}s")
    print(f"  改善率:  {improvement:+.1f}%")
    
    if mae_new < mae_old:
        print(f"\n  ✅ SC Skip 有效！誤差減少 {mae_old - mae_new:.3f}s")
    else:
        print(f"\n  ⚠️  SC Skip 未改善（可能 SC 圈已被過濾）")
else:
    print("  ❌ 測試失敗")

print(f"\n{'='*80}")
print("✅ 測試完成")
print("="*80)
