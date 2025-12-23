#!/usr/bin/env python3
"""
F101 起跑反應分析 - 獨立 GUI 測試
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt

from modules.gui.race_analysis.start_reaction.start_reaction_widget import StartReactionWidget
from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader


class StartReactionTestWindow(QMainWindow):
    """起跑反應分析測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F101 起跑反應分析 - 測試")
        self.setGeometry(100, 100, 1400, 900)
        
        # 主 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 標題
        title = QLabel("<h1>F101 起跑反應分析</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 載入按鈕
        load_btn = QPushButton("載入 Abu Dhabi 2025 Race 數據")
        load_btn.clicked.connect(self.load_data)
        layout.addWidget(load_btn)
        
        # 起跑反應 Widget
        self.reaction_widget = StartReactionWidget()
        layout.addWidget(self.reaction_widget)
        
        print("[TEST GUI] 啟動完成")
    
    def load_data(self):
        """載入數據"""
        print("\n[TEST GUI] 開始載入數據...")
        
        loader = StartReactionDataLoader(2025, 'Abu_Dhabi', 'R')
        data = loader.load_data()
        
        if data:
            print(f"[TEST GUI] 載入成功: {len(data['drivers'])} 位車手")
            print(f"[TEST GUI] Reaction batch time: {data.get('reaction_batch_time', 0):.3f}s")
            
            self.reaction_widget.update_data(data)
            print("[TEST GUI] Widget 更新完成")
        else:
            print("[TEST GUI] 載入失敗")


def main():
    app = QApplication(sys.argv)
    
    # 設置應用程式資訊
    app.setApplicationName("F101 起跑反應分析")
    app.setOrganizationName("F1T Team")
    
    window = StartReactionTestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
