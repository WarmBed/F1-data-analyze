#!/usr/bin/env python3
"""
直接測試 Function 53 執行
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Function 53 直接測試")
print("=" * 70)
print()

# 設置參數
class Args:
    year = 2025
    race = "Australia"
    session = "R"
    function = 53
    force_mode = None
    driver = None
    driver2 = None
    lap = None
    debug = True
    save_json = True
    list_races = False

args = Args()

print(f"參數: {args.year} {args.race} {args.session} Function {args.function}")
print()

# 導入 CLI 類別
try:
    from f1_analysis_modular_main import F1AnalysisModularCLI
    print("✅ CLI 類別導入成功")
except Exception as e:
    print(f"❌ CLI 類別導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# 創建 CLI 實例
try:
    print("創建 CLI 實例...")
    cli = F1AnalysisModularCLI(args)
    print("✅ CLI 實例創建成功")
except Exception as e:
    print(f"❌ CLI 實例創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# 執行分析
try:
    print("執行分析...")
    print("-" * 70)
    success = cli.run()
    print("-" * 70)
    print()
    
    if success:
        print("✅ 分析執行成功")
    else:
        print(f"❌ 分析執行失敗")
        if hasattr(cli, 'last_error_message'):
            print(f"錯誤訊息: {cli.last_error_message}")
        if hasattr(cli, 'last_error_details'):
            print(f"錯誤詳情: {cli.last_error_details}")
            
except Exception as e:
    print(f"❌ 執行過程發生異常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("測試完成")
print("=" * 70)
