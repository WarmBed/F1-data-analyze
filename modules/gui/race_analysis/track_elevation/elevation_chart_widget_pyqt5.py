#!/usr/bin/env python3
"""
賽道高程圖表元件 - PyQt5 原生繪圖版本
========================================

使用 FastF1 遙測數據中的 Z 軸（高度）繪製賽道高程剖面圖
支援連動管理器，可與 TrackMapWidget 同步

Author: F1T Team
Date: 2025-11-10
"""

from typing import Optional, List, Dict, Any
import numpy as np
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QFont, QPen, QColor, QPainter, QBrush, QMouseEvent, QWheelEvent

# 導入多國語言支援
from core.gui_i18n import tr
from core.logger import get_logger


logger = get_logger(__name__)

# 導入連動管理器
try:
    from modules.gui.lap_analysis.linkage import (
        LapAnalysisLinkageMixin, 
        LapAnalysisLinkageDrawingMixin, 
        linkage_manager
    )
except ImportError:
    LapAnalysisLinkageMixin = object
    LapAnalysisLinkageDrawingMixin = object
    linkage_manager = None
    logger.warning("ElevationChart: 連動管理器導入失敗")


class ElevationChartWidget(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """
    賽道高程圖表元件 - PyQt5 原生繪圖版本
    
    特點：
    - 使用 FastF1 Z 軸數據繪製高程剖面
    - 支援彎道標記
    - 支援連動管理器同步
    - 相對高度顯示（以最低點為 0）
    """
    
    # 信號定義
    chart_updated = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 初始化連動混入類
        self.__init_linkage__()
        
        # 設置更新回調
        self.update_callback = self.update
        
        # 基本屬性
        self.circuit_name = "Circuit"
        self.elevation_data: List[Dict[str, Any]] = []
        self.corner_data: List[Dict[str, Any]] = []
        
        # 處理後的數據（用於繪圖）
        self.distances_km: List[float] = []  # 距離（公里）
        self.elevations_relative: List[float] = []  # 相對高度（公尺，最低點為 0）
        self.elevations_absolute: List[float] = []  # 絕對高度（公尺）
        self.min_absolute_elevation: float = 0.0  # 最低點絕對高度
        
        # 顏色設定
        self.elevation_fill_color = QColor(52, 152, 219, 100)  # #3498db with alpha
        self.elevation_line_color = QColor(41, 128, 185)  # #2980b9
        self.corner_color = QColor(200, 0, 0)  # 紅色彎道標記
        self.grid_color = QColor(200, 200, 200)
        self.axis_color = QColor(50, 50, 50)
        self.text_color = QColor(50, 50, 50)
        
        # 繪圖參數
        self.margin_left = 80
        self.margin_right = 20
        self.margin_top = 60  # 增加上邊距以容納標題
        self.margin_bottom = 60  # 底部邊距（彎道標籤已移到框內，恢復正常邊距）
        
        # 數據範圍（會在載入數據時自動計算）
        self.min_distance_km = 0.0
        self.max_distance_km = 6.0
        self.min_elevation = 0.0
        self.max_elevation = 100.0
        
        # 滑鼠交互
        self.setMouseTracking(True)
        self.mouse_x = -1
        self.mouse_y = -1
        
        # 視圖範圍（用於縮放）
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_elevation = None
        self.view_max_elevation = None
        
        # 設置最小尺寸和擴展策略
        self.setMinimumSize(400, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 註冊到連動管理器
        if linkage_manager:
            linkage_manager.register_module(self, "elevation_chart")
            try:
                current_master_state = linkage_manager.is_master_linkage_enabled()
                self.set_master_linkage_enabled(current_master_state)
                logger.info(
                    "[ELEVATION_CHART] 已註冊到連動管理器，主開關狀態: %s",
                    "啟用" if current_master_state else "停用",
                )
            except Exception as e:
                logger.error("[ELEVATION_CHART] 同步連動狀態失敗: %s", e)
        else:
            logger.warning("[ELEVATION_CHART] 連動管理器不可用")
    
    def set_circuit_name(self, name: str):
        """設置賽道名稱"""
        self.circuit_name = str(name)
        self.update()
    
    def plot_elevation(self, 
                      track_outline: List[Dict[str, Any]], 
                      official_corners: List[Dict[str, Any]] = None):
        """
        繪製高程剖面圖
        
        Args:
            track_outline: 賽道輪廓數據，包含 distance_m 和 elevation (Z)
            official_corners: 官方彎道數據（可選）
        """
        logger.debug("[DEBUG] === ElevationChartWidget.plot_elevation() 開始執行 ===")
        logger.debug("[DEBUG] track_outline 數量: %s", len(track_outline))
        logger.debug("[DEBUG] official_corners 類型: %s", type(official_corners))
        logger.debug("[DEBUG] official_corners 數量: %s", len(official_corners) if official_corners else 0)
        
        if official_corners:
            logger.debug("[DEBUG] 收到 %s 個彎道", len(official_corners))
            if len(official_corners) > 0:
                first = official_corners[0]
                last = official_corners[-1]
                logger.debug("[DEBUG]    第 1 個彎道: %s", first)
                logger.debug("[DEBUG]    最後 1 個彎道: %s", last)
        else:
            logger.debug("[DEBUG] official_corners 為 None 或空")
        
        if not track_outline:
            logger.warning("[ELEVATION_CHART] 無高程數據")
            self.elevation_data = []
            self.corner_data = []
            self.distances_km = []
            self.elevations_relative = []
            self.elevations_absolute = []
            self.update()
            return
        
        self.elevation_data = track_outline
        self.corner_data = official_corners or []
        
        logger.debug("[DEBUG] self.corner_data 最終狀態: 長度=%s", len(self.corner_data))
        
        # 提取距離和高度數據
        distances_m = []
        elevations_m = []
        
        for point in track_outline:
            dist = point.get('distance_m', 0.0)
            elev = point.get('elevation') or point.get('z', 0.0)
            
            if elev != 0.0:  # 過濾無效數據
                distances_m.append(dist)
                # ✅ 移除重複除以 10：數據已在 data_loader 中處理
                elevations_m.append(elev)
        
        if not distances_m or not elevations_m:
            logger.warning("[ELEVATION_CHART] 無有效高程數據")
            self.distances_km = []
            self.elevations_relative = []
            self.elevations_absolute = []
            self.update()
            return
        
        # 轉換為公里
        self.distances_km = [d / 1000.0 for d in distances_m]
        
        # 儲存絕對高度
        self.elevations_absolute = elevations_m
        
        # 轉換為相對高度（以最低點為 0）
        self.min_absolute_elevation = min(elevations_m)
        self.elevations_relative = [e - self.min_absolute_elevation for e in elevations_m]
        
        # 計算數據範圍
        self.min_distance_km = min(self.distances_km)
        self.max_distance_km = max(self.distances_km)
        self.min_elevation = 0.0  # 相對高度從 0 開始
        self.max_elevation = max(self.elevations_relative)
        
        # 增加 Y 軸上邊界 10% 以留出空間給彎道標記
        elevation_padding = self.max_elevation * 0.1
        self.max_elevation = self.max_elevation + elevation_padding
        
        # 重置視圖範圍
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_elevation = None
        self.view_max_elevation = None
        
        logger.debug("[ELEVATION_CHART] 繪製高程: %s 個數據點", len(self.distances_km))
        logger.debug(
            "[ELEVATION_CHART]   距離範圍: %.2f ~ %.2f km",
            self.min_distance_km,
            self.max_distance_km,
        )
        logger.debug(
            "[ELEVATION_CHART]   絕對高度: %.2f ~ %.2f m",
            self.min_absolute_elevation,
            max(self.elevations_absolute),
        )
        logger.debug(
            "[ELEVATION_CHART]   相對高度: 0.00 ~ %.2f m",
            self.max_elevation,
        )
        logger.debug("[ELEVATION_CHART]   FastF1 Z 軸已在 data_loader 中除以 10")
        
        # 觸發重繪
        self.update()
        self.chart_updated.emit()
    
    def clear_chart(self):
        """清空圖表"""
        self.elevation_data = []
        self.corner_data = []
        self.distances_km = []
        self.elevations_relative = []
        self.elevations_absolute = []
        self.update()
    
    def paintEvent(self, event):
        """繪製圖表"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 背景
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            
            # 檢查是否有數據
            if not self.distances_km or not self.elevations_relative:
                self._draw_empty_message(painter)
                return
            
            # 計算繪圖區域
            chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            
            if chart_rect.width() <= 0 or chart_rect.height() <= 0:
                return
            
            # 繪製網格和座標軸
            self._draw_grid_and_axes(painter, chart_rect)
            
            # 繪製高程剖面（面積填充 + 線條）
            self._draw_elevation_profile(painter, chart_rect)
            
            # 繪製彎道標記
            if self.corner_data:
                self._draw_corner_markers(painter, chart_rect)
            
            # 繪製標題
            self._draw_title(painter)
            
            # 繪製連動標記（懸停線和固定線）
            if linkage_manager:
                self._draw_linkage_indicators(painter, chart_rect)
                
        except Exception as e:
            logger.error("[ELEVATION_CHART] paintEvent 錯誤: %s", e)
            import traceback
            traceback.print_exc()
    
    def _draw_empty_message(self, painter: QPainter):
        """繪製空白訊息"""
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Arial", 14))
        painter.drawText(self.rect(), Qt.AlignCenter, "Waiting for data...")
    
    def _draw_title(self, painter: QPainter):
        """繪製標題"""
        # ✅ 極簡標題：僅顯示賽道名稱和高度差
        if self.elevations_absolute and self.elevations_relative:
            max_rel = max(self.elevations_relative)
            title_text = f"{self.circuit_name} - Elevation Change: {max_rel:.1f}m"
        else:
            title_text = f"{self.circuit_name} - Elevation Profile"
        
        painter.setPen(QPen(self.text_color))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        title_rect = QRect(0, 5, self.width(), self.margin_top - 10)
        painter.drawText(title_rect, Qt.AlignCenter, title_text)
    
    def _draw_grid_and_axes(self, painter: QPainter, chart_rect: QRect):
        """繪製網格和座標軸"""
        # 確定顯示範圍
        min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
        max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
        min_elev = self.view_min_elevation if self.view_min_elevation is not None else self.min_elevation
        max_elev = self.view_max_elevation if self.view_max_elevation is not None else self.max_elevation
        
        # 繪製背景
        painter.fillRect(chart_rect, QColor(248, 249, 250))
        
        # 網格設定
        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))
        
        # 計算網格間距（距離：每 1 km 一條線）
        dist_range = max_dist - min_dist
        if dist_range > 0:
            dist_step = 1.0  # 每 1 km
            num_dist_lines = int(dist_range / dist_step) + 1
            
            for i in range(num_dist_lines + 1):
                dist_value = min_dist + i * dist_step
                if dist_value > max_dist:
                    break
                
                x = chart_rect.left() + int((dist_value - min_dist) / dist_range * chart_rect.width())
                if chart_rect.left() <= x <= chart_rect.right():
                    painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
        
        # 計算網格間距（高度：自適應）
        elev_range = max_elev - min_elev
        if elev_range > 0:
            # 自適應步進：10m, 20m, 50m 等
            if elev_range <= 50:
                elev_step = 10
            elif elev_range <= 100:
                elev_step = 20
            else:
                elev_step = 50
            
            num_elev_lines = int(elev_range / elev_step) + 1
            
            for i in range(num_elev_lines + 1):
                elev_value = min_elev + i * elev_step
                if elev_value > max_elev:
                    break
                
                y = chart_rect.bottom() - int((elev_value - min_elev) / elev_range * chart_rect.height())
                if chart_rect.top() <= y <= chart_rect.bottom():
                    painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)
        
        # 繪製座標軸
        painter.setPen(QPen(self.axis_color, 2))
        painter.drawRect(chart_rect)
        
        # X 軸刻度標籤（距離）- 改為每 1 km 顯示
        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(self.text_color))
        
        if dist_range > 0:
            dist_step = 1.0  # 每 1 km 顯示一次
            num_dist_ticks = int(dist_range / dist_step) + 1
            
            for i in range(num_dist_ticks + 1):
                dist_value = min_dist + i * dist_step
                if dist_value > max_dist:
                    break
                
                x = chart_rect.left() + int((dist_value - min_dist) / dist_range * chart_rect.width())
                if chart_rect.left() <= x <= chart_rect.right():
                    label = f"{dist_value:.1f}"
                    painter.drawText(x - 30, chart_rect.bottom() + 15, 60, 20, Qt.AlignCenter, label)
        
        # X 軸標籤
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        x_label_rect = QRect(chart_rect.left(), chart_rect.bottom() + 35, chart_rect.width(), 20)
        painter.drawText(x_label_rect, Qt.AlignCenter, "Track Distance (km)")
        
        # Y 軸刻度標籤（高度）
        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(self.text_color))  # ✅ 修復：確保文字顏色正確設置
        
        if elev_range > 0:
            if elev_range <= 50:
                elev_step = 10
            elif elev_range <= 100:
                elev_step = 20
            else:
                elev_step = 50
            
            num_elev_ticks = int(elev_range / elev_step) + 1
            
            for i in range(num_elev_ticks + 1):
                elev_value = min_elev + i * elev_step
                if elev_value > max_elev:
                    break
                
                y = chart_rect.bottom() - int((elev_value - min_elev) / elev_range * chart_rect.height())
                if chart_rect.top() <= y <= chart_rect.bottom():
                    label = f"{int(elev_value)}"
                    # ✅ 修復：增加繪製區域寬度，確保數字顯示完整
                    painter.drawText(chart_rect.left() - 70, y - 10, 60, 20, Qt.AlignRight | Qt.AlignVCenter, label)
        
        # Y 軸標籤（垂直文字）
        painter.save()
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.translate(15, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(-50, -5, 100, 20, Qt.AlignCenter, "Elevation (m)")
        painter.restore()
    
    def _draw_elevation_profile(self, painter: QPainter, chart_rect: QRect):
        """繪製高程剖面（面積填充 + 線條）"""
        if len(self.distances_km) < 2:
            return
        
        # 確定顯示範圍
        min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
        max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
        min_elev = self.view_min_elevation if self.view_min_elevation is not None else self.min_elevation
        max_elev = self.view_max_elevation if self.view_max_elevation is not None else self.max_elevation
        
        dist_range = max_dist - min_dist
        elev_range = max_elev - min_elev
        
        if dist_range <= 0 or elev_range <= 0:
            return
        
        # 轉換數據到螢幕座標
        points = []
        for i in range(len(self.distances_km)):
            dist = self.distances_km[i]
            elev = self.elevations_relative[i]
            
            if min_dist <= dist <= max_dist:
                x = chart_rect.left() + int((dist - min_dist) / dist_range * chart_rect.width())
                y = chart_rect.bottom() - int((elev - min_elev) / elev_range * chart_rect.height())
                points.append(QPoint(x, y))
        
        if len(points) < 2:
            return
        
        # 繪製面積填充
        from PyQt5.QtGui import QPolygon
        fill_points = points.copy()
        fill_points.append(QPoint(points[-1].x(), chart_rect.bottom()))
        fill_points.append(QPoint(points[0].x(), chart_rect.bottom()))
        
        painter.setBrush(QBrush(self.elevation_fill_color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygon(fill_points))
        
        # 繪製線條
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.elevation_line_color, 2))
        painter.drawPolyline(QPolygon(points))
    
    def _draw_corner_markers(self, painter: QPainter, chart_rect: QRect):
        """繪製彎道標記（垂直虛線 + 底部編號）"""
        if not self.corner_data or not self.distances_km:
            logger.debug("[ELEVATION_CHART] 彎道數據: %s 個", len(self.corner_data) if self.corner_data else 0)
            return
        
        logger.debug("[ELEVATION_CHART] 開始繪製彎道標記: %s 個", len(self.corner_data))
        
        # 確定顯示範圍
        min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
        max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
        min_elev = self.view_min_elevation if self.view_min_elevation is not None else self.min_elevation
        max_elev = self.view_max_elevation if self.view_max_elevation is not None else self.max_elevation
        
        dist_range = max_dist - min_dist
        elev_range = max_elev - min_elev
        
        if dist_range <= 0 or elev_range <= 0:
            logger.warning(
                "[ELEVATION_CHART] 距離或高度範圍無效: dist=%s, elev=%s",
                dist_range,
                elev_range,
            )
            return
        
        # 建立距離到高度的插值
        distances_m = [d * 1000 for d in self.distances_km]
        
        drawn_count = 0
        for corner in self.corner_data:
            corner_num = corner.get('number', 0)
            corner_dist_m = corner.get('distance', 0.0)
            
            logger.debug("[ELEVATION_CHART] 彎道 %s: distance=%sm", corner_num, corner_dist_m)
            
            if corner_dist_m == 0.0:
                logger.debug("[ELEVATION_CHART]   跳過: 距離為 0")
                continue
            
            corner_dist_km = corner_dist_m / 1000.0
            
            # 檢查彎道是否在顯示範圍內
            if corner_dist_km < min_dist or corner_dist_km > max_dist:
                logger.debug(
                    "[ELEVATION_CHART]   跳過: 超出範圍 (%.2f - %.2f km)",
                    min_dist,
                    max_dist,
                )
                continue
            
            # 使用線性插值找到對應的相對高度
            if corner_dist_m < distances_m[0] or corner_dist_m > distances_m[-1]:
                logger.debug(
                    "[ELEVATION_CHART]   跳過: 超出數據範圍 (%.0f - %.0f m)",
                    distances_m[0],
                    distances_m[-1],
                )
                continue
            
            corner_elev_relative = np.interp(corner_dist_m, distances_m, self.elevations_relative)
            
            # 計算 X 座標
            x = chart_rect.left() + int((corner_dist_km - min_dist) / dist_range * chart_rect.width())
            
            # 計算 Y 座標（彎道在曲線上的高度位置）
            y_curve = chart_rect.bottom() - int((corner_elev_relative - min_elev) / elev_range * chart_rect.height())
            
            logger.debug(
                "[ELEVATION_CHART]   繪製位置: x=%s, elev=%.1fm, y=%s",
                x,
                corner_elev_relative,
                y_curve,
            )
            
            # === 繪製垂直虛線（從圖表頂部到底部）===
            painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))  # 灰色虛線
            painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
            
            # === 繪製彎道編號（顯示在曲線上方，框內）===
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            label_text = f"T{corner_num}"  # 加上 "T" 前綴
            
            # 計算標籤尺寸
            font_metrics = painter.fontMetrics()
            label_width = font_metrics.width(label_text)
            label_height = font_metrics.height()
            
            # 標籤位置（曲線上方 10px，且在圖表框內）
            label_x = x - label_width // 2
            label_y = y_curve - 10  # 曲線上方 10 像素
            
            # 確保標籤不超出圖表頂部
            if label_y < chart_rect.top() + label_height:
                label_y = chart_rect.top() + label_height
            
            # 繪製標籤背景（半透明白色，增強可讀性）
            padding = 2
            bg_rect = QRect(label_x - padding, label_y - label_height - padding,
                           label_width + 2 * padding, label_height + 2 * padding)
            painter.fillRect(bg_rect, QColor(255, 255, 255, 180))
            
            # 繪製彎道編號文字（深藍色）
            painter.setPen(QPen(QColor(30, 60, 120)))  # 深藍色
            painter.drawText(label_x, label_y, label_text)
            
            drawn_count += 1
        
        logger.debug("[ELEVATION_CHART] 完成繪製: %s/%s 個彎道標記", drawn_count, len(self.corner_data))
    
    def _draw_linkage_indicators(self, painter: QPainter, chart_rect: QRect):
        """繪製連動指示器（懸停線和固定線）"""
        # 繪製懸停線（鼠標移動觸發）
        if self.show_linkage_line and self.linkage_distance_value is not None:
            min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
            max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
            dist_range = max_dist - min_dist
            
            if dist_range > 0:
                # 將距離值從公尺轉換為公里
                linkage_dist_km = self.linkage_distance_value / 1000.0
                
                if min_dist <= linkage_dist_km <= max_dist:
                    x = chart_rect.left() + int((linkage_dist_km - min_dist) / dist_range * chart_rect.width())
                    
                    painter.setPen(QPen(QColor(0, 255, 0, 150), 2, Qt.DashLine))
                    painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
        
        # 繪製固定線（點擊觸發）
        if self.show_fixed_line and self.fixed_distance_value is not None:
            min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
            max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
            dist_range = max_dist - min_dist
            
            if dist_range > 0:
                # 將距離值從公尺轉換為公里
                fixed_dist_km = self.fixed_distance_value / 1000.0
                
                if min_dist <= fixed_dist_km <= max_dist:
                    x = chart_rect.left() + int((fixed_dist_km - min_dist) / dist_range * chart_rect.width())
                    
                    painter.setPen(QPen(QColor(255, 255, 0, 200), 3))
                    painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件 - 觸發連動"""
        if not self.distances_km or not self.elevations_relative:
            return
        
        # 計算圖表區域
        chart_rect = QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        if not chart_rect.contains(event.pos()):
            return
        
        # 確定顯示範圍
        min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
        max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
        min_elev = self.view_min_elevation if self.view_min_elevation is not None else self.min_elevation
        max_elev = self.view_max_elevation if self.view_max_elevation is not None else self.max_elevation
        
        dist_range = max_dist - min_dist
        elev_range = max_elev - min_elev
        
        if dist_range <= 0 or elev_range <= 0:
            return
        
        # 計算距離值（公里）
        rel_x = (event.x() - chart_rect.left()) / chart_rect.width()
        distance_km = min_dist + rel_x * dist_range
        
        # 轉換為公尺（連動系統使用公尺）
        distance_m = distance_km * 1000.0
        
        # 計算 Y 軸相對位置
        rel_y = 1.0 - (event.y() - chart_rect.top()) / chart_rect.height()
        rel_y = max(0.0, min(1.0, rel_y))
        
        # 發送連動信號（添加節流：只在距離變化超過閾值時發送）
        if linkage_manager and self.master_linkage_enabled and self.linkage_enabled:
            # 節流機制：避免過度觸發 update()
            if not hasattr(self, '_last_linkage_distance') or self._last_linkage_distance is None:
                self._last_linkage_distance = distance_m
                linkage_manager.send_x_linkage(distance_m, rel_y, sender=self)
            else:
                # 只在距離變化超過 50 公尺時發送
                distance_diff = abs(distance_m - self._last_linkage_distance)
                if distance_diff > 50.0:  # 節流閾值：50 公尺
                    self._last_linkage_distance = distance_m
                    linkage_manager.send_x_linkage(distance_m, rel_y, sender=self)
    
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠點擊事件 - 固定標記"""
        if event.button() != Qt.LeftButton:
            return
        
        if not self.distances_km or not self.elevations_relative:
            return
        
        # 計算圖表區域
        chart_rect = QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        if not chart_rect.contains(event.pos()):
            return
        
        # 確定顯示範圍
        min_dist = self.view_min_distance if self.view_min_distance is not None else self.min_distance_km
        max_dist = self.view_max_distance if self.view_max_distance is not None else self.max_distance_km
        dist_range = max_dist - min_dist
        
        if dist_range <= 0:
            return
        
        # 計算距離值（公里）
        rel_x = (event.x() - chart_rect.left()) / chart_rect.width()
        distance_km = min_dist + rel_x * dist_range
        
        # 轉換為公尺（連動系統使用公尺）
        distance_m = distance_km * 1000.0
        
        # 發送點擊連動信號
        if linkage_manager and self.master_linkage_enabled and self.linkage_enabled:
            linkage_manager.send_click_linkage(distance_m, sender=self)
    
    def wheelEvent(self, event: QWheelEvent):
        """滑鼠滾輪事件 - 縮放"""
        # 暫時不實現縮放功能
        pass
    
    # ============================================================
    # 連動接口方法（由 LapAnalysisLinkageMixin 要求實現）
    # ============================================================
    
    def on_x_linkage_received(self, distance_value: float, y_relative: float) -> None:
        """
        接收連動信號（懸停線）
        
        Args:
            distance_value: 距離值（公尺）
            y_relative: Y 軸相對位置（0.0 ~ 1.0）
        """
        if not self.master_linkage_enabled or not self.linkage_enabled:
            return
        
        # 更新連動狀態
        self.linkage_distance_value = distance_value
        self.linkage_y_relative = y_relative
        self.show_linkage_line = True
        
        # 觸發重繪
        if self.update_callback:
            self.update_callback()
        else:
            self.update()
    
    def on_x_linkage_clear(self) -> None:
        """清除懸停連動線"""
        if not self.linkage_enabled:
            return
        
        self.show_linkage_line = False
        self.linkage_distance_value = None
        
        # 觸發重繪
        if self.update_callback:
            self.update_callback()
        else:
            self.update()
    
    def on_click_linkage_received(self, distance_value: float) -> None:
        """
        接收點擊連動信號（固定線）
        
        Args:
            distance_value: 距離值（公尺）
        """
        if not self.master_linkage_enabled or not self.linkage_enabled:
            return
        
        # 更新固定線狀態
        self.fixed_distance_value = distance_value
        self.show_fixed_line = True
        
        # 觸發重繪
        if self.update_callback:
            self.update_callback()
        else:
            self.update()
    
    def on_click_linkage_clear(self) -> None:
        """清除固定連動線"""
        if not self.linkage_enabled:
            return
        
        self.show_fixed_line = False
        self.fixed_distance_value = None
        
        # 觸發重繪
        if self.update_callback:
            self.update_callback()
        else:
            self.update()
    
    def set_linkage_enabled(self, enabled: bool) -> None:
        """設置連動啟用狀態"""
        new_state = bool(enabled)
        if self.linkage_enabled == new_state:
            return
        
        self.linkage_enabled = new_state
        
        # 清除連動標記
        if not self.linkage_enabled:
            self.show_linkage_line = False
            self.show_fixed_line = False
            self.linkage_distance_value = None
            self.fixed_distance_value = None
            
            if self.update_callback:
                self.update_callback()
            else:
                self.update()
    
    def set_master_linkage_enabled(self, enabled: bool) -> None:
        """設置主連動開關狀態"""
        new_state = bool(enabled)
        if self.master_linkage_enabled == new_state:
            return
        
        self.master_linkage_enabled = new_state
        
        # 清除連動標記
        if not self.master_linkage_enabled:
            self.show_linkage_line = False
            self.show_fixed_line = False
            self.linkage_distance_value = None
            self.fixed_distance_value = None
            
            if self.update_callback:
                self.update_callback()
            else:
                self.update()
    
    def on_master_linkage_changed(self, enabled: bool) -> None:
        """響應主連動開關變更"""
        self.set_master_linkage_enabled(enabled)


__all__ = ['ElevationChartWidget']
