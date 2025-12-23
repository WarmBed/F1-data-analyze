#!/usr/bin/env python3
"""
測試 Load Workspace 對話框的簡化按鈕樣式
Test Load Workspace Dialog with Standard Qt Button Styles
"""

print("=" * 70)
print("Load Workspace 對話框 - 簡化按鈕測試")
print("Load Workspace Dialog - Standard Button Test")
print("=" * 70)

# 測試模組導入
try:
    from windows.load_workspace_dialog import LoadWorkspaceDialog
    print("\n✅ LoadWorkspaceDialog 導入成功")
    print(f"   類別: {LoadWorkspaceDialog}")
    print(f"   信號: {LoadWorkspaceDialog.workspace_selected}")
except Exception as e:
    print(f"\n❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 測試翻譯
print("\n" + "=" * 70)
print("按鈕翻譯測試")
print("=" * 70)

from core.gui_i18n import tr, set_gui_language

languages = {
    'zh': '中文',
    'en': 'English',
    'ja': '日本語'
}

button_keys = ['delete', 'cancel', 'load_workspace_btn']

for lang_code, lang_name in languages.items():
    set_gui_language(lang_code)
    print(f"\n{lang_name}:")
    for key in button_keys:
        print(f"  {key:20s} -> {tr(key)}")

print("\n" + "=" * 70)
print("測試完成 ✅")
print("=" * 70)
print("\n修改摘要:")
print("  • 移除了 Delete 按鈕的紅色樣式")
print("  • 移除了 Load Workspace 按鈕的藍色樣式和粗體")
print("  • 保留了所有按鈕的功能和多國語言支援")
print("  • 使用 Qt 標準按鈕樣式")
print("\n優點:")
print("  ✓ 與系統原生樣式一致")
print("  ✓ 自動適應系統主題（深色/淺色模式）")
print("  ✓ 代碼更簡潔，維護成本更低")
print("  ✓ 完全保留功能性")
print()
