"""
測試分析對話框
- Detailed Lap Analysis 對話框（應該有詳細圈速分析和圈速箱型圖兩個選項）
- Lap Analysis 對話框（遙測分析選項）
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt

def test_detailed_lap_analysis_dialog():
    """測試 Detailed Lap Analysis 對話框"""
    print("\n" + "="*60)
    print("🔍 測試 Detailed Lap Analysis 對話框")
    print("="*60)
    
    try:
        from core.gui_i18n import set_gui_language
        set_gui_language('en')
        
        from modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog import (
            DetailedLapAnalysisOptionsDialog,
        )
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建對話框
        dialog = DetailedLapAnalysisOptionsDialog()
        
        print("✅ Detailed Lap Analysis 對話框創建成功")
        print(f"   - 對話框標題: {dialog.windowTitle()}")
        
        # 檢查選項列表
        if hasattr(dialog, 'analysis_list'):
            print(f"   - 分析選項數量: {dialog.analysis_list.count()}")
            print("   - 可用選項:")
            for i in range(dialog.analysis_list.count()):
                item = dialog.analysis_list.item(i)
                print(f"     {i+1}. {item.text()}")
                print(f"        資料: {item.data(Qt.UserRole)}")
        
        # 驗證常數
        print(f"\n   - TYPE_DETAIL_TABLE: {DetailedLapAnalysisOptionsDialog.TYPE_DETAIL_TABLE}")
        print(f"   - TYPE_BOX_PLOT: {DetailedLapAnalysisOptionsDialog.TYPE_BOX_PLOT}")
        
        # 測試 get_selected_types 方法
        if hasattr(dialog, 'get_selected_types'):
            selected = dialog.get_selected_types()
            print(f"\n   - 預設選中項目: {selected}")
        
        return True
        
    except Exception as e:
        print(f"❌ Detailed Lap Analysis 對話框測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lap_analysis_dialog():
    """測試 Lap Analysis 對話框（遙測分析）"""
    print("\n" + "="*60)
    print("🔍 測試 Lap Analysis 對話框（遙測分析）")
    print("="*60)
    
    try:
        from core.gui_i18n import set_gui_language
        set_gui_language('en')
        
        from f1t_gui_main import LapAnalysisOptionsDialog
        from PyQt5.QtWidgets import QWidget
        
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
        print(f"   - 對話框標題: {dialog.windowTitle()}")
        print(f"   - 車手1選項數量: {dialog.driver1_combo.count()}")
        print(f"   - 車手2選項數量: {dialog.driver2_combo.count()}")
        print(f"   - 遙測選項數量: {dialog.telemetry_list.count()}")
        
        print("\n   - 遙測圖表選項:")
        for i in range(dialog.telemetry_list.count()):
            item = dialog.telemetry_list.item(i)
            is_selected = item.isSelected()
            status = "✓" if is_selected else " "
            print(f"     [{status}] {item.text()} (key: {item.data(Qt.UserRole)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Lap Analysis 對話框測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dialog_import_in_main():
    """測試主程式是否能正確導入對話框"""
    print("\n" + "="*60)
    print("🔍 測試主程式中的對話框導入")
    print("="*60)
    
    try:
        from f1t_gui_main import StyleHMainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 測試 _prompt_detailed_lap_options 方法存在
        main_window = StyleHMainWindow()
        
        if hasattr(main_window, '_prompt_detailed_lap_options'):
            print("✅ _prompt_detailed_lap_options 方法存在")
        else:
            print("❌ _prompt_detailed_lap_options 方法不存在")
            return False
        
        # 測試 lap_analysis 方法存在
        if hasattr(main_window, 'lap_analysis'):
            print("✅ lap_analysis 方法存在")
        else:
            print("❌ lap_analysis 方法不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 主程式對話框導入測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("分析對話框測試")
    print("=" * 60)
    
    results = {
        "Detailed Lap Analysis 對話框": test_detailed_lap_analysis_dialog(),
        "Lap Analysis 對話框": test_lap_analysis_dialog(),
        "主程式對話框導入": test_dialog_import_in_main(),
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
