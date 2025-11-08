"""完整診斷：模擬 GUI 的車手載入流程"""
import json
import glob
import os

print("=" * 70)
print("模擬 GUI 車手列表載入流程（f1t_gui_main.py:910-1000）")
print("=" * 70)

year = "2025"
race = "Singapore"  # 假設選擇新加坡

# ========== 步驟 1: 嘗試從進站 JSON 讀取 ==========
print(f"\n📋 步驟 1: 嘗試從進站分析 JSON 讀取...")
print(f"   年份: {year}, 賽事: {race}")

pitstop_patterns = [
    f"json/pitstop_analysis_{year}_{race}*.json",
    f"json_exports/pitstop_analysis_{year}_{race}*.json",
    f"cache/driver_fastest_pitstop_{year}_{race}*.pkl",
    f"json/driver_pitstop_summary_{year}*.json"
]

drivers = []
found_file = None

for pattern in pitstop_patterns:
    files = glob.glob(pattern)
    if files:
        found_file = files[0]
        print(f"   ✅ 找到檔案: {os.path.basename(found_file)}")
        
        if found_file.endswith('.json'):
            with open(found_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 嘗試提取車手
            if 'drivers' in data:
                drivers = data['drivers']
                print(f"   ✅ 從 data['drivers'] 提取")
            elif 'data' in data and isinstance(data['data'], dict):
                for key, value in data['data'].items():
                    if 'drivers' in key.lower():
                        if isinstance(value, list):
                            drivers = value
                        elif isinstance(value, dict):
                            drivers = list(value.keys())
                        print(f"   ✅ 從 data['data']['{key}'] 提取")
                        break
                
                if not drivers and 'pitstop_data' in data['data']:
                    pitstop_data = data['data']['pitstop_data']
                    if isinstance(pitstop_data, dict):
                        drivers = list(pitstop_data.keys())
                        print(f"   ✅ 從 pitstop_data.keys() 提取")
            
            if drivers:
                drivers = sorted(drivers)
                print(f"   ✅ 提取到 {len(drivers)} 個車手: {', '.join(drivers[:5])}...")
                break
            else:
                print(f"   ⚠️  檔案存在但無法提取車手")
        break

if not found_file:
    print(f"   ❌ 找不到進站分析檔案")

# ========== 步驟 2: 如果沒找到，從 team_colors 讀取 ==========
if not drivers:
    print(f"\n📋 步驟 2: 從 team_colors JSON 讀取...")
    team_color_patterns = [
        f"json/team_colors_{year}_*.json",
        f"json/team_colors_2025_*.json",
        f"json/team_colors_2024_*.json"
    ]
    
    for pattern in team_color_patterns:
        files = glob.glob(pattern)
        if files:
            latest_file = max(files, key=os.path.getmtime)
            print(f"   ✅ 找到檔案: {os.path.basename(latest_file)}")
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    color_data = json.load(f)
                    if 'data' in color_data and 'drivers' in color_data['data']:
                        drivers = sorted(list(color_data['data']['drivers'].keys()))
                        print(f"   ✅ 提取到 {len(drivers)} 個車手")
                        break
            except Exception as e:
                print(f"   ❌ 讀取失敗: {e}")

# ========== 步驟 3: 使用預設列表 ==========
if not drivers:
    print(f"\n📋 步驟 3: 使用 2025 年預設車手列表...")
    drivers = ["ALB", "ALO", "ANT", "BEA", "BOR", "COL", "DOO", "GAS", "HAD", "HAM", 
              "HUL", "LAW", "LEC", "NOR", "OCO", "PIA", "RUS", "SAI", "STR", "TSU", "VER"]
    print(f"   ✅ 載入預設列表 {len(drivers)} 個車手")

# ========== 結果診斷 ==========
print("\n" + "=" * 70)
print(f"最終載入的車手列表（共 {len(drivers)} 位）")
print("=" * 70)
print(", ".join(drivers))

print("\n" + "=" * 70)
print("問題診斷:")
print("=" * 70)
new_drivers = ["ANT", "BEA", "BOR", "DOO", "HAD", "LAW"]
old_drivers = ["PER", "SAR", "MAG", "BOT", "ZHO"]

print("\n2025 新車手檢查:")
for driver in new_drivers:
    status = "✅" if driver in drivers else "❌ 缺失"
    print(f"  {status} {driver}")

print("\n2024 已離開車手檢查:")
for driver in old_drivers:
    status = "❌ 仍存在" if driver in drivers else "✅ 已移除"
    print(f"  {status} {driver}")

print("\n" + "=" * 70)
print("根本原因分析:")
print("=" * 70)
if 'PER' in drivers:
    print("⚠️  問題確認：載入的車手列表包含 2024 年陣容")
    if found_file and 'pitstop' in found_file.lower():
        print(f"⚠️  原因：從進站 JSON 讀取到舊數據: {os.path.basename(found_file)}")
        print("💡 解決方案：")
        print("   1. 優先使用 team_colors JSON（F98 生成）")
        print("   2. 或者重新執行 F13 功能生成新的進站數據")
else:
    print("✅ 車手列表正確，包含 2025 年完整陣容")
