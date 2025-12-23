"""讀取最新的 CLI 日誌並分析錯誤"""

log_file = "logs/f1_cli_error_2025-10-18.log"

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"總行數: {len(lines)}")
print("\n" + "=" * 80)
print("最後 30 行 (CLI 錯誤日誌):")
print("=" * 80)

for line in lines[-30:]:
    print(line.rstrip())

# 也檢查 CLI 正常日誌
print("\n" + "=" * 80)
print("CLI 正常日誌最後 30 行:")
print("=" * 80)

log_file2 = "logs/f1_cli_2025-10-18.log"
with open(log_file2, 'r', encoding='utf-8', errors='ignore') as f:
    lines2 = f.readlines()

for line in lines2[-30:]:
    print(line.rstrip())
