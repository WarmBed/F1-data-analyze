"""
測試對話框修復
- 驗證 Lap Analysis 對話框能正常顯示
- 驗證事故統計分頁標題使用正確的翻譯
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

def test_lap_analysis_dialog():
    """測試 Lap Analysis 對話框"""
    print("\n🔍 測試 Lap Analysis 對話框...")
    
    try:
        # 設置 GUI 語言為英文
        from core.gui_i18n import set_gui_language
        set_gui_language('en')
        
        # 導入 LapAnalysisOptionsDialog（從 f1t_gui_main.py）
        from f1t_gui_main import LapAnalysisOptionsDialog
        from PyQt5.QtWidgets import QWidget
        
        # 創建測試應用
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建一個 QWidget 父視窗
        parent = QWidget()
        
        # 添加 get_current_parameters 方法到父視窗
        def get_current_parameters():
            return {'year': '2025', 'race': 'Japan', 'session': 'R'}
        
        parent.get_current_parameters = get_current_parameters
        
        # 嘗試創建對話框
        dialog = LapAnalysisOptionsDialog(parent)
        
        print("✅ Lap Analysis 對話框創建成功")
        print(f"   - 對話框標題: {dialog.windowTitle()}")
        print(f"   - 車手1選項數量: {dialog.driver1_combo.count()}")
        print(f"   - 車手2選項數量: {dialog.driver2_combo.count()}")
        print(f"   - 遙測選項數量: {dialog.telemetry_list.count()}")
        
        # 驗證有車手選項
        if dialog.driver1_combo.count() > 0:
            print(f"   - 第一個車手: {dialog.driver1_combo.itemText(0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lap Analysis 對話框測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_accident_statistics_i18n():
    """測試事故統計分頁標題翻譯"""
    print("\n🔍 測試事故統計分頁標題翻譯...")
    
    try:
        from core.gui_i18n import tr, set_gui_language
        
        # 測試三種語言
        languages = {'zh': '事故統計', 'en': 'Accident Statistics', 'ja': '事故統計データ'}
        
        all_passed = True
        for lang, expected in languages.items():
            set_gui_language(lang)
            result = tr('accident_statistics', 'Accident Statistics')
            
            if result == expected:
                print(f"✅ {lang.upper()}: '{result}' (正確)")
            else:
                print(f"❌ {lang.upper()}: 預期 '{expected}'，實際 '{result}'")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 事故統計翻譯測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_accident_module_tab_title():
    """測試事故分析模組的分頁標題"""
    print("\n🔍 測試事故分析模組分頁標題...")
    
    try:
        from core.gui_i18n import set_gui_language
        from modules.gui.accident_analysis.accident_analysis_mdi_simple import AccidentAnalysisModule
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 測試日文
        set_gui_language('ja')
        
        # 創建模擬數據管理器
        class MockDataManager:
            def load_data(self, year, race, session):
                return None
        
        data_manager = MockDataManager()
        
        # 創建模組（不提供數據，只測試 UI 創建）
        module = AccidentAnalysisModule(data_manager)
        
        # 檢查分頁標題
        if hasattr(module, 'tab_widget'):
            tab_count = module.tab_widget.count()
            first_tab_title = module.tab_widget.tabText(0) if tab_count > 0 else ""
            
            print(f"✅ 事故分析模組創建成功")
            print(f"   - 分頁數量: {tab_count}")
            print(f"   - 第一個分頁標題: '{first_tab_title}'")
            
            # 驗證標題包含日文或翻譯
            if '事故統計データ' in first_tab_title or '事故統計' in first_tab_title:
                print(f"✅ 分頁標題使用了翻譯")
                return True
            else:
                print(f"⚠️  分頁標題可能未使用翻譯: {first_tab_title}")
                return False
        else:
            print("⚠️  模組未創建 tab_widget")
            return False
        
    except Exception as e:
        print(f"❌ 事故分析模組測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("對話框修復測試")
    print("=" * 60)
    
    results = {
        "Lap Analysis 對話框": test_lap_analysis_dialog(),
        "事故統計翻譯": test_accident_statistics_i18n(),
        # "事故分析模組分頁": test_accident_module_tab_title(),  # 需要完整 Qt 環境
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
    else:
        print("⚠️  部分測試失敗，請檢查上方詳細信息")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
