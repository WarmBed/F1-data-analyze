#!/usr/bin/env python3
"""
賽道高程圖表元件 - 使用 FastF1 Z 軸數據
========================================

使用 FastF1 遙測數據中的 Z 軸（高度）繪製賽道高程剖面圖

Author: F1T Team
Date: 2025-11-09
"""

from typing import Optional, List, Dict, Any
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class ElevationChartWidget(QWidget):
    """
    賽道高程圖表元件
    
    使用 FastF1 的 X, Y, Z 座標數據繪製高程剖面
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.circuit_name = "Circuit"
        self.elevation_data: List[Dict[str, Any]] = []
        self.corner_data: List[Dict[str, Any]] = []
        
        # 初始化 Matplotlib 圖表
        self.figure = Figure(figsize=(12, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        self._init_empty_chart()
    
    def _init_empty_chart(self):
        """初始化空白圖表"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "等待數據載入...",
                    ha='center', va='center',
                    transform=self.ax.transAxes,
                    fontsize=14, color='gray')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def set_circuit_name(self, name: str):
        """設置賽道名稱"""
        self.circuit_name = str(name)
    
    def plot_elevation(self, 
                      track_outline: List[Dict[str, Any]], 
                      official_corners: List[Dict[str, Any]] = None):
        """
        繪製高程剖面圖
        
        Args:
            track_outline: 賽道輪廓數據，包含 distance_m 和 elevation (Z)
            official_corners: 官方彎道數據（可選）
        """
        if not track_outline:
            print("[ELEVATION_CHART] ⚠️ 無高程數據")
            self._init_empty_chart()
            return
        
        self.elevation_data = track_outline
        self.corner_data = official_corners or []
        
        # 提取距離和高度數據
        distances = []
        elevations = []
        
        for point in track_outline:
            dist = point.get('distance_m', 0.0)
            elev = point.get('elevation') or point.get('z', 0.0)
            
            if elev != 0.0:  # 過濾無效數據
                distances.append(dist / 1000.0)  # 轉換為公里
                # ✅ 移除重複除以 10：數據已在 data_loader 中處理
                elevations.append(elev)
        
        if not distances or not elevations:
            print("[ELEVATION_CHART] ⚠️ 無有效高程數據")
            self._init_empty_chart()
            return
        
        # 轉換為相對高度（以最低點為 0）
        min_elevation = min(elevations)
        elevations_relative = [e - min_elevation for e in elevations]
        max_relative = max(elevations_relative)
        
        print(f"[ELEVATION_CHART] 繪製高程: {len(distances)} 個數據點")
        print(f"[ELEVATION_CHART]   距離範圍: {min(distances):.2f} ~ {max(distances):.2f} km")
        print(f"[ELEVATION_CHART]   絕對高度: {min_elevation:.2f} ~ {max(elevations):.2f} m")
        print(f"[ELEVATION_CHART]   相對高度: 0.00 ~ {max_relative:.2f} m (以最低點為基準)")
        print(f"[ELEVATION_CHART]   ✅ FastF1 Z 軸已在 data_loader 中除以 10")
        
        # 清空並重新繪製
        self.ax.clear()
        
        # === 繪製高程剖面（面積填充） - 使用相對高度 ===
        self.ax.fill_between(distances, elevations_relative, 
                            color='#3498db', alpha=0.4, label='相對高程剖面')
        self.ax.plot(distances, elevations_relative, 
                    color='#2980b9', linewidth=2, label='高度變化')
        
        # === 標註官方彎道位置 ===
        if self.corner_data:
            self._mark_corners(distances, elevations, elevations_relative, min_elevation)
        
        # === 設置圖表樣式 ===
        self.ax.set_xlabel('賽道距離 (km)', fontsize=11, fontweight='bold')
        self.ax.set_ylabel('相對高度 (m)', fontsize=11, fontweight='bold')
        self.ax.set_title(
            f'{self.circuit_name} - 高程剖面圖（相對高度，基於 FastF1 Z 軸）\n' + 
            f'最低點: {min_elevation:.1f}m | 最高點: {max(elevations):.1f}m | 高度差: {max_relative:.1f}m', 
            fontsize=12, fontweight='bold', pad=15
        )
        
        # 網格
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # 圖例
        self.ax.legend(loc='upper right', fontsize=9)
        
        # 緊湊佈局
        self.figure.tight_layout()
        
        # 更新畫布
        self.canvas.draw()
        
        print(f"[ELEVATION_CHART] ✅ 高程圖繪製完成")
    
    def _mark_corners(self, distances: List[float], elevations: List[float], 
                     elevations_relative: List[float], min_elevation: float):
        """
        在高程圖上標註彎道位置（使用相對高度）
        
        Args:
            distances: 距離數組（公里）
            elevations: 絕對高度數組（公尺）
            elevations_relative: 相對高度數組（公尺，以最低點為 0）
            min_elevation: 最低點的絕對高度
        """
        # 建立距離到高度的映射（用於查找彎道對應的高度）
        dist_to_elev = {}
        for d, e in zip(distances, elevations_relative):
            dist_to_elev[round(d, 3)] = e
        
        # 提取全部距離用於線性插值
        distances_m = [d * 1000 for d in distances]  # 轉回公尺
        
        corner_count = 0
        for corner in self.corner_data:
            corner_num = corner.get('number', 0)
            corner_dist_m = corner.get('distance', 0.0)
            
            if corner_dist_m == 0.0:
                continue
            
            # 轉換為公里
            corner_dist_km = corner_dist_m / 1000.0
            
            # 使用線性插值找到對應的相對高度
            if corner_dist_m < distances_m[0] or corner_dist_m > distances_m[-1]:
                continue  # 彎道超出距離範圍
            
            corner_elev_relative = np.interp(corner_dist_m, distances_m, elevations_relative)
            
            # 在圖上標記彎道
            self.ax.plot(corner_dist_km, corner_elev_relative, 
                        'ro', markersize=6, zorder=5)
            
            # 標註彎道編號（稍微偏移避免重疊）
            self.ax.annotate(f'T{corner_num}', 
                           xy=(corner_dist_km, corner_elev_relative),
                           xytext=(0, 10),  # 向上偏移 10 點
                           textcoords='offset points',
                           fontsize=8,
                           fontweight='bold',
                           color='darkred',
                           ha='center',
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor='white', 
                                   edgecolor='darkred',
                                   alpha=0.8))
            
            corner_count += 1
        
        if corner_count > 0:
            print(f"[ELEVATION_CHART] 已標註 {corner_count} 個彎道位置")
    
    def clear_chart(self):
        """清空圖表"""
        self.elevation_data = []
        self.corner_data = []
        self._init_empty_chart()


__all__ = ['ElevationChartWidget']
