#!/usr/bin/env python3
"""測試 AccidentDataManager 的 API-ONLY 模式修復"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_qt_import():
    """測試 1: 驗證 Qt 導入修復"""
    print("\n" + "="*70)
    print("測試 1: 驗證 Qt 導入修復")
    print("="*70)
    
    try:
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        print("✅ Qt 導入成功 - 沒有 'name Qt is not defined' 錯誤")
        return True
    except NameError as e:
        print(f"❌ Qt 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"⚠️  其他錯誤: {e}")
        return False


def test_api_only_policy():
    """測試 2: 驗證 API-ONLY 政策（預設禁用本地 JSON 後備）"""
    print("\n" + "="*70)
    print("測試 2: 驗證 API-ONLY 政策")
    print("="*70)
    
    try:
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        
        # 創建實例
        manager = AccidentDataManager()
        
        # 檢查後備政策
        allow_fallback = manager._allow_local_fallback
        policy_reason = manager._fallback_policy_reason
        
        print(f"📋 本地 JSON 後備: {'允許' if allow_fallback else '禁用'}")
        print(f"📋 政策原因: {policy_reason}")
        
        if not allow_fallback and "API-ONLY" in policy_reason:
            print("✅ API-ONLY 政策已正確啟用（預設禁用本地 JSON 後備）")
            return True
        else:
            print("❌ API-ONLY 政策未正確啟用")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_behavior():
    """測試 3: 驗證錯誤處理不會自動回退到本地 JSON"""
    print("\n" + "="*70)
    print("測試 3: 驗證錯誤處理行為")
    print("="*70)
    
    try:
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        from unittest.mock import Mock, patch
        
        manager = AccidentDataManager()
        
        # 模擬 API 失敗
        error_emitted = []
        manager.error_occurred.connect(lambda msg: error_emitted.append(msg))
        
        # 調用 _on_api_error（模擬 API 請求失敗）
        manager._on_api_error("模擬 API 錯誤")
        
        if error_emitted:
            print(f"✅ API 失敗時正確發出錯誤信號: {error_emitted[0]}")
            return True
        else:
            print("❌ API 失敗時未發出錯誤信號（可能錯誤回退到本地 JSON）")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """執行所有測試"""
    print("\n" + "#"*70)
    print("# AccidentDataManager API-ONLY 模式修復驗證")
    print("#"*70)
    
    results = []
    
    # 測試 1: Qt 導入
    results.append(("Qt 導入修復", test_qt_import()))
    
    # 測試 2: API-ONLY 政策
    results.append(("API-ONLY 政策", test_api_only_policy()))
    
    # 測試 3: 錯誤處理行為
    results.append(("錯誤處理行為", test_fallback_behavior()))
    
    # 總結
    print("\n" + "="*70)
    print("測試總結")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "#"*70)
    if all_passed:
        print("# ✅ 所有測試通過！API-ONLY 模式修復成功")
    else:
        print("# ❌ 部分測試失敗，請檢查上述錯誤")
    print("#"*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
