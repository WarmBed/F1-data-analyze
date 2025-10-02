"""
LapTimeBoxPlotChartWidget - 圈速箱型圖圖表組件 (純 PyQt5 實現)

功能：
- 使用 PyQt5 QPainter 繪製箱型圖（100% Qt 原生）
- 顯示所有車手的圈速分布
- 應用車隊配色方案
- 顯示統計資訊（中位數、Q1、Q3、鬚線、異常值）
- 支援圖表匯出（PNG, JPG）
- 支援滑鼠懸停工具提示
- 支援多國語言（i18n）

作者: F1T Team
日期: 2025-10-02
版本: 2.1.0 (QPainter + i18n)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QFontMetrics, 
    QMouseEvent, QPainterPath, QImage, QPainter as QPainterForExport
)
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# 匯入多國語言支援
from core.gui_i18n import tr


class LapTimeBoxPlotChartWidget(QWidget):
    """圈速箱型圖圖表組件 (純 PyQt5 QPainter 實現)"""
    
    # 2025 賽季車隊配色（20位車手） - 轉換為 QColor
    TEAM_COLORS = {
        'VER': QColor(54, 113, 198),    # Red Bull Racing - 藍色
        'PER': QColor(54, 113, 198),
        'LEC': QColor(232, 0, 45),      # Ferrari - 紅色
        'SAI': QColor(232, 0, 45),
        'HAM': QColor(39, 244, 210),    # Mercedes - 青綠色
        'RUS': QColor(39, 244, 210),
        'NOR': QColor(255, 128, 0),     # McLaren - 橘色
        'PIA': QColor(255, 128, 0),
        'ALO': QColor(34, 153, 113),    # Aston Martin - 綠色
        'STR': QColor(34, 153, 113),
        'GAS': QColor(94, 143, 170),    # Alpine - 藍色
        'OCO': QColor(94, 143, 170),
        'HUL': QColor(182, 186, 189),   # Haas - 灰色
        'MAG': QColor(182, 186, 189),
        'TSU': QColor(102, 146, 255),   # RB - 淺藍色
        'RIC': QColor(102, 146, 255),
        'BOT': QColor(82, 226, 82),     # Kick Sauber - 綠色
        'ZHO': QColor(82, 226, 82),
        'ALB': QColor(100, 196, 255),   # Williams - 淺藍色
        'SAR': QColor(100, 196, 255),
    }
    
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
        
        # 啟用滑鼠追蹤
        self.setMouseTracking(True)
        
        # 設置最小尺寸（與其他通用模組一致：Rain, Tire, Driver Lap 都是 200x100）
        self.setMinimumSize(200, 100)  # 統一為 200x100，提供更高的佈局靈活性
        
        print("[BOXPLOT_CHART] 圖表組件初始化完成 (QPainter 版本)")
        
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
                print("[WARNING] [BOXPLOT_CHART] 無效的數據格式")
                return
                
            self.current_data = data
            self.driver_laptimes = data.get('driver_laptimes', {})
            self.statistics = data.get('statistics', {})
            
            if not self.driver_laptimes:
                print("[WARNING] [BOXPLOT_CHART] 沒有圈速數據")
                self.update()
                return
                
            # 計算 Y 軸範圍
            self._calculate_y_range()
            
            print(f"[BOXPLOT_CHART] 更新數據: {len(self.driver_laptimes)} 位車手")
            self.update()  # 觸發重繪
            
        except Exception as e:
            print(f"[ERROR] [BOXPLOT_CHART] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
            
    def _calculate_y_range(self):
        """計算 Y 軸的合適範圍"""
        if not self.driver_laptimes:
            self.y_min = 0.0
            self.y_max = 100.0
            return
            
        all_times = []
        for lap_times in self.driver_laptimes.values():
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
            
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
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
            
        # 繪製標題
        self._draw_title(painter)
        
        # 繪製圖例
        self._draw_legend(painter)
        
        # 繪製工具提示
        if self.hover_driver:
            self._draw_tooltip(painter)
            
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
        
        # Y 軸標題
        painter.save()
        painter.translate(15, self.chart_rect.center().y())
        painter.rotate(-90)
        title_font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(
            QRect(-100, -10, 200, 20),
            Qt.AlignCenter,
            tr("lap_box_plot.y_axis_title", "Lap Time (seconds)")
        )
        painter.restore()
        
        # X 軸標題
        painter.setFont(title_font)
        painter.drawText(
            QRect(
                self.chart_rect.left(),
                self.chart_rect.bottom() + 60,
                self.chart_rect.width(),
                20
            ),
            Qt.AlignCenter,
            tr("lap_box_plot.x_axis_title", "Driver Code")
        )
        
    def _draw_box_plots(self, painter: QPainter):
        """繪製所有車手的箱型圖"""
        if not self.driver_laptimes:
            return
            
        drivers = sorted(self.driver_laptimes.keys())
        n_drivers = len(drivers)
        
        if n_drivers == 0:
            return
            
        # 計算箱型圖位置
        box_spacing = self.chart_rect.width() / (n_drivers + 1)
        box_width = min(40, box_spacing * 0.6)
        
        for i, driver in enumerate(drivers):
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
        """繪製單個車手的箱型圖"""
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
            team_color = self.TEAM_COLORS.get(driver, QColor(128, 128, 128))
            
            # 檢查是否懸停
            is_hovered = (driver == self.hover_driver)
            
            # 繪製箱體 (Q1 到 Q3)
            box_rect = QRectF(
                x_center - box_width / 2,
                time_to_y(q3),
                box_width,
                time_to_y(q1) - time_to_y(q3)
            )
            
            # 箱體填充顏色（懸停時加深）
            fill_color = team_color if not is_hovered else team_color.darker(110)
            fill_color.setAlpha(180)
            
            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(Qt.black, 2 if is_hovered else 1.5))
            painter.drawRect(box_rect)
            
            # 繪製中位數線（紅色粗線）
            painter.setPen(QPen(QColor(220, 20, 20), 3))
            painter.drawLine(
                QPoint(int(x_center - box_width / 2), int(time_to_y(median))),
                QPoint(int(x_center + box_width / 2), int(time_to_y(median)))
            )
            
            # 繪製鬚線
            painter.setPen(QPen(Qt.black, 1.5, Qt.SolidLine))
            
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
            
            # 繪製異常值（紅色圓點）
            if len(outliers) > 0:
                painter.setPen(QPen(Qt.black, 1))
                painter.setBrush(QBrush(QColor(220, 20, 20)))
                for outlier in outliers:
                    painter.drawEllipse(
                        QPoint(int(x_center), int(time_to_y(outlier))),
                        3, 3
                    )
                    
            # 繪製車手代碼標籤
            label_font = QFont("Arial", 10, QFont.Bold if is_hovered else QFont.Normal)
            painter.setFont(label_font)
            painter.setPen(QPen(Qt.black))
            painter.drawText(
                QRect(
                    int(x_center - box_width),
                    self.chart_rect.bottom() + 5,
                    int(box_width * 2),
                    20
                ),
                Qt.AlignCenter,
                driver
            )
            
        except Exception as e:
            print(f"[ERROR] [BOXPLOT_CHART] 繪製箱型圖失敗 ({driver}): {e}")
            
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
            (tr("lap_box_plot.legend_box", "Box: Q1-Q3"), QColor(150, 150, 150), "box"),
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
        
        # 繪製背景（白底黑字）
        painter.fillRect(tooltip_rect, QColor(255, 255, 255, 250))  # 白色背景，高不透明度
        painter.setPen(QPen(QColor(100, 100, 100), 1))  # 灰色邊框
        painter.drawRect(tooltip_rect)
        
        # 繪製文字（黑色）
        painter.setPen(QPen(Qt.black))
        for i, line in enumerate(lines):
            painter.drawText(
                tooltip_x + 10,
                tooltip_y + 15 + i * line_height,
                line
            )
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件"""
        if not self.driver_laptimes:
            return
            
        # 檢測滑鼠是否在某個箱型圖上
        drivers = sorted(self.driver_laptimes.keys())
        n_drivers = len(drivers)
        
        if n_drivers == 0:
            return
            
        box_spacing = self.chart_rect.width() / (n_drivers + 1)
        box_width = min(40, box_spacing * 0.6)
        
        mouse_x = event.pos().x()
        mouse_y = event.pos().y()
        
        # 檢查是否在圖表區域內
        if not self.chart_rect.contains(event.pos()):
            if self.hover_driver:
                self.hover_driver = None
                self.hover_position = None
                self.update()
            return
            
        # 查找最近的箱型圖
        found_driver = None
        for i, driver in enumerate(drivers):
            x_center = self.chart_rect.left() + (i + 1) * box_spacing
            
            # 檢查 X 座標是否在箱型圖範圍內
            if abs(mouse_x - x_center) < box_width:
                found_driver = driver
                break
                
        if found_driver != self.hover_driver:
            self.hover_driver = found_driver
            self.hover_position = event.pos() if found_driver else None
            self.update()
            
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
                print("[WARNING] [BOXPLOT_CHART] 無數據可匯出")
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
                print(f"[BOXPLOT_CHART] 圖表已匯出: {filepath}")
            else:
                print(f"[ERROR] [BOXPLOT_CHART] 圖表匯出失敗")
                
            return success
            
        except Exception as e:
            print(f"[ERROR] [BOXPLOT_CHART] 匯出圖表失敗: {e}")
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
        print("[BOXPLOT_CHART] 圖表已清空")
        
    def get_current_data(self) -> Optional[Dict]:
        """獲取當前數據"""
        return self.current_data
