#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Brake → Throttle 開啟順序問題
驗證修復：cleanup_threads() → cleanup() 和 _is_loading 標誌重置
"""

import sys
import io
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 設置標準輸出為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_brake_then_throttle():
    """模擬用戶操作：開啟 Brake → 關閉 → 開啟 Throttle"""
    
    print("=" * 80)
    print("[TEST] Brake Analysis -> Throttle Analysis Sequence Test")
    print("=" * 80)
    
    # 測試 1: 導入模組
    print("\n[Test 1] Import Brake and Throttle modules...")
    try:
        from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeDataManager
        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleDataManager
        print("[OK] Modules imported successfully")
    except ImportError as e:
        print(f"[FAIL] Module import failed: {e}")
        return False
    
    # 測試 2: 創建 Brake DataManager
    print("\n[Test 2] Create Brake DataManager...")
    try:
        brake_manager = BrakeDataManager()
        print(f"[OK] Brake Manager created, _is_loading = {brake_manager._is_loading}")
    except Exception as e:
        print(f"[FAIL] Brake Manager creation failed: {e}")
        return False
    
    # 測試 3: 清理 Brake Manager (模擬關閉視窗)
    print("\n[Test 3] Cleanup Brake Manager...")
    try:
        # 先設置 _is_loading = True 模擬載入中狀態
        brake_manager._is_loading = True
        print(f"   Set _is_loading = True (simulate loading state)")
        
        # 執行清理
        brake_manager.cleanup()
        
        # 檢查清理後狀態
        if brake_manager._is_loading == False:
            print(f"[OK] Brake Manager cleanup succeeded, _is_loading reset to False")
        else:
            print(f"[FAIL] Brake Manager cleanup failed, _is_loading still {brake_manager._is_loading}")
            return False
            
    except AttributeError as e:
        if "cleanup_threads" in str(e):
            print(f"[FAIL] Found error: calling non-existent cleanup_threads() method")
            print(f"   Error message: {e}")
            return False
        else:
            print(f"[FAIL] Brake Manager cleanup failed: {e}")
            return False
    except Exception as e:
        print(f"[FAIL] Brake Manager cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 4: 創建 Throttle DataManager (模擬開啟 Throttle)
    print("\n[Test 4] Create Throttle DataManager...")
    try:
        throttle_manager = ThrottleDataManager()
        print(f"[OK] Throttle Manager created, _is_loading = {throttle_manager._is_loading}")
    except Exception as e:
        print(f"[FAIL] Throttle Manager creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 5: 清理 Throttle Manager
    print("\n[Test 5] Cleanup Throttle Manager...")
    try:
        # 先設置 _is_loading = True
        throttle_manager._is_loading = True
        print(f"   Set _is_loading = True (simulate loading state)")
        
        # 執行清理
        throttle_manager.cleanup()
        
        # 檢查清理後狀態
        if throttle_manager._is_loading == False:
            print(f"[OK] Throttle Manager cleanup succeeded, _is_loading reset to False")
        else:
            print(f"[FAIL] Throttle Manager cleanup failed, _is_loading still {throttle_manager._is_loading}")
            return False
            
    except AttributeError as e:
        if "cleanup_threads" in str(e):
            print(f"[FAIL] Found error: calling non-existent cleanup_threads() method")
            print(f"   Error message: {e}")
            return False
        else:
            print(f"[FAIL] Throttle Manager cleanup failed: {e}")
            return False
    except Exception as e:
        print(f"[FAIL] Throttle Manager cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 6: 檢查 cleanup() 方法存在性
    print("\n[Test 6] Check cleanup() method existence...")
    from modules.gui.lap_analysis.telemetry_data_loader_base import TelemetryDataLoader
    
    if hasattr(TelemetryDataLoader, 'cleanup'):
        print("[OK] TelemetryDataLoader has cleanup() method")
    else:
        print("[FAIL] TelemetryDataLoader missing cleanup() method")
        return False
    
    if hasattr(TelemetryDataLoader, 'cleanup_threads'):
        print("[WARNING] TelemetryDataLoader still has cleanup_threads() method (should be removed)")
    else:
        print("[OK] TelemetryDataLoader does not have cleanup_threads() method (correct)")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] All tests passed! Brake -> Throttle sequence issue fixed")
    print("=" * 80)
    return True

if __name__ == '__main__':
    # 創建 QApplication（某些 PyQt 組件需要）
    app = QApplication(sys.argv)
    
    # 執行測試
    success = test_brake_then_throttle()
    
    # 退出
    sys.exit(0 if success else 1)
