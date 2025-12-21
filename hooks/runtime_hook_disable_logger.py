#!/usr/bin/env python3
"""
PyInstaller Runtime Hook - 禁用 EXE 模式下的日誌輸出

此 hook 會在 EXE 啟動時自動設定環境變數 F1T_EXE_DISABLE_LOG=1
從而禁用所有日誌輸出，提升性能並減少檔案 I/O
"""

import os
import sys

# 🔒 EXE 模式檢測
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

if IS_EXE_MODE:
    # ✅ 設定環境變數禁用日誌系統
    os.environ['F1T_EXE_DISABLE_LOG'] = '1'
    
    # 可選：輸出提示訊息（僅開發測試用，正式版可移除）
    # print("[HOOK] EXE mode: Logging disabled for performance")
