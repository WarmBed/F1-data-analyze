#!/usr/bin/env python3
"""
彎道性能散佈圖組件
Corner Performance Scatter Chart Widget

專用 XY 散佈圖組件，用於顯示各車手的彎道性能
- X 軸：入彎速度（entry_50m_speed）
- Y 軸：出彎速度（exit_50m_speed）
- 點色：彎中心速度（apex_speed）

作者: F1T Team
日期: 2025-10-26
版本: 1.0.0
"""

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QMessageBox, QMenu
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor, QColor
from typing import Dict, List, Any, Optional

# 導入國際化和車隊顔色
from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import color_palette_provider


class CornerPerformanceScatterWidget(QWidget):
    """
    彎道性能散佈圖組件
    
    功能：
    - XY 散佈圖（入彎速度 vs 出彎速度）
    - 點色表示彎中心速度
    - 彎道類型切換（低、中、高速）
    - 車手高亮顯示
    - 圖表匯出
    """
    
    # 信號定義
    driver_clicked = pyqtSignal(str)  # 點擊車手時觸發
    corner_switched = pyqtSignal(str)  # 彎道切換時觸發 ("low_speed", "mid_speed", "high_speed")
    
    def __init__(self, parent=None, corner_type="low_speed"):
        """
        初始化散佈圖組件
        
        Args:
            parent: 父組件
            corner_type: 初始彎道類型 ("low_speed", "mid_speed", "high_speed")
        """
        super().__init__(parent)
        
        # 數據屬性
        self.current_data: Optional[Dict] = None
        self.current_corner_type = corner_type  # 使用傳入的初始值
        self.highlighted_driver: Optional[str] = None
        
        # 圖表顯示相關
        self.scatter_points = None  # 散佈點對象
        self.annotations = []  # 標註列表
        self.hover_annotation = None  # 懸停標註
        self.driver_data_map = {}  # 車手數據映射 {index: {driver, entry, exit, apex}}
        
        # 固定標籤管理
        self.pinned_annotations = []  # 儲存已固定的標籤 [{annotation, driver, xy, custom_pos, data_point}]
        self.dragging_annotation = None  # 當前拖曳的標籤
        self.drag_start_pos = None  # 拖曳起始位置（用於計算位移）
        
        # 隱藏過濾管理
        self.hidden_drivers = set()  # 儲存被隱藏的車手代碼集合
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 創建 Matplotlib 圖形（參考 universal_chart_widget 的設定）
        # 使用較小的固定尺寸作為基準，讓 canvas 自動縮放填滿
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # 設置 SizePolicy 讓圖表能夠自適應視窗大小（參考 universal_chart_widget）
        from PyQt5.QtWidgets import QSizePolicy
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.ax = None
        
        # 初始化 UI
        self._init_ui()
        
        # 連接滑鼠事件
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        
    
    def _get_driver_color_hex(self, driver_code: str) -> str:
        """
        根據車手代碼獲取車隊顔色的十六進制字串
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            十六進制顔色字串 (例如 '#FF0000')
        """
        try:
            color_palette_provider.ensure_loaded()
            qcolor = color_palette_provider.get_driver_color(driver_code, fallback=True)
            if isinstance(qcolor, QColor):
                return qcolor.name()
            return '#666666'
        except Exception:
            return '#666666'
    
    def _get_contrasting_text_color(self, bg_color_hex: str) -> str:
        """
        根據背景顔色亮度計算對比文字顔色（白色或黑色）
        
        使用 YIQ 亮度公式：Y = 0.299*R + 0.587*G + 0.114*B
        亮度 < 128 返回白色文字
        亮度 >= 128 返回黑色文字
        
        Args:
            bg_color_hex: 背景顔色的十六進制字串 (如 '#FF0000')
            
        Returns:
            文字顔色的十六進制字串 ('#FFFFFF' 或 '#000000')
        """
        try:
            qcolor = QColor(bg_color_hex)
            luminance = (0.299 * qcolor.red() + 0.587 * qcolor.green() + 0.114 * qcolor.blue())
            return '#FFFFFF' if luminance < 128 else '#000000'
        except Exception:
            return '#000000'  # 預設黑色
    
    def resizeEvent(self, event):
        """
        視窗縮放事件處理
        
        當窗大小改變時，重新調整 matplotlib 佈局以避免留白問題
        參考 universal_chart_widget 的實現
        """
        super().resizeEvent(event)
        
        # 如果有圖表數據，重新調整佈局
        if self.ax is not None:
            try:
                self.figure.tight_layout()
                self.canvas.draw_idle()
            except Exception as e:
                # 忽略佈局調整錯誤（可能在極端視窗時觸發）
                pass
        
    def _init_ui(self):
        """初始化 UI 組件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除外邊距
        layout.setSpacing(5)  # 減少組件間距為 5 像素
        
        # 簡化控制面板 - 移除不需要的控件
        control_layout = QHBoxLayout()
        
        # 隱藏彎道類型切換（父級模組已經是分頁選項卡）
        self.corner_combo = QComboBox()
        self.corner_combo.addItem(tr("low_speed_corner", "低速彎"), "low_speed")
        self.corner_combo.addItem(tr("mid_speed_corner", "中速彎"), "mid_speed")
        self.corner_combo.addItem(tr("high_speed_corner", "高速彎"), "high_speed")
        self.corner_combo.currentIndexChanged.connect(self._on_corner_switch)
        self.corner_combo.hide()  # 隱藏 ComboBox
        
        # 隱藏匯出按鈕（目前未實現）
        self.export_btn = QPushButton(tr("export_chart", "匯出圖表"))
        self.export_btn.clicked.connect(self._export_chart)
        self.export_btn.hide()  # 隱藏匯出按鈕
        
        # 隱藏更新按鈕（數據由父級載入）
        self.refresh_btn = QPushButton(tr("refresh_chart", "更新圖表"))
        self.refresh_btn.clicked.connect(self._refresh_chart)
        self.refresh_btn.hide()  # 隱藏更新按鈕
        
        # 說明標籤
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-size: 10pt;")
        
        # 只顯示說明標籤（父級 GUI 已有 "Show All Data" 按鈕）
        control_layout.addStretch()
        control_layout.addWidget(self.info_label)
        control_layout.addStretch()
        
        # 添加到主佈局
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
        
        # 設置 ComboBox 的正確初始索引（根據 self.current_corner_type）
        corner_index_map = {
            "low_speed": 0,
            "mid_speed": 1,
            "high_speed": 2
        }
        initial_index = corner_index_map.get(self.current_corner_type, 0)
        self.corner_combo.setCurrentIndex(initial_index)
        
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據並重繪圖表
        
        Args:
            data: 包含 fastest_lap_analysis 和 selected_corners 的數據字典
        """
        try:
            if not data or not isinstance(data, dict):
                return
            
            self.current_data = data
            
            # 更新說明標籤
            self._update_info_label()
            
            # 繪製圖表
            self.draw_scatter_chart()
            
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def draw_scatter_chart(self):
        """
        繪製散佈圖
        
        X 軸：入彎速度（entry_50m_speed）
        Y 軸：出彎速度（exit_50m_speed）
        顏色：彎中心速度（apex_speed）
        """
        try:
            if not self.current_data:
                return
            
            # 清除先前固定的標籤（重繪圖表前）
            self._clear_all_pinned_annotations()
            
            # 清空圖形
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 獲取選中的彎道數據
            selected_corners = self.current_data.get("selected_corners", {})
            corner_info = selected_corners.get(self.current_corner_type)
            
            if not corner_info:
                self._show_no_data_message()
                return
            
            # 獲取車手數據列表
            fastest_lap_analysis = self.current_data.get("fastest_lap_analysis", {})
            drivers_data = fastest_lap_analysis.get("drivers", [])
            
            if not drivers_data:
                self._show_no_data_message()
                return
            
            # 準備散佈圖數據
            x_data = []  # 入彎速度
            y_data = []  # 出彎速度
            colors = []  # 彎中心速度
            labels = []  # 車手代碼
            
            # 清空車手數據映射
            self.driver_data_map = {}
            
            # 彎道類型對應的鍵名
            corner_key = f"{self.current_corner_type}_corner_{corner_info['corner_number']}"
            
            for driver_data in drivers_data:
                driver = driver_data.get("driver", "")
                
                # 過濾被隱藏的車手
                if driver in self.hidden_drivers:
                    continue
                
                corners = driver_data.get("corners", {})
                corner_speeds = corners.get(corner_key)
                
                if not corner_speeds:
                    continue
                
                entry_speed = corner_speeds.get("entry_50m_speed")
                exit_speed = corner_speeds.get("exit_50m_speed")
                apex_speed = corner_speeds.get("apex_speed")
                
                # 只添加有效數據
                if entry_speed and exit_speed and apex_speed:
                    index = len(x_data)  # 當前索引
                    x_data.append(entry_speed)
                    y_data.append(exit_speed)
                    colors.append(apex_speed)
                    labels.append(driver)
                    
                    # 儲存車手數據映射（用於懸停提示）
                    self.driver_data_map[index] = {
                        'driver': driver,
                        'entry_speed': entry_speed,
                        'exit_speed': exit_speed,
                        'apex_speed': apex_speed
                    }
            
            if not x_data:
                self._show_no_data_message()
                return
            
            # 繪製散佈圖
            self.scatter_points = self.ax.scatter(
                x_data, y_data,
                c=colors,
                cmap='RdYlGn',  # 紅黃綠色帶（慢到快）
                s=150,  # 點大小
                alpha=0.7,
                edgecolors='black',
                linewidth=1.5,
                picker=True,  # 啟用點擊檢測
                pickradius=10  # 檢測半徑
            )
            
            # 添加顏色條
            cbar = self.figure.colorbar(self.scatter_points, ax=self.ax)
            cbar.set_label(
                tr("apex_speed_kmh", "彎中心速度 (km/h)"),
                fontsize=11,
                weight='bold'
            )
            
            # 智能標籤佈局演算法 - 初始佈局 + 碰撞檢測
            import math
            
            # 計算數據中心點和範圍
            center_x = sum(x_data) / len(x_data)
            center_y = sum(y_data) / len(y_data)
            x_min, x_max = min(x_data), max(x_data)
            y_min, y_max = min(y_data), max(y_data)
            x_range = x_max - x_min
            y_range = y_max - y_min
            
            # 初始標籤位置（基於角度）
            label_positions = []
            for i in range(len(x_data)):
                dx = x_data[i] - center_x
                dy = y_data[i] - center_y
                angle = math.atan2(dy, dx)
                
                # 初始偏移
                offset_distance = 20
                x_offset = offset_distance * math.cos(angle)
                y_offset = offset_distance * math.sin(angle)
                
                label_positions.append({
                    'x': x_data[i],
                    'y': y_data[i],
                    'x_offset': x_offset,
                    'y_offset': y_offset,
                    'label': labels[i]
                })
            
            # === 固定 5x5 偏移 + 邊界反射 + 重疊半透明 ===
            # 重疊檢測：計算所有標籤的邊界框
            label_bboxes = []
            
            for lbl in label_positions:
                # 固定 5x5 偏移（預設）
                x_offset = 5
                y_offset = 5
                
                # 邊界反射：右邊界 → 左偏移
                if lbl['x'] > center_x + (x_max - center_x) * 0.7:
                    x_offset = -5
                
                # 邊界反射：上邊界 → 下偏移
                if lbl['y'] > center_y + (y_max - center_y) * 0.8:
                    y_offset = -5
                
                # 邊界反射：左邊界 → 右偏移
                if lbl['x'] < center_x - (center_x - x_min) * 0.7:
                    x_offset = 5
                
                # 邊界反射：下邊界 → 上偏移
                if lbl['y'] < center_y - (center_y - y_min) * 0.8:
                    y_offset = 5
                
                # 儲存計算結果
                lbl['x_offset'] = x_offset
                lbl['y_offset'] = y_offset
                
                # 計算標籤實際位置（數據座標）
                label_x = lbl['x'] + (x_offset / 72.0) * x_range
                label_y = lbl['y'] + (y_offset / 72.0) * y_range
                
                # 估算標籤邊界框（粗略計算）
                label_width = x_range * 0.04  # 標籤寬度約佔 4% x 範圍
                label_height = y_range * 0.025  # 標籤高度約佔 2.5% y 範圍
                
                bbox = {
                    'x_min': label_x - label_width / 2,
                    'x_max': label_x + label_width / 2,
                    'y_min': label_y - label_height / 2,
                    'y_max': label_y + label_height / 2,
                    'index': len(label_bboxes)
                }
                label_bboxes.append(bbox)
            
            # 檢測重疊並標記
            overlapping_indices = set()
            for i in range(len(label_bboxes)):
                for j in range(i + 1, len(label_bboxes)):
                    bbox_i = label_bboxes[i]
                    bbox_j = label_bboxes[j]
                    
                    # 檢查邊界框是否重疊
                    x_overlap = not (bbox_i['x_max'] < bbox_j['x_min'] or bbox_i['x_min'] > bbox_j['x_max'])
                    y_overlap = not (bbox_i['y_max'] < bbox_j['y_min'] or bbox_i['y_min'] > bbox_j['y_max'])
                    
                    if x_overlap and y_overlap:
                        overlapping_indices.add(i)
                        overlapping_indices.add(j)
            
            # 繪製標籤（固定偏移 + 半透明處理）
            for idx, lbl in enumerate(label_positions):
                x_offset = lbl['x_offset']
                y_offset = lbl['y_offset']
                driver_code = lbl['label']
                
                # 根據偏移方向決定對齊方式
                ha = 'left' if x_offset > 0 else 'right'
                va = 'bottom' if y_offset > 0 else 'top'
                
                # 獲取車隊顏色
                bg_color = self._get_driver_color_hex(driver_code)
                text_color = self._get_contrasting_text_color(bg_color)
                
                # 重疊處理：半透明
                alpha = 0.5 if idx in overlapping_indices else 0.9
                
                # 繪製帶背景色的標籤
                self.ax.annotate(
                    driver_code,
                    (lbl['x'], lbl['y']),
                    xytext=(x_offset, y_offset),
                    textcoords='offset points',
                    fontsize=8,
                    weight='bold',
                    color=text_color,
                    ha=ha,
                    va=va,
                    clip_on=True,
                    bbox=dict(
                        boxstyle='round,pad=0.4',
                        facecolor=bg_color,
                        edgecolor='none',
                        alpha=alpha  # 重疊時半透明
                    )
                )
            
            # 設置座標軸範圍（增加邊距）
            x_margin = x_range * 0.1
            y_margin = y_range * 0.1
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
            
            # 設置標籤
            corner_number = corner_info['corner_number']
            avg_speed = corner_info['avg_apex_speed']
            
            self.ax.set_xlabel(
                tr("entry_speed_50m", "入彎速度 (-50m) [km/h]"),
                fontsize=12,
                weight='bold'
            )
            self.ax.set_ylabel(
                tr("exit_speed_50m", "出彎速度 (+50m) [km/h]"),
                fontsize=12,
                weight='bold'
            )
            
            # 移除圖表標題（父級標題已足夠）
            # corner_number = corner_info['corner_number']
            # avg_speed = corner_info['avg_apex_speed']
            # title = f"T{corner_number} 性能分布 (平均速度: {avg_speed:.1f} km/h)"
            # self.ax.set_title(title, fontsize=14, weight='bold', pad=25)
            
            # 添加網格
            self.ax.grid(True, alpha=0.3, linestyle='--')
            
            # 調整佈局（使用 matplotlib 自動計算，參考 straight_line_speed_widget）
            self.figure.tight_layout()
            
            # 重新繪製
            self.canvas.draw()
            
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _show_no_data_message(self):
        """顯示無數據提示"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.text(
            0.5, 0.5,
            tr("no_corner_data", "該彎道無數據"),
            ha='center', va='center',
            fontsize=16,
            transform=self.ax.transAxes
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def _update_info_label(self):
        """更新說明標籤"""
        if not self.current_data:
            return
        
        selected_corners = self.current_data.get("selected_corners", {})
        corner_info = selected_corners.get(self.current_corner_type)
        
        if corner_info:
            corner_number = corner_info['corner_number']
            avg_speed = corner_info['avg_apex_speed']
            text = f"T{corner_number} | {avg_speed:.1f} km/h"
            self.info_label.setText(text)
    
    def _on_corner_switch(self, index):
        """彎道類型切換事件"""
        corner_type = self.corner_combo.itemData(index)
        if corner_type != self.current_corner_type:
            self.current_corner_type = corner_type
            self._update_info_label()
            self.draw_scatter_chart()
            self.corner_switched.emit(corner_type)
    
    def _refresh_chart(self):
        """更新圖表"""
        self.draw_scatter_chart()
    
    def _on_mouse_move(self, event):
        """
        滑鼠移動事件處理（整合 hover 和 drag 功能）
        
        1. 如果正在拖曳標籤，移動標籤
        2. 否則，處理懸停提示
        """
        # 拖曳標籤處理
        if self.dragging_annotation:
            if event.inaxes == self.ax and event.xdata and event.ydata and self.drag_start_pos:
                # 計算滑鼠移動的位移量
                dx = event.xdata - self.drag_start_pos[0]
                dy = event.ydata - self.drag_start_pos[1]
                
                # 獲取當前 xytext（annotation 文字框的位置）
                annotation = self.dragging_annotation['annotation']
                current_xytext = annotation.xyann  # 獲取當前 annotation 位置
                
                # 轉換位移量為像素單位
                # 我們需要將數據座標的位移轉換為像素單位的位移
                transform = self.ax.transData
                # 獲取起始點和結束點的像素座標
                start_display = transform.transform([self.drag_start_pos])
                end_display = transform.transform([(event.xdata, event.ydata)])
                
                # 計算像素單位位移
                dx_display = end_display[0][0] - start_display[0][0]
                dy_display = end_display[0][1] - start_display[0][1]
                
                # 更新 xytext 位置
                new_xytext = (current_xytext[0] + dx_display, current_xytext[1] + dy_display)
                annotation.xyann = new_xytext
                
                # 儲存自定位置
                self.dragging_annotation['custom_pos'] = new_xytext
                
                # 更新拖曳起始位置
                self.drag_start_pos = (event.xdata, event.ydata)
                
                # 重繪畫布
                self.canvas.draw_idle()
            return
        
        # 懸停提示處理
        if event.inaxes != self.ax or self.scatter_points is None:
            # 如果不在圖表區域或沒有散佈圖，移除懸停提示
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.canvas.draw_idle()
            return
        
        # 檢查是否懸停在散點上
        cont, ind = self.scatter_points.contains(event)
        
        if cont:
            # 獲取第一個懸停的點
            index = ind['ind'][0]
            
            # 從映射中獲取車手資訊
            if index in self.driver_data_map:
                driver_info = self.driver_data_map[index]
                
                # 獲取散點的實際座標
                x_data = self.scatter_points.get_offsets()[index, 0]
                y_data = self.scatter_points.get_offsets()[index, 1]
                
                # 計算圖表中心點（用於智能定位）
                all_offsets = self.scatter_points.get_offsets()
                center_x = all_offsets[:, 0].mean()
                center_y = all_offsets[:, 1].mean()
                
                # 根據散點相對中心的位置，智能調整提示框偏移方向
                if x_data > center_x:
                    x_offset = -15
                    ha = 'right'
                else:
                    x_offset = 15
                    ha = 'left'
                
                if y_data > center_y:
                    y_offset = -15
                    va = 'top'
                else:
                    y_offset = 15
                    va = 'bottom'
                
                # 創建或更新懸停提示
                if self.hover_annotation is None:
                    self.hover_annotation = self.ax.annotate(
                        '',
                        xy=(0, 0),
                        xytext=(x_offset, y_offset),
                        textcoords='offset points',
                        bbox=dict(
                            boxstyle='round,pad=0.8',
                            facecolor='yellow',
                            alpha=0.9,
                            edgecolor='black',
                            linewidth=2
                        ),
                        fontsize=10,
                        weight='normal',
                        color='black',
                        zorder=100,
                        ha=ha,
                        va=va
                    )
                else:
                    # 更新偏移量
                    self.hover_annotation.set_position((x_offset, y_offset))
                    self.hover_annotation.set_ha(ha)
                    self.hover_annotation.set_va(va)
                
                # 組合顯示文字
                text = (
                    f"{driver_info['driver']}\n"
                    f"────────────\n"
                    f"{tr('entry_label', '入彎')}: {driver_info['entry_speed']:.1f} km/h\n"
                    f"{tr('apex_label', '彎心')}: {driver_info['apex_speed']:.1f} km/h\n"
                    f"{tr('exit_label', '出彎')}: {driver_info['exit_speed']:.1f} km/h"
                )
                
                # 更新標註
                self.hover_annotation.set_text(text)
                self.hover_annotation.xy = (x_data, y_data)
                self.hover_annotation.set_visible(True)
                
                # 重繪畫布
                self.canvas.draw_idle()
        else:
            # 沒有懸停在任何點上，隱藏標註
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.canvas.draw_idle()
    
    def _on_click(self, event):
        """
        滑鼠點擊事件處理
        
        左鍵點擊：
        1. 如果點擊已固定的標籤，開始拖曳
        2. 如果點擊散點，固定該散點的提示
        
        右鍵點擊：
        1. 如果點擊散點，顯示選單（含 Hide Driver 選項）
        2. 如果點擊固定標籤，移除該標籤
        3. 如果點擊空白區，清除先前固定的標籤
        """
        if event.inaxes != self.ax or self.scatter_points is None:
            return
        
        # 右鍵：顯示選單或移除標籤
        if event.button == 3:  # 右鍵
            # 先檢查是否點擊散點（最高優先級）
            cont, ind = self.scatter_points.contains(event)
            if cont:
                index = ind['ind'][0]
                if index in self.driver_data_map:
                    # 顯示右鍵選單
                    self._show_context_menu(index, event)
                    return
            
            # 檢查是否點擊了固定標籤
            clicked_pinned = None
            for pinned in self.pinned_annotations:
                annotation = pinned['annotation']
                contains, _ = annotation.contains(event)
                if contains:
                    clicked_pinned = pinned
                    break
            
            if clicked_pinned:
                # 移除該標籤
                self._remove_specific_pinned_annotation(clicked_pinned)
            else:
                # 點擊空白區，清除先前固定的標籤
                self._clear_all_pinned_annotations()
            return
        
        # 左鍵：檢查是否點擊已固定的標籤或散點
        if event.button == 1:  # 左鍵
            # 先檢查是否點擊已固定的標籤（用於拖曳）
            for pinned in self.pinned_annotations:
                annotation = pinned['annotation']
                # matplotlib annotation 的 contains 方法
                contains, _ = annotation.contains(event)
                if contains:
                    # 開始拖曳該標籤
                    self.dragging_annotation = pinned
                    # 記錄拖曳起始位置（滑鼠在數據座標系中的位置）
                    self.drag_start_pos = (event.xdata, event.ydata)
                    return
            
            # 檢查是否點擊散點
            cont, ind = self.scatter_points.contains(event)
            if cont:
                index = ind['ind'][0]
                if index in self.driver_data_map:
                    self._pin_annotation(index)
    
    def _on_release(self, event):
        """
        滑鼠釋放事件處理
        
        停止拖曳標籤
        """
        if self.dragging_annotation:
            self.dragging_annotation = None
            self.drag_start_pos = None
    
    def _pin_annotation(self, index: int):
        """
        固定指定索引的散點提示
        
        Args:
            index: 散點索引
        """
        driver_info = self.driver_data_map[index]
        
        # 檢查是否已固定該車手
        for pinned in self.pinned_annotations:
            if pinned['driver'] == driver_info['driver']:
                return
        
        # 獲取散點座標
        x_data = self.scatter_points.get_offsets()[index, 0]
        y_data = self.scatter_points.get_offsets()[index, 1]
        
        # 計算智能偏移
        all_offsets = self.scatter_points.get_offsets()
        center_x = all_offsets[:, 0].mean()
        center_y = all_offsets[:, 1].mean()
        
        if x_data > center_x:
            x_offset = -15
            ha = 'right'
        else:
            x_offset = 15
            ha = 'left'
        
        if y_data > center_y:
            y_offset = -15
            va = 'top'
        else:
            y_offset = 15
            va = 'bottom'
        
        # 創建固定標籤
        text = (
            f"{driver_info['driver']}\n"
            f"────────────\n"
            f"{tr('entry_label', '入彎')}: {driver_info['entry_speed']:.1f} km/h\n"
            f"{tr('apex_label', '彎心')}: {driver_info['apex_speed']:.1f} km/h\n"
            f"{tr('exit_label', '出彎')}: {driver_info['exit_speed']:.1f} km/h"
        )
        
        annotation = self.ax.annotate(
            text,
            xy=(x_data, y_data),
            xytext=(x_offset, y_offset),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.8',
                facecolor='lightblue',
                alpha=0.95,
                edgecolor='darkblue',
                linewidth=2
            ),
            fontsize=10,
            weight='normal',
            color='black',
            zorder=101,
            ha=ha,
            va=va,
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0',
                color='darkblue',
                linewidth=1.5
            )
        )
        
        # 儲存固定標籤
        self.pinned_annotations.append({
            'annotation': annotation,
            'driver': driver_info['driver'],
            'data_point': (x_data, y_data),  # 儲存原始數據點座標
            'custom_pos': None  # 自定位置（拖曳時使用）
        })
        
        # 重繪畫布
        self.canvas.draw_idle()
        
    
    def _remove_specific_pinned_annotation(self, pinned):
        """
        移除指定的固定標籤
        
        Args:
            pinned: 標籤字典
        """
        if pinned:
            # 移除標籤
            pinned['annotation'].remove()
            self.pinned_annotations.remove(pinned)
            self.canvas.draw_idle()
    
    def _clear_all_pinned_annotations(self):
        """清除先前固定的標籤"""
        if not self.pinned_annotations:
            return
        
        for pinned in self.pinned_annotations:
            pinned['annotation'].remove()
        self.pinned_annotations.clear()
        self.canvas.draw_idle()
    
    # ========== 右鍵選單與數據過濾功能 ==========
    
    def _show_context_menu(self, index: int, event):
        """
        顯示右鍵選單
        
        Args:
            index: 散點索引
            event: 滑鼠事件
        """
        driver_info = self.driver_data_map.get(index)
        if not driver_info:
            return
        
        driver = driver_info['driver']
        
        # 創建選單
        menu = QMenu(self)
        
        # 添加 "Hide Driver" 選項
        hide_action = menu.addAction(f"{tr('hide_driver', 'Hide')} {driver}")
        hide_action.triggered.connect(lambda: self._hide_driver(driver))
        
        # 顯示選單（使用全局位置）
        # 將 matplotlib 事件座標轉換為螢幕座標
        try:
            # 獲取 canvas 在螢幕的位置
            canvas_pos = self.canvas.mapToGlobal(self.canvas.pos())
            # 將 matplotlib 座標轉換為 widget 座標
            x_widget = int(event.x)
            y_widget = int(self.canvas.height() - event.y)  # matplotlib Y 軸是從下往上
            # 計算全局座標
            global_pos = canvas_pos + self.canvas.mapToParent(self.canvas.pos())
            global_pos.setX(global_pos.x() + x_widget)
            global_pos.setY(global_pos.y() + y_widget)
            
            menu.exec_(QCursor.pos())  # 使用滑鼠當前位置比較準確
        except Exception as e:
            menu.exec_(QCursor.pos())
        
    
    def _hide_driver(self, driver: str):
        """
        隱藏指定車手的數據點
        
        Args:
            driver: 車手代碼
        """
        if driver in self.hidden_drivers:
            return
        
        # 添加到隱藏列表
        self.hidden_drivers.add(driver)
        
        # 重繪圖表（重新過濾數據點並調整軸範圍）
        self.draw_scatter_chart()
    
    def show_all_drivers(self):
        """
        顯示所有數據點（恢復先前隱藏的車手）
        
        這是一個公開方法，由 MDI 視窗的 "Show All Data" 按鈕調用
        """
        if not self.hidden_drivers:
            return
        
        # 清空隱藏列表
        hidden_count = len(self.hidden_drivers)
        self.hidden_drivers.clear()
        
        # 重繪圖表（顯示所有數據並調整軸範圍）
        self.draw_scatter_chart()

    
    def _export_chart(self):
        """匯出圖表"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                tr("save_chart", "儲存圖表"),
                f"corner_performance_{self.current_corner_type}.png",
                "PNG Files (*.png);;All Files (*)"
            )
            
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(
                    self,
                    tr("success", "成功"),
                    tr("chart_exported_to", "圖表已匯出至") + f":\n{filename}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("error", "錯誤"),
                tr("export_failed", f"匯出失敗: {str(e)}")
            )
