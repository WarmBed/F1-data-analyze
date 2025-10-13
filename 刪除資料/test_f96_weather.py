"""
Function 96 - Race Weather Forecast 測試腳本
測試 CLI -f96 功能
"""

import subprocess
import sys
from pathlib import Path

print("=" * 80)
print("測試 Function 96 - Race Weather Forecast")
print("=" * 80)

# 測試 1: 自動選擇下一場比賽（2025年）
print("\n[測試 1] 自動選擇下一場比賽")
print("指令: python f1_analysis_modular_main.py -f 96 -y 2025")
print("-" * 80)

result1 = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "96", "-y", "2025"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

print(result1.stdout)
if result1.stderr:
    print("STDERR:", result1.stderr)

print("\n" + "=" * 80)
print(f"測試 1 結果: {'✅ 成功' if result1.returncode == 0 else '❌ 失敗'}")
print(f"退出碼: {result1.returncode}")
print("=" * 80)

# 檢查 JSON 輸出
json_dir = Path("json/weather")
if json_dir.exists():
    json_files = list(json_dir.glob("race_weather_forecast_*.json"))
    if json_files:
        print(f"\n✅ 找到 {len(json_files)} 個天氣預報 JSON 檔案:")
        for f in sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
            print(f"   📄 {f.name}")
            print(f"      大小: {f.stat().st_size / 1024:.1f} KB")
            print(f"      修改時間: {f.stat().st_mtime}")
    else:
        print("\n⚠️  未找到天氣預報 JSON 檔案")
else:
    print("\n⚠️  json/weather 目錄不存在")

# 測試 2: 指定賽事（日本站）
print("\n" + "=" * 80)
print("[測試 2] 指定賽事 - 日本站")
print("指令: python f1_analysis_modular_main.py -f 96 -y 2025 -r Japan")
print("-" * 80)

result2 = subprocess.run(
    [sys.executable, "f1_analysis_modular_main.py", "-f", "96", "-y", "2025", "-r", "Japan"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

print(result2.stdout)
if result2.stderr:
    print("STDERR:", result2.stderr)

print("\n" + "=" * 80)
print(f"測試 2 結果: {'✅ 成功' if result2.returncode == 0 else '❌ 失敗'}")
print(f"退出碼: {result2.returncode}")
print("=" * 80)

# 總結
print("\n" + "=" * 80)
print("📊 測試總結")
print("=" * 80)
print(f"測試 1 (自動選擇): {'✅ 通過' if result1.returncode == 0 else '❌ 失敗'}")
print(f"測試 2 (指定賽事): {'✅ 通過' if result2.returncode == 0 else '❌ 失敗'}")
print("\n預期功能:")
print("✓ 調用 Open-Meteo API 獲取天氣數據")
print("✓ 生成 JSON 檔案到 json/weather/ 目錄")
print("✓ 顯示比賽日前2天、前1天、當天的天氣預報")
print("✓ 包含前2年歷史天氣數據")
print("✓ 智能刷新機制（12小時內使用快取）")
print("=" * 80)
