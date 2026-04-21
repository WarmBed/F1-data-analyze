#!/usr/bin/env python3
"""
煞車性能散點圖元件
Brake Performance Scatter Chart Widget

使用 Matplotlib 繪製煞車前速度-減速度散點圖
X軸: 煞車前速度 (km/h)
Y軸: 減速度 (m/s^2) - 使用絕對值

每個車手用車隊顏色的點表示

2025-01-19: 新增 stint 支援（Merge/Split 模式）

作者: F1T Team
日期: 2025-12-14
版本: 1.1.0
"""

from typing import Dict, List, Any, Optional
import numpy as np

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import (
    color_palette_provider,
    DEFAULT_DRIVER_MAP
)
from core.logger import get_logger

logger = get_logger("brake_chart_widget", component="gui")


class BrakeChartWidget(QWidget):
    """
    煞車性能散點圖元件
    
    視覺化:
    - X軸: 煞車前速度中位數 (km/h)
    - Y軸: 減速度中位數 (m/s^2) - 使用絕對值
    - 每個車手用車隊顏色標記
    - 點大小根據一致性(CV)調整
    
    Stint 支援 (2025-01-19):
    - is_merge_mode: True=合併所有 stint, False=依 stint 分開顯示
    - selected_stints: {driver: [stint_numbers]} 過濾選擇的 stint
    - hidden_drivers: 需要隱藏的車手集合
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 數據存儲
        self._drivers_data: List[Dict[str, Any]] = []
        self.current_data: Optional[Dict[str, Any]] = None
        
        # Stint 過濾狀態 (2025-01-19)
        self.is_merge_mode: bool = True
        self.selected_stints: Dict[str, List[int]] = {}
        self.hidden_drivers: set = set()
        
        # 初始化 Matplotlib 圖表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.canvas)
        
        # 初始化空白圖表
        self._init_empty_chart()
        
        logger.info("[BRAKE_CHART_WIDGET] Chart widget initialized")
    
    def _init_empty_chart(self):
        """初始化空白圖表"""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, 
            tr("waiting_for_data", "Waiting for data..."),
            ha='center', va='center',
            transform=self.ax.transAxes,
            fontsize=14, color='gray'
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def _get_driver_color_hex(self, driver_code: str) -> str:
        """
        獲取車手的車隊顏色（十六進制格式）
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            十六進制顏色字串 (例如 '#FF0000')
        """
        try:
            color_palette_provider.ensure_loaded()
            qcolor = color_palette_provider.get_driver_color(driver_code, fallback=True)
            if isinstance(qcolor, QColor):
                return qcolor.name()
            return '#666666'
        except Exception:
            return '#666666'
    
    def _get_team_name(self, driver_code: str) -> str:
        """
        從 DEFAULT_DRIVER_MAP 獲取車隊名稱
        
        Args:
            driver_code: 車手代碼（如 VER, HAM）
            
        Returns:
            車隊名稱（如 Red Bull Racing, Mercedes）
        """
        team_map = {
            "red bull": "Red Bull Racing",
            "mclaren": "McLaren",
            "ferrari": "Ferrari",
            "mercedes": "Mercedes",
            "aston martin": "Aston Martin",
            "alpine": "Alpine",
            "williams": "Williams",
            "haas": "Haas F1 Team",
            "rb": "RB",
            "kick sauber": "Kick Sauber",
        }
        
        if driver_code in DEFAULT_DRIVER_MAP:
            team_key = DEFAULT_DRIVER_MAP[driver_code][0]
            return team_map.get(team_key, team_key.title())
        
        return "Unknown"
    
    def set_data(self, data: Dict[str, Any]):
        """
        設置數據並繪製圖表
        
        Args:
            data: API 返回的數據，包含 drivers 陣列
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[BRAKE_CHART_WIDGET] Invalid data format")
                return
            
            # 保存完整數據 (用於 stint 過濾)
            self.current_data = data
            
            # 提取 drivers 數據
            drivers = data.get("drivers", [])
            if not drivers:
                drivers = data.get("data", {}).get("drivers", [])
            
            if not drivers:
                logger.warning("[BRAKE_CHART_WIDGET] No drivers data")
                self._init_empty_chart()
                return
            
            logger.info(f"[BRAKE_CHART_WIDGET] Setting data: {len(drivers)} drivers")
            
            self._drivers_data = drivers
            
            # 確保顏色數據已載入
            try:
                color_palette_provider.ensure_loaded()
            except Exception as e:
                logger.warning(f"[BRAKE_CHART_WIDGET] Color loading failed: {e}")
            
            # 繪製圖表
            self._plot_chart()
            
        except Exception as e:
            logger.exception(f"[BRAKE_CHART_WIDGET] Failed to set data: {e}")
    
    def _plot_chart(self):
        """繪製煞車前速度-減速度散點圖（支援 Merge/Split 模式）"""
        self.ax.clear()
        
        if not self._drivers_data:
            self._init_empty_chart()
            return
        
        # 根據模式選擇繪製方式
        if self.is_merge_mode:
            self._plot_merged_mode()
        else:
            self._plot_split_mode()
    
    def _plot_merged_mode(self):
        """
        合併模式: 每個車手一個點（使用 driver-level 統計）
        """
        plotted_drivers = []
        x_values = []
        y_values = []
        
        for driver_data in self._drivers_data:
            driver_code = driver_data.get("driver", "N/A")
            
            # 跳過隱藏的車手
            if driver_code in self.hidden_drivers:
                continue
            
            # 獲取減速度統計
            brake_stats = driver_data.get("brake_decel_stats", {})
            entry_speed_stats = driver_data.get("entry_speed_stats", {})
            
            # 獲取中位數減速度（使用絕對值）
            median_decel = brake_stats.get("median")
            if median_decel is not None:
                median_decel = abs(float(median_decel))
            
            # 獲取中位數煞車前速度
            median_entry_speed = entry_speed_stats.get("median")
            
            if median_decel is None or median_entry_speed is None:
                logger.debug(f"[BRAKE_CHART_WIDGET] Skipping {driver_code}: missing data")
                continue
            
            # 獲取 CV 用於點大小
            cv = brake_stats.get("cv", 10)
            point_size = max(80, min(250, 300 - cv * 10))
            
            # 獲取顏色
            color = self._get_driver_color_hex(driver_code)
            team = self._get_team_name(driver_code)
            
            # 繪製散點
            self.ax.scatter(
                median_entry_speed,
                median_decel,
                c=color,
                s=point_size,
                alpha=0.85,
                edgecolors='white',
                linewidths=1.5,
                label=f"{driver_code} ({team})",
                zorder=5
            )
            
            # 添加車手標籤
            self.ax.annotate(
                driver_code,
                (median_entry_speed, median_decel),
                xytext=(6, 6),
                textcoords='offset points',
                fontsize=9,
                fontweight='bold',
                color=color
            )
            
            plotted_drivers.append(driver_code)
            x_values.append(median_entry_speed)
            y_values.append(median_decel)
        
        # 添加趨勢線
        self._add_trend_line(x_values, y_values)
        
        self._finalize_chart(plotted_drivers, mode="Merge")
    
    def _plot_split_mode(self):
        """
        分離模式: 每個 stint 一個點（使用 stint-level 統計）
        """
        plotted_items = []
        x_values = []
        y_values = []
        
        for driver_data in self._drivers_data:
            driver_code = driver_data.get("driver", "N/A")
            
            # 跳過隱藏的車手
            if driver_code in self.hidden_drivers:
                continue
            
            # 獲取 stints
            stints = driver_data.get("stints", [])
            
            if not stints:
                logger.debug(f"[BRAKE_CHART_WIDGET] Driver {driver_code} has no stint data, skipping")
                continue
            
            # 過濾選擇的 stints
            selected = self.selected_stints.get(driver_code, [])
            if selected:
                # 支援 stint_id 或 stint_number 兩種命名
                stints = [s for s in stints if s.get("stint_id", s.get("stint_number")) in selected]
            
            # 獲取車手基礎顏色
            base_color = self._get_driver_color_hex(driver_code)
            
            for stint in stints:
                stint_number = stint.get("stint_id", stint.get("stint_number", 0))
                compound = stint.get("compound", "UNKNOWN")
                
                # 嘗試從 stint 獲取統計
                brake_stats = stint.get("brake_decel_stats", {})
                entry_speed_stats = stint.get("entry_speed_stats", {})
                
                median_decel = brake_stats.get("median")
                if median_decel is not None:
                    median_decel = abs(float(median_decel))
                
                median_entry_speed = entry_speed_stats.get("median")
                
                # 如果沒有 stint-level 統計，使用 driver-level 作為 fallback
                if median_decel is None:
                    fallback_brake = driver_data.get("brake_decel_stats", {})
                    fallback_val = fallback_brake.get("median")
                    if fallback_val is not None:
                        median_decel = abs(float(fallback_val))
                
                if median_entry_speed is None:
                    fallback_entry = driver_data.get("entry_speed_stats", {})
                    median_entry_speed = fallback_entry.get("median")
                
                if median_decel is None or median_entry_speed is None:
                    continue
                
                # 散點使用輪胎顏色，標籤使用車手顏色
                tire_color = self._get_tire_color(compound, base_color)
                marker = self._get_tire_marker(compound)
                
                # 繪製散點（輪胎顏色 + 黑框讓白色可見）
                self.ax.scatter(
                    median_entry_speed,
                    median_decel,
                    c=tire_color,
                    s=120,
                    alpha=0.85,
                    edgecolors='black',  # 黑框讓 HARD 白色可見
                    linewidths=1.5,
                    marker=marker,
                    zorder=5
                )
                
                # 添加標籤 (車手 S#) - 使用車手顏色
                label_text = f"{driver_code} S{stint_number}"
                self.ax.annotate(
                    label_text,
                    (median_entry_speed, median_decel),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    fontweight='bold',
                    color=base_color  # 車手顏色
                )
                
                plotted_items.append(label_text)
                x_values.append(median_entry_speed)
                y_values.append(median_decel)
        
        # 添加趨勢線
        self._add_trend_line(x_values, y_values)
        
        self._finalize_chart(plotted_items, mode="Split")
    
    def _get_tire_color(self, compound: str, base_color: str) -> str:
        """根據輪胎類型返回顏色"""
        tire_colors = {
            "SOFT": "#FF0000",
            "MEDIUM": "#FFCC00",
            "HARD": "#FFFFFF",
            "INTERMEDIATE": "#00AA00",
            "WET": "#0066FF"
        }
        return tire_colors.get(compound.upper(), base_color)
    
    def _get_tire_marker(self, compound: str) -> str:
        """根據輪胎類型返回標記形狀"""
        markers = {
            "SOFT": "o",
            "MEDIUM": "s",
            "HARD": "D",
            "INTERMEDIATE": "^",
            "WET": "v"
        }
        return markers.get(compound.upper(), "o")
    
    def _add_trend_line(self, x_values: List[float], y_values: List[float]):
        """添加趨勢線"""
        if len(x_values) >= 3:
            try:
                z = np.polyfit(x_values, y_values, 1)
                p = np.poly1d(z)
                x_trend = np.linspace(min(x_values) - 5, max(x_values) + 5, 100)
                self.ax.plot(x_trend, p(x_trend), '--', color='gray', alpha=0.5,
                           label=tr("trend_line", "Trend Line"), zorder=1)
            except Exception as e:
                logger.debug(f"[BRAKE_CHART_WIDGET] Trend line failed: {e}")
    
    def _finalize_chart(self, plotted_items: List[str], mode: str = "Merge"):
        """完成圖表繪製（設置標籤、標題等）"""
        if not plotted_items:
            logger.warning("[BRAKE_CHART_WIDGET] No valid data points to plot")
            self._init_empty_chart()
            return
        
        # 設置圖表樣式
        self.ax.set_xlabel(
            tr("brake_chart_x_label", "Entry Speed (km/h)"),
            fontsize=12, fontweight='bold'
        )
        self.ax.set_ylabel(
            tr("brake_chart_y_label", "Deceleration (m/s^2)"),
            fontsize=12, fontweight='bold'
        )
        
        # 標題包含模式信息
        title_suffix = f" [{mode} Mode]"
        self.ax.set_title(
            tr("brake_chart_title", "Brake Performance - Entry Speed vs Deceleration") + title_suffix,
            fontsize=14, fontweight='bold', pad=15
        )
        
        # 添加註解說明
        note_text = tr("brake_chart_note", "Point size = Consistency (larger = more consistent)")
        if mode == "Split":
            note_text = tr("brake_chart_note_split", "Shape = Tire compound")
        self.ax.text(
            0.02, 0.98,
            note_text,
            transform=self.ax.transAxes,
            fontsize=9, color='gray',
            verticalalignment='top'
        )
        
        # 網格
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_axisbelow(True)
        
        # 設置背景色
        self.ax.set_facecolor('#f8f9fa')
        self.figure.patch.set_facecolor('#ffffff')
        
        # 調整邊距
        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12)
        
        # 重繪
        self.canvas.draw()
        
        logger.info(f"[BRAKE_CHART_WIDGET] Chart plotted ({mode}): {len(plotted_items)} points")
    
    def clear(self):
        """清空圖表"""
        self._drivers_data = []
        self.current_data = None
        self._init_empty_chart()
    
    def filter_by_stints(self, filter_dict: Dict[str, List[int]], is_merge_mode: bool = True):
        """
        根據 stint 選擇過濾圖表
        
        Args:
            filter_dict: {driver: [stint_numbers]} 格式的過濾條件
            is_merge_mode: True=合併模式, False=分離模式
        """
        logger.debug(f"[BRAKE_CHART_WIDGET] filter_by_stints: {len(filter_dict)} drivers, merge={is_merge_mode}")
        
        self.selected_stints = filter_dict
        self.is_merge_mode = is_merge_mode
        
        # 重新繪製
        self._plot_chart()
    
    def set_visible_drivers(self, visible_drivers: set):
        """
        設置可見的車手集合
        
        Args:
            visible_drivers: 可見車手代碼的集合
        """
        # 計算隱藏的車手
        all_drivers = set()
        for driver_data in self._drivers_data:
            all_drivers.add(driver_data.get("driver", ""))
        
        self.hidden_drivers = all_drivers - visible_drivers
        
        logger.debug(f"[BRAKE_CHART_WIDGET] set_visible_drivers: {len(visible_drivers)} visible, {len(self.hidden_drivers)} hidden")


__all__ = ["BrakeChartWidget"]
