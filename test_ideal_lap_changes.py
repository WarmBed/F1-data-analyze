#!/usr/bin/env python3
"""
測試 Ideal Lap Ranking 的修改
1. 車手名字使用黑色字體
2. Export CSV 按鈕已移除
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

def test_widget_driver_color():
    """測試車手名字顏色設定"""
    print("\n🧪 測試 1: 檢查車手名字顏色設定...")
    
    from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_widget import IdealLapRankingTableWidget
    
    # 讀取源碼檢查
    import inspect
    source = inspect.getsource(IdealLapRankingTableWidget._set_row_data)
    
    if "QColor(0, 0, 0)" in source:
        print("   ✅ 車手名字已設定為黑色 QColor(0, 0, 0)")
        return True
    elif "QColor(255, 255, 255)" in source:
        print("   ❌ 車手名字仍是白色 QColor(255, 255, 255)")
        return False
    else:
        print("   ⚠️  無法確認顏色設定")
        return False

def test_export_button_removed():
    """測試 Export CSV 按鈕是否已移除"""
    print("\n🧪 測試 2: 檢查 Export CSV 按鈕...")
    
    from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI
    
    # 讀取源碼檢查
    import inspect
    source = inspect.getsource(IdealLapRankingTableMDI)
    
    if 'btn_export' not in source and '_on_export_clicked' not in source:
        print("   ✅ Export CSV 按鈕已完全移除")
        return True
    elif 'btn_export' in source:
        print("   ❌ btn_export 仍存在於源碼中")
        return False
    elif '_on_export_clicked' in source:
        print("   ❌ _on_export_clicked 方法仍存在")
        return False
    else:
        print("   ⚠️  無法確認按鈕狀態")
        return False

def test_module_import():
    """測試模組是否可以正常導入"""
    print("\n🧪 測試 3: 測試模組導入...")
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI
        print("   ✅ IdealLapRankingTableMDI 導入成功")
        
        from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_widget import IdealLapRankingTableWidget
        print("   ✅ IdealLapRankingTableWidget 導入成功")
        
        return True
    except Exception as e:
        print(f"   ❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🔬 Ideal Lap Ranking 修改驗證測試")
    print("=" * 60)
    
    results = []
    
    # 測試 1: 車手顏色
    results.append(("車手名字黑色", test_widget_driver_color()))
    
    # 測試 2: Export 按鈕移除
    results.append(("Export 按鈕移除", test_export_button_removed()))
    
    # 測試 3: 模組導入
    results.append(("模組導入", test_module_import()))
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"   {test_name:20s} : {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有測試通過！修改成功！")
    else:
        print("⚠️  部分測試失敗，請檢查修改")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
