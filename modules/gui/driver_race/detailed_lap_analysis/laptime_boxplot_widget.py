#!/usr/bin/env python3
"""
LapTimeBoxPlotWidget - F1T 圈速箱型圖視覺化模組
================================================

基於 detailed_laptime_analysis JSON 數據，使用箱型圖 (Box Plot) 視覺化
所有車手的圈速分佈情況。

功能特性：
- 讀取 detailed_laptime_analysis_*.json 數據
- 按車手分組顯示圈速分佈
- 自動過濾異常值（進站圈、安全車圈）
- 顯示中位數、四分位數、異常值
- 車隊配色支援
- 互動式圖表（縮放、平移、保存）

數據來源：
- JSON 檔案：detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json
- 搜尋目錄：json/, json_exports/, cache/ (與 Rain Analysis 一致)
- CLI 功能：Function 28 (Detailed Lap Time Analysis)

架構說明：
- 當前版本：簡化架構，直接繼承 QWidget
- 未來版本：可重構為完全通用架構（UniversalAnalysisMDI）
- 搜尋路徑：與 Rain Analysis 保持一致

作者: F1T Team
日期: 2025-10-02
版本: 1.0.1 (修正搜尋目錄)
"""

import os
import sys
import json
import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QMessageBox, QToolTip
)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPolygonF

# 導入基類和工具
try:
    from ...base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig, CliAnalysisWorker
except ImportError:
    # 獨立運行時添加路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig, CliAnalysisWorker

# 導入 i18n
try:
    from core.gui_i18n import tr, set_gui_language
    I18N_AVAILABLE = True
except ImportError:
    def tr(key, fallback=None):
        return fallback if fallback else key
    I18N_AVAILABLE = False

from core.gui_settings_manager import gui_settings_manager


class BoxPlotCanvas(QWidget):
    """使用 QPainter 自行繪製箱型圖的畫布"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(200, 100)  # 統一最小尺寸標準（與其他圖表組件一致）
        self.setMouseTracking(True)

        self._box_items: List[Dict[str, Any]] = []
        self._value_range: Tuple[float, float] = (0.0, 1.0)
        self._hover_index: Optional[int] = None
        self._hover_regions: List[Tuple[QRectF, Dict[str, Any]]] = []

        self._background_color = QColor("#ffffff")  # 白色背景
        self._axis_color = QColor("#555555")
        self._grid_color = QColor("#e0e0e0")
        self._label_font = QFont("Microsoft JhengHei", 9)

    # ------------------------------------------------------------------
    # 資料設定
    # ------------------------------------------------------------------
    def set_box_data(self, box_items: List[Dict[str, Any]], value_range: Tuple[float, float]) -> None:
        processed: List[Dict[str, Any]] = []

        for item in box_items:
            color = item.get("color")
            if isinstance(color, str):
                color = QColor(color)
            elif not isinstance(color, QColor):
                color = QColor("#cccccc")

            processed.append({
                "driver": item.get("driver", ""),
                "stats": item.get("stats", {}),
                "color": color,
                "count": item.get("count", item.get("stats", {}).get("count", 0)),
                "hover_rect": QRectF(),
                "center": 0.0,
            })

        vmin, vmax = value_range
        if math.isclose(vmin, vmax):
            vmax = vmin + 1.0

        self._box_items = processed
        self._value_range = (float(vmin), float(vmax))
        self._hover_index = None
        self._hover_regions = []
        self.update()

    # ------------------------------------------------------------------
    # 繪圖主流程
    # ------------------------------------------------------------------
    def paintEvent(self, event):  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._background_color)
        painter.setFont(self._label_font)

        if not self._box_items:
            painter.setPen(self._axis_color)
            painter.drawText(self.rect(), Qt.AlignCenter, "No data available")
            return

        vmin, vmax = self._value_range
        ticks = self._generate_ticks(vmin, vmax)

        metrics = painter.fontMetrics()
        tick_label_width = max(
            (metrics.horizontalAdvance(f"{value:.2f}") for value in ticks),
            default=metrics.horizontalAdvance("0.00"),
        )

        longest_driver = max(
            (item.get("driver", "") for item in self._box_items),
            key=len,
            default="Driver",
        )
        driver_text_width = max(metrics.horizontalAdvance(longest_driver), metrics.horizontalAdvance("VER"))
        driver_label_block = metrics.height() * 2 + int(driver_text_width * 0.6)

        margins = {
            "left": max(82, tick_label_width + 42),
            "right": 48,
            "top": 36,
            "bottom": max(110, driver_label_block + 42),
        }

        chart_rect = QRectF(
            self.rect().left() + margins["left"],
            self.rect().top() + margins["top"],
            max(1.0, self.rect().width() - margins["left"] - margins["right"]),
            max(1.0, self.rect().height() - margins["top"] - margins["bottom"]),
        )

        self._hover_regions = []

        self._draw_grid(painter, chart_rect, ticks)
        self._draw_boxes(painter, chart_rect)
        self._draw_axes(painter, chart_rect, margins)
        self._draw_driver_labels(painter, chart_rect)

    # ------------------------------------------------------------------
    # 協助函式：繪製各元素
    # ------------------------------------------------------------------
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF, ticks: List[float]) -> None:
        metrics = painter.fontMetrics()

        for value in ticks:
            y = self._value_to_y(value, chart_rect)
            grid_pen = QPen(self._grid_color)
            grid_pen.setStyle(Qt.DashLine)
            painter.setPen(grid_pen)
            self._draw_line(painter, chart_rect.left(), y, chart_rect.right(), y)

            label_pen = QPen(self._axis_color)
            painter.setPen(label_pen)
            label = f"{value:.2f}"
            text_width = metrics.horizontalAdvance(label)
            painter.drawText(
                QPointF(
                    chart_rect.left() - 12 - text_width,
                    y + metrics.ascent() / 2 - 2,
                ),
                label,
            )

    def _draw_boxes(self, painter: QPainter, chart_rect: QRectF) -> None:
        count = len(self._box_items)
        if count == 0:
            return

        spacing = chart_rect.width() / max(count, 1)
        box_width = min(46.0, spacing * 0.6)
        whisker_width = box_width * 0.7

        vmin, vmax = self._value_range

        for index, item in enumerate(self._box_items):
            stats = item.get("stats", {})
            if not stats:
                continue

            center_x = chart_rect.left() + spacing * (index + 0.5)
            item["center"] = center_x

            q1 = stats.get("q1", vmin)
            q3 = stats.get("q3", vmax)
            median = stats.get("median", (q1 + q3) / 2.0)
            dmin = stats.get("min", q1)
            dmax = stats.get("max", q3)
            mean = stats.get("mean", median)

            q1_y = self._value_to_y(q1, chart_rect)
            q3_y = self._value_to_y(q3, chart_rect)
            median_y = self._value_to_y(median, chart_rect)
            min_y = self._value_to_y(dmin, chart_rect)
            max_y = self._value_to_y(dmax, chart_rect)
            mean_y = self._value_to_y(mean, chart_rect)

            box_rect = QRectF(
                center_x - box_width / 2,
                q3_y,
                box_width,
                max(4.0, q1_y - q3_y),
            )

            fill_color = QColor(item["color"])
            fill_color.setAlpha(190)

            if index == self._hover_index:
                pen = QPen(QColor("#222222"), 2)
                fill_color.setAlpha(230)
            else:
                pen = QPen(QColor("#444444"), 1)

            painter.setPen(pen)
            painter.setBrush(QBrush(fill_color))
            painter.drawRect(box_rect)

            # 中位數
            painter.setPen(QPen(QColor("#d62728"), 2))
            self._draw_line(
                painter,
                center_x - box_width / 2,
                median_y,
                center_x + box_width / 2,
                median_y,
            )

            # 上下鬚
            painter.setPen(QPen(QColor("#333333"), 1))
            self._draw_line(painter, center_x, q3_y, center_x, max_y)
            self._draw_line(painter, center_x, q1_y, center_x, min_y)
            self._draw_line(
                painter,
                center_x - whisker_width / 2,
                max_y,
                center_x + whisker_width / 2,
                max_y,
            )
            self._draw_line(
                painter,
                center_x - whisker_width / 2,
                min_y,
                center_x + whisker_width / 2,
                min_y,
            )

            # 平均值菱形
            mean_size = max(6.0, box_width * 0.35)
            diamond = QPolygonF([
                QPointF(center_x, mean_y - mean_size / 2),
                QPointF(center_x + mean_size / 2, mean_y),
                QPointF(center_x, mean_y + mean_size / 2),
                QPointF(center_x - mean_size / 2, mean_y),
            ])
            painter.setBrush(QBrush(QColor(0, 128, 0)))
            painter.setPen(QPen(QColor(0, 90, 0)))
            painter.drawPolygon(diamond)

            whisker_rect = QRectF(
                center_x - whisker_width / 2,
                min(min_y, max_y),
                whisker_width,
                abs(max_y - min_y),
            )
            hover_rect = box_rect.united(whisker_rect).adjusted(-4, -4, 4, 12)
            self._hover_regions.append((hover_rect, item))

    def _draw_axes(self, painter: QPainter, chart_rect: QRectF, margins: Dict[str, float]) -> None:
        painter.setPen(QPen(self._axis_color, 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.bottomRight())
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.topLeft())

        # 繪製 Y 軸標題（旋轉 90 度）
        # 調整位置以避免與刻度標籤重疊
        painter.save()
        margin_left = margins.get("left", 80.0)
        # 將標題放置在左邊距的 1/4 位置（更靠左），避免與刻度數字重疊
        left_space_center = self.rect().left() + (margin_left / 4.0) + 5.0
        painter.translate(left_space_center, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(
                -chart_rect.height() / 2,
                -15,
                chart_rect.height(),
                30,
            ),
            Qt.AlignCenter,
            "Lap Time (seconds)",
        )
        painter.restore()

        painter.drawText(
            QRectF(
                chart_rect.left(),
                chart_rect.bottom() + max(32.0, (margins["bottom"] - 70.0)),
                chart_rect.width(),
                30,
            ),
            Qt.AlignCenter,
            "Driver",
        )

    def _draw_driver_labels(self, painter: QPainter, chart_rect: QRectF) -> None:
        metrics = painter.fontMetrics()
        for index, item in enumerate(self._box_items):
            center_x = item.get("center", chart_rect.left())
            label = item.get("driver", "")

            painter.save()
            # 將車手標籤往下移動（從 +12 改為 +25），避免與 X 軸線重疊
            painter.translate(center_x, chart_rect.bottom() + 25)
            painter.rotate(-45)
            painter.setPen(self._axis_color)
            painter.drawText(QPointF(0, metrics.ascent()), label)
            painter.restore()

    # ------------------------------------------------------------------
    # 滑鼠互動
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):  # type: ignore[override]
        hovered = None
        point = event.pos()
        for index, (rect, item) in enumerate(self._hover_regions):
            if rect.contains(point):
                hovered = index
                break

        if hovered != self._hover_index:
            self._hover_index = hovered
            if hovered is not None:
                stats = self._box_items[hovered]["stats"]
                tooltip = self._format_tooltip(self._box_items[hovered]["driver"], stats)
                QToolTip.showText(event.globalPos(), tooltip, self)
            else:
                QToolTip.hideText()
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):  # type: ignore[override]
        self._hover_index = None
        QToolTip.hideText()
        self.update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def _value_to_y(self, value: float, chart_rect: QRectF) -> float:
        vmin, vmax = self._value_range
        if math.isclose(vmax, vmin):
            return chart_rect.bottom()
        ratio = (value - vmin) / (vmax - vmin)
        return chart_rect.bottom() - ratio * chart_rect.height()

    def _generate_ticks(self, vmin: float, vmax: float, target: int = 6) -> List[float]:
        if math.isclose(vmin, vmax):
            return [vmin]

        raw_step = (vmax - vmin) / max(target - 1, 1)
        magnitude = 10 ** math.floor(math.log10(raw_step))
        residual = raw_step / magnitude

        if residual <= 1:
            step = 1 * magnitude
        elif residual <= 2:
            step = 2 * magnitude
        elif residual <= 5:
            step = 5 * magnitude
        else:
            step = 10 * magnitude

        tick_start = math.floor(vmin / step) * step
        ticks = []
        value = tick_start
        while value <= vmax + step:
            ticks.append(round(value, 4))
            value += step

        filtered = [tick for tick in ticks if tick >= vmin - step * 0.5]
        if not filtered:
            filtered = ticks
        return filtered[: max(len(filtered), 1)]

    def _format_tooltip(self, driver: str, stats: Dict[str, Any]) -> str:
        return "\n".join([
            driver,
            f"Min: {stats.get('min', 0):.3f}s",
            f"Q1: {stats.get('q1', 0):.3f}s",
            f"Median: {stats.get('median', 0):.3f}s",
            f"Q3: {stats.get('q3', 0):.3f}s",
            f"Max: {stats.get('max', 0):.3f}s",
            f"Mean: {stats.get('mean', 0):.3f}s",
            f"Samples: {int(stats.get('count', 0))}",
        ])

    def _draw_line(self, painter: QPainter, x1: float, y1: float, x2: float, y2: float) -> None:
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class LapTimeBoxPlotWidget(QWidget):
    """
    圈速箱型圖視覺化 Widget
    
    架構說明：
    - 採用簡化架構，直接繼承 QWidget
    - 不使用 UniversalDataLoader 繼承（避免複雜性）
    - 搜尋目錄與 Rain Analysis 保持一致: json/, json_exports/, cache/
    - 支援 CLI 生成數據（Function 28）
    
    數據流：
    1. 搜尋 JSON 檔案（優先本地）
    2. 找不到時調用 CLI 生成
    3. 載入並驗證數據
    4. 過濾處理（進站圈、異常值）
    5. 繪製箱型圖
    
    未來可重構為完全通用架構（像 Rain Analysis 一樣使用 UniversalAnalysisMDI）
    """
    
    # 信號定義
    data_loaded = pyqtSignal(bool, str)  # 數據載入完成信號 (成功, 訊息)
    analysis_updated = pyqtSignal()      # 分析更新信號
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        """
        初始化圈速箱型圖 Widget
        
        Args:
            parent: 父 Widget
            year: 賽季年份
            race: 賽事名稱
            session: 賽事階段 (R/Q/FP1/FP2/FP3)
        """
        super().__init__(parent)
        
        # 賽事參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 數據存儲
        self.raw_data = None
        self.processed_data = None
        self.driver_laptimes = {}  # {driver: [lap_times]}
        
        # 過濾設定
        self.filter_pit_laps = True
        self.filter_outliers = True
        self.outlier_threshold = 1.5  # IQR 倍數
        
        # UI 組件
        self.chart_widget = None  # type: Optional[BoxPlotCanvas]

        # 全域設定管理
        self.settings_manager = gui_settings_manager
        self.settings_manager.boxplot_settings_changed.connect(self._on_global_settings_changed)
        
        # 初始化 UI
        self.init_ui()

        # 套用全域設定
        self._apply_boxplot_settings(self.settings_manager.get_boxplot_settings())
        
        # 如果提供了參數，自動載入數據
        if year and race and session:
            self.load_data(year=year, race=race, session=session)
        
        print(f"[BOXPLOT] LapTimeBoxPlotWidget 已初始化: {year} {race} {session}")
    
    def _debug(self, message: str):
        """除錯輸出"""
        print(f"[BOXPLOT] {message}")
    
    def init_ui(self):
        """初始化使用者介面 - 優化版（移除空白區域）"""
        layout = QVBoxLayout(self)
        # 移除所有邊距和間距，讓圖表完全填滿空間（與 Rain Analysis 一致）
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 直接創建並添加圖表（移除中間容器層）
        self.chart_widget = BoxPlotCanvas(self)
        from PyQt5.QtWidgets import QSizePolicy
        self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chart_widget)

        self.boxplot_stats = {}

        # 隱藏的狀態標籤（為了代碼兼容性保留，但不顯示）
        self.status_label = None

        self._debug("UI 初始化完成（優化版 - 無空白區域）")
    
    # ===== 數據載入和處理 =====
    
    def load_data(self, year=None, race=None, session=None):
        """載入數據"""
        year = year or self.current_year
        race = race or self.current_race
        session = session or self.current_session
        
        self._debug(f"載入數據: {year} {race} {session}")
        if self.status_label:
            self.status_label.setText(f"⏳ Loading data...")
        
        # 更新參數
        self.current_year = str(year)
        self.current_race = race
        self.current_session = session
        
        # 搜尋 JSON 檔案
        json_file = self._search_json_file(year, race, session)
        
        if json_file:
            self._debug(f"✅ 找到 JSON 檔案: {json_file}")
            self._load_from_json(json_file)
        else:
            self._debug("❌ 找不到 JSON 檔案，需要生成")
            self._generate_via_cli(year, race, session)
    
    def _search_json_file(self, year, race, session) -> Optional[str]:
        """搜尋 JSON 檔案 - 與 Rain Analysis 保持一致的搜尋目錄"""
        filename = f"detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json"
        
        # 與 Rain Analysis 一致的搜尋目錄
        search_directories = ["json", "json_exports", "cache"]
        
        self._debug(f"搜尋檔案: {filename}")
        self._debug(f"搜尋目錄: {search_directories}")
        
        for base_path in search_directories:
            full_path = os.path.join(base_path, filename)
            self._debug(f"  檢查: {full_path}")
            if os.path.exists(full_path):
                self._debug(f"  ✅ 找到: {full_path}")
                return full_path
        
        self._debug(f"❌ 找不到檔案")
        return None
    
    def _load_from_json(self, filepath: str):
        """從 JSON 檔案載入數據"""
        try:
            self._debug(f"讀取 JSON: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            
            if not self.raw_data.get('success'):
                self._debug("❌ JSON 標記為不成功")
                if self.status_label:
                    self.status_label.setText("❌ Data loading failed")
                return
            
            # 處理數據
            self.processed_data = self._transform_data_for_display(self.raw_data)
            
            # 更新顯示
            self._update_display(self.processed_data)
            
        except Exception as e:
            self._debug(f"❌ 載入 JSON 失敗: {e}")
            import traceback
            traceback.print_exc()
            if self.status_label:
                self.status_label.setText(f"❌ Failed to load JSON: {e}")
    
    def _generate_via_cli(self, year, race, session):
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用,系統只允許通過 API 獲取數據
        """
        self._debug(f"⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug(f"💡 提示: 請使用 API 獲取數據")
        if self.status_label:
            self.status_label.setText(f"⚠️ CLI 調用已禁用 - 請使用 API")
        return False
    
    def _transform_data_for_display(self, raw_data: Any) -> Any:
        """轉換數據為顯示格式"""
        self._debug("開始轉換數據...")
        
        try:
            all_drivers_data = raw_data.get('all_drivers_detailed_laptime', {})
            
            driver_laptimes = {}
            
            for driver, driver_data in all_drivers_data.items():
                if not driver_data.get('success'):
                    continue
                
                detailed_laps = driver_data.get('detailed_lap_data', [])
                lap_times = []
                
                for lap in detailed_laps:
                    lap_time_seconds = lap.get('lap_time_seconds')
                    
                    # 跳過無效圈速
                    if lap_time_seconds is None or lap_time_seconds <= 0:
                        continue
                    
                    # 過濾進站圈
                    if self.filter_pit_laps:
                        smart_markers = lap.get('smart_markers', {})
                        pit_detection = smart_markers.get('pit_stop_detection', {})
                        if pit_detection.get('is_pit_lap', False):
                            continue
                    
                    lap_times.append(lap_time_seconds)
                
                if lap_times:
                    # 過濾異常值
                    if self.filter_outliers:
                        lap_times = self._filter_outliers(lap_times)
                    
                    driver_laptimes[driver] = lap_times
            
            self._debug(f"✅ 成功轉換 {len(driver_laptimes)} 個車手的數據")
            return driver_laptimes
            
        except Exception as e:
            self._debug(f"❌ 數據轉換失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _filter_outliers(self, data: List[float]) -> List[float]:
        """使用 IQR 方法過濾異常值"""
        if len(data) < 4:
            return data
        
        data_array = np.array(data)
        q1 = np.percentile(data_array, 25)
        q3 = np.percentile(data_array, 75)
        iqr = q3 - q1
        
        threshold = self.outlier_threshold
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        filtered = data_array[(data_array >= lower_bound) & (data_array <= upper_bound)]
        
        removed = len(data) - len(filtered)
        if removed > 0:
            self._debug(f"過濾了 {removed} 個異常值")
        
        return filtered.tolist()
    
    def _update_display(self, processed_data: Any):
        """更新顯示"""
        self._debug("更新顯示...")
        
        if not processed_data or not isinstance(processed_data, dict):
            self._debug("❌ 無有效數據可顯示")
            if self.status_label:
                self.status_label.setText("❌ No valid data to display")
            return
        
        self.driver_laptimes = processed_data
        self.plot_boxplot()
        
        total_drivers = len(processed_data)
        total_laps = sum(len(laps) for laps in processed_data.values())

        # status_label 已隱藏（None），無需更新
        
        self._debug(f"✅ 顯示更新完成: {total_drivers} 車手, {total_laps} 圈")
    
    # ===== 圖表繪製 =====
    
    def plot_boxplot(self):
        """繪製箱型圖"""
        if not self.driver_laptimes:
            self._debug("❌ 無數據可繪製")
            if self.chart_widget:
                self.chart_widget.set_box_data([], (0.0, 1.0))
            return
        
        self._debug(f"繪製箱型圖: {len(self.driver_laptimes)} 個車手")
        
        drivers = sorted(self.driver_laptimes.keys())
        colors = self._get_team_colors(drivers)

        self.boxplot_stats.clear()
        box_items = []
        y_min = float("inf")
        y_max = float("-inf")

        for driver, color in zip(drivers, colors):
            laps = self.driver_laptimes.get(driver, [])
            stats = self._calculate_box_stats(laps)
            if not stats:
                continue

            self.boxplot_stats[driver] = stats
            y_min = min(y_min, stats['min'])
            y_max = max(y_max, stats['max'])

            box_items.append({
                'driver': driver,
                'stats': stats,
                'color': color,
            })

        if not box_items:
            self._debug("❌ 無有效統計數據")
            if self.chart_widget:
                self.chart_widget.set_box_data([], (0.0, 1.0))
            return

        if math.isclose(y_min, y_max):
            y_max = y_min + 1.0

        if self.chart_widget:
            self.chart_widget.set_box_data(box_items, (y_min, y_max))

        self._debug("✅ 箱型圖繪製完成")

    def _calculate_box_stats(self, laps: List[float]) -> Optional[Dict[str, float]]:
        """計算箱型圖統計值"""
        if not laps:
            return None

        arr = np.array(laps, dtype=float)
        stats = {
            'min': float(np.min(arr)),
            'q1': float(np.percentile(arr, 25)),
            'median': float(np.median(arr)),
            'q3': float(np.percentile(arr, 75)),
            'max': float(np.max(arr)),
            'mean': float(np.mean(arr)),
            'count': arr.size
        }
        return stats

    def _apply_boxplot_settings(self, settings: Dict[str, Any]) -> None:
        """套用全域箱型圖設定"""
        self.filter_pit_laps = settings.get('filter_pit_laps', True)
        self.filter_outliers = settings.get('filter_outliers', True)
        self.outlier_threshold = settings.get('outlier_threshold', 1.5)
        self._update_settings_summary()

    def _on_global_settings_changed(self, settings: Dict[str, Any]) -> None:
        """全域設定變更時更新顯示"""
        previous = (
            self.filter_pit_laps,
            self.filter_outliers,
            self.outlier_threshold,
        )
        self._apply_boxplot_settings(settings)

        current = (
            self.filter_pit_laps,
            self.filter_outliers,
            self.outlier_threshold,
        )

        if previous != current and self.raw_data:
            self.processed_data = self._transform_data_for_display(self.raw_data)
            self._update_display(self.processed_data)

    def _update_settings_summary(self) -> None:
        """更新設定摘要顯示"""
        if not hasattr(self, 'settings_summary_label'):
            return

        summary_lines = [
            f"Filter pit laps: {'Enabled' if self.filter_pit_laps else 'Disabled'}",
            f"Filter outliers (IQR): {'Enabled' if self.filter_outliers else 'Disabled'}",
            f"Outlier threshold: {self.outlier_threshold:.1f} × IQR",
        ]

        self.settings_summary_label.setText("\n".join(summary_lines))

    def _open_system_settings(self) -> None:
        """開啟系統設定對話框"""
        if self.settings_manager:
            self.settings_manager.open_system_settings_dialog(self)
    
    def _get_team_colors(self, drivers: List[str]) -> List[str]:
        """獲取車隊配色"""
        # 簡化版車隊配色（可以後續擴展）
        team_colors = {
            'VER': '#0600EF',  # Red Bull
            'PER': '#0600EF',
            'LEC': '#DC0000',  # Ferrari
            'SAI': '#DC0000',
            'HAM': '#00D2BE',  # Mercedes
            'RUS': '#00D2BE',
            'NOR': '#FF8700',  # McLaren
            'PIA': '#FF8700',
            'ALO': '#006F62',  # Aston Martin
            'STR': '#006F62',
            'GAS': '#0090FF',  # Alpine
            'OCO': '#0090FF',
            'TSU': '#2B4562',  # AlphaTauri
            'LAW': '#2B4562',
            'HUL': '#FFFFFF',  # Haas
            'MAG': '#FFFFFF',
            'BOT': '#900000',  # Alfa Romeo
            'ZHO': '#900000',
            'ALB': '#005AFF',  # Williams
            'SAR': '#005AFF',
        }
        
        colors = []
        for driver in drivers:
            colors.append(team_colors.get(driver, '#CCCCCC'))
        
        return colors
    
    # ===== 事件處理 =====
    
    def refresh_analysis(self):
        """刷新分析"""
        if self.current_year and self.current_race and self.current_session:
            self._debug("手動刷新分析...")
            self.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )
        else:
            QMessageBox.warning(self, "Warning", "No race parameters set!")
    
    def export_chart(self):
        """導出圖表"""
        if not self.chart_widget or not self.boxplot_stats:
            QMessageBox.warning(self, "Warning", "No chart to export!")
            return

        from PyQt5.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            f"laptime_boxplot_{self.current_year}_{self.current_race}_{self.current_session}.png",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )

        if filename:
            try:
                pixmap = self.chart_widget.grab()
                if not pixmap.save(filename):
                    raise RuntimeError("Failed to save chart pixmap")
                QMessageBox.information(self, "Success", f"Chart exported to:\n{filename}")
                self._debug(f"✅ 圖表已導出: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export chart:\n{e}")
                self._debug(f"❌ 導出失敗: {e}")
    
    # ===== CLI 回調 =====
    
    def _on_cli_completed(self, success: bool, message: str):
        """CLI 分析完成回調"""
        if success:
            self._debug(f"✅ CLI 分析成功: {message}")
            if self.status_label:
                self.status_label.setText("✅ CLI analysis completed, loading data...")
            
            # 重新嘗試載入數據
            self.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )
        else:
            self._debug(f"❌ CLI 分析失敗: {message}")
            if self.status_label:
                self.status_label.setText(f"❌ CLI analysis failed: {message}")
            QMessageBox.critical(self, "CLI Error", f"Analysis failed:\n{message}")
    
    def _on_cli_progress(self, message: str):
        """CLI 進度更新回調"""
        if self.status_label:
            self.status_label.setText(f"⏳ {message}")


# 測試代碼
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 設置字體
    font = QFont("Arial", 9)
    app.setFont(font)
    
    # 創建測試視窗
    widget = LapTimeBoxPlotWidget(year=2025, race="Belgium", session="R")
    widget.setWindowTitle("Lap Time Box Plot - Test")
    widget.resize(1400, 800)
    widget.show()
    
    sys.exit(app.exec_())
