"""檢查 FP3 與 Q 之間的真實時間差異"""
import json
import glob
import statistics

files = glob.glob('json/predictionJSON/*.json')[:20]
diffs = []

for f in files:
    data = json.load(open(f, 'r', encoding='utf-8'))
    q_res = data.get('qualifying', {}).get('results', {})
    fp3 = data.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
    
    for driver in q_res:
        if driver in fp3:
            q_time = q_res[driver].get('best_time')
            fp3_time = fp3[driver].get('best_lap_time')
            
            if q_time and fp3_time and isinstance(q_time, (int, float)) and isinstance(fp3_time, (int, float)):
                diff = abs(q_time - fp3_time)
                if diff < 10:  # 排除明顯錯誤
                    diffs.append(diff)

if diffs:
    print(f"📊 FP3 vs Q 時間差異分析 (前20場, {len(diffs)}筆):")
    print(f"   平均差異: {statistics.mean(diffs):.3f} 秒")
    print(f"   中位數: {statistics.median(diffs):.3f} 秒")
    print(f"   標準差: {statistics.stdev(diffs):.3f} 秒")
    print(f"   最小值: {min(diffs):.3f} 秒")
    print(f"   最大值: {max(diffs):.3f} 秒")
    print(f"\n💡 結論: 如果平均差異 > 0.5 秒，表示 MAE 0.30s 目標非常困難")
