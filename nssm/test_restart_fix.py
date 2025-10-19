#!/usr/bin/env python3
"""
F1T NSSM 重啟修復測試腳本

測試修復後的服務重啟功能是否正常運作
"""

import sys
import time
from pathlib import Path

# 添加模組路徑
sys.path.append(str(Path(__file__).parent))

from service_monitor import NSSMServiceMonitor


def test_restart_service():
    """測試服務重啟功能"""
    print("🧪 開始測試 F1T-API 重啟功能...")
    
    monitor = NSSMServiceMonitor(debug_enabled=True)
    
    # 測試前檢查服務狀態
    print("\n📊 測試前服務狀態:")
    status = monitor.get_service_status("F1T-API")
    print(f"   服務存在: {status['exists']}")
    print(f"   服務狀態: {status['state']}")
    if status['process_info']:
        print(f"   PID: {status['process_info']['pid']}")
    
    # 執行重啟測試
    print("\n🔄 執行重啟測試...")
    start_time = time.time()
    
    try:
        success = monitor.restart_service("F1T-API")
        end_time = time.time()
        
        print(f"   重啟結果: {'✅ 成功' if success else '❌ 失敗'}")
        print(f"   執行時間: {end_time - start_time:.2f} 秒")
        
        # 檢查重啟後狀態
        print("\n📊 重啟後服務狀態:")
        status = monitor.get_service_status("F1T-API")
        print(f"   服務存在: {status['exists']}")
        print(f"   服務狀態: {status['state']}")
        if status['process_info']:
            print(f"   新 PID: {status['process_info']['pid']}")
        
        return success
        
    except Exception as e:
        end_time = time.time()
        print(f"   ❌ 測試失敗: {e}")
        print(f"   執行時間: {end_time - start_time:.2f} 秒")
        return False


def test_service_resilience():
    """測試服務韌性 - 多次重啟"""
    print("\n🔄 執行韌性測試 (3 次重啟)...")
    
    monitor = NSSMServiceMonitor(debug_enabled=False)
    success_count = 0
    
    for i in range(1, 4):
        print(f"\n   第 {i} 次重啟...")
        if monitor.restart_service("F1T-API"):
            success_count += 1
            print(f"   ✅ 第 {i} 次重啟成功")
        else:
            print(f"   ❌ 第 {i} 次重啟失敗")
        
        # 間隔等待
        if i < 3:
            time.sleep(3)
    
    print(f"\n📊 韌性測試結果: {success_count}/3 次成功")
    return success_count == 3


if __name__ == "__main__":
    print("=" * 50)
    print("F1T NSSM 重啟修復測試")
    print("=" * 50)
    
    # 基本重啟測試
    basic_test_passed = test_restart_service()
    
    # 韌性測試
    resilience_test_passed = test_service_resilience()
    
    # 總結
    print("\n" + "=" * 50)
    print("測試總結:")
    print(f"   基本重啟測試: {'✅ 通過' if basic_test_passed else '❌ 失敗'}")
    print(f"   韌性測試: {'✅ 通過' if resilience_test_passed else '❌ 失敗'}")
    
    if basic_test_passed and resilience_test_passed:
        print("\n🎉 所有測試通過！重啟修復成功！")
        sys.exit(0)
    else:
        print("\n⚠️  部分測試失敗，需要進一步調查")
        sys.exit(1)