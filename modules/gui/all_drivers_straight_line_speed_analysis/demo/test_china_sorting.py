"""
測試 China R 的排序功能修正

問題：字串排序導致 "10.041s" < "7.76s" < "9.799s"
解決：使用 setData(Qt.UserRole, 數值) 進行數值排序
"""

import sys
import os

# 添加專案根目錄到路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import AllDriversStraightLineSpeedTableWidget

def main():
    app = QApplication(sys.argv)
    
    # JSON 路徑
    json_path = os.path.join(project_root, "json", "all_drivers_straight_line_speed_2025_China_R-龜山.json")
    
    if not os.path.exists(json_path):
        print(f"❌ 找不到檔案: {json_path}")
        return
    
    print("=" * 60)
    print("🧪 測試 F48 China R 排序功能修正")
    print("=" * 60)
    print(f"📄 JSON 路徑: {json_path}")
    print()
    
    # 創建 Widget
    widget = AllDriversStraightLineSpeedTableWidget(chart_type="accel_time")
    
    # 載入 JSON 數據
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    success = widget.update_with_json(data)
    
    if success:
        print("✅ 數據載入成功")
        
        # 驗證排序
        print("\n🔍 驗證加速時間排序（第 4 欄）：")
        print("-" * 60)
        
        # 獲取前 5 行的加速時間
        for row in range(min(5, widget.table.rowCount())):
            driver_item = widget.table.item(row, 1)  # 車手
            accel_item = widget.table.item(row, 4)   # 加速時間
            
            if driver_item and accel_item:
                driver = driver_item.text()
                display_text = accel_item.text()
                sort_value = accel_item.data(0x0100)  # Qt.UserRole
                
                print(f"排名 {row + 1}: {driver:3s} | 顯示: {display_text:10s} | 排序值: {sort_value:.3f}s")
        
        print()
        print("✅ 如果排序值是遞增（7.76 < 7.799 < 7.8...），表示修正成功！")
        print()
        print("🖱️  請點擊表頭「加速時間 (100→300)」測試排序功能")
        print("   - 第一次點擊：遞增排序（最快在前）")
        print("   - 第二次點擊：遞減排序（最慢在前）")
        print()
        
        # 顯示視窗
        widget.show()
        widget.resize(1000, 600)
        
        sys.exit(app.exec_())
    else:
        print("❌ 數據載入失敗")

if __name__ == "__main__":
    main()
