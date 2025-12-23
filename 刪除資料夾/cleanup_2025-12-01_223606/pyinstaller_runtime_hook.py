#!/usr/bin/env python3
"""
PyInstaller Runtime Hook - F1T GUI V0.7.0
設置 EXE 運行環境變數和日誌級別
"""

import os
import sys

# ==================== 日誌級別設置 ====================
# EXE 模式：極度靜默（僅記錄嚴重錯誤）
os.environ['F1_LOG_LEVEL'] = 'CRITICAL'

# ==================== 資源路徑設置 ====================
if getattr(sys, 'frozen', False):
    # 設置 PyInstaller 的內部資源路徑
    # _MEIPASS 是 PyInstaller 解壓資源的臨時目錄
    bundle_dir = sys._MEIPASS
    os.environ['F1T_RESOURCE_PATH'] = bundle_dir
    
    # 設置圖片資源路徑
    image_dir = os.path.join(bundle_dir, 'image')
    if os.path.exists(image_dir):
        os.environ['F1T_IMAGE_PATH'] = image_dir

# ==================== FastF1 緩存設置 ====================
# 設置用戶目錄下的緩存路徑
user_cache_dir = os.path.join(os.path.expanduser('~'), '.f1telemetrystation', 'cache')
os.makedirs(user_cache_dir, exist_ok=True)
os.environ['F1T_CACHE_DIR'] = user_cache_dir

# ==================== API 配置 ====================
# 確保使用公開 API
os.environ['F1T_API_MODE'] = 'production'
os.environ['F1T_API_BASE_URL'] = 'https://api.f1telemetrystationpro.org'

# ==================== 編碼設置 ====================
# 確保 UTF-8 編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

print(f"[PyInstaller Hook] F1T GUI V0.7.0 - 環境初始化完成")
print(f"[PyInstaller Hook] 日誌級別: {os.environ.get('F1_LOG_LEVEL', 'DEBUG')}")
print(f"[PyInstaller Hook] API 模式: {os.environ.get('F1T_API_MODE', 'development')}")
print(f"[PyInstaller Hook] 緩存目錄: {user_cache_dir}")
