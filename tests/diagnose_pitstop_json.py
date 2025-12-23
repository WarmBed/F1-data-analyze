"""檢查進站 JSON 的車手列表"""
import json
import glob
import os

# 找最新的進站 JSON
pitstop_files = glob.glob("json/driver_detailed_pitstop_records_2025_*.json")
if not pitstop_files:
    print("❌ 找不到 2025 年進站 JSON 檔案")
    exit(1)

latest_file = max(pitstop_files, key=os.path.getmtime)
print(f"📂 檢查檔案: {os.path.basename(latest_file)}")
print(f"📅 修改時間: {os.path.getmtime(latest_file)}")

with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取車手列表（模擬 GUI 的邏輯）
drivers = []
if 'data' in data and 'pitstop_data' in data['data']:
    pitstop_data = data['data']['pitstop_data']
    if isinstance(pitstop_data, dict):
        drivers = sorted(list(pitstop_data.keys()))

print(f"\n{'=' * 60}")
print(f"進站 JSON 中的車手列表（共 {len(drivers)} 位）")
print(f"{'=' * 60}")
print(", ".join(drivers))

print(f"\n{'=' * 60}")
print("問題診斷:")
print(f"{'=' * 60}")
print(f"  是否包含 DOO (2025新車手): {'✅' if 'DOO' in drivers else '❌'}")
print(f"  是否包含 PER (2024已離開): {'❌ 仍存在' if 'PER' in drivers else '✅ 已移除'}")

print(f"\n{'=' * 60}")
print("結論:")
print(f"{'=' * 60}")
if 'PER' in drivers:
    print("⚠️  問題確認：進站 JSON 包含 2024 年陣容，導致 GUI 顯示舊車手列表")
    print("💡 解決方案：GUI 應優先使用 team_colors JSON，而非進站 JSON")
