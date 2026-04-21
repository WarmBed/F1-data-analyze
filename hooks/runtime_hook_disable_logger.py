#!/usr/bin/env python3
"""
PyInstaller Runtime Hook - EXE 模式日誌控制

此 hook 會在 EXE 啟動時控制日誌輸出
設定 F1T_EXE_DISABLE_LOG=0 啟用日誌（除錯模式）
設定 F1T_EXE_DISABLE_LOG=1 禁用日誌（正式發布）
"""

import os
import sys

# 🔒 EXE 模式檢測
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

if IS_EXE_MODE:
    # ✅ 啟用日誌系統（除錯模式）
    os.environ['F1T_EXE_DISABLE_LOG'] = '1'
    
    # 輸出提示訊息
    print("[HOOK] EXE mode: Logging DISABLED for production")
