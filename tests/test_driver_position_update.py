#!/usr/bin/env python3
"""
測試 Driver Position Analysis 的參數更新功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer

from modules.gui.driver_position_analysis.driver_position_analysis_mdi import DriverPositionAnalysisMDI


class TestWindow(QMainWindow):
    """測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Driver Position Update Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建中央 widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 創建控制按鈕
        button_layout = QHBoxLayout()
        
        btn_mexico = QPushButton("載入 2025 Mexico R")
        btn_mexico.clicked.connect(lambda: self.load_race(2025, "Mexico", "R"))
        button_layout.addWidget(btn_mexico)
        
        btn_japan = QPushButton("更新為 2025 Japan R")
        btn_japan.clicked.connect(lambda: self.update_race(2025, "Japan", "R"))
        button_layout.addWidget(btn_japan)
        
        btn_brazil = QPushButton("更新為 2025 Brazil R")
        btn_brazil.clicked.connect(lambda: self.update_race(2025, "Brazil", "R"))
        button_layout.addWidget(btn_brazil)
        
        layout.addLayout(button_layout)
        
        # 創建 MDI 視窗
        self.mdi = DriverPositionAnalysisMDI()
        layout.addWidget(self.mdi, 1)
        
        print("✅ 測試視窗已創建")
        print("📋 操作說明:")
        print("   1. 點擊 '載入 2025 Mexico R' 初始化")
        print("   2. 點擊 '更新為 2025 Japan R' 測試參數更新")
        print("   3. 點擊 '更新為 2025 Brazil R' 再次測試")
    
    def load_race(self, year: int, race: str, session: str):
        """初始載入"""
        print(f"\n{'='*60}")
        print(f"🏁 初始載入: {year} {race} {session}")
        print(f"{'='*60}")
        
        # 設置參數
        self.mdi.current_year = str(year)
        self.mdi.current_race = race
        self.mdi.current_session = session
        
        # 初始化模組
        success = self.mdi.initialize_module()
        
        if success:
            print(f"✅ 初始化成功")
        else:
            print(f"❌ 初始化失敗")
    
    def update_race(self, year: int, race: str, session: str):
        """更新參數"""
        print(f"\n{'='*60}")
        print(f"🔄 更新參數: {year} {race} {session}")
        print(f"{'='*60}")
        
        # 調用 update_parameters 方法
        success = self.mdi.update_parameters(
            year=year,
            race=race,
            session=session
        )
        
        if success:
            print(f"✅ 參數更新成功")
        else:
            print(f"❌ 參數更新失敗")


def main():
    """主程式"""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    # 自動載入初始數據（延遲 1 秒）
    QTimer.singleShot(1000, lambda: window.load_race(2025, "Mexico", "R"))
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
