#!/usr/bin/env python3
"""
F1T 預載畫面 (Splash Screen) - 5 種風格版本
F1T Splash Screen - 5 Style Variations

提供 5 種不同視覺風格的啟動畫面，均包含：
- F1T Logo 顯示
- 進度條動畫
- 載入狀態訊息
- 版本資訊
"""

from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QLinearGradient
from pathlib import Path
from typing import Optional
import sys

from core.logger import get_logger

# ✅ 導入集中管理的版本號
from config.version import APP_VERSION

logger = get_logger("splash_screen", component="gui")

# EXE 模式檢測和資源路徑處理
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_resource_path(relative_path):
    """獲取資源文件的絕對路徑（支援 EXE 模式）"""
    if IS_EXE_MODE:
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path.cwd()
    return base_path / relative_path


class BaseSplashScreen(QSplashScreen):
    """基礎預載畫面類別"""
    
    progress_updated = pyqtSignal(int)  # 進度更新信號
    
    def __init__(self, logo_path: str, width: int = 600, height: int = 300):
        # 創建空白畫布作為基礎
        base_pixmap = QPixmap(width, height)
        base_pixmap.fill(QColor(20, 20, 30))
        
        super().__init__(base_pixmap)
        
        self.width = width
        self.height = height
        self.progress = 0
        self.message = "正在初始化..."
        self.version = APP_VERSION  # ✅ 使用集中管理的版本號
        self._is_painting = False  # 繪圖狀態標記
        
        # 設置視窗屬性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # 載入 logo (可選，供子類使用)
        self.logo_pixmap = QPixmap(logo_path)
        if not self.logo_pixmap.isNull():
            self.logo_pixmap = self.logo_pixmap.scaled(
                width // 3, height // 3, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
        
    def set_progress(self, value: int, message: str = ""):
        """設置進度 (0-100)"""
        self.progress = max(0, min(100, value))
        if message:
            self.message = message
        self.progress_updated.emit(self.progress)
        # 使用 update() 而不是 repaint() 以避免繪圖衝突
        self.update()
        
    def drawContents(self, painter: QPainter):
        """繪製內容 - 子類別需要實現"""
        pass
    
    def paintEvent(self, event):
        """重寫 paintEvent 以避免繪圖衝突"""
        if self._is_painting:
            return  # 如果正在繪圖，跳過
        
        self._is_painting = True
        try:
            super().paintEvent(event)
        finally:
            self._is_painting = False
    
    def closeEvent(self, event):
        """關閉事件 - 確保繪圖完成"""
        # 等待繪圖完成
        while self._is_painting:
            QApplication.processEvents()
        super().closeEvent(event)


# ========================================
# 版本 1: 經典賽車風格 (F1 Red Racing)
# ========================================
class SplashScreenV1_Racing(BaseSplashScreen):
    """版本 1: 經典賽車風格 - F1 紅色主題"""
    
    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 繪製半透明深色背景
        painter.fillRect(0, 0, self.width, self.height, QColor(15, 15, 20, 200))
        
        # 2. 繪製標題 (F1T Logo 文字)
        title_font = QFont("Arial Black", 36, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(220, 38, 38))  # F1 紅色
        painter.drawText(0, 80, self.width, 60, Qt.AlignCenter, "F1T")
        
        # 3. 副標題
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(0, 140, self.width, 30, Qt.AlignCenter, "Professional Racing Analysis Workstation")
        
        # 4. 進度條 (F1 賽車風格 - 紅色漸層)
        progress_x = 100
        progress_y = self.height - 120
        progress_width = self.width - 200
        progress_height = 20
        
        # 背景
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, QColor(50, 50, 60))
        
        # 進度 (紅色漸層)
        if self.progress > 0:
            gradient = QLinearGradient(progress_x, progress_y, progress_x + progress_width, progress_y)
            gradient.setColorAt(0, QColor(220, 38, 38))  # F1 紅
            gradient.setColorAt(1, QColor(180, 20, 20))  # 深紅
            painter.fillRect(progress_x, progress_y, 
                           int(progress_width * self.progress / 100), 
                           progress_height, gradient)
        
        # 邊框
        painter.setPen(QPen(QColor(220, 38, 38), 2))
        painter.drawRect(progress_x, progress_y, progress_width, progress_height)
        
        # 5. 進度百分比
        percent_font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(percent_font)
        painter.setPen(QColor(220, 38, 38))
        painter.drawText(0, progress_y + progress_height + 10, self.width, 20, 
                        Qt.AlignCenter, f"{self.progress}%")
        
        # 6. 狀態訊息
        message_font = QFont("Arial", 9)
        painter.setFont(message_font)
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(0, progress_y - 15, self.width, 20, Qt.AlignCenter, self.message)
        
        # 7. 版本資訊
        version_font = QFont("Arial", 8)
        painter.setFont(version_font)
        painter.setPen(QColor(120, 120, 120))
        painter.drawText(10, self.height - 15, 200, 20, Qt.AlignLeft, f"Version {self.version}")


# ========================================
# 版本 2: 現代極簡風格 (Minimal Light - 白底黑字)
# ========================================
class SplashScreenV2_Minimal(BaseSplashScreen):
    """版本 2: 現代極簡風格 - 白色主題（白底黑字）"""
    
    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 純白背景
        painter.fillRect(0, 0, self.width, self.height, QColor(255, 255, 255))
        
        # 2. Logo 區域 (留空給背景圖片)
        # 如果需要可以在這裡繪製額外的裝飾
        
        # 3. 產品名稱 (簡潔黑字)
        title_font = QFont("Segoe UI Light", 32)
        painter.setFont(title_font)
        painter.setPen(QColor(30, 30, 30))  # 深灰黑色
        painter.drawText(0, self.height // 2 - 40, self.width, 50, Qt.AlignCenter, "PIT WALL")
        
        # 4. 進度條 (極簡線條)
        progress_x = 150
        progress_y = self.height // 2 + 40
        progress_width = self.width - 300
        progress_height = 2  # 極細線條
        
        # 背景線（淺灰色）
        painter.setPen(QPen(QColor(220, 220, 220), progress_height))
        painter.drawLine(progress_x, progress_y, progress_x + progress_width, progress_y)
        
        # 進度線 (深藍色)
        if self.progress > 0:
            painter.setPen(QPen(QColor(0, 122, 255), progress_height + 2))  # Apple 藍
            painter.drawLine(progress_x, progress_y, 
                           progress_x + int(progress_width * self.progress / 100), progress_y)
        
        # 5. 狀態訊息 (灰色字)
        message_font = QFont("Segoe UI", 9)
        painter.setFont(message_font)
        painter.setPen(QColor(100, 100, 100))  # 中灰色
        painter.drawText(0, progress_y + 30, self.width, 20, Qt.AlignCenter, self.message)
        
        # 6. 版本 (右下角 - 淺灰色)
        version_font = QFont("Segoe UI", 8)
        painter.setFont(version_font)
        painter.setPen(QColor(160, 160, 160))  # 淺灰色
        painter.drawText(self.width - 100, self.height - 20, 90, 20, Qt.AlignRight, self.version)


# ========================================
# 版本 3: 科技未來風格 (Cyber Tech)
# ========================================
class SplashScreenV3_Cyber(BaseSplashScreen):
    """版本 3: 科技未來風格 - 霓虹藍綠主題"""
    
    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 深色背景 + 網格效果
        painter.fillRect(0, 0, self.width, self.height, QColor(5, 10, 20))
        
        # 繪製網格線 (可選)
        painter.setPen(QPen(QColor(0, 180, 255, 30), 1))
        for i in range(0, self.width, 40):
            painter.drawLine(i, 0, i, self.height)
        for i in range(0, self.height, 40):
            painter.drawLine(0, i, self.width, i)
        
        # 2. 標題 (霓虹效果)
        title_font = QFont("Consolas", 32, QFont.Bold)
        painter.setFont(title_font)
        
        # 外發光效果 (多層繪製)
        for offset in [6, 4, 2]:
            painter.setPen(QColor(0, 180, 255, 50))
            painter.drawText(offset, 90 + offset, self.width, 60, Qt.AlignCenter, "F1T")
        
        # 主文字
        painter.setPen(QColor(0, 255, 200))  # 霓虹綠藍
        painter.drawText(0, 90, self.width, 60, Qt.AlignCenter, "F1T")
        
        # 3. 副標題
        subtitle_font = QFont("Consolas", 10)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(0, 150, self.width, 30, Qt.AlignCenter, "[ TELEMETRY ANALYSIS SYSTEM ]")
        
        # 4. 進度條 (霓虹風格)
        progress_x = 100
        progress_y = self.height - 100
        progress_width = self.width - 200
        progress_height = 8
        
        # 外框發光
        painter.setPen(QPen(QColor(0, 180, 255, 100), 3))
        painter.drawRect(progress_x - 2, progress_y - 2, progress_width + 4, progress_height + 4)
        
        # 背景
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, QColor(10, 20, 30))
        
        # 進度 (霓虹藍綠漸層)
        if self.progress > 0:
            gradient = QLinearGradient(progress_x, progress_y, progress_x + progress_width, progress_y)
            gradient.setColorAt(0, QColor(0, 180, 255))  # 霓虹藍
            gradient.setColorAt(1, QColor(0, 255, 200))  # 霓虹綠
            painter.fillRect(progress_x, progress_y, 
                           int(progress_width * self.progress / 100), 
                           progress_height, gradient)
        
        # 5. 數字化進度顯示
        percent_font = QFont("Consolas", 11, QFont.Bold)
        painter.setFont(percent_font)
        painter.setPen(QColor(0, 255, 200))
        painter.drawText(0, progress_y + progress_height + 15, self.width, 20, 
                        Qt.AlignCenter, f"// {self.progress:03d}% //")
        
        # 6. 狀態訊息
        message_font = QFont("Consolas", 8)
        painter.setFont(message_font)
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(0, progress_y - 20, self.width, 20, Qt.AlignCenter, f"> {self.message}")
        
        # 7. 版本
        painter.drawText(10, self.height - 10, 200, 20, Qt.AlignLeft, f"v{self.version}")


# ========================================
# 版本 4: 優雅專業風格 (Professional)
# ========================================
class SplashScreenV4_Professional(BaseSplashScreen):
    """版本 4: 優雅專業風格 - 深藍商務主題"""
    
    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 漸層背景 (深藍到黑)
        gradient_bg = QLinearGradient(0, 0, 0, self.height)
        gradient_bg.setColorAt(0, QColor(25, 35, 50))
        gradient_bg.setColorAt(1, QColor(10, 15, 25))
        painter.fillRect(0, 0, self.width, self.height, gradient_bg)
        
        # 2. 裝飾線條
        painter.setPen(QPen(QColor(70, 130, 180, 100), 2))
        painter.drawLine(50, 200, self.width - 50, 200)
        
        # 3. 標題
        title_font = QFont("Georgia", 28, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(240, 240, 250))
        painter.drawText(0, 100, self.width, 50, Qt.AlignCenter, "F1 TelemetryStation Pro")
        
        # 4. 副標題
        subtitle_font = QFont("Georgia", 11)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(180, 190, 200))
        painter.drawText(0, 155, self.width, 30, Qt.AlignCenter, "Professional Racing Data Analysis Platform")
        
        # 5. 進度條 (優雅風格)
        progress_x = 120
        progress_y = self.height - 120
        progress_width = self.width - 240
        progress_height = 12
        
        # 背景 (帶圓角)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(40, 50, 65))
        painter.drawRoundedRect(progress_x, progress_y, progress_width, progress_height, 6, 6)
        
        # 進度 (金色漸層)
        if self.progress > 0:
            gradient = QLinearGradient(progress_x, progress_y, progress_x + progress_width, progress_y)
            gradient.setColorAt(0, QColor(70, 130, 180))  # 鋼藍
            gradient.setColorAt(1, QColor(100, 149, 237))  # 矢車菊藍
            painter.setBrush(gradient)
            painter.drawRoundedRect(progress_x, progress_y, 
                                   int(progress_width * self.progress / 100), 
                                   progress_height, 6, 6)
        
        # 外框
        painter.setPen(QPen(QColor(70, 130, 180, 150), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(progress_x, progress_y, progress_width, progress_height, 6, 6)
        
        # 6. 進度百分比
        percent_font = QFont("Georgia", 10)
        painter.setFont(percent_font)
        painter.setPen(QColor(180, 190, 200))
        painter.drawText(0, progress_y + progress_height + 12, self.width, 20, 
                        Qt.AlignCenter, f"{self.progress}%")
        
        # 7. 狀態訊息
        message_font = QFont("Georgia", 9)
        painter.setFont(message_font)
        painter.setPen(QColor(150, 160, 170))
        painter.drawText(0, progress_y - 18, self.width, 20, Qt.AlignCenter, self.message)
        
        # 8. 版本和版權
        version_font = QFont("Georgia", 8)
        painter.setFont(version_font)
        painter.setPen(QColor(100, 110, 120))
        painter.drawText(0, self.height - 20, self.width, 20, Qt.AlignCenter, 
                        f"Version {self.version} | © 2025 F1T Development Team")


# ========================================
# 版本 5: 動態賽道風格 (Dynamic Track)
# ========================================
class SplashScreenV5_Track(BaseSplashScreen):
    """版本 5: 動態賽道風格 - 賽道線條主題"""
    
    def __init__(self, logo_path: str, width: int = 600, height: int = 300):
        super().__init__(logo_path, width, height)
        self.animation_offset = 0
        self._animation_timer = None
        
    def showEvent(self, event):
        """視窗顯示時啟動動畫"""
        super().showEvent(event)
        if self._animation_timer is None:
            self._animation_timer = QTimer(self)
            self._animation_timer.timeout.connect(self._update_animation)
            self._animation_timer.start(50)  # 每 50ms 更新
    
    def closeEvent(self, event):
        """關閉時停止動畫"""
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer = None
        super().closeEvent(event)
    
    def _update_animation(self):
        """更新動畫幀"""
        if not self._is_painting:  # 只在不繪圖時更新
            dash_length = 30
            gap_length = 20
            self.animation_offset = (self.animation_offset + 2) % (dash_length + gap_length)
            self.update()  # 使用 update() 而不是 repaint()
        
    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 深色背景
        painter.fillRect(0, 0, self.width, self.height, QColor(18, 18, 22))
        
        # 2. 賽道線條動畫 (模擬賽道邊線)
        painter.setPen(QPen(QColor(255, 255, 255, 40), 3))
        dash_length = 30
        gap_length = 20
        
        # 上方賽道線
        x = self.animation_offset
        y = 60
        while x < self.width + dash_length:
            painter.drawLine(x, y, x + dash_length, y)
            x += dash_length + gap_length
        
        # 下方賽道線
        x = self.animation_offset
        y = self.height - 60
        while x < self.width + dash_length:
            painter.drawLine(x, y, x + dash_length, y)
            x += dash_length + gap_length
        
        # 3. 標題
        title_font = QFont("Arial Black", 32, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 70, 70))  # 賽車紅
        painter.drawText(0, 120, self.width, 60, Qt.AlignCenter, "F1T")
        
        # 4. 副標題
        subtitle_font = QFont("Arial", 11)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(0, 175, self.width, 30, Qt.AlignCenter, "Telemetry Analysis Station")
        
        # 5. 進度條 (賽道風格 - 方格旗配色)
        progress_x = 100
        progress_y = self.height // 2 + 50
        progress_width = self.width - 200
        progress_height = 25
        
        # 背景 (深色)
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, QColor(30, 30, 35))
        
        # 進度 (方格旗風格 - 黑白漸層到紅色)
        if self.progress > 0:
            current_width = int(progress_width * self.progress / 100)
            
            # 使用紅色漸層
            gradient = QLinearGradient(progress_x, progress_y, progress_x + current_width, progress_y)
            gradient.setColorAt(0, QColor(200, 50, 50))
            gradient.setColorAt(0.5, QColor(255, 70, 70))
            gradient.setColorAt(1, QColor(220, 50, 50))
            painter.fillRect(progress_x, progress_y, current_width, progress_height, gradient)
            
            # 添加光澤效果
            gloss = QLinearGradient(progress_x, progress_y, progress_x, progress_y + progress_height)
            gloss.setColorAt(0, QColor(255, 255, 255, 60))
            gloss.setColorAt(0.5, QColor(255, 255, 255, 0))
            painter.fillRect(progress_x, progress_y, current_width, progress_height // 2, gloss)
        
        # 邊框
        painter.setPen(QPen(QColor(255, 70, 70), 2))
        painter.drawRect(progress_x, progress_y, progress_width, progress_height)
        
        # 6. 進度百分比 (在進度條內)
        percent_font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(percent_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(progress_x, progress_y, progress_width, progress_height, 
                        Qt.AlignCenter, f"{self.progress}%")
        
        # 7. 狀態訊息
        message_font = QFont("Arial", 9)
        painter.setFont(message_font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(0, progress_y - 20, self.width, 20, Qt.AlignCenter, self.message)
        
        # 8. 版本
        version_font = QFont("Arial", 8)
        painter.setFont(version_font)
        painter.setPen(QColor(120, 120, 120))
        painter.drawText(10, self.height - 15, 200, 20, Qt.AlignLeft, f"v{self.version}")


# ========================================
# 工廠函數 - 創建指定版本的預載畫面
# ========================================
def create_splash_screen(version: int = 1, logo_path: Optional[str] = None) -> BaseSplashScreen:
    """
    創建預載畫面
    
    Args:
        version: 版本號 (1-5)
            1: 經典賽車風格 (F1 Red Racing)
            2: 現代極簡風格 (Minimal Light - 白底黑字)
            3: 科技未來風格 (Cyber Tech)
            4: 優雅專業風格 (Professional)
            5: 動態賽道風格 (Dynamic Track)
        logo_path: Logo 圖片路徑，None 則使用預設路徑
    
    Returns:
        BaseSplashScreen: 預載畫面實例
    """
    if logo_path is None:
        # 自動尋找 logo.png - 支援 EXE 模式
        logo_path = str(get_resource_path(Path("image") / "logo.png"))
    
    splash_classes = {
        1: SplashScreenV1_Racing,
        2: SplashScreenV2_Minimal,
        3: SplashScreenV3_Cyber,
        4: SplashScreenV4_Professional,
        5: SplashScreenV5_Track,
    }
    
    splash_class = splash_classes.get(version, SplashScreenV1_Racing)
    return splash_class(logo_path)


# ========================================
# 使用範例
# ========================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    logger.info("=" * 60)
    logger.info("F1T 預載畫面示範 - 5 種風格版本")
    logger.info("=" * 60)
    logger.info("可用版本:")
    logger.info("  1. 經典賽車風格 (F1 Red Racing)")
    logger.info("  2. 現代極簡風格 (Minimal Light - 白底黑字)")
    logger.info("  3. 科技未來風格 (Cyber Tech)")
    logger.info("  4. 優雅專業風格 (Professional)")
    logger.info("  5. 動態賽道風格 (Dynamic Track)")
    
    # 讓使用者選擇版本
    try:
        choice = input("請選擇版本 (1-5，直接按 Enter 使用版本 1): ").strip()
        version = int(choice) if choice else 1
        if version not in [1, 2, 3, 4, 5]:
            version = 1
    except ValueError:
        version = 1
    
    logger.info("正在啟動版本 %s...", version)
    
    app = QApplication(sys.argv)
    
    # 創建預載畫面
    splash = create_splash_screen(version)
    splash.show()
    
    # 模擬載入進度
    progress_steps = [
        (10, "正在初始化核心模組..."),
        (25, "正在載入 FastF1 引擎..."),
        (40, "正在連接 API 服務..."),
        (55, "正在載入賽季數據..."),
        (70, "正在初始化 GUI 組件..."),
        (85, "正在配置分析模組..."),
        (100, "啟動完成！"),
    ]
    
    def update_progress():
        if not hasattr(update_progress, 'index'):
            update_progress.index = 0
        
        if update_progress.index < len(progress_steps):
            progress, message = progress_steps[update_progress.index]
            splash.set_progress(progress, message)
            update_progress.index += 1
        else:
            timer.stop()
            splash.finish(splash)  # 3 秒後自動關閉
            
            # 顯示完成訊息
            logger.info("✅ 預載畫面示範完成！")
            logger.info("使用的版本: %s", version)
            QTimer.singleShot(1000, app.quit)
    
    # 使用定時器模擬進度更新
    timer = QTimer()
    timer.timeout.connect(update_progress)
    timer.start(500)  # 每 500ms 更新一次
    
    sys.exit(app.exec_())
