"""調試 USA 第 30 圈預測問題"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "live_win_probability"
MODEL_DIR = ROOT_DIR / "models"

# 載入數據
val_df = pd.read_csv(DATA_DIR / "validation_data.csv")
usa_df = val_df[val_df['race_name'].str.contains('United_States', case=False, na=False)].copy()

# 載入模型
with open(MODEL_DIR / "win_probability_xgb_v2.pkl", 'rb') as f:
    model_data = pickle.load(f)
model = model_data['model']
feature_cols = model_data['feature_columns']

# 添加衍生特徵
usa_df['position_delta'] = usa_df['qualifying_position'] - usa_df['position']
usa_df['log_gap'] = np.log1p(usa_df['gap_to_leader'].abs())
usa_df['race_progress'] = 1 - (usa_df['laps_remaining'] / usa_df['laps_remaining'].max())

# 篩選第 30 圈
lap30 = usa_df[usa_df['current_lap'] == 30].copy()
print(f"第 30 圈樣本數: {len(lap30)}")
print()

# 預測
X = lap30[feature_cols].values
predicted_positions = model.predict(X)
lap30['predicted_position'] = predicted_positions

# 按當前位置排序顯示
lap30_sorted = lap30.sort_values('position')

print("第 30 圈預測結果 (按當前位置排序):")
print(f"{'當前位置':>8} {'車手':>6} {'預測位置':>10} {'實際結果':>10}")
print("-" * 45)

for _, row in lap30_sorted.iterrows():
    print(f"{int(row['position']):>8} {row['driver_code']:>6} {row['predicted_position']:>10.2f} {int(row['final_position']):>10}")

# 模擬 _convert_to_probabilities
print("\n" + "=" * 60)
print("模擬 _convert_to_probabilities 的排名計算:")
print("=" * 60)

# 按字典遍歷順序（模擬實際情況）
driver_codes = lap30['driver_code'].tolist()
pred_positions = lap30['predicted_position'].values

# 計算排名
sorted_indices = np.argsort(pred_positions)
ranks = np.empty_like(sorted_indices)
ranks[sorted_indices] = np.arange(1, len(pred_positions) + 1)

print(f"\n{'遍歷順序':>8} {'車手':>6} {'預測位置':>10} {'計算排名':>10} {'P1% (理論)':>12}")
print("-" * 55)

for i, (driver, pred_pos, rank) in enumerate(zip(driver_codes, pred_positions, ranks)):
    p1 = 1 / (1 + np.exp((rank - 1.5) * 1.8))
    print(f"{i+1:>8} {driver:>6} {pred_pos:>10.2f} {rank:>10} {p1*100:>11.1f}%")

# 找出誰被分配了排名 1
rank1_idx = np.where(ranks == 1)[0][0]
print(f"\n排名 1 被分配給: {driver_codes[rank1_idx]} (預測位置: {pred_positions[rank1_idx]:.2f})")

# 按預測位置排序顯示
print("\n" + "=" * 60)
print("按預測位置排序 (正確的勝率分配):")
print("=" * 60)

lap30_by_pred = lap30.sort_values('predicted_position')
print(f"\n{'預測排名':>8} {'車手':>6} {'當前位置':>10} {'預測位置':>10} {'P1%':>8}")
print("-" * 50)

for rank, (_, row) in enumerate(lap30_by_pred.iterrows(), 1):
    p1 = 1 / (1 + np.exp((rank - 1.5) * 1.8))
    print(f"{rank:>8} {row['driver_code']:>6} {int(row['position']):>10} {row['predicted_position']:>10.2f} {p1*100:>7.1f}%")
