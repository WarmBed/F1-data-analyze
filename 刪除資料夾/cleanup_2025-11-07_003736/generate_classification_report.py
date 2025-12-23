import json

print("=" * 80)
print("🎉 2025 F1 部件變更分類最終報告")
print("=" * 80)

# 載入分類結果
with open('2025_f1_parts_changes_classified.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 統計各分類
stats = {}
for item in data:
    change_type = item.get('變更類型', '未知')
    stats[change_type] = stats.get(change_type, 0) + 1

total = len(data)
print(f"\n✅ 總記錄數: {total} 筆")
print(f"\n📊 分類結果統計:")
print("-" * 80)

# 排序並顯示
for change_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    percentage = count / total * 100
    bar_length = int(percentage / 2)
    bar = "█" * bar_length
    
    # 添加 emoji
    if "未分類" in change_type:
        emoji = "⚠️ "
    elif "升級" in change_type:
        emoji = "🚀"
    elif "重大" in change_type:
        emoji = "⚙️ "
    elif "變更" in change_type:
        emoji = "🔧"
    elif "參數" in change_type:
        emoji = "💻"
    elif "安全" in change_type:
        emoji = "🛡️ "
    elif "維修" in change_type:
        emoji = "🔨"
    else:
        emoji = "  "
    
    print(f"  {emoji} {change_type:42} {count:3} 筆 ({percentage:5.1f}%) {bar}")

print("-" * 80)

# 計算分類成功率
classified = total - stats.get('未分類 (Unclassified)', 0)
success_rate = classified / total * 100
print(f"  ✅ 分類成功: {classified}/{total} 筆 ({success_rate:.1f}%)")
print(f"  ⚠️  未分類: {stats.get('未分類 (Unclassified)', 0)} 筆 ({(100-success_rate):.1f}%)")

# 墨西哥詳細分析
print(f"\n🇲🇽 墨西哥數據驗證:")
print("-" * 80)
mexico_data = [item for item in data if item.get('比賽') == 'Mexico City']
mexico_stats = {}
for item in mexico_data:
    change_type = item.get('變更類型', '未知')
    mexico_stats[change_type] = mexico_stats.get(change_type, 0) + 1

print(f"  總記錄數: {len(mexico_data)} 筆")
print(f"  分類分布:")
for change_type, count in sorted(mexico_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"    • {change_type}: {count} 筆")

print(f"\n  ✅ 驗證結果:")
rear_brake = [item for item in mexico_data if 'brake friction material' in item.get('部件', '').lower()]
gaiter = [item for item in mexico_data if 'gaiter' in item.get('部件', '').lower()]
param_changes = [item for item in mexico_data if 'parameter changes' in item.get('部件', '').lower()]

if rear_brake:
    print(f"    ✅ 'Rear brake friction material' → {rear_brake[0].get('變更類型')}")
if gaiter:
    print(f"    ✅ 'RHS rear lower wishbone gaiter' → {gaiter[0].get('變更類型')}")
if param_changes:
    print(f"    ✅ 'Parameter changes associated...' → {param_changes[0].get('變更類型')}")

# Top 車隊分析
print(f"\n🏆 各車隊分類分布 (TOP 5):")
print("-" * 80)

team_stats = {}
for item in data:
    team = item.get('車隊', 'Unknown')
    change_type = item.get('變更類型', '未知')
    
    if team not in team_stats:
        team_stats[team] = {}
    team_stats[team][change_type] = team_stats[team].get(change_type, 0) + 1

# 按總數排序
top_teams = sorted(team_stats.items(), key=lambda x: sum(x[1].values()), reverse=True)[:5]

for team, types in top_teams:
    total_team = sum(types.values())
    print(f"\n  {team} (總計 {total_team} 筆):")
    for change_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"    • {change_type}: {count} 筆")

# 檔案資訊
print(f"\n📁 輸出檔案:")
print("-" * 80)
print(f"  • 2025_f1_parts_changes_complete.json (原始數據)")
print(f"  • 2025_f1_parts_changes_classified.json (分類結果)")
print(f"  • 包含欄位: 變更類型、類型說明、匹配關鍵字、分類信心度")

print("\n" + "=" * 80)
print("✅ 分類報告生成完成")
print("=" * 80)
