#!/usr/bin/env python3
"""
手動測試：檢查 _refresh_calendar_for_year 的實際行為
"""

import sys
from PyQt5.QtWidgets import QApplication, QComboBox
from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider, SeasonEvent

def test_combobox_logic():
    """測試 ComboBox 索引設定邏輯"""
    print("=" * 60)
    print("測試 ComboBox 索引設定邏輯")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建 ComboBox
    combo = QComboBox()
    
    # 獲取真實的賽事數據
    provider = SeasonCalendarProvider()
    events = provider.get_completed_events(2025)
    completed_events = [event for event in events if event.is_completed]
    
    print(f"\n📊 已完賽比賽數量: {len(completed_events)}")
    
    # 模擬添加項目到 ComboBox
    for event in completed_events:
        label = f"{event.display_label} ({event.race_date})"
        combo.addItem(label, event)
    
    print(f"\n📝 ComboBox 項目數: {combo.count()}")
    
    # 測試索引設定
    print("\n🧪 測試 1: 設定索引為 0 (第一項)")
    combo.setCurrentIndex(0)
    print(f"   當前索引: {combo.currentIndex()}")
    print(f"   當前文字: {combo.currentText()}")
    
    print("\n🧪 測試 2: 設定索引為 -1 (使用 completed_events[-1])")
    last_index = len(completed_events) - 1
    preferred_event = completed_events[-1]
    print(f"   預期選擇: {preferred_event.display_label}")
    print(f"   計算的索引: {last_index}")
    
    # 使用 findData 查找索引
    found_index = combo.findData(preferred_event)
    print(f"   findData 結果: {found_index}")
    
    if found_index >= 0:
        combo.setCurrentIndex(found_index)
        print(f"   ✅ 設定後的索引: {combo.currentIndex()}")
        print(f"   ✅ 設定後的文字: {combo.currentText()}")
        
        # 驗證
        current_data = combo.currentData()
        if current_data == preferred_event:
            print(f"\n✅ 測試通過！ComboBox 正確選擇了最後一項")
            return True
        else:
            print(f"\n❌ 測試失敗！選擇的項目不正確")
            print(f"   預期: {preferred_event.display_label}")
            print(f"   實際: {current_data.display_label if current_data else 'None'}")
            return False
    else:
        print(f"\n❌ findData 失敗，無法找到項目")
        return False

if __name__ == "__main__":
    success = test_combobox_logic()
    sys.exit(0 if success else 1)
