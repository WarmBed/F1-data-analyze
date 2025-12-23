#!/usr/bin/env python3
"""
正賽預測表格元件
Race Prediction Widget

負責顯示正賽預測分析的表格，包含車手排名預測、車隊評級等資訊
基於排位賽數據和動態車隊評級進行預測

作者: F1T Team
日期: 2025-11-27
版本: 1.0.0
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QLabel,
    QGridLayout, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont, QBrush
from typing import Dict, List, Any, Optional

from core.gui_i18n import tr, get_team_name_text
from modules.gui.themes.color_palette_provider import color_palette_provider

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger(component="race_prediction_widget")


class RacePredictionWidget(QWidget):
    """
    正賽預測表格元件
    
    顯示所有車手的正賽預測，包含：
    - 8 欄位表格（排名、車手、車隊、車隊評級、Q位置、預測位置、實際位置、變化）
    - 車隊顏色編碼
    - 名次變化梯度顏色
    - 模型統計摘要
    - Tooltip 懸停資訊
    
    資料格式：
    {
        "metadata": {
            "track": str,
            "year": int,
            "session": str,
            "model_accuracy": float,
            "prediction_time": str
        },
        "predictions": [
            {
                "rank": int,
                "driver": str,
                "team": str,
                "team_rating": float,
                "q_position": int,
                "predicted_position": int,
                "actual_position": int | None,
                "position_change": int | None
            }
        ],
        "team_ratings": {
            "team_name": float,
            ...
        }
    }
    """
    
    # 信號
    data_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_data: Optional[Dict[str, Any]] = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 車隊評級面板（放在最上方）
        self.team_rating_panel = self._create_team_rating_panel()
        layout.addWidget(self.team_rating_panel)
        
        # 主表格
        self.table = self._create_table()
        layout.addWidget(self.table, 1)
        
        # 統計摘要面板
        self.summary_panel = self._create_summary_panel()
        layout.addWidget(self.summary_panel)
    
    def _create_team_rating_panel(self) -> QGroupBox:
        """創建車隊評級面板"""
        panel = QGroupBox(tr("team_ratings_panel", "Team Ratings (Dynamic)"))
        panel.setMaximumHeight(120)
        
        layout = QHBoxLayout()
        panel.setLayout(layout)
        
        # 創建 10 個車隊評級標籤（稍後動態更新）
        self.team_rating_labels = []
        for i in range(10):
            lbl = QLabel("-")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumWidth(100)
            # 使用安全的默認樣式
            lbl.setStyleSheet("padding: 5px; border-radius: 3px; background-color: #CCCCCC;")
            layout.addWidget(lbl)
            self.team_rating_labels.append(lbl)
        
        return panel
    
    def _create_table(self) -> QTableWidget:
        """創建主表格"""
        table = QTableWidget()
        
        # 欄位定義（移除 Team Rating 欄位，評級已在上方面板顯示）
        columns = [
            tr("rank", "Rank"),                    # 0: 預測排名
            tr("driver", "Driver"),                # 1: 車手
            tr("team", "Team"),                    # 2: 車隊
            tr("q_position", "Q Pos"),             # 3: 排位賽位置
            tr("predicted_pos", "Pred Pos"),       # 4: 預測位置
            tr("actual_pos", "Actual Pos"),        # 5: 實際位置
            tr("position_change", "Change")        # 6: 變化
        ]
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 設置表格屬性
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 設置欄位寬度
        table.setColumnWidth(0, 60)    # 排名
        table.setColumnWidth(1, 100)   # 車手
        table.setColumnWidth(2, 150)   # 車隊
        table.setColumnWidth(3, 80)    # Q位置
        table.setColumnWidth(4, 80)    # 預測位置
        table.setColumnWidth(5, 80)    # 實際位置
        table.setColumnWidth(6, 120)   # 變化
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        return table
    
    def _create_summary_panel(self) -> QGroupBox:
        """創建統計摘要面板"""
        panel = QGroupBox(tr("prediction_statistics", "Prediction Statistics"))
        panel.setMaximumHeight(150)
        
        grid_layout = QGridLayout()
        panel.setLayout(grid_layout)
        
        # 標籤字體
        label_font = QFont()
        label_font.setBold(True)
        
        # 行 1: 基本資訊
        self.lbl_total_drivers = self._create_stat_label(tr("total_drivers_label", "Total Drivers: -"), label_font)
        self.lbl_track_info = self._create_stat_label(tr("track_info_label", "Track: -"), label_font)
        grid_layout.addWidget(self.lbl_total_drivers, 0, 0)
        grid_layout.addWidget(self.lbl_track_info, 0, 1)
        
        # 行 2: 預測準確度
        self.lbl_top1_accuracy = self._create_stat_label(tr("top1_accuracy_label", "Top-1 Accuracy: -"), label_font)
        self.lbl_top3_accuracy = self._create_stat_label(tr("top3_accuracy_label", "Top-3 Accuracy: -"), label_font)
        grid_layout.addWidget(self.lbl_top1_accuracy, 1, 0)
        grid_layout.addWidget(self.lbl_top3_accuracy, 1, 1)
        
        # 行 3: 說明
        self.lbl_explanation = self._create_stat_label("", label_font)
        self.lbl_explanation.setWordWrap(True)
        grid_layout.addWidget(self.lbl_explanation, 2, 0, 1, 2)
        
        return panel
    
    def _create_stat_label(self, text: str, font: QFont) -> QLabel:
        """創建統計標籤"""
        label = QLabel(text)
        label.setFont(font)
        return label
    
    def update_display(self, data: Dict[str, Any]):
        """
        更新顯示的資料
        
        Args:
            data: 預測資料
        """
        try:
            self._current_data = data
            
            metadata = data.get("metadata", {})
            predictions = data.get("predictions", [])
            team_ratings = data.get("team_ratings", {})
            
            if not predictions:
                logger.warning("[RACE_PRED_WIDGET] No prediction data")
                return
            
            # 更新車隊評級面板
            self._update_team_rating_panel(team_ratings)
            
            # 更新表格
            self._populate_table(predictions)
            
            # 更新統計摘要
            self._update_statistics_panel(metadata, predictions)
            
            logger.info("[RACE_PRED_WIDGET] Updated display (%s drivers)", len(predictions))
            
        except Exception as e:
            logger.exception("[RACE_PRED_WIDGET] Update display failed: %s", e)
    
    def _update_team_rating_panel(self, team_ratings: Dict[str, float]):
        """更新車隊評級面板"""
        try:
            # 按評級排序
            sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
            
            for i, lbl in enumerate(self.team_rating_labels):
                if i < len(sorted_teams):
                    team_name, rating = sorted_teams[i]
                    
                    # 獲取車隊顏色（返回 QColor 物件）
                    team_color = color_palette_provider.get_team_color(team_name)
                    if team_color and isinstance(team_color, QColor):
                        bg_color = team_color
                        # 將 QColor 轉換為 hex 字串
                        bg_color_hex = bg_color.name()  # 返回 "#RRGGBB" 格式
                    else:
                        bg_color = QColor(100, 100, 100)
                        bg_color_hex = "#666666"
                    
                    # 計算文字顏色（基於背景亮度）
                    luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
                    text_color = "#FFFFFF" if luminance < 128 else "#000000"
                    
                    # 縮短車隊名稱
                    short_name = self._get_short_team_name(team_name)
                    
                    lbl.setText(f"{short_name}\n{rating:.2f}")
                    lbl.setStyleSheet(
                        f"background-color: {bg_color_hex}; "
                        f"color: {text_color}; "
                        f"padding: 5px; "
                        f"border-radius: 3px; "
                        f"font-weight: bold; "
                        f"font-size: 10px;"
                    )
                else:
                    lbl.setText("-")
                    lbl.setStyleSheet("background-color: #CCCCCC; padding: 5px; border-radius: 3px;")
                    
        except Exception as e:
            logger.exception("[RACE_PRED_WIDGET] Update team rating panel failed: %s", e)
    
    def _get_short_team_name(self, team_name: str) -> str:
        """獲取縮短的車隊名稱"""
        short_names = {
            "Red Bull Racing": "Red Bull",
            "McLaren": "McLaren",
            "Ferrari": "Ferrari",
            "Mercedes": "Mercedes",
            "Aston Martin": "Aston Martin",
            "Alpine": "Alpine",
            "Williams": "Williams",
            "Racing Bulls": "RB",
            "Kick Sauber": "Sauber",
            "Haas F1 Team": "Haas"
        }
        return short_names.get(team_name, team_name[:10])
    
    def _populate_table(self, predictions: List[Dict[str, Any]]):
        """填充表格資料"""
        row_count = len(predictions)
        
        self.table.setSortingEnabled(False)
        self.table.setRowCount(row_count)
        
        for row, pred in enumerate(predictions):
            self._set_row_data(row, pred)
        
        self.table.setSortingEnabled(True)
        logger.info("[TABLE] Loaded %s drivers", row_count)
    
    def _set_row_data(self, row: int, pred: Dict[str, Any]):
        """設置單行資料"""
        try:
            # 0. 排名
            rank = pred.get("rank", row + 1)
            rank_item = QTableWidgetItem()
            rank_item.setData(Qt.DisplayRole, int(rank))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, rank_item)
            
            # 1. 車手
            driver_code = pred.get("driver", "N/A")
            team = pred.get("team", "Unknown")
            
            driver_color_hex = color_palette_provider.get_driver_color(driver_code)
            if driver_color_hex:
                driver_color = QColor(driver_color_hex)
            else:
                driver_color = QColor(100, 100, 100)
            
            driver_item = self._create_colored_item(driver_code, driver_color)
            driver_item.setToolTip(f"{driver_code} - {team}")
            self.table.setItem(row, 1, driver_item)
            
            # 2. 車隊
            team_text = get_team_name_text(team) or team
            team_item = self._create_colored_item(team_text, driver_color)
            team_item.setToolTip(team)
            self.table.setItem(row, 2, team_item)
            
            # 3. Q 位置
            q_pos = pred.get("q_position", "N/A")
            q_pos_item = QTableWidgetItem()
            if q_pos != "N/A":
                q_pos_item.setData(Qt.DisplayRole, int(q_pos))
            else:
                q_pos_item.setText("N/A")
            q_pos_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, q_pos_item)
            
            # 4. 預測位置
            pred_pos = pred.get("predicted_position", rank)
            pred_pos_item = QTableWidgetItem()
            pred_pos_item.setData(Qt.DisplayRole, int(pred_pos))
            pred_pos_item.setTextAlignment(Qt.AlignCenter)
            
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            pred_pos_item.setFont(font)
            self.table.setItem(row, 4, pred_pos_item)
            
            # 5. 實際位置
            actual_pos = pred.get("actual_position")
            if actual_pos is not None:
                actual_item = QTableWidgetItem()
                actual_item.setData(Qt.DisplayRole, int(actual_pos))
                actual_item.setForeground(QBrush(QColor(0, 120, 0)))
            else:
                actual_item = QTableWidgetItem("TBD")
                actual_item.setForeground(QBrush(QColor(100, 100, 100)))
            actual_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, actual_item)
            
            # 6. 變化（預測 vs 實際）
            pos_change = pred.get("position_change")
            change_item = self._create_change_item(pos_change)
            self.table.setItem(row, 6, change_item)
            
        except Exception as e:
            logger.exception("Set row data failed (row %s): %s", row, e)
    
    def _create_change_item(self, change: Optional[int]) -> QTableWidgetItem:
        """創建變化欄位項目"""
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        
        font = QFont()
        font.setPointSize(8)
        item.setFont(font)
        
        if change is None:
            item.setText("TBD")
            item.setBackground(QBrush(QColor(230, 230, 230)))
            item.setForeground(QBrush(QColor(100, 100, 100)))
        elif change > 0:
            # 預測比實際差（實際更好）
            item.setText(f"+{change}")
            item.setBackground(QBrush(QColor(255, 200, 200)))
            item.setForeground(QBrush(QColor(180, 0, 0)))
        elif change < 0:
            # 預測比實際好（實際更差）
            item.setText(f"{change}")
            item.setBackground(QBrush(QColor(200, 255, 200)))
            item.setForeground(QBrush(QColor(0, 120, 0)))
        else:
            item.setText("0")
            item.setBackground(QBrush(QColor(230, 230, 230)))
            item.setForeground(QBrush(QColor(100, 100, 100)))
        
        return item
    
    def _get_rating_color(self, rating: float) -> QColor:
        """根據評級返回顏色"""
        if rating >= 7.0:
            return QColor(200, 255, 200)  # 淺綠色
        elif rating >= 5.0:
            return QColor(255, 255, 200)  # 淺黃色
        elif rating >= 3.0:
            return QColor(255, 230, 200)  # 淺橙色
        else:
            return QColor(255, 200, 200)  # 淺紅色
    
    def _update_statistics_panel(self, metadata: Dict[str, Any], predictions: List[Dict[str, Any]]):
        """更新統計摘要面板"""
        try:
            # 總車手數
            total_drivers = len(predictions)
            self.lbl_total_drivers.setText(
                tr("total_drivers_value", "Total Drivers: {count}").format(count=total_drivers)
            )
            
            # 賽道資訊
            track = metadata.get("track", "N/A")
            year = metadata.get("year", 2025)
            self.lbl_track_info.setText(
                tr("track_info_value", "Track: {track} {year}").format(track=track, year=year)
            )
            
            # 計算準確度（如果有實際結果）
            top1_correct = 0
            top3_correct = 0
            has_actual = False
            
            for pred in predictions:
                actual = pred.get("actual_position")
                if actual is not None:
                    has_actual = True
                    predicted = pred.get("predicted_position", pred.get("rank"))
                    if actual == predicted:
                        top1_correct += 1
                    if abs(actual - predicted) <= 2:
                        top3_correct += 1
            
            if has_actual:
                top1_acc = top1_correct / total_drivers * 100
                top3_acc = top3_correct / total_drivers * 100
                self.lbl_top1_accuracy.setText(
                    tr("top1_accuracy_value", "Top-1 Accuracy: {acc:.1f}%").format(acc=top1_acc)
                )
                self.lbl_top3_accuracy.setText(
                    tr("top3_accuracy_value", "Top-3 Accuracy: {acc:.1f}%").format(acc=top3_acc)
                )
            else:
                self.lbl_top1_accuracy.setText(tr("top1_accuracy_pending", "Top-1 Accuracy: Pending"))
                self.lbl_top3_accuracy.setText(tr("top3_accuracy_pending", "Top-3 Accuracy: Pending"))
            
            # 說明
            explanation = tr(
                "race_prediction_explanation",
                "Predictions based on Q position + Dynamic Team Rating (2023-2024 base + 2025 updates)"
            )
            self.lbl_explanation.setText(explanation)
            
        except Exception as e:
            logger.exception("Update statistics panel failed: %s", e)
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """創建帶背景色的表格項目"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        
        font = QFont()
        font.setPointSize(8)
        item.setFont(font)
        return item
    
    def clear_display(self):
        """清空顯示"""
        self.table.setRowCount(0)
        self._current_data = None
        
        # 重置車隊評級面板
        for lbl in self.team_rating_labels:
            lbl.setText("-")
            lbl.setStyleSheet("padding: 5px; border-radius: 3px;")
        
        # 重置統計標籤
        self.lbl_total_drivers.setText(tr("total_drivers_label", "Total Drivers: -"))
        self.lbl_track_info.setText(tr("track_info_label", "Track: -"))
        self.lbl_top1_accuracy.setText(tr("top1_accuracy_label", "Top-1 Accuracy: -"))
        self.lbl_top3_accuracy.setText(tr("top3_accuracy_label", "Top-3 Accuracy: -"))
        self.lbl_explanation.setText("")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前顯示的資料"""
        return self._current_data
