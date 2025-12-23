"""
驗證 File Menu 和 LoadWorkspaceDialog 多國語言化
測試所有 Workspace 相關翻譯鍵是否正確定義
"""

import sys
from core.gui_i18n import tr, set_current_language

def test_file_menu_translations():
    """測試 File Menu 的翻譯"""
    
    # File Menu 相關的翻譯鍵
    keys_to_test = [
        'save_workspace',
        'load_workspace',
    ]
    
    languages = ['zh', 'en', 'ja']
    
    print("=" * 80)
    print("File Menu - Workspace 項目翻譯驗證")
    print("=" * 80)
    
    all_passed = True
    
    for lang in languages:
        set_current_language(lang)
        lang_name = {'zh': '中文', 'en': 'English', 'ja': '日本語'}[lang]
        print(f"\n[{lang_name}]")
        print("-" * 80)
        
        for key in keys_to_test:
            try:
                result = tr(key, f'__FALLBACK_{key}__')
                
                if result == f'__FALLBACK_{key}__':
                    print(f"  ❌ 缺少翻譯鍵: {key}")
                    all_passed = False
                else:
                    print(f"  ✅ {key}: {result}")
            except Exception as e:
                print(f"  ❌ 錯誤 ({key}): {e}")
                all_passed = False
    
    return all_passed


def test_load_workspace_dialog_translations():
    """測試 LoadWorkspaceDialog 的翻譯"""
    
    # LoadWorkspaceDialog 使用的翻譯鍵
    keys_to_test = [
        'load_workspace_title',
        'available_workspaces',
        'workspace_details',
        'workspace_search',
        'search_placeholder',
        'refresh',
        'workspace_id',
        'workspace_name',
        'tab_count',
        'window_count',
        'created_time',
        'description',
        'preview_placeholder',
        'delete',
        'cancel',
        'load_workspace_btn',
        'workspace_loaded_count',
        'load_failed',
        'load_workspaces_error',
        'search_results',
        'preview_name',
        'preview_id',
        'preview_created',
        'preview_modified',
        'preview_tags',
        'preview_statistics',
        'preview_total_tabs',
        'preview_total_windows',
        'preview_tab_details',
        'preview_tab_entry',
        'preview_popped_out',
        'confirm_load_workspace',
        'confirm_delete_workspace',
        'confirm_delete_multiple_workspaces',
        'delete_success',
        'workspace_deleted',
        'workspaces_deleted_success',
        'workspaces_deleted_partial',
        'delete_failed',
        'delete_workspace_error',
        'load_workspace_error',
    ]
    
    languages = ['zh', 'en', 'ja']
    
    print("\n" + "=" * 80)
    print("LoadWorkspaceDialog 翻譯驗證")
    print("=" * 80)
    print(f"\n測試 {len(keys_to_test)} 個翻譯鍵 × {len(languages)} 種語言\n")
    
    all_passed = True
    missing_keys = []
    
    for lang in languages:
        set_current_language(lang)
        lang_name = {'zh': '中文', 'en': 'English', 'ja': '日本語'}[lang]
        print(f"\n[{lang_name}] 測試中...")
        print("-" * 80)
        
        lang_passed = True
        for key in keys_to_test:
            try:
                result = tr(key, f'__FALLBACK_{key}__')
                
                # 檢查是否使用了 fallback
                if result == f'__FALLBACK_{key}__':
                    print(f"  ❌ 缺少翻譯鍵: {key}")
                    missing_keys.append(f"{lang}:{key}")
                    lang_passed = False
                    all_passed = False
                else:
                    # 顯示範例（前 3 個鍵）
                    if keys_to_test.index(key) < 3:
                        print(f"  ✅ {key}: {result}")
            except Exception as e:
                print(f"  ❌ 錯誤 ({key}): {e}")
                lang_passed = False
                all_passed = False
        
        if lang_passed:
            print(f"\n  ✅ [{lang_name}] 所有 {len(keys_to_test)} 個翻譯鍵通過")
        else:
            print(f"\n  ❌ [{lang_name}] 有翻譯鍵缺失")
    
    if not all_passed:
        print("\n" + "=" * 80)
        print("缺失的翻譯鍵：")
        for missing in missing_keys:
            print(f"   - {missing}")
    
    return all_passed


def test_sample_texts():
    """測試範例文字"""
    print("\n" + "=" * 80)
    print("範例文字測試")
    print("=" * 80)
    
    for lang in ['zh', 'en', 'ja']:
        set_current_language(lang)
        lang_name = {'zh': '中文', 'en': 'English', 'ja': '日本語'}[lang]
        print(f"\n[{lang_name}]")
        print("-" * 80)
        
        # File Menu
        print(f"File Menu -> Save: {tr('save_workspace', 'Save Workspace')}")
        print(f"File Menu -> Load: {tr('load_workspace', 'Load Workspace')}")
        
        # LoadWorkspaceDialog
        print(f"\nDialog Title: {tr('load_workspace_title', 'Load Workspace')}")
        print(f"Table Header - Name: {tr('workspace_name', 'Name')}")
        print(f"Table Header - Tabs: {tr('tab_count', 'Tabs')}")
        print(f"Button - Load: {tr('load_workspace_btn', 'Load Workspace')}")
        print(f"Button - Delete: {tr('delete', 'Delete')}")
        print(f"Button - Cancel: {tr('cancel', 'Cancel')}")


if __name__ == "__main__":
    print("\n🚀 開始驗證...\n")
    
    # 測試 File Menu
    file_menu_passed = test_file_menu_translations()
    
    # 測試 LoadWorkspaceDialog
    dialog_passed = test_load_workspace_dialog_translations()
    
    # 測試範例文字
    test_sample_texts()
    
    # 總結
    print("\n" + "=" * 80)
    print("驗證完成")
    print("=" * 80)
    
    if file_menu_passed and dialog_passed:
        print("\n✅ File Menu 和 LoadWorkspaceDialog 已完成多國語言化")
        print("✅ 所有翻譯鍵都已正確定義")
        print("\n下一步：重新生成 EXE 並測試")
        sys.exit(0)
    else:
        print("\n❌ 驗證失敗，請檢查缺失的翻譯鍵")
        if not file_menu_passed:
            print("  ❌ File Menu 有缺失")
        if not dialog_passed:
            print("  ❌ LoadWorkspaceDialog 有缺失")
        sys.exit(1)
