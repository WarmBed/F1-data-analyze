#!/usr/bin/env python3
"""
賽道分析GUI模組 - 基於通用MDI子視窗框架
Track Analysis GUI Module - Based on Universal MDI Subwindow Framework

核心功能：
1. 載入CLI功能2的JSON數據
2. 繪製互動式賽道地圖
3. 顯示賽道位置資訊和統計數據
4. 提供賽道地圖互動功能 (縮放、平移、懸停)
"""

import os
import sys
import json
import subprocess
import time
import gc
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QProgressDialog, QMessageBox, QSplitter,
    QTextEdit, QGroupBox, QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QPointF
from PyQt5.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor, QPolygon, QPainterPath

# 導入賽道地圖繪製元件
try:
    from .track_map_widget import TrackMapWidget
    from .track_data_processor import TrackDataProcessor
except ImportError:
    # 開發階段的導入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        from track_map_widget import TrackMapWidget
        from track_data_processor import TrackDataProcessor
    except ImportError:
        print("[WARNING] 賽道地圖元件尚未實現，使用佔位符")
        TrackMapWidget = None
        TrackDataProcessor = None

# 獲取專案根目錄
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TrackAnalysisCacheManager:
    """賽道分析緩存管理器"""
    
    def __init__(self):
        self.cache_dir = os.path.join(project_root, "json")
        self.cache_expiry = 24 * 60 * 60  # 24小時過期
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, year, race, session):
        """生成緩存鍵值"""
        return f"track_position_{year}_{race}_{session}"
    
    def find_latest_track_json(self, year, race, session):
        """查找最新的賽道分析JSON檔案"""
        # 搜索模式：raw_data_track_position_YEAR_RACE_*.json
        import glob
        pattern = os.path.join(self.cache_dir, f"raw_data_track_position_{year}_{race}_*.json")
        files = glob.glob(pattern)
        
        # 如果沒有找到完全匹配的，嘗試搜索包含關鍵字的檔案
        if not files:
            pattern = os.path.join(self.cache_dir, f"raw_data_track_position_*{year}*.json")
            files = glob.glob(pattern)
        
        if files:
            # 按修改時間排序，返回最新的
            latest_file = max(files, key=os.path.getmtime)
            return latest_file
        
        return None
    
    def is_cache_valid(self, file_path):
        """檢查緩存是否有效"""
        if not os.path.exists(file_path):
            return False
        
        file_age = time.time() - os.path.getmtime(file_path)
        return file_age < self.cache_expiry

class TrackAnalysisWorkerThread(QThread):
    """賽道分析工作執行緒"""
    
    progress_updated = pyqtSignal(int, str)  # 進度和狀態訊息
    analysis_completed = pyqtSignal(dict)    # 分析完成
    analysis_failed = pyqtSignal(str)        # 分析失敗
    
    def __init__(self, year, race, session):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        self.cache_manager = TrackAnalysisCacheManager()
    
    def run(self):
        """執行賽道分析"""
        try:
            self.progress_updated.emit(10, "檢查緩存數據...")
            
            # 1. 檢查緩存
            cached_file = self.cache_manager.find_latest_track_json(
                self.year, self.race, self.session
            )
            
            if cached_file and self.cache_manager.is_cache_valid(cached_file):
                self.progress_updated.emit(50, "使用緩存數據...")
                track_data = self.load_json_data(cached_file)
                if track_data:
                    self.progress_updated.emit(100, "緩存載入完成")
                    self.analysis_completed.emit(track_data)
                    return
            
            # 2. 執行CLI分析
            self.progress_updated.emit(30, "執行賽道位置分析...")
            success = self.run_cli_analysis()
            
            if not success:
                self.analysis_failed.emit("CLI分析執行失敗")
                return
            
            # 3. 載入分析結果
            self.progress_updated.emit(80, "載入分析結果...")
            cached_file = self.cache_manager.find_latest_track_json(
                self.year, self.race, self.session
            )
            
            if cached_file:
                track_data = self.load_json_data(cached_file)
                if track_data:
                    self.progress_updated.emit(100, "分析完成")
                    self.analysis_completed.emit(track_data)
                    return
            
            self.analysis_failed.emit("無法載入分析結果")
            
        except Exception as e:
            self.analysis_failed.emit(f"分析執行錯誤: {str(e)}")
    
    def run_cli_analysis(self):
        """執行CLI賽道位置分析"""
        try:
            cli_script = os.path.join(project_root, "f1_analysis_modular_main.py")
            command = [
                "python", cli_script,
                "-f", "2",  # 功能2: 賽道位置分析
                "-y", str(self.year),
                "-r", self.race,
                "-s", self.session,
                "-d", self.driver  # 添加車手參數
            ]
            
            result = subprocess.run(
                command,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("[ERROR] CLI分析執行超時")
            return False
        except Exception as e:
            print(f"[ERROR] CLI分析執行錯誤: {e}")
            return False
    
    def load_json_data(self, file_path):
        """載入JSON數據"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 驗證數據格式
            if (data.get('analysis_type') == 'track_position_analysis' and
                'detailed_position_records' in data):
                return data
            else:
                print(f"[WARNING] JSON格式不符合預期: {file_path}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 載入JSON失敗: {e}")
            return None

class TrackMapWidget(QWidget):
    """
    專門用於繪製賽道地圖的 PyQt Widget
    使用 QPainter 繪製賽道路線和位置點
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.position_data = []
        self.track_bounds = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # 顯示控制選項
        self.show_start_point = True      # 顯示起始點
        self.show_finish_point = True     # 顯示結束點
        self.show_distance_markers = True # 顯示距離標記
        self.show_track_labels = True     # 顯示 START/FINISH 標籤
        
        # self.setMinimumSize(400, 300) - 尺寸限制已移除
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
    def set_track_data(self, position_data, track_bounds):
        """設置賽道數據"""
        print(f"[TRACK_MAP] set_track_data: 接收 {len(position_data) if position_data else 0} 個位置點")
        print(f"[TRACK_MAP] set_track_data: 賽道邊界 {track_bounds}")
        
        self.position_data = position_data
        self.track_bounds = track_bounds
        
        # 立即計算縮放 (確保widget有正確尺寸)
        if track_bounds and self.width() > 0 and self.height() > 0:
            self.calculate_scale()
            print(f"[TRACK_MAP] set_track_data: 計算完成，縮放因子 {self.scale_factor:.3f}")
            print(f"[TRACK_MAP] set_track_data: 偏移 ({self.offset_x:.1f}, {self.offset_y:.1f})")
        else:
            # 如果widget尺寸還未確定，使用QTimer延遲計算
            print(f"[TRACK_MAP] set_track_data: Widget尺寸 {self.width()}x{self.height()}, 延遲計算縮放")
            QTimer.singleShot(50, self.calculate_scale)
        
        self.update()  # 觸發重繪
        print("[TRACK_MAP] set_track_data: ✅ 觸發重繪完成")
        
    def set_display_options(self, show_start=True, show_finish=True, show_markers=True, show_labels=True):
        """設置顯示選項"""
        self.show_start_point = show_start
        self.show_finish_point = show_finish
        self.show_distance_markers = show_markers
        self.show_track_labels = show_labels
        self.update()  # 觸發重繪
        print(f"[TRACK_MAP] 顯示選項更新: 起始點={show_start}, 結束點={show_finish}, 距離標記={show_markers}, 標籤={show_labels}")
        
    def calculate_scale(self):
        """計算適當的縮放比例 - 響應式計算"""
        if not self.track_bounds:
            print("[TRACK_MAP] calculate_scale: 沒有賽道邊界數據")
            return
            
        # 獲取當前widget的實際尺寸
        widget_width = self.width()
        widget_height = self.height()
        
        # 確保widget有有效尺寸
        if widget_width <= 0 or widget_height <= 0:
            print(f"[TRACK_MAP] calculate_scale: Widget尺寸無效 {widget_width}x{widget_height}")
            return
            
        # 計算保留邊距後的可用空間
        margin = 40  # 邊距
        available_width = widget_width - margin
        available_height = widget_height - margin
        
        # 計算賽道實際尺寸
        track_width = self.track_bounds['x_max'] - self.track_bounds['x_min']
        track_height = self.track_bounds['y_max'] - self.track_bounds['y_min']
        
        if track_width > 0 and track_height > 0:
            # 計算X和Y方向的縮放比例
            scale_x = available_width / track_width
            scale_y = available_height / track_height
            
            # 選擇較小的縮放比例，確保賽道完全顯示
            self.scale_factor = min(scale_x, scale_y) * 0.85  # 85% 填滿，保留一些空白
            
            # 計算置中偏移
            scaled_track_width = track_width * self.scale_factor
            scaled_track_height = track_height * self.scale_factor
            self.offset_x = (widget_width - scaled_track_width) / 2
            self.offset_y = (widget_height - scaled_track_height) / 2
            
            print(f"[TRACK_MAP] calculate_scale: Widget={widget_width}x{widget_height}, 賽道={track_width:.0f}x{track_height:.0f}")
            print(f"[TRACK_MAP] calculate_scale: 縮放={self.scale_factor:.3f}, 偏移=({self.offset_x:.1f}, {self.offset_y:.1f})")
        else:
            print(f"[TRACK_MAP] calculate_scale: 賽道尺寸無效 {track_width}x{track_height}")
            self.scale_factor = 1.0
            self.offset_x = 0
            self.offset_y = 0
    
    def world_to_screen(self, x, y):
        """將世界座標轉換為螢幕座標"""
        if not self.track_bounds:
            return x, y
            
        # 轉換座標系統 (Y軸翻轉)
        screen_x = (x - self.track_bounds['x_min']) * self.scale_factor + self.offset_x
        screen_y = (self.track_bounds['y_max'] - y) * self.scale_factor + self.offset_y
        return int(screen_x), int(screen_y)
    
    def paintEvent(self, event):
        """繪製賽道地圖"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 清空背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        if not self.position_data or not self.track_bounds:
            # 顯示提示文字
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, 
                           "賽道地圖已載入\n50 個位置點\n(點擊可查看詳細座標)")
            print("[TRACK_MAP] paintEvent: 沒有數據，顯示提示文字")
            return
        
        try:
            # 每次繪製時檢查是否需要重新計算縮放
            if (self.scale_factor <= 0 or 
                self.width() != getattr(self, '_last_width', 0) or 
                self.height() != getattr(self, '_last_height', 0)):
                print(f"[TRACK_MAP] paintEvent: 檢測到尺寸變化，重新計算縮放")
                self.calculate_scale()
                self._last_width = self.width()
                self._last_height = self.height()
            
            print(f"[TRACK_MAP] paintEvent: 開始繪製，包含 {len(self.position_data)} 個位置點")
            print(f"[TRACK_MAP] paintEvent: 當前縮放因子 {self.scale_factor:.3f}, 偏移 ({self.offset_x:.1f}, {self.offset_y:.1f})")
            
            # 繪製賽道路線
            if len(self.position_data) > 1:
                points = []
                for record in self.position_data:
                    x = record.get('position_x', 0)
                    y = record.get('position_y', 0)
                    screen_x, screen_y = self.world_to_screen(x, y)
                    points.append(QPointF(screen_x, screen_y))
                
                print(f"[TRACK_MAP] paintEvent: 轉換得到 {len(points)} 個螢幕座標點")
                if len(points) >= 2:
                    print(f"[TRACK_MAP] paintEvent: 第一個點 ({points[0].x():.1f}, {points[0].y():.1f}), 最後一個點 ({points[-1].x():.1f}, {points[-1].y():.1f})")
                
                # 創建平滑的賽道路徑
                path = QPainterPath()
                if len(points) >= 2:
                    path.moveTo(points[0])
                    
                    # 使用二次貝茲曲線創建平滑路徑
                    for i in range(1, len(points)):
                        if i < len(points) - 1:
                            # 計算控制點，使曲線更平滑
                            control_point = QPointF(
                                (points[i].x() + points[i+1].x()) / 2,
                                (points[i].y() + points[i+1].y()) / 2
                            )
                            path.quadTo(points[i], control_point)
                        else:
                            # 最後一個點直接連接
                            path.lineTo(points[i])
                
                # 繪製平滑的賽道線條
                painter.setPen(QPen(QColor(50, 50, 200), 4))  # 稍微加粗線條
                painter.drawPath(path)
                
                # 繪製賽道邊框 (淺色)
                painter.setPen(QPen(QColor(100, 100, 255), 1))
                painter.drawPath(path)
                
                # 繪製起始點 (綠色，稍大)
                if points and self.show_start_point:
                    painter.setBrush(QBrush(QColor(0, 200, 0)))
                    painter.setPen(QPen(QColor(0, 150, 0), 2))
                    painter.drawEllipse(int(points[0].x()) - 6, int(points[0].y()) - 6, 12, 12)
                    
                    # 起始點標籤
                    if self.show_track_labels:
                        painter.setPen(QPen(QColor(0, 100, 0)))
                        painter.setFont(QFont("Arial", 8, QFont.Bold))
                        painter.drawText(int(points[0].x()) + 10, int(points[0].y()) - 5, "START")
                
                # 繪製結束點 (紅色，稍大)
                if len(points) > 1 and self.show_finish_point:
                    painter.setBrush(QBrush(QColor(200, 0, 0)))
                    painter.setPen(QPen(QColor(150, 0, 0), 2))
                    painter.drawEllipse(int(points[-1].x()) - 6, int(points[-1].y()) - 6, 12, 12)
                    
                    # 結束點標籤
                    if self.show_track_labels:
                        painter.setPen(QPen(QColor(100, 0, 0)))
                        painter.setFont(QFont("Arial", 8, QFont.Bold))
                        painter.drawText(int(points[-1].x()) + 10, int(points[-1].y()) - 5, "FINISH")
                
                # 繪製距離標記點 (每隔幾個點)
                if self.show_distance_markers:
                    painter.setBrush(QBrush(QColor(0, 0, 200)))
                    painter.setPen(QPen(QColor(0, 0, 150), 1))
                    step = max(1, len(points) // 8)  # 約8個標記點
                    for i in range(0, len(points), step):
                        if i > 0 and i < len(points) - 1:  # 跳過起始和結束點
                            painter.drawEllipse(int(points[i].x()) - 3, int(points[i].y()) - 3, 6, 6)
                            
                            # 顯示距離標記
                            if i < len(self.position_data):
                                distance_km = self.position_data[i].get('distance_m', 0) / 1000
                                if distance_km > 0:
                                    painter.setPen(QPen(QColor(0, 0, 100)))
                                    painter.setFont(QFont("Arial", 7))
                                    painter.drawText(int(points[i].x()) + 5, int(points[i].y()) + 15, f"{distance_km:.1f}km")
                
                print(f"[TRACK_MAP] paintEvent: ✅ 平滑賽道線條和標記繪製完成")
            
            # 隱藏圖例繪製
            # self.draw_legend(painter)
            
            print("[TRACK_MAP] paintEvent: ✅ 賽道地圖繪製完成")
            
        except Exception as e:
            print(f"[ERROR] paintEvent: 繪製賽道地圖時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            painter.setPen(QPen(QColor(200, 0, 0)))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(10, 20, f"繪製錯誤: {str(e)}")
    
    def mousePressEvent(self, event):
        """處理滑鼠點擊事件"""
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()
            print(f"[TRACK_MAP] 點擊位置: {{'x': {x}, 'y': {y}, 'total_points': {len(self.position_data)}}}")
            
            # 可以在這裡添加更多點擊處理邏輯
            # 例如：找到最近的賽道點、顯示詳細資訊等
            
        super().mousePressEvent(event)
    
    def draw_legend(self, painter):
        """繪製圖例"""
        legend_x = 10
        legend_y = self.height() - 80
        legend_item_height = 15
        current_y = legend_y
        
        painter.setFont(QFont("Arial", 8))
        
        # 賽道線圖例 (總是顯示)
        painter.setPen(QPen(QColor(50, 50, 200), 3))
        painter.drawLine(legend_x, current_y, legend_x + 10, current_y)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(legend_x + 15, current_y + 5, "賽道路線 (平滑化)")
        current_y += legend_item_height
        
        # 起始點圖例 (根據顯示選項)
        if self.show_start_point:
            painter.setBrush(QBrush(QColor(0, 200, 0)))
            painter.setPen(QPen(QColor(0, 150, 0), 1))
            painter.drawEllipse(legend_x, current_y - 4, 8, 8)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(legend_x + 15, current_y + 1, "起始點 (START)")
            current_y += legend_item_height
        
        # 結束點圖例 (根據顯示選項)
        if self.show_finish_point:
            painter.setBrush(QBrush(QColor(200, 0, 0)))
            painter.setPen(QPen(QColor(150, 0, 0), 1))
            painter.drawEllipse(legend_x, current_y - 4, 8, 8)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(legend_x + 15, current_y + 1, "結束點 (FINISH)")
            current_y += legend_item_height
        
        # 距離標記圖例 (根據顯示選項)
        if self.show_distance_markers:
            painter.setBrush(QBrush(QColor(0, 0, 200)))
            painter.setPen(QPen(QColor(0, 0, 150), 1))
            painter.drawEllipse(legend_x, current_y - 4, 6, 6)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(legend_x + 15, current_y + 1, "距離標記")
    
    def force_rescale(self):
        """強制重新計算縮放 - 用於外部觸發"""
        print(f"[TRACK_MAP] force_rescale: 強制重新計算縮放")
        if self.track_bounds:
            self.calculate_scale()
            self.update()
            print(f"[TRACK_MAP] force_rescale: ✅ 縮放更新完成，縮放因子 {self.scale_factor:.3f}")
        else:
            print("[TRACK_MAP] force_rescale: 沒有賽道邊界數據")
    
    def resizeEvent(self, event):
        """視窗大小改變時重新計算縮放"""
        super().resizeEvent(event)
        print(f"[TRACK_MAP] resizeEvent: 新尺寸 {event.size().width()}x{event.size().height()}")
        
        if self.track_bounds:
            old_scale = self.scale_factor
            self.calculate_scale()
            print(f"[TRACK_MAP] resizeEvent: 縮放更新 {old_scale:.3f} -> {self.scale_factor:.3f}")
            self.update()  # 觸發重繪
        else:
            print("[TRACK_MAP] resizeEvent: 等待賽道數據載入")

class TrackAnalysisModule(QWidget):
    """賽道分析主模組"""
    
    def __init__(self, year=2025, race="Japan", session="R", driver="VER"):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        self.driver = driver
        self.track_data = None
        self.data_processor = None
        
        # 初始化數據處理器
        if TrackDataProcessor:
            self.data_processor = TrackDataProcessor()
        
        self.init_ui()
        self.init_connections()
        
        # 自動開始分析
        QTimer.singleShot(100, self.start_analysis_workflow)
    
    def init_ui(self):
        """初始化用戶界面 - 僅顯示賽道地圖"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        layout.setSpacing(0)  # 移除間距
        
        # 隱藏控制面板
        # self.create_control_panel(layout)
        
        # 直接創建賽道地圖區域，無需分割器
        self.create_track_map_area_only(layout)
        
        # 隱藏右側資訊面板
        # self.create_info_panel(splitter)
        
        # 隱藏底部狀態區域
        # self.create_status_area(layout)
    
    def create_control_panel(self, parent_layout):
        """創建頂部控制面板"""
        control_panel = QWidget()
        control_panel.setFixedHeight(70)  # 增加高度以容納兩行控制項
        control_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """)
        
        main_layout = QVBoxLayout(control_panel)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        
        # 第一行：標題和主要按鈕
        top_row = QWidget()
        control_layout = QHBoxLayout(top_row)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 標題標籤
        title_label = QLabel(f"賽道分析 - {self.year} {self.race} {self.session}")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        control_layout.addWidget(title_label)
        
        control_layout.addStretch()
        
        # 重新載入按鈕
        self.reload_btn = QPushButton("🔄 重新載入")
        self.reload_btn.setFixedSize(80, 30)
        self.reload_btn.clicked.connect(self.reload_analysis)
        control_layout.addWidget(self.reload_btn)
        
        # 匯出按鈕
        self.export_btn = QPushButton("📄 匯出")
        self.export_btn.setFixedSize(60, 30)
        self.export_btn.clicked.connect(self.export_track_map)
        control_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(top_row)
        
        # 第二行：顯示選項複選框
        options_row = QWidget()
        options_layout = QHBoxLayout(options_row)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顯示選項標籤
        options_label = QLabel("顯示選項:")
        options_label.setFont(QFont("Microsoft YaHei", 9))
        options_layout.addWidget(options_label)
        
        # 起始點複選框
        self.show_start_checkbox = QCheckBox("起始點")
        self.show_start_checkbox.setChecked(True)
        self.show_start_checkbox.stateChanged.connect(self.update_display_options)
        options_layout.addWidget(self.show_start_checkbox)
        
        # 結束點複選框
        self.show_finish_checkbox = QCheckBox("結束點")
        self.show_finish_checkbox.setChecked(True)
        self.show_finish_checkbox.stateChanged.connect(self.update_display_options)
        options_layout.addWidget(self.show_finish_checkbox)
        
        # 距離標記複選框
        self.show_markers_checkbox = QCheckBox("距離標記")
        self.show_markers_checkbox.setChecked(True)
        self.show_markers_checkbox.stateChanged.connect(self.update_display_options)
        options_layout.addWidget(self.show_markers_checkbox)
        
        # 標籤複選框
        self.show_labels_checkbox = QCheckBox("START/FINISH標籤")
        self.show_labels_checkbox.setChecked(True)
        self.show_labels_checkbox.stateChanged.connect(self.update_display_options)
        options_layout.addWidget(self.show_labels_checkbox)
        
        options_layout.addStretch()
        
        main_layout.addWidget(options_row)
        
        parent_layout.addWidget(control_panel)
    
    def create_track_map_area(self, parent_splitter):
        """創建賽道地圖區域"""
        map_container = QGroupBox("賽道地圖")
        map_layout = QVBoxLayout(map_container)
        
        # 創建賽道地圖元件 (使用新的 PyQt 繪製元件)
        self.track_map = TrackMapWidget()
        # self.track_map.setMinimumSize(400, 300) - 尺寸限制已移除
        map_layout.addWidget(self.track_map)
        
        parent_splitter.addWidget(map_container)
    
    def create_track_map_area_only(self, parent_layout):
        """創建純淨的賽道地圖區域 - 無邊框，無控制項"""
        # 直接創建賽道地圖元件，無容器
        self.track_map = TrackMapWidget()
        self.track_map.setStyleSheet("background-color: white; border: none;")
        
        # 設置默認顯示選項：只顯示起始點，隱藏其他元素
        self.track_map.show_start_point = True       # 顯示起始點
        self.track_map.show_finish_point = False     # 隱藏結束點
        self.track_map.show_distance_markers = False # 隱藏距離標記
        self.track_map.show_track_labels = False     # 隱藏標籤
        
        parent_layout.addWidget(self.track_map)
    
    def create_info_panel(self, parent_splitter):
        """創建右側資訊面板"""
        info_container = QGroupBox("賽道資訊")
        info_layout = QVBoxLayout(info_container)
        
        # 基本資訊區域
        self.create_basic_info_section(info_layout)
        
        # 統計資訊區域
        self.create_statistics_section(info_layout)
        
        # 詳細數據區域
        self.create_data_section(info_layout)
        
        parent_splitter.addWidget(info_container)
    
    def create_basic_info_section(self, parent_layout):
        """創建基本資訊區域"""
        basic_group = QGroupBox("基本資訊")
        basic_layout = QVBoxLayout(basic_group)
        
        self.track_name_label = QLabel("賽道名稱: --")
        self.total_distance_label = QLabel("總長度: --")
        self.position_points_label = QLabel("位置點數: --")
        self.bounds_label = QLabel("座標範圍: --")
        
        for label in [self.track_name_label, self.total_distance_label, 
                     self.position_points_label, self.bounds_label]:
            label.setFont(QFont("Microsoft YaHei", 9))
            basic_layout.addWidget(label)
        
        parent_layout.addWidget(basic_group)
    
    def create_statistics_section(self, parent_layout):
        """創建統計資訊區域"""
        stats_group = QGroupBox("統計資訊")
        stats_layout = QVBoxLayout(stats_group)
        
        self.fastest_lap_label = QLabel("最快圈: --")
        self.data_quality_label = QLabel("數據品質: --")
        
        for label in [self.fastest_lap_label, self.data_quality_label]:
            label.setFont(QFont("Microsoft YaHei", 9))
            stats_layout.addWidget(label)
        
        parent_layout.addWidget(stats_group)
    
    def create_data_section(self, parent_layout):
        """創建詳細數據區域"""
        data_group = QGroupBox("詳細數據")
        data_layout = QVBoxLayout(data_group)
        
        # 數據預覽區域 (可滾動)
        self.data_preview = QTextEdit()
        self.data_preview.setMaximumHeight(150)
        self.data_preview.setFont(QFont("Courier New", 8))
        self.data_preview.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
            }
        """)
        data_layout.addWidget(self.data_preview)
        
        parent_layout.addWidget(data_group)
    
    def create_status_area(self, parent_layout):
        """創建底部狀態區域"""
        self.status_label = QLabel("狀態: 準備中...")
        self.status_label.setFixedHeight(25)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
        """)
        parent_layout.addWidget(self.status_label)
        
        # 進度條 (隱藏狀態)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        parent_layout.addWidget(self.progress_bar)
    
    def init_connections(self):
        """初始化信號連接"""
        # 目前暫無特殊連接需求
        pass
    
    def start_analysis_workflow(self):
        """開始賽道分析工作流程"""
        print(f"[TRACK] 開始賽道分析工作流程: {self.year} {self.race} {self.session}")
        
        # 隱藏狀態和進度顯示
        # self.status_label.setText("狀態: 執行賽道分析中...")
        # self.progress_bar.setVisible(True)
        # self.progress_bar.setValue(0)
        
        # 建立並啟動工作執行緒
        self.worker_thread = TrackAnalysisWorkerThread(self.year, self.race, self.session)
        self.worker_thread.progress_updated.connect(self.on_progress_updated)
        self.worker_thread.analysis_completed.connect(self.on_analysis_completed)
        self.worker_thread.analysis_failed.connect(self.on_analysis_failed)
        self.worker_thread.start()
    
    def on_progress_updated(self, progress, message):
        """進度更新處理"""
        # 隱藏進度顯示
        # self.progress_bar.setValue(progress)
        # self.status_label.setText(f"狀態: {message}")
        print(f"[TRACK] 進度: {progress}% - {message}")
    
    def on_analysis_completed(self, track_data):
        """分析完成處理"""
        self.track_data = track_data
        # 隱藏進度條和狀態更新
        # self.progress_bar.setVisible(False)
        # self.status_label.setText("狀態: 分析完成")
        
        # 更新UI顯示 - 僅更新地圖
        # self.update_track_info_display()  # 隱藏資訊顯示
        self.update_track_map_display()
        
        print("[TRACK] 賽道分析完成，數據已載入")
    
    def on_analysis_failed(self, error_message):
        """分析失敗處理"""
        # 隱藏進度條和狀態更新
        # self.progress_bar.setVisible(False)
        # self.status_label.setText(f"狀態: 分析失敗 - {error_message}")
        
        print(f"[TRACK] 分析失敗: {error_message}")
        # QMessageBox.warning(self, "賽道分析失敗", f"分析執行失敗:\n{error_message}")
    
    def update_track_info_display(self):
        """更新賽道資訊顯示"""
        if not self.track_data:
            return
        
        try:
            # 基本資訊
            session_info = self.track_data.get('session_info', {})
            position_analysis = self.track_data.get('position_analysis', {})
            
            track_name = session_info.get('track_name', '未知賽道')
            distance_km = position_analysis.get('distance_covered_m', 0) / 1000
            total_points = position_analysis.get('total_position_records', 0)
            
            self.track_name_label.setText(f"賽道名稱: {track_name}")
            self.total_distance_label.setText(f"總長度: {distance_km:.3f} km")
            self.position_points_label.setText(f"位置點數: {total_points}")
            
            # 座標範圍
            bounds = position_analysis.get('track_bounds', {})
            if bounds:
                x_range = f"X({bounds.get('x_min', 0):.0f} ~ {bounds.get('x_max', 0):.0f})"
                y_range = f"Y({bounds.get('y_min', 0):.0f} ~ {bounds.get('y_max', 0):.0f})"
                self.bounds_label.setText(f"座標範圍: {x_range}, {y_range}")
            
            # 最快圈資訊
            fastest_lap = position_analysis.get('fastest_lap_info', {})
            if fastest_lap:
                driver = fastest_lap.get('driver', '--')
                lap_num = fastest_lap.get('lap_number', '--')
                # 格式化圈速時間
                lap_time_str = fastest_lap.get('lap_time', '--')
                if 'days' in str(lap_time_str):
                    # 移除 "0 days " 前綴並格式化
                    lap_time_str = str(lap_time_str).replace('0 days ', '')
                
                self.fastest_lap_label.setText(f"最快圈: {driver} (第{lap_num}圈) - {lap_time_str}")
            
            # 數據品質
            data_completeness = "良好" if total_points >= 30 else "普通"
            self.data_quality_label.setText(f"數據品質: {data_completeness}")
            
            # 詳細數據預覽
            self.update_data_preview()
            
        except Exception as e:
            print(f"[ERROR] 更新賽道資訊顯示失敗: {e}")
    
    def update_data_preview(self):
        """更新數據預覽"""
        if not self.track_data:
            return
        
        try:
            records = self.track_data.get('detailed_position_records', [])
            preview_text = "位置數據預覽 (前10個點):\n\n"
            
            for i, record in enumerate(records[:10]):
                point_idx = record.get('point_index', i+1)
                distance = record.get('distance_m', 0)
                x = record.get('position_x', 0)
                y = record.get('position_y', 0)
                
                preview_text += f"#{point_idx:2d}: 距離={distance:7.1f}m, X={x:7.0f}, Y={y:7.0f}\n"
            
            if len(records) > 10:
                preview_text += f"\n... 另外 {len(records) - 10} 個數據點"
            
            self.data_preview.setPlainText(preview_text)
            
        except Exception as e:
            self.data_preview.setPlainText(f"數據預覽載入失敗: {e}")
    
    def update_track_map_display(self):
        """更新賽道地圖顯示"""
        if not self.track_data:
            print("[WARNING] 沒有賽道數據可顯示")
            return
        
        try:
            # 提取位置數據和邊界資訊
            records = self.track_data.get('detailed_position_records', [])
            position_analysis = self.track_data.get('position_analysis', {})
            track_bounds = position_analysis.get('track_bounds', {})
            
            if not records:
                print("[WARNING] 沒有詳細位置記錄")
                return
            
            if not track_bounds:
                print("[WARNING] 沒有賽道邊界資訊")
                return
            
            # 使用新的 TrackMapWidget 顯示賽道地圖
            print(f"[TRACK] 開始載入賽道地圖，包含 {len(records)} 個位置點")
            print(f"[TRACK] 賽道邊界: X({track_bounds.get('x_min', 0):.0f} ~ {track_bounds.get('x_max', 0):.0f}), Y({track_bounds.get('y_min', 0):.0f} ~ {track_bounds.get('y_max', 0):.0f})")
            
            # 設置賽道數據到地圖元件
            self.track_map.set_track_data(records, track_bounds)
            
            # 應用固定顯示選項
            self.update_display_options()
            
            # 確保地圖能正確響應當前視窗大小
            QTimer.singleShot(100, lambda: self._ensure_map_scaling())
            
            print("[TRACK] ✅ 賽道地圖載入完成")
            
        except Exception as e:
            print(f"[ERROR] 更新賽道地圖顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _ensure_map_scaling(self):
        """確保地圖縮放正確 - 內部方法"""
        if hasattr(self, 'track_map') and self.track_map:
            print(f"[TRACK] _ensure_map_scaling: 檢查地圖縮放，模組尺寸 {self.width()}x{self.height()}")
            print(f"[TRACK] _ensure_map_scaling: 地圖元件尺寸 {self.track_map.width()}x{self.track_map.height()}")
            self.track_map.force_rescale()
            print("[TRACK] _ensure_map_scaling: ✅ 地圖縮放檢查完成")
    def update_track_map_with_text(self):
        """更新地圖為文字顯示模式"""
        if not self.track_data or not hasattr(self, 'map_content'):
            return
        
        try:
            records = self.track_data.get('detailed_position_records', [])
            text_content = f"賽道路線已載入\n{len(records)} 個位置點\n(點擊可查看詳細座標)"
            
            # 創建可點擊的標籤
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            
            clickable_label = QLabel(text_content)
            clickable_label.setAlignment(Qt.AlignCenter)
            clickable_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #007bff;
                    border-radius: 10px;
                    color: #007bff;
                    font-size: 14px;
                    background-color: #f8f9fa;
                    padding: 20px;
                }
                QLabel:hover {
                    background-color: #e9ecef;
                    cursor: pointer;
                }
            """)
            # clickable_label.setMinimumSize(400, 200) - 尺寸限制已移除
            
            # 添加點擊事件
            def on_label_click(event):
                self.show_coordinate_details()
            
            clickable_label.mousePressEvent = on_label_click
            
            self.track_map.setWidget(clickable_label)
            
        except Exception as e:
            print(f"[ERROR] 更新文字地圖失敗: {e}")
    
    def show_coordinate_details(self):
        """顯示座標詳細資訊"""
        if not self.track_data:
            return
        
        try:
            records = self.track_data.get('detailed_position_records', [])
            
            # 創建詳細資訊對話框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("賽道座標詳細資訊")
            dialog.setFixedSize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 座標資訊文字區域
            text_area = QTextEdit()
            text_area.setReadOnly(True)
            text_area.setFont(QFont("Consolas", 9))
            
            # 生成座標資訊文字
            coord_text = "賽道位置座標詳細資訊:\n\n"
            coord_text += f"{'點':<3} {'距離(m)':<10} {'X座標':<10} {'Y座標':<10}\n"
            coord_text += "-" * 50 + "\n"
            
            for record in records:
                point_idx = record.get('point_index', 0)
                distance = record.get('distance_m', 0)
                x = record.get('position_x', 0)
                y = record.get('position_y', 0)
                coord_text += f"{point_idx:<3} {distance:<10.1f} {x:<10.0f} {y:<10.0f}\n"
            
            text_area.setPlainText(coord_text)
            layout.addWidget(text_area)
            
            # 關閉按鈕
            close_btn = QPushButton("關閉")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec_()
            
        except Exception as e:
            print(f"[ERROR] 顯示座標詳細資訊失敗: {e}")
    
    def set_analysis_parameters(self, parameters):
        """設定分析參數 - 用於參數同步"""
        year = parameters.get('year', self.year)
        race = parameters.get('race', self.race)
        session = parameters.get('session', self.session)
        
        # 檢查參數是否有變化
        if (str(year) != str(self.year) or 
            str(race) != str(self.race) or 
            str(session) != str(self.session)):
            
            print(f"[TRACK] 更新分析參數: {year} {race} {session}")
            self.year = year
            self.race = race
            self.session = session
            
            # 重新開始分析
            self.start_analysis_workflow()
    
    def reload_analysis(self):
        """重新載入分析"""
        print(f"[TRACK] 重新載入賽道分析: {self.year} {self.race} {self.session}")
        self.start_analysis_workflow()
    
    def update_display_options(self):
        """更新賽道地圖顯示選項 - 固定設置，無複選框控制"""
        if hasattr(self, 'track_map'):
            # 固定顯示選項：只顯示起始點
            show_start = True    # 始終顯示起始點
            show_finish = False  # 始終隱藏結束點
            show_markers = False # 始終隱藏距離標記
            show_labels = False  # 始終隱藏標籤
            
            # 更新地圖顯示選項
            self.track_map.set_display_options(show_start, show_finish, show_markers, show_labels)
            
            print(f"[TRACK] 固定顯示選項: 起始點={show_start}, 結束點={show_finish}, 距離標記={show_markers}, 標籤={show_labels}")
    
    def export_track_map(self):
        """匯出賽道地圖"""
        if not self.track_data:
            QMessageBox.information(self, "匯出失敗", "沒有可匯出的賽道數據")
            return
        
        try:
            # 匯出JSON數據
            export_dir = os.path.join(project_root, "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"track_analysis_{self.year}_{self.race}_{self.session}_{timestamp}.json"
            filepath = os.path.join(export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.track_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "匯出成功", f"賽道數據已匯出至:\n{filepath}")
            
        except Exception as e:
            QMessageBox.warning(self, "匯出失敗", f"匯出過程中發生錯誤:\n{str(e)}")
    
    def resizeEvent(self, event):
        """處理視窗大小調整 - MDI子視窗縮放支援"""
        super().resizeEvent(event)
        
        new_size = event.size()
        old_size = event.oldSize() if event.oldSize().isValid() else new_size
        
        print(f"[TRACK] resizeEvent: MDI視窗縮放 {old_size.width()}x{old_size.height()} -> {new_size.width()}x{new_size.height()}")
        
        # 確保賽道地圖元件存在並且有數據
        if hasattr(self, 'track_map') and self.track_map:
            # 強制重新計算地圖縮放
            if hasattr(self.track_map, 'track_bounds') and self.track_map.track_bounds:
                print("[TRACK] resizeEvent: 觸發賽道地圖重新縮放")
                # 使用QTimer確保widget尺寸已更新
                QTimer.singleShot(10, lambda: self._update_track_map_scale())
            else:
                print("[TRACK] resizeEvent: 賽道地圖尚未載入數據")
        else:
            print("[TRACK] resizeEvent: 賽道地圖元件尚未初始化")
    
    def _update_track_map_scale(self):
        """更新賽道地圖縮放 - 內部方法"""
        if hasattr(self, 'track_map') and self.track_map:
            print(f"[TRACK] _update_track_map_scale: 地圖元件尺寸 {self.track_map.width()}x{self.track_map.height()}")
            self.track_map.calculate_scale()
            self.track_map.update()
            print("[TRACK] _update_track_map_scale: ✅ 賽道地圖縮放更新完成")

# 記憶體優化
def optimize_memory():
    """優化記憶體使用"""
    gc.collect()

if __name__ == "__main__":
    # 獨立測試
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    test_module = TrackAnalysisModule(year=2025, race="Japan", session="R")
    test_module.show()
    test_module.resize(1000, 700)
    
    sys.exit(app.exec_())
