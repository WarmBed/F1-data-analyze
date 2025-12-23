#!/usr/bin/env python3
"""測試積分榜 Widget 整合"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow

from modules.gui.championship.standings_widgets import (
    ConstructorStandingsWidget,
    DriverStandingsWidget
)

def main():
    app = QApplication(sys.argv)
    
    # 創建主視窗
    window = QMainWindow()
    window.setWindowTitle("F1T - 積分榜整合測試")
    window.resize(1400, 800)
    
    # 創建 MDI 區域
    mdi_area = QMdiArea()
    window.setCentralWidget(mdi_area)
    
    # 創建車隊積分榜子視窗
    print("[TEST] 創建車隊積分榜...")
    constructor_widget = ConstructorStandingsWidget()
    constructor_sub = QMdiSubWindow()
    constructor_sub.setWidget(constructor_widget)
    constructor_sub.setWindowTitle("🏆 車隊積分榜")
    constructor_sub.resize(700, 400)
    mdi_area.addSubWindow(constructor_sub)
    constructor_sub.show()
    print("[TEST] ✅ 車隊積分榜創建完成")
    
    # 創建車手積分榜子視窗
    print("[TEST] 創建車手積分榜...")
    driver_widget = DriverStandingsWidget()
    driver_sub = QMdiSubWindow()
    driver_sub.setWidget(driver_widget)
    driver_sub.setWindowTitle("🏁 車手積分榜")
    driver_sub.resize(900, 600)
    mdi_area.addSubWindow(driver_sub)
    driver_sub.show()
    print("[TEST] ✅ 車手積分榜創建完成")
    
    # 平鋪排列視窗
    mdi_area.tileSubWindows()
    print("[TEST] ✅ 視窗已平鋪排列")
    
    window.show()
    print("[TEST] 🎉 測試視窗已顯示")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
