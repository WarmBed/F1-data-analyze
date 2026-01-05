#!/usr/bin/env python3
"""
TrafficAnalysisWidget - F1T 流量分析圖表組件
=============================================

提供流量分析的視覺化組件，包括：
1. 超車難度儀表盤
2. 歷年超車數據趨勢圖
3. 賽道難度排名表
4. DRS Train 風險評估面板
5. Track Position Loss 分析面板

Author: F1T Team
Date: 2025-01-05
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QScrollArea, QSizePolicy,
    QProgressBar, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from core.logger import get_logger
from core.gui_i18n import tr

logger = get_logger("traffic_analysis_widget", component="gui")


class DifficultyGauge(QFrame):
    """超車難度儀表盤組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 標題
        title = QLabel(tr("超車難度"))
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 難度分數顯示
        self.score_label = QLabel("--")
        self.score_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        
        # 難度等級
        self.level_label = QLabel(tr("載入中..."))
        self.level_label.setFont(QFont("Arial", 16))
        self.level_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.level_label)
        
        # 進度條（視覺化難度）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)
        
        # 難度說明
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.description_label)
        
    def update_difficulty(self, score: float, level: str, label: str):
        """更新難度顯示"""
        # 更新分數 (0-1 轉為 0-100%)
        percentage = int(score * 100)
        self.score_label.setText(f"{percentage}%")
        
        # 更新等級
        self.level_label.setText(label)
        
        # 更新進度條
        self.progress_bar.setValue(percentage)
        
        # 設置顏色
        if score < 0.3:
            color = "#27ae60"  # 綠色 - 容易
            description = tr("超車相對容易，DRS 區域有效")
        elif score < 0.5:
            color = "#2ecc71"  # 淺綠
            description = tr("中等偏易，需要把握機會")
        elif score < 0.7:
            color = "#f39c12"  # 橙色 - 中等
            description = tr("中等難度，策略和輪胎優勢很重要")
        elif score < 0.85:
            color = "#e74c3c"  # 紅色 - 難
            description = tr("較難超車，建議優先考慮策略超車")
        else:
            color = "#8e44ad"  # 紫色 - 極難
            description = tr("極難超車，賽道位置至關重要")
        
        self.score_label.setStyleSheet(f"color: {color};")
        self.level_label.setStyleSheet(f"color: {color};")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #ecf0f1;
                border-radius: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 10px;
            }}
        """)
        self.description_label.setText(description)


class YearlyOvertakesChart(FigureCanvas):
    """歷年超車數據趨勢圖"""
    
    def __init__(self, parent=None, width=8, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def plot_overtakes(self, yearly_data: Dict[str, int], race: str):
        """繪製歷年超車趨勢圖"""
        self.axes.clear()
        
        if not yearly_data:
            self.axes.text(0.5, 0.5, tr("無數據"), 
                          ha='center', va='center', fontsize=14)
            self.draw()
            return
        
        years = sorted(yearly_data.keys())
        values = [yearly_data[y] for y in years]
        
        # 創建條形圖
        bars = self.axes.bar(years, values, color='#3498db', edgecolor='white', linewidth=1.5)
        
        # 添加數值標籤
        for bar, val in zip(bars, values):
            height = bar.get_height()
            self.axes.annotate(f'{val}',
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 3),
                              textcoords="offset points",
                              ha='center', va='bottom',
                              fontsize=12, fontweight='bold')
        
        # 添加平均線
        avg = sum(values) / len(values) if values else 0
        self.axes.axhline(y=avg, color='#e74c3c', linestyle='--', linewidth=2,
                         label=f'{tr("平均")}: {avg:.1f}')
        
        self.axes.set_xlabel(tr("年份"), fontsize=12)
        self.axes.set_ylabel(tr("超車次數"), fontsize=12)
        self.axes.set_title(f'{race} - {tr("歷年賽道超車統計")}', fontsize=14, fontweight='bold')
        self.axes.legend(loc='upper right')
        
        # 設置網格
        self.axes.grid(True, axis='y', alpha=0.3)
        self.axes.set_axisbelow(True)
        
        self.fig.tight_layout()
        self.draw()


class CircuitDifficultyTable(QTableWidget):
    """賽道難度排名表"""
    
    circuit_selected = pyqtSignal(str)  # 選中賽道信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()
        
    def _setup_table(self):
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            tr("排名"), tr("賽道"), tr("難度分數"), tr("平均超車"), tr("趨勢")
        ])
        
        # 設置列寬
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.setColumnWidth(0, 50)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 100)
        self.setColumnWidth(4, 80)
        
        # 選擇行為
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        # 連接信號
        self.cellClicked.connect(self._on_cell_clicked)
        
    def _on_cell_clicked(self, row, col):
        """處理單元格點擊"""
        race_item = self.item(row, 1)
        if race_item:
            self.circuit_selected.emit(race_item.text())
    
    def populate_table(self, circuits_data: List[Dict[str, Any]]):
        """填充表格數據"""
        self.setRowCount(len(circuits_data))
        
        for row, circuit in enumerate(circuits_data):
            rank = row + 1
            race = circuit.get("race", "Unknown")
            score = circuit.get("difficulty_score", 0.5)
            avg_overtakes = circuit.get("avg_overtakes_per_race", 0)
            trend = circuit.get("trend", "unknown")
            
            # 排名
            rank_item = QTableWidgetItem(str(rank))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 0, rank_item)
            
            # 賽道名稱
            race_item = QTableWidgetItem(race)
            self.setItem(row, 1, race_item)
            
            # 難度分數
            score_item = QTableWidgetItem(f"{score * 100:.0f}%")
            score_item.setTextAlignment(Qt.AlignCenter)
            
            # 設置顏色
            if score > 0.7:
                score_item.setForeground(QColor("#e74c3c"))
            elif score > 0.5:
                score_item.setForeground(QColor("#f39c12"))
            else:
                score_item.setForeground(QColor("#27ae60"))
            
            self.setItem(row, 2, score_item)
            
            # 平均超車
            overtakes_item = QTableWidgetItem(f"{avg_overtakes:.1f}")
            overtakes_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, overtakes_item)
            
            # 趨勢
            trend_symbol = {"increasing": "↑", "decreasing": "↓", "stable": "→"}.get(trend, "?")
            trend_item = QTableWidgetItem(trend_symbol)
            trend_item.setTextAlignment(Qt.AlignCenter)
            
            if trend == "increasing":
                trend_item.setForeground(QColor("#27ae60"))
            elif trend == "decreasing":
                trend_item.setForeground(QColor("#e74c3c"))
            
            self.setItem(row, 4, trend_item)


class DRSTrainPanel(QGroupBox):
    """DRS Train 風險評估面板"""
    
    calculate_requested = pyqtSignal(int, float)  # (位置, 速度差)
    
    def __init__(self, parent=None):
        super().__init__(tr("DRS Train 風險評估"), parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QGridLayout(self)
        
        # 位置輸入
        layout.addWidget(QLabel(tr("當前位置:")), 0, 0)
        self.position_spin = QSpinBox()
        self.position_spin.setRange(1, 20)
        self.position_spin.setValue(5)
        layout.addWidget(self.position_spin, 0, 1)
        
        # 與前車速度差
        layout.addWidget(QLabel(tr("與前車速度差 (秒/圈):")), 1, 0)
        self.pace_delta_spin = QDoubleSpinBox()
        self.pace_delta_spin.setRange(-2.0, 2.0)
        self.pace_delta_spin.setSingleStep(0.1)
        self.pace_delta_spin.setValue(0.2)
        layout.addWidget(self.pace_delta_spin, 1, 1)
        
        # 計算按鈕
        self.calculate_btn = QPushButton(tr("計算風險"))
        self.calculate_btn.clicked.connect(self._on_calculate)
        layout.addWidget(self.calculate_btn, 2, 0, 1, 2)
        
        # 結果顯示區域
        self.result_frame = QFrame()
        self.result_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        result_layout = QVBoxLayout(self.result_frame)
        
        self.risk_label = QLabel(tr("風險等級: --"))
        self.risk_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_layout.addWidget(self.risk_label)
        
        self.time_loss_label = QLabel(tr("預估時間損失: --"))
        result_layout.addWidget(self.time_loss_label)
        
        self.recommendation_label = QLabel("")
        self.recommendation_label.setWordWrap(True)
        result_layout.addWidget(self.recommendation_label)
        
        layout.addWidget(self.result_frame, 3, 0, 1, 2)
        
    def _on_calculate(self):
        """觸發計算"""
        self.calculate_requested.emit(
            self.position_spin.value(),
            self.pace_delta_spin.value()
        )
    
    def display_result(self, result: Dict[str, Any]):
        """顯示計算結果"""
        risk = result.get("drs_train_risk", 0)
        risk_level = result.get("risk_level", tr("未知"))
        time_loss = result.get("estimated_time_loss_per_lap", 0)
        recommendation = result.get("recommendation", "")
        
        # 設置風險等級顏色
        if risk > 0.7:
            color = "#e74c3c"
        elif risk > 0.5:
            color = "#f39c12"
        else:
            color = "#27ae60"
        
        self.risk_label.setText(f'{tr("風險等級")}: {risk_level} ({risk*100:.0f}%)')
        self.risk_label.setStyleSheet(f"color: {color};")
        
        self.time_loss_label.setText(
            f'{tr("預估時間損失")}: {time_loss:.2f} {tr("秒/圈")}'
        )
        
        self.recommendation_label.setText(f'{tr("建議")}: {recommendation}')


class TrackPositionLossPanel(QGroupBox):
    """Track Position Loss 分析面板"""
    
    calculate_requested = pyqtSignal(int, int, float, float)  # (圈數, 位置, 進站時間, 交通密度)
    
    def __init__(self, parent=None):
        super().__init__(tr("進站位置損失分析"), parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QGridLayout(self)
        
        # 進站圈數
        layout.addWidget(QLabel(tr("進站圈數:")), 0, 0)
        self.pit_lap_spin = QSpinBox()
        self.pit_lap_spin.setRange(1, 70)
        self.pit_lap_spin.setValue(20)
        layout.addWidget(self.pit_lap_spin, 0, 1)
        
        # 進站前位置
        layout.addWidget(QLabel(tr("進站前位置:")), 1, 0)
        self.position_spin = QSpinBox()
        self.position_spin.setRange(1, 20)
        self.position_spin.setValue(5)
        layout.addWidget(self.position_spin, 1, 1)
        
        # 進站時間
        layout.addWidget(QLabel(tr("進站時間 (秒):")), 2, 0)
        self.pit_time_spin = QDoubleSpinBox()
        self.pit_time_spin.setRange(18.0, 30.0)
        self.pit_time_spin.setSingleStep(0.5)
        self.pit_time_spin.setValue(22.0)
        layout.addWidget(self.pit_time_spin, 2, 1)
        
        # 交通密度
        layout.addWidget(QLabel(tr("交通密度:")), 3, 0)
        self.traffic_combo = QComboBox()
        self.traffic_combo.addItems([
            tr("低 (分散)"),
            tr("中等"),
            tr("高 (擁擠)")
        ])
        self.traffic_combo.setCurrentIndex(1)
        layout.addWidget(self.traffic_combo, 3, 1)
        
        # 計算按鈕
        self.calculate_btn = QPushButton(tr("計算位置損失"))
        self.calculate_btn.clicked.connect(self._on_calculate)
        layout.addWidget(self.calculate_btn, 4, 0, 1, 2)
        
        # 結果顯示區域
        self.result_frame = QFrame()
        self.result_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        result_layout = QVBoxLayout(self.result_frame)
        
        self.loss_label = QLabel(tr("預估損失位置: --"))
        self.loss_label.setFont(QFont("Arial", 12, QFont.Bold))
        result_layout.addWidget(self.loss_label)
        
        self.recovery_label = QLabel(tr("回補圈數: --"))
        result_layout.addWidget(self.recovery_label)
        
        self.undercut_label = QLabel(tr("Undercut 潛力: --"))
        result_layout.addWidget(self.undercut_label)
        
        self.overcut_label = QLabel(tr("Overcut 潛力: --"))
        result_layout.addWidget(self.overcut_label)
        
        self.recommendation_label = QLabel("")
        self.recommendation_label.setWordWrap(True)
        result_layout.addWidget(self.recommendation_label)
        
        layout.addWidget(self.result_frame, 5, 0, 1, 2)
        
    def _on_calculate(self):
        """觸發計算"""
        traffic_map = {0: 0.3, 1: 0.5, 2: 0.8}
        traffic = traffic_map.get(self.traffic_combo.currentIndex(), 0.5)
        
        self.calculate_requested.emit(
            self.pit_lap_spin.value(),
            self.position_spin.value(),
            self.pit_time_spin.value(),
            traffic
        )
    
    def display_result(self, result: Dict[str, Any]):
        """顯示計算結果"""
        loss = result.get("estimated_positions_lost", 0)
        recovery_laps = result.get("laps_to_recover", 0)
        undercut = result.get("undercut_potential", "")
        overcut = result.get("overcut_potential", "")
        recommendation = result.get("recommendation", "")
        
        self.loss_label.setText(f'{tr("預估損失位置")}: {loss:.1f} {tr("位")}')
        self.recovery_label.setText(f'{tr("回補圈數")}: {recovery_laps:.1f} {tr("圈")}')
        self.undercut_label.setText(f'Undercut: {undercut}')
        self.overcut_label.setText(f'Overcut: {overcut}')
        self.recommendation_label.setText(f'{tr("建議")}: {recommendation}')


class TrafficAnalysisWidget(QWidget):
    """流量分析主組件"""
    
    # 信號
    circuit_changed = pyqtSignal(str)
    analysis_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_race = None
        self._data_loader = None
        self._setup_ui()
        
    def _setup_ui(self):
        """設置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 頂部：賽道選擇
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(tr("選擇賽道:")))
        
        self.circuit_combo = QComboBox()
        self.circuit_combo.addItems([
            "Abu Dhabi", "Australia", "Austria", "Azerbaijan", "Bahrain",
            "Belgium", "Brazil", "Canada", "China", "Emilia Romagna",
            "Great Britain", "Hungary", "Italy", "Japan", "Las Vegas",
            "Mexico", "Miami", "Monaco", "Netherlands", "Qatar",
            "Saudi Arabia", "Singapore", "Spain", "United States"
        ])
        self.circuit_combo.currentTextChanged.connect(self._on_circuit_changed)
        top_layout.addWidget(self.circuit_combo)
        
        self.analyze_btn = QPushButton(tr("分析"))
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        top_layout.addWidget(self.analyze_btn)
        
        top_layout.addStretch()
        main_layout.addLayout(top_layout)
        
        # 主要內容區域（可滾動）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側：難度儀表盤和趨勢圖
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.difficulty_gauge = DifficultyGauge()
        left_layout.addWidget(self.difficulty_gauge)
        
        self.yearly_chart = YearlyOvertakesChart(width=6, height=3)
        left_layout.addWidget(self.yearly_chart)
        
        splitter.addWidget(left_widget)
        
        # 右側：分析面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.drs_panel = DRSTrainPanel()
        right_layout.addWidget(self.drs_panel)
        
        self.position_loss_panel = TrackPositionLossPanel()
        right_layout.addWidget(self.position_loss_panel)
        
        right_layout.addStretch()
        
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 400])
        
        scroll_layout.addWidget(splitter)
        
        # 底部：賽道排名表
        ranking_group = QGroupBox(tr("全部賽道超車難度排名"))
        ranking_layout = QVBoxLayout(ranking_group)
        
        self.ranking_table = CircuitDifficultyTable()
        self.ranking_table.circuit_selected.connect(self._on_circuit_selected)
        ranking_layout.addWidget(self.ranking_table)
        
        scroll_layout.addWidget(ranking_group)
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
    def set_data_loader(self, loader):
        """設置數據載入器"""
        self._data_loader = loader
        
        # 連接信號
        self.drs_panel.calculate_requested.connect(self._calculate_drs_risk)
        self.position_loss_panel.calculate_requested.connect(self._calculate_position_loss)
        
    def _on_circuit_changed(self, circuit: str):
        """賽道變更處理"""
        self._current_race = circuit
        self.circuit_changed.emit(circuit)
        
    def _on_circuit_selected(self, circuit: str):
        """從排名表選擇賽道"""
        self.circuit_combo.setCurrentText(circuit)
        self._on_analyze_clicked()
        
    def _on_analyze_clicked(self):
        """分析按鈕點擊"""
        race = self.circuit_combo.currentText()
        if race and self._data_loader:
            self.analyze_circuit(race)
            self.analysis_requested.emit(race)
            
    def analyze_circuit(self, race: str):
        """分析指定賽道"""
        if not self._data_loader:
            logger.warning("[TRAFFIC_WIDGET] %s", tr("數據載入器未設置"))
            return
        
        self._current_race = race
        
        # 計算超車難度
        difficulty = self._data_loader.calculate_overtaking_difficulty(race)
        
        # 更新儀表盤
        self.difficulty_gauge.update_difficulty(
            difficulty.get("difficulty_score", 0.5),
            difficulty.get("difficulty_level", "MODERATE"),
            difficulty.get("difficulty_label", tr("中等難度"))
        )
        
        # 更新趨勢圖
        yearly_data = difficulty.get("yearly_overtakes", {})
        self.yearly_chart.plot_overtakes(yearly_data, race)
        
    def populate_ranking_table(self, circuits_data: List[Dict[str, Any]]):
        """填充排名表"""
        self.ranking_table.populate_table(circuits_data)
        
    def _calculate_drs_risk(self, position: int, pace_delta: float):
        """計算 DRS Train 風險"""
        if not self._data_loader or not self._current_race:
            return
        
        result = self._data_loader.get_drs_train_risk(
            self._current_race, position, pace_delta
        )
        self.drs_panel.display_result(result)
        
    def _calculate_position_loss(self, pit_lap: int, position: int, 
                                  pit_time: float, traffic: float):
        """計算進站位置損失"""
        if not self._data_loader or not self._current_race:
            return
        
        result = self._data_loader.get_track_position_loss(
            self._current_race, pit_lap, position, pit_time, traffic
        )
        self.position_loss_panel.display_result(result)
