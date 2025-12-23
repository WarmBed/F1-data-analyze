#!/usr/bin/env python3
"""
測試 Runtime Hook 日誌級別設置
"""
import os
import sys

print("=" * 60)
print("測試 F1T GUI Runtime Hook 日誌級別設置")
print("=" * 60)

# 模擬 PyInstaller 環境
sys._MEIPASS = r"C:\temp\fake_meipass"

# 導入 runtime hook
print("\n1. 導入 Runtime Hook...")
exec(open('pyinstaller_runtime_hook.py', encoding='utf-8').read())

# 檢查環境變數
print("\n2. 檢查環境變數設置:")
log_level = os.environ.get('F1_LOG_LEVEL', 'NOT_SET')
print(f"   F1_LOG_LEVEL = {log_level}")

if log_level == 'DEBUG':
    print("   ✅ 日誌級別正確設置為 DEBUG")
else:
    print(f"   ❌ 錯誤: 日誌級別應該是 DEBUG，實際為 {log_level}")

# 測試日誌系統
print("\n3. 測試日誌系統初始化:")
try:
    from core.logger import setup_logging, get_logger
    
    setup_logging(component="test", level=log_level)
    logger = get_logger("test")
    
    print(f"   當前日誌級別: {logger.level}")
    print(f"   DEBUG 級別值: {10}")
    
    if logger.level <= 10:  # DEBUG = 10
        print("   ✅ 日誌系統已設置為 DEBUG 級別")
    else:
        print(f"   ❌ 錯誤: 日誌級別過高 ({logger.level})")
        
except Exception as e:
    print(f"   ❌ 日誌系統初始化失敗: {e}")

print("\n" + "=" * 60)
print("測試完成！")
print("=" * 60)
