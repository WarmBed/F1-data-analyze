#!/usr/bin/env python3
"""
Demo 2: FIA Parts Changes Classification - Chart Focus
=======================================================

圖表展示版本 - 多圖表視覺化

功能特點：
- 賽事分析長條圖
- 車隊排行長條圖
- 車手排行長條圖
- 變更類型圓餅圖

Author: F1T Team
Date: 2025-11-07
"""

import sys
import os

# 添加專案根目錄到 Python 路徑（用於獨立執行）
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from typing import Dict, List, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import requests

from core.gui_i18n import tr
from core.api_base_url import resolve_api_base_url

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ChartFocusApiWorker(QThread):
    """API Worker"""
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url: str, year: int, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.year = year
    
    def run(self):
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            response = requests.post(
                f"{self.base_url}/api/v2/analysis/execute",
                params={"function_id": "29", "year": self.year},
                timeout=30.0
            )
            # ✅ 中斷檢查點 2: HTTP 請求後
            if self.isInterruptionRequested():
                return
            response.raise_for_status()
            payload = response.json()
            if payload.get("success"):
                if self.isInterruptionRequested():
                    return
                self.success.emit(payload.get("data", {}))
            else:
                if self.isInterruptionRequested():
                    return
                self.failure.emit(payload.get("message", "Failed"))
        except Exception as e:
            if self.isInterruptionRequested():
                return
            self.failure.emit(str(e))


class ChartCanvas(FigureCanvasQTAgg):
    """Matplotlib 圖表畫布"""
    def __init__(self, parent=None, width=5, height=4):
        self.fig = Figure(figsize=(width, height))
        super().__init__(self.fig)


class ChartFocusWidget(QWidget):
    """圖表展示 Widget"""
    
    def __init__(self, year: int = 2025, parent=None):
        super().__init__(parent)
        self.year = year
        self._api_base_url = resolve_api_base_url()
        self._api_worker = None
        
        self.setup_ui()
        
        if MATPLOTLIB_AVAILABLE:
            self.load_data()
        else:
            self.status_label.setText("❌ Matplotlib 未安裝")
    
    def setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel(tr('chart_focus_title', 'FIA Parts Classification - Chart Focus'))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 刷新按鈕
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(tr('refresh', 'Refresh'))
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 滾動區域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.charts_layout = QVBoxLayout(scroll_widget)
        
        if MATPLOTLIB_AVAILABLE:
            # 創建4個圖表
            self.race_chart = ChartCanvas(self, width=8, height=4)
            self.team_chart = ChartCanvas(self, width=8, height=4)
            self.driver_chart = ChartCanvas(self, width=8, height=4)
            self.type_chart = ChartCanvas(self, width=6, height=6)
            
            self.charts_layout.addWidget(QLabel(tr('race_analysis', 'Race Analysis')))
            self.charts_layout.addWidget(self.race_chart)
            self.charts_layout.addWidget(QLabel(tr('team_ranking', 'Team Ranking')))
            self.charts_layout.addWidget(self.team_chart)
            self.charts_layout.addWidget(QLabel(tr('driver_ranking', 'Driver Ranking')))
            self.charts_layout.addWidget(self.driver_chart)
            self.charts_layout.addWidget(QLabel(tr('type_distribution', 'Type Distribution')))
            self.charts_layout.addWidget(self.type_chart)
        else:
            self.charts_layout.addWidget(QLabel("Matplotlib not available"))
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # 狀態
        self.status_label = QLabel(tr('ready', 'Ready'))
        layout.addWidget(self.status_label)
    
    def load_data(self):
        """載入數據"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.status_label.setText(tr('loading', '載入中...'))
        
        if self._api_worker and self._api_worker.isRunning():
            return
        
        self._api_worker = ChartFocusApiWorker(self._api_base_url, self.year, self)
        self._api_worker.success.connect(self.on_data_loaded)
        self._api_worker.failure.connect(self.on_load_error)
        self._api_worker.start()
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功"""
        try:
            records = self._get_records(data)
            
            # 提取統計
            race_stats = {}
            team_stats = {}
            driver_stats = {}
            type_stats = {}
            
            for record in records:
                # 使用中文 API 欄位
                race = record.get("比賽", record.get("race", record.get("event", "Unknown")))
                team = record.get("車隊", record.get("team", "Unknown"))
                driver = record.get("車手", record.get("driver", "Unknown"))
                change_type = record.get("變更類型", record.get("change_type", record.get("type", "Unknown")))
                
                race_stats[race] = race_stats.get(race, 0) + 1
                team_stats[team] = team_stats.get(team, 0) + 1
                driver_stats[driver] = driver_stats.get(driver, 0) + 1
                type_stats[change_type] = type_stats.get(change_type, 0) + 1
            
            # 繪製圖表
            self.draw_bar_chart(self.race_chart, race_stats, "Race Analysis", top_n=10)
            self.draw_bar_chart(self.team_chart, team_stats, "Team Ranking", top_n=10)
            self.draw_bar_chart(self.driver_chart, driver_stats, "Driver Ranking", top_n=10)
            self.draw_pie_chart(self.type_chart, type_stats, "Change Type Distribution")
            
            self.status_label.setText(tr('loaded_successfully', '✅ 載入成功'))
            
        except Exception as e:
            self.on_load_error(str(e))
    
    def on_load_error(self, error: str):
        """載入失敗"""
        self.status_label.setText(f"❌ {error}")
    
    def _get_records(self, data: Dict) -> List[Dict]:
        """提取記錄"""
        for key in ["records", "changes", "parts_changes"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        return data if isinstance(data, list) else []
    
    def draw_bar_chart(self, canvas: ChartCanvas, data: Dict, title: str, top_n: int = 10):
        """繪製長條圖"""
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)
        
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:top_n]
        names = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        
        ax.barh(names, values, color='#3498db')
        ax.set_xlabel('Count')
        ax.set_title(title)
        ax.invert_yaxis()
        
        canvas.fig.tight_layout()
        canvas.draw()
    
    def draw_pie_chart(self, canvas: ChartCanvas, data: Dict, title: str):
        """繪製圓餅圖"""
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)
        
        labels = list(data.keys())
        values = list(data.values())
        
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title(title)
        
        canvas.fig.tight_layout()
        canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChartFocusWidget(2025)
    window.setWindowTitle("Demo 2: Chart Focus")
    window.resize(900, 1000)
    window.show()
    sys.exit(app.exec_())
