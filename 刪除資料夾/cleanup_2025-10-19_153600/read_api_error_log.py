"""讀取 API 錯誤日誌"""

log_file = "logs/f1_api_error_2025-10-18.log"

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"總行數: {len(lines)}")
print("\n最後 50 行:")
print("=" * 80)

for line in lines[-50:]:
    print(line.rstrip())
