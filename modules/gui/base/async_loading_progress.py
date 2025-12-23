#!/usr/bin/env python3
"""
通用異步載入進度管理器
用於統一管理所有模組的載入進度顯示，避免阻塞主執行緒

設計原則：
1. 完全異步 - 不使用任何阻塞調用（如 worker.wait()）
2. 信號驅動 - 使用 Qt 信號槽機制更新進度
3. 可共享 - 所有分析模組都可以使用
4. 用戶友好 - 清晰的進度指示和狀態訊息

Author: F1T Team
Date: 2025-10-17
Version: 1.0.0
"""

from typing import Optional, Callable
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from core.gui_i18n import tr


class AsyncLoadingProgressManager(QWidget):
    """
    異步載入進度管理器
    
    特性：
    - 不阻塞主執行緒（不使用 wait()）
    - 顯示詳細的載入狀態
    - 支援進度百分比和無限進度條
    - 自動旋轉動畫
    - 可取消載入操作
    
    使用範例：
        # 創建管理器
        progress = AsyncLoadingProgressManager(parent=self)
        progress.set_message("正在載入 Throttle Box Plot 數據...")
        progress.show()
        
        # 連接到 Worker 信號
        self.api_worker.progress.connect(progress.update_progress)
        self.api_worker.success.connect(lambda: progress.set_complete("載入成功"))
        self.api_worker.failure.connect(lambda msg: progress.set_error(f"載入失敗: {msg}"))
        
        # 啟動 Worker
        self.api_worker.start()
    """
    
    # 信號定義
    cancelled = pyqtSignal()  # 用戶取消載入
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 message: str = "正在載入數據...",
                 show_cancel_button: bool = False):
        """
        初始化進度管理器
        
        Args:
            parent: 父視窗
            message: 載入訊息
            show_cancel_button: 是否顯示取消按鈕（暫不實現）
        """
        super().__init__(parent)
        self.setObjectName("AsyncLoadingProgress")
        
        # 狀態變數
        self._is_loading = False
        self._current_progress = 0
        self._animation_frame = 0
        self._animation_timer: Optional[QTimer] = None
        
        # 建立 UI
        self._setup_ui(message)
        
    def _setup_ui(self, message: str):
        """設置 UI 組件"""
        # 設置樣式
        self.setStyleSheet("""
            QWidget#AsyncLoadingProgress {
                background-color: rgba(0, 0, 0, 0.85);
                border-radius: 10px;
            }
            QLabel#Spinner {
                color: white;
                font-size: 48pt;
            }
            QLabel#Message {
                color: white;
                font-size: 14pt;
                font-weight: bold;
            }
            QLabel#Detail {
                color: #CCCCCC;
                font-size: 10pt;
            }
            QLabel#Hint {
                color: #AAAAAA;
                font-size: 9pt;
                font-style: italic;
            }
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid white;
                border-radius: 5px;
                text-align: center;
                color: white;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 旋轉動畫符號
        self.spinner = QLabel("⏳")
        self.spinner.setObjectName("Spinner")
        self.spinner.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(48)
        self.spinner.setFont(font)
        layout.addWidget(self.spinner)
        
        # 主要訊息
        self.message_label = QLabel(message)
        self.message_label.setObjectName("Message")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 無限進度條
        self.progress_bar.setFixedWidth(500)
        self.progress_bar.setFixedHeight(30)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        
        # 詳細狀態
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("Detail")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)
        
        # 提示文字
        self.hint_label = QLabel("💡 首次載入可能需要 5-10 秒，請稍候...")
        self.hint_label.setObjectName("Hint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        # 啟動動畫
        self._start_animation()
    
    def _start_animation(self):
        """啟動旋轉動畫（不阻塞主執行緒）"""
        if self._animation_timer is not None:
            self._animation_timer.stop()
            
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_spinner)
        self._animation_timer.start(500)  # 每 500ms 更新一次
        
        self._spinner_frames = ["⏳", "⌛", "⏳", "⌛"]
        self._animation_frame = 0
        self._is_loading = True
    
    def _update_spinner(self):
        """更新旋轉動畫幀"""
        if not self._is_loading:
            return
            
        self.spinner.setText(self._spinner_frames[self._animation_frame])
        self._animation_frame = (self._animation_frame + 1) % len(self._spinner_frames)
    
    def set_message(self, message: str):
        """
        更新主要訊息
        
        Args:
            message: 新的訊息文字
        """
        self.message_label.setText(message)
        QApplication.processEvents()  # 立即更新 UI
    
    def update_progress(self, progress: int, detail: Optional[str] = None):
        """
        更新進度
        
        Args:
            progress: 進度百分比 (0-100)，-1 表示無限進度條
            detail: 詳細狀態訊息（可選）
        """
        self._current_progress = progress
        
        if progress >= 0:
            # 顯示具體進度
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{progress}%")
        else:
            # 無限進度條
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("")
        
        if detail:
            self.detail_label.setText(detail)
        
        QApplication.processEvents()  # 立即更新 UI
    
    def set_complete(self, message: str = "載入完成"):
        """
        設置為完成狀態
        
        Args:
            message: 完成訊息
        """
        self._is_loading = False
        if self._animation_timer:
            self._animation_timer.stop()
        
        self.spinner.setText("✅")
        self.message_label.setText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100%")
        self.detail_label.setText("")
        self.hint_label.setText("✨ 數據已成功載入")
        
        QApplication.processEvents()
        
        # 1 秒後自動關閉
        QTimer.singleShot(1000, self.hide)
    
    def set_error(self, error_message: str):
        """
        設置為錯誤狀態
        
        Args:
            error_message: 錯誤訊息
        """
        self._is_loading = False
        if self._animation_timer:
            self._animation_timer.stop()
        
        self.spinner.setText("❌")
        self.message_label.setText("載入失敗")
        self.detail_label.setText(error_message)
        self.hint_label.setText("請檢查網路連接或稍後再試")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # 進度條變紅色
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid white;
                border-radius: 5px;
                text-align: center;
                color: white;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #F44336;
                border-radius: 5px;
            }
        """)
        
        QApplication.processEvents()
        
        # 3 秒後自動關閉
        QTimer.singleShot(3000, self.hide)
    
    def cleanup(self):
        """清理資源"""
        self._is_loading = False
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer.deleteLater()
            self._animation_timer = None
    
    def showEvent(self, event):
        """顯示時啟動動畫"""
        super().showEvent(event)
        if not self._is_loading:
            self._start_animation()
    
    def hideEvent(self, event):
        """隱藏時停止動畫"""
        super().hideEvent(event)
        self._is_loading = False
        if self._animation_timer:
            self._animation_timer.stop()
    
    def closeEvent(self, event):
        """關閉時清理資源"""
        self.cleanup()
        super().closeEvent(event)


# 使用範例
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout
    from PyQt5.QtCore import QThread, pyqtSignal
    import time
    
    # 模擬 API Worker
    class MockApiWorker(QThread):
        progress = pyqtSignal(int)
        success = pyqtSignal(dict)
        failure = pyqtSignal(str)
        
        def run(self):
            for i in range(0, 101, 10):
                time.sleep(0.5)
                self.progress.emit(i)
            self.success.emit({"data": "test"})
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    test_window = QWidget()
    test_window.resize(800, 600)
    layout = QVBoxLayout(test_window)
    
    # 創建進度管理器
    progress_manager = AsyncLoadingProgressManager(
        parent=test_window,
        message="正在測試異步載入進度管理器..."
    )
    progress_manager.setFixedSize(600, 400)
    layout.addWidget(progress_manager)
    
    # 測試按鈕
    btn = QPushButton("開始測試載入")
    def test_loading():
        progress_manager.show()
        worker = MockApiWorker()
        worker.progress.connect(progress_manager.update_progress)
        worker.success.connect(lambda: progress_manager.set_complete("測試完成！"))
        worker.start()
    
    btn.clicked.connect(test_loading)
    layout.addWidget(btn)
    
    test_window.show()
    sys.exit(app.exec_())
