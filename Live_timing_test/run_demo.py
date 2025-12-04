"""
F1 Live Timing Demo 啟動器
修復 Windows 編碼問題
"""
import sys
import os

# 修復 Windows 編碼問題
if sys.platform == 'win32':
    # 設置標準輸出為 UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    # 設置環境變數
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 導入並執行主程式
from Live_timing_test.demo_histroy_live_position_tracking import main

if __name__ == "__main__":
    main()
