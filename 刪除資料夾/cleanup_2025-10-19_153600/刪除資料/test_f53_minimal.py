#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化 Function 53 測試
"""

import sys
import os
import warnings

# 忽略 FastF1 警告
warnings.filterwarnings('ignore', category=UserWarning, module='fastf1')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Function 53 最小化測試")
print("=" * 70)

# 步驟 1: 導入 Data Loader
try:
    from CLI_modules.cli.core.data_loader import F1SessionDataLoader
    print("✅ DataLoader 導入成功")
except Exception as e:
    print(f"❌ DataLoader 導入失敗: {e}")
    sys.exit(1)

# 步驟 2: 創建 Data Loader
try:
    data_loader = F1SessionDataLoader(
        year=2025,
        race_name="Australia",
        session_type="R"
    )
    print(f"✅ DataLoader 創建成功: 2025 Australia R")
except Exception as e:
    print(f"❌ DataLoader 創建失敗: {e}")
    sys.exit(1)

# 步驟 3: 載入數據
try:
    print("載入比賽數據...")
    if data_loader.load_data():
        print("✅ 數據載入成功")
    else:
        print("❌ 數據載入失敗")
        sys.exit(1)
except Exception as e:
    print(f"❌ 數據載入異常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 步驟 4: 導入 Function Mapper
try:
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    print("✅ FunctionMapper 導入成功")
except Exception as e:
    print(f"❌ FunctionMapper 導入失敗: {e}")
    sys.exit(1)

# 步驟 5: 創建 Mapper 並執行 Function 53
try:
    mapper = F1AnalysisFunctionMapper(data_loader)
    print("✅ Mapper 創建成功")
    
    print()
    print("-" * 70)
    print("執行 Function 53: 理想圈分析")
    print("-" * 70)
    
    result = mapper.execute_function(53, debug=True, save_json=True)
    
    print("-" * 70)
    print()
    
    if result.get("success"):
        print("✅ Function 53 執行成功")
        if "output_file" in result:
            print(f"📁 輸出檔案: {result['output_file']}")
    else:
        print(f"❌ Function 53 執行失敗")
        print(f"錯誤訊息: {result.get('message')}")
        
except Exception as e:
    print(f"❌ 執行異常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("測試完成")
print("=" * 70)
