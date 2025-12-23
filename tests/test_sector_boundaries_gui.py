"""
測試 Sector 邊界 GUI 顯示功能

此腳本驗證：
1. TrackMapWidget 能否正確載入 Sector 邊界數據
2. Sector 邊界線是否正確繪製
3. S1/S2/S3 標籤是否正確顯示
"""

import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.gui.track_analysis.track_map_widget import TrackMapWidget

print("="*60)
print("測試 Sector 邊界 GUI 顯示功能")
print("="*60)

# 讀取 Brazil 2024 的歷史賽道 JSON
json_file = "json/historical_flags_Brazil_2022-2025.json"

print(f"\n載入 JSON: {json_file}")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取數據
api_data = data.get('data', {})
position_records = api_data.get('detailed_position_records', [])
track_bounds = api_data.get('track_bounds')
sector_boundaries = api_data.get('sector_boundaries', [])

print(f"✅ Position records: {len(position_records)}")
print(f"✅ Track bounds: {track_bounds is not None}")
print(f"✅ Sector boundaries: {len(sector_boundaries)}")

if sector_boundaries:
    print(f"\nSector 邊界詳細資訊:")
    for boundary in sector_boundaries:
        print(f"  - {boundary.get('name')}: {boundary.get('distance_m'):.1f}m")
        print(f"    座標: ({boundary.get('position_x'):.1f}, {boundary.get('position_y'):.1f})")

# 創建 Qt 應用
app = QApplication(sys.argv)

# 創建主視窗
window = QMainWindow()
window.setWindowTitle("Sector 邊界測試 - Brazil 2024")
window.resize(1200, 800)

# 創建中央 Widget
central_widget = QWidget()
layout = QVBoxLayout(central_widget)

# 創建 TrackMapWidget
track_map = TrackMapWidget()

# 載入賽道數據
track_data = {
    "position_records": position_records,
    "track_bounds": track_bounds
}

print(f"\n載入賽道數據到 TrackMapWidget...")
success = track_map.load_track_data(track_data)
print(f"載入結果: {success}")

# 🏁 設置 Sector 邊界
if sector_boundaries:
    print(f"\n設置 Sector 邊界...")
    track_map.set_sector_boundaries(sector_boundaries)
    print(f"✅ 已設置 {len(sector_boundaries)} 個 Sector 邊界")

# 啟用速度漸層模式（可選）
track_map.use_speed_gradient = True
print(f"✅ 已啟用速度漸層模式")

# 添加到布局
layout.addWidget(track_map)
window.setCentralWidget(central_widget)

# 顯示視窗
window.show()

print(f"\n" + "="*60)
print(f"視窗已開啟！")
print(f"預期結果：")
print(f"  1. 賽道應該以速度漸層顏色繪製（藍色=高速，紅色=低速）")
print(f"  2. 應該看到 3 條橘紅色虛線（Sector 邊界）")
print(f"  3. 每條線旁應該有標籤：S1、S2、S3")
print(f"  4. 線條應該垂直於賽道方向")
print(f"="*60)

sys.exit(app.exec_())
