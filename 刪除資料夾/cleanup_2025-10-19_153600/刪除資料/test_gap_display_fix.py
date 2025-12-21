"""
測試 Gap 欄位顯示修復
驗證 Constructor 和 Driver Standings 的 Gap 欄位只顯示數字，不顯示符號
"""

import sys
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("測試 Gap 欄位顯示修復")
print("=" * 80)

# 測試 1: 檢查 Constructor Standings
print("\n測試 1: 檢查 Constructor Standings Gap 顯示...")
try:
    with open('modules/gui/constructor_standings/constructor_standings_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查錯誤模式（帶 + 符號）
    if 'f"+{delta:.1f}"' in content:
        print("❌ 仍存在 + 符號：f\"+{delta:.1f}\"")
    else:
        print("✅ + 符號已移除")
    
    # 檢查正確模式（不帶符號）
    if 'f"{delta:.1f}"' in content and 'delta and delta > 0' in content:
        print("✅ 正確模式已實作：f\"{delta:.1f}\"")
    else:
        print("❌ 正確模式未找到")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 2: 檢查 Driver Standings
print("\n測試 2: 檢查 Driver Standings Gap 顯示...")
try:
    with open('modules/gui/driver_standings/driver_standings_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查錯誤模式（帶 + 符號）
    if 'f"+{delta:.1f}"' in content:
        print("❌ 仍存在 + 符號：f\"+{delta:.1f}\"")
    else:
        print("✅ + 符號已移除")
    
    # 檢查正確模式（不帶符號）
    if 'f"{delta:.1f}"' in content and 'delta and delta > 0' in content:
        print("✅ 正確模式已實作：f\"{delta:.1f}\"")
    else:
        print("❌ 正確模式未找到")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 3: 模擬數據填充
print("\n測試 3: 模擬數據填充測試...")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # 測試 Constructor Standings
    from modules.gui.constructor_standings.constructor_standings_widget import ConstructorStandingsWidget
    
    constructor_widget = ConstructorStandingsWidget()
    
    test_data = {
        "season_year": 2025,
        "round": 18,
        "standings": [
            {
                "position": 1,
                "constructor_name": "McLaren",
                "points": 650.0,
                "wins": 12,
                "points_delta": 0.0
            },
            {
                "position": 2,
                "constructor_name": "Ferrari",
                "points": 629.0,
                "wins": 8,
                "points_delta": 21.0
            },
            {
                "position": 3,
                "constructor_name": "Red Bull Racing",
                "points": 610.0,
                "wins": 5,
                "points_delta": 40.0
            }
        ]
    }
    
    constructor_widget.populate_table(test_data)
    
    # 檢查第二行的 Gap 值（應該是 "21.0" 而不是 "+21.0"）
    gap_item = constructor_widget.table.item(1, 4)
    if gap_item:
        gap_text = gap_item.text()
        if gap_text == "21.0":
            print(f"✅ Constructor Gap 顯示正確：'{gap_text}'（無 + 符號）")
        elif gap_text == "+21.0":
            print(f"❌ Constructor Gap 仍有 + 符號：'{gap_text}'")
        else:
            print(f"⚠️  Constructor Gap 顯示異常：'{gap_text}'")
    else:
        print("❌ 無法獲取 Gap 項目")
    
    # 測試 Driver Standings
    from modules.gui.driver_standings.driver_standings_widget import DriverStandingsWidget
    
    driver_widget = DriverStandingsWidget()
    
    driver_test_data = {
        "season_year": 2025,
        "round": 18,
        "standings": [
            {
                "position": 1,
                "driver_code": "PIA",
                "full_name": "Oscar Piastri",
                "team": "McLaren",
                "points": 336.0,
                "wins": 5,
                "points_delta": 0.0
            },
            {
                "position": 2,
                "driver_code": "NOR",
                "full_name": "Lando Norris",
                "team": "McLaren",
                "points": 314.0,
                "wins": 7,
                "points_delta": 22.0
            }
        ]
    }
    
    driver_widget.populate_table(driver_test_data)
    
    # 檢查第二行的 Gap 值
    gap_item = driver_widget.table.item(1, 6)
    if gap_item:
        gap_text = gap_item.text()
        if gap_text == "22.0":
            print(f"✅ Driver Gap 顯示正確：'{gap_text}'（無 + 符號）")
        elif gap_text == "+22.0":
            print(f"❌ Driver Gap 仍有 + 符號：'{gap_text}'")
        else:
            print(f"⚠️  Driver Gap 顯示異常：'{gap_text}'")
    else:
        print("❌ 無法獲取 Gap 項目")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 測試完成！")
print("=" * 80)

print("\n📋 修改總結：")
print("修改前：delta_text = f\"+{delta:.1f}\"  # 顯示 +21.0")
print("修改後：delta_text = f\"{delta:.1f}\"   # 顯示 21.0")
print("")
print("影響範圍：")
print("- modules/gui/constructor_standings/constructor_standings_widget.py (Line 115)")
print("- modules/gui/driver_standings/driver_standings_widget.py (Line 137)")
