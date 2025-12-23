#!/usr/bin/env python3
"""
Speed 模組委派機制驗證測試
驗證 module_ref 賦值和委派調用是否正常工作
"""

import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule, SpeedDataManager

def test_delegation_mechanism():
    """測試委派機制"""
    print("=" * 60)
    print("Speed 模組委派機制驗證測試")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 測試 1: 創建模組
    print("\n[測試 1] 創建 SpeedAnalysisModule...")
    module = SpeedAnalysisModule()
    print("✅ 模組創建成功")
    
    # 測試 2: 初始化模組
    print("\n[測試 2] 初始化模組...")
    success = module.initialize_module()
    print(f"初始化結果: {success}")
    assert success, "模組初始化失敗"
    print("✅ 模組初始化成功")
    
    # 測試 3: 驗證 data_manager 存在
    print("\n[測試 3] 驗證 data_manager 存在...")
    assert hasattr(module, 'data_manager'), "缺少 data_manager 屬性"
    assert module.data_manager is not None, "data_manager 為 None"
    print("✅ data_manager 存在")
    
    # 測試 4: 驗證 module_ref 屬性存在
    print("\n[測試 4] 驗證 module_ref 屬性存在...")
    assert hasattr(module.data_manager, 'module_ref'), "data_manager 缺少 module_ref 屬性"
    print("✅ module_ref 屬性存在")
    
    # 測試 5: 驗證 module_ref 賦值正確
    print("\n[測試 5] 驗證 module_ref 賦值...")
    assert module.data_manager.module_ref is module, "module_ref 未正確賦值"
    print("✅ module_ref 正確指向 module 實例")
    print(f"   - module id: {id(module)}")
    print(f"   - module_ref id: {id(module.data_manager.module_ref)}")
    print(f"   - 引用一致: {module.data_manager.module_ref is module}")
    
    # 測試 6: 驗證委派方法存在
    print("\n[測試 6] 驗證委派方法存在...")
    assert hasattr(module.data_manager, '_check_and_load_telemetry_if_needed'), \
        "缺少 _check_and_load_telemetry_if_needed 方法"
    print("✅ 委派方法存在")
    
    # 測試 7: 測試委派調用（僅檢查不拋出異常）
    print("\n[測試 7] 測試委派調用...")
    try:
        # 設置上下文
        module.data_manager.current_year = "2024"
        module.data_manager.current_race = "Singapore"
        module.data_manager.current_session = "R"
        
        # 嘗試調用委派方法
        result = module.data_manager._check_and_load_telemetry_if_needed()
        print(f"委派調用結果: {result}")
        print("✅ 委派調用執行成功（無異常）")
    except Exception as e:
        print(f"❌ 委派調用失敗: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("所有測試通過")
    print("=" * 60)
    print("\n關鍵驗證結果:")
    print("1. ✅ module_ref 屬性存在")
    print("2. ✅ module_ref 正確賦值")
    print("3. ✅ 委派方法可正常調用")
    print("4. ✅ 委派模式完整實現")
    
    return True

if __name__ == "__main__":
    try:
        test_delegation_mechanism()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
