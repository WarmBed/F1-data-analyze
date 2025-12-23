"""
調試腳本：比較 GUI 和 MD 分析的數據差異
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "live_win_probability"
MODEL_DIR = ROOT_DIR / "models"

print("=" * 80)
print("調試：GUI vs MD 分析差異")
print("=" * 80)

# 載入驗證數據 (這是 MD 分析使用的)
val_df = pd.read_csv(DATA_DIR / "validation_data.csv")

# 篩選 USA 數據，第 30 圈
usa_df = val_df[val_df['race_name'].str.contains('United_States', case=False, na=False)].copy()
lap30 = usa_df[usa_df['current_lap'] == 30].copy()

print(f"\n=== MD 分析數據 (第 30 圈) ===")
print(f"樣本數: {len(lap30)}")
print(f"\n欄位: {list(lap30.columns)}")

# 顯示第 30 圈的關鍵數據
print(f"\n關鍵特徵 (前 6 位):")
print(f"{'車手':<6} {'position':>10} {'gap_to_leader':>15} {'lap_time':>12} {'final_pos':>10}")
print("-" * 60)

for _, row in lap30.sort_values('position').head(6).iterrows():
    print(f"{row['driver_code']:<6} {row['position']:>10} {row['gap_to_leader']:>15.3f} {row['lap_time']:>12.3f} {int(row['final_position']):>10}")

# 載入模型並預測
model_path = MODEL_DIR / "win_probability_xgb_v2.pkl"
with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
feature_cols = model_data['feature_columns']

# 添加衍生特徵
lap30['position_delta'] = lap30['qualifying_position'] - lap30['position']
lap30['log_gap'] = np.log1p(lap30['gap_to_leader'].abs())
lap30['race_progress'] = 1 - (lap30['laps_remaining'] / lap30['laps_remaining'].max())

# 預測
X = lap30[feature_cols].values
predicted_positions = model.predict(X)
lap30['predicted_position'] = predicted_positions

# 計算排名和機率
sorted_indices = np.argsort(predicted_positions)
ranks = np.empty_like(sorted_indices)
ranks[sorted_indices] = np.arange(1, len(predicted_positions) + 1)
lap30['predicted_rank'] = ranks

p1_probs = 1 / (1 + np.exp((ranks - 1.5) * 1.8))
lap30['p1_prob'] = p1_probs * 100

print(f"\n=== 模型預測結果 (第 30 圈) ===")
print(f"{'車手':<6} {'當前位置':>10} {'預測位置':>12} {'預測排名':>10} {'P1%':>8}")
print("-" * 55)

for _, row in lap30.sort_values('predicted_position').head(6).iterrows():
    print(f"{row['driver_code']:<6} {int(row['position']):>10} {row['predicted_position']:>12.2f} {int(row['predicted_rank']):>10} {row['p1_prob']:>7.1f}%")

# 現在模擬 GUI 的情況
print(f"\n\n=== 模擬 GUI 傳入的數據 ===")
print("GUI 可能傳入的 driver_data 欄位:")
print("  - position: 來自 snapshot['drivers'][num]['position']")
print("  - gap_to_leader: 來自 snapshot['drivers'][num]['gap_to_leader']")
print("  - last_lap_time: 來自 snapshot['drivers'][num]['last_lap_time']")
print("")
print("❗ 問題可能在於：")
print("  1. GUI 的 position 欄位名稱或格式不一致")
print("  2. GUI 的 gap_to_leader 是字串格式（如 '+5.234s'）而非數字")
print("  3. GUI 的 lap_time 是字串格式（如 '1:32.456'）而非秒數")
print("")
print("讓我們檢查 predictor 如何解析這些值...")

# 模擬 GUI 傳入字串格式的數據
def simulate_gui_parse(gap_str, lap_time_str):
    """模擬 predictor 的解析邏輯"""
    # 解析 gap
    if gap_str is None:
        gap = 0.0
    elif isinstance(gap_str, (int, float)):
        gap = float(gap_str)
    elif isinstance(gap_str, str):
        gap_str = gap_str.strip()
        if gap_str.startswith('+'):
            gap_str = gap_str[1:]
        if 'L' in gap_str.upper():
            try:
                laps = int(gap_str.upper().replace('L', '').strip())
                gap = laps * 90.0
            except:
                gap = 90.0
        else:
            try:
                gap = float(gap_str)
            except:
                gap = 0.0
    else:
        gap = 0.0
    
    # 解析 lap_time
    if not lap_time_str:
        lap_time = 90.0
    else:
        try:
            if ':' in str(lap_time_str):
                parts = str(lap_time_str).split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                lap_time = minutes * 60 + seconds
            else:
                lap_time = float(lap_time_str)
        except:
            lap_time = 90.0
    
    return gap, lap_time

# 測試解析
test_cases = [
    ("+5.234", "1:32.456"),
    ("5.234", "92.456"),
    (5.234, 92.456),
    (None, None),
]

print(f"\n測試 predictor 解析邏輯:")
print(f"{'gap 輸入':<15} {'lap_time 輸入':<15} {'解析後 gap':>12} {'解析後 lap_time':>15}")
print("-" * 60)
for gap_in, lap_in in test_cases:
    gap_out, lap_out = simulate_gui_parse(gap_in, lap_in)
    print(f"{str(gap_in):<15} {str(lap_in):<15} {gap_out:>12.3f} {lap_out:>15.3f}")

print(f"\n\n=== 結論 ===")
print("""
如果 GUI 顯示的 P1% 與 MD 分析不一致，可能原因：

1. **欄位名稱不一致**
   - MD 使用: 'position', 'gap_to_leader', 'lap_time'
   - GUI 可能使用: 'Position', 'GapToLeader', 'LastLapTime' 等

2. **數據格式不一致**
   - MD 訓練數據: 數值格式 (position=1, gap_to_leader=0.0)
   - GUI 即時數據: 可能是字串格式 (position='1', gap_to_leader='+0.000s')

3. **預設值問題**
   - 如果 GUI 傳入的欄位不存在，predictor 使用預設值
   - position 預設 = 10 (如果讀不到)
   - gap_to_leader 預設 = 0 (如果讀不到)

4. **排名計算差異**
   - MD 是批次處理所有數據
   - GUI 是即時處理，可能只有部分車手數據

建議：在 predictor.py 中添加調試輸出，打印實際收到的 driver_data。
""")
