#!/usr/bin/env python3
"""檢查 brake_performance JSON 的格式是否符合 loader 的預期"""

import json
import os

json_file = "json/brake_performance_2025_Singapore_R.json"

print("=" * 80)
print("Brake Performance JSON 格式驗證")
print("=" * 80)

if not os.path.exists(json_file):
    print(f"❌ 檔案不存在: {json_file}")
    exit(1)

print(f"✅ 檔案存在: {json_file}")
print(f"   大小: {os.path.getsize(json_file)} bytes")

# 讀取 JSON
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

print("\n" + "=" * 80)
print("JSON 結構分析")
print("=" * 80)

print(f"\n1️⃣  頂層結構:")
print(f"   類型: {type(data)}")
print(f"   鍵: {list(data.keys())}")

print(f"\n2️⃣  success 欄位:")
success = data.get("success")
print(f"   值: {success}")
print(f"   類型: {type(success)}")
if not success:
    print("   ❌ success 為 False 或不存在！")
else:
    print("   ✅ success 為 True")

print(f"\n3️⃣  data 欄位 (第一層):")
first_layer = data.get("data")
print(f"   類型: {type(first_layer)}")
if isinstance(first_layer, dict):
    print(f"   鍵: {list(first_layer.keys())}")
else:
    print(f"   ❌ data 不是字典！")

print(f"\n4️⃣  data.data 欄位 (第二層嵌套):")
if isinstance(first_layer, dict) and "data" in first_layer:
    second_layer = first_layer.get("data")
    print(f"   存在第二層嵌套！")
    print(f"   類型: {type(second_layer)}")
    if isinstance(second_layer, dict):
        print(f"   鍵: {list(second_layer.keys())}")
        payload = second_layer
    else:
        print(f"   ❌ 第二層 data 不是字典！")
        payload = first_layer
else:
    print(f"   無第二層嵌套，使用第一層 data 作為 payload")
    payload = first_layer

print(f"\n5️⃣  payload.driver_brakes 欄位:")
driver_brakes = payload.get("driver_brakes") if isinstance(payload, dict) else None
print(f"   類型: {type(driver_brakes)}")
if isinstance(driver_brakes, list):
    print(f"   ✅ driver_brakes 是列表")
    print(f"   車手數量: {len(driver_brakes)}")
    if driver_brakes:
        print(f"   第一個車手鍵: {list(driver_brakes[0].keys())}")
else:
    print(f"   ❌ driver_brakes 不是列表！")

print("\n" + "=" * 80)
print("Loader _validate_data_format() 驗證邏輯")
print("=" * 80)

print("\n檢查項目:")
checks = []

# Check 1: isinstance(raw_data, dict)
check1 = isinstance(data, dict)
checks.append(("isinstance(raw_data, dict)", check1))
print(f"  1. isinstance(raw_data, dict): {check1}")

# Check 2: raw_data.get("success", False)
check2 = data.get("success", False)
checks.append(("raw_data.get('success', False)", check2))
print(f"  2. raw_data.get('success', False): {check2}")

# Check 3: isinstance(first_layer, dict)
check3 = isinstance(first_layer, dict)
checks.append(("isinstance(first_layer, dict)", check3))
print(f"  3. isinstance(first_layer, dict): {check3}")

# Check 4: isinstance(payload, dict)
check4 = isinstance(payload, dict)
checks.append(("isinstance(payload, dict)", check4))
print(f"  4. isinstance(payload, dict): {check4}")

# Check 5: isinstance(driver_brakes, list)
check5 = isinstance(driver_brakes, list)
checks.append(("isinstance(driver_brakes, list)", check5))
print(f"  5. isinstance(driver_brakes, list): {check5}")

print("\n" + "=" * 80)
print("驗證結果")
print("=" * 80)

all_passed = all(check[1] for check in checks)
if all_passed:
    print("✅ 所有檢查通過！JSON 格式符合 loader 預期")
else:
    print("❌ 驗證失敗！以下檢查未通過:")
    for check_name, result in checks:
        if not result:
            print(f"   ❌ {check_name}")

print("\n" + "=" * 80)
print("問題診斷")
print("=" * 80)

if not all_passed:
    print("\n可能的問題:")
    if not check2:
        print("  - JSON 中 success 欄位為 False 或不存在")
        print("  - 這表示 CLI 執行時可能遇到錯誤")
    if not check5:
        print("  - driver_brakes 不是列表或不存在")
        print("  - JSON 格式可能不符合預期")
else:
    print("\nJSON 格式正確，問題可能出在:")
    print("  1. 檔案搜尋時機：loader 在檔案生成前就搜尋完畢")
    print("  2. API 調用失敗：API 無法正確處理 Function 34")
    print("  3. 緩存問題：API 返回舊的或錯誤的緩存數據")
