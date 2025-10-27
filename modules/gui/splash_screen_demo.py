#!/usr/bin/env python3
"""
F1T 預載畫面示範程式
展示所有 5 種風格的預載畫面
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.gui.splash_screen import create_splash_screen


class SplashDemoDialog(QDialog):
    """預載畫面選擇對話框"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1T 預載畫面示範")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("請選擇要預覽的預載畫面風格")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 版本按鈕
        styles = [
            ("版本 1: 經典賽車風格 (F1 Red Racing)", 1, "#DC2626"),
            ("版本 2: 現代極簡風格 (Minimal Light - 白底黑字)", 2, "#3B82F6"),
            ("版本 3: 科技未來風格 (Cyber Tech)", 3, "#00FFCC"),
            ("版本 4: 優雅專業風格 (Professional)", 4, "#4682B4"),
            ("版本 5: 動態賽道風格 (Dynamic Track)", 5, "#FF4646"),
        ]
        
        for label, version, color in styles:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 12px;
                    font-size: 11px;
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: {color}DD;
                }}
            """)
            btn.clicked.connect(lambda checked, v=version: self.show_splash(v))
            layout.addWidget(btn)
        
        # 說明
        info = QLabel("\n點擊按鈕查看對應風格的預載畫面\n預載畫面將自動模擬載入進度")
        info.setStyleSheet("color: gray; font-size: 9px; padding: 5px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
    
    def show_splash(self, version: int):
        """顯示指定版本的預載畫面"""
        print(f"\n{'='*60}")
        print(f"展示版本 {version} 的預載畫面")
        print(f"{'='*60}\n")
        
        # 創建預載畫面
        splash = create_splash_screen(version)
        splash.show()
        
        # 模擬載入進度
        progress_steps = [
            (10, "Initializing core modules..."),
            (25, "Loading FastF1 engine..."),
            (40, "Connecting to API service..."),
            (55, "Loading season data..."),
            (70, "Initializing GUI components..."),
            (85, "Configuring analysis modules..."),
            (100, "Startup complete!"),
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
                # 3 秒後關閉
                QTimer.singleShot(3000, lambda: splash.close())
                print(f"✅ 版本 {version} 預載畫面示範完成\n")
        
        # 進度定時器
        timer = QTimer()
        timer.timeout.connect(update_progress)
        timer.start(600)  # 每 600ms 更新


def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 顯示選擇對話框
    dialog = SplashDemoDialog()
    dialog.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    print("=" * 60)
    print("F1T 預載畫面示範程式")
    print("=" * 60)
    print("\n提供 5 種不同風格的預載畫面:")
    print("  1. 經典賽車風格 - F1 紅色主題，充滿速度感")
    print("  2. 現代極簡風格 - 白底黑字，清新簡約")
    print("  3. 科技未來風格 - 霓虹藍綠，賽博龐克")
    print("  4. 優雅專業風格 - 深藍商務，企業級質感")
    print("  5. 動態賽道風格 - 賽道動畫，方格旗配色")
    print("\n正在啟動選擇介面...\n")
    
    main()
