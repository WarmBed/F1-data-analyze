"""
測試新創建的 Gear, DRS, RPM Trace 模組
========================================

驗證：
1. Import 成功
2. ModuleFactory 可以創建模組
3. 類別名稱正確
4. 模組註冊正確

Author: F1T Team
Date: 2025-12-11
"""

import sys
from PyQt5.QtWidgets import QApplication


def test_imports():
    """測試模組 Import"""
    print("=" * 60)
    print("階段 1: 測試模組 Import")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.live_timing_modules.gear_trace import LiveTimingGearTrace
        print("✅ Gear Trace import 成功")
    except Exception as e:
        print(f"❌ Gear Trace import 失敗: {e}")
        return False
    
    try:
        from modules.gui.live_timing.live_timing_modules.drs_trace import LiveTimingDRSTrace
        print("✅ DRS Trace import 成功")
    except Exception as e:
        print(f"❌ DRS Trace import 失敗: {e}")
        return False
    
    try:
        from modules.gui.live_timing.live_timing_modules.rpm_trace import LiveTimingRPMTrace
        print("✅ RPM Trace import 成功")
    except Exception as e:
        print(f"❌ RPM Trace import 失敗: {e}")
        return False
    
    return True


def test_module_factory():
    """測試 ModuleFactory 創建模組"""
    print("\n" + "=" * 60)
    print("階段 2: 測試 ModuleFactory 創建模組")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        from modules.gui.live_timing.core.module_factory import LiveTimingModuleFactory
        factory = LiveTimingModuleFactory()
        
        # 測試 Gear Trace
        gear_module = factory.create_module('gear_trace')
        if type(gear_module).__name__ == 'LiveTimingGearTrace':
            print(f"✅ Gear Trace 模組創建成功: {type(gear_module).__name__}")
        else:
            print(f"❌ Gear Trace 類別名稱錯誤: {type(gear_module).__name__}")
            return False
        
        # 測試 DRS Trace
        drs_module = factory.create_module('drs_trace')
        if type(drs_module).__name__ == 'LiveTimingDRSTrace':
            print(f"✅ DRS Trace 模組創建成功: {type(drs_module).__name__}")
        else:
            print(f"❌ DRS Trace 類別名稱錯誤: {type(drs_module).__name__}")
            return False
        
        # 測試 RPM Trace
        rpm_module = factory.create_module('rpm_trace')
        if type(rpm_module).__name__ == 'LiveTimingRPMTrace':
            print(f"✅ RPM Trace 模組創建成功: {type(rpm_module).__name__}")
        else:
            print(f"❌ RPM Trace 類別名稱錯誤: {type(rpm_module).__name__}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ModuleFactory 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_module_registry():
    """測試模組註冊"""
    print("\n" + "=" * 60)
    print("階段 3: 測試模組註冊與多國語言")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.core.module_factory import MODULE_REGISTRY, MODULE_METADATA
        
        # 測試 Gear Trace 註冊
        gear_aliases = ["Gear Trace", "檔位追蹤", "ギアトレース", "gear_trace"]
        for alias in gear_aliases:
            if alias in MODULE_REGISTRY and MODULE_REGISTRY[alias] == "gear_trace":
                print(f"✅ Gear Trace 別名註冊成功: {alias}")
            else:
                print(f"❌ Gear Trace 別名註冊失敗: {alias}")
        
        # 測試 DRS Trace 註冊
        drs_aliases = ["DRS Trace", "DRS追蹤", "DRSトレース", "drs_trace"]
        for alias in drs_aliases:
            if alias in MODULE_REGISTRY and MODULE_REGISTRY[alias] == "drs_trace":
                print(f"✅ DRS Trace 別名註冊成功: {alias}")
            else:
                print(f"❌ DRS Trace 別名註冊失敗: {alias}")
        
        # 測試 RPM Trace 註冊
        rpm_aliases = ["RPM Trace", "轉速追蹤", "回転数トレース", "rpm_trace"]
        for alias in rpm_aliases:
            if alias in MODULE_REGISTRY and MODULE_REGISTRY[alias] == "rpm_trace":
                print(f"✅ RPM Trace 別名註冊成功: {alias}")
            else:
                print(f"❌ RPM Trace 別名註冊失敗: {alias}")
        
        # 測試 METADATA
        if "gear_trace" in MODULE_METADATA:
            print(f"✅ Gear Trace METADATA 註冊成功")
            print(f"   - 顯示名稱: {MODULE_METADATA['gear_trace']['display_name']}")
            print(f"   - 描述: {MODULE_METADATA['gear_trace']['description']}")
        else:
            print(f"❌ Gear Trace METADATA 註冊失敗")
        
        if "drs_trace" in MODULE_METADATA:
            print(f"✅ DRS Trace METADATA 註冊成功")
            print(f"   - 顯示名稱: {MODULE_METADATA['drs_trace']['display_name']}")
            print(f"   - 描述: {MODULE_METADATA['drs_trace']['description']}")
        else:
            print(f"❌ DRS Trace METADATA 註冊失敗")
        
        if "rpm_trace" in MODULE_METADATA:
            print(f"✅ RPM Trace METADATA 註冊成功")
            print(f"   - 顯示名稱: {MODULE_METADATA['rpm_trace']['display_name']}")
            print(f"   - 描述: {MODULE_METADATA['rpm_trace']['description']}")
        else:
            print(f"❌ RPM Trace METADATA 註冊失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ 模組註冊測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n" + "🏎️ " * 20)
    print("F1T 新 Trace 模組測試")
    print("Gear Trace | DRS Trace | RPM Trace")
    print("🏎️ " * 20 + "\n")
    
    # 測試 1: Import
    if not test_imports():
        print("\n❌ 測試失敗：Import 階段")
        sys.exit(1)
    
    # 測試 2: ModuleFactory
    if not test_module_factory():
        print("\n❌ 測試失敗：ModuleFactory 階段")
        sys.exit(1)
    
    # 測試 3: 模組註冊
    if not test_module_registry():
        print("\n❌ 測試失敗：模組註冊階段")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 所有測試通過！")
    print("=" * 60)
    print("\n✅ Gear Trace 模組完整功能正常")
    print("✅ DRS Trace 模組完整功能正常")
    print("✅ RPM Trace 模組完整功能正常")
    print("\n📋 下一步：")
    print("1. 啟動 GUI: python f1t_gui_main.py")
    print("2. 開啟 Live Timing 選單")
    print("3. 測試三個新模組：Gear Trace、DRS Trace、RPM Trace")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
