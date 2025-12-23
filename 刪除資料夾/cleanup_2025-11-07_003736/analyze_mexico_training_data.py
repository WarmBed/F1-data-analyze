import pandas as pd
import json
import glob

# 載入 2022-2024 墨西哥數據
files = glob.glob('json/predictionJSON/fp_q_data_*.json')
mexico_times = []

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        metadata = data.get('metadata', {})
        
        # 只要墨西哥且 2022+
        if metadata.get('race') != 'Mexico' or metadata.get('year', 0) < 2022:
            continue
        
        year = metadata.get('year')
        qualifying = data.get('qualifying', {})
        
        for driver_code, qr in qualifying.get('results', {}).items():
            q_time = qr.get('best_time')
            if q_time:
                mexico_times.append((year, driver_code, q_time))

df = pd.DataFrame(mexico_times, columns=['year', 'driver', 'q_time'])
df['q_seconds'] = df['q_time'].apply(lambda x: pd.Timedelta(x).total_seconds() if isinstance(x, str) else x)

print("2022-2024 墨西哥 Q 時間統計:")
print(f"樣本數: {len(df)}")
print(f"平均: {df['q_seconds'].mean():.3f}s")
print(f"標準差: {df['q_seconds'].std():.3f}s")
print(f"最小: {df['q_seconds'].min():.3f}s")
print(f"最大: {df['q_seconds'].max():.3f}s")

print("\n各年統計:")
stats = df.groupby('year')['q_seconds'].agg(['count', 'mean', 'std', 'min', 'max'])
print(stats)

print("\n2025 墨西哥對比:")
mexico_2025_mean = 76.730  # 從剛才的測試結果
print(f"2022-2024 平均: {df['q_seconds'].mean():.3f}s")
print(f"2025 平均: {mexico_2025_mean:.3f}s")
print(f"差異: {mexico_2025_mean - df['q_seconds'].mean():.3f}s")
