#!/usr/bin/env python3
"""驗證 AccidentDataManager 修復"""
import sys
import warnings
warnings.filterwarnings('ignore')  # 忽略 FastF1 警告

try:
    # 測試 1: Qt 導入
    from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager, Qt
    print("[PASS] Qt 導入成功")
    
    # 測試 2: 創建實例
    manager = AccidentDataManager()
    print("[PASS] AccidentDataManager 初始化成功")
    
    # 測試 3: API-ONLY 政策
    if not manager._allow_local_fallback:
        print("[PASS] API-ONLY 政策已啟用（預設禁用本地 JSON 後備）")
        print(f"[INFO] 政策原因: {manager._fallback_policy_reason}")
    else:
        print("[FAIL] API-ONLY 政策未啟用")
        sys.exit(1)
    
    print("\n✅ 所有測試通過！修復成功。")
    
except Exception as e:
    print(f"[FAIL] 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
