"""測試 brake_performance_loader.py 的 function_id 修正"""

print("[TEST] 開始測試 function_id 修正...")

try:
    from modules.gui.all_drivers_brake_performance_analysis.brake_performance_loader import BrakePerformanceDataLoader
    
    loader = BrakePerformanceDataLoader()
    print("[SUCCESS] ✅ Import 成功")
    print(f"類別名稱: {loader.__class__.__name__}")
    print(f"ANALYSIS_TYPE: {loader.ANALYSIS_TYPE}")
    
    # 檢查配置
    config = loader.ANALYSIS_TYPES.get("brake_performance")
    if config:
        print(f"\n[CONFIG] 配置檢查:")
        print(f"  cli_function: {config.cli_function}")
        print(f"  display_name: {config.display_name}")
        print(f"  debug_prefix: {config.debug_prefix}")
        
        if config.cli_function == "34":
            print(f"\n✅ [PASS] cli_function 已正確設置為: 34")
        else:
            print(f"\n❌ [FAIL] cli_function 錯誤: {config.cli_function} (應為 34)")
    else:
        print("❌ 配置未找到")
    
    print("\n[TEST] ✅ 所有測試通過！")
    
except ImportError as e:
    print(f"[ERROR] ❌ Import 失敗: {e}")
except Exception as e:
    print(f"[ERROR] ❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
