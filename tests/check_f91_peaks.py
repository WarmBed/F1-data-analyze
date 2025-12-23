import json
from pathlib import Path

# 找到最新的 F91 預測檔案
files = sorted(Path('json').glob('fp2_race_ml_prediction_v2_2025_Abu_Dhabi_*.json'), 
               key=lambda x: x.stat().st_mtime, reverse=True)

print(f'找到 {len(files)} 個 F91 預測檔案:\n')
for i, f in enumerate(files[:5], 1):
    import datetime
    mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
    print(f'{i}. {f.name}')
    print(f'   修改時間: {mtime.strftime("%Y-%m-%d %H:%M:%S")}')

if not files:
    print('❌ 找不到任何 F91 預測檔案！')
    exit()

latest = files[0]
print(f'\n📊 分析最新檔案: {latest.name}\n')

# 載入最新的 F91 預測
with open(latest, encoding='utf-8') as f:
    data = json.load(f)

ver_data = data['predictions']['1']
laps = ver_data['predicted_laps']

print('VER (1號車) 預測圈速分析:')
print(f'總圈數: {len(laps)}\n')

# 找出所有 > 100 秒的圈數
high_laps = [(int(k), v) for k, v in laps.items() if v > 100]
high_laps.sort()

print(f'> 100秒的異常圈數 ({len(high_laps)} 個):')
if high_laps:
    for lap, time in high_laps:
        print(f'  Lap {lap}: {time:.3f}s')
else:
    print('  ✅ 沒有異常峰值！')

# 統計正常圈速範圍
normal_laps = [v for v in laps.values() if v <= 100]
if normal_laps:
    print(f'\n正常圈速統計 (<= 100秒):')
    print(f'  最小: {min(normal_laps):.3f}s')
    print(f'  最大: {max(normal_laps):.3f}s')
    print(f'  平均: {sum(normal_laps)/len(normal_laps):.3f}s')
