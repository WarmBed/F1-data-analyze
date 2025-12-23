#!/usr/bin/env python3
"""
測試進站分析模組的多視窗關閉功能
驗證修復：同時關閉多個視窗不會導致崩潰
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisModule
from core.logger import get_logger

logger = get_logger(__name__)

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("進站分析多視窗關閉測試")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建中央 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # MDI 區域
        self.mdi_area = QMdiArea()
        layout.addWidget(self.mdi_area)
        
        # 控制按鈕
        btn_layout = QVBoxLayout()
        
        self.btn_open_5 = QPushButton("開啟 5 個進站分析視窗")
        self.btn_open_5.clicked.connect(self.open_5_windows)
        btn_layout.addWidget(self.btn_open_5)
        
        self.btn_close_all = QPushButton("關閉所有視窗 (Close All)")
        self.btn_close_all.clicked.connect(self.close_all_windows)
        btn_layout.addWidget(self.btn_close_all)
        
        self.btn_test_auto = QPushButton("自動測試：開5個→等3秒→全關")
        self.btn_test_auto.clicked.connect(self.auto_test)
        btn_layout.addWidget(self.btn_test_auto)
        
        layout.addLayout(btn_layout)
        
        self.windows_opened = 0
        
    def open_5_windows(self):
        """開啟 5 個進站分析視窗"""
        logger.info("=" * 60)
        logger.info("測試開始：開啟 5 個進站分析視窗")
        logger.info("=" * 60)
        
        for i in range(5):
            self.open_single_window(i + 1)
            
        logger.info(f"✅ 已開啟 {self.windows_opened} 個視窗")
    
    def open_single_window(self, index):
        """開啟單個進站分析視窗"""
        try:
            # 創建進站分析模組
            analysis_module = PitstopAnalysisModule()
            analysis_module.current_year = "2024"
            analysis_module.current_race = "Japan"
            analysis_module.current_session = "R"
            
            # 創建 MDI 子視窗
            sub_window = QMdiSubWindow()
            sub_window.setWidget(analysis_module.get_widget())
            sub_window.setWindowTitle(f"進站分析 #{index}")
            sub_window.setAttribute(Qt.WA_DeleteOnClose)
            
            self.mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            self.windows_opened += 1
            logger.info(f"✅ 視窗 #{index} 已開啟")
            
        except Exception as e:
            logger.error(f"❌ 開啟視窗 #{index} 失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def close_all_windows(self):
        """關閉所有視窗"""
        logger.info("=" * 60)
        logger.info("測試開始：關閉所有視窗")
        logger.info("=" * 60)
        
        sub_windows = self.mdi_area.subWindowList()
        count = len(sub_windows)
        logger.info(f"當前有 {count} 個視窗")
        
        if count == 0:
            logger.warning("沒有視窗需要關閉")
            return
        
        # 記錄開始時間
        start_time = time.time()
        
        # 調用 MDI 的 closeAllSubWindows
        self.mdi_area.closeAllSubWindows()
        
        # 記錄結束時間
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 檢查結果
        remaining = len(self.mdi_area.subWindowList())
        
        logger.info("=" * 60)
        logger.info(f"關閉操作完成")
        logger.info(f"  - 原有視窗: {count}")
        logger.info(f"  - 剩餘視窗: {remaining}")
        logger.info(f"  - 耗時: {elapsed:.3f} 秒")
        
        if remaining == 0:
            logger.info("✅ 測試通過：所有視窗已成功關閉，無崩潰")
        else:
            logger.warning(f"⚠️  警告：還有 {remaining} 個視窗未關閉")
        
        logger.info("=" * 60)
        
        self.windows_opened = 0
    
    def auto_test(self):
        """自動測試：開啟 5 個視窗，等待 3 秒，然後全部關閉"""
        logger.info("🤖 自動測試開始...")
        
        # 開啟 5 個視窗
        self.open_5_windows()
        
        # 等待 3 秒後關閉
        QTimer.singleShot(3000, self.close_all_windows)


def main():
    app = QApplication(sys.argv)
    
    window = TestMainWindow()
    window.show()
    
    logger.info("=" * 60)
    logger.info("進站分析多視窗關閉測試程式已啟動")
    logger.info("請執行以下步驟測試：")
    logger.info("1. 點擊「開啟 5 個進站分析視窗」")
    logger.info("2. 等待視窗載入")
    logger.info("3. 點擊「關閉所有視窗」")
    logger.info("4. 檢查是否有崩潰或「QThread: Destroyed while thread is still running」錯誤")
    logger.info("或直接點擊「自動測試」按鈕")
    logger.info("=" * 60)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
