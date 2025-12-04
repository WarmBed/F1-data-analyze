"""
快速比對 LiveF1 vs fastf1 - HAM Lap 10
直接使用本地緩存避免長時間下載
"""
import pandas as pd
import sys

print("="*70)
print("LiveF1 vs fastf1: HAM Lap 10 實際數據比對")
print("="*70)

# ========== fastf1 ==========
print("\n[1] fastf1 數據")
print("-"*70)

try:
    import fastf1
    fastf1.Cache.enable_cache('f1_analysis_cache')
    
    print("載入 2025 日本站...")
    session = fastf1.get_session(2025, 'Japan', 'R')
    session.load()
    
    ham_laps = session.laps.pick_driver('HAM')
    print(f"✅ HAM 總圈數: {len(ham_laps)}")
    
    if len(ham_laps) >= 10:
        lap10 = ham_laps.iloc[9]
        telemetry = lap10.get_telemetry()
        
        speed = telemetry['Speed'].dropna()
        
        fastf1_count = len(speed)
        fastf1_min = speed.min()
        fastf1_max = speed.max()
        fastf1_mean = speed.mean()
        fastf1_time_span = (telemetry['Time'].max() - telemetry['Time'].min()).total_seconds()
        
        # 計算時間間隔
        time_diffs = telemetry['Time'].diff().dt.total_seconds().dropna()
        fastf1_avg_interval = time_diffs.mean()
        fastf1_sampling_rate = 1 / fastf1_avg_interval
        
        print(f"\n📊 fastf1Lap 10 速度資料:")
        print(f"  樣本數: {fastf1_count}")
        print(f"  速度範圍: {fastf1_min:.1f} - {fastf1_max:.1f} km/h")
        print(f"  平均速度: {fastf1_mean:.1f} km/h")
        print(f"  時間跨度: {fastf1_time_span:.2f} 秒")
        print(f"  平均間隔: {fastf1_avg_interval*1000:.1f} ms")
        print(f"  採樣率: {fastf1_sampling_rate:.2f} Hz")
        
        # 檢查時間間隔分佈
        print(f"\n  時間間隔分佈:")
        print(f"    最小: {time_diffs.min()*1000:.1f} ms")
        print(f"    最大: {time_diffs.max()*1000:.1f} ms")
        print(f"    中位數: {time_diffs.median()*1000:.1f} ms")
        print(f"    標準差: {time_diffs.std()*1000:.1f} ms")
        
        fastf1_success = True
    else:
        print(f"❌ HAM 圈數不足")
        fastf1_success = False
        
except Exception as e:
    print(f"❌ fastf1 失敗: {e}")
    fastf1_success = False

# ========== LiveF1 ==========
print("\n\n[2] LiveF1 數據")
print("-"*70)

try:
    import livef1
    
    print("載入 2025 日本站...")
    session_livef1 = livef1.get_session(
        season=2025,
        meeting_identifier="Japan",
        session_identifier="Race"
    )
    
    # 檢查是否已有緩存
    print("嘗試讀取緩存數據...")
    
    # 先嚐試直接獲取 laps，不觸發完整 generate
    try:
        laps = session_livef1.get_laps()
        print(f"✅ 從緩存讀取成功")
        
        if 'DriverNo' in laps.columns:
            ham_laps = laps[laps['DriverNo'] == 44]
            print(f"✅ HAM 總圈數: {len(ham_laps)}")
            
            if len(ham_laps) >= 10:
                # 嘗試獲取遙測
                telemetry_livef1 = session_livef1.get_car_telemetry()
                
                if telemetry_livef1 is not None and 'DriverNo' in telemetry_livef1.columns:
                    # 過濾 HAM + Lap 10
                    if 'lap_number' in telemetry_livef1.columns:
                        ham_lap10_tel = telemetry_livef1[
                            (telemetry_livef1['DriverNo'] == 44) &
                            (telemetry_livef1['lap_number'] == 10)
                        ]
                    else:
                        # 使用時間範圍過濾
                        lap10_start = ham_laps.iloc[9]['lap_start_time'] if 'lap_start_time' in ham_laps.columns else None
                        lap10_end = ham_laps.iloc[9]['lap_end_time'] if 'lap_end_time' in ham_laps.columns else None
                        
                        if lap10_start and lap10_end:
                            ham_lap10_tel = telemetry_livef1[
                                (telemetry_livef1['DriverNo'] == 44) &
                                (telemetry_livef1['session_time'] >= lap10_start) &
                                (telemetry_livef1['session_time'] <= lap10_end)
                            ]
                        else:
                            ham_lap10_tel = pd.DataFrame()
                    
                    if len(ham_lap10_tel) > 0 and 'speed' in ham_lap10_tel.columns:
                        speed_livef1 = ham_lap10_tel['speed'].dropna()
                        
                        livef1_count = len(speed_livef1)
                        livef1_min = speed_livef1.min()
                        livef1_max = speed_livef1.max()
                        livef1_mean = speed_livef1.mean()
                        
                        # 計算時間間隔
                        if 'session_time' in ham_lap10_tel.columns:
                            time_col = ham_lap10_tel['session_time'].sort_values()
                            time_diffs_livef1 = time_col.diff().dropna()
                            livef1_avg_interval = time_diffs_livef1.mean()
                            livef1_sampling_rate = 1 / livef1_avg_interval
                            livef1_time_span = (time_col.max() - time_col.min())
                            
                            print(f"\n📊 LiveF1 Lap 10 速度資料:")
                            print(f"  樣本數: {livef1_count}")
                            print(f"  速度範圍: {livef1_min:.1f} - {livef1_max:.1f} km/h")
                            print(f"  平均速度: {livef1_mean:.1f} km/h")
                            print(f"  時間跨度: {livef1_time_span:.2f} 秒")
                            print(f"  平均間隔: {livef1_avg_interval*1000:.1f} ms")
                            print(f"  採樣率: {livef1_sampling_rate:.2f} Hz")
                            
                            print(f"\n  時間間隔分佈:")
                            print(f"    最小: {time_diffs_livef1.min()*1000:.1f} ms")
                            print(f"    最大: {time_diffs_livef1.max()*1000:.1f} ms")
                            print(f"    中位數: {time_diffs_livef1.median()*1000:.1f} ms")
                            print(f"    標準差: {time_diffs_livef1.std()*1000:.1f} ms")
                        else:
                            print(f"\n📊 LiveF1 Lap 10 速度資料:")
                            print(f"  樣本數: {livef1_count}")
                            print(f"  速度範圍: {livef1_min:.1f} - {livef1_max:.1f} km/h")
                            print(f"  平均速度: {livef1_mean:.1f} km/h")
                            print(f"  ⚠️ 無時間戳資訊")
                        
                        livef1_success = True
                    else:
                        print(f"❌ 無法獲取 Lap 10 遙測數據")
                        livef1_success = False
                else:
                    print(f"❌ 無法獲取遙測數據")
                    livef1_success = False
            else:
                print(f"❌ HAM 圈數不足")
                livef1_success = False
        else:
            print(f"❌ laps 數據缺少 DriverNo 欄位")
            livef1_success = False
            
    except Exception as cache_err:
        print(f"⚠️ 無緩存數據: {cache_err}")
        print("\n嘗試下載新數據（這可能需要幾分鐘）...")
        
        try:
            session_livef1.generate(silver=True)
            print("✅ 數據生成完成")
            
            # 重複上面的邏輯
            laps = session_livef1.get_laps()
            # ... (相同的處理邏輯)
            livef1_success = False  # 簡化起見，這裡標記為失敗
            print("💡 提示: 如需完整測試，請單獨運行 LiveF1 腳本")
            
        except Exception as gen_err:
            print(f"❌ 數據生成失敗: {gen_err}")
            livef1_success = False
        
except Exception as e:
    print(f"❌ LiveF1 失敗: {e}")
    import traceback
    traceback.print_exc()
    livef1_success = False

# ========== 比較 ==========
print("\n\n[3] 實際數據對比")
print("="*70)

if fastf1_success and livef1_success:
    print(f"\n{'指標':<25} {'LiveF1':>15} {'fastf1':>15} {'差異':>15}")
    print("-"*70)
    print(f"{'樣本數':<25} {livef1_count:>15} {fastf1_count:>15} {abs(livef1_count - fastf1_count):>15}")
    print(f"{'速度範圍 (km/h)':<25} {livef1_min:.1f}-{livef1_max:.1f:>6} {fastf1_min:.1f}-{fastf1_max:.1f:>6} {abs(livef1_min-fastf1_min):.1f}/{abs(livef1_max-fastf1_max):.1f:>6}")
    print(f"{'平均速度 (km/h)':<25} {livef1_mean:>15.1f} {fastf1_mean:>15.1f} {abs(livef1_mean - fastf1_mean):>15.1f}")
    
    if 'livef1_sampling_rate' in locals():
        print(f"{'採樣率 (Hz)':<25} {livef1_sampling_rate:>15.2f} {fastf1_sampling_rate:>15.2f} {abs(livef1_sampling_rate - fastf1_sampling_rate):>15.2f}")
        print(f"{'平均間隔 (ms)':<25} {livef1_avg_interval*1000:>15.1f} {fastf1_avg_interval*1000:>15.1f} {abs(livef1_avg_interval - fastf1_avg_interval)*1000:>15.1f}")
    
    diff_pct = abs(livef1_count - fastf1_count) / fastf1_count * 100
    
    print(f"\n📈 樣本數差異: {diff_pct:.2f}%")
    
    if diff_pct < 1:
        print("✅ 結論: LiveF1 與 fastf1 數據**完全一致**")
    elif diff_pct < 5:
        print("✅ 結論: LiveF1 與 fastf1 數據**高度一致**")
    elif diff_pct < 20:
        print("⚠️ 結論: LiveF1 與 fastf1 有**輕微差異**")
    else:
        print("❌ 結論: LiveF1 與 fastf1 有**明顯差異**")
        
elif fastf1_success:
    print("\n✅ fastf1 數據可用")
    print("❌ LiveF1 數據不可用（可能需要先下載緩存）")
    print("\n💡 建議: 運行 compare_livef1_fastf1.py 下載完整 LiveF1 數據")
    
elif livef1_success:
    print("\n❌ fastf1 數據不可用")
    print("✅ LiveF1 數據可用")
    
else:
    print("\n❌ 兩者數據均不可用")
    print("💡 請檢查網路連線和 API 狀態")

print("\n" + "="*70)
print("測試完成")
print("="*70)
