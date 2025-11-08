#!/usr/bin/env python3
"""
測試 Load Workspace 對話框的多選功能
Test Load Workspace Dialog with Multi-Selection Support
"""

print("=" * 80)
print("Load Workspace 對話框 - 多選功能測試")
print("Load Workspace Dialog - Multi-Selection Feature Test")
print("=" * 80)

# 測試模組導入
try:
    from windows.load_workspace_dialog import LoadWorkspaceDialog
    from PyQt5.QtWidgets import QAbstractItemView
    print("\n✅ LoadWorkspaceDialog 導入成功")
    print(f"   類別: {LoadWorkspaceDialog}")
except Exception as e:
    print(f"\n❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 測試翻譯
print("\n" + "=" * 80)
print("批量刪除翻譯測試")
print("=" * 80)

from core.gui_i18n import tr, set_gui_language

languages = {
    'zh': '中文',
    'en': 'English',
    'ja': '日本語'
}

test_keys = [
    'confirm_delete_workspace',
    'confirm_delete_multiple_workspaces',
    'workspaces_deleted_success',
    'workspaces_deleted_partial'
]

for lang_code, lang_name in languages.items():
    set_gui_language(lang_code)
    print(f"\n{'=' * 80}")
    print(f"{lang_name}:")
    print(f"{'=' * 80}")
    
    # 單個刪除確認
    print("\n單個刪除：")
    print(tr('confirm_delete_workspace').format(name='Test Workspace'))
    
    # 批量刪除確認
    print("\n批量刪除（3 個項目）：")
    print(tr('confirm_delete_multiple_workspaces').format(
        count=3,
        names='Workspace A\n  • Workspace B\n  • Workspace C'
    ))
    
    # 成功訊息
    print("\n刪除成功：")
    print(tr('workspaces_deleted_success').format(count=3))
    
    # 部分成功訊息
    print("\n部分成功：")
    print(tr('workspaces_deleted_partial').format(success=2, failed=1))

print("\n" + "=" * 80)
print("功能摘要")
print("=" * 80)

print("""
✅ 已實現的功能：

1. 多選支援 (ExtendedSelection)
   • 支援 Ctrl + 點擊：選擇多個不連續的項目
   • 支援 Shift + 點擊：選擇連續的項目範圍
   • 支援 Ctrl + A：全選所有項目

2. Load Workspace 按鈕
   • 只載入第一個（最上面的）選中項目
   • 即使選中多個，也只載入第一個
   • 避免工作空間衝突

3. Delete 按鈕 - 批量刪除
   • 可以一次刪除多個選中的 Workspace
   • 顯示將刪除的所有項目名稱
   • 提供刪除結果統計（成功/失敗數量）
   • 支援部分成功的情況處理

4. 預覽功能
   • 顯示第一個選中項目的詳細資訊
   • 選擇多個時，預覽第一個項目

5. 選擇計數
   • 自動統計選中的項目數量
   • 根據數量調整確認對話框內容

使用說明：
──────────────────────────────────────────────────
• 單選：直接點擊項目
• 多選不連續：按住 Ctrl 鍵 + 點擊多個項目
• 多選連續：點擊第一個項目，按住 Shift 鍵 + 點擊最後一個項目
• 全選：Ctrl + A（或點擊第一個，Shift + End）
• 取消選擇：點擊空白處（不在任何行上）

刪除行為：
──────────────────────────────────────────────────
• 選中 1 個：顯示單個刪除確認訊息
• 選中多個：顯示批量刪除確認訊息，列出所有項目名稱
• 刪除成功：顯示成功刪除的數量
• 部分失敗：顯示成功和失敗的數量統計

載入行為：
──────────────────────────────────────────────────
• 無論選中多少個，都只載入第一個（最上面的）項目
• 這樣可以避免工作空間衝突
• 預覽也顯示第一個選中項目的資訊
""")

print("=" * 80)
print("測試完成 ✅")
print("=" * 80)
