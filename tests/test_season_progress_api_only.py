#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Season Progress API-ONLY 模式
驗證本地 JSON 回退是否已完全禁用
"""

import sys
import os
from pathlib import Path

# 設定 UTF-8 編碼
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 禁用 QT 環境變數避免 GUI 初始化
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

print("=" * 80)
print("Season Progress API-ONLY 模式驗證測試")
print("=" * 80)
print()

try:
    # Import 模組
    print("[INFO] Importing SeasonProgressDataLoader...")
    from modules.gui.season_progress.season_progress_data_loader import SeasonProgressDataLoader
    print("[OK] Import successful")
    
    # 創建實例
    loader = SeasonProgressDataLoader('2025')
    print("[OK] Loader instance created")
    
    # 檢查 _allow_local_fallback 設定
    print("\n" + "=" * 80)
    print("設定檢查:")
    print("=" * 80)
    print(f"_allow_local_fallback = {loader._allow_local_fallback}")
    print(f"Expected: False")
    
    if loader._allow_local_fallback:
        print("[FAIL] 本地 JSON 回退仍然啟用!")
        sys.exit(1)
    else:
        print("[PASS] 本地 JSON 回退已正確禁用")
    
    # 測試 _load_calendar_data() 方法
    print("\n" + "=" * 80)
    print("Calendar 載入測試:")
    print("=" * 80)
    
    calendar_data = loader._load_calendar_data()
    
    if calendar_data is None:
        print("[PASS] _load_calendar_data() 返回 None (API-ONLY 模式正確運作)")
    else:
        print(f"[FAIL] _load_calendar_data() 返回了數據 (不應該載入本地 JSON)")
        print(f"返回的數據類型: {type(calendar_data)}")
        sys.exit(1)
    
    # 最終結果
    print("\n" + "=" * 80)
    print("[SUCCESS] 所有測試通過！Season Progress 已完全遵循 API-ONLY 模式")
    print("=" * 80)
    print("\n配置摘要:")
    print("  [OK] _allow_local_fallback = False")
    print("  [OK] _load_calendar_data() 不載入本地 JSON")
    print("  [OK] 僅使用 API 獲取數據")
    
except Exception as e:
    print(f"\n[ERROR] 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
