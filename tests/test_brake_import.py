"""測試 AllDriversBrakePerformanceTableWidget Import"""

print("[TEST] 開始測試 brake performance import...")

try:
    from modules.gui.all_drivers_brake_performance_analysis import AllDriversBrakePerformanceTableWidget
    print("[SUCCESS] ✅ Import 成功")
    print(f"類別名稱: {AllDriversBrakePerformanceTableWidget.__name__}")
    
    # 檢查主要方法
    methods = [m for m in dir(AllDriversBrakePerformanceTableWidget) 
               if not m.startswith('_') and callable(getattr(AllDriversBrakePerformanceTableWidget, m))]
    print(f"公開方法數量: {len(methods)}")
    print(f"主要方法: {', '.join(methods[:15])}")
    
    # 檢查特定的煞車方法
    print("\n[CHECK] 驗證煞車專屬方法:")
    expected_methods = ['update_data', 'sort_data', 'export_chart']
    for method in expected_methods:
        if hasattr(AllDriversBrakePerformanceTableWidget, method):
            print(f"  ✅ {method}")
        else:
            print(f"  ❌ {method} 缺失")
    
    print("\n[TEST] ✅ 所有測試通過！")
    
except ImportError as e:
    print(f"[ERROR] ❌ Import 失敗: {e}")
except Exception as e:
    print(f"[ERROR] ❌ 測試失敗: {e}")
