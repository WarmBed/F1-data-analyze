"""
驗證 QThread 信號洩漏修復

此腳本靜態檢查修復是否正確應用
"""

import sys
import re


def check_signal_disconnect_pattern(file_path: str) -> bool:
    """檢查是否正確實現了信號斷開模式"""
    print("=" * 80)
    print("🔍 靜態代碼檢查：QThread 信號洩漏修復")
    print("=" * 80)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # 檢查 1: trigger_api_runtime_poll 是否有斷開信號
    print("\n[檢查 1] trigger_api_runtime_poll() 信號斷開...")
    pattern1 = r'def trigger_api_runtime_poll.*?\.disconnect\(self\.on_api_runtime_result\)'
    if re.search(pattern1, content, re.DOTALL):
        print("  ✅ 找到 result_ready.disconnect()")
        checks.append(True)
    else:
        print("  ❌ 未找到 result_ready.disconnect()")
        checks.append(False)
    
    pattern2 = r'def trigger_api_runtime_poll.*?\.disconnect\(self\.on_api_runtime_finished\)'
    if re.search(pattern2, content, re.DOTALL):
        print("  ✅ 找到 finished.disconnect()")
        checks.append(True)
    else:
        print("  ❌ 未找到 finished.disconnect()")
        checks.append(False)
    
    # 檢查 2: trigger_api_runtime_poll 是否使用 Qt.UniqueConnection
    print("\n[檢查 2] trigger_api_runtime_poll() 唯一連接...")
    pattern3 = r'def trigger_api_runtime_poll.*?\.connect\(self\.on_api_runtime_result,\s*Qt\.UniqueConnection\)'
    if re.search(pattern3, content, re.DOTALL):
        print("  ✅ result_ready 使用 Qt.UniqueConnection")
        checks.append(True)
    else:
        print("  ❌ result_ready 未使用 Qt.UniqueConnection")
        checks.append(False)
    
    pattern4 = r'def trigger_api_runtime_poll.*?\.connect\(self\.on_api_runtime_finished,\s*Qt\.UniqueConnection\)'
    if re.search(pattern4, content, re.DOTALL):
        print("  ✅ finished 使用 Qt.UniqueConnection")
        checks.append(True)
    else:
        print("  ❌ finished 未使用 Qt.UniqueConnection")
        checks.append(False)
    
    # 檢查 3: trigger_api_health_check 是否有斷開信號
    print("\n[檢查 3] trigger_api_health_check() 信號斷開...")
    pattern5 = r'def trigger_api_health_check.*?\.disconnect\(self\.on_api_health_result\)'
    if re.search(pattern5, content, re.DOTALL):
        print("  ✅ 找到 result_ready.disconnect()")
        checks.append(True)
    else:
        print("  ❌ 未找到 result_ready.disconnect()")
        checks.append(False)
    
    pattern6 = r'def trigger_api_health_check.*?\.disconnect\(self\.on_api_health_finished\)'
    if re.search(pattern6, content, re.DOTALL):
        print("  ✅ 找到 finished.disconnect()")
        checks.append(True)
    else:
        print("  ❌ 未找到 finished.disconnect()")
        checks.append(False)
    
    # 檢查 4: trigger_api_health_check 是否使用 Qt.UniqueConnection
    print("\n[檢查 4] trigger_api_health_check() 唯一連接...")
    pattern7 = r'def trigger_api_health_check.*?\.connect\(self\.on_api_health_result,\s*Qt\.UniqueConnection\)'
    if re.search(pattern7, content, re.DOTALL):
        print("  ✅ result_ready 使用 Qt.UniqueConnection")
        checks.append(True)
    else:
        print("  ❌ result_ready 未使用 Qt.UniqueConnection")
        checks.append(False)
    
    pattern8 = r'def trigger_api_health_check.*?\.connect\(self\.on_api_health_finished,\s*Qt\.UniqueConnection\)'
    if re.search(pattern8, content, re.DOTALL):
        print("  ✅ finished 使用 Qt.UniqueConnection")
        checks.append(True)
    else:
        print("  ❌ finished 未使用 Qt.UniqueConnection")
        checks.append(False)
    
    # 檢查 5: 異常處理
    print("\n[檢查 5] 異常處理...")
    if 'except (TypeError, RuntimeError):' in content:
        print("  ✅ 找到正確的異常處理 (TypeError, RuntimeError)")
        checks.append(True)
    else:
        print("  ❌ 未找到正確的異常處理")
        checks.append(False)
    
    # 總結
    print("\n" + "=" * 80)
    passed = sum(checks)
    total = len(checks)
    print(f"檢查結果: {passed}/{total} 通過")
    
    if passed == total:
        print("✅ 所有檢查通過 - 修復正確應用")
        print("=" * 80)
        return True
    else:
        print("❌ 部分檢查失敗 - 修復未完全應用")
        print("=" * 80)
        return False


if __name__ == "__main__":
    file_path = "f1t_gui_main.py"
    success = check_signal_disconnect_pattern(file_path)
    sys.exit(0 if success else 1)
