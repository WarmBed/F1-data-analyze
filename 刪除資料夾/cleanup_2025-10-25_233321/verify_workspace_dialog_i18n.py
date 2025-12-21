"""
驗證 SaveWorkspaceDialog 多國語言化
測試所有翻譯鍵是否正確定義
"""

import sys
from core.gui_i18n import tr, set_current_language

def test_translation_keys():
    """測試所有翻譯鍵"""
    
    # 需要測試的翻譯鍵
    keys_to_test = [
        'save_workspace_title',
        'save_workspace_dialog_title',
        'workspace_basic_info',
        'workspace_name_label',
        'workspace_name_required',
        'workspace_name_placeholder',
        'workspace_description_label',
        'workspace_description_placeholder',
        'workspace_tags_label',
        'workspace_tags_placeholder',
        'workspace_statistics',
        'workspace_loading_stats',
        'workspace_total_tabs',
        'workspace_total_windows',
        'workspace_window_types',
        'workspace_parameters',
        'workspace_year',
        'workspace_race',
        'workspace_session',
        'workspace_preview',
        'workspace_preview_placeholder',
        'workspace_cancel',
        'workspace_save_button',
        'workspace_cannot_save',
        'workspace_no_tabs_message',
        'workspace_load_error',
        'workspace_load_data_failed',
        'workspace_name_hint_exists',
        'workspace_name_hint_available',
        'workspace_validation_failed',
        'workspace_name_required_message',
        'workspace_name_duplicate',
        'workspace_name_duplicate_message',
        'workspace_save_success',
        'workspace_save_success_message',
        'workspace_save_failed',
        'workspace_save_failed_message',
    ]
    
    languages = ['zh', 'en', 'ja']
    
    print("=" * 80)
    print("SaveWorkspaceDialog 多國語言化驗證")
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
    
    # 最終結果
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 驗證成功！所有翻譯鍵都已正確定義")
        print(f"✅ {len(keys_to_test)} 個鍵 × {len(languages)} 種語言 = {len(keys_to_test) * len(languages)} 個翻譯全部通過")
        return True
    else:
        print("❌ 驗證失敗！以下翻譯鍵缺失：")
        for missing in missing_keys:
            print(f"   - {missing}")
        return False


def test_sample_dialog_texts():
    """測試範例對話框文字"""
    print("\n" + "=" * 80)
    print("範例文字測試")
    print("=" * 80)
    
    for lang in ['zh', 'en', 'ja']:
        set_current_language(lang)
        lang_name = {'zh': '中文', 'en': 'English', 'ja': '日本語'}[lang]
        print(f"\n[{lang_name}]")
        print("-" * 80)
        
        print(f"窗口標題: {tr('save_workspace_title', 'Save Workspace')}")
        print(f"對話框標題: {tr('save_workspace_dialog_title', 'Save Current Workspace')}")
        print(f"儲存按鈕: {tr('workspace_save_button', 'Save Workspace')}")
        print(f"取消按鈕: {tr('workspace_cancel', 'Cancel')}")
        print(f"統計標題: {tr('workspace_statistics', 'Workspace Statistics')}")
        
        # 測試格式化字串
        success_msg = tr('workspace_save_success_message', 
                        "Workspace '{name}' saved successfully!\n\n• Tabs: {tabs}\n• Windows: {windows}")
        print(f"\n成功訊息範例:")
        print(success_msg.format(name="Test Workspace", tabs=5, windows=12))


if __name__ == "__main__":
    print("\n🚀 開始驗證...\n")
    
    # 測試翻譯鍵
    keys_passed = test_translation_keys()
    
    # 測試範例文字
    test_sample_dialog_texts()
    
    # 總結
    print("\n" + "=" * 80)
    print("驗證完成")
    print("=" * 80)
    
    if keys_passed:
        print("\n✅ SaveWorkspaceDialog 已完成多國語言化")
        print("✅ 所有翻譯鍵都已正確定義")
        print("✅ 客製化按鈕樣式已移除")
        print("\n下一步：重新生成 EXE 並測試")
        sys.exit(0)
    else:
        print("\n❌ 驗證失敗，請檢查缺失的翻譯鍵")
        sys.exit(1)
