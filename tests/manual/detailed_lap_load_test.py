"""
修正版測試：詳細圈速分析模組
目的：模擬主 GUI 的正確環境，避免閃退
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 測試 API 模式，讓數據管理器自行決定是否回退
if "F1T_DISABLE_LAPTIME_API" in os.environ:
    del os.environ["F1T_DISABLE_LAPTIME_API"]

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import QTimer

from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import (
    driverLapAnalysisMDI,
)

class TestMainWindow(QMainWindow):
    """測試主視窗 - 模擬主 GUI 環境"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detailed Lap Analysis Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建 MDI Area（模擬主 GUI 結構）
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        
        self.mdi = None
        self.load_completed = False
    
    def create_analysis_window(self):
        """創建詳細圈速分析視窗"""
        print("[TEST] 創建詳細圈速分析視窗...")
        self.mdi = driverLapAnalysisMDI()
        
        # 連接數據載入信號
        self.mdi.data_manager.data_loaded.connect(self.on_data_loaded)
        self.mdi.data_manager.load_error.connect(self.on_load_error)
        
        # 在 MDI Area 中創建子視窗
        widget = self.mdi.get_widget()
        sub_window = QMdiSubWindow()
        sub_window.setWidget(widget)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        print("[TEST] 更新參數...")
        self.mdi.update_parameters(year=2025, race="Japan", session="R")
    
    def on_data_loaded(self, data):
        """數據載入完成"""
        print(f"[TEST] ✅ 數據載入成功，類型: {type(data).__name__}")
        self.load_completed = True
        # 載入完成後 2 秒關閉
        QTimer.singleShot(2000, self.safe_close)
    
    def on_load_error(self, error):
        """數據載入錯誤"""
        print(f"[TEST] ❌ 數據載入失敗: {error}")
        self.load_completed = True
        # 錯誤後 2 秒關閉
        QTimer.singleShot(2000, self.safe_close)
    
    def safe_close(self):
        """安全關閉（觸發 closeEvent）"""
        print("[TEST] 準備安全關閉...")
        self.close()
    
    def closeEvent(self, event):
        """正確的關閉事件處理"""
        print("[TEST] closeEvent 觸發，開始清理...")
        
        # 停止所有載入
        if self.mdi and hasattr(self.mdi.data_manager, 'stop_loading'):
            print("[TEST] 停止數據載入...")
            self.mdi.data_manager.stop_loading()
        
        # 關閉所有 MDI 子視窗
        print("[TEST] 關閉所有子視窗...")
        self.mdi_area.closeAllSubWindows()
        
        print("[TEST] 清理完成，接受關閉事件")
        event.accept()
        
        # 延遲退出應用程式
        QTimer.singleShot(100, QApplication.quit)

def main():
    print("="*60)
    print("詳細圈速分析測試 - 修正版")
    print("="*60)
    
    app = QApplication(sys.argv)
    
    # 創建主視窗
    main_window = TestMainWindow()
    main_window.show()
    
    # 延遲創建分析視窗，確保主視窗完全初始化
    QTimer.singleShot(300, main_window.create_analysis_window)
    
    # 設置超時保護（如果 10 秒後還沒完成）
    def timeout():
        print("[TEST] ⏰ 超時，強制關閉...")
        main_window.safe_close()
    
    QTimer.singleShot(10000, timeout)
    
    print("[TEST] 進入事件循環...\n")
    exit_code = app.exec_()
    
    print(f"\n[TEST] 應用程式退出，退出碼: {exit_code}")
    print("done")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
