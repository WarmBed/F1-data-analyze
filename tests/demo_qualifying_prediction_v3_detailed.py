#!/usr/bin/env python3
"""
排位賽預測 GUI Demo - V3 詳細版
Qualifying Prediction Demo - Detailed Version

詳細版本，10 欄：排名、車手、車隊、FP3、預測時間、△FP3、信賴度、R²、MAE、樣本數
適合深入分析

Author: F1T Team
Date: 2025-11-05
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox,
    QPushButton, QGroupBox, QProgressBar, QAbstractItemView,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen


class DetailedConfidenceDelegate(QStyledItemDelegate):
    """詳細信賴度委託（顯示 R² 值 + 進度條）"""
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        r2_value = index.data(Qt.UserRole)
        
        if r2_value is None:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 背景
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QBrush(QColor(35, 35, 35)))
        
        # 計算進度條
        base_x = option.rect.x() + 5
        base_y = option.rect.y() + 8
        bar_width = option.rect.width() - 10
        bar_height = 16
        
        # 進度條背景
        bg_rect = QRectF(base_x, base_y, bar_width, bar_height)
        painter.fillRect(bg_rect, QBrush(QColor(25, 25, 25)))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawRect(bg_rect)
        
        # 進度條填充
        fill_width = bar_width * r2_value
        fill_rect = QRectF(base_x, base_y, fill_width, bar_height)
        
        # 根據 R² 值選擇顏色
        if r2_value >= 0.90:
            color = QColor(0, 200, 0)  # 綠色
        elif r2_value >= 0.85:
            color = QColor(100, 200, 100)  # 淺綠
        elif r2_value >= 0.75:
            color = QColor(255, 200, 0)  # 黃色
        else:
            color = QColor(255, 100, 0)  # 橙色
        
        painter.fillRect(fill_rect, QBrush(color))
        
        # 繪製 R² 數值
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.setPen(QPen(QColor(255, 255, 255)))
        text = f"R²={r2_value:.4f}"
        text_x = int(base_x + bar_width / 2 - 30)
        text_y = int(base_y + bar_height / 2 + 4)
        painter.drawText(text_x, text_y, text)
        
        painter.restore()


class QualifyingPredictionDetailedDemo(QMainWindow):
    """排位賽預測詳細 Demo"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 - 詳細版 (10 欄)")
        self.setGeometry(100, 100, 1400, 700)
        
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
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        main_layout.addWidget(self.status_label)
    
    def _create_control_panel(self) -> QGroupBox:
        group_box = QGroupBox("詳細預測參數")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("年份:"))
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2024", "2025"])
        self.year_combo.setCurrentText("2025")
        layout.addWidget(self.year_combo)
        
        layout.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems(["Austria", "Monza", "Spa", "Silverstone", "Monaco"])
        layout.addWidget(self.race_combo)
        
        layout.addStretch()
        
        self.predict_button = QPushButton("🔮 執行詳細預測")
        self.predict_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #388e3c;}
        """)
        layout.addWidget(self.predict_button)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        
        # 10 欄
        columns = ["排名", "車手", "車隊", "FP3 時間", "預測時間", "△ FP3", "信賴度", "R²", "MAE", "樣本數"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setRowHeight(0, 35)
        
        # 欄位寬度
        table.setColumnWidth(0, 50)   # 排名
        table.setColumnWidth(1, 70)   # 車手
        table.setColumnWidth(2, 140)  # 車隊
        table.setColumnWidth(3, 100)  # FP3
        table.setColumnWidth(4, 100)  # 預測時間
        table.setColumnWidth(5, 80)   # △ FP3
        table.setColumnWidth(6, 60)   # 信賴度
        table.setColumnWidth(7, 150)  # R²（使用委託）
        table.setColumnWidth(8, 80)   # MAE
        table.setColumnWidth(9, 80)   # 樣本數
        
        # 設置委託
        self.r2_delegate = DetailedConfidenceDelegate()
        table.setItemDelegateForColumn(7, self.r2_delegate)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        
        return table
    
    def _populate_table(self):
        predictions = self.mock_data["predictions"]
        self.table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            self.table.setRowHeight(row, 35)
            
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
            
            # 車隊
            team_item = QTableWidgetItem(pred["team"])
            team_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            team_item.setBackground(self._get_team_color(pred["team"]))
            self.table.setItem(row, 2, team_item)
            
            # FP3 時間
            fp3_item = QTableWidgetItem(self._format_time(pred["fp3_time"]))
            fp3_item.setTextAlignment(Qt.AlignCenter)
            fp3_item.setFont(QFont("Consolas", 9))
            self.table.setItem(row, 3, fp3_item)
            
            # 預測時間
            pred_item = QTableWidgetItem(self._format_time(pred["predicted_time"]))
            pred_item.setTextAlignment(Qt.AlignCenter)
            pred_item.setFont(QFont("Consolas", 10, QFont.Bold))
            pred_item.setForeground(QColor(100, 255, 100))  # 淺綠色
            self.table.setItem(row, 4, pred_item)
            
            # △ FP3
            improvement = pred["improvement"]
            delta_item = QTableWidgetItem(f"{improvement:+.3f}s")
            delta_item.setTextAlignment(Qt.AlignCenter)
            delta_item.setFont(QFont("Consolas", 9))
            delta_item.setBackground(self._get_improvement_color(improvement))
            self.table.setItem(row, 5, delta_item)
            
            # 信賴度（百分比）
            conf_item = QTableWidgetItem(f"{int(pred['confidence']*100)}%")
            conf_item.setTextAlignment(Qt.AlignCenter)
            conf_item.setFont(QFont("Arial", 9))
            self.table.setItem(row, 6, conf_item)
            
            # R²（使用委託）
            r2_item = QTableWidgetItem("")
            r2_item.setData(Qt.UserRole, pred["r2"])
            self.table.setItem(row, 7, r2_item)
            
            # MAE
            mae_item = QTableWidgetItem(f"{pred['mae']:.3f}s")
            mae_item.setTextAlignment(Qt.AlignCenter)
            mae_item.setFont(QFont("Arial", 9))
            self.table.setItem(row, 8, mae_item)
            
            # 樣本數
            sample_item = QTableWidgetItem(str(pred["samples"]))
            sample_item.setTextAlignment(Qt.AlignCenter)
            sample_item.setFont(QFont("Arial", 9))
            self.table.setItem(row, 9, sample_item)
        
        # 更新狀態
        metadata = self.mock_data["metadata"]
        self.status_label.setText(
            f"📊 模型: {metadata['model_version']} | "
            f"賽道: {metadata['track']} {metadata['year']} | "
            f"平均 R²: {metadata['avg_r2']:.4f} | "
            f"平均 MAE: {metadata['avg_mae']:.3f}s"
        )
    
    def _get_team_color(self, team: str) -> QColor:
        team_colors = {
            "Red Bull Racing": QColor(30, 65, 255),
            "Ferrari": QColor(220, 0, 0),
            "Mercedes": QColor(0, 210, 190),
            "McLaren": QColor(255, 135, 0),
            "Aston Martin": QColor(0, 111, 98),
        }
        return team_colors.get(team, QColor(100, 100, 100))
    
    def _get_improvement_color(self, improvement: float) -> QColor:
        if improvement <= -0.15:
            return QColor(0, 150, 0)
        elif improvement <= -0.10:
            return QColor(100, 200, 100)
        elif improvement <= -0.05:
            return QColor(255, 255, 100)
        else:
            return QColor(255, 150, 100)
    
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
                "avg_r2": 0.8856,
                "avg_mae": 2.612
            },
            "predictions": [
                {"rank": 1, "driver": "VER", "team": "Red Bull Racing", "fp3_time": 64.643, "predicted_time": 64.523, "improvement": -0.120, "confidence": 0.98, "r2": 0.9234, "mae": 1.823, "samples": 152},
                {"rank": 2, "driver": "LEC", "team": "Ferrari", "fp3_time": 64.869, "predicted_time": 64.689, "improvement": -0.180, "confidence": 0.95, "r2": 0.8956, "mae": 2.145, "samples": 148},
                {"rank": 3, "driver": "NOR", "team": "McLaren", "fp3_time": 64.862, "predicted_time": 64.712, "improvement": -0.150, "confidence": 0.92, "r2": 0.8845, "mae": 2.567, "samples": 145},
                {"rank": 4, "driver": "SAI", "team": "Ferrari", "fp3_time": 65.011, "predicted_time": 64.801, "improvement": -0.210, "confidence": 0.91, "r2": 0.8723, "mae": 2.789, "samples": 143},
                {"rank": 5, "driver": "PIA", "team": "McLaren", "fp3_time": 65.004, "predicted_time": 64.834, "improvement": -0.170, "confidence": 0.89, "r2": 0.8612, "mae": 2.934, "samples": 141},
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
    
    window = QualifyingPredictionDetailedDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
