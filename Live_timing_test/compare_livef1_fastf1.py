"""
LiveF1 vs fastf1 資料對比測試
目標: 提取 HAM Lap 10 速度資料並比較數量
"""
import pandas as pd

print("="*70)
print("LiveF1 vs fastf1: HAM Lap 10 資料對比")
print("="*70)

# ========== Part 1: LiveF1 ==========
print("\n[Part 1] 使用 LiveF1 提取資料")
print("-"*70)

try:
    import livef1
    
    print("[1.1] 載入 2025 日本站...")
    session_livef1 = livef1.get_session(
        season=2025,
        meeting_identifier="Japan",
        session_identifier="Race"
    )
    
    print("[1.2] 生成 Silver layer...")
    session_livef1.generate(silver=True)
    
    print("[1.3] 取得 laps 資料...")
    laps_livef1 = session_livef1.get_laps()
    
    print(f"  總圈數資料: {len(laps_livef1)}")
    print(f"  可用欄位: {list(laps_livef1.columns)[:10]}...")
    
    # 檢查是否有 DriverNo 欄位
    if 'DriverNo' in laps_livef1.columns:
        print(f"  車手清單: {sorted(laps_livef1['DriverNo'].unique())}")
        
        # 過濾 HAM (44號)
        ham_laps_livef1 = laps_livef1[laps_livef1['DriverNo'] == 44]
        print(f"\n[1.4] HAM 總圈數: {len(ham_laps_livef1)}")
        
        if len(ham_laps_livef1) >= 10:
            # 取得 Lap 10
            if 'lap_number' in ham_laps_livef1.columns:
                ham_lap10_livef1 = ham_laps_livef1[ham_laps_livef1['lap_number'] == 10]
            else:
                # 如果沒有 lap_number，用索引
                ham_lap10_livef1 = ham_laps_livef1.iloc[9:10]
            
            print(f"[1.5] Lap 10 資料:")
            print(f"  記錄數: {len(ham_lap10_livef1)}")
            
            # 嘗試取得遙測
            print("\n[1.6] 嘗試取得遙測資料...")
            telemetry_livef1 = session_livef1.get_car_telemetry()
            
            if telemetry_livef1 is not None:
                print(f"  遙測總記錄: {len(telemetry_livef1)}")
                print(f"  遙測欄位: {list(telemetry_livef1.columns)[:10]}...")
                
                # 過濾 HAM + Lap 10
                if 'DriverNo' in telemetry_livef1.columns and 'lap_number' in telemetry_livef1.columns:
                    ham_lap10_tel_livef1 = telemetry_livef1[
                        (telemetry_livef1['DriverNo'] == 44) &
                        (telemetry_livef1['lap_number'] == 10)
                    ]
                    
                    if 'speed' in ham_lap10_tel_livef1.columns:
                        speed_livef1 = ham_lap10_tel_livef1['speed'].dropna()
                        livef1_count = len(speed_livef1)
                        livef1_min = speed_livef1.min()
                        livef1_max = speed_livef1.max()
                        livef1_mean = speed_livef1.mean()
                        
                        print(f"\n[LiveF1 結果]")
                        print(f"  速度資料點: {livef1_count}")
                        print(f"  速度範圍: {livef1_min:.1f} - {livef1_max:.1f} km/h")
                        print(f"  平均速度: {livef1_mean:.1f} km/h")
                    else:
                        print("  [WARNING] 遙測中無 'speed' 欄位")
                        livef1_count = 0
                else:
                    print("  [WARNING] 遙測中缺少 DriverNo 或 lap_number 欄位")
                    livef1_count = 0
            else:
                print("  [WARNING] 無法取得遙測資料")
                livef1_count = 0
        else:
            print(f"  [ERROR] HAM 只有 {len(ham_laps_livef1)} 圈")
            livef1_count = 0
    else:
        print("  [ERROR] laps 資料中無 DriverNo 欄位")
        print(f"  可用欄位: {list(laps_livef1.columns)}")
        livef1_count = 0
        
except Exception as e:
    print(f"[ERROR] LiveF1 失敗: {e}")
    import traceback
    traceback.print_exc()
    livef1_count = 0

# ========== Part 2: fastf1 ==========
print("\n\n[Part 2] 使用 fastf1 提取資料")
print("-"*70)

try:
    import fastf1
    
    fastf1.Cache.enable_cache('f1_analysis_cache')
    
    print("[2.1] 載入 2025 日本站...")
    session_fastf1 = fastf1.get_session(2025, 'Japan', 'R')
    session_fastf1.load()
    
    print("[2.2] 取得 HAM 資料...")
    ham_laps_fastf1 = session_fastf1.laps.pick_driver('HAM')
    print(f"  HAM 總圈數: {len(ham_laps_fastf1)}")
    
    if len(ham_laps_fastf1) >= 10:
        print("[2.3] 取得 Lap 10...")
        lap10_fastf1 = ham_laps_fastf1.iloc[9]
        
        print(f"  圈速: {lap10_fastf1['LapTime']}")
        
        print("[2.4] 取得遙測...")
        telemetry_fastf1 = lap10_fastf1.get_telemetry()
        
        speed_fastf1 = telemetry_fastf1['Speed'].dropna()
        fastf1_count = len(speed_fastf1)
        fastf1_min = speed_fastf1.min()
        fastf1_max = speed_fastf1.max()
        fastf1_mean = speed_fastf1.mean()
        
        print(f"\n[fastf1 結果]")
        print(f"  速度資料點: {fastf1_count}")
        print(f"  速度範圍: {fastf1_min:.1f} - {fastf1_max:.1f} km/h")
        print(f"  平均速度: {fastf1_mean:.1f} km/h")
    else:
        print(f"  [ERROR] HAM 只有 {len(ham_laps_fastf1)} 圈")
        fastf1_count = 0
        
except Exception as e:
    print(f"[ERROR] fastf1 失敗: {e}")
    import traceback
    traceback.print_exc()
    fastf1_count = 0

# ========== Part 3: 比較 ==========
print("\n\n[Part 3] 資料對比")
print("="*70)

print(f"\n{'項目':<20} {'LiveF1':>15} {'fastf1':>15} {'差異':>15}")
print("-"*70)
print(f"{'速度資料點數':<20} {livef1_count:>15} {fastf1_count:>15} {abs(livef1_count - fastf1_count):>15}")

if livef1_count > 0 and fastf1_count > 0:
    print(f"{'最小速度 (km/h)':<20} {livef1_min:>15.1f} {fastf1_min:>15.1f} {abs(livef1_min - fastf1_min):>15.1f}")
    print(f"{'最大速度 (km/h)':<20} {livef1_max:>15.1f} {fastf1_max:>15.1f} {abs(livef1_max - fastf1_max):>15.1f}")
    print(f"{'平均速度 (km/h)':<20} {livef1_mean:>15.1f} {fastf1_mean:>15.1f} {abs(livef1_mean - fastf1_mean):>15.1f}")
    
    # 計算差異百分比
    diff_pct = abs(livef1_count - fastf1_count) / fastf1_count * 100
    
    print(f"\n資料點差異: {diff_pct:.2f}%")
    
    if diff_pct < 5:
        print("✅ 結果: 兩者資料量非常接近!")
    elif diff_pct < 20:
        print("⚠️  結果: 兩者有些許差異")
    else:
        print("❌ 結果: 兩者差異較大")

print("\n" + "="*70)
print("測試完成!")
print("="*70)
