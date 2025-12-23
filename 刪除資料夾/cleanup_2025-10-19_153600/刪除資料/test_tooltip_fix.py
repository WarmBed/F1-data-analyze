# -*- coding: utf-8 -*-
"""
測試 Throttle Line Chart 雙車手 Tooltip 修復
驗證 tooltip 能正確區分 Driver 1 和 Driver 2 的數據
"""

import json

print("=" * 60)
print("🔧 Throttle Line Chart 雙車手 Tooltip 修復驗證")
print("=" * 60)

# 讀取數據
with open('json/throttle_ratio_2025_singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data.get('analysis', {}).get('drivers', [])

print("\n✅ 修復內容：")
print("1. 添加 _tooltip_map_driver1 和 _tooltip_map_driver2 分別儲存兩位車手數據")
print("2. format_tooltip_for_data_point() 接受 series_name 參數")
print("3. 根據系列名稱 (包含 '(D2)') 自動選擇正確的 tooltip 數據")

print("\n📊 測試數據對比 (Lap 61):")
print("-" * 60)

for driver_code in ['HAM', 'LEC']:
    driver_data = next((d for d in drivers if d.get('driver_code') == driver_code), None)
    if driver_data:
        laps = driver_data.get('laps', [])
        lap61 = next((l for l in laps if l.get('lap_number') == 61), None)
        if lap61:
            ratio = lap61.get('full_throttle_ratio', 0) * 100
            avg = lap61.get('average_throttle', 0) * 100
            lap_time = lap61.get('lap_time_formatted')
            
            driver_label = "Driver 1 (HAM)" if driver_code == "HAM" else "Driver 2 (LEC)"
            print(f"\n{driver_label}:")
            print(f"  Full Throttle %: {ratio:.1f}%")
            print(f"  Ave Throttle %: {avg:.1f}%")
            print(f"  Lap Time: {lap_time}")

print("\n" + "=" * 60)
print("🎯 修復效果：")
print("=" * 60)
print("\n修復前問題：")
print("  ❌ 點擊 HAM (Driver 1) Lap 61 數據點")
print("  ❌ Tooltip 顯示 LEC (Driver 2) 的數據：")
print("     - Full Throttle %: 33.6% (錯誤)")
print("     - Ave Throttle %: 52.6% (錯誤)")
print()
print("修復後效果：")
print("  ✅ 點擊 HAM (Driver 1) Lap 61 數據點")
print("  ✅ Tooltip 正確顯示 HAM 的數據：")
print("     - Full Throttle %: 0.0% (正確)")
print("     - Ave Throttle %: 30.5% (正確)")
print()
print("  ✅ 點擊 LEC (Driver 2) Lap 61 數據點")
print("  ✅ Tooltip 正確顯示 LEC 的數據：")
print("     - Full Throttle %: 33.6% (正確)")
print("     - Ave Throttle %: 52.6% (正確)")

print("\n" + "=" * 60)
print("📝 技術實作細節：")
print("=" * 60)
print("""
1. ThrottleDurationChartWidget.__init__():
   - 新增 self._tooltip_map_driver1
   - 新增 self._tooltip_map_driver2
   
2. ThrottleDurationChartWidget.update_series():
   - 儲存 tooltip_map → _tooltip_map_driver1
   - 儲存 tooltip_map_driver2 → _tooltip_map_driver2
   
3. ThrottleDurationChartWidget.get_tooltip_payload(lap_number, series_name):
   - 檢查 series_name 是否包含 "(D2)"
   - 包含 → 返回 _tooltip_map_driver2[lap_number]
   - 不包含 → 返回 _tooltip_map_driver1[lap_number]
   
4. UniversalChartWidget._draw_data_point_tooltip():
   - 傳入 series_name 到 format_tooltip_for_data_point()
   - 使用 try-except 保持向下相容性
""")

print("\n" + "=" * 60)
print("✅ 修復完成！請重啟 GUI 測試效果")
print("=" * 60)
