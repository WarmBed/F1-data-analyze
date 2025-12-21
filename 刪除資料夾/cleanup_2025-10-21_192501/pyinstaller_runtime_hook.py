#!/usr/bin/env python3
"""
PyInstaller Runtime Hook - F1T GUI
在 EXE 啟動時自動設置環境變數
"""
import os
import sys

# 設置日誌級別為 DEBUG（確保所有重要日誌都會被記錄）
if 'F1_LOG_LEVEL' not in os.environ:
    os.environ['F1_LOG_LEVEL'] = 'DEBUG'
    print(f"[RUNTIME_HOOK] 已設置 F1_LOG_LEVEL=DEBUG")

# 輸出啟動資訊（僅在控制台模式可見）
if hasattr(sys, '_MEIPASS'):
    print(f"[RUNTIME_HOOK] 運行於打包環境: {sys._MEIPASS}")
    print(f"[RUNTIME_HOOK] 日誌級別: {os.environ.get('F1_LOG_LEVEL', 'INFO')}")
