"""
TrackPlotWidget - 賽道繪圖組件
==============================

基於 PyQtGraph 的高效能賽道繪圖組件，提供互動式的賽道軌跡視覺化。

功能特色：
1. 高效能的賽道軌跡繪製
2. 互動式縮放、平移功能
3. 原點標註 (紅色圓圈)
4. 滑鼠點擊位置標記
5. 自動視圖範圍調整
6. 圖片匯出功能

Author: F1T Team
Date: 2025-08-28  
Version: 1.0.0
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox

# 檢查 PyQtGraph 是否可用
try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget, mkPen, mkBrush
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    # 如果 PyQtGraph 不可用，使用 matplotlib 作為後備
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        MATPLOTLIB_AVAILABLE = True
    except ImportError:
        MATPLOTLIB_AVAILABLE = False


class TrackPlotWidget(QWidget):
    """
    賽道繪圖組件
    
    提供賽道軌跡的視覺化展示，支援互動式操作。
    """
    
    # 信號定義
    position_clicked = pyqtSignal(dict)     # 位置點被點擊
    view_changed = pyqtSignal(dict)         # 視圖範圍改變
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據相關
        self._track_data = None
        self._position_records = []
        
        # 繪圖相關
        self._plot_widget = None
        self._track_line = None
        self._origin_marker = None
        self._selected_marker = None
        
        # UI 控制
        self._show_origin = True
        self._show_grid = True
        self._auto_range = True
        self._use_smooth_curve = True  # 新增：是否使用平滑曲線
        
        # 初始化 UI
        self._init_ui()
        
    def _init_ui(self) -> None:
        """初始化使用者介面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        layout.setSpacing(0)  # 移除間距
        
        # 直接創建繪圖區域，不添加控制面板
        if PYQTGRAPH_AVAILABLE:
            self._init_pyqtgraph_plot()
        elif MATPLOTLIB_AVAILABLE:
            self._init_matplotlib_plot()
        else:
            # 如果都不可用，顯示錯誤訊息
            error_label = QLabel("錯誤：需要安裝 PyQtGraph 或 Matplotlib 才能顯示賽道圖")
            error_label.setStyleSheet("color: red; font-weight: bold; padding: 20px;")
            layout.addWidget(error_label)
            return
            
        layout.addWidget(self._plot_widget)
        
    def _create_control_panel(self) -> QWidget:
        """創建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # 顯示選項
        self._origin_checkbox = QCheckBox("顯示原點")
        self._origin_checkbox.setChecked(self._show_origin)
        self._origin_checkbox.toggled.connect(self._on_origin_toggle)
        layout.addWidget(self._origin_checkbox)
        
        self._grid_checkbox = QCheckBox("顯示網格") 
        self._grid_checkbox.setChecked(self._show_grid)
        self._grid_checkbox.toggled.connect(self._on_grid_toggle)
        layout.addWidget(self._grid_checkbox)
        
        self._auto_range_checkbox = QCheckBox("自動範圍")
        self._auto_range_checkbox.setChecked(self._auto_range)
        self._auto_range_checkbox.toggled.connect(self._on_auto_range_toggle)
        layout.addWidget(self._auto_range_checkbox)
        
        # 操作按鈕
        reset_button = QPushButton("重置視圖")
        reset_button.clicked.connect(self._reset_view)
        layout.addWidget(reset_button)
        
        export_button = QPushButton("匯出圖片")
        export_button.clicked.connect(self._export_plot)
        layout.addWidget(export_button)
        
        layout.addStretch()
        return panel
        
    def _init_pyqtgraph_plot(self) -> None:
        """初始化 PyQtGraph 繪圖"""
        # 創建繪圖 widget
        self._plot_widget = PlotWidget()
        
        # 設定淺灰色背景，接近第一張圖片
        self._plot_widget.setBackground('#E8E8E8')  # 淺灰色背景
        
        # 隱藏坐標軸標籤和刻度
        self._plot_widget.getAxis('left').setStyle(showValues=False)
        self._plot_widget.getAxis('bottom').setStyle(showValues=False)
        self._plot_widget.getAxis('left').setLabel('')
        self._plot_widget.getAxis('bottom').setLabel('')
        self._plot_widget.setTitle('')  # 移除標題
        
        # 隱藏坐標軸線
        self._plot_widget.getAxis('left').setPen(None)
        self._plot_widget.getAxis('bottom').setPen(None)
        self._plot_widget.getAxis('top').setPen(None)
        self._plot_widget.getAxis('right').setPen(None)
        
        # 關閉網格
        self._plot_widget.showGrid(x=False, y=False)
        
        # 設定等比例
        self._plot_widget.setAspectLocked(True)
        
        # 連接滑鼠事件
        self._plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
    def _init_matplotlib_plot(self) -> None:
        """初始化 Matplotlib 繪圖 (後備方案)"""
        # 創建 matplotlib figure
        self._figure = Figure(figsize=(10, 8))
        self._plot_widget = FigureCanvas(self._figure)
        self._axes = self._figure.add_subplot(111)
        
        # 設定基本屬性
        self._axes.set_xlabel('X 座標 (m)')
        self._axes.set_ylabel('Y 座標 (m)')
        self._axes.set_title('F1 賽道軌跡')
        self._axes.grid(self._show_grid)
        self._axes.set_aspect('equal')
        
    def set_track_data(self, track_data: Dict[str, Any]) -> None:
        """
        設定賽道數據
        
        Args:
            track_data: 賽道數據字典
        """
        try:
            print(f"🗺️ [TRACK_PLOT] 接收到賽道數據: {type(track_data)}")
            
            self._track_data = track_data
            self._position_records = track_data.get('detailed_position_records', [])
            
            print(f"🗺️ [TRACK_PLOT] 位置記錄數量: {len(self._position_records)}")
            
            if not self._position_records:
                print("⚠️ [TRACK_PLOT] 沒有位置記錄，清除繪圖")
                self.clear_plot()
                return
                
            # 顯示前幾個點的樣本數據
            if self._position_records:
                sample_points = self._position_records[:3]
                print(f"🗺️ [TRACK_PLOT] 樣本數據: {sample_points}")
                
            # 繪製賽道
            self._draw_track()
            
            # 調整視圖
            if self._auto_range:
                self._fit_view()
                
        except Exception as e:
            print(f"設定賽道數據時發生錯誤: {str(e)}")
            
    def _draw_track(self) -> None:
        """繪製賽道軌跡"""
        if not self._position_records:
            print("⚠️ [TRACK_PLOT] 沒有位置記錄，無法繪製")
            return
            
        # 提取座標 (修復鍵名問題)
        x_coords = [record.get('position_x', record.get('x', 0)) for record in self._position_records]
        y_coords = [record.get('position_y', record.get('y', 0)) for record in self._position_records]
        
        print(f"🗺️ [TRACK_PLOT] 開始繪製賽道，座標數量: {len(x_coords)}")
        print(f"🗺️ [TRACK_PLOT] X 座標範圍: {min(x_coords):.1f} ~ {max(x_coords):.1f}")
        print(f"🗺️ [TRACK_PLOT] Y 座標範圍: {min(y_coords):.1f} ~ {max(y_coords):.1f}")
        
        if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
            print("🗺️ [TRACK_PLOT] 使用 PyQtGraph 繪製")
            self._draw_track_pyqtgraph(x_coords, y_coords)
        elif MATPLOTLIB_AVAILABLE:
            print("🗺️ [TRACK_PLOT] 使用 Matplotlib 繪製")
            self._draw_track_matplotlib(x_coords, y_coords)
            
    def _draw_track_pyqtgraph(self, x_coords: List[float], y_coords: List[float]) -> None:
        """使用 PyQtGraph 繪製賽道 - 高質量渲染"""
        print(f"🗺️ [TRACK_PLOT] PyQtGraph 繪製開始，點數: {len(x_coords)}")
        
        # 清除現有的繪圖
        self._plot_widget.clear()
        
        # 啟用高質量渲染選項 (使用正確的抗鋸齒方法)
        self._plot_widget.setAntialiasing(True)
        
        # 選擇是否使用平滑化
        if self._use_smooth_curve:
            display_x, display_y = self._smooth_track_curve(x_coords, y_coords)
            print(f"🗺️ [TRACK_PLOT] 使用平滑化數據繪製")
        else:
            display_x, display_y = x_coords, y_coords
            print(f"🗺️ [TRACK_PLOT] 使用原始數據繪製")
        
        # 繪製賽道線（優化視覺效果 - 圓滑線條但保持特徵）
        pen = mkPen(
            color='#4A69E2',      # 藍色
            width=3,              # 稍微加粗線條
            style=Qt.SolidLine,   # 實線
            capStyle=Qt.RoundCap, # 圓形端點
            joinStyle=Qt.RoundJoin # 圓形接合點（重要！讓轉角更圓滑）
        )
        
        self._track_line = self._plot_widget.plot(
            display_x, display_y, 
            pen=pen, 
            name='賽道軌跡',
            antialias=True,       # 抗鋸齒（讓線條邊緣更平滑）
            downsample=1,         # 不降採樣
            connect='finite',     # 只連接有效點
            skipFiniteCheck=False # 檢查有限值
        )
        
        print(f"🗺️ [TRACK_PLOT] 賽道線繪製完成（點數: {len(display_x)}）")
        
        # 繪製起點標記（紅色圓圈）- 使用原始座標
        if self._show_origin and len(x_coords) > 0:
            origin_pen = mkPen(color='red', width=3)
            origin_brush = mkBrush(color='red')
            self._origin_marker = self._plot_widget.plot(
                [x_coords[0]], [y_coords[0]], 
                pen=origin_pen,
                symbol='o', 
                symbolSize=12,
                symbolBrush=origin_brush,
                name='起點'
            )
            print(f"🗺️ [TRACK_PLOT] 起點標記繪製完成: ({x_coords[0]:.1f}, {y_coords[0]:.1f})")
    
    def _gaussian_smooth(self, x_coords: List[float], y_coords: List[float], sigma: float = 1.5) -> tuple:
        """使用高斯濾波進行賽道平滑化"""
        try:
            if len(x_coords) < 3:
                return x_coords, y_coords
            
            # 使用 SciPy 的高斯濾波（如果可用）
            try:
                from scipy.ndimage import gaussian_filter1d
                import numpy as np
                
                # 轉換為 numpy 陣列
                x_array = np.array(x_coords)
                y_array = np.array(y_coords)
                
                # 應用高斯濾波
                smoothed_x = gaussian_filter1d(x_array, sigma=sigma, mode='wrap')  # wrap 模式適合環形賽道
                smoothed_y = gaussian_filter1d(y_array, sigma=sigma, mode='wrap')
                
                # 轉換回列表
                smoothed_x = smoothed_x.tolist()
                smoothed_y = smoothed_y.tolist()
                
                print(f"🗺️ [TRACK_PLOT] SciPy 高斯濾波完成: sigma={sigma}, 點數: {len(x_coords)}")
                return smoothed_x, smoothed_y
                
            except ImportError:
                print("⚠️ [TRACK_PLOT] SciPy 不可用，使用內建高斯濾波")
                # 回退到內建實現
                smoothed_x = self._apply_gaussian_filter(x_coords, sigma)
                smoothed_y = self._apply_gaussian_filter(y_coords, sigma)
                
                print(f"🗺️ [TRACK_PLOT] 內建高斯濾波完成: sigma={sigma}, 點數: {len(x_coords)}")
                return smoothed_x, smoothed_y
            
        except Exception as e:
            print(f"⚠️ [TRACK_PLOT] 高斯濾波失敗: {e}，使用原始數據")
            return x_coords, y_coords
    
    def _apply_gaussian_filter(self, data: List[float], sigma: float) -> List[float]:
        """應用一維高斯濾波"""
        import math
        
        # 計算高斯核大小（通常是 sigma 的 6 倍）
        kernel_size = int(6 * sigma) + 1
        if kernel_size % 2 == 0:
            kernel_size += 1  # 確保是奇數
        
        # 生成高斯核
        kernel = []
        center = kernel_size // 2
        sum_weights = 0
        
        for i in range(kernel_size):
            x = i - center
            weight = math.exp(-(x * x) / (2 * sigma * sigma))
            kernel.append(weight)
            sum_weights += weight
        
        # 正規化核
        kernel = [w / sum_weights for w in kernel]
        
        # 應用濾波（處理邊界）
        filtered = []
        data_len = len(data)
        
        for i in range(data_len):
            weighted_sum = 0
            weight_sum = 0
            
            for j in range(kernel_size):
                data_idx = i - center + j
                
                # 處理邊界情況 - 環形賽道，連接首尾
                if data_idx < 0:
                    data_idx = data_len + data_idx
                elif data_idx >= data_len:
                    data_idx = data_idx - data_len
                
                weighted_sum += data[data_idx] * kernel[j]
                weight_sum += kernel[j]
            
            filtered.append(weighted_sum / weight_sum if weight_sum > 0 else data[i])
        
        return filtered
    
    def _smooth_track_curve(self, x_coords: List[float], y_coords: List[float]) -> tuple:
        """卡特莫-羅姆樣條平滑化 - 10倍插值密度，保持賽道特徵並增強曲線流暢度"""
        try:
            if len(x_coords) < 4:  # 卡特莫-羅姆樣條至少需要4個點
                return self._linear_interpolation_fallback(x_coords, y_coords, 10)
            
            # 使用卡特莫-羅姆樣條進行高品質插值
            smooth_x, smooth_y = self._catmull_rom_spline(x_coords, y_coords, density=10)
            
            print(f"🗺️ [TRACK_PLOT] 卡特莫-羅姆樣條完成: {len(x_coords)} → {len(smooth_x)} 個點（10倍密度）")
            return smooth_x, smooth_y
            
        except Exception as e:
            print(f"⚠️ [TRACK_PLOT] 卡特莫-羅姆樣條失敗: {e}，使用線性插值後備方案")
            return self._linear_interpolation_fallback(x_coords, y_coords, 10)
    
    def _catmull_rom_spline(self, x_coords: List[float], y_coords: List[float], density: int = 10) -> tuple:
        """卡特莫-羅姆樣條插值實現"""
        def catmull_rom_segment(p0, p1, p2, p3, num_points):
            """計算兩點間的卡特莫-羅姆樣條段"""
            points = []
            for i in range(num_points):
                t = i / (num_points - 1) if num_points > 1 else 0
                t2 = t * t
                t3 = t2 * t
                
                # 卡特莫-羅姆樣條公式
                x = 0.5 * ((2 * p1[0]) +
                          (-p0[0] + p2[0]) * t +
                          (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                          (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
                          
                y = 0.5 * ((2 * p1[1]) +
                          (-p0[1] + p2[1]) * t +
                          (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                          (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
                          
                points.append((x, y))
            return points
            
        points = list(zip(x_coords, y_coords))
        smooth_x, smooth_y = [], []
        
        # 為每個原始線段生成平滑插值
        for i in range(len(points)):
            # 獲取4個控制點（環形賽道處理）
            p0 = points[(i - 1) % len(points)]
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            p3 = points[(i + 2) % len(points)]
            
            # 生成這段的插值點
            segment_points = catmull_rom_segment(p0, p1, p2, p3, density)
            
            # 只取前面部分點，避免重複（除了最後一段）
            end_idx = density if i < len(points) - 1 else density
            for j in range(end_idx):
                if j < len(segment_points):
                    smooth_x.append(segment_points[j][0])
                    smooth_y.append(segment_points[j][1])
                    
        return smooth_x, smooth_y
    
    def _linear_interpolation_fallback(self, x_coords: List[float], y_coords: List[float], density: int) -> tuple:
        """線性插值後備方案"""
        if density <= 1:
            return x_coords, y_coords
            
        smooth_x, smooth_y = [], []
        
        for i in range(len(x_coords)):
            smooth_x.append(x_coords[i])
            smooth_y.append(y_coords[i])
            
            next_i = (i + 1) % len(x_coords)
            
            # 在兩點間插入 density-1 個點
            for j in range(1, density):
                ratio = j / density
                interp_x = x_coords[i] * (1 - ratio) + x_coords[next_i] * ratio
                interp_y = y_coords[i] * (1 - ratio) + y_coords[next_i] * ratio
                smooth_x.append(interp_x)
                smooth_y.append(interp_y)
                
        return smooth_x, smooth_y
    
    def _simple_smooth(self, x_coords: List[float], y_coords: List[float]) -> tuple:
        """簡化的平滑方法 - 不依賴NumPy"""
        if len(x_coords) < 5:
            return x_coords, y_coords
            
        smooth_x = x_coords.copy()
        smooth_y = y_coords.copy()
        
        # 對每個內部點進行3點平滑
        for i in range(1, len(x_coords) - 1):
            smooth_x[i] = (x_coords[i-1] + x_coords[i] + x_coords[i+1]) / 3.0
            smooth_y[i] = (y_coords[i-1] + y_coords[i] + y_coords[i+1]) / 3.0
            
        print(f"🗺️ [TRACK_PLOT] 簡化平滑完成: 保持 {len(x_coords)} 個點")
        return smooth_x, smooth_y
    
    def _draw_track_matplotlib(self, x_coords: List[float], y_coords: List[float]) -> None:
        """使用 Matplotlib 繪製賽道 - 高質量渲染"""
        # 清除現有的繪圖
        self._axes.clear()
        
        # 選擇是否使用平滑化
        if self._use_smooth_curve:
            display_x, display_y = self._smooth_track_curve(x_coords, y_coords)
            print(f"🗺️ [TRACK_PLOT] Matplotlib 使用平滑化數據繪製")
        else:
            display_x, display_y = x_coords, y_coords
            print(f"🗺️ [TRACK_PLOT] Matplotlib 使用原始數據繪製")
        
        # 繪製賽道線（高質量設置）
        self._axes.plot(
            display_x, display_y, 
            color='#4A69E2',        # 藍色
            linewidth=3,            # 稍微加粗
            linestyle='-',          # 實線
            solid_capstyle='round', # 圓形端點
            solid_joinstyle='round',# 圓形接合點
            antialiased=True,       # 抗鋸齒
            label='賽道軌跡'
        )
        
        # 繪製原點標記
        if self._show_origin and len(x_coords) > 0:
            self._axes.plot(
                x_coords[0], y_coords[0], 
                'o', 
                color='red', 
                markersize=8, 
                markeredgecolor='darkred',
                markeredgewidth=1,
                label='起點'
            )
            
        # 更新屬性（高質量設置）
        self._axes.set_xlabel('X 座標 (m)', fontsize=10)
        self._axes.set_ylabel('Y 座標 (m)', fontsize=10) 
        self._axes.set_title('F1 賽道軌跡', fontsize=12, fontweight='bold')
        
        if self._show_grid:
            self._axes.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        self._axes.set_aspect('equal')
        self._axes.legend(loc='upper right', fontsize=9)
        
        # 刷新圖形
        self._plot_widget.draw()
        
    def _fit_view(self) -> None:
        """調整視圖以適應所有數據"""
        if not self._position_records:
            return
            
        if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
            self._plot_widget.autoRange()
        elif MATPLOTLIB_AVAILABLE:
            self._axes.relim()
            self._axes.autoscale()
            self._plot_widget.draw()
            
    def _reset_view(self) -> None:
        """重置視圖"""
        self._fit_view()
        
    def _on_mouse_clicked(self, event) -> None:
        """滑鼠點擊事件處理"""
        if not PYQTGRAPH_AVAILABLE or not self._position_records:
            return
            
        try:
            # 獲取點擊位置
            scene_pos = event.scenePos()
            view_pos = self._plot_widget.getViewBox().mapSceneToView(scene_pos)
            click_x, click_y = view_pos.x(), view_pos.y()
            
            # 尋找最近的數據點
            closest_point = self._find_closest_point(click_x, click_y)
            if closest_point:
                # 標記選中的點
                self._mark_selected_point(closest_point)
                
                # 發出信號
                self.position_clicked.emit(closest_point)
                
        except Exception as e:
            print(f"處理滑鼠點擊事件時發生錯誤: {str(e)}")
            
    def _find_closest_point(self, click_x: float, click_y: float) -> Optional[Dict[str, Any]]:
        """尋找最接近點擊位置的數據點"""
        if not self._position_records:
            return None
            
        min_distance = float('inf')
        closest_point = None
        
        for i, record in enumerate(self._position_records):
            dx = record.get('position_x', record.get('x', 0)) - click_x
            dy = record.get('position_y', record.get('y', 0)) - click_y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_point = record.copy()
                closest_point['index'] = i
                
        return closest_point
        
    def _mark_selected_point(self, point: Dict[str, Any]) -> None:
        """標記選中的點"""
        if not PYQTGRAPH_AVAILABLE:
            return
            
        # 移除之前的標記
        if self._selected_marker:
            self._plot_widget.removeItem(self._selected_marker)
            
        # 添加新的標記
        pen = mkPen(color='green', width=3)
        brush = mkBrush(color='green')
        self._selected_marker = self._plot_widget.plot(
            [point.get('position_x', point.get('x', 0))], 
            [point.get('position_y', point.get('y', 0))], 
            pen=pen,
            symbol='s', 
            symbolSize=8,
            symbolBrush=brush,
            name='選中點'
        )
        
    def _on_origin_toggle(self, checked: bool) -> None:
        """原點顯示切換"""
        self._show_origin = checked
        if self._track_data:
            self._draw_track()
            
    def _on_grid_toggle(self, checked: bool) -> None:
        """網格顯示切換"""
        self._show_grid = checked
        if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
            self._plot_widget.showGrid(x=checked, y=checked)
        elif MATPLOTLIB_AVAILABLE:
            self._axes.grid(checked)
            self._plot_widget.draw()
            
    def _on_auto_range_toggle(self, checked: bool) -> None:
        """自動範圍切換"""
        self._auto_range = checked
        
    def _export_plot(self) -> None:
        """匯出圖片"""
        try:
            if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
                # 使用檔案對話框選擇保存位置
                from PyQt5.QtWidgets import QFileDialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "匯出賽道圖", 
                    "track_plot.png", 
                    "PNG Files (*.png);;All Files (*)"
                )
                if file_path:
                    exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
                    exporter.export(file_path)
                    
            elif MATPLOTLIB_AVAILABLE:
                from PyQt5.QtWidgets import QFileDialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "匯出賽道圖", 
                    "track_plot.png", 
                    "PNG Files (*.png);;All Files (*)"
                )
                if file_path:
                    self._figure.savefig(file_path, dpi=300, bbox_inches='tight')
                    
        except Exception as e:
            print(f"匯出圖片時發生錯誤: {str(e)}")
            
    def export_plot(self, file_path: str) -> bool:
        """
        匯出圖片到指定路徑
        
        Args:
            file_path: 輸出檔案路徑
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
                exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
                exporter.export(file_path)
                return True
                
            elif MATPLOTLIB_AVAILABLE:
                self._figure.savefig(file_path, dpi=300, bbox_inches='tight')
                return True
                
            return False
            
        except Exception as e:
            print(f"匯出圖片到 {file_path} 時發生錯誤: {str(e)}")
            return False
            
    def clear_plot(self) -> None:
        """清除繪圖"""
        if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
            self._plot_widget.clear()
        elif MATPLOTLIB_AVAILABLE:
            self._axes.clear()
            self._axes.set_xlabel('X 座標 (m)')
            self._axes.set_ylabel('Y 座標 (m)')
            self._axes.set_title('F1 賽道軌跡')
            self._plot_widget.draw()
            
        # 清除內部狀態
        self._track_line = None
        self._origin_marker = None
        self._selected_marker = None
        
    def set_smooth_curve(self, enabled: bool) -> None:
        """設置是否使用平滑曲線"""
        if self._use_smooth_curve != enabled:
            self._use_smooth_curve = enabled
            print(f"🗺️ [TRACK_PLOT] 平滑曲線模式: {'啟用' if enabled else '停用'}")
            # 重新繪製
            if self._position_records:
                self._draw_track()
    
    def toggle_smooth_curve(self) -> None:
        """切換平滑曲線模式"""
        self.set_smooth_curve(not self._use_smooth_curve)
    
    def _draw_track_manual(self, x_coords: List[float], y_coords: List[float]) -> None:
        """手動繪製賽道 - 用於測試不同平滑化方法"""
        if not PYQTGRAPH_AVAILABLE or not isinstance(self._plot_widget, PlotWidget):
            return
            
        # 清除現有的繪圖
        self._plot_widget.clear()
        
        # 啟用高質量渲染
        self._plot_widget.setAntialiasing(True)
        
        # 繪製賽道線
        pen = mkPen(
            color='#4A69E2',
            width=3,
            style=Qt.SolidLine,
            capStyle=Qt.RoundCap,
            joinStyle=Qt.RoundJoin
        )
        
        self._track_line = self._plot_widget.plot(
            x_coords, y_coords,
            pen=pen,
            name='賽道軌跡',
            antialias=True,
            connect='finite'
        )
        
        # 繪製起點標記
        if self._show_origin and len(x_coords) > 0:
            origin_pen = mkPen(color='red', width=3)
            origin_brush = mkBrush(color='red')
            self._origin_marker = self._plot_widget.plot(
                [x_coords[0]], [y_coords[0]],
                pen=origin_pen,
                symbol='o',
                symbolSize=12,
                symbolBrush=origin_brush,
                name='起點'
            )
            
        # 自動調整視圖
        if self._auto_range:
            self._fit_view()

    def get_current_view_range(self) -> Optional[Dict[str, float]]:
        """獲取當前視圖範圍"""
        try:
            if PYQTGRAPH_AVAILABLE and isinstance(self._plot_widget, PlotWidget):
                view_box = self._plot_widget.getViewBox()
                [[x_min, x_max], [y_min, y_max]] = view_box.viewRange()
                return {
                    'x_min': x_min,
                    'x_max': x_max, 
                    'y_min': y_min,
                    'y_max': y_max
                }
            return None
        except Exception:
            return None
