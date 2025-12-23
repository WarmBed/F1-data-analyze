#!/usr/bin/env python3
"""
F101 起跑反應分析 Widget
Start Reaction Analysis Widget

顯示起跑反應分析結果：
- 0-10 km/h 離合器反應條形圖
- 0-20 km/h 起步反應條形圖
- 首圈位置變化表格
- 綜合排名表格

作者: F1T Team
日期: 2025-12-22
"""

from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QGroupBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from core.gui_i18n import tr

import logging
logger = logging.getLogger(__name__)


# F1 車隊顏色
TEAM_COLORS = {
    'VER': '#3671C6', 'NOR': '#FF8000', 'PIA': '#FF8000',
    'LEC': '#E8002D', 'SAI': '#E8002D', 'HAM': '#27F4D2', 
    'RUS': '#27F4D2', 'ALO': '#229971', 'STR': '#229971',
    'GAS': '#FF87BC', 'OCO': '#FF87BC', 'TSU': '#6692FF',
    'RIC': '#6692FF', 'ALB': '#1868DB', 'COL': '#1868DB',
    'HUL': '#B6BABD', 'BEA': '#52E252', 'DOO': '#52E252',
    'HAD': '#B6BABD', 'ANT': '#52E252',
}


class StartReactionWidget(QWidget):
    """
    起跑反應分析顯示元件
    """
    
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self._setup_ui()
    
    def _setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 創建標籤頁
        self.tab_widget = QTabWidget()
        
        # Tab 1: 起跑反應速度（第二批次速度）
        self.reaction_tab = QWidget()
        self._setup_reaction_tab()
        self.tab_widget.addTab(self.reaction_tab, tr("reaction_speed", "Reaction Speed"))
        
        # Tab 2: 加速時間圖表 (0-10, 0-20)
        self.accel_tab = QWidget()
        self._setup_accel_tab()
        self.tab_widget.addTab(self.accel_tab, tr("acceleration_chart", "Acceleration Chart"))
        
        # Tab 3: 首圈位置變化
        self.position_tab = QWidget()
        self._setup_position_tab()
        self.tab_widget.addTab(self.position_tab, tr("position_changes", "Position Changes"))
        
        # Tab 4: 綜合排名
        self.ranking_tab = QWidget()
        self._setup_ranking_tab()
        self.tab_widget.addTab(self.ranking_tab, tr("combined_ranking", "Combined Ranking"))
        
        layout.addWidget(self.tab_widget)
    
    def _setup_reaction_tab(self):
        """設置起跑反應速度標籤頁"""
        layout = QVBoxLayout(self.reaction_tab)
        
        # 標題說明
        self.reaction_label = QLabel("<b>Reaction Speed at ~2s after green light (higher = faster reaction)</b>")
        layout.addWidget(self.reaction_label)
        
        # 圖表
        self.fig_reaction = Figure(figsize=(12, 8), dpi=100)
        self.canvas_reaction = FigureCanvas(self.fig_reaction)
        layout.addWidget(self.canvas_reaction)
    
    def _setup_accel_tab(self):
        """設置加速時間圖表標籤頁"""
        layout = QVBoxLayout(self.accel_tab)
        
        # 使用 Splitter 分割兩個圖表
        splitter = QSplitter(Qt.Horizontal)
        
        # 0-10 km/h 圖表 (離合器反應)
        self.fig_t10 = Figure(figsize=(6, 8), dpi=100)
        self.canvas_t10 = FigureCanvas(self.fig_t10)
        frame_t10 = QFrame()
        frame_t10.setFrameStyle(QFrame.Box | QFrame.Sunken)
        frame_layout_10 = QVBoxLayout(frame_t10)
        frame_layout_10.addWidget(QLabel("<b>0-10 km/h (Clutch Reaction)</b>"))
        frame_layout_10.addWidget(self.canvas_t10)
        splitter.addWidget(frame_t10)
        
        # 0-20 km/h 圖表 (起步反應)
        self.fig_t20 = Figure(figsize=(6, 8), dpi=100)
        self.canvas_t20 = FigureCanvas(self.fig_t20)
        frame_t20 = QFrame()
        frame_t20.setFrameStyle(QFrame.Box | QFrame.Sunken)
        frame_layout_20 = QVBoxLayout(frame_t20)
        frame_layout_20.addWidget(QLabel("<b>0-20 km/h (Start Reaction)</b>"))
        frame_layout_20.addWidget(self.canvas_t20)
        splitter.addWidget(frame_t20)
        
        layout.addWidget(splitter)
    
    def _setup_position_tab(self):
        """設置首圈位置變化標籤頁"""
        layout = QVBoxLayout(self.position_tab)
        
        # 位置變化表格
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(5)
        self.position_table.setHorizontalHeaderLabels([
            tr("driver", "Driver"),
            tr("grid", "Grid"),
            tr("lap1_end", "Lap 1 End"),
            tr("delta", "Delta"),
            tr("visual", "Visual")
        ])
        
        header = self.position_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.position_table)
    
    def _setup_ranking_tab(self):
        """設置綜合排名標籤頁"""
        layout = QVBoxLayout(self.ranking_tab)
        
        # 綜合排名表格
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(7)
        self.ranking_table.setHorizontalHeaderLabels([
            tr("rank", "Rank"),
            tr("driver", "Driver"),
            tr("reaction", "Reaction"),
            tr("t10", "0-10 km/h"),
            tr("t20", "0-20 km/h"),
            tr("position", "Pos Change"),
            tr("score", "Score")
        ])
        
        header = self.ranking_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.ranking_table)
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新顯示數據
        
        Args:
            data: 分析結果數據
        """
        self._data = data
        
        logger.debug(f"[START_REACTION_WIDGET] Updating with data keys: {data.keys() if data else 'None'}")
        
        if not data:
            return
        
        # 更新起跑反應速度圖表
        self._update_reaction_chart(data)
        
        # 更新加速時間圖表
        self._update_accel_charts(data)
        
        # 更新位置變化表格
        self._update_position_table(data)
        
        # 更新綜合排名
        self._update_ranking_table(data)
        
        self.data_updated.emit(data)
    
    def _update_reaction_chart(self, data: Dict[str, Any]):
        """更新起跑反應速度圖表"""
        drivers = data.get('drivers', [])
        batch_time = data.get('reaction_batch_time', 0)
        
        if not drivers:
            return
        
        # 準備數據 - 按 reaction_speed 排序（高到低）
        reaction_data = [(d['name'], d.get('reaction_speed', 0)) for d in drivers if d.get('reaction_speed', 0) > 0]
        reaction_data.sort(key=lambda x: -x[1])  # 速度高的在前
        
        self.fig_reaction.clear()
        ax = self.fig_reaction.add_subplot(111)
        
        names = [d[0] for d in reaction_data]
        speeds = [d[1] for d in reaction_data]
        colors = [TEAM_COLORS.get(n, '#888888') for n in names]
        
        bars = ax.barh(range(len(names)), speeds, color=colors, edgecolor='white', linewidth=0.5)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names)
        ax.set_xlabel('Speed (km/h)')
        ax.set_title(f'Reaction Speed at t={batch_time:.2f}s after green light\n(Higher = Faster Reaction)')
        ax.invert_yaxis()
        
        # 添加數值標籤
        for bar, speed in zip(bars, speeds):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{speed} km/h', va='center', fontsize=9)
        
        # 標記最快和最慢
        if speeds:
            ax.axvline(x=max(speeds), color='green', linestyle='--', alpha=0.5, label='Fastest')
            ax.axvline(x=min(speeds), color='red', linestyle='--', alpha=0.5, label='Slowest')
        
        self.fig_reaction.tight_layout()
        self.canvas_reaction.draw()
        
        # 更新標籤
        self.reaction_label.setText(
            f"<b>Reaction Speed at t={batch_time:.2f}s after green light</b><br>"
            f"Fastest: {names[0]} ({speeds[0]} km/h) | "
            f"Slowest: {names[-1]} ({speeds[-1]} km/h) | "
            f"Gap: {speeds[0] - speeds[-1]} km/h"
        )
    
    def _update_accel_charts(self, data: Dict[str, Any]):
        """更新加速時間圖表"""
        drivers = data.get('drivers', [])
        
        if not drivers:
            return
        
        # 準備數據 - 使用 t10 (0-10 km/h) 和 t20 (0-20 km/h)
        t10_data = [(d['name'], d['t10']) for d in drivers if d.get('t10')]
        t20_data = [(d['name'], d['t20']) for d in drivers if d.get('t20')]
        
        # 排序
        t10_data.sort(key=lambda x: x[1])
        t20_data.sort(key=lambda x: x[1])
        
        # 繪製 0-10 km/h (離合器反應)
        self.fig_t10.clear()
        ax1 = self.fig_t10.add_subplot(111)
        
        names_10 = [d[0] for d in t10_data]
        times_10 = [d[1] for d in t10_data]
        colors_10 = [TEAM_COLORS.get(n, '#888888') for n in names_10]
        
        bars1 = ax1.barh(names_10, times_10, color=colors_10, edgecolor='white', linewidth=0.5)
        ax1.set_xlabel('Time (s)')
        ax1.set_title('0-10 km/h Clutch Reaction Time')
        ax1.invert_yaxis()
        
        # 添加數值標籤
        for bar, time in zip(bars1, times_10):
            ax1.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{time:.3f}s', va='center', fontsize=8)
        
        self.fig_t10.tight_layout()
        self.canvas_t10.draw()
        
        # 繪製 0-20 km/h (起步反應)
        self.fig_t20.clear()
        ax2 = self.fig_t20.add_subplot(111)
        
        names_20 = [d[0] for d in t20_data]
        times_20 = [d[1] for d in t20_data]
        colors_20 = [TEAM_COLORS.get(n, '#888888') for n in names_20]
        
        bars2 = ax2.barh(names_20, times_20, color=colors_20, edgecolor='white', linewidth=0.5)
        ax2.set_xlabel('Time (s)')
        ax2.set_title('0-20 km/h Start Reaction Time')
        ax2.invert_yaxis()
        
        for bar, time in zip(bars2, times_20):
            ax2.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{time:.3f}s', va='center', fontsize=8)
        
        self.fig_t20.tight_layout()
        self.canvas_t20.draw()
    
    def _update_position_table(self, data: Dict[str, Any]):
        """更新首圈位置變化表格"""
        drivers = data.get('drivers', [])
        
        # 按 grid 排序
        sorted_drivers = sorted(drivers, key=lambda d: d.get('grid', 99))
        
        self.position_table.setRowCount(len(sorted_drivers))
        
        for row, driver in enumerate(sorted_drivers):
            name = driver.get('name', '?')
            grid = driver.get('grid')
            lap1 = driver.get('lap1_pos')
            delta = driver.get('position_delta', 0)
            
            # 車手名稱 (帶顏色)
            name_item = QTableWidgetItem(name)
            color = TEAM_COLORS.get(name, '#888888')
            name_item.setBackground(QColor(color))
            name_item.setForeground(QColor('white'))
            self.position_table.setItem(row, 0, name_item)
            
            # Grid
            grid_item = QTableWidgetItem(f'P{grid}' if grid else '-')
            grid_item.setTextAlignment(Qt.AlignCenter)
            self.position_table.setItem(row, 1, grid_item)
            
            # Lap 1 End
            lap1_item = QTableWidgetItem(f'P{lap1}' if lap1 else '-')
            lap1_item.setTextAlignment(Qt.AlignCenter)
            self.position_table.setItem(row, 2, lap1_item)
            
            # Delta
            if delta > 0:
                delta_text = f'+{delta}'
                delta_color = QColor('#00AA00')
            elif delta < 0:
                delta_text = str(delta)
                delta_color = QColor('#CC0000')
            else:
                delta_text = '0'
                delta_color = QColor('#666666')
            
            delta_item = QTableWidgetItem(delta_text)
            delta_item.setTextAlignment(Qt.AlignCenter)
            delta_item.setForeground(delta_color)
            font = delta_item.font()
            font.setBold(True)
            delta_item.setFont(font)
            self.position_table.setItem(row, 3, delta_item)
            
            # Visual
            if delta > 0:
                visual = '+' * delta + '>'
            elif delta < 0:
                visual = '<' + '-' * abs(delta)
            else:
                visual = '='
            
            visual_item = QTableWidgetItem(visual)
            visual_item.setTextAlignment(Qt.AlignCenter)
            visual_item.setForeground(delta_color)
            self.position_table.setItem(row, 4, visual_item)
    
    def _update_ranking_table(self, data: Dict[str, Any]):
        """更新綜合排名表格"""
        drivers = data.get('drivers', [])
        
        # 計算綜合分數並排序
        ranked = []
        
        # 找出最大/最小值用於計算分數
        t10_values = [d['t10'] for d in drivers if d.get('t10')]
        t20_values = [d['t20'] for d in drivers if d.get('t20')]
        reaction_values = [d['reaction_speed'] for d in drivers if d.get('reaction_speed', 0) > 0]
        
        if not t10_values or not t20_values or not reaction_values:
            return
        
        min_t10, max_t10 = min(t10_values), max(t10_values)
        min_t20, max_t20 = min(t20_values), max(t20_values)
        min_reaction, max_reaction = min(reaction_values), max(reaction_values)
        
        for driver in drivers:
            t10 = driver.get('t10')
            t20 = driver.get('t20')
            reaction = driver.get('reaction_speed', 0)
            delta = driver.get('position_delta', 0)
            
            if t10 and t20 and reaction > 0:
                # 計算分數
                # reaction_speed 佔 30 分（速度越高分數越高）
                reaction_score = (reaction - min_reaction) / (max_reaction - min_reaction) * 30 if max_reaction != min_reaction else 15
                # t10 離合器反應佔 25 分（時間越短分數越高）
                clutch_score = (max_t10 - t10) / (max_t10 - min_t10) * 25 if max_t10 != min_t10 else 12.5
                # t20 起步反應佔 25 分（時間越短分數越高）
                start_score = (max_t20 - t20) / (max_t20 - min_t20) * 25 if max_t20 != min_t20 else 12.5
                # 位置變化佔 20 分
                position_score = max(0, min(20, delta * 5 + 10))
                total = reaction_score + clutch_score + start_score + position_score
                
                ranked.append({
                    'name': driver['name'],
                    'reaction': reaction,
                    't10': t10,
                    't20': t20,
                    'delta': delta,
                    'score': total
                })
        
        # 按分數排序
        ranked.sort(key=lambda x: -x['score'])
        
        self.ranking_table.setRowCount(len(ranked))
        
        for row, driver in enumerate(ranked):
            # Rank
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            if row < 3:
                font = rank_item.font()
                font.setBold(True)
                rank_item.setFont(font)
            self.ranking_table.setItem(row, 0, rank_item)
            
            # Driver
            name_item = QTableWidgetItem(driver['name'])
            color = TEAM_COLORS.get(driver['name'], '#888888')
            name_item.setBackground(QColor(color))
            name_item.setForeground(QColor('white'))
            self.ranking_table.setItem(row, 1, name_item)
            
            # Reaction Speed
            reaction_item = QTableWidgetItem(f"{driver['reaction']} km/h")
            reaction_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 2, reaction_item)
            
            # 0-10 km/h
            t10_item = QTableWidgetItem(f"{driver['t10']:.3f}s")
            t10_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 3, t10_item)
            
            # 0-20 km/h
            t20_item = QTableWidgetItem(f"{driver['t20']:.3f}s")
            t20_item.setTextAlignment(Qt.AlignCenter)
            self.ranking_table.setItem(row, 4, t20_item)
            
            # Position
            delta = driver['delta']
            if delta > 0:
                pos_text = f'+{delta}'
                pos_color = QColor('#00AA00')
            elif delta < 0:
                pos_text = str(delta)
                pos_color = QColor('#CC0000')
            else:
                pos_text = '0'
                pos_color = QColor('#666666')
            
            pos_item = QTableWidgetItem(pos_text)
            pos_item.setTextAlignment(Qt.AlignCenter)
            pos_item.setForeground(pos_color)
            self.ranking_table.setItem(row, 5, pos_item)
            
            # Score
            score_item = QTableWidgetItem(f"{driver['score']:.1f}")
            score_item.setTextAlignment(Qt.AlignCenter)
            if row < 3:
                font = score_item.font()
                font.setBold(True)
                score_item.setFont(font)
            self.ranking_table.setItem(row, 6, score_item)
    
    def clear(self):
        """清空顯示"""
        self._data = None
        self.fig_reaction.clear()
        self.fig_t10.clear()
        self.fig_t20.clear()
        self.canvas_reaction.draw()
        self.canvas_t10.draw()
        self.canvas_t20.draw()
        self.position_table.setRowCount(0)
        self.ranking_table.setRowCount(0)
