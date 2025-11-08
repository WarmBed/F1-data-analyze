"""
測試新的 F48 邏輯（基於最高速度點回推）
測試案例：2025 China R - ALO
"""

import sys
sys.path.insert(0, "d:\\OneDrive\\Code\\F1-data-analyze")

from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import AllDriversStraightLineSpeedAnalysis
from CLI_modules.cli.data.data_loader import F1DataLoader

print("=" * 80)
print("F48 新邏輯測試：基於最高速度點回推直線段")
print("=" * 80)

# 載入數據
print("\n[1] 載入 2025 China R 數據...")
loader = F1DataLoader(year=2025, race='China', session='R')

# 創建分析器
print("[2] 創建 F48 分析器...")
analyzer = AllDriversStraightLineSpeedAnalysis(loader, 2025, 'China', 'R')

# 執行分析
print("[3] 執行分析...")
result = analyzer.analyze()

# 檢查結果
if result and result.get('success'):
    print("\n[4] 分析成功！")
    
    # 找到 ALO 的數據
    alo_data = None
    for driver in result['data']['driver_speeds']:
        if driver['driver'] == 'ALO':
            alo_data = driver
            break
    
    if alo_data:
        print("\n" + "=" * 80)
        print("ALO 分析結果")
        print("=" * 80)
        print(f"車手: {alo_data['full_name']} ({alo_data['driver']})")
        print(f"車隊: {alo_data['team']}")
        print(f"最高速度: {alo_data['max_speed_kmh']} km/h")
        print(f"圈數: {alo_data['lap_number']}")
        print(f"距離: {alo_data['distance_m']:.1f} m")
        print(f"油門: {alo_data['throttle_percent']:.0f}%")
        print(f"DRS: {alo_data['drs']}")
        
        if 'acceleration_100_300' in alo_data:
            acc = alo_data['acceleration_100_300']
            print(f"\n加速性能 (100→250 km/h):")
            print(f"  時間: {acc['time_seconds']:.2f} 秒")
            print(f"  距離: {acc['distance_meters']:.2f} 公尺")
            print(f"  平均加速度: {acc['avg_acceleration_ms2']:.2f} m/s²")
            print(f"  直線段起點速度: {acc['segment_start_speed']:.0f} km/h")
            print(f"  直線段最高速度: {acc['segment_max_speed']:.0f} km/h")
        
        print("\n" + "=" * 80)
        print("對比 F13 數據")
        print("=" * 80)
        print("F13 (comparison_telemetry): ALO_max = 328.0 km/h")
        print(f"F48 (新邏輯): max_speed = {alo_data['max_speed_kmh']} km/h")
        
        if alo_data['max_speed_kmh'] >= 320:
            print("\n✅ 成功！新邏輯捕捉到真實最高速度")
        else:
            print(f"\n❌ 仍有差異：{328 - alo_data['max_speed_kmh']} km/h")
    else:
        print("❌ 找不到 ALO 的數據")
else:
    print("❌ 分析失敗")
    if result:
        print(f"錯誤訊息: {result.get('message')}")
