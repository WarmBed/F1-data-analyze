"""
診斷 lap_analysis_windows.discard() 失敗的原因

測試流程：
1. 檢查 Speed Analysis 模組的 __hash__ 和 __eq__ 方法
2. 模擬 add/discard 操作
3. 驗證物件 identity
"""

import sys
sys.path.insert(0, r'C:\Users\mike2\OneDrive\Code\F1-data-analyze')

def diagnose_set_behavior():
    print("=" * 80)
    print("診斷 lap_analysis_windows.discard() 失敗原因")
    print("=" * 80)
    
    # 導入 SpeedAnalysisModule
    try:
        from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
        print("✅ 成功導入 SpeedAnalysisModule")
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        return
    
    # 創建模組實例
    print("\n" + "=" * 80)
    print("測試 1: 基本 set 操作")
    print("=" * 80)
    
    module = SpeedAnalysisModule()
    print(f"模組實例: {module}")
    print(f"模組 ID: {id(module)}")
    print(f"模組 type: {type(module)}")
    
    # 檢查是否有 __hash__ 方法
    print(f"\n模組是否可 hash: {hasattr(module, '__hash__')}")
    if hasattr(module, '__hash__'):
        try:
            hash_value = hash(module)
            print(f"模組 hash 值: {hash_value}")
        except Exception as e:
            print(f"❌ hash() 失敗: {e}")
    
    # 檢查是否有 __eq__ 方法
    print(f"模組是否有 __eq__: {hasattr(module, '__eq__')}")
    
    # 測試 set 操作
    print("\n" + "=" * 80)
    print("測試 2: 模擬 lap_analysis_windows 操作")
    print("=" * 80)
    
    test_set = set()
    
    # 添加模組
    print(f"\n步驟 1: 添加模組到 set")
    test_set.add(module)
    print(f"  Set 大小: {len(test_set)}")
    print(f"  模組在 set 中: {module in test_set}")
    print(f"  Set 內容: {test_set}")
    
    # 檢查 identity
    print(f"\n步驟 2: 檢查 identity")
    for item in test_set:
        print(f"  Set 中的物件 ID: {id(item)}")
        print(f"  原始模組 ID: {id(module)}")
        print(f"  ID 相同: {id(item) == id(module)}")
        print(f"  物件相同 (is): {item is module}")
        print(f"  物件相等 (==): {item == module}")
    
    # 嘗試移除
    print(f"\n步驟 3: 嘗試 discard()")
    print(f"  移除前 set 大小: {len(test_set)}")
    test_set.discard(module)
    print(f"  移除後 set 大小: {len(test_set)}")
    print(f"  模組還在 set 中: {module in test_set}")
    
    if len(test_set) > 0:
        print(f"\n❌ 警告: discard() 失敗！模組仍在 set 中")
        for item in test_set:
            print(f"  殘留物件: {item}")
            print(f"  殘留物件 ID: {id(item)}")
    else:
        print(f"\n✅ discard() 成功！set 已清空")
    
    # 測試 _sub_window 屬性的影響
    print("\n" + "=" * 80)
    print("測試 3: _sub_window 屬性是否影響 hash")
    print("=" * 80)
    
    module2 = SpeedAnalysisModule()
    test_set2 = set()
    test_set2.add(module2)
    
    print(f"添加前 hash: {hash(module2) if hasattr(module2, '__hash__') else 'N/A'}")
    
    # 模擬設置 _sub_window（如同真實流程）
    class FakeSubWindow:
        pass
    
    module2._sub_window = FakeSubWindow()
    print(f"設置 _sub_window 後 hash: {hash(module2) if hasattr(module2, '__hash__') else 'N/A'}")
    
    print(f"模組還在 set 中: {module2 in test_set2}")
    test_set2.discard(module2)
    print(f"discard() 後 set 大小: {len(test_set2)}")
    
    # 檢查基類
    print("\n" + "=" * 80)
    print("測試 4: 檢查 SpeedAnalysisModule 的繼承鏈")
    print("=" * 80)
    
    print(f"MRO (Method Resolution Order):")
    for i, cls in enumerate(SpeedAnalysisModule.__mro__):
        print(f"  {i}. {cls}")
        if hasattr(cls, '__hash__'):
            print(f"     - 定義了 __hash__")
        if hasattr(cls, '__eq__'):
            print(f"     - 定義了 __eq__")

if __name__ == '__main__':
    diagnose_set_behavior()
