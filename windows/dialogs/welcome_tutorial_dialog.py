# -*- coding: utf-8 -*-
"""
Welcome Tutorial Dialog - 首次啟動教學視窗

在用戶首次啟動應用程式時顯示教學引導，包含 GIF 動畫和說明文字。
提供「不再顯示」選項，保存用戶偏好設定。
"""

import json
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QSize, QTimer, QUrl
from PyQt5.QtGui import QMovie, QFont, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QPushButton, QWidget, QScrollArea,
    QFrame, QStackedWidget, QSizePolicy
)

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger(__name__)

# 用戶偏好設定檔案路徑
USER_PREFERENCES_FILE = Path.home() / ".f1t" / "user_preferences.json"


class TutorialPage(QWidget):
    """單頁教學內容"""
    
    def __init__(self, title: str, description: str, gif_path: Optional[str] = None, 
                 image_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._setup_ui(title, description, gif_path, image_path)
        
    def _setup_ui(self, title: str, description: str, gif_path: Optional[str], 
                  image_path: Optional[str]):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #E10600;")  # F1 紅色
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # GIF 或圖片區域
        media_container = QFrame()
        media_container.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
        """)
        media_layout = QVBoxLayout(media_container)
        media_layout.setContentsMargins(10, 10, 10, 10)
        
        self._media_label = QLabel()
        self._media_label.setAlignment(Qt.AlignCenter)
        self._media_label.setMinimumSize(600, 350)
        self._media_label.setMaximumSize(800, 450)
        self._media_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._movie = None
        
        if gif_path and Path(gif_path).exists():
            # 載入 GIF 動畫
            self._movie = QMovie(gif_path)
            self._movie.setScaledSize(QSize(600, 350))
            # 設定兩倍速播放
            self._movie.setSpeed(200)  # 200% = 2x speed
            self._media_label.setMovie(self._movie)
            self._movie.start()
            logger.debug(f"[TUTORIAL] Loaded GIF: {gif_path}")
        elif image_path and Path(image_path).exists():
            # 載入靜態圖片
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(600, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._media_label.setPixmap(scaled_pixmap)
            logger.debug(f"[TUTORIAL] Loaded image: {image_path}")
        else:
            # 顯示佔位符
            self._media_label.setText("🎬")
            self._media_label.setStyleSheet("font-size: 72px; color: #666;")
            
        media_layout.addWidget(self._media_label)
        layout.addWidget(media_container)
        
        # 說明文字
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 11))
        desc_label.setStyleSheet("color: #333; line-height: 1.5;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
    def stop_animation(self):
        """停止 GIF 動畫"""
        if self._movie:
            self._movie.stop()


class WelcomeTutorialDialog(QDialog):
    """
    歡迎教學對話框
    
    顯示多頁教學內容，包含 GIF 動畫和說明文字。
    提供「不再顯示」選項。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("welcome_tutorial_title", "Welcome to PIT WALL"))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setMinimumSize(750, 650)
        self.resize(800, 700)
        
        self._current_page = 0
        self._pages = []
        
        self._setup_ui()
        self._setup_pages()
        self._apply_styles()
        
        logger.info("[TUTORIAL] Welcome tutorial dialog initialized")
        
    def _setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 頂部 Logo 區域
        header_layout = QHBoxLayout()
        
        title_label = QLabel("PIT WALL")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: #1a1a1a;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 頁碼指示器
        self._page_indicator = QLabel("1 / 1")
        self._page_indicator.setFont(QFont("Segoe UI", 10))
        self._page_indicator.setStyleSheet("color: #666;")
        header_layout.addWidget(self._page_indicator)
        
        layout.addLayout(header_layout)
        
        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        layout.addWidget(line)
        
        # 教學內容區域 (使用 QStackedWidget 切換頁面)
        self._stacked_widget = QStackedWidget()
        layout.addWidget(self._stacked_widget, 1)
        
        # 底部控制區域
        bottom_layout = QHBoxLayout()
        
        # 「不再顯示」勾選框
        self._dont_show_checkbox = QCheckBox(
            tr("dont_show_again", "Don't show this again")
        )
        self._dont_show_checkbox.setFont(QFont("Segoe UI", 10))
        self._dont_show_checkbox.setStyleSheet("color: #666;")
        bottom_layout.addWidget(self._dont_show_checkbox)
        
        bottom_layout.addStretch()
        
        # 上一頁按鈕
        self._prev_btn = QPushButton(tr("previous", "Previous"))
        self._prev_btn.setFont(QFont("Segoe UI", 10))
        self._prev_btn.setMinimumWidth(100)
        self._prev_btn.clicked.connect(self._go_previous)
        self._prev_btn.setEnabled(False)
        bottom_layout.addWidget(self._prev_btn)
        
        # 下一頁/完成按鈕
        self._next_btn = QPushButton(tr("next", "Next"))
        self._next_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._next_btn.setMinimumWidth(100)
        self._next_btn.clicked.connect(self._go_next)
        self._next_btn.setStyleSheet("""
            QPushButton {
                background-color: #E10600;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #ff1a1a;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
        """)
        bottom_layout.addWidget(self._next_btn)
        
        layout.addLayout(bottom_layout)
        
    def _setup_pages(self):
        """設置教學頁面"""
        # 取得資源路徑
        base_path = Path(__file__).parent.parent.parent / "resources" / "tutorials"
        image_folder = Path(__file__).parent.parent.parent / "image"
        
        # 定義教學頁面
        pages_config = [
            {
                "title": tr("tutorial_page1_title", "Welcome to PIT WALL"),
                "description": tr("tutorial_page1_desc", 
                    "PIT WALL is a professional F1 telemetry analysis tool.\n\n"
                    "You can open example workspaces from File > Load Workspace\n"
                    "to quickly explore the features.\n\n"
                    "Recommended: 27\" or larger monitor for best experience."
                ),
                "gif": str(image_folder / "workspace.gif"),
                "image": str(image_folder / "workspace.png"),
            },
            {
                "title": tr("tutorial_page2_title", "Select Year, Race, and Session"),
                "description": tr("tutorial_page2_desc",
                    "1. Use the dropdowns at the top to select Year, Race, and Session\n"
                    "2. The system will automatically fetch available races for the selected year\n"
                    "3. Sessions include: FP1, FP2, FP3, Q (Qualifying), R (Race)"
                ),
                "gif": str(image_folder / "selectyear.gif"),
                "image": str(image_folder / "selectyear.png"),
            },
            {
                "title": tr("tutorial_page3_title", "Open Analysis Modules"),
                "description": tr("tutorial_page3_desc",
                    "1. Click on items in the left function tree to open analysis modules\n"
                    "2. Each module opens in a new MDI window\n"
                    "3. You can arrange, resize, and tile windows as needed\n"
                    "4. Double-click a window title to maximize it"
                ),
                "gif": str(image_folder / "openanalysismodules.gif"),
                "image": str(image_folder / "openanalysismodules.png"),
            },
            {
                "title": tr("tutorial_page4_title", "Live Timing Features"),
                "description": tr("tutorial_page4_desc",
                    "1. Access Live Timing modules from the function tree\n"
                    "2. Load historical race data or connect to live sessions\n"
                    "3. Use the playback controls to replay races\n"
                    "4. F1TV Pro subscription required for live data"
                ),
                "gif": str(image_folder / "Livetimemodule.gif"),
                "image": str(image_folder / "Livetimemodule.png"),
            },
        ]
        
        for config in pages_config:
            page = TutorialPage(
                title=config["title"],
                description=config["description"],
                gif_path=config.get("gif"),
                image_path=config.get("image")
            )
            self._pages.append(page)
            self._stacked_widget.addWidget(page)
            
        self._update_navigation()
        
    def _apply_styles(self):
        """套用淺色主題樣式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #1a1a1a;
            }
            QCheckBox {
                color: #555555;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #ccc;
                background-color: #f5f5f5;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #E10600;
                background-color: #E10600;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #1a1a1a;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #aaa;
            }
        """)
        
    def _update_navigation(self):
        """更新導航按鈕狀態"""
        total_pages = len(self._pages)
        current = self._current_page + 1
        
        self._page_indicator.setText(f"{current} / {total_pages}")
        self._prev_btn.setEnabled(self._current_page > 0)
        
        if self._current_page >= total_pages - 1:
            self._next_btn.setText(tr("get_started", "Get Started"))
        else:
            self._next_btn.setText(tr("next", "Next"))
            
    def _go_previous(self):
        """上一頁"""
        if self._current_page > 0:
            self._current_page -= 1
            self._stacked_widget.setCurrentIndex(self._current_page)
            self._update_navigation()
            
    def _go_next(self):
        """下一頁或完成"""
        if self._current_page >= len(self._pages) - 1:
            # 最後一頁，關閉對話框
            self._finish()
        else:
            self._current_page += 1
            self._stacked_widget.setCurrentIndex(self._current_page)
            self._update_navigation()
            
    def _finish(self):
        """完成教學"""
        # 保存用戶偏好設定
        if self._dont_show_checkbox.isChecked():
            self._save_preference(show_tutorial=False)
            logger.info("[TUTORIAL] User chose not to show tutorial again")
        else:
            logger.info("[TUTORIAL] Tutorial completed, will show again next time")
            
        # 停止所有 GIF 動畫
        for page in self._pages:
            page.stop_animation()
            
        self.accept()
        
    def closeEvent(self, event):
        """關閉事件"""
        # 停止所有 GIF 動畫
        for page in self._pages:
            page.stop_animation()
        super().closeEvent(event)
        
    @staticmethod
    def _save_preference(show_tutorial: bool):
        """保存用戶偏好設定"""
        try:
            USER_PREFERENCES_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # 讀取現有設定
            preferences = {}
            if USER_PREFERENCES_FILE.exists():
                with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                    
            # 更新設定
            preferences['show_welcome_tutorial'] = show_tutorial
            
            # 保存設定
            with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
                
            logger.info(f"[TUTORIAL] Preferences saved to {USER_PREFERENCES_FILE}")
            
        except Exception as e:
            logger.error(f"[TUTORIAL] Failed to save preferences: {e}")
            
    @staticmethod
    def should_show_tutorial() -> bool:
        """檢查是否應該顯示教學"""
        try:
            if not USER_PREFERENCES_FILE.exists():
                return True  # 首次啟動
                
            with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
                
            return preferences.get('show_welcome_tutorial', True)
            
        except Exception as e:
            logger.error(f"[TUTORIAL] Failed to read preferences: {e}")
            return True  # 出錯時仍顯示教學
            
    @staticmethod
    def reset_tutorial_preference():
        """重置教學顯示設定（從選單中調用）"""
        WelcomeTutorialDialog._save_preference(show_tutorial=True)
        logger.info("[TUTORIAL] Tutorial preference reset, will show on next launch")


def show_welcome_tutorial_if_needed(parent=None) -> bool:
    """
    如果需要，顯示歡迎教學對話框
    
    Args:
        parent: 父視窗
        
    Returns:
        bool: 是否顯示了教學
    """
    if WelcomeTutorialDialog.should_show_tutorial():
        dialog = WelcomeTutorialDialog(parent)
        dialog.exec_()
        return True
    return False
