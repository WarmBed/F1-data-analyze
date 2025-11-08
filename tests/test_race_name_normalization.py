"""測試賽道名稱標準化功能"""
import sys
import os

print("=" * 80)
print("🧪 測試賽道名稱標準化功能")
print("=" * 80)

# 測試 .title() 方法的轉換效果
test_cases = [
    # (輸入, 預期輸出)
    ("japan", "Japan"),
    ("JAPAN", "Japan"),
    ("Japan", "Japan"),
    ("JaPaN", "Japan"),
    ("china", "China"),
    ("CHINA", "China"),
    ("australia", "Australia"),
    ("saudi arabia", "Saudi Arabia"),
    ("SAUDI ARABIA", "Saudi Arabia"),
    ("united states", "United States"),
    ("abu dhabi", "Abu Dhabi"),
    ("las vegas", "Las Vegas"),
    ("emilia romagna", "Emilia Romagna"),
]

print("\n📋 測試用例:")
print(f"{'輸入':<20} {'→':<5} {'輸出':<20} {'狀態':<10}")
print("-" * 60)

all_passed = True
for input_name, expected_output in test_cases:
    actual_output = input_name.title()
    status = "✅ 通過" if actual_output == expected_output else "❌ 失敗"
    if actual_output != expected_output:
        all_passed = False
    print(f"{input_name:<20} {'→':<5} {actual_output:<20} {status:<10}")
    if actual_output != expected_output:
        print(f"  預期: {expected_output}, 實際: {actual_output}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ 所有測試通過！")
else:
    print("❌ 部分測試失敗！")

# 檢查修改後的檔案
print("\n" + "=" * 80)
print("📄 檢查修改後的檔案")
print("=" * 80)

files_to_check = [
    ("CLI_modules/cli/analyzer/brake_performance_analyzer.py", "race_name = race_name.title()"),
    ("CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py", "race_name = race_name.title()"),
]

for file_path, search_string in files_to_check:
    print(f"\n檢查: {file_path}")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if search_string in content:
            print(f"  ✅ 找到標準化代碼: {search_string}")
            
            # 找出包含該代碼的行號
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if search_string in line:
                    print(f"  位置: Line {i}")
                    # 顯示上下文（前後 2 行）
                    start = max(0, i - 3)
                    end = min(len(lines), i + 2)
                    print(f"\n  上下文:")
                    for j in range(start, end):
                        prefix = "  → " if j == i - 1 else "    "
                        print(f"{prefix}{j+1:4d}: {lines[j]}")
                    break
        else:
            print(f"  ❌ 未找到標準化代碼")
    else:
        print(f"  ⚠️  檔案不存在")

print("\n" + "=" * 80)
print("🎯 下一步：實際測試")
print("=" * 80)

print("""
建議執行以下測試：

1. 測試小寫賽道名稱（煞車分析）:
   python f1_analysis_modular_main.py -f 34 -y 2025 -r japan -s R

2. 測試小寫賽道名稱（直線速度分析）:
   python f1_analysis_modular_main.py -f 48 -y 2025 -r china -s R

3. 測試多單字賽道名稱:
   python f1_analysis_modular_main.py -f 34 -y 2025 -r "saudi arabia" -s R

4. 測試 API 調用（外網）:
   curl -X POST https://api.f1telemetrystationpro.org/analyze \\
     -H "Content-Type: application/json" \\
     -d '{"function_id": "34", "year": 2025, "race": "japan", "session": "R"}'
""")

print("=" * 80)
