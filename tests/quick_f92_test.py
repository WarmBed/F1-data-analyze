"""
F92 快速測試 - 僅輸出關鍵結果
"""
import sys
import fastf1
from smart_base_time_extractor import extract_base_time_robust

sys.path.insert(0, 'CLI_modules/cli/prediction')
from f92_hybrid_predictor import F92HybridPredictor

# 禁用緩存訊息
fastf1.Cache.enable_cache('f1_analysis_cache/')

f92 = F92HybridPredictor()

print("="*80)
print("Japan 2025 VER")
print("="*80)
base_time_j, info_j = extract_base_time_robust(2025, "Japan", "VER")
result_j = f92.predict(
    year=2025, race="Japan", driver="VER",
    base_time=base_time_j,
    stints=[(1, 21, "MEDIUM"), (22, 53, "HARD")],
    skip_laps=info_j.get('sc_laps', []),
    use_ml=True
)
print(f"\nJapan MAE: {result_j.get('mae', 'N/A')}")
print(f"Japan Bias: {result_j.get('mean_error', 'N/A')}")

print("\n" + "="*80)
print("Mexico 2024 VER")
print("="*80)
base_time_m, info_m = extract_base_time_robust(2024, "Mexico", "VER")
print(f"Base Time: {base_time_m:.3f}s")
print(f"SC Laps: {info_m.get('sc_laps', [])}")
result_m = f92.predict(
    year=2024, race="Mexico", driver="VER",
    base_time=base_time_m,
    stints=[(1, 26, "MEDIUM"), (27, 71, "HARD")],
    skip_laps=info_m.get('sc_laps', []),
    use_ml=True
)
print(f"\nMexico MAE: {result_m.get('mae', 'N/A')}")
print(f"Mexico Bias: {result_m.get('mean_error', 'N/A')}")

print("\n" + "="*80)
print("總結")
print("="*80)
print(f"Japan:  MAE={result_j.get('mae', 'N/A'):.3f}s, Bias={result_j.get('mean_error', 0):+.3f}s")
print(f"Mexico: MAE={result_m.get('mae', 'N/A'):.3f}s, Bias={result_m.get('mean_error', 0):+.3f}s")
print(f"\n✅ SC Skip 已啟用: Japan {len(info_j.get('sc_laps', []))} 圈, Mexico {len(info_m.get('sc_laps', []))} 圈")
