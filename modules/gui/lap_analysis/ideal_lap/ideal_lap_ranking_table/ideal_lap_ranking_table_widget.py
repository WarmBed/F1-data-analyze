#!/usr/bin/env python3
"""
理想圈排名表格元件
Ideal Lap Ranking Table Widget

負責顯示理想圈分析的排名表格，包含車手排名、理想圈、實際最速圈等資訊
支援排序、顏色編碼、Tooltip 等進階功能

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QLabel,
    QGridLayout, QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QColor, QFont, QBrush, QPainter
from typing import Dict, List, Any, Optional

from core.gui_i18n import tr, get_team_name_text
from core.logger import get_logger
from modules.gui.themes.color_palette_provider import color_palette_provider  # ✅ 使用通用顏色系統
from modules.gui.lap_analysis.ideal_lap.shared_colors import (
    get_gap_color,
    get_competitiveness_color,
)

logger = get_logger(__name__)


class SectorTimeDelegate(QStyledItemDelegate):
    """自訂 Delegate：雙列顯示最速與理想分段時間"""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        data = index.data(Qt.UserRole)

        painter.save()

        # 背景填色，支援選取狀態
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.palette.base())

        fastest_text = None
        ideal_text = None
        if isinstance(data, dict):
            fastest_text = data.get('fastest_text')
            ideal_text = data.get('ideal_text')

        rect = option.rect.adjusted(0, 4, 0, -4)
        fm = painter.fontMetrics()
        line_height = fm.height()

        lines = []
        if fastest_text:
            lines.append(('fastest', fastest_text))
        else:
            lines.append(('na', tr('na', 'N/A')))

        if ideal_text:
            lines.append(('ideal', ideal_text))

        total_height = line_height * len(lines)
        start_y = rect.y() + (rect.height() - total_height) / 2 + line_height - fm.descent()

        current_y = start_y
        for role, text in lines:
            if role == 'fastest':
                painter.setPen(QColor(0, 0, 0))
            elif role == 'ideal':
                painter.setPen(QColor(30, 90, 200))
            else:
                painter.setPen(QColor(120, 120, 120))

            self._draw_text_line(painter, rect, text, current_y)
            current_y += line_height

        painter.restore()

    def _draw_text_line(self, painter: QPainter, rect: QRect, text: str, baseline_y: float):
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        x = rect.x() + (rect.width() - text_width) / 2
        painter.drawText(int(x), int(baseline_y), text)

    def _draw_centered_text(self, painter: QPainter, rect: QRect, text: str):
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        x = rect.x() + (rect.width() - text_width) / 2
        y = rect.y() + (rect.height() + text_height) / 2 - fm.descent()
        painter.drawText(int(x), int(y), text)


class SectorMarksDelegate(QStyledItemDelegate):
    """
    自訂 Delegate：用於繪製混合顏色的分段標記
    - ✓ (綠色) = 該分段在最速圈中已經是最佳狀態
    - ✗ (黑色) = 該分段在最速圈中還有提升空間
    """
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """
        自訂繪製：逐字符繪製不同顏色
        """
        # 獲取文字內容
        text = index.data(Qt.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return
        
        # 啟用反鋸齒
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 設定字體（8pt，與其他欄位一致）
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # 計算文字區域（置中）
        text_rect = option.rect
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        
        # 計算起始 X 座標（置中）
        x = text_rect.x() + (text_rect.width() - text_width) // 2
        y = text_rect.y() + (text_rect.height() + text_height) // 2 - fm.descent()
        
        # 逐字符繪製
        for char in text:
            if char == "✓":
                painter.setPen(QColor(0, 150, 0))  # 綠色
            else:  # ✗
                painter.setPen(QColor(0, 0, 0))  # 黑色
            
            painter.drawText(x, y, char)
            x += fm.horizontalAdvance(char)  # 移動到下一個字符位置


class IdealLapRankingTableWidget(QWidget):
    """
    理想圈排名表格元件
    
    顯示所有車手的理想圈排名，包含：
    - 11 欄位表格（排名、車手、車隊、最速圈、理想圈、S1/S2/S3、差異等）
    - 車隊顏色編碼
    - 差異梯度顏色
    - 競爭力顏色
    - Tooltip 懸停資訊
    - 統計摘要面板
    """
    
    # 已移除 detail_requested 信號（Action 欄已移除）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 資料快取
        self._current_data = None
        self._ranking_data = []
        self._summary_data = {}
        
        # ✅ 移除本地車隊顏色定義，使用共用配置
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI 佈局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 1. 主表格
        self.table = self._create_table()
        layout.addWidget(self.table, 1)  # 給予彈性空間
        
        # 2. 統計摘要面板（移到下方）
        self.summary_panel = self._create_summary_panel()
        layout.addWidget(self.summary_panel)
    
    def _create_summary_panel(self) -> QGroupBox:
        """創建統計摘要面板"""
        panel = QGroupBox(tr('race_statistics_summary', '📊 賽事統計摘要'))
        panel.setMaximumHeight(150)
        
        grid_layout = QGridLayout()
        panel.setLayout(grid_layout)
        
        # 標籤字體
        label_font = QFont()
        label_font.setBold(True)
        
        # 行 1: 基本資訊
        self.lbl_total_drivers = self._create_stat_label(f"{tr('total_drivers', '總車手數')}: -", label_font)
        self.lbl_session_fastest = self._create_stat_label(f"{tr('session_fastest_lap', '全場最速實際圈')}: -", label_font)
        grid_layout.addWidget(self.lbl_total_drivers, 0, 0)
        grid_layout.addWidget(self.lbl_session_fastest, 0, 1)
        
        # 行 2: 理想圈統計
        self.lbl_fastest_ideal = self._create_stat_label(f"{tr('fastest_ideal_lap', '最快理想圈')}: -", label_font)
        self.lbl_ideal_range = self._create_stat_label(f"{tr('ideal_lap_range', '理想圈範圍')}: -", label_font)
        grid_layout.addWidget(self.lbl_fastest_ideal, 1, 0)
        grid_layout.addWidget(self.lbl_ideal_range, 1, 1)
        
        # 行 3: 潛力分析
        self.lbl_avg_gap = self._create_stat_label(f"{tr('average_gap', '平均差異')}: -", label_font)
        self.lbl_perfect_laps = self._create_stat_label(f"{tr('perfect_lap_rate', '完美單圈達成率')}: -", label_font)
        grid_layout.addWidget(self.lbl_avg_gap, 2, 0)
        grid_layout.addWidget(self.lbl_perfect_laps, 2, 1)
        
        return panel
    
    def _create_stat_label(self, text: str, font: QFont) -> QLabel:
        """創建統計標籤"""
        label = QLabel(text)
        label.setFont(font)
        return label
    
    def _create_table(self) -> QTableWidget:
        """創建主表格"""
        table = QTableWidget()
        
        # 設置欄位（新增車隊與分段資訊）
        columns = [
            tr('table_header_position', '排名'),           # 0: position
            tr('table_header_driver', '車手'),             # 1: driver (背景色)
            tr('table_header_team', '車隊'),               # 2: team
            tr('table_header_fastest_lap', '車手最速圈'),  # 3: fastest_lap_time
            tr('table_header_ideal_lap', '理想圈'),        # 4: ideal_lap_time
            tr('table_header_s1', 'S1'),                   # 5: sector 1
            tr('table_header_s2', 'S2'),                   # 6: sector 2
            tr('table_header_s3', 'S3'),                   # 7: sector 3
            tr('table_header_gap', '差異'),                # 8: time_gap (梯度顏色)
            tr('table_header_gap_to_fastest', '與全場最速差距'),  # 9: gap_to_session_fastest
            tr('table_header_sector_breakdown', '分段')    # 10: sector_breakdown
        ]
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 設置表格屬性
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # ✅ 禁用選擇功能
        table.setSelectionMode(QAbstractItemView.NoSelection)
        
        # 設置欄位寬度（11 欄）
        table.setColumnWidth(0, 60)   # 排名
        table.setColumnWidth(1, 100)  # 車手（套用車隊顏色）
        table.setColumnWidth(2, 130)  # 車隊
        table.setColumnWidth(3, 120)  # 車手最速圈
        table.setColumnWidth(4, 120)  # 理想圈
        table.setColumnWidth(5, 110)  # S1
        table.setColumnWidth(6, 110)  # S2
        table.setColumnWidth(7, 110)  # S3
        table.setColumnWidth(8, 100)  # 差異
        table.setColumnWidth(9, 150)  # 與全場最速差距
        table.setColumnWidth(10, 90)  # 分段

        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)  # 最後一欄自動伸展

        # ✅ 為分段時間欄位設置自訂 Delegate
        self._sector_time_delegate = SectorTimeDelegate(table)
        for col in (5, 6, 7):
            table.setItemDelegateForColumn(col, self._sector_time_delegate)

        # ✅ 為 Sectors 欄位（第 10 欄）設置自訂 Delegate
        self._sector_marks_delegate = SectorMarksDelegate(table)
        table.setItemDelegateForColumn(10, self._sector_marks_delegate)
        
        # ✅ 隱藏排名欄位（第 0 欄）
        table.setColumnHidden(0, True)
        
        return table
    
    # ========== 公開方法 ==========
    
    def populate_table(self, ranking_data: List[Dict[str, Any]]):
        """
        填充表格資料
        
        Args:
            ranking_data: 車手排名資料列表
        """
        try:
            self._ranking_data = ranking_data
            row_count = len(ranking_data)
            
            self.table.setSortingEnabled(False)  # 暫時禁用排序以提高效能
            self.table.setRowCount(row_count)
            
            for row, driver in enumerate(ranking_data):
                self._set_row_data(row, driver)
            
            self.table.setSortingEnabled(True)  # 重新啟用排序
            logger.info(f"[TABLE_WIDGET] ✅ 已載入 {row_count} 位車手")
            
        except Exception as e:
            logger.error(f"{tr('table_populate_failed', '[TABLE_WIDGET] 填充表格失敗')}: {e}")
            import traceback
            traceback.print_exc()
    
    def update_statistics_panel(self, summary_data: Dict[str, Any]):
        """
        更新統計摘要面板
        
        Args:
            summary_data: 統計資料字典
        """
        try:
            self._summary_data = summary_data
            
            # 更新標籤
            total_drivers = summary_data.get("total_drivers", 20)
            self.lbl_total_drivers.setText(f"{tr('total_drivers', '總車手數')}: {total_drivers}")
            
            # 全場最速實際圈
            session_fastest = summary_data.get("session_fastest_lap")
            session_fastest_driver = summary_data.get("session_fastest_driver", tr('na', 'N/A'))
            session_fastest_lap_num = summary_data.get("session_fastest_lap_number", "")
            if session_fastest:
                fastest_text = f"{tr('session_fastest_lap', '全場最速實際圈')}: {self._format_time(session_fastest)}"
                if session_fastest_driver != tr('na', 'N/A'):
                    fastest_text += f" ({session_fastest_driver}"
                    if session_fastest_lap_num:
                        fastest_text += f" L{session_fastest_lap_num}"
                    fastest_text += ")"
                self.lbl_session_fastest.setText(fastest_text)
            else:
                self.lbl_session_fastest.setText(f"{tr('session_fastest_lap', '全場最速實際圈')}: {tr('na', 'N/A')}")
            
            # 最快理想圈（支援新舊兩種格式）
            fastest_ideal_info = summary_data.get("fastest_ideal_lap")
            if isinstance(fastest_ideal_info, dict):
                # 新格式：{"time": 94.183, "driver": "VER"}
                fastest_ideal_time = fastest_ideal_info.get("time")
                fastest_ideal_driver = fastest_ideal_info.get("driver", tr('na', 'N/A'))
                if fastest_ideal_time:
                    self.lbl_fastest_ideal.setText(
                        f"{tr('fastest_ideal_lap', '最快理想圈')}: {self._format_time(fastest_ideal_time)} ({fastest_ideal_driver})"
                    )
            elif isinstance(fastest_ideal_info, (int, float)):
                # 舊格式：直接是數字
                self.lbl_fastest_ideal.setText(
                    f"{tr('fastest_ideal_lap', '最快理想圈')}: {self._format_time(fastest_ideal_info)}"
                )
            else:
                self.lbl_fastest_ideal.setText(f"{tr('fastest_ideal_lap', '最快理想圈')}: {tr('na', 'N/A')}")
            
            # 理想圈範圍（支援新舊兩種格式）
            ideal_range = summary_data.get("ideal_lap_range")
            if isinstance(ideal_range, dict):
                # 新格式：{"range_seconds": 7.927, "fastest": 94.183, "slowest": 102.11}
                range_seconds = ideal_range.get("range_seconds", 0)
                fastest_time = ideal_range.get("fastest")
                slowest_time = ideal_range.get("slowest")
                range_text = f"{tr('ideal_lap_range', '理想圈範圍')}: {range_seconds:.3f}s"
                if fastest_time and slowest_time:
                    range_text += f" ({self._format_time(fastest_time)} ~ {self._format_time(slowest_time)})"
                self.lbl_ideal_range.setText(range_text)
            elif isinstance(ideal_range, (int, float)):
                # 舊格式：ideal_lap_spread
                ideal_spread = summary_data.get("ideal_lap_spread", ideal_range)
                self.lbl_ideal_range.setText(f"{tr('ideal_lap_range', '理想圈範圍')}: {ideal_spread:.3f}s")
            else:
                self.lbl_ideal_range.setText(f"{tr('ideal_lap_range', '理想圈範圍')}: {tr('na', 'N/A')}")
            
            # 平均差異
            avg_gap = summary_data.get("average_gap", 0)
            self.lbl_avg_gap.setText(f"{tr('average_gap', '平均差異')}: {avg_gap:.3f}s")
            
            # 完美單圈達成率
            perfect_rate = summary_data.get("perfect_lap_rate", "0/20")
            self.lbl_perfect_laps.setText(f"{tr('perfect_lap_rate', '完美單圈達成率')}: {perfect_rate}")
            
        except Exception as e:
            logger.error(f"{tr('statistics_update_failed', '[TABLE_WIDGET] 更新統計面板失敗')}: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_table(self):
        """清空表格"""
        self.table.setRowCount(0)
        self._ranking_data = []
        logger.debug("[TABLE_WIDGET] 表格已清空")
    
    # ========== 私有方法 ==========
    
    def _set_row_data(self, row: int, driver: Dict[str, Any]):
        """
        設置單行資料
        
        Args:
            row: 行號
            driver: 車手資料字典
        """
        try:
            # 0. 排名
            pos_item = QTableWidgetItem()
            pos_item.setData(Qt.DisplayRole, int(driver.get("position", 0)))
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, pos_item)
            
            # 1. 車手（套用車手背景色，自動選擇文字顏色）
            driver_code = driver.get("driver", "N/A")
            team = driver.get("team", "Unknown")
            driver_color = self._get_driver_color(driver_code)
            driver_item = self._create_colored_item(driver_code, driver_color)
            # ✅ 使用多國語言翻譯的車隊名稱
            team_translated = get_team_name_text(team)
            driver_item.setToolTip(f"{driver_code} - {team_translated}")
            self.table.setItem(row, 1, driver_item)
            
            # 2. 車隊（套用車手背景色，自動選擇文字顏色，使用多國語言翻譯）
            team_item = self._create_colored_item(team_translated, driver_color)
            team_item.setToolTip(team_translated)
            self.table.setItem(row, 2, team_item)

            # 3. 車手最速圈
            fastest_lap = driver.get("fastest_lap_time")
            fastest_lap_item = QTableWidgetItem(self._format_time(fastest_lap))
            fastest_lap_item.setTextAlignment(Qt.AlignCenter)
            # 設置 Tooltip
            if fastest_lap:
                fastest_lap_item.setToolTip(self._create_fastest_lap_tooltip(driver))
            self.table.setItem(row, 3, fastest_lap_item)
            
            # 4. 理想圈
            ideal_lap = driver.get("ideal_lap_time")
            ideal_lap_item = QTableWidgetItem(self._format_time(ideal_lap))
            ideal_lap_item.setTextAlignment(Qt.AlignCenter)
            # 設置 Tooltip
            if ideal_lap:
                ideal_lap_item.setToolTip(self._create_ideal_lap_tooltip(driver))
            self.table.setItem(row, 4, ideal_lap_item)

            # 5-7. 分段最佳 vs 理想
            sector_breakdown = driver.get("sector_breakdown", {})
            for col_index, sector_num in enumerate([1, 2, 3], start=5):
                sector_item = self._create_sector_item(sector_breakdown, sector_num)
                self.table.setItem(row, col_index, sector_item)
            
            # 8. 差異（套用梯度顏色）
            gap = driver.get("time_gap", 0)
            gap_item = QTableWidgetItem()
            gap_item.setData(Qt.DisplayRole, gap)  # 用於排序
            gap_item.setText(f"+{gap:.3f}s" if gap > 0 else f"{gap:.3f}s")
            gap_item.setTextAlignment(Qt.AlignCenter)
            gap_item.setBackground(self._get_gap_color(gap))
            # 設置 Tooltip
            gap_item.setToolTip(self._create_gap_tooltip(gap, ideal_lap, fastest_lap))
            self.table.setItem(row, 8, gap_item)
            
            # 9. 與全場最速差距（套用統一顏色標準）
            gap_to_fastest = driver.get("gap_to_session_fastest")
            if gap_to_fastest is not None:
                gap_fastest_item = QTableWidgetItem()
                gap_fastest_item.setData(Qt.DisplayRole, gap_to_fastest)
                gap_fastest_item.setText(f"+{gap_to_fastest:.3f}s")
                gap_fastest_item.setTextAlignment(Qt.AlignCenter)
                # ✅ 修正：使用統一的 gap_color 標準，而非 competitiveness_color
                gap_fastest_item.setBackground(self._get_gap_color(gap_to_fastest))
                self.table.setItem(row, 9, gap_fastest_item)
            else:
                gap_fastest_item = QTableWidgetItem(tr('na', 'N/A'))
                gap_fastest_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 9, gap_fastest_item)
            
            # 10. 分段標記（打勾綠色，XX 黑色）
            sector_marks = self._get_sector_marks(sector_breakdown)
            sector_item = QTableWidgetItem(sector_marks)
            sector_item.setTextAlignment(Qt.AlignCenter)
            # ✅ Delegate 會自動處理顏色繪製，不需要 setForeground
            self.table.setItem(row, 10, sector_item)
            
            # 已移除操作按鈕（Action 欄）
            
        except Exception as e:
            logger.error(f"{tr('set_row_data_failed', '[TABLE_WIDGET] 設置行資料失敗')} (row {row}): {e}")
            import traceback
            traceback.print_exc()
    
    def _format_time(self, seconds: Optional[float]) -> str:
        """
        格式化時間為 MM:SS.mmm
        
        Args:
            seconds: 秒數
            
        Returns:
            str: 格式化後的時間字串
        """
        if seconds is None:
            return tr('na', 'N/A')
        
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """
        獲取車手顏色（使用通用顏色系統）
        
        Args:
            driver_code: 車手代碼（例如: "VER", "HAM"）
            
        Returns:
            QColor: 車手顏色
        """
        return color_palette_provider.get_driver_color(driver_code, fallback=True)
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """
        創建帶背景色的表格項目，自動選擇文字顏色
        
        Args:
            text: 顯示文字
            bg_color: 背景顏色
            
        Returns:
            QTableWidgetItem: 帶顏色的表格項目
        """
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        # 根據背景色亮度決定文字顏色
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _get_gap_color(self, gap: float) -> QColor:
        """根據差異返回梯度顏色（使用共用配置）"""
        return get_gap_color(gap)
    
    def _get_competitiveness_color(self, gap: float) -> QColor:
        """根據與全場最速差距返回競爭力顏色（使用共用配置）"""
        return get_competitiveness_color(gap)
    
    def _get_sector_marks(self, sector_breakdown: Dict[str, Any]) -> str:
        """
        生成分段標記符號
        
        Args:
            sector_breakdown: 分段詳情
            
        Returns:
            str: 標記符號 (例如: "✓✗✗")
            ✓ = 該分段在最速圈中已經是最佳狀態
            ✗ = 該分段在最速圈中還有提升空間（理想圈取自其他圈）
        """
        # 檢查每個分段是否在最速圈中已是最佳
        marks = []
        for sector_num in [1, 2, 3]:
            sector_key = f"sector_{sector_num}"
            if sector_key in sector_breakdown:
                sector_info = sector_breakdown[sector_key]
                # 修復：使用正確的欄位名稱 "is_optimal_in_fastest"
                if isinstance(sector_info, dict):
                    is_optimal = sector_info.get("is_optimal_in_fastest", False)
                    marks.append("✓" if is_optimal else "✗")
                else:
                    marks.append("✗")
            else:
                marks.append("✗")
        
        return "".join(marks)
    
    def _create_sector_item(self, sector_breakdown: Dict[str, Any], sector_num: int) -> QTableWidgetItem:
        """建立單一分段的表格項目"""
        sector_key = f"sector_{sector_num}"
        sector_info = sector_breakdown.get(sector_key, {})
        fastest_time = None
        ideal_time = None
        if isinstance(sector_info, dict):
            fastest_time = sector_info.get("fastest_time")
            ideal_time = sector_info.get("ideal_time", sector_info.get("time"))

        fastest_text = self._format_sector_time(fastest_time) if fastest_time is not None else None
        ideal_text = self._format_sector_time(ideal_time) if ideal_time is not None else None

        item = QTableWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setText("")
        # 依據最速圈排序，若不存在則置於末端
        sort_value = fastest_time if fastest_time is not None else float('inf')
        item.setData(Qt.DisplayRole, sort_value)
        item.setData(Qt.UserRole, {
            'fastest_text': fastest_text,
            'ideal_text': ideal_text
        })
        item.setTextAlignment(Qt.AlignCenter)

        tooltip_lines = []
        if fastest_text is not None:
            tooltip_lines.append(
                f"{tr('sector_label_best', '最佳')}: {fastest_text}"
            )
        if ideal_text is not None:
            tooltip_lines.append(
                f"{tr('sector_label_ideal', '理想')}: {ideal_text}"
            )
        if not tooltip_lines:
            tooltip_lines.append(tr('na', 'N/A'))
        item.setToolTip("\n".join(tooltip_lines))
        return item

    def _format_sector_time(self, seconds: Optional[float]) -> str:
        """格式化分段時間（固定顯示秒數）"""
        if seconds is None:
            return tr('na', 'N/A')
        return f"{seconds:.3f}"
    
    def _create_fastest_lap_tooltip(self, driver: Dict[str, Any]) -> str:
        """創建車手最速圈的 Tooltip"""
        fastest_lap = driver.get("fastest_lap_time")
        if not fastest_lap:
            return tr('tooltip_no_fastest_lap_data', '無最速圈資料')
        
        # 找到最速圈的圈數
        fastest_lap_num = None
        if "laps" in driver and isinstance(driver["laps"], list):
            for lap in driver["laps"]:
                if lap.get("lap_time_seconds") == fastest_lap:
                    fastest_lap_num = lap.get("lap_number")
                    break
        
        if fastest_lap_num:
            return tr('tooltip_fastest_lap_with_number', '最速圈: {time} (Lap {lap_num})').format(
                time=self._format_time(fastest_lap),
                lap_num=fastest_lap_num
            )
        else:
            return tr('tooltip_fastest_lap', '最速圈: {time}').format(
                time=self._format_time(fastest_lap)
            )
    
    def _create_gap_tooltip(self, gap: Optional[float], ideal_lap: Optional[float], fastest_lap: Optional[float]) -> str:
        """創建差異欄位的 Tooltip"""
        if gap is None:
            return tr('tooltip_gap_cannot_calculate', '無法計算差異')

        tooltip_lines = []

        percentage = 0.0
        if fastest_lap:
            percentage = (gap / fastest_lap) * 100 if fastest_lap else 0
            tooltip_lines.append(
                tr('tooltip_gap_value', '差異: +{gap}s (+{percentage}%)').format(
                    gap=f"{gap:.3f}",
                    percentage=f"{percentage:.2f}"
                )
            )
        else:
            tooltip_lines.append(
                tr('tooltip_gap_value', '差異: +{gap}s (+{percentage}%)').format(
                    gap=f"{gap:.3f}",
                    percentage="N/A"
                )
            )

        if fastest_lap:
            tooltip_lines.append(
                tr('tooltip_fastest_lap', '最速圈: {time}').format(
                    time=self._format_time(fastest_lap)
                )
            )

        if ideal_lap:
            tooltip_lines.append(
                tr('tooltip_ideal_lap', '理想圈: {time}').format(
                    time=self._format_time(ideal_lap)
                )
            )

        if gap < 0.2:
            tooltip_lines.append(tr('tooltip_gap_near_perfect', '評估: 接近完美單圈'))
        elif gap < 0.5:
            tooltip_lines.append(tr('tooltip_gap_moderate', '評估: 有中等提升空間'))
        else:
            tooltip_lines.append(tr('tooltip_gap_significant', '評估: 有明顯改善空間'))

        return "\n".join(tooltip_lines)

    def _create_ideal_lap_tooltip(self, driver: Dict[str, Any]) -> str:
        """創建理想圈的 Tooltip"""
        ideal_lap = driver.get("ideal_lap_time")
        if not ideal_lap:
            return tr('tooltip_no_ideal_lap_data', '無理想圈資料')
        
        tooltip_lines = [tr('tooltip_ideal_lap', '理想圈: {time}').format(time=self._format_time(ideal_lap))]
        
        # 顯示分段來源
        ideal_detail = driver.get("ideal_lap_detail", {})
        if isinstance(ideal_detail, dict):
            sector_sources = ideal_detail.get("sector_sources", {})
            for sector_num in [1, 2, 3]:
                sector_info = None
                if isinstance(sector_sources, dict):
                    sector_info = sector_sources.get(f"s{sector_num}")
                if sector_info is None:
                    sector_info = ideal_detail.get(f"sector_{sector_num}")
                if not isinstance(sector_info, dict):
                    continue
                sector_time = sector_info.get("time")
                lap_number = sector_info.get("lap")
                if sector_time is None:
                    continue
                tooltip_lines.append(
                    tr('tooltip_sector_detail', 'S{sector_num}: {time}s (Lap {lap_num})').format(
                        sector_num=sector_num,
                        time=self._format_sector_time(sector_time),
                        lap_num=lap_number if lap_number is not None else tr('na', 'N/A')
                    )
                )

        gap = driver.get("time_gap")
        fastest_lap = driver.get("fastest_lap_time")
        if gap is not None:
            if fastest_lap:
                percentage = (gap / fastest_lap) * 100 if fastest_lap else 0
                tooltip_lines.append(
                    tr('tooltip_gap_value', '差異: +{gap}s (+{percentage}%)').format(
                        gap=f"{gap:.3f}",
                        percentage=f"{percentage:.2f}"
                    )
                )
            else:
                tooltip_lines.append(
                    tr('tooltip_gap_value', '差異: +{gap}s (+{percentage}%)').format(
                        gap=f"{gap:.3f}",
                        percentage="N/A"
                    )
                )

            if gap < 0.2:
                assessment = tr('tooltip_gap_near_perfect', '評估: 接近完美單圈')
            elif gap < 0.5:
                assessment = tr('tooltip_gap_moderate', '評估: 有中等提升空間')
            else:
                assessment = tr('tooltip_gap_significant', '評估: 有明顯改善空間')
            tooltip_lines.append(assessment)
        else:
            tooltip_lines.append(tr('tooltip_gap_cannot_calculate', '無法計算差異'))
        
        return "\n".join(tooltip_lines)
    
    # ========== 事件處理 ==========
    


# ========== 測試代碼 ==========
if __name__ == "__main__":
    import sys
    import json
    from PyQt5.QtWidgets import QApplication
    
    logger.debug("=" * 60)
    logger.debug("理想圈排名表格元件 - 獨立測試")
    logger.debug("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建元件
    widget = IdealLapRankingTableWidget()
    widget.setWindowTitle("Ideal Lap Ranking Table - Test")
    widget.resize(1400, 900)
    widget.show()
    
    # 載入測試資料
    try:
        json_path = "json/ideal_lap_ranking_2025_Japan_R.json"
        logger.debug(f"\n📂 載入測試資料: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "analysis_result" in data:
            ranking = data["analysis_result"]["ranking"]
            summary = data["analysis_result"]["summary"]
            
            logger.info(f"資料載入成功")
            logger.debug(f"   車手數: {len(ranking)}")
            
            # 填充表格
            widget.populate_table(ranking)
            widget.update_statistics_panel(summary)
            
            logger.info(f"表格已填充")
        else:
            logger.error("JSON 結構不正確")
    
    except FileNotFoundError:
        logger.error(f"找不到測試資料檔案: {json_path}")
        logger.debug("💡 提示: 請先執行 CLI 生成資料")
    except Exception as e:
        logger.error(f"測試失敗: {e}")
        import traceback

        traceback.print_exc()
    
    sys.exit(app.exec_())
