#!/usr/bin/env python3
"""
PedalBehaviorStackedBarChartWidget - 油門/煞車行為疊加棒狀圖組件
================================================================

功能：
- 使用 PyQt5 QPainter 繪製垂直疊加棒狀圖（100% Qt 原生）
- 顯示所有車手的 Pedal State 分布（4 種狀態）
- 應用車隊配色方案標記車手
- 固定 Pedal State 顏色（throttle_only=綠、brake_only=紅、trail_braking=橙、coasting=灰）
- Y 軸固定為 0-100%
- 支援圖表匯出（PNG, JPG）
- 支援多國語言（i18n）

Author: F1T Team
Date: 2026-01-12
Version: 1.0.0
"""

from PyQt5.QtWidgets import QWidget, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QFontMetrics,
    QMouseEvent, QImage
)
from typing import Dict, List, Any, Optional, Tuple

from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider
from core.logger import get_logger

logger = get_logger(__name__)


class PedalBehaviorStackedBarChartWidget(QWidget):
    """油門/煞車行為疊加棒狀圖組件（純 QPainter 實現）"""
    
    # Pedal State 固定顏色（淺色系）
    PEDAL_STATE_COLORS = {
        'throttle_only': QColor(144, 238, 144),    # 淺綠色
        'brake_only': QColor(255, 182, 193),       # 淺紅色
        'trail_braking': QColor(255, 218, 185),    # 淺橙色
        'coasting': QColor(211, 211, 211)          # 淺灰色
    }
    
    # 信號
    chart_clicked = pyqtSignal(str)  # 點擊車手棒時發射車手代碼
    
    def __init__(self, parent=None):
        """初始化圖表組件"""
        super().__init__(parent)
        
        # 數據屬性
        self.driver_pedal_data: Dict[str, Dict[str, float]] = {}
        self.current_data: Optional[Dict] = None
        
        # 佈局參數
        self.margin_left = 60
        self.margin_right = 30
        self.margin_top = 60  # 增加上方空間給 tooltip
        self.margin_bottom = 40  # 減少底部空間（標籤水平顯示）
        
        # 圖表區域
        self.chart_rect = QRect()
        
        # 懸停狀態
        self.hover_driver = None
        self.hover_position = None
        
        # 啟用滑鼠追蹤
        self.setMouseTracking(True)
        
        # 設置最小尺寸
        self.setMinimumSize(200, 100)
        
        logger.debug("[PEDAL_CHART] 圖表組件初始化完成")
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新圖表數據並重繪
        
        參數:
            data: 包含以下鍵的字典
                - driver_pedal_data: Dict[str, Dict[str, float]] - 每位車手的 Pedal State 比例
                - metadata: Dict - 元數據（可選）
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[PEDAL_CHART] 無效的數據格式")
                self.driver_pedal_data = {}
                self.current_data = None
                self.update()
                return
            
            self.driver_pedal_data = data.get('driver_pedal_data', {})
            self.current_data = data
            
            # 確保載入正確年份的車手顏色
            self._ensure_color_palette_loaded(data)
            
            if not self.driver_pedal_data:
                logger.warning("[PEDAL_CHART] 沒有車手數據")
            else:
                logger.debug(f"[PEDAL_CHART] 更新數據: {len(self.driver_pedal_data)} 位車手")
            
            self.update()  # 觸發重繪
            
        except Exception as e:
            logger.error(f"[PEDAL_CHART] 更新數據失敗: {e}")
            self.driver_pedal_data = {}
            self.current_data = None
            self.update()
    
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 填充背景
        painter.fillRect(self.rect(), Qt.white)
        
        # 更新圖表區域
        self.chart_rect = QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        if self.driver_pedal_data:
            self._draw_chart(painter)
        else:
            self._draw_no_data_message(painter)
    
    def _draw_chart(self, painter: QPainter):
        """繪製疊加棒狀圖"""
        drivers = list(self.driver_pedal_data.keys())
        n_drivers = len(drivers)
        
        if n_drivers == 0:
            return
        
        # 繪製 Y 軸和標籤
        self._draw_y_axis(painter)
        
        # 計算棒寬度
        available_width = self.chart_rect.width()
        bar_width = min(available_width / (n_drivers * 1.5), 60)  # 最大 60px
        spacing = bar_width * 0.5
        total_width = n_drivers * bar_width + (n_drivers - 1) * spacing
        start_x = self.chart_rect.left() + (available_width - total_width) / 2
        
        # 繪製每位車手的疊加棒
        for i, driver_code in enumerate(drivers):
            pedal_data = self.driver_pedal_data[driver_code]
            x = start_x + i * (bar_width + spacing)
            
            self._draw_stacked_bar(painter, driver_code, pedal_data, x, bar_width)
        
        # 繪製圖例
        self._draw_legend(painter)
    
    def _draw_stacked_bar(self, painter: QPainter, driver_code: str, pedal_data: Dict[str, float], x: float, width: float):
        """繪製單個車手的疊加棒"""
        # 獲取車隊顏色（僅用於標籤）
        team_color = self._get_team_color(driver_code)
        
        # 計算每個 Pedal State 的高度
        chart_height = self.chart_rect.height()
        y_bottom = self.chart_rect.bottom()
        
        # 從下到上堆疊
        current_y = y_bottom
        
        # 繪製順序：throttle_only → brake_only → trail_braking → coasting
        pedal_states = ['throttle_only', 'brake_only', 'trail_braking', 'coasting']
        
        for state in pedal_states:
            ratio = pedal_data.get(state, 0.0)
            if ratio <= 0:
                continue
            
            # 計算高度（比例 * 圖表高度）
            height = ratio * chart_height
            
            # 繪製矩形
            color = self.PEDAL_STATE_COLORS[state]
            painter.fillRect(QRectF(x, current_y - height, width, height), QBrush(color))
            
            # 繪製內部邊框（淺灰色）
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawRect(QRectF(x, current_y - height, width, height))
            
            # 在區塊內顯示百分比數字（1px 黑字）
            if height >= 12:  # 只在區塊夠高時顯示
                painter.setPen(QPen(Qt.black, 1))
                num_font = QFont("Arial", 7)
                painter.setFont(num_font)
                percent_text = f"{ratio * 100:.0f}"
                text_rect = QRectF(x, current_y - height, width, height)
                painter.drawText(text_rect, Qt.AlignCenter, percent_text)
            
            # 更新 Y 位置
            current_y -= height
        
        # 繪製外框（固定黑色）
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(QRectF(x, y_bottom - chart_height, width, chart_height))
        
        # 繪製車手標籤（X 軸）- 水平顯示
        painter.setPen(QPen(team_color, 1))
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        
        label_y = y_bottom + 5
        label_rect = QRectF(x - 5, label_y, width + 10, 20)
        painter.drawText(label_rect, Qt.AlignCenter, driver_code)
        
        # 懸停效果（無粗體框線，僅顯示數值）
        if self.hover_driver == driver_code:
            self._draw_hover_tooltip(painter, driver_code, pedal_data, x, width)
    
    def _draw_y_axis(self, painter: QPainter):
        """繪製 Y 軸（0-100%）"""
        painter.setPen(QPen(Qt.black, 2))
        
        # Y 軸線
        painter.drawLine(
            self.chart_rect.left(), self.chart_rect.top(),
            self.chart_rect.left(), self.chart_rect.bottom()
        )
        
        # Y 軸刻度（0%, 25%, 50%, 75%, 100%）
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        for i in range(5):
            value = i * 25
            y = self.chart_rect.bottom() - (value / 100.0) * self.chart_rect.height()
            
            # 刻度線
            painter.drawLine(
                self.chart_rect.left() - 5, int(y),
                self.chart_rect.left(), int(y)
            )
            
            # 繪製 25%, 50%, 75% 的水平虛線（1px）
            if value in (25, 50, 75):
                dash_pen = QPen(QColor(180, 180, 180), 1, Qt.DashLine)
                painter.setPen(dash_pen)
                painter.drawLine(
                    self.chart_rect.left(), int(y),
                    self.chart_rect.right(), int(y)
                )
                painter.setPen(QPen(Qt.black, 2))  # 恢復原本的畫筆
            
            # 刻度標籤
            label = f"{value}%"
            label_rect = QRect(self.chart_rect.left() - 50, int(y) - 10, 40, 20)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label)
        
        # Y 軸標題
        painter.save()
        painter.translate(20, self.chart_rect.center().y())
        painter.rotate(-90)
        font_title = QFont("Arial", 11, QFont.Bold)
        painter.setFont(font_title)
        painter.drawText(QRect(-100, -10, 200, 20), Qt.AlignCenter, tr("Pedal State Distribution"))
        painter.restore()
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例（水平排列）"""
        box_size = 12
        spacing = 8
        
        font = QFont("Arial", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        pedal_states = [
            ('throttle_only', tr("Throttle Only")),
            ('brake_only', tr("Brake Only")),
            ('trail_braking', tr("Trail Braking")),
            ('coasting', tr("Coasting"))
        ]
        
        # 計算每個項目的寬度
        item_widths = []
        for state, label in pedal_states:
            text_width = fm.horizontalAdvance(label)
            item_width = box_size + 5 + text_width + spacing
            item_widths.append(item_width)
        
        total_width = sum(item_widths)
        
        # 水平居中放置（從圖表右側開始）
        legend_x = self.chart_rect.right() - total_width
        legend_y = 15
        
        current_x = legend_x
        for i, (state, label) in enumerate(pedal_states):
            # 繪製色塊
            color = self.PEDAL_STATE_COLORS[state]
            painter.fillRect(int(current_x), legend_y, box_size, box_size, QBrush(color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(int(current_x), legend_y, box_size, box_size)
            
            # 繪製標籤（水平）
            text_x = int(current_x) + box_size + 5
            text_y = legend_y + box_size - 2
            painter.drawText(text_x, text_y, label)
            
            current_x += item_widths[i]
    
    def _draw_hover_tooltip(self, painter: QPainter, driver_code: str, pedal_data: Dict[str, float], bar_x: float, bar_width: float):
        """繪製懸停時的數值 Tooltip（無粗體框線）"""
        if not self.hover_position:
            return
        
        # Tooltip 內容
        throttle = pedal_data.get('throttle_only', 0) * 100
        brake = pedal_data.get('brake_only', 0) * 100
        trail = pedal_data.get('trail_braking', 0) * 100
        coast = pedal_data.get('coasting', 0) * 100
        
        lines = [
            f"{driver_code}",
            f"Throttle: {throttle:.1f}%",
            f"Brake: {brake:.1f}%",
            f"Trail Braking: {trail:.1f}%",
            f"Coasting: {coast:.1f}%"
        ]
        
        # Tooltip 位置（在棒的上方）
        font = QFont("Arial", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        line_height = fm.height() + 2
        tooltip_width = max(fm.horizontalAdvance(line) for line in lines) + 16
        tooltip_height = len(lines) * line_height + 10
        
        # 計算位置（在棒的正上方）
        tooltip_x = bar_x + bar_width / 2 - tooltip_width / 2
        tooltip_y = self.chart_rect.top() - tooltip_height - 5
        
        # 確保不超出邊界
        if tooltip_x < 5:
            tooltip_x = 5
        if tooltip_x + tooltip_width > self.width() - 5:
            tooltip_x = self.width() - tooltip_width - 5
        if tooltip_y < 5:
            tooltip_y = self.chart_rect.top() + 5
        
        # 繪製 Tooltip 背景
        painter.fillRect(QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height), 
                        QBrush(QColor(255, 255, 240, 230)))  # 淺黃色背景
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height))
        
        # 繪製文字
        painter.setPen(QPen(Qt.black, 1))
        for i, line in enumerate(lines):
            text_y = tooltip_y + 8 + (i + 1) * line_height - 4
            if i == 0:  # 車手代碼用粗體
                bold_font = QFont("Arial", 9, QFont.Bold)
                painter.setFont(bold_font)
            else:
                painter.setFont(font)
            painter.drawText(int(tooltip_x + 8), int(text_y), line)
    
    def _draw_no_data_message(self, painter: QPainter):
        """繪製無數據訊息"""
        font = QFont("Arial", 14)
        painter.setFont(font)
        painter.setPen(QPen(Qt.gray, 1))
        painter.drawText(self.rect(), Qt.AlignCenter, tr("No Pedal Behavior Data"))
    
    def _ensure_color_palette_loaded(self, data: Dict[str, Any]):
        """確保載入正確年份的車手顏色"""
        target_year = None
        metadata = data.get('metadata', {})
        
        # 嘗試從 api_meta 獲取年份
        api_meta = data.get('api_meta', {})
        if api_meta:
            params = api_meta.get('params')
            if isinstance(params, dict):
                target_year = params.get('year') or params.get('season_year')
        
        # 嘗試從 metadata 獲取
        if target_year is None:
            target_year = metadata.get('season_year') or metadata.get('year')
        
        try:
            if target_year is not None:
                color_palette_provider.ensure_loaded(year=int(target_year))
            else:
                color_palette_provider.ensure_loaded()
        except Exception:
            pass  # Provider 已有預設回退機制
    
    def _get_team_color(self, driver_code: str) -> QColor:
        """
        獲取車手的車隊顏色
        
        支援純車手代碼（如 "ALB"）或帶 Stint 後綴（如 "ALB S1"）
        """
        # 提取純車手代碼（移除 " S{stint_id}" 後綴）
        # 例如 "ALB S3" → "ALB", "VER" → "VER"
        pure_driver_code = driver_code.split(' ')[0] if ' S' in driver_code else driver_code
        
        color = color_palette_provider.get_driver_color(pure_driver_code, format="qcolor")
        if isinstance(color, QColor):
            return QColor(color)
        return QColor(128, 128, 128)  # 預設灰色
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """處理滑鼠移動事件"""
        pos = event.pos()
        
        # 檢查是否懸停在某個棒上
        old_hover = self.hover_driver
        self.hover_driver = None
        
        if self.chart_rect.contains(pos):
            drivers = list(self.driver_pedal_data.keys())
            n_drivers = len(drivers)
            
            if n_drivers > 0:
                available_width = self.chart_rect.width()
                bar_width = min(available_width / (n_drivers * 1.5), 60)
                spacing = bar_width * 0.5
                total_width = n_drivers * bar_width + (n_drivers - 1) * spacing
                start_x = self.chart_rect.left() + (available_width - total_width) / 2
                
                for i, driver_code in enumerate(drivers):
                    x = start_x + i * (bar_width + spacing)
                    if x <= pos.x() <= x + bar_width:
                        self.hover_driver = driver_code
                        self.hover_position = pos
                        break
        
        if old_hover != self.hover_driver:
            self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """處理滑鼠點擊事件"""
        if event.button() == Qt.LeftButton and self.hover_driver:
            self.chart_clicked.emit(self.hover_driver)
    
    def contextMenuEvent(self, event):
        """右鍵選單"""
        menu = QMenu(self)
        
        export_action = QAction(tr("Export Chart"), self)
        export_action.triggered.connect(self._export_chart)
        menu.addAction(export_action)
        
        menu.exec_(event.globalPos())
    
    def _export_chart(self):
        """匯出圖表為圖片"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export Chart"),
            "pedal_behavior_chart.png",
            "PNG (*.png);;JPEG (*.jpg)"
        )
        
        if file_path:
            try:
                # 創建圖片
                image = QImage(self.size(), QImage.Format_ARGB32)
                image.fill(Qt.white)
                
                # 繪製到圖片
                painter = QPainter(image)
                self.render(painter)
                painter.end()
                
                # 儲存
                image.save(file_path)
                
                QMessageBox.information(
                    self,
                    tr("Export Successful"),
                    tr("Chart exported to: ") + file_path
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr("Export Failed"),
                    str(e)
                )
