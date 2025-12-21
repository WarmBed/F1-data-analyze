import json
from pathlib import Path

# 找到最新的 F91 預測檔案
json_dir = Path('json')
files = sorted(json_dir.glob('fp2_race_ml_prediction_v2_2025_Abu_Dhabi_*.json'), 
               key=lambda x: x.stat().st_mtime, reverse=True)

if not files:
    print("找不到 F91 預測檔案！")
    exit()

latest_file = files[0]
print(f'檢查檔案: {latest_file.name}\n')

# 載入數據
with open(latest_file, encoding='utf-8') as f:
    data = json.load(f)

ver_data = data['predictions']['1']
laps = ver_data['predicted_laps']

print('VER (1號車) 預測圈速分析:')
print(f'總圈數: {len(laps)}\n')

# 找出所有 > 95 秒的圈數
high_laps = [(int(k), v) for k, v in laps.items() if v > 95]
high_laps.sort()

print(f'> 95秒的圈數 ({len(high_laps)} 個):')
for lap, time in high_laps:
    print(f'  Lap {lap}: {time:.3f}s')

# 統計
lap_times = list(laps.values())
avg = sum(lap_times) / len(lap_times)
threshold = avg * 1.15

print(f'\n平均圈速: {avg:.3f}s')
print(f'異常閾值 (平均*1.15): {threshold:.3f}s')
print(f'\n超出閾值的圈數:')
outliers = [(k,v) for k,v in high_laps if v > threshold]
if outliers:
    for k, v in outliers:
        print(f'  Lap {k}: {v:.3f}s (超出 {v-threshold:.3f}s)')
else:
    print('  無')
