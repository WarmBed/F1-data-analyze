#!/usr/bin/env python3
"""
煞車性能模組鍵值修正測試
Brake Performance Module Key Mapping Fix Test

測試修正後的鍵值對應是否正確

日期: 2025-10-18
"""

print("="*80)
print("煞車性能模組鍵值修正測試")
print("="*80)
print()

# 測試 1: 重新導入模組
print("[測試 1] 重新導入修正後的模組...")
try:
    from modules.gui.all_drivers_brake_performance_analysis import AllDriversBrakePerformanceModule
    print("✅ 模組導入成功")
except Exception as e:
    print(f"❌ 模組導入失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
print()

# 測試 2: 創建模組實例
print("[測試 2] 創建模組實例...")
try:
    module = AllDriversBrakePerformanceModule(year=2025, race='Australia', session='R')
    print(f"✅ 模組實例創建成功: {module.display_name}")
except Exception as e:
    print(f"❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
print()

# 測試 3: 檢查 JSON 數據結構
print("[測試 3] 驗證 JSON 數據結構...")
import json
try:
    with open('json/brake_performance_2025_Australia_R.json', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✅ JSON 檔案讀取成功")
    print(f"   Success: {data.get('success')}")
    
    data_obj = data.get('data', {})
    driver_brakes = data_obj.get('driver_brakes', [])
    reference_brake_zone = data_obj.get('reference_brake_zone', {})
    
    print(f"   車手數量: {len(driver_brakes)}")
    print(f"   參考煞車區: {reference_brake_zone.get('driver', 'N/A')}")
    
    if driver_brakes:
        first = driver_brakes[0]
        print(f"\n   第一筆車手數據:")
        print(f"     - driver: {first.get('driver')}")
        print(f"     - team: {first.get('team')}")
        print(f"     - max_deceleration_g: {first.get('max_deceleration_g')}")
        print(f"     - brake_time_s: {first.get('brake_time_s')}")
        print(f"     - brake_distance_m: {first.get('brake_distance_m')}")
        print(f"     - brake_start_speed_kmh: {first.get('brake_start_speed_kmh')}")
        
except Exception as e:
    print(f"❌ JSON 驗證失敗: {e}")
    import traceback
    traceback.print_exc()
print()

# 測試 4: 模擬數據更新
print("[測試 4] 測試表格數據更新...")
print("   (需要啟動 GUI 查看實際顯示)")
print("   預期結果:")
print("     - 車手: NOR, ALB, SAI...")
print("     - 最大減速度: 2.73 G, 2.XX G...")
print("     - 煞車起始速度: 278 km/h, XXX km/h...")
print("     - 煞車距離: 77.2 m, XX.X m...")
print("     ❌ 不應該出現 9999")
print()

print("="*80)
print("測試完成")
print("="*80)
print()
print("📋 關鍵修正項目:")
print("   ✅ driver_speeds → driver_brakes")
print("   ✅ reference_segment → reference_brake_zone")
print("   ✅ max_deceleration_kmh → max_deceleration_g")
print("   ✅ brake_time_seconds → brake_time_s")
print("   ✅ brake_distance_meters → brake_distance_m")
print("   ✅ segment_start_speed_kmh → brake_start_speed_kmh")
print()
print("🎯 下一步: 啟動 GUI 測試實際顯示")
print("   python f1t_gui_main.py")
print("="*80)
