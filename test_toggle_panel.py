#!/usr/bin/env python3
"""
測試摺疊面板功能
"""
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget, QLabel, QToolButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt
import sys

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("測試摺疊功能")
        self.resize(1200, 600)
        
        # 中央 widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 主 splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.main_splitter)
        
        # 左側容器（包含面板和按鈕）
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # 左側面板
        self.left_panel = QWidget()
        self.left_panel.setMinimumWidth(350)
        self.left_panel.setMaximumWidth(420)
        self.left_panel.setStyleSheet("background-color: #f0f0f0;")
        left_panel_layout = QVBoxLayout(self.left_panel)
        left_panel_layout.addWidget(QLabel("這是左側參數面板\n可以摺疊/展開"))
        left_layout.addWidget(self.left_panel)
        
        # 摺疊按鈕
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("◀")
        self.toggle_btn.setFixedWidth(15)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
                background-color: #e0e0e0;
                border: none;
                border-left: 1px solid #ccc;
                font-size: 10px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_panel)
        self.toggle_btn.setToolTip("收起/展開面板 (Ctrl+B)")
        left_layout.addWidget(self.toggle_btn)
        
        # 右側面板
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #e0f0ff;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("這是右側結果區域"))
        
        # 添加到 splitter
        self.main_splitter.addWidget(left_container)
        self.main_splitter.addWidget(right_panel)
        
        # 設置比例
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        
        # 狀態
        self._panel_visible = True
        self._saved_width = 400
        
        # 顯示初始大小
        self.statusBar().showMessage(f"初始 sizes: {self.main_splitter.sizes()}")
    
    def _toggle_panel(self):
        """切換面板顯示/隱藏"""
        print(f"\n[TOGGLE] 開始切換，當前狀態: {'可見' if self._panel_visible else '隱藏'}")
        
        current_sizes = self.main_splitter.sizes()
        print(f"[TOGGLE] 當前 splitter sizes: {current_sizes}")
        
        if not current_sizes or len(current_sizes) < 2:
            print(f"[TOGGLE] ⚠️ Splitter 尚未初始化")
            self.statusBar().showMessage("⚠️ Splitter 尚未初始化")
            return
        
        if self._panel_visible:
            # 摺疊
            self._saved_width = current_sizes[0]
            print(f"[TOGGLE] 保存寬度: {self._saved_width}px")
            
            total_width = sum(current_sizes)
            new_sizes = [15, total_width - 15]
            self.main_splitter.setSizes(new_sizes)
            print(f"[TOGGLE] 設置新 sizes: {new_sizes}")
            print(f"[TOGGLE] 實際 sizes: {self.main_splitter.sizes()}")
            
            self.toggle_btn.setText("▶")
            self.toggle_btn.setToolTip("展開面板")
            self._panel_visible = False
            
            self.statusBar().showMessage(f"✅ 已摺疊 - sizes: {self.main_splitter.sizes()}")
            
        else:
            # 展開
            total_width = sum(current_sizes)
            restore_width = self._saved_width if self._saved_width > 0 else 400
            new_sizes = [restore_width, total_width - restore_width]
            self.main_splitter.setSizes(new_sizes)
            print(f"[TOGGLE] 設置新 sizes: {new_sizes}")
            print(f"[TOGGLE] 實際 sizes: {self.main_splitter.sizes()}")
            
            self.toggle_btn.setText("◀")
            self.toggle_btn.setToolTip("收起面板")
            self._panel_visible = True
            
            self.statusBar().showMessage(f"✅ 已展開 - sizes: {self.main_splitter.sizes()}")
        
        print(f"[TOGGLE] 完成\n")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    # 延遲顯示實際 sizes
    from PyQt5.QtCore import QTimer
    def show_sizes():
        sizes = window.main_splitter.sizes()
        print(f"視窗顯示後的 sizes: {sizes}")
        window.statusBar().showMessage(f"視窗顯示後 sizes: {sizes}")
    
    QTimer.singleShot(100, show_sizes)
    
    print("\n✅ 測試視窗已啟動")
    print("點擊右側的按鈕測試摺疊/展開功能\n")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
