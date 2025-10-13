"""
測試主視窗 resizeEvent 機制
驗證主視窗調整大小時，Welcome Tab 中的固定視窗會同步調整
"""

import sys
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🧪 測試主視窗 resizeEvent 機制")
print("=" * 80)

# 測試 1: 驗證 StyleHMainWindow 類別有 resizeEvent 方法
print("\n測試 1: 檢查 StyleHMainWindow.resizeEvent 是否存在...")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # 檢查主視窗類別
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 檢查 StyleHMainWindow 是否有 resizeEvent
    if 'class StyleHMainWindow' in content:
        class_start = content.find('class StyleHMainWindow')
        class_section = content[class_start:class_start + 50000]
        
        if 'def resizeEvent(self, event):' in class_section:
            print("✅ StyleHMainWindow.resizeEvent 方法存在")
            
            # 檢查是否調用 _rearrange_fixed_windows
            if '_rearrange_fixed_windows' in class_section:
                print("✅ resizeEvent 中調用了 _rearrange_fixed_windows")
            else:
                print("❌ resizeEvent 未調用 _rearrange_fixed_windows")
        else:
            print("❌ StyleHMainWindow.resizeEvent 方法不存在")
    else:
        print("❌ 找不到 StyleHMainWindow 類別")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 2: 檢查 _find_mdi_area 輔助方法
print("\n測試 2: 檢查 _find_mdi_area 輔助方法...")
try:
    if 'def _find_mdi_area(self, widget):' in content:
        print("✅ _find_mdi_area 輔助方法存在")
        
        # 檢查遞迴搜尋邏輯
        if 'isinstance(widget, CustomMdiArea)' in content:
            print("✅ 包含 CustomMdiArea 類型檢查")
        else:
            print("❌ 缺少 CustomMdiArea 類型檢查")
            
        if 'result = self._find_mdi_area(child)' in content:
            print("✅ 包含遞迴搜尋邏輯")
        else:
            print("❌ 缺少遞迴搜尋邏輯")
    else:
        print("❌ _find_mdi_area 輔助方法不存在")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 3: 檢查調試輸出
print("\n測試 3: 檢查調試輸出...")
try:
    if '[MAIN_RESIZE]' in content:
        print("✅ 包含主視窗調整大小的調試輸出")
    else:
        print("⚠️  缺少調試輸出（建議添加以便追蹤）")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 4: 檢查 CustomMdiArea._rearrange_fixed_windows 是否存在
print("\n測試 4: 檢查 CustomMdiArea._rearrange_fixed_windows...")
try:
    if 'class CustomMdiArea' in content:
        mdi_class_start = content.find('class CustomMdiArea')
        mdi_class_section = content[mdi_class_start:mdi_class_start + 10000]
        
        if 'def _rearrange_fixed_windows(self):' in mdi_class_section:
            print("✅ CustomMdiArea._rearrange_fixed_windows 方法存在")
            
            # 檢查固定視窗篩選
            if 'is_welcome_fixed' in mdi_class_section:
                print("✅ 包含 is_welcome_fixed 屬性篩選")
            else:
                print("❌ 缺少固定視窗篩選邏輯")
        else:
            print("❌ CustomMdiArea._rearrange_fixed_windows 方法不存在")
    else:
        print("❌ 找不到 CustomMdiArea 類別")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

print("\n" + "=" * 80)
print("✅ 靜態測試完成！")
print("=" * 80)

print("\n📋 手動測試指南：")
print("1. 執行: python f1t_gui_main.py")
print("2. 觀察初始化時的 [MDI_RESIZE] 日誌輸出")
print("3. 調整主視窗大小（拖曳邊緣）")
print("4. 檢查是否出現 [MAIN_RESIZE] 日誌")
print("5. 檢查是否出現新的 [MDI_RESIZE] 日誌")
print("6. 觀察三個固定視窗是否隨主視窗同步調整大小")

print("\n🎯 預期行為：")
print("- 調整主視窗時，應該看到:")
print("  [MAIN_RESIZE] 主視窗調整大小，觸發 MDI 重新排列")
print("  [MDI_RESIZE] 重新排列 3 個固定視窗")
print("  [MDI_RESIZE] MDI 尺寸: XXXxYYY")
print("  [MDI_RESIZE] 每個視窗寬度: ZZZpx")
print("  [MDI_RESIZE] 視窗 0/1/2: 調整前 → 調整後")
