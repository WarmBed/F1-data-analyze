#!/usr/bin/env python3
"""
F1T NSSM 服務監控 - 性能優化啟動腳本
使用 .pyw 無控制台模式啟動，適合後台運行

性能優化特性:
- 單例模式共享資源
- 智能緩存機制  
- 減少系統調用頻率
- 15秒刷新間隔
"""

import sys
import os
from pathlib import Path

# 設定 Python 路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 設定環境變數優化性能
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['QT_SCALE_FACTOR'] = '1.0'  # 防止 DPI 縮放問題

try:
    # 導入並啟動 GUI
    from nssm_monitor_gui import main
    
    # Windows 性能優化
    if sys.platform == 'win32':
        import ctypes
        # 設定進程優先級為正常
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(), 0x00000020
        )
    
    # 啟動應用程式
    main()
    
except Exception as e:
    # 錯誤處理 - 寫入日誌檔案
    error_log = current_dir / "monitor_error.log"
    with open(error_log, 'w', encoding='utf-8') as f:
        f.write(f"啟動錯誤: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    # 顯示錯誤對話框（如果可能）
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("啟動錯誤", f"NSSM 監控啟動失敗:\n{e}")
    except:
        pass