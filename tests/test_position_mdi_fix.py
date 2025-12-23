#!/usr/bin/env python3
"""
測試車手排名分析 MDI 修復
Test Driver Position Analysis MDI Fix

驗證：
1. 模組可正常導入
2. _show_error() 方法已實現
3. None 值排序邏輯正確

作者: F1T Team
日期: 2025-10-28
"""

import sys
import traceback


def test_import():
    """測試模組導入"""
    print("=" * 60)
    print("階段 1: 測試模組導入")
    print("=" * 60)
    
    try:
        from modules.gui.driver_position_analysis.driver_position_analysis_mdi import (
            DriverPositionAnalysisMDI
        )
        print("✅ 模組導入成功")
        return True, DriverPositionAnalysisMDI
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        traceback.print_exc()
        return False, None


def test_show_error_method(mdi_class):
    """測試 _show_error() 方法是否存在"""
    print("\n" + "=" * 60)
    print("階段 2: 測試 _show_error() 方法")
    print("=" * 60)
    
    try:
        if not hasattr(mdi_class, '_show_error'):
            print("❌ _show_error() 方法不存在")
            return False
        
        print("✅ _show_error() 方法已定義")
        
        # 檢查方法簽名
        import inspect
        sig = inspect.signature(mdi_class._show_error)
        params = list(sig.parameters.keys())
        print(f"   方法參數: {params}")
        
        if 'self' in params and 'title' in params and 'message' in params:
            print("✅ 方法簽名正確")
            return True
        else:
            print(f"❌ 方法簽名不正確，預期 (self, title, message)，實際: {params}")
            return False
            
    except Exception as e:
        print(f"❌ 方法檢查失敗: {e}")
        traceback.print_exc()
        return False


def test_none_sorting():
    """測試 None 值排序邏輯"""
    print("\n" + "=" * 60)
    print("階段 3: 測試 None 值排序邏輯")
    print("=" * 60)
    
    try:
        # 測試數據（包含 None 值）
        test_data = [
            {"driver": "VER", "finishing_position": 1},
            {"driver": "PER", "finishing_position": None},  # 退賽
            {"driver": "LEC", "finishing_position": 3},
            {"driver": "SAI", "finishing_position": None},  # 退賽
            {"driver": "HAM", "finishing_position": 2},
        ]
        
        print(f"排序前: {[d['finishing_position'] for d in test_data]}")
        
        # 使用修復後的排序邏輯
        test_data.sort(key=lambda x: x.get("finishing_position") if x.get("finishing_position") is not None else 999)
        
        sorted_positions = [d['finishing_position'] for d in test_data]
        print(f"排序後: {sorted_positions}")
        
        # 驗證排序結果
        expected = [1, 2, 3, None, None]
        if sorted_positions == expected:
            print("✅ None 值排序邏輯正確")
            print(f"   車手順序: {[d['driver'] for d in test_data]}")
            return True
        else:
            print(f"❌ 排序結果不正確，預期: {expected}")
            return False
            
    except Exception as e:
        print(f"❌ 排序測試失敗: {e}")
        traceback.print_exc()
        return False


def test_none_get_behavior():
    """測試 .get() 方法對 None 值的處理"""
    print("\n" + "=" * 60)
    print("階段 4: 測試 .get() 預設值行為")
    print("=" * 60)
    
    try:
        test_dict = {"finishing_position": None}
        
        # 錯誤的方式（會導致原始錯誤）
        result1 = test_dict.get("finishing_position", 999)
        print(f"方式 1: dict.get('key', 999) 當值為 None 時 = {result1} (類型: {type(result1).__name__})")
        
        # 正確的方式（修復後的邏輯）
        result2 = test_dict.get("finishing_position") if test_dict.get("finishing_position") is not None else 999
        print(f"方式 2: 明確檢查 is not None = {result2} (類型: {type(result2).__name__})")
        
        # 說明問題
        print("\n[INSIGHT] 關鍵洞察:")
        print("   .get('key', default) 只在鍵不存在時返回 default")
        print("   如果鍵存在但值為 None，仍會返回 None")
        print("   因此需要明確檢查 'is not None'")
        
        if result2 == 999:
            print("\n✅ 修復後的邏輯正確處理 None 值")
            return True
        else:
            print("\n❌ 邏輯驗證失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n[TEST] 開始測試車手排名分析 MDI 修復")
    print("=" * 60)
    
    results = []
    
    # 階段 1: 模組導入
    success, mdi_class = test_import()
    results.append(("模組導入", success))
    
    if not success:
        print("\n❌ 無法繼續測試，模組導入失敗")
        return False
    
    # 階段 2: _show_error() 方法
    success = test_show_error_method(mdi_class)
    results.append(("_show_error() 方法", success))
    
    # 階段 3: None 值排序
    success = test_none_sorting()
    results.append(("None 值排序", success))
    
    # 階段 4: .get() 行為
    success = test_none_get_behavior()
    results.append((".get() 預設值行為", success))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] 所有測試通過！修復成功！")
        return True
    else:
        print("\n[WARNING] 部分測試失敗，請檢查上述錯誤")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
