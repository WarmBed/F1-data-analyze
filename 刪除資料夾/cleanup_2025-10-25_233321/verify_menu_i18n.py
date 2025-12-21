"""
驗證主選單多國語言化
測試 File, View, Analysis, Tools 選單的所有翻譯鍵
"""

import sys
from core.gui_i18n import tr, set_current_language

def test_menu_translations():
    """測試所有選單的翻譯"""
    
    # 需要測試的翻譯鍵
    menu_keys = {
        'File Menu': [
            'save_workspace',
            'load_workspace',
        ],
        'View Menu': [
            'tile_windows',
            'cascade_windows',
            'minimize_all_windows',
            'maximize_all_windows',
            'restore_all_windows',
            'close_all_windows',
            'full_screen',
        ],
        'Tools Menu': [
            'system_settings',
            'check_api_status',
            'check_api_status_tip',
            'language_menu',
        ],
    }
    
    languages = ['zh', 'en', 'ja']
    
    print("=" * 80)
    print("主選單多國語言化驗證")
    print("=" * 80)
    
    total_keys = sum(len(keys) for keys in menu_keys.values())
    print(f"\n測試 {total_keys} 個翻譯鍵 × {len(languages)} 種語言\n")
    
    all_passed = True
    missing_keys = []
    
    for lang in languages:
        set_current_language(lang)
        lang_name = {'zh': '中文', 'en': 'English', 'ja': '日本語'}[lang]
        print(f"\n[{lang_name}] 測試中...")
        print("=" * 80)
        
        lang_passed = True
        
        for menu_name, keys in menu_keys.items():
            print(f"\n  {menu_name}:")
            print("  " + "-" * 76)
            
            for key in keys:
                try:
                    result = tr(key, f'__FALLBACK_{key}__')
                    
                    if result == f'__FALLBACK_{key}__':
                        print(f"    ❌ 缺少翻譯鍵: {key}")
                        missing_keys.append(f"{lang}:{key}")
                        lang_passed = False
                        all_passed = False
                    else:
                        print(f"    ✅ {key}: {result}")
                except Exception as e:
                    print(f"    ❌ 錯誤 ({key}): {e}")
                    lang_passed = False
                    all_passed = False
        
        if lang_passed:
            print(f"\n  ✅ [{lang_name}] 所有 {total_keys} 個翻譯鍵通過")
        else:
            print(f"\n  ❌ [{lang_name}] 有翻譯鍵缺失")
    
    # 最終結果
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 驗證成功！所有翻譯鍵都已正確定義")
        print(f"✅ {total_keys} 個鍵 × {len(languages)} 種語言 = {total_keys * len(languages)} 個翻譯全部通過")
        return True
    else:
        print("❌ 驗證失敗！以下翻譯鍵缺失：")
        for missing in missing_keys:
            print(f"   - {missing}")
        return False


def test_sample_menu_texts():
    """測試範例選單文字"""
    print("\n" + "=" * 80)
    print("範例選單文字測試")
    print("=" * 80)
    
    for lang in ['zh', 'en', 'ja']:
        set_current_language(lang)
        lang_name = {'zh': '中文', 'en': 'English', 'ja': '日本語'}[lang]
        print(f"\n[{lang_name}]")
        print("-" * 80)
        
        # File Menu
        print("File Menu:")
        print(f"  - {tr('save_workspace', 'Save Workspace')}")
        print(f"  - {tr('load_workspace', 'Load Workspace')}")
        
        # View Menu
        print("\nView Menu:")
        print(f"  - {tr('tile_windows', 'Tile Windows')}")
        print(f"  - {tr('cascade_windows', 'Cascade Windows')}")
        print(f"  - {tr('close_all_windows', 'Close All Windows')}")
        print(f"  - {tr('full_screen', 'Full Screen')}")
        
        # Tools Menu
        print("\nTools Menu:")
        print(f"  - {tr('system_settings', 'System Settings')}")
        print(f"  - {tr('check_api_status', 'Check API Status')}")
        print(f"  - {tr('language_menu', 'Language')}")


if __name__ == "__main__":
    print("\n🚀 開始驗證...\n")
    
    # 測試所有選單翻譯
    menu_passed = test_menu_translations()
    
    # 測試範例文字
    test_sample_menu_texts()
    
    # 總結
    print("\n" + "=" * 80)
    print("驗證完成")
    print("=" * 80)
    
    if menu_passed:
        print("\n✅ 所有主選單項目已完成多國語言化")
        print("✅ File, View, Tools 選單的所有翻譯鍵都已正確定義")
        print("\n下一步：測試 GUI 或重新生成 EXE")
        sys.exit(0)
    else:
        print("\n❌ 驗證失敗，請檢查缺失的翻譯鍵")
        sys.exit(1)
