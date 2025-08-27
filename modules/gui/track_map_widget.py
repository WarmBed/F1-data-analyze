#!/usr/bin/env python3
"""
賽道地圖繪製元件 - TrackMapWidget
Track Map Drawing Widget

此檔案為賽道地圖繪製的核心元件，負責：
1. 載入賽道位置數據
2. 繪製賽道路線和標記
3. 提供互動功能 (縮放、平移、懸停)
4. 顯示距離標記和座標網格

目前為佔位符實現，待後續完整開發
"""

import sys
import json
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

class TrackMapWidget(QWidget):
    """賽道地圖繪製元件 - 佔位符版本"""
    
    # 信號定義
    point_hovered = pyqtSignal(dict)  # 座標點懸停信號
    point_clicked = pyqtSignal(dict)  # 座標點點擊信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.track_data = None
        self.position_records = []
        self.track_bounds = {}
        
        # 繪圖設定
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.margin = 50  # 邊距
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # self.setMinimumSize(400, 300) - 尺寸限制已移除
        self.setStyleSheet("""
            TrackMapWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        
        # 設置佔位符
        layout = QVBoxLayout(self)
        self.placeholder_label = QLabel("賽道地圖\n(準備中...)")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                border: 2px dashed #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 20px;
            }
        """)
        layout.addWidget(self.placeholder_label)
    
    def load_track_data(self, track_data):
        """載入賽道數據"""
        self.track_data = track_data
        
        if not track_data:
            print("[TRACK_MAP] 無賽道數據")
            return False
        
        try:
            # 提取位置記錄
            self.position_records = track_data.get('detailed_position_records', [])
            
            # 提取賽道邊界
            position_analysis = track_data.get('position_analysis', {})
            self.track_bounds = position_analysis.get('track_bounds', {})
            
            # 基本資訊
            session_info = track_data.get('session_info', {})
            track_name = session_info.get('track_name', '未知賽道')
            
            print(f"[TRACK_MAP] 賽道數據載入完成: {track_name}")
            print(f"[TRACK_MAP] 位置點數: {len(self.position_records)}")
            print(f"[TRACK_MAP] 賽道邊界: {self.track_bounds}")
            
            # 更新佔位符顯示
            self.placeholder_label.setText(f"賽道地圖\n{track_name}\n{len(self.position_records)} 個位置點")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 載入賽道數據失敗: {e}")
            return False
    
    def draw_track_map(self):
        """繪製賽道地圖 - 佔位符版本"""
        if not self.position_records:
            print("[TRACK_MAP] 沒有位置數據可繪製")
            return
        
        print(f"[TRACK_MAP] 開始繪製賽道地圖 ({len(self.position_records)} 個點)")
        
        # 更新顯示狀態
        self.placeholder_label.setText(f"賽道地圖已載入\n{len(self.position_records)} 個位置點\n(點擊可查看詳細座標)")
        
        # 觸發重繪
        self.update()
    
    def paintEvent(self, event):
        """繪製事件 - 簡化版本"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 如果有數據，繪製簡化的賽道示意圖
        if self.position_records and len(self.position_records) > 1:
            self.draw_simplified_track(painter)
        else:
            # 繪製佔位符
            self.draw_placeholder(painter)
    
    def draw_simplified_track(self, painter):
        """繪製簡化的賽道示意圖"""
        try:
            # 計算顯示範圍
            widget_rect = self.rect()
            map_rect = widget_rect.adjusted(self.margin, self.margin, -self.margin, -self.margin)
            
            if map_rect.width() <= 0 or map_rect.height() <= 0:
                return
            
            # 獲取座標範圍
            x_coords = [record['position_x'] for record in self.position_records]
            y_coords = [record['position_y'] for record in self.position_records]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            x_range = x_max - x_min
            y_range = y_max - y_min
            
            if x_range == 0 or y_range == 0:
                return
            
            # 計算縮放因子
            scale_x = map_rect.width() / x_range
            scale_y = map_rect.height() / y_range
            scale = min(scale_x, scale_y) * 0.9  # 留一些邊距
            
            # 設置繪筆
            track_pen = QPen(QColor(60, 60, 60), 3)
            point_pen = QPen(QColor(255, 0, 0), 2)
            
            # 繪製賽道路線
            painter.setPen(track_pen)
            for i in range(len(self.position_records) - 1):
                current = self.position_records[i]
                next_point = self.position_records[i + 1]
                
                # 轉換座標
                x1 = int(map_rect.left() + (current['position_x'] - x_min) * scale)
                y1 = int(map_rect.top() + (current['position_y'] - y_min) * scale)
                x2 = int(map_rect.left() + (next_point['position_x'] - x_min) * scale)
                y2 = int(map_rect.top() + (next_point['position_y'] - y_min) * scale)
                
                painter.drawLine(x1, y1, x2, y2)
            
            # 繪製起終點
            if self.position_records:
                start_point = self.position_records[0]
                x = int(map_rect.left() + (start_point['position_x'] - x_min) * scale)
                y = int(map_rect.top() + (start_point['position_y'] - y_min) * scale)
                
                painter.setPen(point_pen)
                painter.setBrush(QBrush(QColor(255, 0, 0)))
                painter.drawEllipse(x-4, y-4, 8, 8)
                
                # 起點標籤
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(x+10, y, "START")
            
            # 繪製資訊文字
            info_text = f"賽道位置點: {len(self.position_records)}"
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(QFont("Microsoft YaHei", 9))
            painter.drawText(10, widget_rect.height() - 10, info_text)
            
        except Exception as e:
            print(f"[ERROR] 繪製賽道失敗: {e}")
    
    def draw_placeholder(self, painter):
        """繪製佔位符"""
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        
        rect = self.rect().adjusted(20, 20, -20, -20)
        painter.drawRect(rect)
        
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Microsoft YaHei", 12))
        painter.drawText(rect, Qt.AlignCenter, "賽道地圖\n準備中...")
    
    def mousePressEvent(self, event):
        """滑鼠點擊事件"""
        if event.button() == Qt.LeftButton and self.position_records:
            # 簡化版本：顯示點擊位置的資訊
            click_info = {
                'x': event.x(),
                'y': event.y(),
                'total_points': len(self.position_records)
            }
            print(f"[TRACK_MAP] 點擊位置: {click_info}")
            self.point_clicked.emit(click_info)
    
    def wheelEvent(self, event):
        """滾輪縮放事件 - 佔位符"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        
        # 限制縮放範圍
        self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))
        
        print(f"[TRACK_MAP] 縮放係數: {self.zoom_factor:.2f}")
        self.update()
    
    def on_resize(self):
        """視窗大小調整處理"""
        self.update()
    
    def clear_map(self):
        """清除地圖"""
        self.track_data = None
        self.position_records = []
        self.track_bounds = {}
        self.placeholder_label.setText("賽道地圖\n(準備中...)")
        self.update()
    
    def get_track_info(self):
        """獲取賽道資訊"""
        if not self.track_data:
            return {}
        
        return {
            'position_count': len(self.position_records),
            'track_bounds': self.track_bounds.copy(),
            'has_data': bool(self.position_records)
        }

# 數據處理器佔位符
class TrackDataProcessor:
    """賽道數據處理器 - 佔位符版本"""
    
    def __init__(self):
        pass
    
    def parse_json_data(self, json_file_path):
        """解析JSON數據"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] 解析JSON失敗: {e}")
            return None
    
    def process_coordinates(self, raw_coordinates):
        """處理座標數據 - 佔位符"""
        # 簡單的座標處理
        processed = []
        for coord in raw_coordinates:
            processed.append({
                'x': coord.get('position_x', 0),
                'y': coord.get('position_y', 0),
                'distance': coord.get('distance_m', 0)
            })
        return processed
    
    def calculate_track_features(self, coordinates):
        """計算賽道特徵 - 佔位符"""
        if not coordinates:
            return {}
        
        # 基本統計
        distances = [c.get('distance_m', 0) for c in coordinates]
        return {
            'total_distance': max(distances) if distances else 0,
            'point_count': len(coordinates),
            'avg_distance_interval': (max(distances) - min(distances)) / len(coordinates) if len(coordinates) > 1 else 0
        }

if __name__ == "__main__":
    # 獨立測試
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    widget = TrackMapWidget()
    widget.show()
    widget.resize(600, 400)
    
    sys.exit(app.exec_())
