#!/usr/bin/env python3
"""
理想圈分段對比模組 - 完整測試腳本
測試所有修正是否正確
"""

import sys
from PyQt5.QtWidgets import QApplication

def test_import():
    """測試 1: Import"""
    print("\n" + "="*60)
    print("[TEST 1] Import 模組")
    print("="*60)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import IdealLapSectorComparisonModule
        print("✅ IdealLapSectorComparisonModule Import 成功")
        return True
    except Exception as e:
        print(f"❌ Import 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_widget_methods():
    """測試 2: Widget 方法"""
    print("\n" + "="*60)
    print("🧪 測試 2: Widget 方法檢查")
    print("="*60)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_widget import IdealLapSectorComparisonWidget
        
        # 需要 QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        widget = IdealLapSectorComparisonWidget()
        
        # 檢查必要方法
        required_methods = [
            'draw_comparison_bars',  # 繪製圖表
            'sort_data',            # 排序
            'clear_chart',          # ✅ 新添加
            'update_statistics_panel'  # ✅ 新添加（統一介面）
        ]
        
        print("\n檢查必要方法:")
        all_ok = True
        for method in required_methods:
            has_method = hasattr(widget, method) and callable(getattr(widget, method))
            status = "✅" if has_method else "❌"
            print(f"  {status} {method}: {has_method}")
            if not has_method:
                all_ok = False
        
        if all_ok:
            print("\n✅ 所有必要方法都存在")
            return True
        else:
            print("\n❌ 缺少必要方法")
            return False
            
    except Exception as e:
        print(f"❌ Widget 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mdi_methods():
    """測試 3: MDI 方法"""
    print("\n" + "="*60)
    print("🧪 測試 3: MDI 方法檢查")
    print("="*60)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI
        
        # 需要 QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 檢查類別方法（不需要實例化）
        required_methods = [
            '_show_error',          # ✅ 新添加
            '_on_data_loaded',      # 數據載入回調
            '_on_api_success',      # API 成功回調
            '_on_api_failure',      # API 失敗回調
            'load_initial_data'     # 載入初始數據
        ]
        
        print("\n檢查必要方法:")
        all_ok = True
        for method in required_methods:
            has_method = hasattr(IdealLapSectorComparisonMDI, method)
            status = "✅" if has_method else "❌"
            print(f"  {status} {method}: {has_method}")
            if not has_method:
                all_ok = False
        
        if all_ok:
            print("\n✅ 所有必要方法都存在")
            return True
        else:
            print("\n❌ 缺少必要方法")
            return False
            
    except Exception as e:
        print(f"❌ MDI 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """測試 4: 錯誤處理"""
    print("\n" + "="*60)
    print("🧪 測試 4: 錯誤處理機制")
    print("="*60)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI
        import inspect
        
        # 檢查 _show_error 方法簽名
        if hasattr(IdealLapSectorComparisonMDI, '_show_error'):
            sig = inspect.signature(IdealLapSectorComparisonMDI._show_error)
            params = list(sig.parameters.keys())
            
            print(f"\n_show_error() 方法簽名:")
            print(f"  參數: {params}")
            
            # 檢查參數是否正確
            expected_params = ['self', 'title', 'message']
            if params == expected_params:
                print(f"  ✅ 參數正確: {expected_params}")
                
                # 檢查方法實現（讀取源代碼）
                source = inspect.getsource(IdealLapSectorComparisonMDI._show_error)
                
                # 檢查是否使用 chart_widget 作為 parent
                if 'chart_widget' in source and 'QMessageBox' in source:
                    print(f"  ✅ 正確使用 chart_widget 作為 parent")
                    print(f"  ✅ 正確調用 QMessageBox")
                    return True
                else:
                    print(f"  ❌ 實現不正確")
                    return False
            else:
                print(f"  ❌ 參數不正確，預期: {expected_params}")
                return False
        else:
            print(f"  ❌ _show_error() 方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_callback():
    """測試 5: API 回調邏輯"""
    print("\n" + "="*60)
    print("🧪 測試 5: API 回調邏輯")
    print("="*60)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI
        import inspect
        
        # 檢查 _on_api_success 方法實現
        if hasattr(IdealLapSectorComparisonMDI, '_on_api_success'):
            source = inspect.getsource(IdealLapSectorComparisonMDI._on_api_success)
            
            print("\n檢查 _on_api_success() 實現:")
            
            # ✅ 應該調用 _on_data_loaded()
            if '_on_data_loaded' in source:
                print("  ✅ 正確調用 _on_data_loaded()")
            else:
                print("  ❌ 沒有調用 _on_data_loaded()")
                return False
            
            # ❌ 不應該調用 update_chart()
            if 'update_chart' not in source:
                print("  ✅ 沒有錯誤地調用 update_chart()")
            else:
                print("  ❌ 仍然調用了 update_chart()（錯誤!）")
                return False
            
            print("\n✅ API 回調邏輯正確")
            return True
        else:
            print("  ❌ _on_api_success() 方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ API 回調測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n" + "="*70)
    print("[MAIN] 理想圈分段對比模組 - 完整測試")
    print("="*70)
    
    results = {
        "Import 測試": test_import(),
        "Widget 方法測試": test_widget_methods(),
        "MDI 方法測試": test_mdi_methods(),
        "錯誤處理測試": test_error_handling(),
        "API 回調測試": test_api_callback()
    }
    
    # 測試結果摘要
    print("\n" + "="*70)
    print("📊 測試結果摘要")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {status} - {test_name}")
    
    # 總體結果
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    failed_tests = total_tests - passed_tests
    
    print("\n" + "="*70)
    if failed_tests == 0:
        print("🎉 所有測試通過! ({}/{})".format(passed_tests, total_tests))
        print("✅ 模組修正成功，可以進行 GUI 整合測試")
    else:
        print(f"⚠️  有 {failed_tests} 個測試失敗 ({passed_tests}/{total_tests} 通過)")
        print("❌ 需要進一步修正")
    print("="*70)
    
    return failed_tests == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
