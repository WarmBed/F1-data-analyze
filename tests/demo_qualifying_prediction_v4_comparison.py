#!/usr/bin/env python3
"""
排位賽預測 GUI Demo - V4 對比版
Qualifying Prediction Demo - Comparison Version

對比版本，顯示多個模型（v3.7 vs v3.8）的預測結果
8 欄：排名、車手、v3.7 預測、v3.8 預測、差異、FP3、實際 Q、準確度

Author: F1T Team
Date: 2025-11-05
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox,
    QPushButton, QGroupBox, QAbstractItemView, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class QualifyingPredictionComparisonDemo(QMainWindow):
    """排位賽預測對比 Demo"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 - 模型對比版 (v3.7 vs v3.8)")
        self.setGeometry(100, 100, 1300, 700)
        
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
        
        # 統計面板
        stats_panel = self._create_stats_panel()
        main_layout.addWidget(stats_panel)
    
    def _create_control_panel(self) -> QGroupBox:
        group_box = QGroupBox("模型對比參數")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems(["Austria 2024 (已完賽)", "Monza 2024 (已完賽)", "Spa 2024 (已完賽)"])
        layout.addWidget(self.race_combo)
        
        # 顯示選項
        self.show_v37 = QCheckBox("顯示 v3.7")
        self.show_v37.setChecked(True)
        layout.addWidget(self.show_v37)
        
        self.show_v38 = QCheckBox("顯示 v3.8")
        self.show_v38.setChecked(True)
        layout.addWidget(self.show_v38)
        
        self.show_actual = QCheckBox("顯示實際結果")
        self.show_actual.setChecked(True)
        layout.addWidget(self.show_actual)
        
        layout.addStretch()
        
        self.compare_button = QPushButton("📊 執行對比")
        self.compare_button.setStyleSheet("""
            QPushButton {
                background-color: #e65100;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #f57c00;}
        """)
        layout.addWidget(self.compare_button)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        
        # 8 欄
        columns = ["排名", "車手", "v3.7 預測", "v3.8 預測", "模型差異", "FP3 時間", "實際 Q", "v3.8 準確度"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # 欄位寬度
        table.setColumnWidth(0, 50)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 110)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 110)
        table.setColumnWidth(6, 110)
        table.setColumnWidth(7, 100)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStretchLastSection(True)
        
        return table
    
    def _populate_table(self):
        predictions = self.mock_data["predictions"]
        self.table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            # 排名
            rank_item = QTableWidgetItem(str(pred["rank"]))
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table.setItem(row, 0, rank_item)
            
            # 車手
            driver_item = QTableWidgetItem(pred["driver"])
            driver_item.setTextAlignment(Qt.AlignCenter)
            driver_item.setFont(QFont("Consolas", 10, QFont.Bold))
            self.table.setItem(row, 1, driver_item)
            
            # v3.7 預測
            v37_item = QTableWidgetItem(self._format_time(pred["v37_pred"]))
            v37_item.setTextAlignment(Qt.AlignCenter)
            v37_item.setFont(QFont("Consolas", 9))
            v37_item.setForeground(QColor(150, 150, 200))  # 淺紫
            self.table.setItem(row, 2, v37_item)
            
            # v3.8 預測
            v38_item = QTableWidgetItem(self._format_time(pred["v38_pred"]))
            v38_item.setTextAlignment(Qt.AlignCenter)
            v38_item.setFont(QFont("Consolas", 9, QFont.Bold))
            v38_item.setForeground(QColor(100, 255, 100))  # 淺綠
            self.table.setItem(row, 3, v38_item)
            
            # 模型差異
            diff = pred["v38_pred"] - pred["v37_pred"]
            diff_item = QTableWidgetItem(f"{diff:+.3f}s")
            diff_item.setTextAlignment(Qt.AlignCenter)
            diff_item.setFont(QFont("Consolas", 9))
            if diff < 0:
                diff_item.setBackground(QColor(0, 100, 0))  # v3.8 更快（改進）
                diff_item.setForeground(QColor(255, 255, 255))
            else:
                diff_item.setBackground(QColor(100, 100, 100))
            self.table.setItem(row, 4, diff_item)
            
            # FP3 時間
            fp3_item = QTableWidgetItem(self._format_time(pred["fp3_time"]))
            fp3_item.setTextAlignment(Qt.AlignCenter)
            fp3_item.setFont(QFont("Consolas", 9))
            self.table.setItem(row, 5, fp3_item)
            
            # 實際 Q
            actual_item = QTableWidgetItem(self._format_time(pred["actual_q"]))
            actual_item.setTextAlignment(Qt.AlignCenter)
            actual_item.setFont(QFont("Consolas", 9, QFont.Bold))
            actual_item.setForeground(QColor(255, 215, 0))  # 金色
            self.table.setItem(row, 6, actual_item)
            
            # v3.8 準確度
            error = abs(pred["v38_pred"] - pred["actual_q"])
            accuracy_item = QTableWidgetItem(f"±{error:.3f}s")
            accuracy_item.setTextAlignment(Qt.AlignCenter)
            accuracy_item.setFont(QFont("Consolas", 9))
            accuracy_item.setBackground(self._get_accuracy_color(error))
            self.table.setItem(row, 7, accuracy_item)
    
    def _create_stats_panel(self) -> QGroupBox:
        group_box = QGroupBox("📊 對比統計")
        layout = QHBoxLayout()
        
        # v3.7 統計
        self.v37_label = QLabel()
        self.v37_label.setStyleSheet("color: #9999cc; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.v37_label)
        
        layout.addWidget(QLabel("|"))
        
        # v3.8 統計
        self.v38_label = QLabel()
        self.v38_label.setStyleSheet("color: #66ff66; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.v38_label)
        
        layout.addWidget(QLabel("|"))
        
        # 改進
        self.improvement_label = QLabel()
        self.improvement_label.setStyleSheet("color: #ffcc00; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.improvement_label)
        
        layout.addStretch()
        
        group_box.setLayout(layout)
        
        # 更新統計
        metadata = self.mock_data["metadata"]
        self.v37_label.setText(f"v3.7 MAE: {metadata['v37_mae']:.3f}s | R²: {metadata['v37_r2']:.4f}")
        self.v38_label.setText(f"v3.8 MAE: {metadata['v38_mae']:.3f}s | R²: {metadata['v38_r2']:.4f}")
        improvement = ((metadata['v37_mae'] - metadata['v38_mae']) / metadata['v37_mae']) * 100
        self.improvement_label.setText(f"改進: {improvement:.1f}% ⬆")
        
        return group_box
    
    def _get_accuracy_color(self, error: float) -> QColor:
        if error < 0.1:
            return QColor(0, 150, 0)  # 綠色（極準）
        elif error < 0.2:
            return QColor(100, 200, 100)  # 淺綠
        elif error < 0.3:
            return QColor(255, 255, 100)  # 黃色
        else:
            return QColor(255, 150, 100)  # 橙色
    
    def _format_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _generate_mock_data(self) -> dict:
        return {
            "metadata": {
                "v37_mae": 2.847,
                "v37_r2": 0.8612,
                "v38_mae": 2.534,
                "v38_r2": 0.8923,
                "track": "Austria 2024"
            },
            "predictions": [
                {"rank": 1, "driver": "VER", "v37_pred": 64.643, "v38_pred": 64.523, "fp3_time": 64.643, "actual_q": 64.512},
                {"rank": 2, "driver": "LEC", "v37_pred": 64.823, "v38_pred": 64.689, "fp3_time": 64.869, "actual_q": 64.701},
                {"rank": 3, "driver": "NOR", "v37_pred": 64.867, "v38_pred": 64.712, "fp3_time": 64.862, "actual_q": 64.723},
                {"rank": 4, "driver": "SAI", "v37_pred": 65.012, "v38_pred": 64.801, "fp3_time": 65.011, "actual_q": 64.834},
                {"rank": 5, "driver": "PIA", "v37_pred": 65.023, "v38_pred": 64.834, "fp3_time": 65.004, "actual_q": 64.856},
                {"rank": 6, "driver": "HAM", "v37_pred": 65.145, "v38_pred": 64.923, "fp3_time": 65.063, "actual_q": 64.945},
                {"rank": 7, "driver": "RUS", "v37_pred": 65.234, "v38_pred": 64.991, "fp3_time": 65.181, "actual_q": 65.012},
            ]
        }


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
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
    
    window = QualifyingPredictionComparisonDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
