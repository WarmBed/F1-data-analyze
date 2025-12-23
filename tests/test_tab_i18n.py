#!/usr/bin/env python3
"""
測試分頁右鍵選單的多國語言化
Test Tab Context Menu Internationalization
"""

from core.gui_i18n import tr, set_gui_language, get_gui_language

def test_tab_i18n():
    """測試所有相關的翻譯條目"""
    
    print("=" * 60)
    print("分頁右鍵選單 - 多國語言化測試")
    print("Tab Context Menu - i18n Test")
    print("=" * 60)
    
    # 測試鍵值列表
    test_keys = [
        'tab_popout_menu',
        'tab_return_menu',
        'tab_already_popped',
        'home_tab_no_popout',
        'tab_popout_success',
        'tab_return_success',
        'tab_not_popped',
        'tab_starting_popout',
        'tab_starting_return',
        'tab_placeholder_label',
        'popout_tooltip',
        'close_tooltip',
    ]
    
    # 測試三種語言
    languages = {
        'zh': '中文 (Chinese)',
        'en': '英文 (English)',
        'ja': '日文 (Japanese)'
    }
    
    for lang_code, lang_name in languages.items():
        print(f"\n{'=' * 60}")
        print(f"語言 / Language: {lang_name} ({lang_code})")
        print(f"{'=' * 60}")
        
        # 切換語言
        set_gui_language(lang_code)
        current_lang = get_gui_language()
        print(f"✓ 當前語言設定: {current_lang}\n")
        
        # 測試每個鍵值
        for key in test_keys:
            translation = tr(key)
            
            # 處理需要格式化的字串
            if '{' in translation:
                if 'index' in translation and 'name' in translation:
                    translation = translation.format(index=1, name="Test Tab")
                elif 'index' in translation:
                    translation = translation.format(index=1)
                elif 'name' in translation:
                    translation = translation.format(name="Test Tab")
            
            print(f"  {key:30s} -> {translation}")
    
    print("\n" + "=" * 60)
    print("測試完成 / Test Completed")
    print("=" * 60)

if __name__ == "__main__":
    test_tab_i18n()
