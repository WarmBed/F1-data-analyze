#!/usr/bin/env python3
"""
測試 Workspace 對話框的多國語言化
Test Workspace Dialog Internationalization
"""

from core.gui_i18n import tr, set_gui_language, get_gui_language

def test_workspace_i18n():
    """測試所有 Workspace 相關的翻譯條目"""
    
    print("=" * 70)
    print("Workspace 對話框 - 多國語言化測試")
    print("Workspace Dialog - i18n Test")
    print("=" * 70)
    
    # 測試鍵值列表
    test_keys = [
        # 對話框標題和標籤
        'load_workspace_title',
        'available_workspaces',
        'workspace_details',
        'workspace_search',
        'search_placeholder',
        'refresh',
        
        # 表格標題
        'workspace_id',
        'workspace_name',
        'tab_count',
        'window_count',
        'created_time',
        'description',
        
        # 按鈕
        'load_workspace_btn',
        'delete',
        'cancel',
        
        # 訊息
        'preview_placeholder',
        'load_failed',
        'delete_success',
        'delete_failed',
    ]
    
    # 測試三種語言
    languages = {
        'zh': '中文 (Chinese)',
        'en': '英文 (English)',
        'ja': '日文 (Japanese)'
    }
    
    for lang_code, lang_name in languages.items():
        print(f"\n{'=' * 70}")
        print(f"語言 / Language: {lang_name} ({lang_code})")
        print(f"{'=' * 70}")
        
        # 切換語言
        set_gui_language(lang_code)
        current_lang = get_gui_language()
        print(f"✓ 當前語言設定: {current_lang}\n")
        
        # 測試每個鍵值
        for key in test_keys:
            translation = tr(key)
            print(f"  {key:30s} -> {translation}")
    
    # 測試格式化字串
    print(f"\n{'=' * 70}")
    print("格式化字串測試 / Formatted String Test")
    print(f"{'=' * 70}")
    
    for lang_code, lang_name in languages.items():
        set_gui_language(lang_code)
        print(f"\n{lang_name}:")
        
        # 測試載入確認訊息
        confirm_msg = tr('confirm_load_workspace').format(
            name='Test Workspace',
            tabs=3,
            windows=5
        )
        print(f"  載入確認:\n{confirm_msg}\n")
        
        # 測試刪除確認訊息
        delete_msg = tr('confirm_delete_workspace').format(
            name='Test Workspace'
        )
        print(f"  刪除確認:\n{delete_msg}\n")
        
        # 測試預覽格式
        preview_name = tr('preview_name').format(name='Test Workspace')
        print(f"  預覽名稱: {preview_name}")
        
        preview_tabs = tr('preview_total_tabs').format(count=3)
        print(f"  總分頁數: {preview_tabs}")
        
        preview_windows = tr('preview_total_windows').format(count=5)
        print(f"  總視窗數: {preview_windows}")
    
    print("\n" + "=" * 70)
    print("測試完成 / Test Completed")
    print("=" * 70)

if __name__ == "__main__":
    test_workspace_i18n()
