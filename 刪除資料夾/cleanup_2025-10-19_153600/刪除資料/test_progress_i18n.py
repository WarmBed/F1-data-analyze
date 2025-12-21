"""
測試進度對話框的多國語言化

驗證所有翻譯鍵是否正確註冊並可用於中文、英文和日文
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_i18n_keys():
    """測試所有進度對話框相關的翻譯鍵"""
    from core.gui_i18n import tr, set_gui_language
    
    # 定義需要測試的翻譯鍵
    translation_keys = [
        'update_progress_title',
        'update_progress_preparing',
        'update_progress_updating',
        'update_progress_no_windows',
        'update_progress_no_telemetry',
        'update',
        'cancel',
    ]
    
    # 測試三種語言
    languages = {
        'zh': '中文',
        'en': 'English',
        'ja': '日本語'
    }
    
    print("=" * 80)
    print("🌍 進度對話框多國語言化測試")
    print("=" * 80)
    
    all_passed = True
    
    for lang_code, lang_name in languages.items():
        print(f"\n[測試語言: {lang_name} ({lang_code})]")
        print("-" * 80)
        
        # 切換語言
        set_gui_language(lang_code)
        
        for key in translation_keys:
            try:
                translation = tr(key)
                
                # 檢查是否成功翻譯（不應該返回原鍵值）
                if translation == key:
                    print(f"  ❌ {key}: 未找到翻譯（返回原鍵）")
                    all_passed = False
                elif '{0}' in key:  # 帶參數的翻譯
                    # 測試格式化
                    formatted = translation.format(5)
                    print(f"  ✅ {key}: {formatted}")
                else:
                    print(f"  ✅ {key}: {translation}")
                    
            except Exception as e:
                print(f"  ❌ {key}: 錯誤 - {e}")
                all_passed = False
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("🎉 所有翻譯鍵測試通過！")
        return True
    else:
        print("⚠️ 部分翻譯鍵測試失敗")
        return False

def test_progress_dialog_simulation():
    """模擬進度對話框的使用情境"""
    from core.gui_i18n import tr, set_gui_language
    
    print("\n" + "=" * 80)
    print("🎬 模擬進度對話框使用情境")
    print("=" * 80)
    
    for lang_code, lang_name in [('zh', '中文'), ('en', 'English'), ('ja', '日本語')]:
        print(f"\n[語言: {lang_name}]")
        set_gui_language(lang_code)
        
        # 模擬進度對話框創建
        print(f"  視窗標題: {tr('update_progress_title')}")
        print(f"  初始訊息: {tr('update_progress_preparing')}")
        print(f"  取消按鈕: {tr('cancel')}")
        
        # 模擬更新進度
        analysis_type = "gear"
        current = 1
        total = 8
        window_title = f"Gear Analysis_2025_Australia_R"
        
        progress_text = f"{tr('update_progress_updating')} {analysis_type} ({current}/{total})...\n{window_title}"
        print(f"  進度文字: {progress_text}")
        
        # 模擬無視窗情況
        print(f"  無視窗訊息: {tr('update_progress_no_windows')}")
        
        # 模擬無遙測模組情況
        skipped = 3
        no_telemetry_msg = tr('update_progress_no_telemetry').format(skipped)
        print(f"  無遙測訊息: {no_telemetry_msg}")

def test_import_in_main_file():
    """測試主程式是否可以正確導入和使用翻譯"""
    print("\n" + "=" * 80)
    print("📦 測試主程式導入")
    print("=" * 80)
    
    try:
        # 測試主程式的 tr 導入
        from f1t_gui_main import tr
        print("  ✅ 成功從 f1t_gui_main 導入 tr 函數")
        
        # 測試翻譯
        test_key = 'update_progress_title'
        result = tr(test_key)
        print(f"  ✅ 翻譯測試: tr('{test_key}') = '{result}'")
        
        return True
    except ImportError as e:
        print(f"  ❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    results = {}
    
    # 執行所有測試
    print("開始執行測試...\n")
    
    results['翻譯鍵測試'] = test_i18n_keys()
    results['情境模擬'] = test_progress_dialog_simulation() or True  # 此測試只顯示，不判定失敗
    results['主程式導入'] = test_import_in_main_file()
    
    # 總結
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！進度對話框已成功多國語言化")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} 個測試失敗")
        sys.exit(1)
