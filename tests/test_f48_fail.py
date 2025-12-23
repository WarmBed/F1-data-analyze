#!/usr/bin/env python3
"""
測試 F48 失敗原因
"""

import sys
sys.path.insert(0, '.')

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper

# 創建映射器
mapper = F1AnalysisFunctionMapper()

# 載入數據
print("載入 2018 Great Britain FP3...")
load_result = mapper._load_data(year=2018, race="Great Britain", session_type="FP3")
print(f"載入結果: {load_result.get('success')}")

if not load_result.get('success'):
    print(f"載入失敗: {load_result.get('message')}")
    sys.exit(1)

# 執行 F48
print("\n執行 F48 分析...")
result = mapper.execute_function(
    function_id=48,
    year=2018,
    race="Great Britain",
    session="FP3"
)

print(f"\n結果: {result.get('success')}")
print(f"訊息: {result.get('message')}")

if not result.get('success'):
    sys.exit(1)
