"""
深度調試測試：詳細圈速分析模組閃退問題
目的：逐步初始化並監控所有關鍵點
"""
import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

class SignalMonitor(QObject):
    """監控所有信號觸發"""
    def __init__(self):
        super().__init__()
        self.events = []
    
    def log_event(self, event_name, *args):
        timestamp = len(self.events)
        self.events.append((timestamp, event_name, args))
        print(f"[{timestamp:03d}] 🔔 {event_name}", end="")
        if args:
            print(f" | 參數: {args[:3]}")
        else:
            print()

class TestWindow(QMainWindow):
    """模擬主 GUI 環境"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detailed Lap Analysis - Deep Debug Test")
        self.setGeometry(100, 100, 1200, 800)
        
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        
        self.monitor = SignalMonitor()
        self.mdi = None
        self.sub_window = None
        
        print("\n" + "="*70)
        print("測試環境初始化完成")
        print("="*70)
    
    def create_analysis_window(self):
        """創建詳細圈速分析視窗"""
        try:
            self.monitor.log_event("開始導入模組")
            from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import (
                driverLapAnalysisMDI,
            )
            self.monitor.log_event("模組導入成功")
            
            self.monitor.log_event("創建 MDI 實例")
            self.mdi = driverLapAnalysisMDI()
            self.monitor.log_event("MDI 實例創建成功")
            
            # 連接所有可能的信號
            self.monitor.log_event("開始連接信號")
            dm = self.mdi.data_manager
            
            if hasattr(dm, 'data_loaded'):
                dm.data_loaded.connect(lambda d: self.monitor.log_event("data_loaded 觸發", type(d).__name__))
                self.monitor.log_event("已連接 data_loaded")
            
            if hasattr(dm, 'load_error'):
                dm.load_error.connect(lambda e: self.monitor.log_event("load_error 觸發", str(e)[:50]))
                self.monitor.log_event("已連接 load_error")
            
            if hasattr(dm, 'load_progress'):
                dm.load_progress.connect(lambda p: self.monitor.log_event("load_progress", f"{p}%"))
                self.monitor.log_event("已連接 load_progress")
            
            if hasattr(dm, 'status_changed'):
                dm.status_changed.connect(lambda s: self.monitor.log_event("status_changed", s[:50]))
                self.monitor.log_event("已連接 status_changed")
            
            # 檢查初始狀態
            print("\n初始狀態檢查:")
            print(f"  - 數據管理器: {dm}")
            print(f"  - API worker: {dm._api_worker}")
            print(f"  - CLI worker: {getattr(dm, '_cli_worker', 'N/A')}")
            print(f"  - 載入中標記: {dm._is_loading}")
            print(f"  - API 啟用: {getattr(dm, '_api_enabled', 'N/A')}")
            
            # 創建 MDI 子視窗
            self.monitor.log_event("創建 MDI 子視窗")
            widget = self.mdi.get_widget()
            self.sub_window = QMdiSubWindow()
            self.sub_window.setWidget(widget)
            self.mdi_area.addSubWindow(self.sub_window)
            self.sub_window.show()
            self.monitor.log_event("MDI 子視窗顯示完成")
            
            # 更新參數
            self.monitor.log_event("開始更新參數")
            self.mdi.update_parameters(year=2025, race="Japan", session="R")
            self.monitor.log_event("參數更新完成")
            
            # 定期檢查狀態
            self.setup_status_checks()
            
        except Exception as e:
            print(f"\n❌ 創建過程發生錯誤: {e}")
            print(traceback.format_exc())
            self.monitor.log_event("創建失敗", str(e))
    
    def setup_status_checks(self):
        """設置定期狀態檢查"""
        def check_status(interval):
            if not self.mdi:
                return
            
            dm = self.mdi.data_manager
            print(f"\n[狀態檢查 @ {interval}ms]")
            print(f"  - API worker 存在: {dm._api_worker is not None}")
            if dm._api_worker:
                print(f"    └─ 執行中: {dm._api_worker.isRunning()}")
            
            cli_worker = getattr(dm, '_cli_worker', None)
            print(f"  - CLI worker 存在: {cli_worker is not None}")
            if cli_worker:
                print(f"    └─ 執行中: {cli_worker.isRunning()}")
            
            print(f"  - 載入中: {dm._is_loading}")
            print(f"  - 最後數據源: {getattr(dm, '_last_data_source', 'N/A')}")
            print(f"  - 快取數據: {dm._cached_data is not None}")
        
        # 在不同時間點檢查
        for interval in [2000, 4000, 6000, 8000]:
            QTimer.singleShot(interval, lambda i=interval: check_status(i))
    
    def closeEvent(self, event):
        """正確的清理流程"""
        print("\n" + "="*70)
        print("開始關閉流程")
        print("="*70)
        
        self.monitor.log_event("closeEvent 觸發")
        
        if self.mdi:
            dm = self.mdi.data_manager
            
            # 檢查 worker 狀態
            print("\n關閉前 Worker 狀態:")
            print(f"  - API worker: {dm._api_worker}")
            if dm._api_worker:
                print(f"    └─ 執行中: {dm._api_worker.isRunning()}")
            
            cli_worker = getattr(dm, '_cli_worker', None)
            print(f"  - CLI worker: {cli_worker}")
            if cli_worker:
                print(f"    └─ 執行中: {cli_worker.isRunning()}")
            
            # 執行清理
            self.monitor.log_event("調用 stop_loading")
            if hasattr(dm, 'stop_loading'):
                dm.stop_loading()
            
            # 再次檢查
            QTimer.singleShot(100, self.check_cleanup_result)
        
        # 關閉所有子視窗
        self.monitor.log_event("關閉所有子視窗")
        self.mdi_area.closeAllSubWindows()
        
        # 打印事件日誌
        print("\n" + "="*70)
        print("事件日誌摘要:")
        print("="*70)
        for timestamp, event, args in self.monitor.events:
            print(f"  [{timestamp:03d}] {event}")
        
        self.monitor.log_event("closeEvent 完成")
        event.accept()
    
    def check_cleanup_result(self):
        """檢查清理結果"""
        if not self.mdi:
            return
        
        dm = self.mdi.data_manager
        print("\n清理後 Worker 狀態:")
        print(f"  - API worker: {dm._api_worker}")
        print(f"  - CLI worker: {getattr(dm, '_cli_worker', None)}")
        print(f"  - 載入中: {dm._is_loading}")

def main():
    print("="*70)
    print("詳細圈速分析模組 - 深度調試測試")
    print("="*70)
    
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # 延遲創建分析視窗，確保主視窗完全初始化
    QTimer.singleShot(500, window.create_analysis_window)
    
    # 設置自動關閉（給足夠時間完成載入）
    def auto_close():
        print("\n⏰ 超時自動關閉...")
        window.close()
        QTimer.singleShot(500, app.quit)
    
    QTimer.singleShot(12000, auto_close)
    
    print("\n進入事件循環...\n")
    exit_code = app.exec_()
    
    print("\n" + "="*70)
    print(f"應用程式退出，退出碼: {exit_code}")
    print("="*70)
    
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n✅ 測試完成，退出碼: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        print(traceback.format_exc())
        sys.exit(1)
