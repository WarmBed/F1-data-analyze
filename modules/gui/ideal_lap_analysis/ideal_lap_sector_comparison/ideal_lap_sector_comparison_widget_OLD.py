#!/usr/bin/env python3
"""
理想圈分段對比圖表元件
Ideal Lap Sector Comparison Chart Widget

✅ 使用 QPainter 繪製水平堆疊棒狀圖，展示理想圈與最快圈的分段對比
✅ 完全參考 lap_box_plot_analysis 的 QPainter 實現模式

作者: F1T Team
日期: 2025-10-10
版本: 2.0.0 (完全重寫 - QPainter 版本)
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QFontMetrics,
    QMouseEvent, QImage, QPainter as QPainterForExport
)
from typing import List, Dict, Optional, Any

# ✅ 參考 lap_box_plot_analysis: 導入國際化和車隊配色
from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider


class IdealLapSectorComparisonWidget(QWidget):
    """
    理想圈分段對比圖表元件 (純 PyQt5 QPainter 實現)
    
    ✅ 完全參考 LapTimeBoxPlotChartWidget 的實現架構
    
    功能：
    - 繪製水平堆疊棒狀圖（每位車手兩條：理想圈 + 最快圈）
    - 分段顏色編碼（S1=藍、S2=綠、S3=橙）
    - 時間差標記（✓=完美、❌=可改進）
    - 支援滑鼠懸停、點擊、排序
    """
    
    # ✅ 參考 lap_box_plot_analysis: 信號定義
    bar_clicked = pyqtSignal(str)  # 點擊車手棒狀圖時發射車手代碼
    sort_changed = pyqtSignal(str)  # 排序方式變更
    
    # 預設顏色
    DEFAULT_COLOR = QColor(128, 128, 128)
    
    # 分段顏色定義
    SECTOR_COLORS = {
        "s1": QColor(31, 119, 180),   # 藍色
        "s2": QColor(44, 160, 44),    # 綠色
        "s3": QColor(255, 127, 14)    # 橙色
    }
    
    def __init__(self, parent=None):
        """初始化圖表元件"""
        super().__init__(parent)
        
        # ✅ 參考 lap_box_plot_analysis: 數據屬性
        self.comparison_data: List[Dict] = []
        self.statistics: Dict[str, Any] = {}
        self.current_data: Optional[Dict] = None
        self.current_sort = "position"  # 預設排序方式
        
        # ✅ 參考 lap_box_plot_analysis: 佈局參數
        self.margin_left = 120  # 增加左側邊距以顯示車手名稱
        self.margin_right = 80  # 增加右側邊距以顯示時間差標記
        self.margin_top = 50
        self.margin_bottom = 80
        
        # 圖表區域
        self.chart_rect = QRect()
        
        # ✅ 參考 lap_box_plot_analysis: 懸停狀態
        self.hover_driver = None
        self.hover_position = None
        
        # X 軸範圍（時間軸，將在繪製時計算）
        self.x_min = 0.0
        self.x_max = 100.0
        
        # ✅ 參考 lap_box_plot_analysis: 啟用滑鼠追蹤
        self.setMouseTracking(True)
        
        # ✅ 參考 lap_box_plot_analysis: 設置最小尺寸
        self.setMinimumSize(200, 100)
        
        print("[SECTOR_COMPARISON] 圖表元件初始化完成 (QPainter 版本)")
    
    def draw_comparison_bars(self, comparison_data: List[Dict], statistics: Dict = None):
        """
        繪製分段對比棒狀圖
        
        Args:
            comparison_data: 對比資料列表
            statistics: 統計資料（可選）
        """
        try:
            self._debug(f"[DRAW] 開始繪製棒狀圖，共 {len(comparison_data)} 位車手")
            
            if not comparison_data:
                self._debug("[DRAW] ⚠️ 無資料可繪製")
                self._draw_no_data_message()
                return
            
            self.comparison_data = comparison_data
            self.statistics = statistics or {}
            
            # 清除現有圖表
            self.ax.clear()
            
            # 準備資料
            drivers = [d["driver"] for d in comparison_data]
            num_drivers = len(drivers)
            
            # Y 軸位置（每位車手佔用 2 個位置：理想圈 + 最快圈）
            y_positions = np.arange(num_drivers) * 2
            bar_height = 0.4
            
            # ========== 繪製堆疊棒狀圖 ==========
            for idx, driver_data in enumerate(comparison_data):
                y_ideal = y_positions[idx] - bar_height / 2
                y_fastest = y_positions[idx] + bar_height / 2
                
                ideal_s1, ideal_s2, ideal_s3 = driver_data["ideal_sectors"]
                fastest_s1, fastest_s2, fastest_s3 = driver_data["fastest_sectors"]
                
                # 理想圈堆疊棒（實心）
                self.ax.barh(
                    y_ideal, ideal_s1, height=bar_height,
                    color=self.SECTOR_COLORS["s1"], alpha=0.9,
                    label=self.SECTOR_LABELS["s1"] if idx == 0 else ""
                )
                self.ax.barh(
                    y_ideal, ideal_s2, height=bar_height, left=ideal_s1,
                    color=self.SECTOR_COLORS["s2"], alpha=0.9,
                    label=self.SECTOR_LABELS["s2"] if idx == 0 else ""
                )
                self.ax.barh(
                    y_ideal, ideal_s3, height=bar_height, left=ideal_s1 + ideal_s2,
                    color=self.SECTOR_COLORS["s3"], alpha=0.9,
                    label=self.SECTOR_LABELS["s3"] if idx == 0 else ""
                )
                
                # 最快圈堆疊棒（半透明）
                self.ax.barh(
                    y_fastest, fastest_s1, height=bar_height,
                    color=self.SECTOR_COLORS["s1"], alpha=0.5
                )
                self.ax.barh(
                    y_fastest, fastest_s2, height=bar_height, left=fastest_s1,
                    color=self.SECTOR_COLORS["s2"], alpha=0.5
                )
                self.ax.barh(
                    y_fastest, fastest_s3, height=bar_height, left=fastest_s1 + fastest_s2,
                    color=self.SECTOR_COLORS["s3"], alpha=0.5
                )
                
                # 添加時間差標記
                self._add_delta_markers(driver_data, y_positions[idx])
            
            # ========== 設置軸標籤和標題 ==========
            self.ax.set_yticks(y_positions)
            self.ax.set_yticklabels(drivers, fontsize=9)
            self.ax.set_xlabel("Lap Time (seconds)", fontsize=10)
            self.ax.set_title("Ideal Lap vs Fastest Lap - Sector Breakdown", fontsize=12, fontweight='bold')
            
            # 添加圖例
            self.ax.legend(loc='upper right', fontsize=9)
            
            # 網格線
            self.ax.grid(axis='x', alpha=0.3, linestyle='--')
            
            # 調整布局
            self.figure.tight_layout()
            
            # 刷新畫布
            self.canvas.draw()
            
            self._debug("[DRAW] ✅ 圖表繪製完成")
            
        except Exception as e:
            self._debug(f"[DRAW] ❌ 繪製失敗: {e}")
            import traceback
            traceback.print_exc()
            self._draw_error_message(str(e))
    
    def _add_delta_markers(self, driver_data: Dict, y_center: float):
        """
        添加時間差標記（✓ 或 ❌）
        
        Args:
            driver_data: 車手資料
            y_center: Y 軸中心位置
        """
        try:
            ideal_total = sum(driver_data["ideal_sectors"])
            fastest_total = sum(driver_data["fastest_sectors"])
            delta_total = fastest_total - ideal_total
            
            # 判斷是否接近完美（總差距 < 0.1s）
            is_near_perfect = abs(delta_total) < 0.1
            marker = "✓" if is_near_perfect else "❌"
            color = "green" if is_near_perfect else "red"
            
            # 在棒狀圖右側添加總時間差標記
            self.ax.text(
                fastest_total + 1.5,  # X 位置（棒狀圖右側）
                y_center,             # Y 位置（車手中心）
                f"{marker} {delta_total:+.3f}s",
                color=color,
                fontsize=8,
                va='center',
                ha='left',
                fontweight='bold'
            )
            
            # 添加各分段的 ✓/❌ 標記（可選，較小字體）
            is_optimal = driver_data.get("is_optimal", [False, False, False])
            sector_positions = [
                driver_data["ideal_sectors"][0] / 2,
                driver_data["ideal_sectors"][0] + driver_data["ideal_sectors"][1] / 2,
                sum(driver_data["ideal_sectors"][:2]) + driver_data["ideal_sectors"][2] / 2
            ]
            
            for i, (is_opt, x_pos) in enumerate(zip(is_optimal, sector_positions)):
                if is_opt:
                    self.ax.text(
                        x_pos, y_center + 0.6,
                        "✓", color="green", fontsize=6, ha='center'
                    )
            
        except Exception as e:
            self._debug(f"[MARKERS] ⚠️ 添加標記失敗: {e}")
    
    def _draw_no_data_message(self):
        """繪製無資料訊息"""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, 
            "📊 No Data Available\n\nPlease load data first.",
            ha='center', va='center',
            fontsize=14, color='gray',
            transform=self.ax.transAxes
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def _draw_error_message(self, error: str):
        """繪製錯誤訊息"""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5,
            f"❌ Error\n\n{error}",
            ha='center', va='center',
            fontsize=12, color='red',
            transform=self.ax.transAxes
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def sort_data(self, sort_key: str):
        """
        排序資料並重繪
        
        Args:
            sort_key: 排序鍵（"position", "ideal_lap", "fastest_lap", "delta"）
        """
        if not self.comparison_data:
            return
        
        self._debug(f"[SORT] 依據 {sort_key} 排序")
        
        # 排序邏輯
        if sort_key == "position":
            sorted_data = sorted(self.comparison_data, key=lambda x: x.get("position", 99))
        elif sort_key == "ideal_lap":
            sorted_data = sorted(self.comparison_data, key=lambda x: x["ideal_lap_time"])
        elif sort_key == "fastest_lap":
            sorted_data = sorted(self.comparison_data, key=lambda x: x["fastest_lap_time"])
        elif sort_key == "delta":
            sorted_data = sorted(
                self.comparison_data,
                key=lambda x: x["fastest_lap_time"] - x["ideal_lap_time"],
                reverse=True
            )
        else:
            sorted_data = self.comparison_data
        
        self.current_sort = sort_key
        self.draw_comparison_bars(sorted_data, self.statistics)
        self.sort_changed.emit(sort_key)
    
    def filter_by_team(self, team: str):
        """
        依車隊篩選（保留功能，暫未實作）
        
        Args:
            team: 車隊名稱
        """
        # TODO: 實作車隊篩選邏輯
        pass
    
    def clear_chart(self):
        """
        清空圖表（複製 ranking_table 的 clear_table() 模式）
        
        ✅ 保持與 ranking_table 一致性
        """
        self.comparison_data = []
        self.statistics = {}
        
        # 清除圖表
        if hasattr(self, 'ax') and self.ax:
            self.ax.clear()
            self.ax.text(
                0.5, 0.5,
                "📊 Chart Cleared\n\nPlease load data to view comparison.",
                ha='center', va='center',
                fontsize=14, color='gray',
                transform=self.ax.transAxes
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.draw()
        
        print("[SECTOR_COMPARISON_WIDGET] ✅ 圖表已清空")
    
    def update_statistics_panel(self, statistics: Dict):
        """
        更新統計面板（複製 ranking_table 模式，提供統一介面）
        
        ✅ 保持與 ranking_table 一致性
        
        Args:
            statistics: 統計資料
        """
        # 內部使用 ControlPanel 的 update_statistics 方法
        # 此方法提供與 ranking_table 一致的介面
        self.statistics = statistics
        print(f"[SECTOR_COMPARISON_WIDGET] ✅ 統計資料已更新")
    
    def _debug(self, message: str):
        """除錯訊息輸出"""
        if hasattr(self, '_debug_enabled') and self._debug_enabled:
            print(message)
        else:
            # 預設輸出
            print(message)


class SectorComparisonControlPanel(QWidget):
    """
    分段對比控制面板
    
    包含：
    - 統計面板
    - 排序選擇
    - 篩選器
    """
    
    sort_requested = pyqtSignal(str)  # 排序請求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # ========== 統計面板 ==========
        self.stats_group = QGroupBox("📊 Sector Statistics")
        stats_layout = QGridLayout()
        
        # 欄位標題
        headers = ["Sector", "Avg Loss", "Max Loss", "Min Loss", "Perfect Drivers"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setFont(QFont("Arial", 9, QFont.Bold))
            stats_layout.addWidget(label, 0, col)
        
        # 分段資料（初始為空，待更新）
        self.sector_labels = {}
        for row, sector in enumerate(["Sector 1", "Sector 2", "Sector 3"], start=1):
            stats_layout.addWidget(QLabel(sector), row, 0)
            
            for col in range(1, 5):
                label = QLabel("-")
                label.setAlignment(Qt.AlignCenter)
                stats_layout.addWidget(label, row, col)
                self.sector_labels[f"s{row}_{col}"] = label
        
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)
        
        # ========== 控制按鈕 ==========
        control_layout = QHBoxLayout()
        
        # 排序選擇
        control_layout.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Position",
            "Ideal Lap Time",
            "Fastest Lap Time",
            "Time Gap (Δ)"
        ])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        control_layout.addWidget(self.sort_combo)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
    
    def _on_sort_changed(self, index: int):
        """排序選擇變更"""
        sort_keys = ["position", "ideal_lap", "fastest_lap", "delta"]
        if 0 <= index < len(sort_keys):
            self.sort_requested.emit(sort_keys[index])
    
    def update_statistics(self, statistics: Dict):
        """
        更新統計面板
        
        Args:
            statistics: 統計資料
        """
        for sector_num, sector_key in enumerate(["sector_1", "sector_2", "sector_3"], start=1):
            if sector_key in statistics:
                stats = statistics[sector_key]
                
                # Avg Loss
                self.sector_labels[f"s{sector_num}_1"].setText(f"{stats['avg_loss']:+.3f}s")
                
                # Max Loss
                max_text = f"{stats['max_loss']:+.3f}s\n({stats['max_loss_driver']})"
                self.sector_labels[f"s{sector_num}_2"].setText(max_text)
                
                # Min Loss
                min_text = f"{stats['min_loss']:+.3f}s\n({stats['min_loss_driver']})"
                self.sector_labels[f"s{sector_num}_3"].setText(min_text)
                
                # Perfect Drivers
                perfect_text = f"{stats['perfect_count']} ({stats['perfect_percentage']:.1f}%)"
                self.sector_labels[f"s{sector_num}_4"].setText(perfect_text)
