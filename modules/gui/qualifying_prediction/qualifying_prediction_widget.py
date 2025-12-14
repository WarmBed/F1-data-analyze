#!/usr/bin/env python3
"""
排位賽預測表格元件
Qualifying Prediction Widget

負責顯示排位賽預測分析的表格，包含車手排名、FP3時間、預測時間、Q結果等資訊
基於機器學習模型的預測結果

作者: F1T Team
日期: 2025-11-05
版本: 1.0.0
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QLabel,
    QGridLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont, QBrush
from typing import Dict, List, Any, Optional

from core.gui_i18n import tr, get_team_name_text
from modules.gui.themes.color_palette_provider import color_palette_provider  # ✅ 使用通用顏色系統

from core.logger import get_logger
logger = get_logger(__name__)




class QualifyingPredictionWidget(QWidget):
    """
    排位賽預測表格元件
    
    顯示所有車手的排位賽預測，包含：
    - 7 欄位表格（排名、車手、車隊、FP3時間、預測時間、Q結果、△FP3）
    - 車隊顏色編碼
    - 改善幅度梯度顏色
    - 模型統計摘要（R²、MAE、可靠性）
    - Tooltip 懸停資訊
    
    資料格式：
    {
        "metadata": {
            "track": str,
            "year": int,
            "model_r2": float,  # 模型級別指標
            "model_mae": float,
            "sample_count": int,
            "avg_prediction_time": float,
            "prediction_range": float,
            "reliability_text": str,
            "reliability_color": str
        },
        "predictions": [
            {
                "rank": int,
                "driver": str,
                "team": str,
                "fp3_time": float,
                "predicted_time": float,
                "actual_q_time": float | None,
                "improvement": float
            }
        ]
    }
    """
    
    # 信號
    data_requested = pyqtSignal(dict)  # 請求載入數據
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_data: Optional[Dict[str, Any]] = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 主表格
        self.table = self._create_table()
        layout.addWidget(self.table, 1)  # 給予彈性空間
        
        # 統計摘要面板
        self.summary_panel = self._create_summary_panel()
        layout.addWidget(self.summary_panel)
    
    def _create_table(self) -> QTableWidget:
        """創建主表格（7 欄，移除每個車手的 R² 欄位）"""
        table = QTableWidget()
        
        # ✅ 重新調整欄位順序（2025-11-05）
        # 順序: 車手 → 車隊 → FP3時間 → 預測時間 → Q時間 → △FP3 → 預測名次 → Q名次 → 變化
        columns = [
            tr("rank", "排名"),           # 0: position (隱藏，用於排序)
            tr("driver", "車手"),          # 1: driver (背景色)
            tr("team", "車隊"),            # 2: team
            tr("fp3_time", "FP3 時間"),    # 3: fp3_time
            tr("predicted_time", "預測時間"),  # 4: predicted_time
            tr("q_result", "Q 時間"),      # 5: actual_q_time
            tr("delta_fp3", "△ FP3"),     # 6: improvement (梯度顏色)
            tr("fp3_rank", "預測名次"),    # 7: fp3_predicted_rank
            tr("q_rank", "Q 名次"),        # 8: actual_q_rank
            tr("rank_change", "變化")      # 9: rank_change (綠色=進步，紅色=退步)
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
        table.setColumnWidth(5, 120)  # Q 時間
        table.setColumnWidth(6, 120)  # △ FP3
        table.setColumnWidth(7, 80)   # 預測名次
        table.setColumnWidth(8, 80)   # Q 名次
        table.setColumnWidth(9, 100)  # 變化
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # ✅ 隱藏排名欄位（第 0 欄）
        table.setColumnHidden(0, True)
        
        return table
    
    def _create_summary_panel(self) -> QGroupBox:
        """創建統計摘要面板（與 ideal_lap_ranking_table 一致的 GridLayout）"""
        panel = QGroupBox(tr("prediction_statistics", "📊 預測統計摘要"))
        panel.setMaximumHeight(180)
        
        grid_layout = QGridLayout()
        panel.setLayout(grid_layout)
        
        # 標籤字體
        label_font = QFont()
        label_font.setBold(True)
        
        # 行 1: 基本資訊
        self.lbl_total_drivers = self._create_stat_label(tr("total_drivers_label", "總車手數: -"), label_font)
        self.lbl_track_info = self._create_stat_label(tr("track_info_label", "賽道: -"), label_font)
        grid_layout.addWidget(self.lbl_total_drivers, 0, 0)
        grid_layout.addWidget(self.lbl_track_info, 0, 1)
        
        # 行 2: 模型指標（所有車手共用）
        self.lbl_model_r2 = self._create_stat_label(tr("model_r2_label", "🎯 模型 R²: -"), label_font)
        self.lbl_model_mae = self._create_stat_label(tr("model_mae_label", "📏 模型 MAE: -"), label_font)
        grid_layout.addWidget(self.lbl_model_r2, 1, 0)
        grid_layout.addWidget(self.lbl_model_mae, 1, 1)
        
        # 行 3: R² 說明（跨兩欄）
        self.lbl_r2_explanation = self._create_stat_label("", label_font)
        self.lbl_r2_explanation.setWordWrap(True)
        grid_layout.addWidget(self.lbl_r2_explanation, 2, 0, 1, 2)  # 跨兩欄
        
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
            data: 預測資料（包含 metadata 和 predictions）
        """
        try:
            self._current_data = data
            
            metadata = data.get("metadata", {})
            predictions = data.get("predictions", [])
            
            if not predictions:
                logger.warning("[QUALIFYING_WIDGET] ⚠️ 沒有預測數據")
                return
            
            # 更新表格
            self._populate_table(predictions)
            
            # 更新統計摘要
            self._update_statistics_panel(metadata, predictions)
            
            logger.info("[QUALIFYING_WIDGET] ✅ 已更新顯示 (%s 位車手)", len(predictions))
            
        except Exception as e:
            logger.exception("[QUALIFYING_WIDGET] ❌ 更新顯示失敗: %s", e)
    
    def _populate_table(self, predictions: List[Dict[str, Any]]):
        """填充表格資料"""
        row_count = len(predictions)
        
        self.table.setSortingEnabled(False)  # 暫時禁用排序
        self.table.setRowCount(row_count)
        
        for row, pred in enumerate(predictions):
            self._set_row_data(row, pred)
        
        self.table.setSortingEnabled(True)  # 重新啟用排序
        logger.info("[TABLE] ✅ 已載入 %s 位車手", row_count)
    
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
            
            # ✅ 使用 color_palette_provider 獲取車手顏色
            driver_color_hex = color_palette_provider.get_driver_color(driver_code)
            if driver_color_hex:
                # 轉換 hex 為 QColor
                driver_color = QColor(driver_color_hex)
            else:
                # 預設灰色
                driver_color = QColor(100, 100, 100)
            
            driver_item = self._create_colored_item(driver_code, driver_color)
            driver_item.setToolTip(f"{driver_code} - {team}")
            self.table.setItem(row, 1, driver_item)
            
            # 2. 車隊（套用車手背景色）
            team_text = get_team_name_text(team) or team
            team_item = self._create_colored_item(team_text, driver_color)
            team_item.setToolTip(team)
            self.table.setItem(row, 2, team_item)
            
            # 3. FP3 時間
            fp3_time = pred.get("fp3_time")
            fp3_item = QTableWidgetItem(self._format_time(fp3_time))
            fp3_item.setTextAlignment(Qt.AlignCenter)
            
            # ✅ 使用系統預設字體（8pt，無粗體）
            font = QFont()
            font.setPointSize(8)
            fp3_item.setFont(font)
            self.table.setItem(row, 3, fp3_item)
            
            # 4. 預測時間
            pred_time = pred.get("predicted_time")
            pred_item = QTableWidgetItem(self._format_time(pred_time))
            pred_item.setTextAlignment(Qt.AlignCenter)
            
            # ✅ 使用系統預設字體（8pt，無粗體）
            font = QFont()
            font.setPointSize(8)
            pred_item.setFont(font)
            self.table.setItem(row, 4, pred_item)
            
            # 5. Q 時間
            actual_q = pred.get("actual_q_time")
            if actual_q is not None:
                q_item = QTableWidgetItem(self._format_time(actual_q))
            else:
                q_item = QTableWidgetItem("N/A")
                q_item.setForeground(QBrush(QColor(120, 120, 120)))
            
            # ✅ 使用系統預設字體（8pt，無粗體）
            font = QFont()
            font.setPointSize(8)
            q_item.setFont(font)
            q_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, q_item)
            
            # 6. △ FP3（使用 Driver Race Position 風格：淡色背景 + 三角形）
            improvement = pred.get("improvement", 0)
            delta_item = QTableWidgetItem()
            delta_item.setData(Qt.DisplayRole, improvement)
            
            # ✅ 設置字體（8pt，與 Driver Race Position 一致）
            # 使用系統預設字體以支援 Unicode 符號（▲▼）
            font = QFont()
            font.setPointSize(8)
            delta_item.setFont(font)
            
            # 使用三角形符號和淺色背景
            if improvement > 0:
                # 進步 - 淺綠色背景 + 向上三角形
                delta_item.setText(f"+{improvement:.3f}s ▲")
                delta_item.setBackground(QBrush(QColor(200, 255, 200)))  # 淺綠色
                delta_item.setForeground(QBrush(QColor(0, 120, 0)))  # 深綠色文字（與 Position 統一）
            elif improvement < 0:
                # 退步 - 淺紅色背景 + 向下三角形
                delta_item.setText(f"{improvement:.3f}s ▼")
                delta_item.setBackground(QBrush(QColor(255, 200, 200)))  # 淺紅色
                delta_item.setForeground(QBrush(QColor(180, 0, 0)))  # 深紅色文字（與 Position 統一）
            else:
                # 持平 - 淺灰色背景
                delta_item.setText(f"{improvement:.3f}s")
                delta_item.setBackground(QBrush(QColor(230, 230, 230)))  # 淺灰色（與 Position 統一）
                delta_item.setForeground(QBrush(QColor(100, 100, 100)))
            
            delta_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, delta_item)
            
            # 7. 預測名次（FP3 預測名次）
            fp3_rank = pred.get("fp3_predicted_rank", pred.get("rank"))
            fp3_rank_item = QTableWidgetItem()
            fp3_rank_item.setData(Qt.DisplayRole, int(fp3_rank))
            fp3_rank_item.setTextAlignment(Qt.AlignCenter)
            
            # ✅ 使用系統預設字體（8pt，無粗體）
            font = QFont()
            font.setPointSize(8)
            fp3_rank_item.setFont(font)
            self.table.setItem(row, 7, fp3_rank_item)
            
            # 8. Q 名次
            actual_q_rank = pred.get("actual_q_rank")
            if actual_q_rank is not None:
                q_rank_item = QTableWidgetItem()
                q_rank_item.setData(Qt.DisplayRole, int(actual_q_rank))
                
                # ✅ 使用系統預設字體（8pt，無粗體）
                font = QFont()
                font.setPointSize(8)
                q_rank_item.setFont(font)
                q_rank_item.setForeground(QBrush(QColor(0, 120, 0)))  # 深綠色（與 Position 統一）
            else:
                q_rank_item = QTableWidgetItem("N/A")
                q_rank_item.setForeground(QBrush(QColor(100, 100, 100)))  # 深灰色（與 Position 統一）
                
                # ✅ 使用系統預設字體（8pt，無粗體）
                font = QFont()
                font.setPointSize(8)
                q_rank_item.setFont(font)
            q_rank_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 8, q_rank_item)
            
            # 9. 變化（名次變化：FP3預測 → Q實際，使用 Driver Race Position 風格）
            rank_change = pred.get("rank_change")
            if rank_change is not None:
                change_item = QTableWidgetItem()
                
                # ✅ 設置字體（8pt，與 Driver Race Position 一致）
                # 使用系統預設字體以支援 Unicode 符號（▲▼━）
                font = QFont()
                font.setPointSize(8)
                change_item.setFont(font)
                
                # 使用三角形符號和淺色背景（與 Driver Race Position 一致）
                if rank_change > 0:
                    # 進步（排名上升）- 淺綠色背景 + 向上三角形
                    change_item.setText(f"{rank_change} ▲")
                    change_item.setBackground(QBrush(QColor(200, 255, 200)))  # 淺綠色
                    change_item.setForeground(QBrush(QColor(0, 120, 0)))  # 深綠色文字（與 Position 統一）
                elif rank_change < 0:
                    # 退步（排名下降）- 淺紅色背景 + 向下三角形
                    change_item.setText(f"{abs(rank_change)} ▼")  # 使用絕對值，更清楚
                    change_item.setBackground(QBrush(QColor(255, 200, 200)))  # 淺紅色
                    change_item.setForeground(QBrush(QColor(180, 0, 0)))  # 深紅色文字（與 Position 統一）
                else:
                    # 持平 - 淺灰色背景 + 橫線
                    change_item.setText("0 ━")
                    change_item.setBackground(QBrush(QColor(230, 230, 230)))  # 淺灰色（與 Position 統一）
                    change_item.setForeground(QBrush(QColor(100, 100, 100)))  # 深灰色文字
                
                change_item.setData(Qt.DisplayRole, rank_change)  # 用於排序
            else:
                # 沒有 Q 結果
                change_item = QTableWidgetItem("N/A")
                change_item.setBackground(QBrush(QColor(230, 230, 230)))  # 淺灰色背景（與 Position 統一）
                change_item.setForeground(QBrush(QColor(100, 100, 100)))  # 深灰色文字
                
                # ✅ 使用系統預設字體
                font = QFont()
                font.setPointSize(8)
                change_item.setFont(font)
            
            change_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 9, change_item)
            
        except Exception as e:
            logger.exception("❌ 設置行資料失敗 (row %s): %s", row, e)
    
    def _update_statistics_panel(self, metadata: Dict[str, Any], predictions: List[Dict[str, Any]]):
        """更新統計摘要面板"""
        try:
            # 總車手數
            total_drivers = len(predictions)
            self.lbl_total_drivers.setText(
                tr("total_drivers_value", "總車手數: {count}").format(count=total_drivers)
            )
            
            # 賽道資訊
            track = metadata.get("track", "N/A")
            year = metadata.get("year", 2025)
            self.lbl_track_info.setText(
                tr("track_info_value", "賽道: {track} {year}").format(track=track, year=year)
            )
            
            # ✅ 模型 R²（所有車手共用）
            model_r2 = metadata.get("model_r2", 0)
            sample_count = metadata.get("sample_count", 0)
            self.lbl_model_r2.setText(
                tr("model_r2_value", "🎯 模型 R²: {r2} (樣本數: {count})").format(
                    r2=f"{model_r2:.4f}",
                    count=sample_count
                )
            )
            
            # ✅ 模型 MAE（所有車手共用）
            model_mae = metadata.get("model_mae", 0)
            self.lbl_model_mae.setText(
                tr("model_mae_value", "📏 模型 MAE: {mae}s (平均誤差)").format(mae=f"{model_mae:.3f}")
            )
            
            # ✅ R² 說明（根據數值動態顯示）
            reliability_text = metadata.get("reliability_text", "")
            reliability_color = metadata.get("reliability_color", "black")
            
            if reliability_text:
                full_text = tr("r2_explanation", "💡 R² 說明: {text}").format(text=reliability_text)
                self.lbl_r2_explanation.setText(full_text)
                self.lbl_r2_explanation.setStyleSheet(f"color: {reliability_color}; font-weight: bold;")
            
        except Exception as e:
            logger.exception("❌ 更新統計面板失敗: %s", e)
    
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
        
        # ✅ 使用系統預設字體（8pt，無粗體）
        font = QFont()
        font.setPointSize(8)
        item.setFont(font)
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
    
    def clear_display(self):
        """清空顯示"""
        self.table.setRowCount(0)
        self._current_data = None
        
        # 重置統計標籤
        self.lbl_total_drivers.setText(tr("total_drivers_label", "總車手數: -"))
        self.lbl_track_info.setText(tr("track_info_label", "賽道: -"))
        self.lbl_model_r2.setText(tr("model_r2_label", "🎯 模型 R²: -"))
        self.lbl_model_mae.setText(tr("model_mae_label", "📏 模型 MAE: -"))
        self.lbl_r2_explanation.setText("")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前顯示的資料"""
        return self._current_data
