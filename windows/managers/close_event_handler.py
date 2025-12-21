# -*- coding: utf-8 -*-
"""
CloseEventHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class CloseEventHandler:
    """從 f1t_gui_main.py 提取的 closeEvent 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def closeEvent(self, event):
        """視窗關閉事件處理"""
        try:
            # === 步驟 1: 停止所有定時器 ===
            if hasattr(self, 'api_health_timer') and self.main_window.api_health_timer:
                self.main_window.api_health_timer.stop()
                self.main_window.api_health_timer.deleteLater()
                self.main_window.api_health_timer = None
            
            # === 步驟 2: 正確關閉 API Health Worker ===
            if hasattr(self, '_api_health_worker') and self.main_window._api_health_worker:
                try:
                    # 斷開所有信號連接
                    self.main_window._api_health_worker.result_ready.disconnect(self.main_window.on_api_health_result)
                except Exception:
                    pass
                try:
                    self.main_window._api_health_worker.finished.disconnect(self.main_window.on_api_health_finished)
                except Exception:
                    pass
                
                # ✅ 正確的執行緒停止順序
                if self.main_window._api_health_worker.isRunning():
                    # 1. 設置停止標誌（應用層）
                    self.main_window._api_health_worker.stop_worker()
                    # 2. 請求中斷（Qt 層）
                    self.main_window._api_health_worker.requestInterruption()
                    # 3. 等待執行緒完成
                    self.main_window._api_health_worker.wait(500)  # 增加到 500ms
                    # 4. 如果仍在運行，強制終止
                    if self.main_window._api_health_worker.isRunning():
                        logger.debug(f"[MAIN] ⚠️  API Health Worker 未在時限內結束，強制終止")
                        self.main_window._api_health_worker.quit()
                        self.main_window._api_health_worker.wait(200)
                        if self.main_window._api_health_worker.isRunning():
                            self.main_window._api_health_worker.terminate()
                            self.main_window._api_health_worker.wait(100)
                
                # 5. 標記為待刪除
                self.main_window._api_health_worker.deleteLater()
                self.main_window._api_health_worker = None
            self.main_window._api_health_worker_active = False

            if hasattr(self, 'api_runtime_timer') and self.main_window.api_runtime_timer:
                self.main_window.api_runtime_timer.stop()
                self.main_window.api_runtime_timer.deleteLater()
                self.main_window.api_runtime_timer = None
            
            # === 步驟 3: 正確關閉 API Runtime Worker ===
            if hasattr(self, '_api_runtime_worker') and self.main_window._api_runtime_worker:
                try:
                    self.main_window._api_runtime_worker.result_ready.disconnect(self.main_window.on_api_runtime_result)
                except Exception:
                    pass
                try:
                    self.main_window._api_runtime_worker.finished.disconnect(self.main_window.on_api_runtime_finished)
                except Exception:
                    pass
                
                # ✅ 正確的執行緒停止順序
                if self.main_window._api_runtime_worker.isRunning():
                    # 1. 設置停止標誌（應用層）
                    self.main_window._api_runtime_worker.stop_worker()
                    # 2. 請求中斷（Qt 層）
                    self.main_window._api_runtime_worker.requestInterruption()
                    # 3. 等待執行緒完成
                    self.main_window._api_runtime_worker.wait(500)  # 增加到 500ms
                    # 4. 如果仍在運行，強制終止
                    if self.main_window._api_runtime_worker.isRunning():
                        logger.debug(f"[MAIN] ⚠️  API Runtime Worker 未在時限內結束，強制終止")
                        self.main_window._api_runtime_worker.quit()
                        self.main_window._api_runtime_worker.wait(200)
                        if self.main_window._api_runtime_worker.isRunning():
                            self.main_window._api_runtime_worker.terminate()
                            self.main_window._api_runtime_worker.wait(100)
                
                # 5. 標記為待刪除
                self.main_window._api_runtime_worker.deleteLater()
                self.main_window._api_runtime_worker = None
            self.main_window._api_runtime_worker_active = False

            logger.debug("[MAIN] 🛑 接收到關閉請求，開始清理資源...")
            
            # 顯示關閉確認對話框（可選）
            from core.gui_i18n import tr
            reply = QMessageBox.question(
                self, 
                tr('confirm_exit', 'Confirm Exit'), 
                tr('confirm_exit_message', 'Are you sure you want to exit F1T Professional Racing Analysis Workstation?\n\nAll running analyses will be stopped.'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # 停止所有正在執行的 CLI 分析
            logger.debug("[MAIN] 🔄 停止所有分析進程...")
            self.main_window.stop_all_analyses()
            
            # 關閉所有子視窗
            logger.debug("[MAIN] 🪟 關閉所有子視窗...")
            self.main_window.close_all_subwindows()
            
            # 清理分析模組管理器
            if hasattr(self, 'analysis_module_manager'):
                try:
                    self.main_window.analysis_module_manager.cleanup_all()
                    logger.debug("[MAIN] 🧹 分析模組管理器已清理")
                except Exception as e:
                    logger.debug(f"[MAIN] ⚠️ 分析模組管理器清理警告: {e}")
            
            # 清理全域 CLI 分析管理器
            try:
                cli_analysis_manager.cleanup_all()
                logger.debug("[MAIN] 🔧 CLI 分析管理器已清理")
            except Exception as e:
                logger.debug(f"[MAIN] ⚠️ CLI 分析管理器清理警告: {e}")
            
            # 強制垃圾回收
            try:
                import gc
                gc.collect()
                logger.debug("[MAIN] 🗑️ 垃圾回收完成")
            except Exception as e:
                logger.debug(f"[MAIN] ⚠️ 垃圾回收警告: {e}")
            
            logger.debug("[MAIN] ✅ 資源清理完成，程序即將退出")
            
            # 接受關閉事件
            event.accept()
            
            # 確保應用程序完全退出
            from PyQt5.QtWidgets import QApplication
            import sys
            
            app = QApplication.instance()
            if app:
                app.quit()
                # 給一點時間讓 Qt 完成清理
                QTimer.singleShot(100, lambda: sys.exit(0))
            
        except Exception as e:
            logger.debug(f"[MAIN] ❌ 關閉事件處理錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 即使出錯也要強制關閉
            event.accept()
            try:
                import sys
                sys.exit(1)
            except:
                pass
