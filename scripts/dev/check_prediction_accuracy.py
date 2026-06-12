"""檢查預測準確度 - 診斷燃油校正問題"""
import json
from pathlib import Path

# 讀取 Abu Dhabi JSON
json_path = Path("json/fp2_qualifying_prediction_2025_Abu Dhabi.json")
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== Abu Dhabi 2025 預測 vs 實際 Q ===")
print(f"燃油校正啟用: {data['metadata'].get('fuel_correction_enabled')}")
print()

predictions = data['predictions']
print(f"{'車手':<5} {'FP2時間':>10} {'預測時間':>10} {'Q實際':>10} {'預測誤差':>10} {'燃油校正':>10}")
print("-" * 70)

total_error = 0
count = 0
for p in predictions[:17]:
    driver = p['driver']
    fp2 = p['fp2_time']
    pred = p['predicted_time']  # 修正欄位名
    actual = p.get('actual_q_time')
    fuel_corr = p.get('fuel_correction', 0)
    
    if actual:
        error = pred - actual
        total_error += abs(error)
        count += 1
        print(f"{driver:<5} {fp2:>10.3f} {pred:>10.3f} {actual:>10.3f} {error:>+10.3f} {fuel_corr:>10.3f}")
    else:
        print(f"{driver:<5} {fp2:>10.3f} {pred:>10.3f} {'N/A':>10} {'N/A':>10} {fuel_corr:>10.3f}")

if count > 0:
    print(f"\n平均絕對誤差 (MAE): {total_error/count:.3f}s")

# 檢查車隊燃油習慣
print("\n\n=== 車隊燃油習慣檢查 ===")
habits_path = Path("training_data/team_fuel_habits.json")
with open(habits_path, 'r', encoding='utf-8') as f:
    habits = json.load(f)

print(f"{'車隊':<20} {'校正秒數':>10} {'QS樣本數':>10}")
print("-" * 45)
for team, info in habits['teams'].items():
    corr = info.get('fuel_correction_seconds', 0)
    samples = info.get('quali_sim_samples', 0)
    if corr:
        print(f"{team:<20} {corr:>10.3f} {samples:>10}")

# 比較：不使用燃油校正的情況
print("\n\n=== 如果不使用燃油校正 (原本預測 + 燃油校正 = 現有預測) ===")
print(f"{'車手':<5} {'現有預測':>10} {'燃油校正':>10} {'原本預測':>10} {'Q實際':>10} {'原本誤差':>10}")
print("-" * 70)

total_error_orig = 0
count_orig = 0
for p in predictions[:10]:
    driver = p['driver']
    pred = p['predicted_time']  # 修正欄位名
    actual = p.get('actual_q_time')
    fuel_corr = p.get('fuel_correction', 0)
    
    # 還原原本預測 (不含燃油校正)
    orig_pred = pred + fuel_corr  # 因為現有 = 原本 - 燃油校正
    
    if actual:
        error_orig = orig_pred - actual
        total_error_orig += abs(error_orig)
        count_orig += 1
        print(f"{driver:<5} {pred:>10.3f} {fuel_corr:>10.3f} {orig_pred:>10.3f} {actual:>10.3f} {error_orig:>+10.3f}")

if count_orig > 0:
    print(f"\n不使用燃油校正的 MAE: {total_error_orig/count_orig:.3f}s")
    print(f"使用燃油校正的 MAE: {total_error/count:.3f}s")
    print(f"差異: {total_error_orig/count_orig - total_error/count:+.3f}s")
