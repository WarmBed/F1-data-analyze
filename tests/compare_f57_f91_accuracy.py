import json
import numpy as np

# 載入 Real 數據
with open('json/LiveF1/2025/Abu_Dhabi_Race/TimingData.json', encoding='utf-8') as f:
    real_data = json.load(f)

# 載入 F57 預測
with open('json/combined_laptime_2025_Abu_Dhabi_R_20251213_025407.json', encoding='utf-8') as f:
    f57_data = json.load(f)

# 載入最新 F91 預測
with open('json/fp2_race_ml_prediction_v2_2025_Abu_Dhabi_20251213_041436.json', encoding='utf-8') as f:
    f91_data = json.load(f)

# 解析 Real 數據（VER - 車號 1）
real_laps = {}
for record in real_data.get('records', []):
    lines = record.get('Lines', {})
    if '1' in lines:  # VER
        lap_num = lines['1'].get('NumberOfLaps')
        last_time_str = lines['1'].get('LastLapTime', {}).get('Value', '')
        
        if lap_num and last_time_str and ':' in last_time_str:
            try:
                parts = last_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                lap_time = minutes * 60 + seconds
                
                # 過濾進站圈
                if lap_time < 110:
                    real_laps[lap_num] = lap_time
            except:
                pass

# 解析 F57 預測
f57_predictions = f57_data['drivers']['1']['predictions']

# 解析 F91 預測
f91_predictions = f91_data['predictions']['1']['predicted_laps']

# 計算誤差（只比較有 Real 數據的圈數）
print("\n" + "="*60)
print("F57 vs F91 準確度對比分析 - VER (2025 Abu Dhabi GP)")
print("="*60)

# 統計資訊
f57_errors = []
f91_errors = []
comparison_laps = []

for lap_str, real_time in real_laps.items():
    lap_num = int(lap_str)
    
    # F57 預測（索引是 lap_num - 1）
    if lap_num - 1 < len(f57_predictions):
        f57_pred = f57_predictions[lap_num - 1]
        f57_error = abs(f57_pred - real_time)
        f57_errors.append(f57_error)
    else:
        f57_pred = None
        f57_error = None
    
    # F91 預測
    if str(lap_num) in f91_predictions:
        f91_pred = f91_predictions[str(lap_num)]
        f91_error = abs(f91_pred - real_time)
        f91_errors.append(f91_error)
    else:
        f91_pred = None
        f91_error = None
    
    comparison_laps.append({
        'lap': lap_num,
        'real': real_time,
        'f57': f57_pred,
        'f91': f91_pred,
        'f57_error': f57_error,
        'f91_error': f91_error
    })

# 計算統計指標
print(f"\n有效對比圈數: {len(f57_errors)} 圈")
print(f"\n{'方法':<10} {'MAE (秒)':<12} {'最大誤差':<12} {'最小誤差':<12} {'標準差':<12}")
print("-" * 60)

f57_mae = np.mean(f57_errors)
f57_max = np.max(f57_errors)
f57_min = np.min(f57_errors)
f57_std = np.std(f57_errors)

print(f"{'F57':<10} {f57_mae:<12.3f} {f57_max:<12.3f} {f57_min:<12.3f} {f57_std:<12.3f}")

f91_mae = np.mean(f91_errors)
f91_max = np.max(f91_errors)
f91_min = np.min(f91_errors)
f91_std = np.std(f91_errors)

print(f"{'F91':<10} {f91_mae:<12.3f} {f91_max:<12.3f} {f91_min:<12.3f} {f91_std:<12.3f}")

# 改進百分比
improvement = ((f57_mae - f91_mae) / f57_mae) * 100
print(f"\n{'='*60}")
if f91_mae < f57_mae:
    print(f"✅ F91 比 F57 準確 {improvement:.1f}%")
else:
    print(f"❌ F91 比 F57 差 {abs(improvement):.1f}%")
print(f"{'='*60}")

# 詳細對比前 20 圈
print(f"\n詳細對比（前 20 圈）:")
print(f"{'圈數':<6} {'Real':<10} {'F57':<10} {'F91':<10} {'F57誤差':<10} {'F91誤差':<10} {'勝者':<6}")
print("-" * 70)

for lap_data in comparison_laps[:20]:
    lap = lap_data['lap']
    real = lap_data['real']
    f57 = lap_data['f57']
    f91 = lap_data['f91']
    f57_err = lap_data['f57_error']
    f91_err = lap_data['f91_error']
    
    if f57_err is not None and f91_err is not None:
        winner = 'F91 ✓' if f91_err < f57_err else 'F57 ✓'
        print(f"{lap:<6} {real:<10.3f} {f57:<10.3f} {f91:<10.3f} {f57_err:<10.3f} {f91_err:<10.3f} {winner:<6}")

# 統計勝率
f91_wins = sum(1 for ld in comparison_laps if ld['f91_error'] is not None and ld['f57_error'] is not None and ld['f91_error'] < ld['f57_error'])
f57_wins = sum(1 for ld in comparison_laps if ld['f91_error'] is not None and ld['f57_error'] is not None and ld['f57_error'] < ld['f91_error'])

print(f"\n逐圈勝率統計:")
print(f"  F91 更準: {f91_wins} 圈 ({f91_wins/len(comparison_laps)*100:.1f}%)")
print(f"  F57 更準: {f57_wins} 圈 ({f57_wins/len(comparison_laps)*100:.1f}%)")
