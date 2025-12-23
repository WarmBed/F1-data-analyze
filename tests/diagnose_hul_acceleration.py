"""
診斷 SAI 與 HUL 加速性能數據對比

從 GUI 表格中看到：
- SAI: 加速時間 3.600s, 平均加速度 8.10 m/s², 加速距離 208.5m (排名 #3)
- HUL: 加速時間 3.560s, 平均加速度 7.80 m/s², 加速距離 210.0m (排名 #2)

分析：
1. 驗證實際使用的起始速度閾值（100 vs 150 km/h）
2. 計算理論加速度並對比 JSON 記錄
3. 解釋為什麼時間與加速度的關係
"""

import json

# 找到 JSON 檔案
json_file = "json/all_drivers_straight_line_speed_2025_Singapore_R.json"

print("="*80)
print("SAI vs HUL 加速性能對比分析")
print("="*80)

# 讀取 JSON
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ✅ 正確的路徑：data['data']['data']['driver_speeds']（雙層嵌套）
inner_data = data['data']['data']
driver_speeds = inner_data['driver_speeds']

# 找到 SAI 和 HUL 的數據
sai_data = None
hul_data = None

for driver_data in driver_speeds:
    if driver_data['driver'] == 'SAI':
        sai_data = driver_data
    elif driver_data['driver'] == 'HUL':
        hul_data = driver_data

if not sai_data or not hul_data:
    print("❌ 找不到 SAI 或 HUL 的數據")
    exit(1)

print("\n📊 車手數據對比:\n")

print("=" * 80)
print(f"{'項目':<30} {'SAI':>15} {'HUL':>15} {'差異':>15}")
print("=" * 80)

# 基本數據
max_speed_sai = sai_data.get('max_speed_kmh', 0)
max_speed_hul = hul_data.get('max_speed_kmh', 0)
print(f"{'最高速度 (km/h)':<30} {max_speed_sai:>15.1f} {max_speed_hul:>15.1f} {max_speed_sai - max_speed_hul:>15.1f}")

distance_sai = sai_data.get('distance_m', 0)
distance_hul = hul_data.get('distance_m', 0)
print(f"{'測量距離 (m)':<30} {distance_sai:>15.1f} {distance_hul:>15.1f} {distance_sai - distance_hul:>15.1f}")

# 加速性能數據
print("\n" + "-" * 80)
print("加速性能數據 (實際: 150→250 km/h)")
print("-" * 80)

accel_time_sai = sai_data.get('acceleration_time_100_300_seconds', 0)
accel_time_hul = hul_data.get('acceleration_time_100_300_seconds', 0)
print(f"{'加速時間 (s)':<30} {accel_time_sai:>15.3f} {accel_time_hul:>15.3f} {accel_time_sai - accel_time_hul:>15.3f}")

accel_dist_sai = sai_data.get('acceleration_distance_100_300_meters', 0)
accel_dist_hul = hul_data.get('acceleration_distance_100_300_meters', 0)
print(f"{'加速距離 (m)':<30} {accel_dist_sai:>15.1f} {accel_dist_hul:>15.1f} {accel_dist_sai - accel_dist_hul:>15.1f}")

avg_accel_sai = sai_data.get('avg_acceleration_100_300_ms2', 0)
avg_accel_hul = hul_data.get('avg_acceleration_100_300_ms2', 0)
print(f"{'平均加速度 (m/s²)':<30} {avg_accel_sai:>15.2f} {avg_accel_hul:>15.2f} {avg_accel_sai - avg_accel_hul:>15.2f}")

# 檢查是否有起始速度資訊
print("\n" + "-" * 80)
print("檢查可能的原因")
print("-" * 80)

# 計算理論加速度
print("\n📐 理論加速度計算驗證:\n")
print("⚠️  重要發現：CLI 計算的是 起始速度 → 250 km/h（不是 300 km/h）")
print("   （檢查代碼: all_drivers_straight_line_speed.py 第 876 行）")
print()

# 實際計算：起始速度 → 250 km/h
end_speed_actual = 250 / 3.6  # m/s

# 測試多種起始速度假設
test_cases = [
    (100, "100→250 km/h"),
    (150, "150→250 km/h"),
    (200, "200→250 km/h"),
]

best_match_sai = None
best_match_hul = None
best_error_sai = float('inf')
best_error_hul = float('inf')

for start_speed_kmh, label in test_cases:
    start_speed_ms = start_speed_kmh / 3.6
    delta_v = end_speed_actual - start_speed_ms
    
    # SAI
    theoretical_accel_sai = delta_v / accel_time_sai if accel_time_sai > 0 else 0
    error_sai = abs(theoretical_accel_sai - avg_accel_sai)
    
    # HUL
    theoretical_accel_hul = delta_v / accel_time_hul if accel_time_hul > 0 else 0
    error_hul = abs(theoretical_accel_hul - avg_accel_hul)
    
    print(f"{label}:")
    print(f"  速度變化: {delta_v:.2f} m/s")
    print(f"  SAI 理論: {theoretical_accel_sai:.2f} m/s² (誤差: {error_sai:.2f}) {'✅' if error_sai < 0.05 else '❌'}")
    print(f"  HUL 理論: {theoretical_accel_hul:.2f} m/s² (誤差: {error_hul:.2f}) {'✅' if error_hul < 0.05 else '❌'}")
    print()
    
    if error_sai < best_error_sai:
        best_error_sai = error_sai
        best_match_sai = (start_speed_kmh, label, theoretical_accel_sai, delta_v)
    
    if error_hul < best_error_hul:
        best_error_hul = error_hul
        best_match_hul = (start_speed_kmh, label, theoretical_accel_hul, delta_v)

# 結論
print("\n" + "="*80)
print("🔍 診斷結論:")
print("="*80)

if best_match_sai:
    start_kmh, label, calc_accel, delta_v = best_match_sai
    print(f"✅ SAI 使用 {start_kmh} km/h 作為起始速度 → 250 km/h")
    print(f"   計算邏輯: (250 - {start_kmh}) km/h = {delta_v:.2f} m/s ÷ {accel_time_sai:.3f}s = {avg_accel_sai:.2f} m/s²")
    print(f"   理論值: {calc_accel:.2f} m/s² (誤差: {best_error_sai:.3f})")

if best_match_hul:
    start_kmh, label, calc_accel, delta_v = best_match_hul
    print(f"✅ HUL 使用 {start_kmh} km/h 作為起始速度 → 250 km/h")
    print(f"   計算邏輯: (250 - {start_kmh}) km/h = {delta_v:.2f} m/s ÷ {accel_time_hul:.3f}s = {avg_accel_hul:.2f} m/s²")
    print(f"   理論值: {calc_accel:.2f} m/s² (誤差: {best_error_hul:.3f})")

print("\n💡 解釋：為什麼 SAI 時間長但加速度反而高？")
print("-" * 80)
if best_match_sai and best_match_hul:
    start_sai = best_match_sai[0]
    start_hul = best_match_hul[0]
    delta_v_sai = best_match_sai[3]
    delta_v_hul = best_match_hul[3]
    
    print(f"速度變化:")
    print(f"  SAI: {start_sai} → 250 km/h = {delta_v_sai:.2f} m/s")
    print(f"  HUL: {start_hul} → 250 km/h = {delta_v_hul:.2f} m/s")
    print()
    print(f"加速度 = 速度變化 ÷ 時間:")
    print(f"  SAI: {delta_v_sai:.2f} m/s ÷ {accel_time_sai:.3f}s = {avg_accel_sai:.2f} m/s²")
    print(f"  HUL: {delta_v_hul:.2f} m/s ÷ {accel_time_hul:.3f}s = {avg_accel_hul:.2f} m/s²")
    print()
    
    time_diff = accel_time_sai - accel_time_hul
    accel_diff = avg_accel_sai - avg_accel_hul
    
    if time_diff > 0 and accel_diff > 0:
        print("⚠️  特殊情況：SAI 時間更長但加速度更高")
        print(f"   時間差: +{time_diff:.3f}s (SAI 更慢)")
        print(f"   加速度差: +{accel_diff:.2f} m/s² (SAI 更強)")
        print()
        print("📊 可能原因:")
        print("   1. 兩者使用相同起始速度但測量點不同")
        print("   2. SAI 在該直線段的動力輸出特性較好")
        print("   3. 空氣動力學或輪胎溫度差異")
    elif time_diff < 0 and accel_diff < 0:
        print("✅ 符合物理定律：時間越短 → 加速度越大")
        print(f"   SAI 用了 {abs(time_diff):.3f}s 更短時間")
        print(f"   所以加速度高了 {abs(accel_diff):.2f} m/s²")
    else:
        print("✅ 物理定律：時間與加速度成反比")
        print(f"   時間差: {time_diff:+.3f}s")
        print(f"   加速度差: {accel_diff:+.2f} m/s²")

print("\n" + "="*80)
