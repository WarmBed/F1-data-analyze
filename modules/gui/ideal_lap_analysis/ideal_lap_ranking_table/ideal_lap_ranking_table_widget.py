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
    QGridLayout, QStyledItemDelegate, QStyleOptionViewItem
)
from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QColor, QFont, QBrush, QPainter
from typing import Dict, List, Any, Optional

# 導入翻譯系統
try:
    from core.gui_i18n import tr
except ImportError:
    # 降級方案：如果找不到翻譯系統，使用預設英文
    def tr(key, default=None):
        return default if default else key

# ✅ 導入共用顏色配置
try:
    from ..shared_colors import get_gap_color, get_team_color, get_competitiveness_color, TEAM_COLORS
except ImportError:
    from modules.gui.ideal_lap_analysis.shared_colors import get_gap_color, get_team_color, get_competitiveness_color, TEAM_COLORS


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
    - 10 欄位表格（排名、車手、車隊、最速圈、理想圈、差異等）
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
        
        # 設置欄位（已移除「車隊」和「操作」欄位）
        columns = [
            tr('table_header_position', '排名'),           # 0: position
            tr('table_header_driver', '車手'),             # 1: driver (背景色)
            tr('table_header_fastest_lap', '車手最速圈'),  # 2: fastest_lap_time
            tr('table_header_ideal_lap', '理想圈'),        # 3: ideal_lap_time
            tr('table_header_gap', '差異'),                # 4: time_gap (梯度顏色)
            tr('table_header_gap_to_fastest', '與全場最速差距'),  # 5: gap_to_session_fastest
            tr('table_header_sector_breakdown', '分段')    # 6: sector_breakdown
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
        
        # 設置欄位寬度（7 欄：已移除 Team 欄與 Action 欄）
        table.setColumnWidth(0, 60)   # 排名
        table.setColumnWidth(1, 100)  # 車手（加寬以顯示車隊顏色）
        table.setColumnWidth(2, 120)  # 車手最速圈
        table.setColumnWidth(3, 120)  # 理想圈
        table.setColumnWidth(4, 100)  # 差異
        table.setColumnWidth(5, 150)  # 與全場最速差距
        table.setColumnWidth(6, 90)   # 分段
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)  # 最後一欄自動伸展
        
        # ✅ 為 Sectors 欄位（第 6 欄）設置自訂 Delegate
        table.setItemDelegateForColumn(6, SectorMarksDelegate(table))
        
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
            print(f"[TABLE_WIDGET] ✅ 已載入 {row_count} 位車手")
            
        except Exception as e:
            print(f"❌ {tr('table_populate_failed', '[TABLE_WIDGET] 填充表格失敗')}: {e}")
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
            print(f"❌ {tr('statistics_update_failed', '[TABLE_WIDGET] 更新統計面板失敗')}: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_table(self):
        """清空表格"""
        self.table.setRowCount(0)
        self._ranking_data = []
        print("[TABLE_WIDGET] 表格已清空")
    
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
            
            # 1. 車手（套用車隊背景色，顯示車隊名稱在 Tooltip）
            driver_code = driver.get("driver", "N/A")
            team = driver.get("team", "Unknown")
            driver_item = QTableWidgetItem(driver_code)
            driver_item.setTextAlignment(Qt.AlignCenter)
            driver_item.setBackground(self._get_team_color(team))
            # 設置前景色為黑色以提高可讀性
            driver_item.setForeground(QBrush(QColor(0, 0, 0)))
            # 車隊名稱顯示在 Tooltip
            driver_item.setToolTip(f"{driver_code} - {team}")
            self.table.setItem(row, 1, driver_item)
            
            # 2. 車手最速圈
            fastest_lap = driver.get("fastest_lap_time")
            fastest_lap_item = QTableWidgetItem(self._format_time(fastest_lap))
            fastest_lap_item.setTextAlignment(Qt.AlignCenter)
            # 設置 Tooltip
            if fastest_lap:
                fastest_lap_item.setToolTip(self._create_fastest_lap_tooltip(driver))
            self.table.setItem(row, 2, fastest_lap_item)
            
            # 3. 理想圈
            ideal_lap = driver.get("ideal_lap_time")
            ideal_lap_item = QTableWidgetItem(self._format_time(ideal_lap))
            ideal_lap_item.setTextAlignment(Qt.AlignCenter)
            # 設置 Tooltip
            if ideal_lap:
                ideal_lap_item.setToolTip(self._create_ideal_lap_tooltip(driver))
            self.table.setItem(row, 3, ideal_lap_item)
            
            # 4. 差異（套用梯度顏色）
            gap = driver.get("time_gap", 0)
            gap_item = QTableWidgetItem()
            gap_item.setData(Qt.DisplayRole, gap)  # 用於排序
            gap_item.setText(f"+{gap:.3f}s" if gap > 0 else f"{gap:.3f}s")
            gap_item.setTextAlignment(Qt.AlignCenter)
            gap_item.setBackground(self._get_gap_color(gap))
            # 設置 Tooltip
            gap_item.setToolTip(self._create_gap_tooltip(gap, ideal_lap, fastest_lap))
            self.table.setItem(row, 4, gap_item)
            
            # 5. 與全場最速差距（套用統一顏色標準）
            gap_to_fastest = driver.get("gap_to_session_fastest")
            if gap_to_fastest is not None:
                gap_fastest_item = QTableWidgetItem()
                gap_fastest_item.setData(Qt.DisplayRole, gap_to_fastest)
                gap_fastest_item.setText(f"+{gap_to_fastest:.3f}s")
                gap_fastest_item.setTextAlignment(Qt.AlignCenter)
                # ✅ 修正：使用統一的 gap_color 標準，而非 competitiveness_color
                gap_fastest_item.setBackground(self._get_gap_color(gap_to_fastest))
                self.table.setItem(row, 5, gap_fastest_item)
            else:
                gap_fastest_item = QTableWidgetItem("N/A")
                gap_fastest_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 5, gap_fastest_item)
            
            # 6. 分段標記（打勾綠色，XX 黑色）
            sector_marks = self._get_sector_marks(driver.get("sector_breakdown", {}))
            sector_item = QTableWidgetItem(sector_marks)
            sector_item.setTextAlignment(Qt.AlignCenter)
            # ✅ Delegate 會自動處理顏色繪製，不需要 setForeground
            self.table.setItem(row, 6, sector_item)
            
            # 已移除操作按鈕（Action 欄）
            
        except Exception as e:
            print(f"❌ {tr('set_row_data_failed', '[TABLE_WIDGET] 設置行資料失敗')} (row {row}): {e}")
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
    
    def _get_team_color(self, team: str) -> QColor:
        """獲取車隊顏色（使用共用配置）"""
        return get_team_color(team)
    
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
    
    def _create_ideal_lap_tooltip(self, driver: Dict[str, Any]) -> str:
        """創建理想圈的 Tooltip"""
        ideal_lap = driver.get("ideal_lap_time")
        if not ideal_lap:
            return tr('tooltip_no_ideal_lap_data', '無理想圈資料')
        
        tooltip_lines = [tr('tooltip_ideal_lap', '理想圈: {time}').format(time=self._format_time(ideal_lap))]
        
        # 顯示分段來源
        ideal_detail = driver.get("ideal_lap_detail", {})
        if isinstance(ideal_detail, dict):
            for sector_num in [1, 2, 3]:
                sector_key = f"sector_{sector_num}"
                if sector_key in ideal_detail:
                    sector_info = ideal_detail[sector_key]
                    if isinstance(sector_info, dict):
                        sector_time = sector_info.get("time", 0)
                        sector_lap = sector_info.get("lap_number", tr('na', 'N/A'))
                        tooltip_lines.append(
                            tr('tooltip_sector_detail', 'S{sector_num}: {time}s (Lap {lap_num})').format(
                                sector_num=sector_num,
                                time=f"{sector_time:.3f}",
                                lap_num=sector_lap
                            )
                        )
        
        return "\n".join(tooltip_lines)
    
    def _create_gap_tooltip(self, gap: float, ideal_lap: float, fastest_lap: float) -> str:
        """創建差異的 Tooltip"""
        if ideal_lap is None or fastest_lap is None:
            return tr('tooltip_gap_cannot_calculate', '無法計算差異')
        
        percentage = (gap / ideal_lap) * 100 if ideal_lap > 0 else 0
        
        tooltip_lines = [
            tr('tooltip_gap_value', '差異: +{gap}s (+{percentage}%)').format(
                gap=f"{gap:.3f}",
                percentage=f"{percentage:.2f}"
            )
        ]
        
        # 評估
        if gap < 0.2:
            assessment = tr('tooltip_gap_near_perfect', '評估: 接近完美單圈')
        elif gap < 0.5:
            assessment = tr('tooltip_gap_moderate', '評估: 有中等提升空間')
        else:
            assessment = tr('tooltip_gap_significant', '評估: 有明顯改善空間')
        
        tooltip_lines.append(assessment)
        
        return "\n".join(tooltip_lines)
    
    # ========== 事件處理 ==========
    


# ========== 測試代碼 ==========
if __name__ == "__main__":
    import sys
    import json
    from PyQt5.QtWidgets import QApplication
    
    print("=" * 60)
    print("理想圈排名表格元件 - 獨立測試")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建元件
    widget = IdealLapRankingTableWidget()
    widget.setWindowTitle("Ideal Lap Ranking Table - Test")
    widget.resize(1400, 900)
    widget.show()
    
    # 載入測試資料
    try:
        json_path = "json/ideal_lap_ranking_2025_Japan_R.json"
        print(f"\n📂 載入測試資料: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "analysis_result" in data:
            ranking = data["analysis_result"]["ranking"]
            summary = data["analysis_result"]["summary"]
            
            print(f"✅ 資料載入成功")
            print(f"   車手數: {len(ranking)}")
            
            # 填充表格
            widget.populate_table(ranking)
            widget.update_statistics_panel(summary)
            
            print(f"✅ 表格已填充")
        else:
            print("❌ JSON 結構不正確")
    
    except FileNotFoundError:
        print(f"❌ 找不到測試資料檔案: {json_path}")
        print("💡 提示: 請先執行 CLI 生成資料")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(app.exec_())
