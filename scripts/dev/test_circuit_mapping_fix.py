#!/usr/bin/env python3
"""測試賽道名稱映射修復"""

# 模擬映射表
CIRCUIT_NAME_TO_RACE_MAPPING = {
    "Yas Island": "Abu_Dhabi",
    "Las Vegas": "Las_Vegas",
    "Melbourne": "Australia",
}

# 測試案例
test_cases = [
    ("Yas Island", "track_circuit_data_Abu_Dhabi.json"),
    ("Las Vegas", "track_circuit_data_Las_Vegas.json"),
    ("Melbourne", "track_circuit_data_Australia.json"),
    ("Abu Dhabi", "track_circuit_data_Abu_Dhabi.json"),  # 已經是正確名稱
]

print("=" * 70)
print("賽道名稱映射測試")
print("=" * 70)

for circuit_name, expected_file in test_cases:
    # 應用映射
    mapped_name = CIRCUIT_NAME_TO_RACE_MAPPING.get(circuit_name, circuit_name)
    
    # 構建檔案名
    if mapped_name != circuit_name:
        actual_file = f"track_circuit_data_{mapped_name}.json"
        status = "✅ 映射"
    else:
        actual_file = f"track_circuit_data_{circuit_name.replace(' ', '_')}.json"
        status = "➡️  直接"
    
    match = "✅" if actual_file == expected_file else "❌"
    
    print(f"\n{status} {circuit_name:20s}")
    print(f"  → 映射名稱: {mapped_name}")
    print(f"  → 產生檔名: {actual_file}")
    print(f"  → 預期檔名: {expected_file}")
    print(f"  → 結果: {match}")

print("\n" + "=" * 70)
print("✅ 映射表測試完成")
print("=" * 70)
