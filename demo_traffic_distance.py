#!/usr/bin/env python3
"""
Traffic Distance DEMO
======================

獨立 DEMO：讀取 CLI F127 產生的 JSON 並以表格顯示每位車手的 traffic 統計。

執行方式：
    python demo_traffic_distance.py

預設載入：json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json

Author: F1T Team
Date: 2025-12-23
"""

import sys
from pathlib import Path

# 確保專案根目錄在 Python path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from modules.gui.live_timing.live_timing_modules.traffic_distance import TrafficDistanceWidget


class DemoWindow(QMainWindow):
    """Traffic Distance DEMO 主視窗"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Distance DEMO (F127)")
        self.setMinimumSize(700, 500)

        # 中央 Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Traffic Distance Widget
        self._widget = TrafficDistanceWidget()
        layout.addWidget(self._widget)

        # 設置深色背景
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")

        # 載入預設 JSON
        self._load_default_json()

    def _load_default_json(self):
        default_file = PROJECT_ROOT / "json" / "live_timing_traffic_distance_2025_Abu_Dhabi_R.json"
        if default_file.exists():
            self._widget.load_from_file(default_file)
            print(f"[DEMO] 已載入: {default_file}")
        else:
            print(f"[DEMO] 找不到預設 JSON: {default_file}")
            print("[DEMO] 請先執行 CLI: python f1_analysis_modular_main.py -f 127 -y 2025 -r Abu_Dhabi -s R")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = DemoWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
