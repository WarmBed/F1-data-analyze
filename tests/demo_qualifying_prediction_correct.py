#!/usr/bin/env python3
"""
排位賽預測 GUI Demo - 正確版本
Qualifying Prediction Demo - Correct Version

✅ 正確理解：
- R² 和 MAE 是「模型級別」指標，不是「車手級別」
- 同一賽道的所有車手共用同一個模型 R²
- 移除表格中每個車手的 R² 欄位
- R² 資訊移到統計摘要面板

欄位：排名、車手、車隊、FP3 時間、預測時間、Q 結果、△ FP3

作者: F1T Team
日期: 2025-11-05
版本: 2.0.0（正確版本）
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox,
    QGroupBox, QAbstractItemView, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush
from typing import Dict, List, Any, Optional


class QualifyingPredictionCorrectDemo(QMainWindow):
    """排位賽預測 Demo - 正確版本（模型級別 R²）"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 - 正確版本（模型 R² = 0.8923）")
        self.setGeometry(100, 100, 1300, 800)
        
        # 模擬數據
        self.mock_data = self._generate_mock_data()
        
        self._init_ui()
        self._populate_table()
        self._update_statistics_panel()
    
    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # ✅ 使用白底（與 ideal_lap_ranking_table 一致）
        central_widget.setStyleSheet("background-color: white;")
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 主表格
        self.table = self._create_table()
        main_layout.addWidget(self.table, 1)  # 給予彈性空間
        
        # 統計摘要面板（移到下方）
        self.summary_panel = self._create_summary_panel()
        main_layout.addWidget(self.summary_panel)
    
    def _create_control_panel(self) -> QGroupBox:
        """創建控制面板（無預測按鈕）"""
        panel = QGroupBox("預測參數")
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
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _create_table(self) -> QTableWidget:
        """創建主表格（移除每個車手的 R² 欄位）"""
        table = QTableWidget()
        
        # ✅ 設置欄位（7 欄，移除信賴度和 R²）
        columns = [
            "排名",        # 0: position (隱藏)
            "車手",        # 1: driver (背景色)
            "車隊",        # 2: team
            "FP3 時間",    # 3: fp3_time
            "預測時間",    # 4: predicted_time
            "Q 結果",      # 5: actual_q_time
            "△ FP3"       # 6: improvement (梯度顏色)
        ]
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # ✅ 設置表格屬性（與 ideal_lap_ranking_table 一致）
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)  # 禁用選擇
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # ✅ 設置欄位寬度
        table.setColumnWidth(0, 60)   # 排名（隱藏）
        table.setColumnWidth(1, 100)  # 車手
        table.setColumnWidth(2, 150)  # 車隊
        table.setColumnWidth(3, 120)  # FP3 時間
        table.setColumnWidth(4, 120)  # 預測時間
        table.setColumnWidth(5, 120)  # Q 結果
        table.setColumnWidth(6, 120)  # △ FP3
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # ✅ 隱藏排名欄位（第 0 欄）
        table.setColumnHidden(0, True)
        
        return table
    
    def _create_summary_panel(self) -> QGroupBox:
        """創建統計摘要面板"""
        panel = QGroupBox("📊 預測統計摘要")
        panel.setMaximumHeight(180)
        
        grid_layout = QGridLayout()
        panel.setLayout(grid_layout)
        
        # 標籤字體
        label_font = QFont()
        label_font.setBold(True)
        
        # 行 1: 基本資訊
        self.lbl_total_drivers = self._create_stat_label("總車手數: -", label_font)
        self.lbl_track_info = self._create_stat_label("賽道: -", label_font)
        grid_layout.addWidget(self.lbl_total_drivers, 0, 0)
        grid_layout.addWidget(self.lbl_track_info, 0, 1)
        
        # 行 2: 預測時間統計
        self.lbl_avg_prediction = self._create_stat_label("平均預測時間: -", label_font)
        self.lbl_prediction_range = self._create_stat_label("預測時間範圍: -", label_font)
        grid_layout.addWidget(self.lbl_avg_prediction, 1, 0)
        grid_layout.addWidget(self.lbl_prediction_range, 1, 1)
        
        # 行 3: 模型指標（所有車手共用）
        self.lbl_model_r2 = self._create_stat_label("🎯 模型 R²: -", label_font)
        self.lbl_model_mae = self._create_stat_label("📏 模型 MAE: -", label_font)
        grid_layout.addWidget(self.lbl_model_r2, 2, 0)
        grid_layout.addWidget(self.lbl_model_mae, 2, 1)
        
        # 行 4: R² 說明
        self.lbl_r2_explanation = self._create_stat_label("", label_font)
        self.lbl_r2_explanation.setWordWrap(True)
        grid_layout.addWidget(self.lbl_r2_explanation, 3, 0, 1, 2)  # 跨兩欄
        
        return panel
    
    def _create_stat_label(self, text: str, font: QFont) -> QLabel:
        """創建統計標籤"""
        label = QLabel(text)
        label.setFont(font)
        return label
    
    def _populate_table(self):
        """填充表格資料"""
        predictions = self.mock_data["predictions"]
        row_count = len(predictions)
        
        self.table.setSortingEnabled(False)  # 暫時禁用排序
        self.table.setRowCount(row_count)
        
        for row, pred in enumerate(predictions):
            self._set_row_data(row, pred)
        
        self.table.setSortingEnabled(True)  # 重新啟用排序
        print(f"[TABLE] ✅ 已載入 {row_count} 位車手")
    
    def _set_row_data(self, row: int, pred: Dict[str, Any]):
        """設置單行資料"""
        try:
            # 0. 排名（隱藏，用於排序）
            pos_item = QTableWidgetItem()
            pos_item.setData(Qt.DisplayRole, int(pred.get("rank", 0)))
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, pos_item)
            
            # 1. 車手（套用車手背景色）
            driver_code = pred.get("driver", "N/A")
            team = pred.get("team", "Unknown")
            driver_color = self._get_driver_color(driver_code)
            driver_item = self._create_colored_item(driver_code, driver_color)
            driver_item.setToolTip(f"{driver_code} - {team}")
            self.table.setItem(row, 1, driver_item)
            
            # 2. 車隊（套用車手背景色）
            team_item = self._create_colored_item(team, driver_color)
            team_item.setToolTip(team)
            self.table.setItem(row, 2, team_item)
            
            # 3. FP3 時間
            fp3_time = pred.get("fp3_time")
            fp3_item = QTableWidgetItem(self._format_time(fp3_time))
            fp3_item.setTextAlignment(Qt.AlignCenter)
            fp3_item.setFont(QFont("Arial", 8))
            self.table.setItem(row, 3, fp3_item)
            
            # 4. 預測時間
            pred_time = pred.get("predicted_time")
            pred_item = QTableWidgetItem(self._format_time(pred_time))
            pred_item.setTextAlignment(Qt.AlignCenter)
            pred_item.setFont(QFont("Arial", 8, QFont.Bold))
            self.table.setItem(row, 4, pred_item)
            
            # 5. Q 結果
            actual_q = pred.get("actual_q_time")
            if actual_q is not None:
                q_item = QTableWidgetItem(self._format_time(actual_q))
                q_item.setFont(QFont("Arial", 8))
            else:
                q_item = QTableWidgetItem("N/A")
                q_item.setForeground(QBrush(QColor(120, 120, 120)))
                q_item.setFont(QFont("Arial", 8))
            q_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, q_item)
            
            # 6. △ FP3（套用梯度顏色）
            improvement = pred.get("improvement", 0)
            delta_item = QTableWidgetItem()
            delta_item.setData(Qt.DisplayRole, improvement)
            delta_item.setText(f"+{improvement:.3f}s" if improvement >= 0 else f"{improvement:.3f}s")
            delta_item.setTextAlignment(Qt.AlignCenter)
            delta_item.setFont(QFont("Arial", 8))
            delta_item.setBackground(self._get_improvement_color(improvement))
            self.table.setItem(row, 6, delta_item)
            
        except Exception as e:
            print(f"❌ 設置行資料失敗 (row {row}): {e}")
    
    def _update_statistics_panel(self):
        """更新統計摘要面板"""
        try:
            metadata = self.mock_data["metadata"]
            predictions = self.mock_data["predictions"]
            
            # 總車手數
            total_drivers = len(predictions)
            self.lbl_total_drivers.setText(f"總車手數: {total_drivers}")
            
            # 賽道資訊
            track = metadata.get("track", "N/A")
            year = metadata.get("year", 2025)
            self.lbl_track_info.setText(f"賽道: {track} {year}")
            
            # 平均預測時間
            avg_pred = sum(p["predicted_time"] for p in predictions) / len(predictions)
            self.lbl_avg_prediction.setText(f"平均預測時間: {self._format_time(avg_pred)}")
            
            # 預測時間範圍
            min_pred = min(p["predicted_time"] for p in predictions)
            max_pred = max(p["predicted_time"] for p in predictions)
            pred_range = max_pred - min_pred
            self.lbl_prediction_range.setText(
                f"預測時間範圍: {pred_range:.3f}s ({self._format_time(min_pred)} ~ {self._format_time(max_pred)})"
            )
            
            # ✅ 模型 R²（所有車手共用）
            model_r2 = metadata.get("model_r2", 0)
            sample_count = metadata.get("sample_count", 0)
            self.lbl_model_r2.setText(f"🎯 模型 R²: {model_r2:.4f} (樣本數: {sample_count})")
            
            # ✅ 模型 MAE（所有車手共用）
            model_mae = metadata.get("model_mae", 0)
            self.lbl_model_mae.setText(f"📏 模型 MAE: {model_mae:.3f}s (平均誤差)")
            
            # ✅ R² 說明（根據數值動態顯示）
            if model_r2 >= 0.90:
                r2_text = "💡 R² 說明: 極佳（90%+）- 模型能解釋 90% 以上的時間變異，所有車手的預測都高度可靠"
                r2_color = "green"
            elif model_r2 >= 0.85:
                r2_text = "💡 R² 說明: 優秀（85%+）- 模型能解釋 85% 以上的時間變異，所有車手的預測都較可靠"
                r2_color = "darkgreen"
            elif model_r2 >= 0.75:
                r2_text = "💡 R² 說明: 良好（75%+）- 模型能解釋 75% 以上的時間變異，所有車手的預測有一定可靠性"
                r2_color = "orange"
            else:
                r2_text = "💡 R² 說明: 中等（<75%）- 模型解釋能力有限，所有車手的預測僅供參考"
                r2_color = "red"
            
            self.lbl_r2_explanation.setText(r2_text)
            self.lbl_r2_explanation.setStyleSheet(f"color: {r2_color}; font-weight: bold;")
            
        except Exception as e:
            print(f"❌ 更新統計面板失敗: {e}")
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """獲取車手顏色（簡化版車隊色）"""
        team_colors = {
            "VER": QColor(30, 65, 255),      # Red Bull
            "PER": QColor(30, 65, 255),
            "LEC": QColor(220, 0, 0),        # Ferrari
            "SAI": QColor(220, 0, 0),
            "HAM": QColor(0, 210, 190),      # Mercedes
            "RUS": QColor(0, 210, 190),
            "NOR": QColor(255, 135, 0),      # McLaren
            "PIA": QColor(255, 135, 0),
            "ALO": QColor(0, 111, 98),       # Aston Martin
            "STR": QColor(0, 111, 98),
            "GAS": QColor(255, 135, 188),    # Alpine
            "OCO": QColor(255, 135, 188),
            "ALB": QColor(0, 82, 255),       # Williams
            "SAR": QColor(0, 82, 255),
            "TSU": QColor(102, 146, 255),    # RB
            "RIC": QColor(102, 146, 255),
            "BOT": QColor(0, 230, 0),        # Kick Sauber
            "ZHO": QColor(0, 230, 0),
            "HUL": QColor(180, 180, 180),    # Haas
            "MAG": QColor(180, 180, 180),
        }
        return team_colors.get(driver_code, QColor(100, 100, 100))
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """創建帶背景色的表格項目，自動選擇文字顏色"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        # ✅ 根據背景色亮度決定文字顏色（與 ideal_lap_ranking_table 一致）
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        item.setFont(QFont("Arial", 8))
        return item
    
    def _get_improvement_color(self, improvement: float) -> QColor:
        """根據改善幅度返回梯度顏色"""
        if improvement <= -0.3:
            return QColor(0, 180, 0)      # 深綠（極大改善）
        elif improvement <= -0.2:
            return QColor(50, 220, 50)    # 綠色
        elif improvement <= -0.1:
            return QColor(150, 255, 150)  # 淺綠
        elif improvement <= 0.0:
            return QColor(255, 255, 150)  # 黃色
        elif improvement <= 0.1:
            return QColor(255, 200, 100)  # 橙色
        else:
            return QColor(255, 150, 150)  # 紅色（退步）
    
    def _format_time(self, seconds: Optional[float]) -> str:
        """格式化時間為 MM:SS.mmm"""
        if seconds is None:
            return "N/A"
        
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _generate_mock_data(self) -> dict:
        """生成模擬預測數據（Austria 2025）"""
        return {
            "metadata": {
                "track": "Austria",
                "year": 2025,
                "session": "Q",
                "model_r2": 0.8923,      # ✅ 唯一的模型 R²
                "model_mae": 2.534,      # ✅ 唯一的模型 MAE
                "sample_count": 145,     # ✅ 訓練樣本數
                "prediction_time": "2025-11-05T14:30:00"
            },
            "predictions": [
                # ✅ 所有車手共用同一個模型（R² = 0.8923, MAE = 2.534s）
                {"rank": 1, "driver": "VER", "team": "Red Bull Racing", "fp3_time": 64.643, "predicted_time": 64.523, "actual_q_time": 64.512, "improvement": -0.120},
                {"rank": 2, "driver": "LEC", "team": "Ferrari", "fp3_time": 64.869, "predicted_time": 64.689, "actual_q_time": 64.701, "improvement": -0.180},
                {"rank": 3, "driver": "NOR", "team": "McLaren", "fp3_time": 64.862, "predicted_time": 64.712, "actual_q_time": 64.723, "improvement": -0.150},
                {"rank": 4, "driver": "SAI", "team": "Ferrari", "fp3_time": 65.011, "predicted_time": 64.801, "actual_q_time": 64.834, "improvement": -0.210},
                {"rank": 5, "driver": "PIA", "team": "McLaren", "fp3_time": 65.004, "predicted_time": 64.834, "actual_q_time": 64.856, "improvement": -0.170},
                {"rank": 6, "driver": "HAM", "team": "Mercedes", "fp3_time": 65.063, "predicted_time": 64.923, "actual_q_time": None, "improvement": -0.140},
                {"rank": 7, "driver": "RUS", "team": "Mercedes", "fp3_time": 65.181, "predicted_time": 64.991, "actual_q_time": None, "improvement": -0.190},
                {"rank": 8, "driver": "PER", "team": "Red Bull Racing", "fp3_time": 65.205, "predicted_time": 65.045, "actual_q_time": None, "improvement": -0.160},
                {"rank": 9, "driver": "ALO", "team": "Aston Martin", "fp3_time": 65.319, "predicted_time": 65.189, "actual_q_time": None, "improvement": -0.130},
                {"rank": 10, "driver": "STR", "team": "Aston Martin", "fp3_time": 65.467, "predicted_time": 65.267, "actual_q_time": None, "improvement": -0.200},
                {"rank": 11, "driver": "GAS", "team": "Alpine", "fp3_time": 65.545, "predicted_time": 65.412, "actual_q_time": None, "improvement": -0.133},
                {"rank": 12, "driver": "OCO", "team": "Alpine", "fp3_time": 65.612, "predicted_time": 65.489, "actual_q_time": None, "improvement": -0.123},
                {"rank": 13, "driver": "ALB", "team": "Williams", "fp3_time": 65.701, "predicted_time": 65.567, "actual_q_time": None, "improvement": -0.134},
                {"rank": 14, "driver": "SAR", "team": "Williams", "fp3_time": 65.789, "predicted_time": 65.623, "actual_q_time": None, "improvement": -0.166},
                {"rank": 15, "driver": "TSU", "team": "RB", "fp3_time": 65.823, "predicted_time": 65.701, "actual_q_time": None, "improvement": -0.122},
            ]
        }


def main():
    """主程式"""
    app = QApplication(sys.argv)
    
    # ✅ 不設置深色主題，使用系統預設（白底）
    
    window = QualifyingPredictionCorrectDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
