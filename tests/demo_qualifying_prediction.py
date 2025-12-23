#!/usr/bin/env python3
"""
排位賽預測 GUI Demo
Qualifying Prediction GUI Demo

展示預測結果的表格介面，用於確認 UI 設計
使用模擬數據，不需要實際 API 或 CLI 調用

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


class ConfidenceProgressBar(QProgressBar):
    """信賴度進度條（類似 pitstop_analysis）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setMaximum(100)
        self.setMinimum(0)
        self.setFixedHeight(20)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:0.5 #ffff00, stop:1 #ff0000
                );
                border-radius: 2px;
            }
        """)
    
    def set_confidence(self, confidence: float):
        """設置信賴度（0.0 - 1.0）"""
        percentage = int(confidence * 100)
        self.setValue(percentage)
        self.setFormat(f"{percentage}%")


class QualifyingPredictionDemo(QMainWindow):
    """排位賽預測 Demo 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 GUI Demo - v3.8 模型")
        self.setGeometry(100, 100, 1200, 700)
        
        # 模擬數據
        self.mock_data = self._generate_mock_data()
        
        self._init_ui()
        self._populate_table()
    
    def _init_ui(self):
        """初始化 UI"""
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
        status_panel = self._create_status_panel()
        main_layout.addWidget(status_panel)
    
    def _create_control_panel(self) -> QGroupBox:
        """創建控制面板"""
        group_box = QGroupBox("預測參數")
        layout = QHBoxLayout()
        
        # 年份選擇
        layout.addWidget(QLabel("年份:"))
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2024", "2025"])
        self.year_combo.setCurrentText("2025")
        layout.addWidget(self.year_combo)
        
        # 賽事選擇
        layout.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems([
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
            "Miami", "Imola", "Monaco", "Canada", "Spain",
            "Austria", "Great Britain", "Hungary", "Belgium", "Netherlands",
            "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
            "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
        ])
        self.race_combo.setCurrentText("Austria")
        layout.addWidget(self.race_combo)
        
        # 會話類型
        layout.addWidget(QLabel("會話:"))
        self.session_combo = QComboBox()
        self.session_combo.addItems(["Q (排位賽)"])
        layout.addWidget(self.session_combo)
        
        layout.addStretch()
        
        # 預測按鈕
        self.predict_button = QPushButton("🔮 執行預測")
        self.predict_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.predict_button.clicked.connect(self._on_predict_clicked)
        layout.addWidget(self.predict_button)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_table(self) -> QTableWidget:
        """創建預測結果表格"""
        table = QTableWidget()
        
        # 設置欄位
        columns = ["排名", "車手", "車隊", "預測時間", "信賴度", "△ FP3"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 表格樣式
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # 欄位寬度
        table.setColumnWidth(0, 60)   # 排名
        table.setColumnWidth(1, 80)   # 車手
        table.setColumnWidth(2, 150)  # 車隊
        table.setColumnWidth(3, 120)  # 預測時間
        table.setColumnWidth(4, 200)  # 信賴度（進度條）
        table.setColumnWidth(5, 100)  # △ FP3
        
        # Header 樣式
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStretchLastSection(True)
        
        return table
    
    def _create_status_panel(self) -> QWidget:
        """創建狀態面板"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 模型資訊
        self.model_info_label = QLabel()
        self.model_info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.model_info_label)
        
        layout.addStretch()
        
        # 統計資訊
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.stats_label)
        
        widget.setLayout(layout)
        return widget
    
    def _populate_table(self):
        """填充表格數據"""
        predictions = self.mock_data["predictions"]
        metadata = self.mock_data["metadata"]
        
        self.table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            # 排名
            rank_item = self._create_rank_item(pred["rank"])
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
            
            # 預測時間
            time_item = QTableWidgetItem(self._format_time(pred["predicted_time"]))
            time_item.setTextAlignment(Qt.AlignCenter)
            time_item.setFont(QFont("Consolas", 10))
            self.table.setItem(row, 3, time_item)
            
            # 信賴度（進度條）
            confidence_bar = ConfidenceProgressBar()
            confidence_bar.set_confidence(pred["confidence"])
            self.table.setCellWidget(row, 4, confidence_bar)
            
            # △ FP3
            improvement_item = self._create_improvement_item(pred["improvement"])
            self.table.setItem(row, 5, improvement_item)
        
        # 更新狀態欄
        self._update_status_info(metadata)
    
    def _create_rank_item(self, rank: int) -> QTableWidgetItem:
        """創建排名單元格"""
        if rank == 1:
            text = "🥇 1"
        elif rank == 2:
            text = "🥈 2"
        elif rank == 3:
            text = "🥉 3"
        else:
            text = str(rank)
        
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFont(QFont("Arial", 10, QFont.Bold))
        return item
    
    def _create_improvement_item(self, improvement: float) -> QTableWidgetItem:
        """創建時間改善單元格（梯度顏色）"""
        # 格式化文字
        if improvement >= 0:
            text = f"+{improvement:.3f}s"
        else:
            text = f"{improvement:.3f}s"
        
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFont(QFont("Consolas", 9))
        
        # 梯度顏色（改善越多越綠）
        color = self._get_improvement_color(improvement)
        item.setBackground(color)
        
        # 文字顏色（深色背景用白字，淺色背景用黑字）
        if improvement < -0.15:
            item.setForeground(QColor(255, 255, 255))  # 白色
        else:
            item.setForeground(QColor(0, 0, 0))        # 黑色
        
        return item
    
    def _get_improvement_color(self, improvement: float) -> QColor:
        """
        根據改善幅度返回漸變顏色
        
        -0.21s → 深綠色 (最大改善)
        -0.15s → 淺綠色
        -0.10s → 黃色
        -0.05s → 橙色
        +0.00s → 紅色 (沒改善/退步)
        """
        if improvement <= -0.18:       # 深綠
            return QColor(0, 150, 0)
        elif improvement <= -0.15:     # 綠色
            return QColor(50, 200, 50)
        elif improvement <= -0.12:     # 淺綠
            return QColor(100, 255, 100)
        elif improvement <= -0.08:     # 黃綠
            return QColor(200, 255, 100)
        elif improvement <= -0.05:     # 黃色
            return QColor(255, 255, 100)
        elif improvement <= 0:         # 橙色
            return QColor(255, 200, 100)
        else:                          # 紅色
            return QColor(255, 100, 100)
    
    def _get_team_color(self, team: str) -> QColor:
        """返回車隊顏色"""
        team_colors = {
            "Red Bull Racing": QColor(30, 65, 255),
            "Ferrari": QColor(220, 0, 0),
            "Mercedes": QColor(0, 210, 190),
            "McLaren": QColor(255, 135, 0),
            "Aston Martin": QColor(0, 111, 98),
            "Alpine": QColor(255, 135, 188),
            "Williams": QColor(0, 82, 255),
            "RB": QColor(102, 146, 255),
            "Kick Sauber": QColor(0, 230, 0),
            "Haas": QColor(180, 180, 180)
        }
        return team_colors.get(team, QColor(100, 100, 100))
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間（秒 → MM:SS.SSS）"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _update_status_info(self, metadata: dict):
        """更新狀態欄資訊"""
        # 模型資訊
        model_text = (
            f"📊 模型: {metadata['model_version']} | "
            f"R²: {metadata['model_r2']:.4f} | "
            f"MAE: {metadata['model_mae']:.3f}s | "
            f"樣本數: {metadata['sample_count']}"
        )
        self.model_info_label.setText(model_text)
        
        # 統計資訊
        avg_improvement = metadata["avg_improvement"]
        stats_text = (
            f"平均改善: {avg_improvement:.3f}s | "
            f"前五車手時間差: {metadata['top5_gap']:.3f}s"
        )
        self.stats_label.setText(stats_text)
    
    def _on_predict_clicked(self):
        """執行預測按鈕點擊事件"""
        year = self.year_combo.currentText()
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        # 模擬：顯示載入狀態
        self.predict_button.setText("⏳ 預測中...")
        self.predict_button.setEnabled(False)
        
        # 實際應用中，這裡會調用 API
        # result = await api.predict(year=year, race=race, session=session)
        
        # Demo：直接重新填充相同數據
        QApplication.processEvents()
        import time
        time.sleep(0.5)  # 模擬網路延遲
        
        self._populate_table()
        
        self.predict_button.setText("🔮 執行預測")
        self.predict_button.setEnabled(True)
    
    def _generate_mock_data(self) -> dict:
        """生成模擬預測數據（Austria 2025）"""
        return {
            "metadata": {
                "model_version": "v3.8",
                "track": "Austria",
                "year": 2025,
                "session": "Q",
                "model_r2": 0.8923,
                "model_mae": 2.534,
                "sample_count": 145,
                "avg_improvement": -0.165,
                "top5_gap": 0.311,
                "prediction_time": "2025-11-05T14:30:00"
            },
            "predictions": [
                {
                    "rank": 1,
                    "driver": "VER",
                    "team": "Red Bull Racing",
                    "predicted_time": 64.523,
                    "fp3_time": 64.643,
                    "improvement": -0.120,
                    "confidence": 0.98
                },
                {
                    "rank": 2,
                    "driver": "LEC",
                    "team": "Ferrari",
                    "predicted_time": 64.689,
                    "fp3_time": 64.869,
                    "improvement": -0.180,
                    "confidence": 0.95
                },
                {
                    "rank": 3,
                    "driver": "NOR",
                    "team": "McLaren",
                    "predicted_time": 64.712,
                    "fp3_time": 64.862,
                    "improvement": -0.150,
                    "confidence": 0.92
                },
                {
                    "rank": 4,
                    "driver": "SAI",
                    "team": "Ferrari",
                    "predicted_time": 64.801,
                    "fp3_time": 65.011,
                    "improvement": -0.210,
                    "confidence": 0.91
                },
                {
                    "rank": 5,
                    "driver": "PIA",
                    "team": "McLaren",
                    "predicted_time": 64.834,
                    "fp3_time": 65.004,
                    "improvement": -0.170,
                    "confidence": 0.89
                },
                {
                    "rank": 6,
                    "driver": "HAM",
                    "team": "Mercedes",
                    "predicted_time": 64.923,
                    "fp3_time": 65.063,
                    "improvement": -0.140,
                    "confidence": 0.85
                },
                {
                    "rank": 7,
                    "driver": "RUS",
                    "team": "Mercedes",
                    "predicted_time": 64.991,
                    "fp3_time": 65.181,
                    "improvement": -0.190,
                    "confidence": 0.84
                },
                {
                    "rank": 8,
                    "driver": "PER",
                    "team": "Red Bull Racing",
                    "predicted_time": 65.045,
                    "fp3_time": 65.205,
                    "improvement": -0.160,
                    "confidence": 0.82
                },
                {
                    "rank": 9,
                    "driver": "ALO",
                    "team": "Aston Martin",
                    "predicted_time": 65.189,
                    "fp3_time": 65.319,
                    "improvement": -0.130,
                    "confidence": 0.78
                },
                {
                    "rank": 10,
                    "driver": "STR",
                    "team": "Aston Martin",
                    "predicted_time": 65.267,
                    "fp3_time": 65.467,
                    "improvement": -0.200,
                    "confidence": 0.75
                },
                {
                    "rank": 11,
                    "driver": "GAS",
                    "team": "Alpine",
                    "predicted_time": 65.412,
                    "fp3_time": 65.545,
                    "improvement": -0.133,
                    "confidence": 0.72
                },
                {
                    "rank": 12,
                    "driver": "OCO",
                    "team": "Alpine",
                    "predicted_time": 65.489,
                    "fp3_time": 65.612,
                    "improvement": -0.123,
                    "confidence": 0.70
                },
                {
                    "rank": 13,
                    "driver": "ALB",
                    "team": "Williams",
                    "predicted_time": 65.567,
                    "fp3_time": 65.701,
                    "improvement": -0.134,
                    "confidence": 0.68
                },
                {
                    "rank": 14,
                    "driver": "SAR",
                    "team": "Williams",
                    "predicted_time": 65.623,
                    "fp3_time": 65.789,
                    "improvement": -0.166,
                    "confidence": 0.66
                },
                {
                    "rank": 15,
                    "driver": "TSU",
                    "team": "RB",
                    "predicted_time": 65.701,
                    "fp3_time": 65.823,
                    "improvement": -0.122,
                    "confidence": 0.64
                }
            ]
        }


def main():
    """主程式"""
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle("Fusion")
    
    # 深色主題
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    # 創建並顯示主視窗
    window = QualifyingPredictionDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
