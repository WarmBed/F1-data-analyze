"""
深入診斷 SAI 的原始遙測數據

目標：
1. 從 JSON 找出 SAI 的加速性能數據
2. 反推實際使用的起始速度
3. 檢查是否與 HUL 使用相同的起始速度閾值
4. 驗證 CLI 計算邏輯的正確性
"""

import json

# 讀取 JSON
json_file = "json/all_drivers_straight_line_speed_2025_Singapore_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

inner_data = data['data']['data']
driver_speeds = inner_data['driver_speeds']

# 找到 SAI 和 HUL
sai = next(d for d in driver_speeds if d['driver'] == 'SAI')
hul = next(d for d in driver_speeds if d['driver'] == 'HUL')

print("="*80)
print("SAI 原始遙測數據深度分析")
print("="*80)

print("\n📦 JSON 中的所有 SAI 欄位:")
print("-" * 80)
for key, value in sai.items():
    if value is not None and value != "":
        print(f"  {key}: {value}")

print("\n" + "="*80)
print("🔬 加速性能反推分析")
print("="*80)

# 從 JSON 提取數據
accel_time_sai = sai.get('acceleration_time_100_300_seconds', 0)
avg_accel_sai = sai.get('avg_acceleration_100_300_ms2', 0)
accel_dist_sai = sai.get('acceleration_distance_100_300_meters', 0)

print(f"\nSAI 記錄的加速數據:")
print(f"  加速時間: {accel_time_sai:.3f} 秒")
print(f"  平均加速度: {avg_accel_sai:.2f} m/s²")
print(f"  加速距離: {accel_dist_sai:.1f} 米")

# 反推起始速度
# 公式: avg_accel = (v_end - v_start) / time
# 已知: avg_accel = 8.10 m/s², time = 3.600s, v_end = 250 km/h = 69.44 m/s
# 求: v_start

v_end_ms = 250 / 3.6  # 69.44 m/s
delta_v = avg_accel_sai * accel_time_sai  # 速度變化
v_start_ms = v_end_ms - delta_v
v_start_kmh = v_start_ms * 3.6

print(f"\n反推計算:")
print(f"  已知終點速度: 250 km/h = {v_end_ms:.2f} m/s")
print(f"  速度變化: {avg_accel_sai:.2f} m/s² × {accel_time_sai:.3f}s = {delta_v:.2f} m/s")
print(f"  反推起始速度: {v_end_ms:.2f} - {delta_v:.2f} = {v_start_ms:.2f} m/s")
print(f"  轉換為 km/h: {v_start_kmh:.1f} km/h")

print("\n" + "-" * 80)
print("驗證:")
if abs(v_start_kmh - 150) < 5:
    print(f"  ✅ 起始速度 {v_start_kmh:.1f} km/h 接近 150 km/h 閾值")
elif abs(v_start_kmh - 100) < 5:
    print(f"  ✅ 起始速度 {v_start_kmh:.1f} km/h 接近 100 km/h 閾值")
else:
    print(f"  ⚠️  起始速度 {v_start_kmh:.1f} km/h 不符合 100 或 150 km/h 標準閾值")
    print(f"  可能使用了實際最小速度作為起點（階梯式邏輯的第三級）")

# 對比 HUL
print("\n" + "="*80)
print("🔄 與 HUL 對比")
print("="*80)

accel_time_hul = hul.get('acceleration_time_100_300_seconds', 0)
avg_accel_hul = hul.get('avg_acceleration_100_300_ms2', 0)

delta_v_hul = avg_accel_hul * accel_time_hul
v_start_ms_hul = v_end_ms - delta_v_hul
v_start_kmh_hul = v_start_ms_hul * 3.6

print(f"\nHUL:")
print(f"  加速時間: {accel_time_hul:.3f} 秒")
print(f"  平均加速度: {avg_accel_hul:.2f} m/s²")
print(f"  反推起始速度: {v_start_kmh_hul:.1f} km/h")

print(f"\nSAI:")
print(f"  加速時間: {accel_time_sai:.3f} 秒")
print(f"  平均加速度: {avg_accel_sai:.2f} m/s²")
print(f"  反推起始速度: {v_start_kmh:.1f} km/h")

print(f"\n差異:")
print(f"  起始速度差: {v_start_kmh - v_start_kmh_hul:+.1f} km/h")
print(f"  時間差: {accel_time_sai - accel_time_hul:+.3f} 秒")
print(f"  加速度差: {avg_accel_sai - avg_accel_hul:+.2f} m/s²")

# 檢查是否有其他加速相關欄位
print("\n" + "="*80)
print("🔍 檢查 JSON 中的其他相關欄位")
print("="*80)

acceleration_fields = {k: v for k, v in sai.items() if 'accel' in k.lower() or 'speed' in k.lower() or 'continuous' in k.lower()}
print("\nSAI 的所有速度/加速度相關欄位:")
for key, value in acceleration_fields.items():
    print(f"  {key}: {value}")

# 最終結論
print("\n" + "="*80)
print("📊 最終診斷結論")
print("="*80)

if abs(v_start_kmh - v_start_kmh_hul) < 1:
    print("✅ SAI 和 HUL 使用相同的起始速度")
    print(f"   兩者都使用 {v_start_kmh:.1f} km/h 作為起點")
    print()
    print("⚠️  但這與預期的 150 km/h 閾值不符！")
    print(f"   實際起始速度: {v_start_kmh:.1f} km/h")
    print(f"   預期閾值: 150 km/h")
    print(f"   差異: {v_start_kmh - 150:.1f} km/h")
    print()
    print("💡 可能原因:")
    print("   1. CLI 實際使用了 '實際最小速度' 作為起點（階梯式邏輯第三級）")
    print("   2. 在該直線段，所有車手的最小速度都約為 {:.0f} km/h".format(v_start_kmh))
    print("   3. 需要檢查 CLI 代碼中的階梯式閾值邏輯實現")
else:
    print("⚠️  SAI 和 HUL 使用不同的起始速度！")
    print(f"   SAI: {v_start_kmh:.1f} km/h")
    print(f"   HUL: {v_start_kmh_hul:.1f} km/h")
    print(f"   差異: {v_start_kmh - v_start_kmh_hul:.1f} km/h")
    print()
    print("💡 這解釋了為什麼 SAI 時間長但加速度反而高")
    print("   因為兩者測量的速度範圍不同！")

print("\n" + "="*80)
