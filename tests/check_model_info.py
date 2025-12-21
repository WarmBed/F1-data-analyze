import pickle
import datetime
from pathlib import Path

model_file = Path('models/fp2_race_ml_v2.0/Yas_Island.pkl')
data = pickle.load(open(model_file, 'rb'))

trained_time = datetime.datetime.fromisoformat(data['trained_at'])

print('Yas_Island 模型資訊:')
print(f'  訓練時間: {trained_time.strftime("%Y-%m-%d %H:%M:%S")}')
print(f'  訓練樣本: {data["training_samples"]}')
print(f'  訓練圈數: {data["total_laps_trained"]}')
print(f'  MAE: {data["mae"]:.6f}')
print(f'  R²: {data["r2"]:.6f}')
print(f'\n  訓練的圈數範圍:')
print(f'  第1個圈: {data["label_cols"][0]}')
print(f'  最後1個圈: {data["label_cols"][-1]}')
print(f'  總共: {len(data["label_cols"])} 個圈數')

# 檢查是否包含異常圈數
print(f'\n  檢查是否包含可能的 pit lap:')
for lap_col in data["label_cols"]:
    lap_num = int(lap_col.replace("race_lap_", ""))
    if lap_num in [3, 15, 26, 34, 38]:  # 異常圈數
        print(f'    ⚠️  包含異常圈: {lap_col}')
