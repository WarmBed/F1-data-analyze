"""
分析 Lap 19 的 Gap Trend 計算細節

Gap Trend 是用線性回歸計算前 5 圈（Lap 14-19）的 Gap 變化率
"""
import pickle
from pathlib import Path
import numpy as np
from scipy import stats

pkl_path = Path("data/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

# 獲取車號映射
driver_info = data.get('driver_info', {})
tsu_number = None
nor_number = None
for number, info in driver_info.items():
    tla = info.get('driver_tla') or info.get('tla')
    if tla == 'TSU':
        tsu_number = number
    elif tla == 'NOR':
        nor_number = number

snapshots = data.get('snapshots', [])

print("=" * 80)
print("🔍 Lap 19 的 Gap Trend 計算詳解")
print("=" * 80)
print("\nGap Trend 使用 5 圈滾動窗口（Lap 14-19）計算線性回歸斜率")
print("Gap = TSU_gap_to_leader - NOR_gap_to_leader")
print("- 正值: TSU 落後 NOR")
print("- 負值: TSU 領先 NOR（Gap 變小 = NOR 正在追近）")
print("\n" + "=" * 80)

# 收集 Lap 14-19 的 Gap 數據
gap_data = []

for target_lap in range(14, 20):
    for snapshot in snapshots:
        if snapshot.get('current_lap') == target_lap:
            drivers = snapshot.get('drivers', {})
            
            tsu_data = None
            nor_data = None
            
            for driver in drivers.values():
                tla = driver.get('driver_tla')
                if tla == 'TSU':
                    tsu_data = driver
                elif tla == 'NOR':
                    nor_data = driver
            
            if tsu_data and nor_data:
                tsu_gap = float(tsu_data.get('gap_to_leader', 0))
                nor_gap = float(nor_data.get('gap_to_leader', 0))
                gap = tsu_gap - nor_gap
                
                tsu_pos = tsu_data.get('position')
                nor_pos = nor_data.get('position')
                
                gap_data.append({
                    'lap': target_lap,
                    'tsu_pos': tsu_pos,
                    'nor_pos': nor_pos,
                    'tsu_gap_to_leader': tsu_gap,
                    'nor_gap_to_leader': nor_gap,
                    'gap': gap
                })
                
                print(f"\nLap {target_lap}:")
                print(f"   TSU: P{tsu_pos}, gap_to_leader = {tsu_gap:.3f}s")
                print(f"   NOR: P{nor_pos}, gap_to_leader = {nor_gap:.3f}s")
                print(f"   Gap (TSU vs NOR) = {gap:+.3f}s")
            break

# 計算線性回歸
if len(gap_data) >= 3:
    laps = [d['lap'] for d in gap_data]
    gaps = [d['gap'] for d in gap_data]
    
    # 使用 scipy 線性回歸
    slope, intercept, r_value, p_value, std_err = stats.linregress(laps, gaps)
    
    print("\n" + "=" * 80)
    print("📊 線性回歸分析")
    print("=" * 80)
    print(f"資料點數量: {len(gap_data)}")
    print(f"斜率 (Gap Trend): {slope:.4f} s/lap")
    print(f"截距: {intercept:.4f}")
    print(f"R² 值: {r_value**2:.4f}（越接近 1 = 線性關係越強）")
    print(f"標準誤差: {std_err:.4f}")
    
    # 顯示每圈的 Gap 變化
    print("\n" + "=" * 80)
    print("📈 逐圈 Gap 變化分析")
    print("=" * 80)
    
    for i in range(1, len(gap_data)):
        prev_gap = gap_data[i-1]['gap']
        curr_gap = gap_data[i]['gap']
        gap_change = curr_gap - prev_gap
        
        print(f"\nLap {gap_data[i-1]['lap']} → Lap {gap_data[i]['lap']}:")
        print(f"   Gap 變化: {prev_gap:+.3f}s → {curr_gap:+.3f}s")
        print(f"   變化量: {gap_change:+.3f}s")
        
        if gap_change < 0:
            print(f"   ✅ NOR 追近了 {abs(gap_change):.3f} 秒")
        elif gap_change > 0:
            print(f"   ⚠️  TSU 拉開了 {gap_change:.3f} 秒")
        else:
            print(f"   ➡️  Gap 維持不變")
    
    # 計算平均每圈變化
    avg_change = (gaps[-1] - gaps[0]) / (laps[-1] - laps[0])
    print(f"\n平均每圈 Gap 變化: {avg_change:.4f} s/lap")
    print(f"線性回歸斜率: {slope:.4f} s/lap")
    print(f"差異: {abs(avg_change - slope):.4f} s/lap")
    
    # 解釋 Gap Trend 的意義
    print("\n" + "=" * 80)
    print("💡 Gap Trend 解讀")
    print("=" * 80)
    
    if slope < 0:
        print(f"斜率 = {slope:.4f} s/lap（負值）")
        print("➡️  意義: Gap 正在縮小，NOR 正在追近 TSU")
        print(f"   每圈縮小約 {abs(slope):.2f} 秒")
        print(f"   若持續此趨勢，{abs(gaps[-1]/slope):.1f} 圈後 NOR 會追上 TSU")
    elif slope > 0:
        print(f"斜率 = {slope:.4f} s/lap（正值）")
        print("➡️  意義: Gap 正在擴大，TSU 正在拉開距離")
        print(f"   每圈拉開約 {slope:.2f} 秒")
    else:
        print("斜率 = 0 s/lap")
        print("➡️  意義: Gap 維持不變，兩車速度相同")
    
    # 檢查是否有異常數據點
    print("\n" + "=" * 80)
    print("⚠️  異常值檢查")
    print("=" * 80)
    
    # 計算實際 Gap 變化 vs 預測值
    for i, d in enumerate(gap_data):
        predicted_gap = slope * d['lap'] + intercept
        residual = d['gap'] - predicted_gap
        
        print(f"\nLap {d['lap']}:")
        print(f"   實際 Gap: {d['gap']:+.3f}s")
        print(f"   預測 Gap: {predicted_gap:+.3f}s")
        print(f"   殘差: {residual:+.3f}s")
        
        if abs(residual) > 2.0:
            print(f"   ⚠️  異常！殘差超過 2 秒（可能是進站或超車）")

print("\n" + "=" * 80)
print("🎯 為什麼 Lap 19 的 Gap Trend 這麼大？")
print("=" * 80)
print("\n可能原因:")
print("1. Lap 16-17 之間 NOR 進站，Gap 從 +15.4s 突變成 -4.9s（變化 20+ 秒）")
print("2. 5 圈窗口（Lap 14-19）包含了這個巨大的進站變化")
print("3. 線性回歸計算整段趨勢，平均每圈 Gap 變化約 -4.67 s/lap")
print("4. 這個趨勢值是「歷史平均」，不是「當前實際速度差」")
print("\n⚠️  問題:")
print("- 進站造成的 Gap 突變，不應該算入「速度趨勢」")
print("- 應該只計算同一個 stint 內的趨勢（排除進站圈）")
