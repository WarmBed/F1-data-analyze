"""
檢查 Abu Dhabi 2025 R 的 High-Speed Corner 分析中是否有 VER 的資料
"""

import json
from pathlib import Path

def check_ver_in_highspeed_corner():
    """檢查 VER 在高速彎的資料"""
    
    json_file = Path("json/all_drivers_cornering_analysis_2025_Abu Dhabi_R.json")
    
    if not json_file.exists():
        print(f"❌ 找不到檔案: {json_file}")
        return
    
    print("=" * 80)
    print("檢查 Abu Dhabi 2025 R - High-Speed Corner Analysis 中的 VER 資料")
    print("=" * 80)
    
    # 載入數據
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查頂層結構
    print("\n1️⃣ 頂層鍵值:")
    print(f"   {list(data.keys())}")
    
    # 檢查選擇的彎道
    selected_corners = data.get('selected_corners', {})
    print(f"\n2️⃣ 選擇的彎道類型:")
    print(f"   {list(selected_corners.keys())}")
    
    # 檢查高速彎資訊
    high_speed_corner = selected_corners.get('high_speed', {})
    print(f"\n3️⃣ 高速彎資訊:")
    print(f"   彎道編號: {high_speed_corner.get('corner_number')}")
    print(f"   彎道名稱: {high_speed_corner.get('corner_name')}")
    print(f"   平均頂點速度: {high_speed_corner.get('avg_apex_speed')} km/h")
    
    # 檢查最快圈分析
    fastest_lap_analysis = data.get('fastest_lap_analysis', {})
    print(f"\n4️⃣ 最快圈分析:")
    print(f"   描述: {fastest_lap_analysis.get('description')}")
    print(f"   總車手數: {fastest_lap_analysis.get('total_drivers')}")
    
    drivers = fastest_lap_analysis.get('drivers', [])
    if drivers:
        driver_list = sorted([d.get('driver') for d in drivers])
        print(f"   車手清單: {driver_list}")
        
        # 尋找 VER
        ver_data = None
        for driver_data in drivers:
            if driver_data.get('driver') == 'VER':
                ver_data = driver_data
                break
        
        print(f"\n5️⃣ VER 資料檢查:")
        if ver_data:
            print("   ✅ 找到 VER 的資料!")
            print(f"   車隊: {ver_data.get('team')}")
            print(f"   最快圈時間: {ver_data.get('fastest_lap_time')}")
            
            # 檢查高速彎的數據
            high_speed_data = ver_data.get('high_speed', {})
            print(f"\n   高速彎數據:")
            print(f"   - 彎道編號: {high_speed_data.get('corner_number')}")
            print(f"   - Entry -50m 速度: {high_speed_data.get('entry_50m_speed')} km/h")
            print(f"   - Apex 速度: {high_speed_data.get('apex_speed')} km/h")
            print(f"   - Exit +50m 速度: {high_speed_data.get('exit_50m_speed')} km/h")
            
        else:
            print("   ❌ 找不到 VER 的資料!")
            print(f"   總共有 {len(drivers)} 位車手的資料")
            print(f"   缺少的可能原因:")
            print(f"   1. VER 沒有完成有效的最快圈")
            print(f"   2. VER 的最快圈沒有通過該彎道的遙測數據")
            print(f"   3. 資料處理時 VER 被過濾掉了")
    
    # 檢查全圈分析
    all_laps_analysis = data.get('all_laps_analysis', {})
    if all_laps_analysis:
        print(f"\n6️⃣ 全圈分析:")
        print(f"   描述: {all_laps_analysis.get('description')}")
        
        high_speed_laps = all_laps_analysis.get('high_speed', {})
        if high_speed_laps:
            ver_laps = None
            for driver, laps_data in high_speed_laps.items():
                if driver == 'VER':
                    ver_laps = laps_data
                    break
            
            if ver_laps:
                print(f"\n   ✅ 在全圈分析中找到 VER 的高速彎資料!")
                print(f"   總圈數: {len(ver_laps.get('laps', []))}")
            else:
                print(f"\n   ❌ 在全圈分析中也找不到 VER 的高速彎資料!")
                print(f"   可用車手: {list(high_speed_laps.keys())}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_ver_in_highspeed_corner()
