"""
LapTimeBoxPlotChartWidget - 圈速箱型圖圖表組件 (純 PyQt5 實現)

功能：
- 使用 PyQt5 QPainter 繪製箱型圖（100% Qt 原生）
- 顯示所有車手的圈速分布
- 應用車隊配色方案
- 顯示統計資訊（中位數、Q1、Q3、鬚線、異常值）
- 支援圖表匯出（PNG, JPG）
- 支        else:
            self._draw_no_data_message(painter)
            
        # 繪製標題 (已隱藏)
        # self._draw_title(painter)
        
        # 繪製圖例 (已隱藏)
        # self._draw_legend(painter)示
- 支援多國語言（i18n）

作者: F1T Team
日期: 2025-10-02
版本: 2.1.0 (QPainter + i18n)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QMenu, QInputDialog
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QFontMetrics, 
    QMouseEvent, QPainterPath, QImage, QPainter as QPainterForExport,
    QCursor
)
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# 匯入多國語言支援
from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider

from core.logger import get_logger
logger = get_logger(__name__)


class LapTimeBoxPlotChartWidget(QWidget):
    """圈速箱型圖圖表組件 (純 PyQt5 QPainter 實現)"""
    
    DEFAULT_COLOR = QColor(128, 128, 128)
    
    # 信號
    chart_clicked = pyqtSignal(str)  # 點擊車手箱型圖時發射車手代碼
    
    def __init__(self, parent=None):
        """初始化圖表組件"""
        super().__init__(parent)
        
        # 數據屬性
        self.driver_laptimes: Dict[str, List[float]] = {}
        self.statistics: Dict[str, Dict[str, float]] = {}
        self.current_data: Optional[Dict] = None
        
        # 佈局參數
        self.margin_left = 60
        self.margin_right = 30
        self.margin_top = 50
        self.margin_bottom = 80
        
        # 圖表區域
        self.chart_rect = QRect()
        
        # 懸停狀態
        self.hover_driver = None
        self.hover_position = None
        
        # Y 軸範圍（將在繪製時計算）
        self.y_min = 0.0
        self.y_max = 100.0
        
        # 🆕 數據過濾管理
        self.hidden_drivers = set()  # 儲存被隱藏的車手代碼集合
        
        # 🆕 Y 軸範圍控制
        self.y_axis_mode = "auto"  # "auto", "limit_100", "limit_95", "custom"
        self.y_axis_custom_max = 100.0  # 自訂 Y 軸上限
        
        # 啟用滑鼠追蹤
        self.setMouseTracking(True)
        
        # 🔧 強制啟用滑鼠事件接收
        self.setFocusPolicy(Qt.StrongFocus)  # 允許接收鍵盤和滑鼠焦點
        self.setAttribute(Qt.WA_Hover, True)  # 啟用 hover 事件
        
        # 設置最小尺寸（與其他通用模組一致：Rain, Tire, Driver Lap 都是 200x100）
        self.setMinimumSize(200, 100)  # 統一為 200x100，提供更高的佈局靈活性
        
        logger.debug("[BOXPLOT_CHART] 圖表組件初始化完成 (QPainter 版本)")
        
    def update_data(self, data: Dict[str, Any]):
        """
        更新圖表數據並重繪
        
        參數:
            data: 包含以下鍵的字典
                - driver_laptimes: Dict[str, List[float]] - 每位車手的圈速列表
                - statistics: Dict[str, Dict[str, float]] - 統計資訊
                - metadata: Dict - 元數據（可選）
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[BOXPLOT_CHART] 無效的數據格式")
                return
                
            self.current_data = data
            self.driver_laptimes = data.get('driver_laptimes', {})
            self.statistics = data.get('statistics', {})
            self._ensure_palette_for_data(data)
            
            if not self.driver_laptimes:
                logger.warning("[BOXPLOT_CHART] 沒有圈速數據")
                self.update()
                return
                
            # 計算 Y 軸範圍
            self._calculate_y_range()
            
            logger.debug(f"[BOXPLOT_CHART] 更新數據: {len(self.driver_laptimes)} 位車手")
            self.update()  # 觸發重繪
            
        except Exception as e:
            logger.error(f"[BOXPLOT_CHART] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
            
    def _ensure_palette_for_data(self, data: Dict[str, Any]) -> None:
        """Ensure the colour palette matches the data source season."""
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

    def _driver_color(self, driver: str) -> QColor:
        """Return the colour for the specified driver code."""
        color = color_palette_provider.get_driver_color(driver, format="qcolor")
        if isinstance(color, QColor):
            return QColor(color)
        return QColor(self.DEFAULT_COLOR)

    def _calculate_y_range(self):
        """計算 Y 軸的合適範圍（考慮可見車手和 Y 軸模式）"""
        if not self.driver_laptimes:
            self.y_min = 0.0
            self.y_max = 100.0
            return
        
        # 根據 Y 軸模式決定過濾上限
        y_limit = None
        if self.y_axis_mode == "limit_100":
            y_limit = 100.0
        elif self.y_axis_mode == "limit_95":
            y_limit = 95.0
        elif self.y_axis_mode == "custom":
            y_limit = self.y_axis_custom_max
        # "auto" 模式不設限制
            
        all_times = []
        # 🆕 只收集可見車手的數據，並根據 Y 軸模式過濾
        for driver, lap_times in self.driver_laptimes.items():
            if driver not in self.hidden_drivers:
                if y_limit is not None:
                    # 過濾超過上限的數據點
                    filtered_times = [t for t in lap_times if t <= y_limit]
                    all_times.extend(filtered_times)
                else:
                    all_times.extend(lap_times)
            
        if all_times:
            self.y_min = min(all_times)
            self.y_max = max(all_times)
            
            # 添加 5% 的邊距
            range_padding = (self.y_max - self.y_min) * 0.05
            self.y_min -= range_padding
            self.y_max += range_padding
        else:
            self.y_min = 0.0
            self.y_max = 100.0
            
        logger.debug(f"[BOXPLOT_CHART] Y 軸範圍: {self.y_min:.1f} - {self.y_max:.1f} (mode={self.y_axis_mode})")
            
    def paintEvent(self, event):
        """繪製事件"""
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
            
            # 繪製背景
            self._draw_background(painter)
            
            # 繪製網格
            self._draw_grid(painter)
            
            # 繪製座標軸
            self._draw_axes(painter)
            
            # 繪製座標軸標籤
            self._draw_axis_labels(painter)
            
            # 繪製數據
            if self.driver_laptimes:
                self._draw_box_plots(painter)
            else:
                self._draw_no_data_message(painter)
                
            # 繪製標題 (已隱藏)
            # self._draw_title(painter)
            
            # 繪製圖例 (已隱藏)
            # self._draw_legend(painter)
            
            # 繪製工具提示
            if self.hover_driver:
                self._draw_tooltip(painter)
        finally:
            # 🔑 確保總是釋放 QPainter 資源
            painter.end()
            
    def _draw_background(self, painter: QPainter):
        """繪製背景"""
        # 整體背景
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        # 圖表區域背景
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))
        
    def _draw_grid(self, painter: QPainter):
        """繪製網格線"""
        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
        
        # 水平網格線（Y 軸）
        num_y_lines = 8
        for i in range(num_y_lines + 1):
            y = self.chart_rect.top() + (self.chart_rect.height() * i / num_y_lines)
            painter.drawLine(
                self.chart_rect.left(),
                int(y),
                self.chart_rect.right(),
                int(y)
            )
            
    def _draw_axes(self, painter: QPainter):
        """繪製座標軸"""
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        
        # X 軸
        painter.drawLine(
            self.chart_rect.bottomLeft(),
            self.chart_rect.bottomRight()
        )
        
        # Y 軸
        painter.drawLine(
            self.chart_rect.bottomLeft(),
            self.chart_rect.topLeft()
        )
        
    def _draw_axis_labels(self, painter: QPainter):
        """繪製座標軸標籤"""
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(QColor(70, 70, 70)))
        
        # Y 軸標籤（圈速時間）
        num_y_labels = 8
        for i in range(num_y_labels + 1):
            y_pos = self.chart_rect.top() + (self.chart_rect.height() * i / num_y_labels)
            value = self.y_max - ((self.y_max - self.y_min) * i / num_y_labels)
            
            # 繪製標籤文字
            label = f"{value:.2f}s"
            painter.drawText(
                QRect(5, int(y_pos) - 10, self.margin_left - 10, 20),
                Qt.AlignRight | Qt.AlignVCenter,
                label
            )
            
        # X 軸標籤（車手代碼）會在繪製箱型圖時一起繪製
        
        # Y 軸標題（調整距離使其離 Y 軸數值更遠）
        painter.save()
        painter.translate(5, self.chart_rect.center().y())  # 從 15 改為 5，增加距離
        painter.rotate(-90)
        title_font = QFont()
        title_font.setPointSize(8)
        painter.setFont(title_font)
        painter.drawText(
            QRect(-100, -10, 200, 20),
            Qt.AlignCenter,
            tr("lap_box_plot.y_axis_title", "Lap Time (seconds)")
        )
        painter.restore()
        
        # X 軸標題 (已隱藏)
        # painter.setFont(title_font)
        # painter.drawText(
        #     QRect(
        #         self.chart_rect.left(),
        #         self.chart_rect.bottom() + 60,
        #         self.chart_rect.width(),
        #         20
        #     ),
        #     Qt.AlignCenter,
        #     tr("lap_box_plot.x_axis_title", "Driver Code")
        # )
        
    def _draw_box_plots(self, painter: QPainter):
        """繪製所有車手的箱型圖"""
        if not self.driver_laptimes:
            return
            
        drivers = sorted(self.driver_laptimes.keys())
        
        # 🆕 過濾被隱藏的車手
        visible_drivers = [d for d in drivers if d not in self.hidden_drivers]
        
        if not visible_drivers:
            logger.debug("[BOXPLOT_CHART] 所有車手都被隱藏")
            return
        
        n_drivers = len(visible_drivers)
        if n_drivers == 0:
            return
            
        # 計算箱型圖位置
        box_spacing = self.chart_rect.width() / (n_drivers + 1)
        box_width = min(40, box_spacing * 0.6)
        
        for i, driver in enumerate(visible_drivers):
            lap_times = self.driver_laptimes[driver]
            if not lap_times:
                continue
                
            # 計算箱型圖的 X 位置
            x_center = self.chart_rect.left() + (i + 1) * box_spacing
            
            # 繪製單個箱型圖
            self._draw_single_box_plot(
                painter,
                driver,
                lap_times,
                x_center,
                box_width
            )
            
    def _draw_single_box_plot(
        self,
        painter: QPainter,
        driver: str,
        lap_times: List[float],
        x_center: float,
        box_width: float
    ):
        """繪製單個車手的箱型圖（彩色半透明 + 疊加散點圖樣式）"""
        try:
            # 計算統計值
            lap_times_array = np.array(lap_times)
            q1 = np.percentile(lap_times_array, 25)
            median = np.percentile(lap_times_array, 50)
            q3 = np.percentile(lap_times_array, 75)
            iqr = q3 - q1
            
            # 計算鬚線範圍
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # 過濾異常值
            whisker_data = lap_times_array[
                (lap_times_array >= lower_bound) & (lap_times_array <= upper_bound)
            ]
            
            if len(whisker_data) > 0:
                whisker_min = whisker_data.min()
                whisker_max = whisker_data.max()
            else:
                whisker_min = q1
                whisker_max = q3
                
            # 異常值
            outliers = lap_times_array[
                (lap_times_array < lower_bound) | (lap_times_array > upper_bound)
            ]
            
            # 座標轉換函數
            def time_to_y(time_val):
                if self.y_max == self.y_min:
                    return self.chart_rect.center().y()
                ratio = (time_val - self.y_min) / (self.y_max - self.y_min)
                return self.chart_rect.bottom() - (ratio * self.chart_rect.height())
            
            # 獲取車隊配色
            team_color = self._driver_color(driver)
            
            # 檢查是否懸停
            is_hovered = (driver == self.hover_driver)
            
            # ========== 1. 繪製箱體 (Q1 到 Q3) - 半透明填充 ==========
            box_rect = QRectF(
                x_center - box_width / 2,
                time_to_y(q3),
                box_width,
                time_to_y(q1) - time_to_y(q3)
            )
            
            # 箱體填充顏色：半透明車隊配色（懸停時加深）
            fill_color = QColor(team_color)
            fill_color.setAlpha(100 if not is_hovered else 140)  # 更透明，讓散點更明顯
            
            # 箱體邊框使用相同車隊配色（不透明）
            border_color = QColor(team_color)
            border_color.setAlpha(255)
            
            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(border_color, 2 if is_hovered else 1.5))
            painter.drawRect(box_rect)
            
            # ========== 2. 繪製鬚線（使用車隊配色）==========
            whisker_pen = QPen(border_color, 1.5, Qt.SolidLine)
            painter.setPen(whisker_pen)
            
            # 上鬚線（從 Q3 到 whisker_max）
            painter.drawLine(
                QPoint(int(x_center), int(time_to_y(q3))),
                QPoint(int(x_center), int(time_to_y(whisker_max)))
            )
            # 上端帽
            painter.drawLine(
                QPoint(int(x_center - box_width / 4), int(time_to_y(whisker_max))),
                QPoint(int(x_center + box_width / 4), int(time_to_y(whisker_max)))
            )
            
            # 下鬚線（從 Q1 到 whisker_min）
            painter.drawLine(
                QPoint(int(x_center), int(time_to_y(q1))),
                QPoint(int(x_center), int(time_to_y(whisker_min)))
            )
            # 下端帽
            painter.drawLine(
                QPoint(int(x_center - box_width / 4), int(time_to_y(whisker_min))),
                QPoint(int(x_center + box_width / 4), int(time_to_y(whisker_min)))
            )
            
            # ========== 3. 繪製中位數線（使用深色車隊配色）==========
            median_color = QColor(team_color).darker(130)
            painter.setPen(QPen(median_color, 2.5))
            painter.drawLine(
                QPoint(int(x_center - box_width / 2), int(time_to_y(median))),
                QPoint(int(x_center + box_width / 2), int(time_to_y(median)))
            )
            
            # ========== 4. 繪製散點圖（所有數據點疊加在箱型圖上）==========
            # 使用抖動效果（jitter）避免散點重疊
            np.random.seed(hash(driver) % (2**31))  # 固定隨機種子，保持一致性
            jitter_range = box_width * 0.35  # 抖動範圍
            
            # 散點顏色：車隊配色，半透明
            scatter_color = QColor(team_color)
            scatter_color.setAlpha(200)
            
            painter.setPen(QPen(border_color, 0.5))
            painter.setBrush(QBrush(scatter_color))
            
            scatter_radius = 4  # 散點大小
            
            for lap_time in lap_times_array:
                # 添加水平抖動
                jitter_x = np.random.uniform(-jitter_range, jitter_range)
                x_pos = x_center + jitter_x
                y_pos = time_to_y(lap_time)
                
                painter.drawEllipse(
                    QPoint(int(x_pos), int(y_pos)),
                    scatter_radius, scatter_radius
                )
            
            # ========== 5. 繪製異常值（使用不同樣式標記）==========
            if len(outliers) > 0:
                outlier_color = QColor(team_color).darker(150)
                painter.setPen(QPen(outlier_color, 1.5))
                painter.setBrush(Qt.NoBrush)  # 空心圓圈標記異常值
                
                for outlier in outliers:
                    jitter_x = np.random.uniform(-jitter_range * 0.5, jitter_range * 0.5)
                    painter.drawEllipse(
                        QPoint(int(x_center + jitter_x), int(time_to_y(outlier))),
                        5, 5  # 比普通散點大一點
                    )
                    
            # ========== 6. 繪製車手代碼標籤（圓角背景 + 車隊配色）==========
            label_font = QFont("Arial", 9, QFont.Bold if is_hovered else QFont.Normal)
            painter.setFont(label_font)
            fm = QFontMetrics(label_font)
            label_width = fm.horizontalAdvance(driver)
            label_height = fm.height()
            
            label_x = x_center - label_width // 2
            label_y = self.chart_rect.bottom() + 15
            
            # 背景矩形
            padding = 3
            bg_rect = QRectF(
                label_x - padding,
                label_y - label_height + 2,
                label_width + padding * 2,
                label_height + padding
            )
            
            # 繪製背景
            painter.setPen(Qt.NoPen)
            bg_color = QColor(team_color)
            bg_color.setAlpha(200)
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(bg_rect, 3, 3)
            
            # 計算亮度決定文字顏色
            luminance = 0.299 * team_color.red() + 0.587 * team_color.green() + 0.114 * team_color.blue()
            text_color = QColor(0, 0, 0) if luminance > 128 else QColor(255, 255, 255)
            painter.setPen(text_color)
            painter.drawText(int(label_x), int(label_y), driver)
            
        except Exception as e:
            logger.error(f"[BOXPLOT_CHART] 繪製箱型圖失敗 ({driver}): {e}")
            
    def _draw_title(self, painter: QPainter):
        """繪製標題"""
        title_font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(30, 30, 30)))
        
        painter.drawText(
            QRect(0, 10, self.width(), 30),
            Qt.AlignCenter,
            tr("lap_box_plot.chart_title", "📊 Lap Time Box Plot Analysis")
        )
        
    def _draw_legend(self, painter: QPainter):
        """繪製圖例"""
        legend_x = self.width() - 180
        legend_y = self.margin_top
        legend_width = 170
        legend_height = 95  # 減少高度（移除中位數後只需 3 項）
        
        # 圖例背景
        legend_rect = QRect(legend_x, legend_y, legend_width, legend_height)
        painter.fillRect(legend_rect, QColor(255, 255, 255, 230))
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawRect(legend_rect)
        
        # 圖例項目（移除中位數）
        legend_font = QFont("Arial", 9)
        painter.setFont(legend_font)
        
        items = [
            (tr("lap_box_plot.legend_box", "Box: Q1-Q3"), QColor(255, 255, 255), "box"),  # 白色方框
            (tr("lap_box_plot.legend_whisker", "Whisker: 1.5×IQR"), Qt.black, "whisker"),
            (tr("lap_box_plot.legend_outlier", "Outlier"), QColor(220, 20, 20), "outlier")
        ]
        
        item_height = 25
        for i, (label, color, item_type) in enumerate(items):
            y = legend_y + 10 + i * item_height
            
            # 繪製圖示
            if item_type == "box":
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.black, 1))
                painter.drawRect(legend_x + 10, y, 15, 15)
            elif item_type == "median":
                painter.setPen(QPen(color, 3))
                painter.drawLine(legend_x + 10, y + 7, legend_x + 25, y + 7)
            elif item_type == "whisker":
                painter.setPen(QPen(color, 1.5))
                painter.drawLine(legend_x + 17, y, legend_x + 17, y + 15)
                painter.drawLine(legend_x + 12, y, legend_x + 22, y)
                painter.drawLine(legend_x + 12, y + 15, legend_x + 22, y + 15)
            elif item_type == "outlier":
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.black, 1))
                painter.drawEllipse(QPoint(legend_x + 17, y + 7), 4, 4)
                
            # 繪製標籤
            painter.setPen(QPen(Qt.black))
            painter.drawText(legend_x + 35, y + 12, label)
            
    def _draw_no_data_message(self, painter: QPainter):
        """繪製無數據訊息"""
        font = QFont("Arial", 14)
        painter.setFont(font)
        painter.setPen(QPen(QColor(150, 150, 150)))
        
        no_data_msg = tr("lap_box_plot.no_data", "📊 No lap time data available\n\nPlease check data source or adjust filter settings")
        painter.drawText(
            self.chart_rect,
            Qt.AlignCenter,
            no_data_msg
        )
        
    def _draw_tooltip(self, painter: QPainter):
        """繪製工具提示"""
        if not self.hover_driver or not self.hover_position:
            return
            
        stats = self.statistics.get(self.hover_driver)
        if not stats:
            return
            
        # 工具提示內容（多國語言支援）
        lines = [
            f"{tr('lap_box_plot.tooltip_driver', 'Driver')}: {self.hover_driver}",
            f"{tr('lap_box_plot.tooltip_laps', 'Laps')}: {stats.get('count', 0)}",
            f"{tr('lap_box_plot.tooltip_median', 'Median')}: {stats.get('median', 0):.3f}s",
            f"{tr('lap_box_plot.tooltip_mean', 'Mean')}: {stats.get('mean', 0):.3f}s",
            f"Q1: {stats.get('q1', 0):.3f}s",
            f"Q3: {stats.get('q3', 0):.3f}s",
            f"IQR: {stats.get('iqr', 0):.3f}s"
        ]
        
        # 計算工具提示尺寸
        font = QFont("Arial", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        max_width = max(fm.width(line) for line in lines)
        line_height = fm.height()
        tooltip_width = max_width + 20
        tooltip_height = len(lines) * line_height + 10
        
        # 工具提示位置
        tooltip_x = self.hover_position.x() + 15
        tooltip_y = self.hover_position.y() - tooltip_height - 10
        
        # 邊界檢查
        if tooltip_x + tooltip_width > self.width():
            tooltip_x = self.hover_position.x() - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = self.hover_position.y() + 15
            
        tooltip_rect = QRect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # 繪製背景（白底黑字）- 重置畫筆和畫刷狀態
        painter.setBrush(QBrush(QColor(255, 255, 255, 250)))  # 白色背景
        painter.setPen(QPen(QColor(100, 100, 100), 1))  # 灰色邊框
        painter.drawRect(tooltip_rect)
        
        # 繪製文字（黑色）- 重置畫刷
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(Qt.black))
        for i, line in enumerate(lines):
            painter.drawText(
                tooltip_x + 10,
                tooltip_y + 15 + i * line_height,
                line
            )
            
    def _detect_hovered_driver(self, position: QPoint) -> Optional[str]:
        """
        檢測滑鼠位置是否懸停在某個車手的箱型圖上
        
        Args:
            position: 滑鼠位置
            
        Returns:
            車手代碼，如果沒有懸停則返回 None
        """
        if not self.driver_laptimes:
            return None
        
        drivers = sorted(self.driver_laptimes.keys())
        
        # 只檢測可見的車手
        visible_drivers = [d for d in drivers if d not in self.hidden_drivers]
        if not visible_drivers:
            return None
        
        n_drivers = len(visible_drivers)
        box_spacing = self.chart_rect.width() / (n_drivers + 1)
        box_width = min(40, box_spacing * 0.6)
        
        for i, driver in enumerate(visible_drivers):
            x_center = self.chart_rect.left() + (i + 1) * box_spacing
            
            # 檢查 X 座標是否在箱型圖範圍內（擴大點擊區域）
            rect = QRectF(
                x_center - box_width / 2,
                self.chart_rect.top(),
                box_width,
                self.chart_rect.height()
            )
            
            if rect.contains(position):
                return driver
        
        return None
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件"""
        position = event.pos()
        previous_driver = self.hover_driver
        
        # 使用統一的檢測方法
        hovered_driver = self._detect_hovered_driver(position)
        
        if hovered_driver != previous_driver:
            self.hover_driver = hovered_driver
            self.hover_position = position if hovered_driver else None
            self.update()
        else:
            self.hover_position = position if hovered_driver else None
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.hover_driver = None
        self.hover_position = None
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠點擊事件處理（左鍵和右鍵）"""
        logger.debug(f"[BOXPLOT_CHART] mousePressEvent 被觸發！")
        logger.debug(f"[BOXPLOT_CHART] - 滑鼠位置: {event.pos()}")
        logger.debug(f"[BOXPLOT_CHART] - 按鍵類型: {event.button()} (Left=1, Right=2)")
        
        # 實時檢測點擊位置的車手（不依賴 hover_driver）
        driver = self._detect_hovered_driver(event.pos())
        logger.debug(f"[BOXPLOT_CHART] - 檢測到車手: {driver}")
        
        # 右鍵：顯示選單（即使沒點到車手也可以調整 Y 軸）
        if event.button() == Qt.RightButton:
            logger.info(f"[BOXPLOT_CHART] 右鍵點擊，driver={driver}，準備顯示選單")
            self._show_context_menu(driver, event)
            return
        
        # 左鍵：需要點到車手才發射信號
        if event.button() == Qt.LeftButton and driver:
            logger.info(f"[BOXPLOT_CHART] 左鍵點擊 {driver}")
            self.chart_clicked.emit(driver)
            
    def export_chart(self, filepath: str) -> bool:
        """
        匯出圖表到文件
        
        參數:
            filepath: 儲存路徑（支援 .png, .jpg）
            
        返回:
            bool: 匯出是否成功
        """
        try:
            if not self.current_data or not self.driver_laptimes:
                logger.warning("[BOXPLOT_CHART] 無數據可匯出")
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
                logger.debug(f"[BOXPLOT_CHART] 圖表已匯出: {filepath}")
            else:
                logger.error(f"[BOXPLOT_CHART] 圖表匯出失敗")
                
            return success
            
        except Exception as e:
            logger.error(f"[BOXPLOT_CHART] 匯出圖表失敗: {e}")
            import traceback

            traceback.print_exc()
            return False
            
    def clear_chart(self):
        """清空圖表"""
        self.driver_laptimes = {}
        self.statistics = {}
        self.current_data = None
        self.hover_driver = None
        self.hover_position = None
        self.update()
        logger.debug("[BOXPLOT_CHART] 圖表已清空")
        
    def get_current_data(self) -> Optional[Dict]:
        """獲取當前數據"""
        return self.current_data
    
    # ========== 🆕 右鍵選單與數據過濾功能 ==========
    
    def _show_context_menu(self, driver: str, event: QMouseEvent):
        """
        顯示右鍵選單
        
        Args:
            driver: 車手代碼
            event: 滑鼠事件
        """
        # 創建選單
        menu = QMenu(self)
        
        # ========== 車手操作選項 ==========
        if driver:
            hide_action = menu.addAction(f"🚫 {tr('hide_driver', 'Hide')} {driver}")
            hide_action.triggered.connect(lambda: self._hide_driver(driver))
            menu.addSeparator()
        
        # ========== Y 軸範圍控制選項 ==========
        y_axis_menu = menu.addMenu(tr('y_axis_range', 'Y-Axis Range'))
        
        # 自動範圍
        auto_action = y_axis_menu.addAction(tr('y_axis_auto', 'Auto Range'))
        auto_action.setCheckable(True)
        auto_action.setChecked(self.y_axis_mode == "auto")
        auto_action.triggered.connect(lambda: self._set_y_axis_mode("auto"))
        
        # 忽略超過 100 秒
        limit_100_action = y_axis_menu.addAction(tr('y_axis_limit_100', 'Limit to 100s'))
        limit_100_action.setCheckable(True)
        limit_100_action.setChecked(self.y_axis_mode == "limit_100")
        limit_100_action.triggered.connect(lambda: self._set_y_axis_mode("limit_100"))
        
        # 忽略超過 95 秒
        limit_95_action = y_axis_menu.addAction(tr('y_axis_limit_95', 'Limit to 95s'))
        limit_95_action.setCheckable(True)
        limit_95_action.setChecked(self.y_axis_mode == "limit_95")
        limit_95_action.triggered.connect(lambda: self._set_y_axis_mode("limit_95"))
        
        y_axis_menu.addSeparator()
        
        # 自訂上限
        custom_action = y_axis_menu.addAction(tr('y_axis_custom', 'Custom Limit...'))
        custom_action.triggered.connect(self._show_custom_y_axis_dialog)
        
        # ========== 顯示所有車手 ==========
        if self.hidden_drivers:
            menu.addSeparator()
            show_all_action = menu.addAction(tr('show_all_drivers', 'Show All Drivers'))
            show_all_action.triggered.connect(self.show_all_drivers)
        
        # 顯示選單（使用全局坐標）
        try:
            menu.exec_(QCursor.pos())
        except Exception as e:
            logger.error(f"[BOXPLOT_CHART] 顯示選單失敗: {e}")
        
        logger.debug(f"[BOXPLOT_CHART] 顯示右鍵選單: driver={driver}, y_mode={self.y_axis_mode}")

    def _set_y_axis_mode(self, mode: str):
        """
        設定 Y 軸範圍模式
        
        Args:
            mode: "auto", "limit_100", "limit_95", "custom"
        """
        if mode == self.y_axis_mode:
            return
            
        self.y_axis_mode = mode
        logger.info(f"[BOXPLOT_CHART] Y 軸模式變更為: {mode}")
        
        # 重新計算 Y 軸範圍
        self._calculate_y_range()
        
        # 重繪圖表
        self.update()
    
    def _show_custom_y_axis_dialog(self):
        """顯示自訂 Y 軸上限對話框"""
        # 取得當前預設值（使用目前的 y_max 作為參考）
        current_max = self.y_axis_custom_max if self.y_axis_mode == "custom" else self.y_max
        
        value, ok = QInputDialog.getDouble(
            self,
            tr('y_axis_custom_title', 'Custom Y-Axis Limit'),
            tr('y_axis_custom_label', 'Enter maximum lap time (seconds):'),
            current_max,  # 預設值
            50.0,  # 最小值
            300.0,  # 最大值
            1  # 小數位數
        )
        
        if ok:
            self.y_axis_custom_max = value
            self.y_axis_mode = "custom"
            logger.info(f"[BOXPLOT_CHART] Y 軸自訂上限: {value:.1f} 秒")
            
            # 重新計算 Y 軸範圍
            self._calculate_y_range()
            
            # 重繪圖表
            self.update()
    
    def _hide_driver(self, driver: str):
        """
        隱藏指定車手的數據
        
        Args:
            driver: 車手代碼
        """
        if driver in self.hidden_drivers:
            logger.debug(f"[BOXPLOT_CHART] 車手 {driver} 已經被隱藏")
            return
        
        # 添加到隱藏集合
        self.hidden_drivers.add(driver)
        logger.debug(f"[BOXPLOT_CHART] 隱藏車手: {driver}")
        logger.debug(f"[BOXPLOT_CHART] 當前隱藏車手: {self.hidden_drivers}")
        
        # 重新計算 Y 軸範圍（只考慮可見車手）
        self._calculate_y_range()
        
        # 重繪圖表（會自動過濾隱藏的車手）
        self.update()
    
    def show_all_drivers(self):
        """
        顯示所有車手數據（恢復所有隱藏的車手）
        
        這是一個公開方法，供 MDI 視窗的 "Show All Data" 按鈕調用
        """
        if not self.hidden_drivers:
            logger.debug("[BOXPLOT_CHART] 沒有隱藏的車手需要恢復")
            return
        
        # 清空隱藏集合
        hidden_count = len(self.hidden_drivers)
        self.hidden_drivers.clear()
        logger.debug(f"[BOXPLOT_CHART] 已恢復 {hidden_count} 個隱藏車手")
        
        # 重新計算 Y 軸範圍（包含所有車手）
        self._calculate_y_range()
        
        # 重繪圖表（顯示所有數據）
        self.update()
