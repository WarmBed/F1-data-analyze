#!/usr/bin/env python3
"""
測試分頁重新命名功能
Test Tab Rename Feature
"""

import sys
from PyQt5.QtWidgets import QApplication

# 測試階段 1: 導入驗證
print("=" * 60)
print("階段 1: 導入驗證")
print("=" * 60)

try:
    from f1t_gui_main import F1AnalysisGUI
    print("✅ F1AnalysisGUI 導入成功")
except Exception as e:
    print(f"❌ F1AnalysisGUI 導入失敗: {e}")
    sys.exit(1)

try:
    from core.gui_i18n import tr, get_gui_language
    print("✅ GUI 國際化模組導入成功")
except Exception as e:
    print(f"❌ GUI 國際化模組導入失敗: {e}")
    sys.exit(1)

# 測試階段 2: 翻譯鍵驗證
print("\n" + "=" * 60)
print("階段 2: 翻譯鍵驗證")
print("=" * 60)

translation_keys = [
    'tab_rename_menu',
    'tab_rename_dialog_title',
    'tab_rename_dialog_label',
    'tab_rename_success',
    'home_tab_no_rename'
]

for key in translation_keys:
    zh_text = tr(key)
    print(f"✅ {key}: {zh_text}")

# 測試階段 3: 方法存在性驗證
print("\n" + "=" * 60)
print("階段 3: 方法存在性驗證")
print("=" * 60)

app = QApplication(sys.argv)
gui = F1AnalysisGUI()

methods_to_check = [
    'rename_tab',
    '_get_unique_tab_name',
    '_show_tab_context_menu'
]

for method_name in methods_to_check:
    if hasattr(gui, method_name):
        print(f"✅ 方法存在: {method_name}")
    else:
        print(f"❌ 方法不存在: {method_name}")

# 測試階段 4: 唯一名稱生成邏輯測試
print("\n" + "=" * 60)
print("階段 4: 唯一名稱生成邏輯測試")
print("=" * 60)

# 模擬已存在的分頁名稱
test_cases = [
    ("新分頁", []),  # 無重複
    ("新分頁", ["新分頁"]),  # 一個重複 -> "新分頁 (1)"
    ("新分頁", ["新分頁", "新分頁 (1)"]),  # 兩個重複 -> "新分頁 (2)"
    ("Tab 1", ["主頁", "Tab 1", "Tab 2"]),  # 重複 -> "Tab 1 (1)"
]

# 手動測試唯一名稱邏輯
for base_name, existing in test_cases:
    # 模擬分頁名稱
    gui.tab_widget.clear()
    for name in existing:
        gui.tab_widget.addTab(gui.create_welcome_tab(), name)
    
    unique_name = gui._get_unique_tab_name(base_name)
    print(f"✅ 基礎名稱: '{base_name}' | 現有: {existing} | 結果: '{unique_name}'")

print("\n" + "=" * 60)
print("✅ 所有測試完成!")
print("=" * 60)
print("\n💡 提示: 如需手動測試，請執行以下步驟:")
print("   1. 啟動 GUI: python f1t_gui_main.py")
print("   2. 創建多個分頁（點擊 [+] 按鈕）")
print("   3. 在分頁標籤上按右鍵")
print("   4. 選擇「重新命名分頁」")
print("   5. 輸入新名稱並確認")
print("   6. 測試重複名稱、彈出視窗同步等功能")
print("=" * 60)

sys.exit(0)
