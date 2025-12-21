"""
USA 2025 勝率預測分析

分析每一圈的 P1%/P2%/P3% 預測準確率
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "live_win_probability"
MODEL_DIR = ROOT_DIR / "models"

print("=" * 80)
print("USA 2025 勝率預測逐圈分析")
print("=" * 80)

# 載入驗證數據
val_df = pd.read_csv(DATA_DIR / "validation_data.csv")

# 篩選 USA 數據
usa_df = val_df[val_df['race_name'].str.contains('United_States', case=False, na=False)].copy()
print(f"\nUSA 2025 樣本數: {len(usa_df)}")

if len(usa_df) == 0:
    print("找不到 USA 數據!")
    exit()

# 載入模型
model_path = MODEL_DIR / "win_probability_xgb_v2.pkl"
with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
feature_cols = model_data['feature_columns']
print(f"模型特徵數: {len(feature_cols)}")

# 添加衍生特徵
usa_df['position_delta'] = usa_df['qualifying_position'] - usa_df['position']
usa_df['log_gap'] = np.log1p(usa_df['gap_to_leader'].abs())
usa_df['race_progress'] = 1 - (usa_df['laps_remaining'] / usa_df['laps_remaining'].max())

# 預測
X = usa_df[feature_cols].values
y_true = usa_df['final_position'].values
y_pred = model.predict(X)

usa_df['predicted_position'] = y_pred
usa_df['error'] = np.abs(usa_df['final_position'] - usa_df['predicted_position'])

# 計算排名並生成機率
def calc_probabilities(group):
    """計算每圈的 P1%/P2%/P3%"""
    pred_positions = group['predicted_position'].values
    sorted_indices = np.argsort(pred_positions)
    ranks = np.empty_like(sorted_indices)
    ranks[sorted_indices] = np.arange(1, len(pred_positions) + 1)
    
    p1_probs = 1 / (1 + np.exp((ranks - 1.5) * 1.8))
    p2_probs = 1 / (1 + np.exp((ranks - 2.5) * 1.5))
    p3_probs = 1 / (1 + np.exp((ranks - 3.5) * 1.2))
    
    group['p1_prob'] = p1_probs * 100
    group['p2_prob'] = p2_probs * 100
    group['p3_prob'] = p3_probs * 100
    group['predicted_rank'] = ranks
    
    return group

# 計算每圈數據 (用 current_lap 作為圈數)
usa_df = usa_df.groupby('current_lap', group_keys=False).apply(calc_probabilities)

# 獲取實際比賽結果
actual_results = usa_df.groupby('driver_code')['final_position'].first().to_dict()
print(f"\n實際比賽結果:")
for driver, pos in sorted(actual_results.items(), key=lambda x: x[1]):
    print(f"  P{int(pos)}: {driver}")

# 獲取總圈數
total_laps = usa_df['current_lap'].max()
print(f"\n總圈數: {total_laps}")

# 逐圈分析
print("\n" + "=" * 80)
print("逐圈預測分析")
print("=" * 80)

lap_results = []

for lap in sorted(usa_df['current_lap'].unique()):
    lap_data = usa_df[usa_df['current_lap'] == lap].copy()
    
    # 計算該圈的指標
    mae = lap_data['error'].mean()
    top1_acc = (lap_data['error'] <= 1).mean() * 100
    top3_acc = (lap_data['error'] <= 3).mean() * 100
    
    # 預測 P1 準確率
    pred_p1_mask = lap_data['predicted_rank'] == 1
    actual_p1_mask = lap_data['final_position'] == 1
    p1_correct = (pred_p1_mask == actual_p1_mask).mean() * 100
    
    # 預測 P3 準確率
    pred_p3_mask = lap_data['predicted_rank'] <= 3
    actual_p3_mask = lap_data['final_position'] <= 3
    p3_correct = (pred_p3_mask == actual_p3_mask).mean() * 100
    
    # 獲取該圈 Top 3 預測
    top3_pred = lap_data.nsmallest(3, 'predicted_position')[['driver_code', 'p1_prob', 'predicted_position']].values.tolist()
    
    # 獲取實際 P1 的預測
    actual_p1_driver = [d for d, p in actual_results.items() if p == 1][0]
    actual_p1_data = lap_data[lap_data['driver_code'] == actual_p1_driver]
    if len(actual_p1_data) > 0:
        actual_p1_predicted_prob = actual_p1_data['p1_prob'].values[0]
        actual_p1_predicted_pos = actual_p1_data['predicted_position'].values[0]
    else:
        actual_p1_predicted_prob = 0
        actual_p1_predicted_pos = 0
    
    lap_results.append({
        'lap': lap,
        'laps_remaining': total_laps - lap,
        'mae': mae,
        'top1_acc': top1_acc,
        'top3_acc': top3_acc,
        'p1_correct': p1_correct,
        'p3_correct': p3_correct,
        'top3_pred': top3_pred,
        'actual_p1_driver': actual_p1_driver,
        'actual_p1_prob': actual_p1_predicted_prob,
        'actual_p1_pred_pos': actual_p1_predicted_pos,
    })

# 輸出詳細報告
print(f"\n{'圈數':>4} {'剩餘':>4} {'MAE':>6} {'Top1%':>7} {'Top3%':>7} {'P1正確':>7} {'P3正確':>7} | {'預測P1':>10} {'實際P1機率':>10}")
print("-" * 100)

for r in lap_results:
    top1_driver = r['top3_pred'][0][0] if r['top3_pred'] else '-'
    print(f"{r['lap']:>4} {r['laps_remaining']:>4} {r['mae']:>6.2f} {r['top1_acc']:>6.1f}% {r['top3_acc']:>6.1f}% {r['p1_correct']:>6.1f}% {r['p3_correct']:>6.1f}% | {top1_driver:>10} {r['actual_p1_prob']:>9.1f}%")

# 階段性統計
print("\n" + "=" * 80)
print("階段性統計")
print("=" * 80)

stages = [
    (1, 10, "開始階段 (1-10圈)"),
    (11, 20, "前期 (11-20圈)"),
    (21, 35, "中期 (21-35圈)"),
    (36, 45, "後期 (36-45圈)"),
    (46, 999, "最後階段 (46圈+)"),
]

print(f"\n{'階段':<20} {'MAE':>8} {'Top1%':>8} {'Top3%':>8} {'P1正確':>8} {'實際P1平均機率':>15}")
print("-" * 75)

for start, end, name in stages:
    stage_data = [r for r in lap_results if start <= r['lap'] <= end]
    if not stage_data:
        continue
    
    avg_mae = np.mean([r['mae'] for r in stage_data])
    avg_top1 = np.mean([r['top1_acc'] for r in stage_data])
    avg_top3 = np.mean([r['top3_acc'] for r in stage_data])
    avg_p1_correct = np.mean([r['p1_correct'] for r in stage_data])
    avg_actual_p1_prob = np.mean([r['actual_p1_prob'] for r in stage_data])
    
    print(f"{name:<20} {avg_mae:>8.2f} {avg_top1:>7.1f}% {avg_top3:>7.1f}% {avg_p1_correct:>7.1f}% {avg_actual_p1_prob:>14.1f}%")

# 關鍵圈數詳細預測
print("\n" + "=" * 80)
print("關鍵圈數 Top 5 預測詳情")
print("=" * 80)

key_laps = [1, 10, 20, 30, 40, total_laps - 5, total_laps - 1, total_laps]
key_laps = [l for l in key_laps if l <= total_laps and l > 0]

for lap in key_laps:
    lap_data = usa_df[usa_df['current_lap'] == lap].copy()
    if len(lap_data) == 0:
        continue
        
    print(f"\n第 {lap} 圈 (剩餘 {total_laps - lap} 圈):")
    print(f"{'排名':>4} {'車手':>6} {'預測位置':>10} {'P1%':>8} {'P2%':>8} {'P3%':>8} {'實際位置':>10}")
    print("-" * 65)
    
    top5 = lap_data.nsmallest(5, 'predicted_position')
    for _, row in top5.iterrows():
        print(f"{int(row['predicted_rank']):>4} {row['driver_code']:>6} {row['predicted_position']:>10.2f} {row['p1_prob']:>7.1f}% {row['p2_prob']:>7.1f}% {row['p3_prob']:>7.1f}% {int(row['final_position']):>10}")

# 輸出最終結論
print("\n" + "=" * 80)
print("結論")
print("=" * 80)

# 找出模型預測最準確的時間點
best_lap = max(lap_results, key=lambda x: x['top3_acc'])
worst_lap = min(lap_results, key=lambda x: x['top3_acc'])

print(f"""
USA 2025 勝率預測分析結論:

1. 實際比賽結果: P1={actual_results.get('VER', actual_results.get('NOR', '-'))}, 
   實際獲勝車手在最後一圈的預測 P1%: {lap_results[-1]['actual_p1_prob']:.1f}%

2. 最佳預測圈數: 第 {best_lap['lap']} 圈 (Top-3 準確率: {best_lap['top3_acc']:.1f}%)

3. 最差預測圈數: 第 {worst_lap['lap']} 圈 (Top-3 準確率: {worst_lap['top3_acc']:.1f}%)

4. 整體表現:
   - 平均 MAE: {np.mean([r['mae'] for r in lap_results]):.2f}
   - 平均 Top-1 準確率: {np.mean([r['top1_acc'] for r in lap_results]):.1f}%
   - 平均 Top-3 準確率: {np.mean([r['top3_acc'] for r in lap_results]):.1f}%
""")
