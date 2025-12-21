"""
展示如何使用功能13的時間序列數據繪製圖表

範例 1: 使用距離作為 X 軸（原有功能）
範例 2: 使用時間作為 X 軸（新功能）
"""
import json
import matplotlib.pyplot as plt

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 讀取 JSON 數據
json_file = "json/comparison_telemetry_VER_LEC_2024_Australia_R_Lap1_Lap1.json"
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

time_series = data['time_series']
driver1 = time_series['driver1']
driver2 = time_series['driver2']

# 選擇要繪製的通道（速度）
speed_data1 = driver1['channels']['Speed']
speed_data2 = driver2['channels']['Speed']

# 創建雙子圖對比
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# 範例 1: 使用距離作為 X 軸（傳統方式）
ax1.plot(speed_data1['distance_meters'], speed_data1['values'], 
         color='#FF6B6B', linewidth=2, alpha=0.8, label=driver1['driver_code'])
ax1.plot(speed_data2['distance_meters'], speed_data2['values'], 
         color='#4ECDC4', linewidth=2, alpha=0.8, label=driver2['driver_code'])
ax1.set_xlabel('賽道距離 (m)', fontsize=12)
ax1.set_ylabel('速度 (km/h)', fontsize=12)
ax1.set_title('範例 1: 速度 vs 距離（傳統方式）', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)

# 範例 2: 使用時間作為 X 軸（新功能）
ax2.plot(speed_data1['time_seconds'], speed_data1['values'], 
         color='#FF6B6B', linewidth=2, alpha=0.8, label=driver1['driver_code'])
ax2.plot(speed_data2['time_seconds'], speed_data2['values'], 
         color='#4ECDC4', linewidth=2, alpha=0.8, label=driver2['driver_code'])
ax2.set_xlabel('時間 (秒)', fontsize=12)
ax2.set_ylabel('速度 (km/h)', fontsize=12)
ax2.set_title('範例 2: 速度 vs 時間（新功能 - 時間序列）', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=11)

plt.tight_layout()
plt.savefig('cache/demo_time_series_comparison.png', dpi=150, bbox_inches='tight')
print("✅ 圖表已保存到: cache/demo_time_series_comparison.png")
print("\n📊 數據統計:")
print(f"  • 距離範圍: {speed_data1['distance_meters'][0]:.2f} ~ {speed_data1['distance_meters'][-1]:.2f} m")
print(f"  • 時間範圍: {speed_data1['time_seconds'][0]:.2f} ~ {speed_data1['time_seconds'][-1]:.2f} s")
print(f"  • 圈用時: {speed_data1['time_seconds'][-1] - speed_data1['time_seconds'][0]:.2f} 秒")
print(f"  • 數據點數: {len(speed_data1['values'])} 個")
print(f"  • {driver1['driver_code']} 最高速度: {max(speed_data1['values']):.2f} km/h")
print(f"  • {driver2['driver_code']} 最高速度: {max(speed_data2['values']):.2f} km/h")

plt.show()
