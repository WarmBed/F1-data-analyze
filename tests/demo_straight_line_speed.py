"""快速示範：直線速度分析（Function 48）"""
import subprocess
import json
import os
from datetime import datetime

print("=" * 80)
print("🏎️  直線速度分析快速示範（Function 48）")
print("=" * 80)

# 示範參數
demos = [
    {"year": 2025, "race": "Japan", "session": "R", "desc": "日本大獎賽"},
    {"year": 2025, "race": "China", "session": "R", "desc": "中國大獎賽"},
    {"year": 2024, "race": "Italy", "session": "R", "desc": "義大利大獎賽（Monza 高速賽道）"},
]

print("\n📋 可用的示範分析：")
for i, demo in enumerate(demos, 1):
    print(f"   {i}. {demo['desc']} ({demo['year']} {demo['race']} {demo['session']})")

print("\n" + "=" * 80)
print("🚀 CLI 命令格式")
print("=" * 80)
print("\n基本格式：")
print("python f1_analysis_modular_main.py -f 48 -y <年份> -r <賽事> -s <會話>\n")

for i, demo in enumerate(demos, 1):
    cmd = f"python f1_analysis_modular_main.py -f 48 -y {demo['year']} -r {demo['race']} -s {demo['session']}"
    print(f"{i}. {demo['desc']}")
    print(f"   {cmd}\n")

print("=" * 80)
print("📂 輸出檔案位置")
print("=" * 80)
print("\njson/all_drivers_straight_line_speed_<年份>_<賽事>_<會話>_<時間戳>.json\n")

# 檢查現有的 JSON 檔案
json_dir = "json"
if os.path.exists(json_dir):
    files = [f for f in os.listdir(json_dir) if f.startswith("all_drivers_straight_line_speed")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(json_dir, x)), reverse=True)
    
    if files:
        print("=" * 80)
        print("📄 最近的分析結果（前 5 個）")
        print("=" * 80)
        
        for i, file in enumerate(files[:5], 1):
            filepath = os.path.join(json_dir, file)
            mtime = os.path.getmtime(filepath)
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_kb = os.path.getsize(filepath) / 1024
            
            print(f"\n{i}. {file}")
            print(f"   時間：{mtime_str}")
            print(f"   大小：{size_kb:.1f} KB")
            
            # 讀取檔案內容摘要
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if data.get('success'):
                    metadata = data.get('data', {}).get('metadata', {})
                    drivers = data.get('data', {}).get('drivers', [])
                    
                    print(f"   年份：{metadata.get('year')}")
                    print(f"   賽事：{metadata.get('race')}")
                    print(f"   會話：{metadata.get('session')}")
                    print(f"   車手數量：{len(drivers)}")
                    print(f"   統一終點速度：{metadata.get('unified_end_speed_kmh', 'N/A')} km/h")
                    
                    if drivers:
                        # 顯示前 3 名
                        print(f"   前 3 名：")
                        for j, driver in enumerate(drivers[:3], 1):
                            print(f"      {j}. {driver.get('driver')} - 加速 {driver.get('segment_accel_time_seconds', 'N/A'):.2f}s")
            except Exception as e:
                print(f"   ⚠️  無法讀取檔案：{e}")

print("\n" + "=" * 80)
print("🎯 GUI 使用方式")
print("=" * 80)
print("""
1. 啟動 GUI：python f1t_gui_main.py
2. 選擇賽事參數（年份、賽事、會話）
3. 點擊選單：分析 → 全車手直線速度分析
4. 查看結果表格和圖表
""")

print("=" * 80)
print("✨ v3.3.1 新功能")
print("=" * 80)
print("""
✅ 往後搜索高油門起點（解決 N/A 問題）
✅ 最高速度時間追蹤（新欄位）
✅ 數據回退機制（完整數據覆蓋）
✅ 錯誤處理強化（None 值檢查）
""")

print("=" * 80)
print("📚 詳細說明文件")
print("=" * 80)
print("\n請參閱：直線速度分析使用指南.md")
print("\n" + "=" * 80)
