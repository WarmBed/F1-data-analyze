#!/usr/bin/env python3
"""
🏎️ F1 車手名次分析 GUI - 5 個方案啟動器

快速啟動各個 Demo 方案進行比較

使用方法：
    python demo_position_launcher.py [A|B|C|D|E]
    
    或直接運行顯示選擇介面
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QFont, QTextCursor


class DemoLauncher(QMainWindow):
    """Demo 方案選擇啟動器"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏎️ F1 車手名次分析 GUI - 方案選擇器")
        self.setGeometry(100, 100, 900, 700)
        
        self.processes = {}  # 儲存啟動的進程
        
        self._init_ui()
        self._check_data_file()
    
    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title = QLabel("🏎️ F1 車手名次分析 GUI")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #e10600;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("選擇一個方案啟動 Demo 進行測試")
        subtitle.setStyleSheet("font-size: 12pt; color: #666;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # 方案按鈕區域
        self._add_option_buttons(layout)
        
        # 說明文字區域
        self._add_description_area(layout)
        
        # 狀態列
        self.status_label = QLabel("✅ 就緒")
        self.status_label.setStyleSheet("""
            font-size: 11pt;
            padding: 8px;
            background: #e9ecef;
            border-radius: 5px;
        """)
        layout.addWidget(self.status_label)
    
    def _add_option_buttons(self, layout):
        """添加方案選擇按鈕"""
        options = [
            ("A", "雙 Tab 視圖", "表格 + 圖表，完全複製 all_drivers_speed 架構", "#007bff"),
            ("B", "單一圖表視圖", "簡化版，專注於視覺化，3 種圖表模式", "#28a745"),
            ("C", "表格優先 + 彈出圖表", "主視圖是表格，點擊按鈕彈出圖表", "#17a2b8"),
            ("D", "垂直分割視圖", "表格 + 圖表並排，QSplitter 可調整比例", "#ffc107"),
            ("E", "互動式圖表 + 懸浮詳情", "點擊長條顯示詳情，支援篩選功能", "#dc3545"),
        ]
        
        for option_id, title, desc, color in options:
            btn_layout = QHBoxLayout()
            
            # 主按鈕
            btn = QPushButton(f"🚀 啟動方案 {option_id}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color)};
                }}
            """)
            btn.setMinimumHeight(80)
            btn.clicked.connect(lambda checked, opt=option_id: self._launch_demo(opt))
            
            # 說明標籤
            desc_label = QLabel(f"<b>{title}</b><br/>{desc}")
            desc_label.setStyleSheet("font-size: 10pt; padding: 10px;")
            desc_label.setWordWrap(True)
            
            btn_layout.addWidget(btn, stretch=2)
            btn_layout.addWidget(desc_label, stretch=3)
            
            layout.addLayout(btn_layout)
    
    def _add_description_area(self, layout):
        """添加詳細說明區域"""
        desc_group = QLabel("📖 方案對比說明")
        desc_group.setStyleSheet("font-size: 13pt; font-weight: bold; margin-top: 10px;")
        layout.addWidget(desc_group)
        
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(150)
        desc_text.setStyleSheet("font-size: 10pt; background: #f8f9fa;")
        
        desc_content = """
方案 A（推薦）：完全複製 all_drivers_speed 模組架構，雙 Tab 切換，延遲載入 Matplotlib
方案 B：簡化版，只有圖表，提供 3 種視圖（最終名次、名次變化、起始vs最終對比）
方案 C：表格為主，需要時點擊按鈕彈出獨立圖表視窗
方案 D：表格和圖表同時顯示，使用 QSplitter 可拖動調整比例
方案 E：互動性最強，點擊圖表長條顯示車手詳情，支援進步/退步車手篩選

✅ 所有方案都使用真實的 2024 日本 GP 數據
✅ 所有方案都整合車隊配色系統
✅ 所有方案都支援基本的互動功能
        """
        desc_text.setPlainText(desc_content.strip())
        layout.addWidget(desc_text)
    
    def _darken_color(self, color: str) -> str:
        """將顏色變暗（用於 hover 效果）"""
        color_map = {
            "#007bff": "#0056b3",
            "#28a745": "#1e7e34",
            "#17a2b8": "#117a8b",
            "#ffc107": "#d39e00",
            "#dc3545": "#bd2130",
        }
        return color_map.get(color, color)
    
    def _check_data_file(self):
        """檢查數據檔案是否存在"""
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if not json_path.exists():
            QMessageBox.critical(
                self,
                "❌ 錯誤",
                f"找不到數據檔案：\n{json_path}\n\n"
                "請先執行 CLI 生成數據：\n"
                "python f1_analysis_modular_main.py -f 25 -y 2024 -r Japan -s R"
            )
            self.status_label.setText("❌ 缺少數據檔案")
            self.status_label.setStyleSheet("""
                font-size: 11pt;
                padding: 8px;
                background: #f8d7da;
                color: #721c24;
                border-radius: 5px;
            """)
        else:
            self.status_label.setText(f"✅ 數據檔案已就緒：{json_path.name}")
    
    def _launch_demo(self, option: str):
        """啟動指定的 Demo"""
        script_name = f"demo_position_option_{option.lower()}.py"
        script_path = Path(script_name)
        
        if not script_path.exists():
            QMessageBox.critical(self, "錯誤", f"找不到 Demo 腳本：{script_name}")
            return
        
        print(f"[LAUNCHER] 啟動方案 {option}：{script_name}")
        
        # 使用 QProcess 啟動外部進程
        process = QProcess(self)
        process.start("python", [script_name])
        
        if process.waitForStarted():
            self.processes[option] = process
            self.status_label.setText(f"🚀 方案 {option} 已啟動")
            self.status_label.setStyleSheet("""
                font-size: 11pt;
                padding: 8px;
                background: #d4edda;
                color: #155724;
                border-radius: 5px;
            """)
            
            QMessageBox.information(
                self,
                "✅ 啟動成功",
                f"方案 {option} Demo 已啟動！\n\n"
                "關閉 Demo 視窗後可繼續測試其他方案。"
            )
        else:
            QMessageBox.critical(self, "錯誤", f"無法啟動方案 {option}")
    
    def closeEvent(self, event):
        """關閉時清理所有進程"""
        for option, process in self.processes.items():
            if process.state() == QProcess.Running:
                print(f"[LAUNCHER] 終止方案 {option} 進程")
                process.terminate()
                process.waitForFinished(3000)
        
        event.accept()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 命令列參數啟動特定方案
    if len(sys.argv) > 1:
        option = sys.argv[1].upper()
        if option in ['A', 'B', 'C', 'D', 'E']:
            script_name = f"demo_position_option_{option.lower()}.py"
            print(f"[LAUNCHER] 直接啟動方案 {option}")
            
            import subprocess
            subprocess.run([sys.executable, script_name])
            return
        else:
            print(f"錯誤：無效的方案代號 '{option}'")
            print("有效選項：A, B, C, D, E")
            return
    
    # 啟動選擇器 GUI
    launcher = DemoLauncher()
    launcher.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
