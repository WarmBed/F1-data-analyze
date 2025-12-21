"""等待分析完成後自動驗證和生成圖表"""
import time
import os
import json
import subprocess

json_file = 'json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json'

print("⏳ 等待 F120 分析完成...")
print("=" * 60)

# 等待 JSON 生成
max_wait = 300  # 最多等 5 分鐘
waited = 0
while not os.path.exists(json_file) and waited < max_wait:
    time.sleep(5)
    waited += 5
    if waited % 30 == 0:
        print(f"  已等待 {waited} 秒...")

if not os.path.exists(json_file):
    print("❌ 超時！JSON 檔案未生成")
    exit(1)

print(f"✅ JSON 檔案已生成！")
print("=" * 60)

# 驗證數據
print("\n📊 驗證修復效果...")
with open(json_file, encoding='utf-8') as f:
    data = json.load(f)

drivers = data['mode_a_unified']['drivers']

# ANT T6
ant = [d for d in drivers if d['driver'] == 'ANT'][0]
ant_t6 = ant["corners"]["low_speed_corner_6"]
print(f"\nANT T6 (低速彎):")
print(f"  最大速度: {ant_t6['max_speed']} km/h")
print(f"  變異係數: {ant_t6['cv']}%")
print(f"  速度範例: {ant_t6['speeds_raw'][:5]}")

# ALO T7
alo = [d for d in drivers if d['driver'] == 'ALO'][0]
alo_t7 = alo["corners"]["mid_speed_corner_5"]  # T5 是中速彎
print(f"\nALO T5 (中速彎):")
print(f"  最小速度: {alo_t7['min_speed']} km/h")
print(f"  變異係數: {alo_t7['cv']}%")

# ALO T8
alo_t8 = alo["corners"]["high_speed_corner_8"]
print(f"\nALO T8 (高速彎):")
print(f"  最小速度: {alo_t8['min_speed']} km/h")
print(f"  變異係數: {alo_t8['cv']}%")

# 修復評估
print("\n" + "=" * 60)
print("修復效果評估:")
print("=" * 60)

ant_fixed = ant_t6['max_speed'] < 100 and ant_t6['cv'] < 15
alo_t7_fixed = alo_t7['min_speed'] > 90 and alo_t7['cv'] < 15
alo_t8_fixed = alo_t8['min_speed'] > 200 and alo_t8['cv'] < 15

print(f"  ANT T6: {'✅ 已修復' if ant_fixed else '❌ 仍有異常'}")
print(f"  ALO T5: {'✅ 已修復' if alo_t7_fixed else '❌ 仍有異常'}")
print(f"  ALO T8: {'✅ 已修復' if alo_t8_fixed else '❌ 仍有異常'}")

if ant_fixed and alo_t7_fixed and alo_t8_fixed:
    print("\n🎉 數據修復成功！")
    print("\n開始生成圖表...")
    print("=" * 60)
    
    # 生成圖表
    result = subprocess.run(['python', 'visualize_f120_results.py'], 
                          capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.returncode == 0:
        print("\n✅ 圖表生成完成！")
    else:
        print(f"\n❌ 圖表生成失敗: {result.stderr}")
else:
    print("\n⚠️  修復未完全成功，請檢查代碼")

print("=" * 60)
