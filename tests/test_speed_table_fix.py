#!/usr/bin/env python3
"""
測試 All Drivers Speed Table Widget 的動態欄位功能
"""
import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import AllDriversStraightLineSpeedTableWidget

def test_widget_methods():
    """測試 Widget 方法是否正確實現"""
    print("\n=== 階段 1: Import 測試 ===")
    print("✅ Import 成功")
    
    print("\n=== 階段 2: 方法驗證 ===")
    app = QApplication(sys.argv)
    widget = AllDriversStraightLineSpeedTableWidget()
    
    # 檢查關鍵方法是否存在
    assert hasattr(widget, '_get_column_visibility'), "❌ 缺少 _get_column_visibility 方法"
    print("✅ _get_column_visibility 方法存在")
    
    assert hasattr(widget, '_get_visible_columns'), "❌ 缺少 _get_visible_columns 方法"
    print("✅ _get_visible_columns 方法存在")
    
    assert hasattr(widget, '_get_column_index'), "❌ 缺少 _get_column_index 方法"
    print("✅ _get_column_index 方法存在")
    
    assert hasattr(widget, '_set_item_at_column'), "❌ 缺少 _set_item_at_column 方法"
    print("✅ _set_item_at_column 方法存在")
    
    print("\n=== 階段 3: 邏輯驗證 ===")
    
    # 測試 _get_column_index 返回值
    print("\n測試可見欄位索引...")
    visible_idx = widget._get_column_index('driver')
    print(f"  'driver' 欄位索引: {visible_idx}")
    assert visible_idx is not None, "❌ 'driver' 應該可見"
    assert visible_idx == 0, f"❌ 'driver' 應該是索引 0，實際是 {visible_idx}"
    print("  ✅ 'driver' 欄位索引正確")
    
    # 測試隱藏欄位（如果 max_speed 預設隱藏）
    print("\n測試欄位可見性...")
    visibility = widget._get_column_visibility()
    print(f"  欄位可見性設定: {visibility}")
    
    # 測試 _get_column_index 對隱藏欄位的處理
    if not visibility.get('max_speed', True):
        hidden_idx = widget._get_column_index('max_speed')
        print(f"  'max_speed' 欄位索引（應為 None）: {hidden_idx}")
        assert hidden_idx is None, f"❌ 隱藏欄位應返回 None，實際返回 {hidden_idx}"
        print("  ✅ 隱藏欄位正確返回 None")
    else:
        print("  ℹ️  'max_speed' 目前設定為可見，跳過隱藏測試")
    
    print("\n=== 測試完成 ===")
    print("✅ 所有測試通過！")
    
    app.quit()

if __name__ == "__main__":
    try:
        test_widget_methods()
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
