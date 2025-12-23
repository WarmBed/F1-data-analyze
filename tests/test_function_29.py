#!/usr/bin/env python3
"""
測試 Function 29 - FIA 部件變更分析
"""
import sys
sys.path.insert(0, '.')

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper

print("=" * 80)
print("測試 Function 29 - FIA 部件變更分析")
print("=" * 80)

# 創建映射器 (不需要 data_loader)
mapper = F1AnalysisFunctionMapper(None, None, None)

# 測試 1: 基本執行
print("\n[測試 1] 基本執行 - 2025 年所有資料")
result = mapper.execute_function_by_number(29, year=2025)
if result.get("success"):
    print(f"✅ 成功: {result.get('message')}")
    print(f"   總記錄數: {result['statistics']['total_records']}")
    print(f"   變更類型: {list(result['type_percentages'].keys())}")
else:
    print(f"❌ 失敗: {result.get('message')}")

# 測試 2: 篩選車隊
print("\n[測試 2] 篩選 Red Bull Racing")
result2 = mapper.execute_function_by_number(29, year=2025, team="Red Bull Racing")
if result2.get("success"):
    print(f"✅ 成功: {result2.get('message')}")
    print(f"   Red Bull 記錄數: {result2['statistics']['total_records']}")
else:
    print(f"❌ 失敗: {result2.get('message')}")

# 測試 3: 篩選變更類型
print("\n[測試 3] 篩選 '升級套件 (Upgrade Package)'")
result3 = mapper.execute_function_by_number(29, year=2025, change_type="升級套件 (Upgrade Package)")
if result3.get("success"):
    print(f"✅ 成功: {result3.get('message')}")
    print(f"   升級套件記錄數: {result3['statistics']['total_records']}")
else:
    print(f"❌ 失敗: {result3.get('message')}")

# 測試 4: 篩選賽事
print("\n[測試 4] 篩選 Japan 賽事")
result4 = mapper.execute_function_by_number(29, year=2025, race="Japan")
if result4.get("success"):
    print(f"✅ 成功: {result4.get('message')}")
    print(f"   Japan 記錄數: {result4['statistics']['total_records']}")
else:
    print(f"❌ 失敗: {result4.get('message')}")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)
