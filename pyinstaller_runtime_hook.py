#!/usr/bin/env python3
"""
PyInstaller Runtime Hook - EXE 完全靜默模式
在 EXE 啟動時自動執行，配置完全靜默的日誌系統
"""

import os
import sys

# 🔇 EXE 模式：完全靜默日誌系統
# 設置日誌等級為 CRITICAL（最高等級，實際上不記錄任何內容）
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
    
    # 🔇 禁用所有日誌輸出（EXE 模式專用）
    # 這個環境變數會被 core/logger.py 檢測並使用 NullHandler
    os.environ['F1T_EXE_SILENT_MODE'] = '1'
else:
    # 開發模式（這段不會在 EXE 中執行）
    os.environ['F1_LOG_LEVEL'] = 'INFO'
