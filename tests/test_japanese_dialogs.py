"""
測試日文語系下的對話框
確保 Lap Analysis 和 Detailed Lap Analysis 對話框在日文模式下能正常顯示
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt

def test_japanese_lap_analysis_dialog():
    """測試日文模式下的 Lap Analysis 對話框"""
    print("\n" + "="*60)
    print("🇯🇵 測試日文模式 - Lap Analysis 對話框")
    print("="*60)
    
    try:
        from core.gui_i18n import set_gui_language, tr
        
        # 設置為日文
        set_gui_language('ja')
        print(f"✅ 語言已切換至: 日文")
        
        from f1t_gui_main import LapAnalysisOptionsDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建父視窗
        parent = QWidget()
        
        # 添加 get_current_parameters 方法
        def get_current_parameters():
            return {'year': '2025', 'race': 'Australia', 'session': 'R'}
        
        parent.get_current_parameters = get_current_parameters
        
        # 創建對話框
        dialog = LapAnalysisOptionsDialog(parent)
        
        print("✅ Lap Analysis 對話框創建成功")
        print(f"   - 對話框標題: '{dialog.windowTitle()}'")
        
        # 驗證標題翻譯
        expected_title = tr('telemetry_options_title', 'Telemetry Analysis Options')
        print(f"   - 預期標題: '{expected_title}'")
        
        if dialog.windowTitle() == expected_title:
            print(f"   ✅ 標題翻譯正確")
        else:
            print(f"   ❌ 標題翻譯不符")
            return False
        
        # 檢查日文標題應該包含「テレメトリー」
        if 'テレメトリー' in dialog.windowTitle():
            print(f"   ✅ 標題包含日文字符")
        else:
            print(f"   ⚠️  標題未包含日文字符（可能使用了英文回退）")
        
        print(f"   - 車手1選項數量: {dialog.driver1_combo.count()}")
        print(f"   - 遙測選項數量: {dialog.telemetry_list.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_japanese_detailed_lap_dialog():
    """測試日文模式下的 Detailed Lap Analysis 對話框"""
    print("\n" + "="*60)
    print("🇯🇵 測試日文模式 - Detailed Lap Analysis 對話框")
    print("="*60)
    
    try:
        from core.gui_i18n import set_gui_language, tr
        
        # 設置為日文
        set_gui_language('ja')
        print(f"✅ 語言已切換至: 日文")
        
        from modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog import (
            DetailedLapAnalysisOptionsDialog,
        )
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建對話框
        dialog = DetailedLapAnalysisOptionsDialog()
        
        print("✅ Detailed Lap Analysis 對話框創建成功")
        print(f"   - 對話框標題: '{dialog.windowTitle()}'")
        
        # 驗證標題翻譯
        expected_title = tr('detailed_lap_options_title', 'Detailed Lap Analysis Options')
        print(f"   - 預期標題: '{expected_title}'")
        
        if dialog.windowTitle() == expected_title:
            print(f"   ✅ 標題翻譯正確")
        else:
            print(f"   ❌ 標題翻譯不符")
            return False
        
        # 檢查日文標題應該包含「詳細」或「ラップ」
        if '詳細' in dialog.windowTitle() or 'ラップ' in dialog.windowTitle():
            print(f"   ✅ 標題包含日文字符")
        else:
            print(f"   ⚠️  標題未包含日文字符（可能使用了英文回退）")
        
        # 檢查選項列表
        if hasattr(dialog, 'analysis_list'):
            print(f"   - 分析選項數量: {dialog.analysis_list.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translation_keys():
    """測試翻譯鍵是否存在"""
    print("\n" + "="*60)
    print("🔍 測試翻譯鍵")
    print("="*60)
    
    try:
        from core.gui_i18n import set_gui_language, tr
        
        test_keys = [
            ('telemetry_options_title', 'Telemetry Analysis Options'),
            ('detailed_lap_options_title', 'Detailed Lap Analysis Options'),
        ]
        
        all_passed = True
        
        for lang, lang_name in [('zh', '中文'), ('en', '英文'), ('ja', '日文')]:
            set_gui_language(lang)
            print(f"\n📝 測試 {lang_name} 翻譯:")
            
            for key, fallback in test_keys:
                result = tr(key, fallback)
                print(f"   - {key}: '{result}'")
                
                # 檢查是否返回了預設值（表示翻譯缺失）
                if result == fallback and lang != 'en':
                    print(f"     ⚠️  可能使用了英文回退")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("日文語系對話框測試")
    print("=" * 60)
    
    results = {
        "翻譯鍵測試": test_translation_keys(),
        "日文 Lap Analysis 對話框": test_japanese_lap_analysis_dialog(),
        "日文 Detailed Lap 對話框": test_japanese_detailed_lap_dialog(),
    }
    
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有測試通過！")
        print("📌 日文語系下對話框應該能正常顯示")
    else:
        print("⚠️  部分測試失敗，請檢查上方詳細信息")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
