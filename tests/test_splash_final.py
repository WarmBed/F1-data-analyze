#!/usr/bin/env python3
"""
最終測試：啟動畫面整合驗證
此腳本會啟動完整的 GUI 應用程式並自動關閉（15秒後）
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

print("=" * 70)
print("F1T GUI 啟動畫面整合 - 最終測試")
print("=" * 70)
print("\n此測試將：")
print("1. 顯示啟動畫面")
print("2. 啟動完整的 GUI 主視窗")
print("3. 15秒後自動關閉")
print("\n請觀察啟動畫面是否正確顯示進度...\n")

# 導入主函數
from f1t_gui_main import main

# 創建自動關閉計時器
def auto_close_after_delay():
    """15秒後自動關閉應用程式"""
    print("\n[自動測試] 15秒後自動關閉...")
    QTimer.singleShot(15000, lambda: (
        print("[自動測試] 正在關閉 GUI..."),
        QApplication.quit()
    ))

# 修改 sys.argv 以避免參數問題
if __name__ == "__main__":
    try:
        # 設定自動關閉計時器
        QTimer.singleShot(100, auto_close_after_delay)
        
        # 啟動主程式
        print("[測試開始] 啟動 F1T GUI...")
        print("-" * 70)
        
        main()
        
        print("-" * 70)
        print("\n✅ GUI 已正常關閉")
        
    except KeyboardInterrupt:
        print("\n⚠️  測試被使用者中斷（Ctrl+C）")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
