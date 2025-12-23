"""檢查煞車分析的執行結果"""

with open('logs/f1_cli_2025-10-18.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# 找到最近的 Function 36 執行記錄
print("最近的 Function 36 執行記錄:")
print("=" * 80)

brake_lines = [l for l in lines if '36' in l or 'brake' in l.lower() or '煞車' in l]
for line in brake_lines[-30:]:
    print(line.rstrip())

# 檢查錯誤日誌
print("\n" + "=" * 80)
print("錯誤日誌:")
print("=" * 80)

with open('logs/f1_cli_error_2025-10-18.log', 'r', encoding='utf-8', errors='ignore') as f:
    error_lines = f.readlines()

brake_errors = [l for l in error_lines if '36' in l or 'brake' in l.lower() or '煞車' in l]
if brake_errors:
    for line in brake_errors[-20:]:
        print(line.rstrip())
else:
    print("無 Function 36 相關錯誤")
