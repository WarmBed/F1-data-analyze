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
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新圖表數據並重繪
        
        ✅ 完全參考 lap_box_plot_analysis.update_data()
        
        參數:
            data: 包含以下鍵的字典
                - comparison_data: List[Dict] - 每位車手的對比數據
                - statistics: Dict[str, Any] - 統計資訊
                - metadata: Dict - 元數據（可選）
        """
        try:
            if not data or not isinstance(data, dict):
                print("[WARNING] [SECTOR_COMPARISON] 無效的數據格式")
                return
            
            self.current_data = data
            
            # ✅ 參考實際 JSON 結構 (ideal_lap_ranking_2025_Japan_R.json)
            # 結構: analysis_result.ranking[] 或直接 comparison_data[]
            if 'analysis_result' in data:
                # 實際 JSON 格式
                self.comparison_data = data['analysis_result'].get('ranking', [])
                self.statistics = data['analysis_result'].get('summary', {})
            else:
                # 舊格式 (向後兼容)
                self.comparison_data = data.get('comparison_data', [])
                self.statistics = data.get('statistics', {})
            
            self._ensure_palette_for_data(data)
            
            if not self.comparison_data:
                print("[WARNING] [SECTOR_COMPARISON] 沒有對比數據")
                self.update()  # ✅ 觸發 paintEvent
                return
            
            # 計算 X 軸範圍（時間軸）
            self._calculate_x_range()
            
            print(f"[SECTOR_COMPARISON] 更新數據: {len(self.comparison_data)} 位車手")
            self.update()  # ✅ 參考 lap_box_plot_analysis: 觸發重繪
            
        except Exception as e:
            print(f"[ERROR] [SECTOR_COMPARISON] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _ensure_palette_for_data(self, data: Dict[str, Any]) -> None:
        """✅ 參考 lap_box_plot_analysis: 確保車隊配色匹配數據的賽季"""
        if not isinstance(data, dict):
            return

        metadata = data.get("metadata", {}) or {}
        target_year = None

        api_meta = metadata.get("api")
        if isinstance(api_meta, dict):
            params = api_meta.get("params")
            if isinstance(params, dict):
                target_year = params.get("year") or params.get("season_year")

        if target_year is None:
            target_year = metadata.get("season_year") or metadata.get("year")

        try:
            if target_year is not None:
                color_palette_provider.ensure_loaded(year=int(target_year))
            else:
                color_palette_provider.ensure_loaded()
        except Exception:
            pass
    
    def _extract_sector_times(self, driver_data: Dict[str, Any]) -> tuple:
        """
        ✅ 提取分段時間（支援實際 JSON 格式）
        
        Returns:
            tuple: (ideal_sectors, fastest_sectors) - 兩個包含 3 個分段時間的列表
        """
        # ✅ 實際 JSON 格式: sector_breakdown.sector_X.time
        sector_breakdown = driver_data.get("sector_breakdown", {})
        if sector_breakdown:
            ideal_sectors = [
                sector_breakdown.get("sector_1", {}).get("time", 0),
                sector_breakdown.get("sector_2", {}).get("time", 0),
                sector_breakdown.get("sector_3", {}).get("time", 0)
            ]
            # 目前 JSON 中沒有分開的 fastest_sectors
            # 使用 ideal_sectors 作為 fastest_sectors (因為理想圈已經是最快的分段組合)
            fastest_sectors = ideal_sectors[:]
        else:
            # 舊格式: ideal_sectors 陣列 (向後兼容)
            ideal_sectors = driver_data.get("ideal_sectors", [0, 0, 0])
            fastest_sectors = driver_data.get("fastest_sectors", ideal_sectors[:])
        
        return ideal_sectors, fastest_sectors
    
    def _driver_color(self, driver: str) -> QColor:
        """✅ 參考 lap_box_plot_analysis: 獲取車手配色"""
        color = color_palette_provider.get_driver_color(driver, format="qcolor")
        if isinstance(color, QColor):
            return QColor(color)
        return QColor(self.DEFAULT_COLOR)
    
    def _calculate_x_range(self):
        """計算 X 軸的合適範圍（時間軸）"""
        if not self.comparison_data:
            self.x_min = 0.0
            self.x_max = 100.0
            return
        
        # 找出所有總時間
        all_times = []
        for driver_data in self.comparison_data:
            # ✅ 實際 JSON 格式: sector_breakdown.sector_X.time
            sector_breakdown = driver_data.get("sector_breakdown", {})
            if sector_breakdown:
                # 從 sector_breakdown 計算總時間
                ideal_total = sum([
                    sector_breakdown.get("sector_1", {}).get("time", 0),
                    sector_breakdown.get("sector_2", {}).get("time", 0),
                    sector_breakdown.get("sector_3", {}).get("time", 0)
                ])
            else:
                # 舊格式: ideal_sectors 陣列 (向後兼容)
                ideal_total = sum(driver_data.get("ideal_sectors", [0, 0, 0]))
            
            # 也可以使用 ideal_lap_time 和 fastest_lap_time
            ideal_lap = driver_data.get("ideal_lap_time", ideal_total)
            fastest_lap = driver_data.get("fastest_lap_time", ideal_total)
            
            all_times.extend([ideal_lap, fastest_lap])
        
        if all_times:
            self.x_min = 0  # 時間軸從 0 開始
            self.x_max = max(all_times)
            
            # 添加 5% 的右側邊距以顯示時間差標記
            range_padding = self.x_max * 0.05
            self.x_max += range_padding
        else:
            self.x_min = 0.0
            self.x_max = 100.0
    
    def paintEvent(self, event):
        """
        ✅ 參考 lap_box_plot_analysis: 繪製事件
        
        使用 QPainter 繪製水平堆疊棒狀圖
        """
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # 更新圖表區域
            self.chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            
            # ✅ 參考 lap_box_plot_analysis: 繪製流程
            # 1. 繪製背景
            self._draw_background(painter)
            
            # 2. 繪製網格
            self._draw_grid(painter)
            
            # 3. 繪製座標軸
            self._draw_axes(painter)
            
            # 4. 繪製座標軸標籤
            self._draw_axis_labels(painter)
            
            # 5. 繪製數據
            if self.comparison_data:
                self._draw_stacked_bars(painter)
            else:
                self._draw_no_data_message(painter)
            
            # 6. 繪製工具提示
            if self.hover_driver:
                self._draw_tooltip(painter)
                
        finally:
            # ✅ 參考 lap_box_plot_analysis: 確保總是釋放 QPainter 資源
            painter.end()
    
    def _draw_background(self, painter: QPainter):
        """✅ 參考 lap_box_plot_analysis: 繪製背景"""
        # 整體背景
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        # 圖表區域背景
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))
    
    def _draw_grid(self, painter: QPainter):
        """✅ 參考 lap_box_plot_analysis: 繪製網格線"""
        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
        
        # 垂直網格線（X 軸 - 時間軸）
        num_x_lines = 8
        for i in range(num_x_lines + 1):
            x = self.chart_rect.left() + (self.chart_rect.width() * i / num_x_lines)
            painter.drawLine(
                int(x),
                self.chart_rect.top(),
                int(x),
                self.chart_rect.bottom()
            )
    
    def _draw_axes(self, painter: QPainter):
        """✅ 參考 lap_box_plot_analysis: 繪製座標軸"""
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        
        # Y 軸（左側）
        painter.drawLine(
            self.chart_rect.topLeft(),
            self.chart_rect.bottomLeft()
        )
        
        # X 軸（底部）
        painter.drawLine(
            self.chart_rect.bottomLeft(),
            self.chart_rect.bottomRight()
        )
    
    def _draw_axis_labels(self, painter: QPainter):
        """✅ 參考 lap_box_plot_analysis: 繪製座標軸標籤"""
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setFont(QFont("Arial", 9))
        
        # X 軸標籤（時間刻度）
        num_ticks = 8
        for i in range(num_ticks + 1):
            x = self.chart_rect.left() + (self.chart_rect.width() * i / num_ticks)
            time_value = self.x_min + (self.x_max - self.x_min) * i / num_ticks
            
            # 繪製刻度標籤
            label_text = f"{time_value:.1f}s"
            text_rect = painter.fontMetrics().boundingRect(label_text)
            painter.drawText(
                int(x - text_rect.width() / 2),
                self.chart_rect.bottom() + 20,
                label_text
            )
        
        # X 軸標題
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        x_title = tr("sector_comparison.x_axis_title", "Lap Time (seconds)")
        x_title_rect = painter.fontMetrics().boundingRect(x_title)
        painter.drawText(
            self.chart_rect.center().x() - x_title_rect.width() // 2,
            self.chart_rect.bottom() + 50,
            x_title
        )
        
        # Y 軸標題
        painter.save()
        painter.translate(15, self.chart_rect.center().y())
        painter.rotate(-90)
        y_title = tr("sector_comparison.y_axis_title", "Driver")
        painter.drawText(-painter.fontMetrics().boundingRect(y_title).width() // 2, 0, y_title)
        painter.restore()
    
    def _draw_stacked_bars(self, painter: QPainter):
        """繪製所有車手的堆疊棒狀圖"""
        if not self.comparison_data:
            return
        
        num_drivers = len(self.comparison_data)
        
        if num_drivers == 0:
            return
        
        # 計算棒狀圖位置
        bar_spacing = self.chart_rect.height() / (num_drivers + 1)
        bar_height = min(20, bar_spacing * 0.4)  # 每位車手有兩條棒：理想圈和最快圈
        
        for i, driver_data in enumerate(self.comparison_data):
            driver = driver_data.get("driver", "Unknown")
            
            # 計算 Y 位置（垂直位置）
            y_center = self.chart_rect.top() + (i + 1) * bar_spacing
            
            # 繪製單個車手的堆疊棒狀圖
            self._draw_single_driver_bars(
                painter,
                driver_data,
                y_center,
                bar_height
            )
    
    def _draw_single_driver_bars(
        self,
        painter: QPainter,
        driver_data: Dict,
        y_center: float,
        bar_height: float
    ):
        """繪製單個車手的堆疊棒狀圖（理想圈 + 最快圈）"""
        try:
            driver = driver_data.get("driver", "Unknown")
            # ✅ 使用統一的分段時間提取方法
            ideal_sectors, fastest_sectors = self._extract_sector_times(driver_data)
            
            # 獲取車手配色
            driver_color = self._driver_color(driver)
            
            # 檢查是否懸停
            is_hovered = (driver == self.hover_driver)
            
            # 座標轉換函數
            def time_to_x(time_val):
                if self.x_max == self.x_min:
                    return self.chart_rect.left()
                ratio = (time_val - self.x_min) / (self.x_max - self.x_min)
                return self.chart_rect.left() + (ratio * self.chart_rect.width())
            
            # 繪製理想圈堆疊棒（上方，實心）
            y_ideal = y_center - bar_height / 2 - 2
            self._draw_stacked_bar(
                painter,
                ideal_sectors,
                time_to_x,
                y_ideal,
                bar_height,
                is_ideal=True,
                is_hovered=is_hovered
            )
            
            # 繪製最快圈堆疊棒（下方，半透明）
            y_fastest = y_center + bar_height / 2 + 2
            self._draw_stacked_bar(
                painter,
                fastest_sectors,
                time_to_x,
                y_fastest,
                bar_height,
                is_ideal=False,
                is_hovered=is_hovered
            )
            
            # 繪製車手名稱（左側）
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setFont(QFont("Arial", 9, QFont.Bold if is_hovered else QFont.Normal))
            painter.drawText(
                10,
                int(y_center + 4),
                driver
            )
            
            # 繪製時間差標記（右側）
            self._draw_delta_marker(painter, driver_data, y_center, time_to_x)
            
        except Exception as e:
            print(f"[ERROR] [SECTOR_COMPARISON] 繪製車手棒狀圖失敗: {e}")
    
    def _draw_stacked_bar(
        self,
        painter: QPainter,
        sectors: List[float],
        time_to_x,
        y_pos: float,
        height: float,
        is_ideal: bool,
        is_hovered: bool
    ):
        """繪製堆疊棒狀圖（三個分段）"""
        if len(sectors) < 3:
            return
        
        s1, s2, s3 = sectors
        
        # 透明度設置
        alpha = 180 if is_ideal else 120
        if is_hovered:
            alpha = min(255, alpha + 40)
        
        # 繪製 Sector 1（藍色）
        x_start = time_to_x(0)
        x_end = time_to_x(s1)
        color = QColor(self.SECTOR_COLORS["s1"])
        color.setAlpha(alpha)
        painter.fillRect(
            QRectF(x_start, y_pos, x_end - x_start, height),
            QBrush(color)
        )
        
        # 繪製 Sector 2（綠色）
        x_start = time_to_x(s1)
        x_end = time_to_x(s1 + s2)
        color = QColor(self.SECTOR_COLORS["s2"])
        color.setAlpha(alpha)
        painter.fillRect(
            QRectF(x_start, y_pos, x_end - x_start, height),
            QBrush(color)
        )
        
        # 繪製 Sector 3（橙色）
        x_start = time_to_x(s1 + s2)
        x_end = time_to_x(s1 + s2 + s3)
        color = QColor(self.SECTOR_COLORS["s3"])
        color.setAlpha(alpha)
        painter.fillRect(
            QRectF(x_start, y_pos, x_end - x_start, height),
            QBrush(color)
        )
    
    def _draw_delta_marker(self, painter: QPainter, driver_data: Dict, y_center: float, time_to_x):
        """繪製時間差標記"""
        try:
            # ✅ 使用統一的分段時間提取方法
            ideal_sectors, fastest_sectors = self._extract_sector_times(driver_data)
            ideal_total = sum(ideal_sectors)
            fastest_total = sum(fastest_sectors)
            delta = fastest_total - ideal_total
            
            # 判斷是否接近完美（總差距 < 0.1s）
            is_near_perfect = abs(delta) < 0.1
            marker = "✓" if is_near_perfect else "❌"
            color = QColor(0, 150, 0) if is_near_perfect else QColor(200, 50, 50)
            
            # 繪製標記
            painter.setPen(QPen(color, 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            
            marker_x = time_to_x(fastest_total) + 10
            marker_text = f"{marker} {delta:+.3f}s"
            painter.drawText(int(marker_x), int(y_center + 4), marker_text)
            
        except Exception as e:
            print(f"[ERROR] [SECTOR_COMPARISON] 繪製時間差標記失敗: {e}")
    
    def _draw_no_data_message(self, painter: QPainter):
        """✅ 參考 lap_box_plot_analysis: 繪製無數據訊息"""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.setFont(QFont("Arial", 12))
        
        message = tr("sector_comparison.no_data", "📊 No Data Available\n\nPlease load data first.")
        
        # 使用單行顯示避免換行問題
        painter.drawText(
            self.rect().center().x() - 100,
            self.rect().center().y(),
            "📊 No Data Available - Please load data first."
        )
    
    def _draw_tooltip(self, painter: QPainter):
        """✅ 參考 lap_box_plot_analysis: 繪製工具提示"""
        if not self.hover_driver or not self.hover_position:
            return
        
        # 找到懸停車手的數據
        driver_data = None
        for data in self.comparison_data:
            if data.get("driver") == self.hover_driver:
                driver_data = data
                break
        
        if not driver_data:
            return
        
        # 準備 Tooltip 文字
        # ✅ 使用統一的分段時間提取方法
        ideal_sectors, fastest_sectors = self._extract_sector_times(driver_data)
        ideal_total = sum(ideal_sectors)
        fastest_total = sum(fastest_sectors)
        delta = fastest_total - ideal_total
        
        # 繪製 Tooltip 背景和文字
        painter.setFont(QFont("Arial", 9))
        
        tooltip_lines = [
            f"Driver: {self.hover_driver}",
            f"Ideal: {ideal_total:.3f}s",
            f"Fastest: {fastest_total:.3f}s",
            f"Delta: {delta:+.3f}s"
        ]
        
        # 計算 Tooltip 尺寸
        max_width = 0
        line_height = painter.fontMetrics().height()
        for line in tooltip_lines:
            line_width = painter.fontMetrics().boundingRect(line).width()
            max_width = max(max_width, line_width)
        
        tooltip_width = max_width + 20
        tooltip_height = len(tooltip_lines) * line_height + 20
        
        # Tooltip 位置
        tooltip_x = self.hover_position.x() + 15
        tooltip_y = self.hover_position.y() - tooltip_height - 10
        
        # 繪製 Tooltip 背景
        tooltip_rect = QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        painter.fillRect(tooltip_rect, QColor(255, 255, 220, 230))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(tooltip_rect)
        
        # 繪製 Tooltip 文字
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for i, line in enumerate(tooltip_lines):
            painter.drawText(
                int(tooltip_x + 10),
                int(tooltip_y + 15 + i * line_height),
                line
            )
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """✅ 參考 lap_box_plot_analysis: 滑鼠移動事件"""
        if not self.comparison_data:
            return
        
        num_drivers = len(self.comparison_data)
        if num_drivers == 0:
            return
        
        bar_spacing = self.chart_rect.height() / (num_drivers + 1)
        
        mouse_y = event.pos().y()
        
        # 檢查是否在圖表區域內
        if not self.chart_rect.contains(event.pos()):
            if self.hover_driver:
                self.hover_driver = None
                self.hover_position = None
                self.update()
            return
        
        # 查找最近的棒狀圖
        found_driver = None
        for i, driver_data in enumerate(self.comparison_data):
            y_center = self.chart_rect.top() + (i + 1) * bar_spacing
            
            # 檢查 Y 座標是否在棒狀圖範圍內
            if abs(mouse_y - y_center) < bar_spacing / 2:
                found_driver = driver_data.get("driver")
                break
        
        if found_driver != self.hover_driver:
            self.hover_driver = found_driver
            self.hover_position = event.pos() if found_driver else None
            self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """✅ 參考 lap_box_plot_analysis: 滑鼠點擊事件"""
        if event.button() == Qt.LeftButton and self.hover_driver:
            self.bar_clicked.emit(self.hover_driver)
    
    def sort_data(self, sort_key: str):
        """
        排序資料並重繪
        
        ✅ 參考 lap_box_plot_analysis: 使用 update() 觸發重繪
        
        Args:
            sort_key: 排序鍵（"position", "ideal_lap", "fastest_lap", "delta"）
        """
        if not self.comparison_data:
            return
        
        print(f"[SECTOR_COMPARISON] 依據 {sort_key} 排序")
        
        # 定義排序鍵提取函數
        def get_ideal_time(x):
            ideal_sectors, _ = self._extract_sector_times(x)
            return sum(ideal_sectors)
        
        def get_fastest_time(x):
            _, fastest_sectors = self._extract_sector_times(x)
            return sum(fastest_sectors)
        
        def get_delta(x):
            ideal_sectors, fastest_sectors = self._extract_sector_times(x)
            return sum(fastest_sectors) - sum(ideal_sectors)
        
        # 排序邏輯
        if sort_key == "position":
            sorted_data = sorted(self.comparison_data, key=lambda x: x.get("position", 99))
        elif sort_key == "ideal_lap":
            sorted_data = sorted(self.comparison_data, key=get_ideal_time)
        elif sort_key == "fastest_lap":
            sorted_data = sorted(self.comparison_data, key=get_fastest_time)
        elif sort_key == "delta":
            sorted_data = sorted(self.comparison_data, key=get_delta, reverse=True)
        else:
            sorted_data = self.comparison_data
        
        self.comparison_data = sorted_data  # ✅ 更新數據
        self.current_sort = sort_key
        self.update()  # ✅ 觸發 paintEvent 重繪
        self.sort_changed.emit(sort_key)  # ✅ 發射信號
    
    def export_chart(self, filepath: str) -> bool:
        """
        ✅ 參考 lap_box_plot_analysis: 匯出圖表到文件
        
        參數:
            filepath: 儲存路徑（支援 .png, .jpg）
            
        返回:
            bool: 匯出是否成功
        """
        try:
            if not self.current_data or not self.comparison_data:
                print("[WARNING] [SECTOR_COMPARISON] 無數據可匯出")
                return False
            
            # 創建高解析度圖像
            image = QImage(self.size() * 2, QImage.Format_ARGB32)
            image.fill(Qt.white)
            
            # 在圖像上繪製
            painter = QPainterForExport(image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.scale(2.0, 2.0)  # 2倍解析度
            
            # 執行繪製
            self.render(painter)
            painter.end()
            
            # 儲存圖像
            success = image.save(filepath)
            
            if success:
                print(f"[SECTOR_COMPARISON] 圖表已匯出: {filepath}")
            else:
                print(f"[ERROR] [SECTOR_COMPARISON] 圖表匯出失敗")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] [SECTOR_COMPARISON] 匯出圖表失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def clear_chart(self):
        """✅ 參考 lap_box_plot_analysis: 清空圖表"""
        self.comparison_data = []
        self.statistics = {}
        self.current_data = None
        self.hover_driver = None
        self.hover_position = None
        self.update()  # ✅ 觸發 paintEvent 重繪
        print("[SECTOR_COMPARISON] 圖表已清空")
    
    def get_current_data(self) -> Optional[Dict]:
        """✅ 參考 lap_box_plot_analysis: 獲取當前數據"""
        return self.current_data
