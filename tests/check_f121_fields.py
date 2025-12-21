"""檢查 F121 完整欄位結構"""
import json

# 讀取 JSON
data = json.load(open('json/fp2_straight_line_all_laps_analysis_2025_Abu Dhabi_R.json', 'r', encoding='utf-8'))

print("=" * 80)
print("F121 JSON 完整欄位結構")
print("=" * 80)
print()

print("【頂層欄位】")
for key in data.keys():
    value = data[key]
    if isinstance(value, (dict, list)):
        print(f"  • {key}: {type(value).__name__}")
    else:
        print(f"  • {key}: {value}")
print()

print("【drivers 陣列欄位】(以 HAM 為例)")
ham = next((d for d in data.get('drivers', []) if d['driver'] == 'HAM'), None)
if ham:
    for key, value in ham.items():
        value_type = type(value).__name__
        
        if isinstance(value, dict):
            print(f"  • {key}: {value_type}")
            print(f"    └─ 子欄位:")
            for subkey, subvalue in value.items():
                print(f"       • {subkey}: {subvalue}")
        elif isinstance(value, list):
            print(f"  • {key}: {value_type} (長度: {len(value)})")
            if len(value) <= 5:
                print(f"       值: {value}")
            else:
                print(f"       值: {value[:3]} ... {value[-2:]}")
        else:
            print(f"  • {key}: {value}")
print()

print("【summary 欄位】")
summary = data.get('summary', {})
if summary:
    for key, value in summary.items():
        print(f"  • {key}: {value}")
else:
    print("  (無 summary 欄位)")
print()

print("【main_straight 欄位】")
main_straight = data.get('main_straight', {})
if main_straight:
    for key, value in main_straight.items():
        print(f"  • {key}: {value}")
else:
    print("  (無 main_straight 欄位)")

print()
print("=" * 80)
print(f"總車手數: {len(data.get('drivers', []))}")
print("=" * 80)
