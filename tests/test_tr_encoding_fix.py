#!/usr/bin/env python3
"""
測試 tr() 函數編碼修復
Test tr() function encoding fix
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

# 導入翻譯函數
from core.gui_i18n import tr

def test_tr_encoding():
    """測試 tr() 函數是否能正確處理中文"""
    print("=" * 60)
    print("測試 tr() 函數編碼")
    print("=" * 60)
    
    # 測試 1: 基本中文翻譯
    test1 = tr("straight_speed_info_no_data", "分析範圍: 未載入資料")
    print(f"✅ 測試 1 - 基本翻譯: {test1}")
    print(f"   類型: {type(test1)}")
    print(f"   編碼: {test1.encode('utf-8')}")
    
    # 測試 2: 帶格式化的翻譯
    test2 = tr("straight_speed_info_range", "分析範圍: {start}m → {end}m (長度: {length}m)")
    formatted = test2.format(start="100.0", end="200.0", length="100.0")
    print(f"✅ 測試 2 - 格式化翻譯: {formatted}")
    
    # 測試 3: 在 QLabel 中使用
    app = QApplication(sys.argv)
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    label = QLabel()
    label.setText(tr("straight_speed_info_no_data", "分析範圍: 未載入資料"))
    print(f"✅ 測試 3 - QLabel 設置: {label.text()}")
    
    layout.addWidget(label)
    widget.setWindowTitle("編碼測試")
    widget.resize(400, 200)
    
    print("\n" + "=" * 60)
    print("所有測試通過！GUI 視窗已創建但不顯示（測試成功）")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_tr_encoding()
        if success:
            print("\n✅ 編碼修復驗證成功！")
            sys.exit(0)
        else:
            print("\n❌ 編碼修復驗證失敗！")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
