#!/usr/bin/env python3
"""
PyInstaller Runtime Hook - 設置環境變數
在 EXE 啟動時自動執行
"""

import os
import sys

# 設置日誌等級為 CRITICAL（極度靜默模式）
os.environ['F1_LOG_LEVEL'] = 'CRITICAL'

# 確保 frozen 模式被正確設置
if getattr(sys, 'frozen', False):
    # 設置 PyInstaller 的內部資源路徑
    # _MEIPASS 是 PyInstaller 解壓資源的臨時目錄
    base_path = sys._MEIPASS
    os.environ['F1T_RESOURCE_PATH'] = base_path
    
    # 設置語言配置目錄（使用用戶目錄）
    user_config_dir = os.path.join(os.path.expanduser('~'), '.f1telemetrystation')
    os.makedirs(user_config_dir, exist_ok=True)
    os.environ['F1T_CONFIG_DIR'] = user_config_dir
else:
    # 開發模式
    os.environ['F1_LOG_LEVEL'] = 'INFO'
