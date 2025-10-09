#!/usr/bin/env python3
"""
載入指示器組件
用於改善 API 載入時的用戶體驗
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class LoadingIndicator(QWidget):
    """通用載入指示器組件"""
    
    def __init__(self, parent=None, message="正在載入數據..."):
        super().__init__(parent)
        self.setObjectName("LoadingIndicator")
        self._setup_ui(message)
        self._start_animation()
    
    def _setup_ui(self, message):
        """設置 UI"""
        # 半透明黑色背景
        self.setStyleSheet("""
            QWidget#LoadingIndicator {
                background-color: rgba(0, 0, 0, 0.85);
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
            QLabel#Hint {
                color: #CCCCCC;
                font-size: 10pt;
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
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 旋轉動畫符號
        self.spinner = QLabel("⏳")
        self.spinner.setObjectName("Spinner")
        self.spinner.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinner)
        
        # 載入訊息
        self.message_label = QLabel(message)
        self.message_label.setObjectName("Message")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 無限進度條
        self.progress_bar.setFixedWidth(400)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        
        # 提示文字
        self.hint_label = QLabel("💡 首次載入可能需要 5-10 秒，請稍候...")
        self.hint_label.setObjectName("Hint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        # 技術細節（可選）
        self.detail_label = QLabel("正在連接 API 伺服器...")
        self.detail_label.setObjectName("Hint")
        self.detail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_label)
    
    def _start_animation(self):
        """啟動動畫"""
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_spinner)
        self.animation_timer.start(500)  # 每 500ms 更新
        
        self.spinner_frames = ["⏳", "⌛", "⏳", "⌛"]
        self.current_frame = 0
    
    def _update_spinner(self):
        """更新旋轉動畫"""
        self.spinner.setText(self.spinner_frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.spinner_frames)
    
    def update_message(self, message: str):
        """更新載入訊息"""
        self.message_label.setText(message)
    
    def update_progress(self, progress: int, detail: str = None):
        """更新進度（0-100）"""
        if progress >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setRange(0, 0)  # 無限進度條
        
        if detail:
            self.detail_label.setText(detail)
    
    def cleanup(self):
        """清理資源"""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
            self.animation_timer.deleteLater()


class CacheBanner(QWidget):
    """緩存數據提示橫幅"""
    
    def __init__(self, parent=None, cache_age="3 分鐘前"):
        super().__init__(parent)
        self.setObjectName("CacheBanner")
        self._setup_ui(cache_age)
    
    def _setup_ui(self, cache_age):
        """設置 UI"""
        self.setStyleSheet("""
            QWidget#CacheBanner {
                background-color: #FFF3CD;
                border: 1px solid #FFE69C;
                border-radius: 5px;
            }
            QLabel {
                color: #856404;
                font-size: 10pt;
                padding: 5px;
            }
        """)
        self.setFixedHeight(30)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        label = QLabel(f"📦 使用緩存數據（{cache_age}）- 點擊右上角刷新按鈕更新")
        layout.addWidget(label)


# 使用範例
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試載入指示器
    indicator = LoadingIndicator(message="正在載入輪胎分析數據...")
    indicator.resize(600, 400)
    indicator.show()
    
    # 模擬進度更新
    import time
    def update_progress():
        for i in range(0, 101, 10):
            indicator.update_progress(i, f"已載入 {i}%...")
            app.processEvents()
            time.sleep(0.3)
        indicator.close()
    
    QTimer.singleShot(1000, update_progress)
    
    sys.exit(app.exec_())
