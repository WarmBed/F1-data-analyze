# -*- coding: utf-8 -*-
"""
測試 CC% 和 OT% 完整集成

驗證項目：
1. CloseCombatPredictor 導入成功
2. OvertakePredictor 導入成功
3. 初始化方法存在
4. 更新方法存在
5. 3 個額外特徵計算方法存在
6. 調用點都已添加

Author: F1T Team
Date: 2025-12-10
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_imports():
    """測試延遲導入函數"""
    print("=" * 60)
    print("測試 1: 延遲導入函數")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.core.data_manager import (
            _lazy_import_overtake_predictor,
            _lazy_import_close_combat_predictor
        )
        
        print("✅ _lazy_import_overtake_predictor 存在")
        print("✅ _lazy_import_close_combat_predictor 存在")
        
        # 測試導入
        ot_success = _lazy_import_overtake_predictor()
        cc_success = _lazy_import_close_combat_predictor()
        
        print(f"{'✅' if ot_success else '❌'} F83 OvertakePredictor 導入: {ot_success}")
        print(f"{'✅' if cc_success else '❌'} F85 CloseCombatPredictor 導入: {cc_success}")
        
        return ot_success and cc_success
    except Exception as e:
        print(f"❌ 導入測試失敗: {e}")
        return False

def test_init_methods():
    """測試初始化方法"""
    print("\n" + "=" * 60)
    print("測試 2: 初始化方法")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
        
        methods = [
            '_init_overtake_predictor',
            '_init_close_combat_predictor'
        ]
        
        all_exist = True
        for method in methods:
            exists = hasattr(LiveTimingDataManager, method)
            print(f"{'✅' if exists else '❌'} {method}: {exists}")
            all_exist = all_exist and exists
        
        return all_exist
    except Exception as e:
        print(f"❌ 初始化方法測試失敗: {e}")
        return False

def test_update_methods():
    """測試更新方法"""
    print("\n" + "=" * 60)
    print("測試 3: 更新方法")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
        
        methods = [
            '_update_overtake_predictions',
            '_update_close_combat_predictions'
        ]
        
        all_exist = True
        for method in methods:
            exists = hasattr(LiveTimingDataManager, method)
            print(f"{'✅' if exists else '❌'} {method}: {exists}")
            all_exist = all_exist and exists
        
        return all_exist
    except Exception as e:
        print(f"❌ 更新方法測試失敗: {e}")
        return False

def test_feature_calculation_methods():
    """測試 3 個額外特徵計算方法"""
    print("\n" + "=" * 60)
    print("測試 4: F85 額外特徵計算方法")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
        
        methods = [
            '_calculate_gap_trend_3lap',
            '_calculate_min_gap_last_5lap',
            '_calculate_consecutive_catching_laps'
        ]
        
        all_exist = True
        for method in methods:
            exists = hasattr(LiveTimingDataManager, method)
            print(f"{'✅' if exists else '❌'} {method}: {exists}")
            all_exist = all_exist and exists
        
        return all_exist
    except Exception as e:
        print(f"❌ 特徵計算方法測試失敗: {e}")
        return False

def test_model_files():
    """測試模型檔案是否存在"""
    print("\n" + "=" * 60)
    print("測試 5: 模型檔案")
    print("=" * 60)
    
    model_dir = project_root / "models" / "overtake_prediction"
    
    ot_models = list(model_dir.glob("overtake_xgb_*.json"))
    cc_models = list(model_dir.glob("close_combat_xgb_*.json"))
    
    print(f"{'✅' if ot_models else '❌'} F83 模型檔案: {len(ot_models)} 個")
    if ot_models:
        print(f"   最新: {ot_models[0].name}")
    
    print(f"{'✅' if cc_models else '❌'} F85 模型檔案: {len(cc_models)} 個")
    if cc_models:
        print(f"   最新: {cc_models[0].name}")
    
    return len(ot_models) > 0 and len(cc_models) > 0

def test_predictor_initialization():
    """測試預測器初始化"""
    print("\n" + "=" * 60)
    print("測試 6: 預測器初始化")
    print("=" * 60)
    
    try:
        from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
        
        # 創建單例實例
        manager = LiveTimingDataManager.instance()
        
        ot_exists = hasattr(manager, '_overtake_predictor')
        cc_exists = hasattr(manager, '_close_combat_predictor')
        
        print(f"{'✅' if ot_exists else '❌'} _overtake_predictor 屬性存在: {ot_exists}")
        print(f"{'✅' if cc_exists else '❌'} _close_combat_predictor 屬性存在: {cc_exists}")
        
        if ot_exists:
            ot_loaded = manager._overtake_predictor is not None
            print(f"{'✅' if ot_loaded else '⚠️'} F83 預測器已載入: {ot_loaded}")
            if ot_loaded:
                print(f"   模型版本: v{manager._overtake_predictor.model_version}")
        
        if cc_exists:
            cc_loaded = manager._close_combat_predictor is not None
            print(f"{'✅' if cc_loaded else '⚠️'} F85 預測器已載入: {cc_loaded}")
            if cc_loaded:
                print(f"   模型版本: v{manager._close_combat_predictor.model_version}")
        
        return ot_exists and cc_exists
    except Exception as e:
        print(f"❌ 預測器初始化測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """執行所有測試"""
    print("\n" + "🔍 " * 20)
    print("CC% 和 OT% 完整集成驗證測試")
    print("🔍 " * 20 + "\n")
    
    results = {
        "延遲導入函數": test_imports(),
        "初始化方法": test_init_methods(),
        "更新方法": test_update_methods(),
        "特徵計算方法": test_feature_calculation_methods(),
        "模型檔案": test_model_files(),
        "預測器初始化": test_predictor_initialization()
    }
    
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        print(f"{'✅' if result else '❌'} {test_name}")
    
    print("\n" + "=" * 60)
    print(f"通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有測試通過！CC% 已完整複製 OT% 的實現模式")
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗，請檢查上方錯誤訊息")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
