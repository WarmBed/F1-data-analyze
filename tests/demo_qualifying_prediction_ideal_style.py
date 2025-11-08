#!/usr/bin/env python3
"""
排位賽預測 GUI Demo - Ideal Ranking Table 風格
Qualifying Prediction Demo - Ideal Ranking Table Style

完全遵循 ideal_lap_ranking_table_widget.py 的風格：
- 白底黑字
- 8pt 字體
- 車隊背景色 + 自動文字顏色
- 統計摘要面板
- 梯度顏色差異
- 所有 UI 元素與 ideal_lap_ranking_table 一致

欄位：排名、車手、車隊、FP3 時間、預測時間、Q 結果、△ FP3、信賴度、R²

作者: F1T Team
日期: 2025-11-05
版本: 1.0.0
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox,
    QPushButton, QGroupBox, QAbstractItemView, QGridLayout,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen
from typing import Dict, List, Any, Optional


class ConfidenceBarDelegate(QStyledItemDelegate):
    """信賴度進度條委託（基於 R²）"""
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        r2_value = index.data(Qt.UserRole)
        
        if r2_value is None:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 背景填色，支援選取狀態
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.palette.base())
        
        # 計算進度條
        base_x = option.rect.x() + 5
        base_y = option.rect.y() + option.rect.height() // 2 - 8
        bar_width = option.rect.width() - 60
        bar_height = 16
        
        # 進度條背景
        bg_rect = QRectF(base_x, base_y, bar_width, bar_height)
        painter.fillRect(bg_rect, QBrush(QColor(240, 240, 240)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(bg_rect)
        
        # 進度條填充
        fill_width = bar_width * r2_value
        fill_rect = QRectF(base_x, base_y, fill_width, bar_height)
        
        # 根據 R² 值選擇顏色
        if r2_value >= 0.90:
            color = QColor(0, 150, 0)  # 深綠
        elif r2_value >= 0.85:
            color = QColor(100, 200, 100)  # 淺綠
        elif r2_value >= 0.75:
            color = QColor(255, 200, 0)  # 黃色
        else:
            color = QColor(255, 150, 0)  # 橙色
        
        painter.fillRect(fill_rect, QBrush(color))
        
        # 繪製百分比文字
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QPen(QColor(0, 0, 0)))
        text = f"{int(r2_value * 100)}%"
        text_x = int(base_x + bar_width + 5)
        text_y = int(base_y + bar_height // 2 + 4)
        painter.drawText(text_x, text_y, text)
        
        painter.restore()


class QualifyingPredictionIdealStyleDemo(QMainWindow):
    """排位賽預測 Demo - Ideal Ranking Table 風格"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 - Ideal Ranking Table 風格")
        self.setGeometry(100, 100, 1400, 800)
        
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
        """創建控制面板"""
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
        
        # ❌ 移除預測按鈕（已取消）
        
        panel.setLayout(layout)
        return panel
    
    def _create_table(self) -> QTableWidget:
        """創建主表格（完全遵循 ideal_lap_ranking_table 風格）"""
        table = QTableWidget()
        
        # 設置欄位
        columns = [
            "排名",        # 0: position (隱藏)
            "車手",        # 1: driver (背景色)
            "車隊",        # 2: team
            "FP3 時間",    # 3: fp3_time
            "預測時間",    # 4: predicted_time
            "Q 結果",      # 5: actual_q_time
            "△ FP3",      # 6: improvement (梯度顏色)
            "信賴度",      # 7: confidence (進度條)
            "R²"          # 8: r2_value
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
        table.setColumnWidth(6, 100)  # △ FP3
        table.setColumnWidth(7, 150)  # 信賴度（進度條）
        table.setColumnWidth(8, 100)  # R²
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # ✅ 隱藏排名欄位（第 0 欄）
        table.setColumnHidden(0, True)
        
        # ✅ 為信賴度欄位設置自訂 Delegate
        self.confidence_delegate = ConfidenceBarDelegate(table)
        table.setItemDelegateForColumn(7, self.confidence_delegate)
        
        return table
    
    def _create_summary_panel(self) -> QGroupBox:
        """創建統計摘要面板（與 ideal_lap_ranking_table 一致）"""
        panel = QGroupBox("📊 預測統計摘要")
        panel.setMaximumHeight(150)
        
        grid_layout = QGridLayout()
        panel.setLayout(grid_layout)
        
        # 標籤字體
        label_font = QFont()
        label_font.setBold(True)
        
        # 行 1: 基本資訊
        self.lbl_total_drivers = self._create_stat_label("總車手數: -", label_font)
        self.lbl_model_version = self._create_stat_label("模型版本: -", label_font)
        grid_layout.addWidget(self.lbl_total_drivers, 0, 0)
        grid_layout.addWidget(self.lbl_model_version, 0, 1)
        
        # 行 2: 預測統計
        self.lbl_avg_prediction = self._create_stat_label("平均預測時間: -", label_font)
        self.lbl_prediction_range = self._create_stat_label("預測時間範圍: -", label_font)
        grid_layout.addWidget(self.lbl_avg_prediction, 1, 0)
        grid_layout.addWidget(self.lbl_prediction_range, 1, 1)
        
        # 行 3: 模型指標
        self.lbl_model_r2 = self._create_stat_label("模型 R²: -", label_font)
        self.lbl_avg_improvement = self._create_stat_label("平均改善: -", label_font)
        grid_layout.addWidget(self.lbl_model_r2, 2, 0)
        grid_layout.addWidget(self.lbl_avg_improvement, 2, 1)
        
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
            
            # 7. 信賴度（使用委託繪製進度條）
            confidence = pred.get("confidence", 0)
            conf_item = QTableWidgetItem("")
            conf_item.setData(Qt.UserRole, confidence)
            self.table.setItem(row, 7, conf_item)
            
            # 8. R²
            r2 = pred.get("r2", 0)
            r2_item = QTableWidgetItem(f"{r2:.4f}")
            r2_item.setTextAlignment(Qt.AlignCenter)
            r2_item.setFont(QFont("Arial", 8))
            self.table.setItem(row, 8, r2_item)
            
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
            
            # 模型版本
            model_version = metadata.get("model_version", "N/A")
            self.lbl_model_version.setText(f"模型版本: {model_version}")
            
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
            
            # 模型 R²
            model_r2 = metadata.get("model_r2", 0)
            model_mae = metadata.get("model_mae", 0)
            self.lbl_model_r2.setText(f"模型 R²: {model_r2:.4f} (MAE: {model_mae:.3f}s)")
            
            # 平均改善
            avg_improvement = metadata.get("avg_improvement", 0)
            self.lbl_avg_improvement.setText(f"平均改善: {avg_improvement:.3f}s")
            
        except Exception as e:
            print(f"❌ 更新統計面板失敗: {e}")
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """獲取車手顏色（簡化版車隊色）"""
        # 簡化的車隊顏色映射（基於車手代碼）
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
        """根據改善幅度返回梯度顏色（與 ideal_lap_ranking_table 的 gap_color 一致）"""
        # 使用與 shared_colors.get_gap_color 相同的邏輯
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
    
    def _on_predict_clicked(self):
        """執行預測按鈕點擊事件"""
        # 實際應用中會調用 API
        print("🔮 執行預測...")
    
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
                "prediction_time": "2025-11-05T14:30:00"
            },
            "predictions": [
                {"rank": 1, "driver": "VER", "team": "Red Bull Racing", "fp3_time": 64.643, "predicted_time": 64.523, "actual_q_time": 64.512, "improvement": -0.120, "confidence": 0.98, "r2": 0.9234},
                {"rank": 2, "driver": "LEC", "team": "Ferrari", "fp3_time": 64.869, "predicted_time": 64.689, "actual_q_time": 64.701, "improvement": -0.180, "confidence": 0.95, "r2": 0.8956},
                {"rank": 3, "driver": "NOR", "team": "McLaren", "fp3_time": 64.862, "predicted_time": 64.712, "actual_q_time": 64.723, "improvement": -0.150, "confidence": 0.92, "r2": 0.8845},
                {"rank": 4, "driver": "SAI", "team": "Ferrari", "fp3_time": 65.011, "predicted_time": 64.801, "actual_q_time": 64.834, "improvement": -0.210, "confidence": 0.91, "r2": 0.8723},
                {"rank": 5, "driver": "PIA", "team": "McLaren", "fp3_time": 65.004, "predicted_time": 64.834, "actual_q_time": 64.856, "improvement": -0.170, "confidence": 0.89, "r2": 0.8612},
                {"rank": 6, "driver": "HAM", "team": "Mercedes", "fp3_time": 65.063, "predicted_time": 64.923, "actual_q_time": None, "improvement": -0.140, "confidence": 0.85, "r2": 0.8501},
                {"rank": 7, "driver": "RUS", "team": "Mercedes", "fp3_time": 65.181, "predicted_time": 64.991, "actual_q_time": None, "improvement": -0.190, "confidence": 0.84, "r2": 0.8434},
                {"rank": 8, "driver": "PER", "team": "Red Bull Racing", "fp3_time": 65.205, "predicted_time": 65.045, "actual_q_time": None, "improvement": -0.160, "confidence": 0.82, "r2": 0.8345},
                {"rank": 9, "driver": "ALO", "team": "Aston Martin", "fp3_time": 65.319, "predicted_time": 65.189, "actual_q_time": None, "improvement": -0.130, "confidence": 0.78, "r2": 0.8223},
                {"rank": 10, "driver": "STR", "team": "Aston Martin", "fp3_time": 65.467, "predicted_time": 65.267, "actual_q_time": None, "improvement": -0.200, "confidence": 0.75, "r2": 0.8134},
                {"rank": 11, "driver": "GAS", "team": "Alpine", "fp3_time": 65.545, "predicted_time": 65.412, "actual_q_time": None, "improvement": -0.133, "confidence": 0.72, "r2": 0.8045},
                {"rank": 12, "driver": "OCO", "team": "Alpine", "fp3_time": 65.612, "predicted_time": 65.489, "actual_q_time": None, "improvement": -0.123, "confidence": 0.70, "r2": 0.7956},
                {"rank": 13, "driver": "ALB", "team": "Williams", "fp3_time": 65.701, "predicted_time": 65.567, "actual_q_time": None, "improvement": -0.134, "confidence": 0.68, "r2": 0.7867},
                {"rank": 14, "driver": "SAR", "team": "Williams", "fp3_time": 65.789, "predicted_time": 65.623, "actual_q_time": None, "improvement": -0.166, "confidence": 0.66, "r2": 0.7778},
                {"rank": 15, "driver": "TSU", "team": "RB", "fp3_time": 65.823, "predicted_time": 65.701, "actual_q_time": None, "improvement": -0.122, "confidence": 0.64, "r2": 0.7689},
            ]
        }


def main():
    """主程式"""
    app = QApplication(sys.argv)
    
    # ✅ 不設置深色主題，使用系統預設（白底）
    # 不調用 app.setStyle("Fusion") 或 setPalette()
    
    window = QualifyingPredictionIdealStyleDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
