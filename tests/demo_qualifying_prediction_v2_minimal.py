#!/usr/bin/env python3
"""
排位賽預測 GUI Demo - V2 極簡版
Qualifying Prediction Demo - Minimal Version

極簡設計，僅 4 欄：排名、車手、預測時間、信賴度
適合快速查看預測結果

Author: F1T Team
Date: 2025-11-05
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox,
    QPushButton, QGroupBox, QProgressBar, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class MinimalConfidenceBar(QProgressBar):
    """極簡信賴度進度條"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setMaximum(100)
        self.setMinimum(0)
        self.setFixedHeight(18)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 2px;
                text-align: center;
                background-color: #1e1e1e;
                color: white;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 1px;
            }
        """)
    
    def set_confidence(self, confidence: float):
        percentage = int(confidence * 100)
        self.setValue(percentage)
        self.setFormat(f"{percentage}%")


class QualifyingPredictionMinimalDemo(QMainWindow):
    """排位賽預測極簡 Demo"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 - 極簡版 (4 欄)")
        self.setGeometry(100, 100, 800, 600)
        
        self.mock_data = self._generate_mock_data()
        self._init_ui()
        self._populate_table()
    
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 表格
        self.table = self._create_table()
        main_layout.addWidget(self.table)
        
        # 狀態欄
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #888; font-size: 10px;")
        main_layout.addWidget(self.status_label)
    
    def _create_control_panel(self) -> QGroupBox:
        group_box = QGroupBox("預測參數")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems(["Austria", "Monza", "Spa", "Monaco"])
        layout.addWidget(self.race_combo)
        
        layout.addStretch()
        
        self.predict_button = QPushButton("🔮 執行預測")
        self.predict_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {background-color: #5a9ff2;}
        """)
        layout.addWidget(self.predict_button)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        
        # 僅 4 欄
        columns = ["排名", "車手", "預測時間", "信賴度"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # 欄位寬度
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 150)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStretchLastSection(True)
        
        return table
    
    def _populate_table(self):
        predictions = self.mock_data["predictions"][:10]  # 僅顯示前 10 名
        self.table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            # 排名
            rank_item = QTableWidgetItem(str(pred["rank"]))
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFont(QFont("Arial", 11, QFont.Bold))
            if pred["rank"] <= 3:
                rank_item.setForeground(QColor(255, 215, 0))  # 金色
            self.table.setItem(row, 0, rank_item)
            
            # 車手
            driver_item = QTableWidgetItem(pred["driver"])
            driver_item.setTextAlignment(Qt.AlignCenter)
            driver_item.setFont(QFont("Consolas", 11, QFont.Bold))
            self.table.setItem(row, 1, driver_item)
            
            # 預測時間
            time_item = QTableWidgetItem(self._format_time(pred["predicted_time"]))
            time_item.setTextAlignment(Qt.AlignCenter)
            time_item.setFont(QFont("Consolas", 11))
            self.table.setItem(row, 2, time_item)
            
            # 信賴度
            confidence_bar = MinimalConfidenceBar()
            confidence_bar.set_confidence(pred["confidence"])
            self.table.setCellWidget(row, 3, confidence_bar)
        
        # 更新狀態
        metadata = self.mock_data["metadata"]
        self.status_label.setText(
            f"📊 模型: {metadata['model_version']} | "
            f"R²: {metadata['model_r2']:.4f} | "
            f"賽道: {metadata['track']} 2025"
        )
    
    def _format_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _generate_mock_data(self) -> dict:
        return {
            "metadata": {
                "model_version": "v3.8",
                "track": "Austria",
                "year": 2025,
                "model_r2": 0.8923,
            },
            "predictions": [
                {"rank": 1, "driver": "VER", "predicted_time": 64.523, "confidence": 0.98},
                {"rank": 2, "driver": "LEC", "predicted_time": 64.689, "confidence": 0.95},
                {"rank": 3, "driver": "NOR", "predicted_time": 64.712, "confidence": 0.92},
                {"rank": 4, "driver": "SAI", "predicted_time": 64.801, "confidence": 0.91},
                {"rank": 5, "driver": "PIA", "predicted_time": 64.834, "confidence": 0.89},
                {"rank": 6, "driver": "HAM", "predicted_time": 64.923, "confidence": 0.85},
                {"rank": 7, "driver": "RUS", "predicted_time": 64.991, "confidence": 0.84},
                {"rank": 8, "driver": "PER", "predicted_time": 65.045, "confidence": 0.82},
                {"rank": 9, "driver": "ALO", "predicted_time": 65.189, "confidence": 0.78},
                {"rank": 10, "driver": "STR", "predicted_time": 65.267, "confidence": 0.75},
            ]
        }


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 深色主題
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    app.setPalette(palette)
    
    window = QualifyingPredictionMinimalDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
