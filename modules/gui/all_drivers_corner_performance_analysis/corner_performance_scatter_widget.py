#!/usr/bin/env python3
"""
彎道性能散點圖元件
Corner Performance Scatter Chart Widget

提供 XY 散點圖，用於顯示全車手的彎道性能
- X 軸：進彎速度（entry_50m_speed）
- Y 軸：出彎速度（exit_50m_speed）
- 點顏色：彎中心速度（apex_speed）

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
    QLabel, QComboBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict, List, Any, Optional

# 導入國際化和車隊配色
from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import color_palette_provider


class CornerPerformanceScatterWidget(QWidget):
    """
    彎道性能散點圖元件
    
    功能：
    - XY 散點圖（進彎速度 vs 出彎速度）
    - 點顏色表示彎中心速度
    - 彎道類型切換（低速/中速/高速）
    - 車手高亮顯示
    - 圖表匯出
    """
    
    # 信號定義
    driver_clicked = pyqtSignal(str)  # 點擊車手時發射
    corner_switched = pyqtSignal(str)  # 彎道切換時發射 ("low_speed", "mid_speed", "high_speed")
    
    def __init__(self, parent=None, corner_type="low_speed"):
        """
        初始化圖表元件
        
        Args:
            parent: 父元件
            corner_type: 初始彎道類型 ("low_speed", "mid_speed", "high_speed")
        """
        super().__init__(parent)
        
        # 數據屬性
        self.current_data: Optional[Dict] = None
        self.current_corner_type = corner_type  # 使用傳入的初始類型
        self.highlighted_driver: Optional[str] = None
        
        # 懸停提示相關
        self.scatter_points = None  # 散點圖對象
        self.annotations = []  # 標註列表
        self.hover_annotation = None  # 懸停標註
        self.driver_data_map = {}  # 車手數據映射 {index: {driver, entry, exit, apex}}
        
        # 固定標籤管理
        self.pinned_annotations = []  # 儲存已固定的標籤 [{annotation, driver, xy, custom_pos, data_point}]
        self.dragging_annotation = None  # 當前拖動的標籤
        self.drag_start_pos = None  # 拖動起始位置（用於計算偏移）
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 創建 Matplotlib 圖形（參考 universal_chart_widget 的設定）
        # 使用較小的固定尺寸作為基準，讓 canvas 自動縮放填充
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # ✅ 設置 SizePolicy 讓圖表能夠自適應視窗大小（參考 universal_chart_widget）
        from PyQt5.QtWidgets import QSizePolicy
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.ax = None
        
        # 初始化 UI
        self._init_ui()
        
        # 連接滑鼠事件
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        
        print("[CORNER_SCATTER] 元件初始化完成")
    
    def resizeEvent(self, event):
        """
        視窗縮放事件處理
        
        當視窗大小改變時，重新調整 matplotlib 佈局以避免白色區域
        參考 universal_chart_widget 的實現
        """
        super().resizeEvent(event)
        
        # 如果有圖表數據，重新調整佈局
        if self.ax is not None:
            try:
                self.figure.tight_layout()
                self.canvas.draw_idle()
            except Exception as e:
                # 忽略佈局調整錯誤（可能在極小視窗時發生）
                pass
        
    def _init_ui(self):
        """初始化 UI 組件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除外邊距
        layout.setSpacing(5)  # 減少組件間距為 5 像素
        
        # ✅ 簡化控制面板 - 隱藏不必要的元件
        control_layout = QHBoxLayout()
        
        # ❌ 隱藏彎道類型選擇（每個模組已經是獨立的彎道類型）
        self.corner_combo = QComboBox()
        self.corner_combo.addItem(tr("low_speed_corner", "低速彎"), "low_speed")
        self.corner_combo.addItem(tr("mid_speed_corner", "中速彎"), "mid_speed")
        self.corner_combo.addItem(tr("high_speed_corner", "高速彎"), "high_speed")
        self.corner_combo.currentIndexChanged.connect(self._on_corner_switch)
        self.corner_combo.hide()  # ✅ 隱藏 ComboBox
        
        # ❌ 隱藏匯出按鈕（功能未實現）
        self.export_btn = QPushButton(tr("export_chart", "匯出圖表"))
        self.export_btn.clicked.connect(self._export_chart)
        self.export_btn.hide()  # ✅ 隱藏匯出按鈕
        
        # ❌ 隱藏刷新按鈕（數據會自動載入）
        self.refresh_btn = QPushButton(tr("refresh_chart", "刷新圖表"))
        self.refresh_btn.clicked.connect(self._refresh_chart)
        self.refresh_btn.hide()  # ✅ 隱藏刷新按鈕
        
        # 說明標籤
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-size: 10pt;")
        
        # ✅ 只顯示說明標籤
        control_layout.addStretch()
        control_layout.addWidget(self.info_label)
        control_layout.addStretch()
        
        # 添加到主佈局
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
        
        # 設置 ComboBox 為正確的初始值（根據 self.current_corner_type）
        corner_index_map = {
            "low_speed": 0,
            "mid_speed": 1,
            "high_speed": 2
        }
        initial_index = corner_index_map.get(self.current_corner_type, 0)
        self.corner_combo.setCurrentIndex(initial_index)
        print(f"[CORNER_SCATTER] ComboBox 已設置為初始彎道類型: {self.current_corner_type} (index={initial_index})")
        
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據並重繪圖表
        
        Args:
            data: 包含 fastest_lap_analysis 和 selected_corners 的數據字典
        """
        try:
            if not data or not isinstance(data, dict):
                print("[WARNING] [CORNER_SCATTER] 無效的數據格式")
                return
            
            self.current_data = data
            
            # 更新說明標籤
            self._update_info_label()
            
            # 繪製圖表
            self.draw_scatter_chart()
            
            print(f"[CORNER_SCATTER] 數據更新完成，彎道類型: {self.current_corner_type}")
            
        except Exception as e:
            print(f"[ERROR] [CORNER_SCATTER] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_scatter_chart(self):
        """
        繪製散點圖
        
        X 軸：進彎速度（entry_50m_speed）
        Y 軸：出彎速度（exit_50m_speed）
        顏色：彎中心速度（apex_speed）
        """
        try:
            if not self.current_data:
                print("[WARNING] [CORNER_SCATTER] 無數據可繪製")
                return
            
            # 清除所有固定標籤（重繪圖表時）
            self._clear_all_pinned_annotations()
            
            # 清空舊圖表
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 獲取選中的彎道資訊
            selected_corners = self.current_data.get("selected_corners", {})
            corner_info = selected_corners.get(self.current_corner_type)
            
            if not corner_info:
                self._show_no_data_message()
                return
            
            # 獲取最速圈分析數據
            fastest_lap_analysis = self.current_data.get("fastest_lap_analysis", {})
            drivers_data = fastest_lap_analysis.get("drivers", [])
            
            if not drivers_data:
                self._show_no_data_message()
                return
            
            # 提取散點數據
            x_data = []  # 進彎速度
            y_data = []  # 出彎速度
            colors = []  # 彎中心速度
            labels = []  # 車手代碼
            
            # 清空車手數據映射
            self.driver_data_map = {}
            
            # 彎道類型對應的鍵名
            corner_key = f"{self.current_corner_type}_corner_{corner_info['corner_number']}"
            
            for driver_data in drivers_data:
                driver = driver_data.get("driver", "")
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
            
            # 繪製散點圖
            self.scatter_points = self.ax.scatter(
                x_data, y_data,
                c=colors,
                cmap='RdYlGn',  # 紅黃綠色階（紅=慢，綠=快）
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
            
            # ✅ 進階智能標籤避讓算法 - 力導向佈局 + 碰撞檢測
            import math
            
            # 計算數據中心點和範圍
            center_x = sum(x_data) / len(x_data)
            center_y = sum(y_data) / len(y_data)
            x_min, x_max = min(x_data), max(x_data)
            y_min, y_max = min(y_data), max(y_data)
            x_range = x_max - x_min
            y_range = y_max - y_min
            
            # 初始化標籤位置（基於角度）
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
            
            # ✅ 改進的力導向演算法 - 平衡避讓與距離
            max_iterations = 50
            repulsion_strength = 2.5  # 降低排斥力強度（避免推太遠）
            attraction_strength = 0.3  # 新增：吸引力強度（拉回數據點）
            label_size_x = 3.5  # 減小標籤寬度估算（允許更近）
            label_size_y = 2.0  # 減小標籤高度估算
            point_radius = 0.8  # 數據點半徑（避免與圓圈重疊）
            
            for iteration in range(max_iterations):
                moved = False
                
                for i in range(len(label_positions)):
                    lbl_i = label_positions[i]
                    # 計算標籤在數據座標中的位置
                    lbl_x_i = lbl_i['x'] + (lbl_i['x_offset'] / 72.0) * x_range
                    lbl_y_i = lbl_i['y'] + (lbl_i['y_offset'] / 72.0) * y_range
                    
                    total_force_x = 0
                    total_force_y = 0
                    
                    # 1️⃣ 與其他標籤的排斥力
                    for j in range(len(label_positions)):
                        if i == j:
                            continue
                        
                        lbl_j = label_positions[j]
                        lbl_x_j = lbl_j['x'] + (lbl_j['x_offset'] / 72.0) * x_range
                        lbl_y_j = lbl_j['y'] + (lbl_j['y_offset'] / 72.0) * y_range
                        
                        dx = lbl_x_i - lbl_x_j
                        dy = lbl_y_i - lbl_y_j
                        dist = math.sqrt(dx**2 + dy**2)
                        
                        # 最小安全距離
                        min_distance = math.sqrt(label_size_x**2 + label_size_y**2)
                        
                        # 排斥力（距離越近，力越大）
                        if dist < min_distance and dist > 0.1:
                            repulsion = repulsion_strength * (min_distance - dist) / dist
                            total_force_x += repulsion * dx
                            total_force_y += repulsion * dy
                            moved = True
                    
                    # 2️⃣ 與數據點的吸引力（拉回原點）
                    # 計算標籤與數據點的距離
                    dist_to_point = math.sqrt(
                        ((lbl_x_i - lbl_i['x'])**2 + (lbl_y_i - lbl_i['y'])**2)
                    )
                    
                    # 如果標籤離數據點太遠，施加吸引力
                    ideal_distance = 2.5  # 理想距離（數據座標單位）
                    if dist_to_point > ideal_distance:
                        attraction = attraction_strength * (dist_to_point - ideal_distance)
                        dx_to_point = lbl_i['x'] - lbl_x_i
                        dy_to_point = lbl_i['y'] - lbl_y_i
                        if dist_to_point > 0.1:
                            total_force_x += attraction * dx_to_point / dist_to_point
                            total_force_y += attraction * dy_to_point / dist_to_point
                    
                    # 3️⃣ 避免與數據點圓圈重疊
                    # 如果標籤太靠近數據點，施加排斥力
                    if dist_to_point < point_radius:
                        repulsion = 2.0 * (point_radius - dist_to_point)
                        dx_from_point = lbl_x_i - lbl_i['x']
                        dy_from_point = lbl_y_i - lbl_i['y']
                        if dist_to_point > 0.01:
                            total_force_x += repulsion * dx_from_point / dist_to_point
                            total_force_y += repulsion * dy_from_point / dist_to_point
                            moved = True
                    
                    # 應用力調整偏移
                    if abs(total_force_x) > 0.01 or abs(total_force_y) > 0.01:
                        # 轉換回 points 單位（使用更小的步長避免震盪）
                        lbl_i['x_offset'] += (total_force_x / x_range) * 72.0 * 0.3
                        lbl_i['y_offset'] += (total_force_y / y_range) * 72.0 * 0.3
                        
                        # 限制偏移範圍（更嚴格的限制）
                        max_offset = 28  # 降低最大偏移距離
                        offset_mag = math.sqrt(lbl_i['x_offset']**2 + lbl_i['y_offset']**2)
                        if offset_mag > max_offset:
                            scale = max_offset / offset_mag
                            lbl_i['x_offset'] *= scale
                            lbl_i['y_offset'] *= scale
                
                # 如果沒有移動，提前結束
                if not moved:
                    break
            
            # 繪製標籤
            for lbl in label_positions:
                x_offset = lbl['x_offset']
                y_offset = lbl['y_offset']
                
                # 根據偏移方向決定對齊方式
                ha = 'left' if x_offset > 0 else 'right'
                va = 'bottom' if y_offset > 0 else 'top'
                
                # 特殊處理：避免與 colorbar 重疊（右側區域）
                if lbl['x'] > center_x + (x_max - center_x) * 0.7:
                    x_offset = -abs(x_offset)
                    ha = 'right'
                
                self.ax.annotate(
                    lbl['label'],
                    (lbl['x'], lbl['y']),
                    xytext=(x_offset, y_offset),
                    textcoords='offset points',
                    fontsize=7.5,  # 略微減小字體
                    weight='bold',
                    color='#333',
                    ha=ha,
                    va=va,
                    alpha=0.85,
                    clip_on=True
                )
            
            # ✅ 設定坐標軸範圍，增加邊距
            x_margin = x_range * 0.1
            y_margin = y_range * 0.1
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
            
            # 設定標籤
            corner_number = corner_info['corner_number']
            avg_speed = corner_info['avg_apex_speed']
            
            self.ax.set_xlabel(
                tr("entry_speed_50m", "進彎速度 (-50m) [km/h]"),
                fontsize=12,
                weight='bold'
            )
            self.ax.set_ylabel(
                tr("exit_speed_50m", "出彎速度 (+50m) [km/h]"),
                fontsize=12,
                weight='bold'
            )
            
            # ❌ 隱藏圖表標題（窗口標題已足夠）
            # corner_number = corner_info['corner_number']
            # avg_speed = corner_info['avg_apex_speed']
            # title = f"T{corner_number} 性能分布 (平均速度: {avg_speed:.1f} km/h)"
            # self.ax.set_title(title, fontsize=14, weight='bold', pad=25)
            
            # 添加網格
            self.ax.grid(True, alpha=0.3, linestyle='--')
            
            # 調整佈局（使用 matplotlib 自動計算，參考 straight_line_speed_widget）
            self.figure.tight_layout()
            
            # 刷新畫布
            self.canvas.draw()
            
            print(f"[CORNER_SCATTER] 散點圖繪製完成: {len(x_data)} 個數據點")
            
        except Exception as e:
            print(f"[ERROR] [CORNER_SCATTER] 繪製散點圖失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_no_data_message(self):
        """顯示無數據訊息"""
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
            print(f"[CORNER_SCATTER] 切換彎道類型: {corner_type}")
    
    def _refresh_chart(self):
        """刷新圖表"""
        print("[CORNER_SCATTER] 刷新圖表")
        self.draw_scatter_chart()
    
    def _on_mouse_move(self, event):
        """
        滑鼠移動事件處理（整合 hover 和 drag 功能）
        
        1. 如果正在拖動標籤，移動標籤
        2. 否則，處理懸停提示
        """
        # 優先處理拖動
        if self.dragging_annotation:
            if event.inaxes == self.ax and event.xdata and event.ydata and self.drag_start_pos:
                # 計算滑鼠移動的偏移量
                dx = event.xdata - self.drag_start_pos[0]
                dy = event.ydata - self.drag_start_pos[1]
                
                # 獲取當前的 xytext（annotation 文字框的位置）
                annotation = self.dragging_annotation['annotation']
                current_xytext = annotation.xyann  # 取得當前的 annotation 位置
                
                # 轉換偏移量為螢幕像素
                # 我們需要將數據座標的偏移轉換為螢幕像素偏移
                transform = self.ax.transData
                # 取得起始點和結束點的螢幕座標
                start_display = transform.transform([self.drag_start_pos])
                end_display = transform.transform([(event.xdata, event.ydata)])
                
                # 計算螢幕像素偏移
                dx_display = end_display[0][0] - start_display[0][0]
                dy_display = end_display[0][1] - start_display[0][1]
                
                # 更新 xytext 位置
                new_xytext = (current_xytext[0] + dx_display, current_xytext[1] + dy_display)
                annotation.xyann = new_xytext
                
                # 儲存新位置
                self.dragging_annotation['custom_pos'] = new_xytext
                
                # 更新拖動起始位置
                self.drag_start_pos = (event.xdata, event.ydata)
                
                # 重繪畫布
                self.canvas.draw_idle()
            return
        
        # 處理懸停提示
        if event.inaxes != self.ax or self.scatter_points is None:
            # 如果不在圖表區域或沒有散點，移除懸停標註
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.canvas.draw_idle()
            return
        
        # 檢查是否懸停在散點上
        cont, ind = self.scatter_points.contains(event)
        
        if cont:
            # 獲取第一個懸停的點
            index = ind['ind'][0]
            
            # 從映射中獲取車手數據
            if index in self.driver_data_map:
                driver_info = self.driver_data_map[index]
                
                # 獲取散點的實際座標
                x_data = self.scatter_points.get_offsets()[index, 0]
                y_data = self.scatter_points.get_offsets()[index, 1]
                
                # 計算圖表中心點（用於智能定位）
                all_offsets = self.scatter_points.get_offsets()
                center_x = all_offsets[:, 0].mean()
                center_y = all_offsets[:, 1].mean()
                
                # 根據散點相對於中心的位置，智能調整提示框偏移方向
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
                
                # 創建或更新懸停標註
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
                
                # 格式化顯示文字
                text = (
                    f"{driver_info['driver']}\n"
                    f"────────────\n"
                    f"{tr('entry_label', '進彎')}: {driver_info['entry_speed']:.1f} km/h\n"
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
        1. 如果點擊已固定的標籤，開始拖動
        2. 如果點擊散點，固定該散點的標籤
        
        右鍵點擊：
        1. 如果點擊固定標籤，移除該標籤
        2. 如果點擊空白處，清除所有固定標籤
        """
        if event.inaxes != self.ax or self.scatter_points is None:
            return
        
        # 右鍵：移除固定標籤或清除全部
        if event.button == 3:  # 右鍵
            # 先檢查是否點擊了固定標籤
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
                # 點擊空白處，清除所有固定標籤
                self._clear_all_pinned_annotations()
            return
        
        # 左鍵：檢查是否點擊已固定的標籤或散點
        if event.button == 1:  # 左鍵
            # 先檢查是否點擊已固定的標籤框（用於拖動）
            for pinned in self.pinned_annotations:
                annotation = pinned['annotation']
                # matplotlib annotation 的 contains 方法
                contains, _ = annotation.contains(event)
                if contains:
                    # 開始拖動該標籤
                    self.dragging_annotation = pinned
                    # 記錄拖動起始位置（滑鼠在數據座標系中的位置）
                    self.drag_start_pos = (event.xdata, event.ydata)
                    print(f"[CORNER_SCATTER] 開始拖動標籤: {pinned['driver']}")
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
        
        停止拖動標籤
        """
        if self.dragging_annotation:
            print(f"[CORNER_SCATTER] 停止拖動標籤: {self.dragging_annotation['driver']}")
            self.dragging_annotation = None
            self.drag_start_pos = None
    
    def _pin_annotation(self, index: int):
        """
        固定指定索引的散點標籤
        
        Args:
            index: 散點索引
        """
        driver_info = self.driver_data_map[index]
        
        # 檢查是否已固定該車手
        for pinned in self.pinned_annotations:
            if pinned['driver'] == driver_info['driver']:
                print(f"[CORNER_SCATTER] 車手 {driver_info['driver']} 的標籤已固定")
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
            f"{tr('entry_label', '進彎')}: {driver_info['entry_speed']:.1f} km/h\n"
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
            'data_point': (x_data, y_data),  # 儲存原始數據點位置
            'custom_pos': None  # 自訂位置（拖動後使用）
        })
        
        # 重繪畫布
        self.canvas.draw_idle()
        
        print(f"[CORNER_SCATTER] 已固定標籤: {driver_info['driver']}")
    
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
            print(f"[CORNER_SCATTER] 已移除標籤: {pinned['driver']}")
    
    def _clear_all_pinned_annotations(self):
        """清除所有固定標籤"""
        if not self.pinned_annotations:
            print("[CORNER_SCATTER] 沒有固定標籤需要清除")
            return
        
        for pinned in self.pinned_annotations:
            pinned['annotation'].remove()
        self.pinned_annotations.clear()
        self.canvas.draw_idle()
        print("[CORNER_SCATTER] 已清除所有固定標籤")
    
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
                print(f"[CORNER_SCATTER] 圖表已匯出: {filename}")
                
        except Exception as e:
            print(f"[ERROR] [CORNER_SCATTER] 匯出圖表失敗: {e}")
            QMessageBox.critical(
                self,
                tr("error", "錯誤"),
                tr("export_failed", f"匯出失敗: {str(e)}")
            )
