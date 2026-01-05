# -*- coding: utf-8 -*-
"""專責處理多車手油門折線圖的圖表元件。"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen

from core.gui_i18n import tr
from modules.gui.universal_chart_widget import ChartDataSeries
from modules.gui.themes.color_palette_provider import color_palette_provider

from .linked_chart_widget import LinkedUniversalChartWidget

logger = logging.getLogger(__name__)

# 未選中車手的灰色
GRAY_COLOR = QColor(180, 180, 180)


class ThrottleDurationChartWidget(LinkedUniversalChartWidget):
    """呈現多車手全油門百分比折線圖。"""
    
    # 縮放變更信號（供外部同步使用）
    zoom_changed = pyqtSignal(bool)  # True = 已縮放, False = 重置

    def __init__(self, parent=None):
        super().__init__(title=tr("throttle_line_chart.throttle_duration_title", "Full Throttle Duration"), parent=parent)

        # ⚙️ Throttle Line Chart 專屬設定：禁用舊功能，使用新的通用互動系統
        self.show_value_tooltips = False  # 禁用垂直虛線旁的數值提示
        self.mouse_x = -1  # 禁用垂直虛線追蹤（設為 -1 使其不顯示）

        self.set_axis_labels(
            tr("throttle_line_chart.axis_lap", "Lap"),
            tr("throttle_line_chart.axis_full_throttle_percent", "Full Throttle %"),  # 左Y軸：百分比
            tr("throttle_line_chart.axis_full_throttle_seconds", "Full Throttle Time"),  # 右Y軸：秒數（備用）
            x_unit="",
            left_y_unit="%",   # 左Y軸單位：百分比
            right_y_unit="s",  # 右Y軸單位：秒數（備用）
        )

        # 儲存多車手的 tooltip 數據
        self._tooltip_maps: Dict[str, Dict[int, Dict[str, object]]] = {}  # {driver_code: {lap: tooltip_data}}
        self._tooltip_map: Dict[int, Dict[str, object]] = {}  # 向下相容性
        
        self._active_settings: Dict[str, bool] = {
            "show_full_duration": False,
            "show_ratio": True,
            "show_average": False,
            "highlight_threshold": False,
        }
        
        # 追蹤已使用的車隊顏色（用於同隊虛線區分）
        self._team_color_usage: Dict[str, int] = {}  # {team_name: count}
        
        # 右鍵框選縮放功能變數（複製自 LaptimeChartWidget）
        self.zoom_rect_start: Optional[QPoint] = None  # 右鍵框選起始點
        self.zoom_rect_end: Optional[QPoint] = None    # 右鍵框選結束點
        self.is_zooming: bool = False      # 是否正在框選
        self.zoom_x_range: Optional[Tuple[float, float]] = None  # 自定義 X 軸範圍 (縮放後)
        self.zoom_y_range: Optional[Tuple[float, float]] = None  # 自定義 Y 軸範圍 (縮放後)
        self.is_zoomed: bool = False       # 是否已縮放

    # ------------------------------------------------------------------
    # 覆寫父類方法 - 支援縮放範圍（參照 LaptimeChartWidget）
    # ------------------------------------------------------------------
    def get_overall_x_range(self) -> Tuple[float, float]:
        """獲取 X 軸範圍 - 優先使用縮放範圍"""
        if self.is_zoomed and self.zoom_x_range:
            return self.zoom_x_range
        return super().get_overall_x_range()
    
    def get_overall_y_range(self) -> Tuple[float, float]:
        """獲取 Y 軸範圍 - 優先使用縮放範圍"""
        if self.is_zoomed and self.zoom_y_range:
            return self.zoom_y_range
        # 使用左 Y 軸範圍（百分比）
        return super().get_y_range_for_axis("left")
    
    def get_y_range_for_axis(self, y_axis: str = "left") -> Tuple[float, float]:
        """獲取指定 Y 軸範圍 - 優先使用縮放範圍"""
        if y_axis == "left" and self.is_zoomed and self.zoom_y_range:
            return self.zoom_y_range
        return super().get_y_range_for_axis(y_axis)
    
    def draw_x_axis_labels(self, painter, chart_area):
        """覆寫 X 軸標籤繪製 - 顯示 Lap 數字而非分鐘數（參照 LaptimeChartWidget）"""
        if not self.data_series:
            return
        
        x_min, x_max = self.get_overall_x_range()
        if x_max <= x_min:
            return
        
        # 設置字體
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色文字
        
        # 計算合適的 Lap 間隔
        lap_range = x_max - x_min
        if lap_range <= 10:
            interval = 1
        elif lap_range <= 30:
            interval = 5
        elif lap_range <= 60:
            interval = 10
        else:
            interval = 20
        
        # 從第一個整數 Lap 開始
        start_lap = int(x_min)
        if start_lap < x_min:
            start_lap += 1
        
        # 繪製 Lap 標籤
        current_lap = start_lap
        while current_lap <= x_max:
            # 計算螢幕座標
            progress = (current_lap - x_min) / (x_max - x_min)
            screen_x = int(chart_area.left() + chart_area.width() * progress)
            
            # 確保在圖表區域內
            if screen_x >= chart_area.left() and screen_x <= chart_area.right():
                # 繪製刻度線
                painter.drawLine(screen_x, chart_area.bottom(), screen_x, chart_area.bottom() + 5)
                
                # 繪製標籤 "Lap N"
                label = f"Lap {current_lap}"
                painter.drawText(screen_x - 20, chart_area.bottom() + 18, label)
            
            current_lap += interval
    
    def draw_left_y_axis_labels(self, painter, chart_area):
        """覆寫左 Y 軸標籤繪製 - 使用縮放範圍（參照 LaptimeChartWidget）"""
        y_min, y_max = self.get_overall_y_range()
        if y_max <= y_min:
            return
        
        # 設置字體
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 0, 0), 1))  # 黑色文字
        
        # 繪製 5 個主要刻度
        for i in range(6):
            y_value = y_min + (y_max - y_min) * i / 5
            screen_y = int(chart_area.bottom() - chart_area.height() * i / 5)
            
            # 繪製刻度線
            painter.drawLine(chart_area.left() - 5, screen_y, chart_area.left(), screen_y)
            
            # 繪製標籤（百分比）
            label = f"{y_value:.1f}%"
            label_x = max(5, chart_area.left() - 45)
            painter.drawText(label_x, screen_y + 5, label)

    # ------------------------------------------------------------------
    # 顏色輔助方法
    # ------------------------------------------------------------------
    def _get_driver_color(self, driver_code: str) -> QColor:
        """獲取車手顏色（使用 color_palette_provider）"""
        if not driver_code:
            return GRAY_COLOR
        
        code = str(driver_code).strip().upper()
        qcolor = color_palette_provider.get_driver_color(code, format="qcolor")
        if qcolor and isinstance(qcolor, QColor) and qcolor.isValid():
            return qcolor
        return GRAY_COLOR
    
    def _get_driver_team(self, driver_code: str) -> str:
        """獲取車手所屬車隊"""
        if not driver_code:
            return "unknown"
        
        code = str(driver_code).strip().upper()
        # 從 color_palette_provider 獲取車隊信息
        team_info = color_palette_provider.get_driver_team(code)
        if team_info:
            return team_info.lower()
        return "unknown"
    
    def _should_use_dashed_line(self, driver_code: str) -> bool:
        """判斷是否應該使用虛線（同隊第二位車手，按字母順序）"""
        team = self._get_driver_team(driver_code)
        if team == "unknown":
            return False
        
        code_upper = str(driver_code).strip().upper()
        
        # 記錄這個車隊的所有車手
        if team not in self._team_color_usage:
            self._team_color_usage[team] = []
        
        if code_upper not in self._team_color_usage[team]:
            self._team_color_usage[team].append(code_upper)
        
        # 按字母順序排序，第一個用實線，其他用虛線
        sorted_drivers = sorted(self._team_color_usage[team])
        return code_upper != sorted_drivers[0]

    # ------------------------------------------------------------------
    # 公開 API - 多車手版本
    # ------------------------------------------------------------------
    def update_series_multi_driver(
        self,
        all_drivers_data: Dict[str, Sequence[Dict[str, object]]],
        all_tooltip_maps: Dict[str, Dict[int, Dict[str, object]]],
        selected_drivers: List[str],
        *,
        show_ratio: bool = True,
        show_average: bool = False,
        flag_markers: Optional[Dict[int, str]] = None,
    ) -> None:
        """
        更新多車手數據（新版 API）- 只顯示選中的車手
        
        Args:
            all_drivers_data: 所有車手的圈數數據 {driver_code: [lap_records]}
            all_tooltip_maps: 所有車手的 tooltip 數據 {driver_code: {lap: tooltip_data}}
            selected_drivers: 選中的車手列表（只顯示這些車手）
            show_ratio: 是否顯示 Full Throttle %
            show_average: 是否顯示 Average Throttle %
            flag_markers: 旗幟標記
        """
        self._active_settings.update({
            "show_ratio": show_ratio,
            "show_average": show_average,
        })
        
        # 儲存 tooltip 數據
        self._tooltip_maps = dict(all_tooltip_maps or {})
        
        self.clear_data()
        
        # 重置車隊顏色使用追蹤
        self._team_color_usage = {}
        
        # 只繪製選中的車手
        for driver_code in selected_drivers:
            if not driver_code:
                continue
            
            code_upper = driver_code.upper()
            lap_records = all_drivers_data.get(code_upper) or all_drivers_data.get(driver_code)
            if not lap_records:
                continue
            
            # 獲取車手顏色
            driver_color = self._get_driver_color(driver_code)
            
            # 判斷是否使用虛線（同隊第二位車手）
            use_dashed = self._should_use_dashed_line(driver_code)
            line_style = Qt.DashLine if use_dashed else Qt.SolidLine
            
            self._add_driver_series(
                driver_code=driver_code,
                lap_records=lap_records,
                color=driver_color,
                line_style=line_style,
                line_width=2,
                show_ratio=show_ratio,
                show_average=show_average,
            )
        
        self.set_flag_markers(flag_markers)
        self.set_pinned_marker(None, None)
        self.recalculate_data_ranges()
        self.update()
    
    def _add_driver_series(
        self,
        driver_code: str,
        lap_records: Sequence[Dict[str, object]],
        color: QColor,
        line_style: int,
        line_width: int,
        show_ratio: bool,
        show_average: bool,
    ) -> None:
        """為單個車手添加數據系列"""
        lap_numbers: List[int] = []
        ratio_values: List[float] = []
        average_values: List[float] = []
        
        for record in lap_records:
            lap_no = self._safe_int(record.get("lap_number"))
            
            # 優先使用百分比格式，如果沒有則使用小數格式並轉換
            ratio = self._safe_float(record.get("full_throttle_ratio_percent"))
            if ratio is None:
                raw_ratio = self._safe_float(record.get("full_throttle_ratio"))
                if raw_ratio is not None:
                    ratio = raw_ratio * 100.0
            
            avg = self._safe_float(record.get("average_throttle_percent"))
            if avg is None:
                raw_avg = self._safe_float(record.get("average_throttle"))
                if raw_avg is not None:
                    avg = raw_avg * 100.0
            
            if lap_no is None:
                continue
            
            lap_numbers.append(lap_no)
            ratio_values.append(ratio if ratio is not None else float("nan"))
            average_values.append(avg if avg is not None else float("nan"))
        
        if not lap_numbers:
            return
        
        # 轉換 QColor 為 hex 字串
        color_hex = color.name() if isinstance(color, QColor) else str(color)
        
        # Full Throttle %
        if show_ratio:
            cleaned_ratio = self._replace_nan_with_previous(ratio_values)
            if cleaned_ratio:
                self.add_data_series(
                    ChartDataSeries(
                        name=f"{driver_code} Full Throttle %",
                        x_data=lap_numbers,
                        y_data=cleaned_ratio,
                        color=color_hex,
                        line_width=line_width,
                        y_axis="left",
                        line_style=line_style,
                    )
                )
        
        # Average Throttle %（使用虛線）
        if show_average:
            cleaned_average = self._replace_nan_with_previous(average_values)
            if cleaned_average:
                self.add_data_series(
                    ChartDataSeries(
                        name=f"{driver_code} Average %",
                        x_data=lap_numbers,
                        y_data=cleaned_average,
                        color=color_hex,
                        line_width=max(1, line_width - 1),
                        y_axis="left",
                        line_style=Qt.DotLine,  # 平均值用點線
                    )
                )

    # ------------------------------------------------------------------
    # 舊版 API（向下相容）
    # ------------------------------------------------------------------
    def update_series(
        self,
        lap_records: Sequence[Dict[str, object]],
        tooltip_map: Dict[int, Dict[str, object]],
        *,
        show_full_duration: bool = False,
        show_ratio: bool = True,
        show_average: bool = False,
        highlight_threshold: bool = False,
        threshold_percent: Optional[float] = None,
        pit_laps: Optional[Iterable[int]] = None,
        caution_laps: Optional[Iterable[int]] = None,
        flag_markers: Optional[Dict[int, str]] = None,
        lap_records_driver2: Optional[Sequence[Dict[str, object]]] = None,
        tooltip_map_driver2: Optional[Dict[int, Dict[str, object]]] = None,
        driver1_code: str = "D1",
        driver2_code: str = "D2",
    ) -> None:
        """舊版 API（保留向下相容性）"""
        # 轉換為新格式
        all_drivers_data = {driver1_code: lap_records}
        all_tooltip_maps = {driver1_code: tooltip_map or {}}
        selected_drivers = [driver1_code]
        
        if lap_records_driver2:
            all_drivers_data[driver2_code] = lap_records_driver2
            all_tooltip_maps[driver2_code] = tooltip_map_driver2 or {}
            selected_drivers.append(driver2_code)
        
        # 呼叫新版 API
        self.update_series_multi_driver(
            all_drivers_data=all_drivers_data,
            all_tooltip_maps=all_tooltip_maps,
            selected_drivers=selected_drivers,
            show_ratio=show_ratio,
            show_average=show_average,
            flag_markers=flag_markers,
        )

    def get_tooltip_payload(self, lap_number: int, series_name: str = "") -> Dict[str, object]:
        """
        獲取指定圈數的 tooltip 數據
        
        Args:
            lap_number: 圈數
            series_name: 系列名稱（用於判斷車手）
        
        Returns:
            Tooltip 數據字典
        """
        # 從系列名稱提取車手代碼
        driver_code = None
        if series_name:
            # 系列名稱格式: "VER Full Throttle %" 或 "VER Average %"
            parts = series_name.split()
            if parts:
                driver_code = parts[0].upper()
        
        # 優先使用多車手模式的 tooltip 數據
        if self._tooltip_maps and driver_code:
            driver_tooltip = self._tooltip_maps.get(driver_code, {})
            if driver_tooltip:
                return dict(driver_tooltip.get(int(lap_number), {}))
        
        # 向下相容：使用舊的單一 tooltip map
        if hasattr(self, '_tooltip_map') and self._tooltip_map:
            return dict(self._tooltip_map.get(int(lap_number), {}))
        
        return {}
    
    def format_tooltip_for_data_point(self, lap_number: int, series_name: str = "") -> List[str]:
        """
        為數據點互動系統格式化 tooltip 文字
        只顯示：Lap, Ave Throttle %, Full throttle %, Lap time, DRS %, Tyre
        
        Args:
            lap_number: 圈數
            series_name: 系列名稱（用於雙車手模式判斷）
        """
        payload = self.get_tooltip_payload(lap_number, series_name)
        if not payload:
            return []
        
        lines = []
        
        # Lap
        lines.append(f"Lap {lap_number}")
        
        # Full Throttle % (Full throttle %)
        ratio = payload.get("full_throttle_ratio_percent")
        if ratio is not None:
            try:
                lines.append(f"Full Throttle %: {float(ratio):.1f}%")
            except (TypeError, ValueError):
                pass
        
        # Average Throttle % (Ave Throttle %)
        avg = payload.get("average_throttle_percent")
        if avg is not None:
            try:
                lines.append(f"Ave Throttle %: {float(avg):.1f}%")
            except (TypeError, ValueError):
                pass
        
        # Lap Time
        lap_time_fmt = payload.get("lap_time_formatted") or payload.get("lap_time")
        if lap_time_fmt:
            lines.append(f"Lap Time: {lap_time_fmt}")
        elif payload.get("lap_time_seconds") is not None:
            try:
                lines.append(f"Lap Time: {float(payload['lap_time_seconds']):.3f}s")
            except (TypeError, ValueError):
                pass
        
        # DRS %
        drs = payload.get("drs_percent")
        if drs is not None:
            try:
                lines.append(f"DRS %: {float(drs):.1f}%")
            except (TypeError, ValueError):
                pass
        
        # Tyre
        compound = payload.get("compound", "N/A")
        lines.append(f"Tyre: {compound}")
        
        return lines

    # ------------------------------------------------------------------
    # 輔助工具
    # ------------------------------------------------------------------
    @staticmethod
    def _replace_nan_with_previous(series: Sequence[Optional[float]]) -> List[float]:
        cleaned: List[float] = []
        last_value: Optional[float] = None
        for value in series:
            if value is None or (isinstance(value, float) and value != value):  # NaN 檢查
                fallback = last_value if last_value is not None else 0.0
                cleaned.append(fallback)
            else:
                numeric = float(value)
                cleaned.append(numeric)
                last_value = numeric
        return cleaned

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_nan(value) -> bool:
        return isinstance(value, float) and value != value

    # ------------------------------------------------------------------
    # 覆寫繪圖：固定標籤
    # ------------------------------------------------------------------
    def _draw_pinned_annotation(self, painter, chart_area) -> None:
        """❌ 已禁用舊的 pinned_marker 系統，使用通用的 pinned_data_points 替代"""
        # 不再繪製淺藍色的 "Lap XX full throttle(s)" 提示
        # 新系統使用 universal_chart_widget.py 中的 draw_hover_and_pinned_data_points()
        pass

    def _build_pinned_lines(self, lap: int, payload: Dict[str, object]) -> List[str]:
        """[已禁用] 舊系統不再使用"""
        return []

    # ------------------------------------------------------------------
    # 右鍵框選縮放功能和滾輪縮放（複製自 LaptimeChartWidget）
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        """覆寫 paintEvent 以繪製縮放選擇框"""
        # 先調用父類的 paintEvent
        super().paintEvent(event)
        
        # 繪製縮放選擇框（右鍵拖動時）
        if self.is_zooming and self.zoom_rect_start and self.zoom_rect_end:
            painter = QPainter(self)
            zoom_rect = QRect(self.zoom_rect_start, self.zoom_rect_end).normalized()
            # 半透明藍色填充
            painter.setBrush(QBrush(QColor(100, 150, 255, 50)))
            painter.setPen(QPen(QColor(50, 100, 200), 2, Qt.DashLine))
            painter.drawRect(zoom_rect)
            painter.end()
    
    def wheelEvent(self, event):
        """滾輪縮放 - 以滑鼠位置為中心進行縮放"""
        chart_area = self.get_chart_area()
        if not chart_area.contains(event.pos()):
            super().wheelEvent(event)
            return
        
        # 獲取滾動方向
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        
        # 縮放因子
        zoom_factor = 1.15 if delta > 0 else 0.87  # 放大或縮小
        
        # 獲取當前數據範圍
        current_x_min, current_x_max = self.get_overall_x_range()
        current_y_min, current_y_max = self.get_overall_y_range()
        
        if current_x_max <= current_x_min or current_y_max <= current_y_min:
            return
        
        # 計算滑鼠位置對應的數據座標（作為縮放中心）
        mouse_x = event.pos().x()
        mouse_y = event.pos().y()
        
        # 轉換為數據座標
        data_x = current_x_min + (mouse_x - chart_area.left()) * (current_x_max - current_x_min) / chart_area.width()
        data_y = current_y_max - (mouse_y - chart_area.top()) * (current_y_max - current_y_min) / chart_area.height()
        
        # 計算新的範圍（以滑鼠位置為中心縮放）
        new_x_range = (current_x_max - current_x_min) / zoom_factor
        new_y_range = (current_y_max - current_y_min) / zoom_factor
        
        # 保持滑鼠位置在相同的數據點上
        x_ratio = (data_x - current_x_min) / (current_x_max - current_x_min)
        y_ratio = (data_y - current_y_min) / (current_y_max - current_y_min)
        
        new_x_min = data_x - x_ratio * new_x_range
        new_x_max = data_x + (1 - x_ratio) * new_x_range
        new_y_min = data_y - y_ratio * new_y_range
        new_y_max = data_y + (1 - y_ratio) * new_y_range
        
        # 確保範圍有效
        if new_x_min >= new_x_max or new_y_min >= new_y_max:
            return
        
        # 應用縮放
        self.zoom_x_range = (new_x_min, new_x_max)
        self.zoom_y_range = (new_y_min, new_y_max)
        self.is_zoomed = True
        
        print(f"[DEBUG] 滾輪縮放: X=({new_x_min:.1f}, {new_x_max:.1f}), Y=({new_y_min:.1f}, {new_y_max:.1f})")
        
        # 發射信號通知父組件
        self.zoom_changed.emit(True)
        
        # 重繪圖表
        self.update()
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """雙擊圖表區域重置縮放"""
        if event.button() == Qt.LeftButton:
            chart_area = self.get_chart_area()
            if chart_area.contains(event.pos()) and self.is_zoomed:
                self.reset_zoom()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 右鍵開始縮放框選"""
        if event.button() == Qt.RightButton:
            chart_area = self.get_chart_area()
            if chart_area.contains(event.pos()):
                # 右鍵開始縮放框選
                self.is_zooming = True
                self.zoom_rect_start = event.pos()
                self.zoom_rect_end = event.pos()
                self.setCursor(Qt.CrossCursor)
                print(f"[ZOOM] 開始框選: {event.pos()}")
                event.accept()
                return
        
        # 其他情況交給父類處理
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 處理縮放框選"""
        # 處理縮放框選
        if self.is_zooming:
            self.zoom_rect_end = event.pos()
            self.update()  # 重繪以顯示選擇框
            event.accept()
            return
        
        # 其他情況交給父類處理
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 完成縮放框選"""
        # 處理縮放框選完成
        if event.button() == Qt.RightButton and self.is_zooming:
            self.is_zooming = False
            self.setCursor(Qt.ArrowCursor)
            
            # 計算選擇框的範圍並應用縮放
            if self.zoom_rect_start and self.zoom_rect_end:
                print(f"[ZOOM] 框選完成: {self.zoom_rect_start} -> {self.zoom_rect_end}")
                self._apply_zoom_from_rect()
            
            self.zoom_rect_start = None
            self.zoom_rect_end = None
            event.accept()
            return
        
        # 其他情況交給父類處理
        super().mouseReleaseEvent(event)
    
    def _apply_zoom_from_rect(self):
        """根據選擇框應用縮放（參照 LaptimeChartWidget）"""
        if not self.zoom_rect_start or not self.zoom_rect_end:
            return
        
        # 計算選擇框的歸一化矩形
        rect = QRect(self.zoom_rect_start, self.zoom_rect_end).normalized()
        
        # 確保選擇框有最小尺寸（避免誤觸）
        if rect.width() < 20 or rect.height() < 20:
            print("[ZOOM] 選擇框太小，忽略縮放")
            return
        
        # 獲取圖表區域
        chart_area = self.get_chart_area()
        if not chart_area.isValid():
            return
        
        # 獲取原始數據範圍（不使用縮放範圍）
        if self.is_zoomed and self.zoom_x_range and self.zoom_y_range:
            # 已縮放，使用當前縮放範圍作為基礎
            current_x_min, current_x_max = self.zoom_x_range
            current_y_min, current_y_max = self.zoom_y_range
        else:
            # 未縮放，從父類獲取原始範圍
            current_x_min, current_x_max = super().get_overall_x_range()
            current_y_min, current_y_max = self.get_y_range_for_axis("left")
        
        print(f"[ZOOM] 當前範圍: X=({current_x_min:.1f}, {current_x_max:.1f}), Y=({current_y_min:.1f}, {current_y_max:.1f})")
        
        if current_x_max <= current_x_min or current_y_max <= current_y_min:
            return
        
        # 螢幕座標轉數據座標
        chart_left = chart_area.left()
        chart_right = chart_area.right()
        chart_top = chart_area.top()
        chart_bottom = chart_area.bottom()
        
        # X 座標轉換
        new_x_min = current_x_min + (rect.left() - chart_left) * (current_x_max - current_x_min) / (chart_right - chart_left)
        new_x_max = current_x_min + (rect.right() - chart_left) * (current_x_max - current_x_min) / (chart_right - chart_left)
        
        # Y 座標轉換（注意 Y 軸方向相反）
        new_y_max = current_y_max - (rect.top() - chart_top) * (current_y_max - current_y_min) / (chart_bottom - chart_top)
        new_y_min = current_y_max - (rect.bottom() - chart_top) * (current_y_max - current_y_min) / (chart_bottom - chart_top)
        
        print(f"[ZOOM] 新範圍: X=({new_x_min:.1f}, {new_x_max:.1f}), Y=({new_y_min:.1f}, {new_y_max:.1f})")
        
        # 確保範圍有效
        if new_x_min >= new_x_max or new_y_min >= new_y_max:
            print("[ZOOM] 無效的縮放範圍")
            return
        
        # 應用縮放
        self.zoom_x_range = (new_x_min, new_x_max)
        self.zoom_y_range = (new_y_min, new_y_max)
        self.is_zoomed = True
        
        print(f"[ZOOM] 縮放已應用: X=({new_x_min:.1f}, {new_x_max:.1f}), Y=({new_y_min:.1f}, {new_y_max:.1f})")
        
        # 發射信號通知父組件
        self.zoom_changed.emit(True)
        
        # 重繪圖表
        self.update()
    
    def reset_zoom(self):
        """重置縮放，顯示全部數據"""
        if not self.is_zoomed:
            return
        
        self.zoom_x_range = None
        self.zoom_y_range = None
        self.is_zoomed = False
        
        # 重置視圖縮放
        self.x_scale = 1.0
        self.x_offset = 0.0
        self.y_scale = 1.0
        self.y_offset = 0.0
        
        logger.debug("[ZOOM] 重置縮放，顯示全部數據")
        
        # 發射信號通知父組件
        self.zoom_changed.emit(False)
        
        # 重新計算數據範圍
        self.recalculate_data_ranges()
        
        # 重繪圖表
        self.update()


__all__ = ["ThrottleDurationChartWidget"]
