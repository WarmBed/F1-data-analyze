#!/usr/bin/env python3
"""
Telemetry Analysis 模組載入測試腳本
測試 QPainter 資源管理修正
"""

import sys
import os

# 添加專案根目錄到路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
from PyQt5.QtCore import QTimer, Qt
from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule

class TestMainWindow(QMainWindow):
    """測試主視窗 - 模擬主 GUI 環境"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Analysis 測試")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建 MDI 區域
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        
        self.analysis_module = None
        self.sub_window = None
        
        print("✅ 測試視窗創建完成")
        
        # 延遲創建分析視窗
        QTimer.singleShot(500, self.create_analysis_window)
        
        # 設定自動關閉定時器（10秒後）
        QTimer.singleShot(10000, self.safe_close)
    
    def create_analysis_window(self):
        """創建遙測分析視窗"""
        try:
            print("🔄 開始創建 Telemetry Analysis 模組...")
            
            # 創建模組實例
            self.analysis_module = TelemetryAnalysisModule()
            
            # 初始化模組
            if not self.analysis_module.initialize_module(parent_widget=self.mdi_area):
                print("❌ 模組初始化失敗")
                return
            
            print("✅ 模組初始化成功")
            
            # 更新參數
            year = "2025"
            race = "Japan"
            session = "R"
            
            print(f"🔄 更新參數: {year} {race} {session}")
            if not self.analysis_module.update_parameters(year, race, session):
                print("❌ 參數更新失敗")
                return
            
            print("✅ 參數更新成功")
            
            # 獲取 Widget
            widget = self.analysis_module.get_widget()
            if not widget:
                print("❌ 獲取 Widget 失敗")
                return
            
            print("✅ 獲取 Widget 成功")
            
            # 創建 MDI 子視窗
            self.sub_window = QMdiSubWindow()
            self.sub_window.setWidget(widget)
            self.sub_window.setWindowTitle(f"遙測分析 - {year} {race} {session}")
            self.sub_window.setAttribute(Qt.WA_DeleteOnClose, False)
            
            # 添加到 MDI 區域
            self.mdi_area.addSubWindow(self.sub_window)
            self.sub_window.show()
            
            print("✅ 遙測分析視窗創建完成")
            
            # 等待數據載入
            QTimer.singleShot(3000, self.check_data_status)
            
        except Exception as e:
            print(f"❌ 創建分析視窗時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def check_data_status(self):
        """檢查數據載入狀態"""
        if self.analysis_module:
            status = self.analysis_module.get_status_info()
            print(f"📊 模組狀態:")
            print(f"  - 模組名稱: {status.get('module_name')}")
            print(f"  - 當前參數: {status.get('current_year')} {status.get('current_race')} {status.get('current_session')}")
            print(f"  - 正在載入: {status.get('is_loading')}")
            print(f"  - 數據已載入: {status.get('data_loaded')}")
    
    def safe_close(self):
        """安全關閉"""
        print("🔄 開始安全關閉...")
        
        try:
            # 停止數據載入
            if self.analysis_module and hasattr(self.analysis_module, 'data_manager'):
                print("  停止數據管理器...")
                if hasattr(self.analysis_module.data_manager, '_stop_generation_monitoring'):
                    self.analysis_module.data_manager._stop_generation_monitoring()
            
            # 關閉子視窗
            if self.sub_window:
                print("  關閉分析視窗...")
                self.sub_window.close()
            
            # 清理模組
            if self.analysis_module:
                print("  清理模組資源...")
                self.analysis_module.cleanup()
            
            print("✅ 資源清理完成")
            
        except Exception as e:
            print(f"⚠️ 清理過程中發生錯誤: {e}")
        
        finally:
            # 關閉主視窗
            print("🔚 關閉測試視窗")
            self.close()
            print("done")
    
    def closeEvent(self, event):
        """視窗關閉事件"""
        print("📌 closeEvent 觸發")
        
        # 確保清理完成
        if self.analysis_module:
            try:
                if hasattr(self.analysis_module, 'data_manager'):
                    if hasattr(self.analysis_module.data_manager, '_stop_generation_monitoring'):
                        self.analysis_module.data_manager._stop_generation_monitoring()
                self.analysis_module.cleanup()
            except Exception as e:
                print(f"⚠️ closeEvent 清理錯誤: {e}")
        
        event.accept()


if __name__ == "__main__":
    print("🚀 啟動 Telemetry Analysis 測試...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Telemetry Analysis Test")
    
    window = TestMainWindow()
    window.show()
    
    exit_code = app.exec_()
    print(f"📊 應用程式退出碼: {exit_code}")
    sys.exit(exit_code)
