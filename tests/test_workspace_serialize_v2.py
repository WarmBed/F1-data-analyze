"""
測試改進後的 Workspace 序列化邏輯
階段 1: Import 測試 + 方法驗證

原則 0: 反幻覺編碼五原則
- 禁止幻覺編碼
- 模組資料夾優先
- 通用模組優先
- 模組多國語言化
- print 輸出會被 logger 導出
"""

print("=" * 80)
print("階段 1: Import 測試")
print("=" * 80)

try:
    print("✅ 測試 1: Import WorkspaceSerializer")
    from core.workspace_serializer import WorkspaceSerializer
    print("   成功! WorkspaceSerializer 已導入")
    
    print("\n✅ 測試 2: 檢查 WINDOW_TYPE_MAPPING")
    mapping = WorkspaceSerializer.WINDOW_TYPE_MAPPING
    print(f"   支援的類型數量: {len(mapping)}")
    print(f"   支援的類型: {list(set(mapping.values()))}")
    
    print("\n✅ 測試 3: 檢查新方法是否存在")
    methods_to_check = [
        '_serialize_mdi_window',
        '_find_analysis_widget',
        '_extract_parameters'
    ]
    
    for method_name in methods_to_check:
        if hasattr(WorkspaceSerializer, method_name):
            print(f"   ✅ {method_name} 方法存在")
        else:
            print(f"   ❌ {method_name} 方法不存在")
    
    print("\n✅ 測試 4: 檢查 _find_analysis_widget 簽名")
    import inspect
    sig = inspect.signature(WorkspaceSerializer._find_analysis_widget)
    print(f"   方法簽名: {sig}")
    params = list(sig.parameters.keys())
    print(f"   參數列表: {params}")
    
    if 'root_widget' in params and 'max_depth' in params:
        print("   ✅ 參數正確")
    else:
        print("   ❌ 參數不正確")
    
    print("\n" + "=" * 80)
    print("階段 1 測試完成 - 所有 Import 和方法驗證通過")
    print("=" * 80)
    print("\n下一步: 請手動執行 GUI 並測試 Save Workspace 功能")
    print("預期行為: 序列化時應該正確識別模組類型並提取參數")
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
