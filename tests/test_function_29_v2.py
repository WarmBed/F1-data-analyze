#!/usr/bin/env python3
"""
測試 Function 29 V2.0 分類器整合
"""
import sys
import os

# 設置編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 測試 Import
print("=" * 80)
print("測試 1: Import V2 分類器")
print("=" * 80)
try:
    from CLI_modules.cli.core.fia_parts_classifier import UpgradeClassifierV2
    print("✅ Import 成功: UpgradeClassifierV2")
except Exception as e:
    print(f"❌ Import 失敗: {e}")
    sys.exit(1)

# 測試分類器初始化
print("\n" + "=" * 80)
print("測試 2: 初始化分類器")
print("=" * 80)
try:
    classifier = UpgradeClassifierV2()
    print("✅ 分類器初始化成功")
except Exception as e:
    print(f"❌ 初始化失敗: {e}")
    sys.exit(1)

# 測試分類功能
print("\n" + "=" * 80)
print("測試 3: 測試分類功能")
print("=" * 80)
test_cases = [
    {
        "部件": "parameter changes associated with gearbox",
        "原始文本": "Car 04: parameter changes associated with gearbox assembly replacement"
    },
    {
        "部件": "Floor assembly (excluding skids and plank)",
        "原始文本": "Car 18: Floor assembly (excluding skids and plank)"
    },
    {
        "部件": "ICE sump rubber",
        "原始文本": "Car 04: ICE sump rubber"
    },
    {
        "部件": "From The FIA Formula One Technical Delegate",
        "原始文本": "From The FIA Formula One Technical Delegate To The Stewards"
    }
]

for idx, test in enumerate(test_cases, 1):
    result = classifier.classify_part_change(test["部件"], test["原始文本"])
    print(f"\n測試案例 {idx}:")
    print(f"  部件: {test['部件']}")
    print(f"  分類: {result['變更類型顯示']}")
    print(f"  信心度: {result['信心度']}")
    print(f"  關鍵字: {', '.join(result['匹配關鍵字'])}")

# 測試 Function 29 整合
print("\n" + "=" * 80)
print("測試 4: Function 29 整合測試")
print("=" * 80)

# 檢查資料檔案
import json
data_file_v2 = "2025_f1_parts_changes_v2_classified.json"
data_file_v1 = "2025_f1_parts_changes_classified.json"

if os.path.exists(data_file_v2):
    print(f"✅ 找到 V2 資料檔案: {data_file_v2}")
    with open(data_file_v2, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   總記錄數: {len(data)}")
    
    # 信心度分佈
    confidences = [r.get("分類信心度", 0.0) for r in data]
    high_conf = len([c for c in confidences if c >= 0.80])
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    print(f"   平均信心度: {avg_conf:.2f}")
    print(f"   高信心度 (≥0.80): {high_conf} ({high_conf/len(data)*100:.1f}%)")
    
elif os.path.exists(data_file_v1):
    print(f"⚠️  找到 V1 資料檔案: {data_file_v1}")
    print("   建議執行: python reclassify_2025_parts_v2.py 生成 V2 資料")
    with open(data_file_v1, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   總記錄數: {len(data)}")
else:
    print(f"❌ 找不到資料檔案")

# 測試 Function Mapper
print("\n" + "=" * 80)
print("測試 5: Function Mapper 整合")
print("=" * 80)
try:
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    print("✅ Function Mapper Import 成功")
    
    # 檢查 Function 29 是否存在
    mapper_instance = F1AnalysisFunctionMapper(None, None, None, None, None)
    if 29 in mapper_instance.function_mapping:
        print("✅ Function 29 已在 function_mapping 中")
    else:
        print("❌ Function 29 未在 function_mapping 中")
        
except Exception as e:
    print(f"❌ Function Mapper 測試失敗: {e}")

print("\n" + "=" * 80)
print("✅ 所有測試完成")
print("=" * 80)
