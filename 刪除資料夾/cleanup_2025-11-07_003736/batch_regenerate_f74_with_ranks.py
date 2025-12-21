#!/usr/bin/env python3
"""
批次重新生成所有 F74 排位賽預測 JSON（包含名次欄位）
"""
import subprocess
import time

# 2025 賽季所有賽事
races_2025 = [
    "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
    "Miami", "Monaco", "Spain", "Canada", "Austria",
    "Great Britain", "Belgium", "Hungary", "Netherlands", "Italy",
    "Azerbaijan", "Singapore", "United States", "Mexico"
]

print("=" * 70)
print("批次重新生成 F74 排位賽預測 JSON（包含名次欄位）")
print("=" * 70)
print(f"\n📋 總共 {len(races_2025)} 個賽事")
print(f"⏰ 開始時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

success_count = 0
failed_races = []

for i, race in enumerate(races_2025, 1):
    print(f"\n[{i}/{len(races_2025)}] 正在處理: {race}")
    print("-" * 70)
    
    try:
        # 執行 F74
        cmd = [
            "python", "f1_analysis_modular_main.py",
            "-f", "74",
            "-y", "2025",
            "-r", race
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=180  # 3 分鐘超時
        )
        
        if result.returncode == 0:
            print(f"✅ {race} - 成功生成")
            success_count += 1
        else:
            print(f"❌ {race} - 失敗")
            print(f"   錯誤: {result.stderr[:200]}")
            failed_races.append(race)
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {race} - 超時（超過 3 分鐘）")
        failed_races.append(race)
    except Exception as e:
        print(f"❌ {race} - 錯誤: {e}")
        failed_races.append(race)

# 總結
print("\n" + "=" * 70)
print("批次生成完成")
print("=" * 70)
print(f"✅ 成功: {success_count}/{len(races_2025)}")
print(f"❌ 失敗: {len(failed_races)}/{len(races_2025)}")

if failed_races:
    print(f"\n失敗的賽事: {', '.join(failed_races)}")

print(f"\n⏰ 完成時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
