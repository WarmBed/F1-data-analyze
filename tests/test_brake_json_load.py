"""測試 GUI 讀取 Brake Performance JSON"""
import json

json_file = "json/brake_performance_2025_Singapore_R.json"

try:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✅ JSON 檔案載入成功！")
    
    # 數據在 data 層級
    data_content = data.get('data', {})
    metadata = data_content.get('metadata', {})
    
    print(f"\n分析類型: {metadata.get('analysis_type')}")
    print(f"成功狀態: {data.get('success')}")
    print(f"車手數量: {len(data_content.get('driver_brakes', []))}")
    
    print("\n前 3 位車手煞車數據：")
    for i, driver in enumerate(data_content.get('driver_brakes', [])[:3], 1):
        driver_code = driver.get('driver') or driver.get('driver_code') or 'N/A'
        print(f"\n{i}. {driver_code} ({driver.get('team', 'N/A')})")
        print(f"   最速圈: 第 {driver.get('lap_number')} 圈")
        max_decel_ms2 = driver.get('max_deceleration_ms2', 0)
        max_decel_g = driver.get('max_deceleration_g', 0)
        print(f"   最大減速度: {max_decel_ms2:.2f} m/s² ({max_decel_g:.2f} G)")
        brake_dist = driver.get('brake_distance_m', 0)
        speed_reduction = driver.get('speed_reduction_kmh', 0)
        print(f"   煞車距離: {brake_dist:.1f}m")
        print(f"   速度減少: {speed_reduction:.1f} km/h")

except Exception as e:
    print(f"❌ 錯誤: {e}")
