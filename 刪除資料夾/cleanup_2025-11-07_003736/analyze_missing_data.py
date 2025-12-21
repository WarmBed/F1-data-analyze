import json

# 讀取 JSON 檔案
with open('json/all_drivers_cornering_analysis_2025_Mexico_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("分析 T13 數據缺失原因")
print("=" * 80)

# 檢查 PIA 和 ANT 的詳細信息
drivers_with_issues = ['PIA', 'ANT']

for driver_code in drivers_with_issues:
    print(f"\n🔍 車手: {driver_code}")
    print("-" * 80)
    
    # 從 fastest_lap_analysis 找到該車手
    driver_data = None
    for d in data['fastest_lap_analysis']['drivers']:
        if d['driver'] == driver_code:
            driver_data = d
            break
    
    if driver_data:
        print(f"最快圈數: Lap {driver_data['fastest_lap_number']}")
        print(f"圈速: {driver_data['lap_time']:.3f}s")
        print(f"\nT13 (low-speed corner) 數據:")
        t13 = driver_data['corners']['low_speed_corner_13']
        print(f"  - Entry 50m 速度: {t13['entry_50m_speed']}")
        print(f"  - Apex 速度: {t13['apex_speed']}")
        print(f"  - Exit 50m 速度: {t13['exit_50m_speed']}")
        
        # 檢查其他彎道數據
        print(f"\nT2 (mid-speed corner) 數據:")
        t2 = driver_data['corners']['mid_speed_corner_2']
        print(f"  - Entry 50m 速度: {t2['entry_50m_speed']}")
        print(f"  - Apex 速度: {t2['apex_speed']}")
        print(f"  - Exit 50m 速度: {t2['exit_50m_speed']}")
        
        print(f"\nT9 (high-speed corner) 數據:")
        t9 = driver_data['corners']['high_speed_corner_9']
        print(f"  - Entry 50m 速度: {t9['entry_50m_speed']}")
        print(f"  - Apex 速度: {t9['apex_speed']}")
        print(f"  - Exit 50m 速度: {t9['exit_50m_speed']}")

print("\n" + "=" * 80)
print("可能原因分析:")
print("=" * 80)
print("""
1. 賽道距離數據問題:
   - T13 的 apex_distance 是 3756.65m (接近賽道終點)
   - PIA 缺失 entry_50m_speed: 可能在 apex 前 50m 位置遙測數據不完整
   - ANT 缺失 exit_50m_speed: 可能在 apex 後 50m 位置遙測數據不完整

2. 遙測數據採樣問題:
   - FastF1 數據可能在某些賽道位置有採樣間隔
   - 最快圈的遙測數據可能在特定位置缺失

3. 賽道佈局特殊性:
   - T13 位於賽道尾段，靠近計時線
   - entry/exit 50m 範圍可能跨越計時線導致數據不連續

建議解決方案:
- 使用插值方法填補缺失的 entry/exit 速度
- 調整 entry/exit 檢測距離（如改用 40m 或 60m）
- 檢查該圈的完整遙測數據是否存在異常
""")
