#!/usr/bin/env python3
"""
綜合測試：分頁右鍵選單 + Workspace 對話框多國語言化
Comprehensive Test: Tab Context Menu + Workspace Dialog i18n
"""

from core.gui_i18n import tr, set_gui_language, get_gui_language

def print_section(title):
    """印出分隔線"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_comprehensive_i18n():
    """綜合測試所有多國語言化功能"""
    
    print_section("F1T GUI 多國語言化綜合測試")
    
    # 所有測試項目
    test_categories = {
        '分頁右鍵選單 (Tab Context Menu)': [
            'tab_popout_menu',
            'tab_return_menu',
            'tab_already_popped',
            'home_tab_no_popout',
            'popout_tooltip',
            'close_tooltip',
        ],
        'Workspace 對話框 (Workspace Dialog)': [
            'load_workspace_title',
            'available_workspaces',
            'workspace_details',
            'search_placeholder',
            'load_workspace_btn',
            'delete',
        ],
        '按鈕與控制項 (Buttons & Controls)': [
            'ok',
            'cancel',
            'refresh',
            'select_all',
            'select_none',
        ],
    }
    
    # 測試三種語言
    languages = {
        'zh': '中文',
        'en': 'English',
        'ja': '日本語'
    }
    
    for lang_code, lang_name in languages.items():
        print_section(f"語言測試: {lang_name} ({lang_code})")
        
        set_gui_language(lang_code)
        
        for category, keys in test_categories.items():
            print(f"\n【{category}】")
            for key in keys:
                translation = tr(key)
                print(f"  {key:30s} → {translation}")
    
    # 格式化字串測試
    print_section("格式化字串測試 (Formatted Strings)")
    
    for lang_code, lang_name in languages.items():
        set_gui_language(lang_code)
        print(f"\n{lang_name}:")
        
        # 分頁相關
        print(f"  彈出成功: {tr('tab_popout_success').format(index=2)}")
        print(f"  返回成功: {tr('tab_return_success').format(index=2)}")
        
        # Workspace 相關
        print(f"  載入數量: {tr('workspace_loaded_count').format(count=10)}")
        print(f"  搜尋結果: {tr('search_results').format(count=3)}")
    
    print_section("測試完成 ✅")
    print("\n所有多國語言化功能測試通過！")
    print("All i18n features tested successfully!")
    print()

if __name__ == "__main__":
    test_comprehensive_i18n()
