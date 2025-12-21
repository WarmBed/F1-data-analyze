#!/usr/bin/env python3
"""
事故分析模組 API-ONLY 修復驗證腳本
快速檢查兩個關鍵修復：
1. Qt 導入修復
2. API-ONLY 政策啟用
"""

def main():
    import sys
    import warnings
    warnings.filterwarnings('ignore')
    
    print("="*70)
    print("事故分析模組 API-ONLY 修復驗證")
    print("="*70 + "\n")
    
    # 測試 1: Qt 導入
    print("【測試 1】Qt 導入修復")
    try:
        from PyQt5.QtCore import Qt
        from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager
        print("  ✅ Qt 成功導入")
        print("  ✅ AccidentDataManager 成功導入")
    except NameError as e:
        print(f"  ❌ Qt 導入失敗: {e}")
        return 1
    except Exception as e:
        print(f"  ❌ 導入錯誤: {e}")
        return 1
    
    # 測試 2: API-ONLY 政策
    print("\n【測試 2】API-ONLY 政策檢查")
    try:
        manager = AccidentDataManager()
        
        # 檢查後備政策狀態
        allow_fallback = manager._allow_local_fallback
        policy_reason = manager._fallback_policy_reason
        
        print(f"  📋 本地 JSON 後備: {'啟用' if allow_fallback else '禁用'}")
        print(f"  📋 政策原因: {policy_reason}")
        
        if not allow_fallback:
            print("  ✅ API-ONLY 政策已正確啟用")
            
            # 驗證政策原因包含 API-ONLY
            if "API-ONLY" in policy_reason:
                print("  ✅ 政策原因正確（包含 'API-ONLY' 關鍵字）")
            else:
                print("  ⚠️  政策原因可能不正確")
        else:
            print("  ❌ 警告: 本地 JSON 後備仍然啟用（違反 API-ONLY 政策）")
            return 1
            
    except Exception as e:
        print(f"  ❌ 政策檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 測試 3: 錯誤處理邏輯
    print("\n【測試 3】錯誤處理邏輯驗證")
    try:
        # 模擬 API 錯誤
        error_received = []
        manager.error_occurred.connect(lambda msg: error_received.append(msg))
        
        # 觸發 API 錯誤處理
        manager._on_api_error("模擬 API 請求失敗")
        
        if error_received:
            print(f"  ✅ API 失敗時正確發出錯誤信號")
            print(f"  📋 錯誤訊息: {error_received[0][:50]}...")
        else:
            print("  ❌ API 失敗時未發出錯誤信號")
            return 1
            
    except Exception as e:
        print(f"  ❌ 錯誤處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 總結
    print("\n" + "="*70)
    print("✅ 所有測試通過！修復已成功應用。")
    print("="*70)
    print("\n修復摘要:")
    print("  1. ✅ Qt 導入錯誤已修復 (from PyQt5.QtCore import Qt)")
    print("  2. ✅ API-ONLY 政策已啟用 (預設禁用本地 JSON 後備)")
    print("  3. ✅ 錯誤處理邏輯正確 (API 失敗時不會自動回退)")
    print("\n" + "="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
