#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SignalR Recorder Tool - F1 Live Timing 訊號錄製器

用於錄製和解析 F1 Live Timing SignalR 訊號的工具。
為 2026 年改版做準備，在 FP1 時錄製真實數據用於分析和 GUI 開發。

功能:
1. 連接 SignalR 並錄製原始訊號
2. 即時顯示接收的訊號類型和統計
3. 解析已錄製的 JSONL 檔案
4. 匯出解析後的數據

使用方式:
    python signalr_recorder_gui.py

Author: F1T Team
Date: 2025-12-21
"""

import sys
import os

# 確保可以 import 專案模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from tools.signalr_recorder.gui.main_window import SignalRRecorderWindow


def main():
    """主程式入口"""
    # 確保高 DPI 支援
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("F1 SignalR Recorder")
    app.setApplicationVersion("1.0.0")
    
    # 設置深色主題
    app.setStyle("Fusion")
    
    window = SignalRRecorderWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
