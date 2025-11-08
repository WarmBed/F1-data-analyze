#!/usr/bin/env python3
"""
Demo 5: FIA Parts Changes Classification - Dashboard
=====================================================

儀表板綜合版本 - Grid Layout 多區塊

功能特點：
- 左上：統計卡片（總記錄/平均信心度）
- 右上：變更類型圓餅圖
- 左下：賽事分析表格
- 右下：車隊+車手排行

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
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QFrame, QHeaderView, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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


class DashboardApiWorker(QThread):
    """API Worker"""
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url: str, year: int, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.year = year
    
    def run(self):
        try:
            response = requests.post(
                f"{self.base_url}/api/v2/analysis/execute",
                params={"function_id": "29", "year": self.year},
                timeout=30.0
            )
            response.raise_for_status()
            payload = response.json()
            
            if payload.get("success"):
                self.success.emit(payload.get("data", {}))
            else:
                self.failure.emit(payload.get("message", "Failed"))
        except Exception as e:
            self.failure.emit(str(e))


class StatCard(QFrame):
    """統計卡片"""
    def __init__(self, title: str, value: str, color: str = "#3498db", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str):
        """更新數值"""
        self.value_label.setText(value)


class DashboardWidget(QWidget):
    """儀表板 Widget"""
    
    def __init__(self, year: int = 2025, parent=None):
        super().__init__(parent)
        self.year = year
        self._api_base_url = resolve_api_base_url()
        self._api_worker = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel(tr('dashboard_title', 'FIA Parts Classification - Dashboard'))
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # 刷新按鈕
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(tr('refresh', 'Refresh'))
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Grid 佈局
        grid = QGridLayout()
        
        # 左上：統計卡片區域
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        
        self.total_card = StatCard(tr('total_records', 'Total Records'), "0", "#3498db")
        cards_layout.addWidget(self.total_card)
        
        self.avg_conf_card = StatCard(tr('avg_confidence', 'Avg Confidence'), "0.00", "#2ecc71")
        cards_layout.addWidget(self.avg_conf_card)
        
        grid.addWidget(cards_widget, 0, 0)
        
        # 右上：圓餅圖
        if MATPLOTLIB_AVAILABLE:
            self.pie_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 4)))
            grid.addWidget(self.pie_canvas, 0, 1)
        else:
            grid.addWidget(QLabel("Matplotlib not available"), 0, 1)
        
        # 左下：賽事表格
        self.race_table = self.create_table(tr('race_analysis', 'Race Analysis'))
        grid.addWidget(self.race_table, 1, 0)
        
        # 右下：車隊+車手表格
        right_bottom = QWidget()
        rb_layout = QVBoxLayout(right_bottom)
        
        self.team_table = self.create_table(tr('team_ranking', 'Team Ranking'))
        rb_layout.addWidget(self.team_table)
        
        self.driver_table = self.create_table(tr('driver_ranking', 'Driver Ranking'))
        rb_layout.addWidget(self.driver_table)
        
        grid.addWidget(right_bottom, 1, 1)
        
        layout.addLayout(grid)
        
        # 狀態
        self.status_label = QLabel(tr('ready', 'Ready'))
        layout.addWidget(self.status_label)
    
    def create_table(self, title: str) -> QTableWidget:
        """創建表格"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([title, tr('count', 'Count')])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setColumnWidth(1, 60)
        table.setAlternatingRowColors(True)
        table.setMaximumHeight(200)
        return table
    
    def load_data(self):
        """載入數據"""
        self.status_label.setText(tr('loading', '載入中...'))
        
        if self._api_worker and self._api_worker.isRunning():
            return
        
        self._api_worker = DashboardApiWorker(self._api_base_url, self.year, self)
        self._api_worker.success.connect(self.on_data_loaded)
        self._api_worker.failure.connect(self.on_load_error)
        self._api_worker.start()
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功"""
        try:
            records = self._get_records(data)
            
            # 統計卡片
            total = len(records)
            self.total_card.set_value(str(total))
            
            confidences = []
            for r in records:
                # 使用中文欄位
                conf = r.get("分類信心度", r.get("confidence", r.get("confidence_score")))
                if conf is not None:
                    try:
                        confidences.append(float(conf))
                    except:
                        pass
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            self.avg_conf_card.set_value(f"{avg_conf:.2f}")
            
            # 提取統計（使用中文欄位）
            race_stats = {}
            team_stats = {}
            driver_stats = {}
            type_stats = {}
            
            for record in records:
                race = record.get("比賽", record.get("race", record.get("event", "Unknown")))
                team = record.get("車隊", record.get("team", "Unknown"))
                driver = record.get("車手", record.get("driver", "Unknown"))
                change_type = record.get("變更類型", record.get("change_type", record.get("type", "Unknown")))
                
                race_stats[race] = race_stats.get(race, 0) + 1
                team_stats[team] = team_stats.get(team, 0) + 1
                driver_stats[driver] = driver_stats.get(driver, 0) + 1
                type_stats[change_type] = type_stats.get(change_type, 0) + 1
            
            # 更新表格
            self.populate_table(self.race_table, sorted(race_stats.items(), key=lambda x: x[1], reverse=True)[:10])
            self.populate_table(self.team_table, sorted(team_stats.items(), key=lambda x: x[1], reverse=True)[:5])
            self.populate_table(self.driver_table, sorted(driver_stats.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # 繪製圓餅圖
            if MATPLOTLIB_AVAILABLE:
                self.draw_pie_chart(type_stats)
            
            self.status_label.setText(f"✅ {total} {tr('records_loaded', 'records loaded')}")
            
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
    
    def populate_table(self, table: QTableWidget, data: List[tuple]):
        """填充表格"""
        table.setRowCount(len(data))
        
        for row, (name, count) in enumerate(data):
            name_item = QTableWidgetItem(str(name))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, count_item)
    
    def draw_pie_chart(self, data: Dict):
        """繪製圓餅圖"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.pie_canvas.figure.clear()
        ax = self.pie_canvas.figure.add_subplot(111)
        
        labels = list(data.keys())
        values = list(data.values())
        
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title('Change Type Distribution')
        
        self.pie_canvas.figure.tight_layout()
        self.pie_canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWidget(2025)
    window.setWindowTitle("Demo 5: Dashboard")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
