"""查找最新的 Function 36 China 執行結果"""

with open('logs/f1_cli_2025-10-18.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# 找到最近一次 Function 36 China 的執行
print("=" * 80)
print("Function 36 China 執行日誌:")
print("=" * 80)

target_start = None
for i, line in enumerate(lines):
    if '21:05:23' in line and 'China' in line:
        target_start = i
        break

if target_start:
    # 顯示從 China 開始到結束的所有日誌
    for line in lines[target_start:target_start+50]:
        print(line.rstrip())
else:
    print("沒有找到 China 的執行記錄")
    # 顯示最後 20 行
    print("\n最後 20 行:")
    for line in lines[-20:]:
        print(line.rstrip())
