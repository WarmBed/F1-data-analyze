"""
使用 fastf1 提取 HAM Lap 10 詳細資料
"""
import fastf1
import pandas as pd

print("="*70)
print("HAM Lap 10 詳細資料分析 (使用 fastf1)")
print("="*70)

# 啟用快取
fastf1.Cache.enable_cache('f1_analysis_cache')

print("\n[1] 載入 2025 日本站正賽...")
session = fastf1.get_session(2025, 'Japan', 'R')
session.load()

print("\n[2] 尋找 Hamilton...")
# 列出所有車手
print(f"  比賽車手: {session.drivers}")

# 找 Hamilton
ham_laps = session.laps.pick_driver('HAM')
print(f"\n[3] HAM 總圈數: {len(ham_laps)}")

if len(ham_laps) >= 10:
    # 取得 Lap 10
    lap10 = ham_laps.iloc[9]  # Index 9 = Lap 10
    
    print(f"\n{'='*70}")
    print("Lap 10基本資訊")
    print("="*70)
    print(f"車手: Lewis Hamilton (HAM)")
    print(f"車號: {lap10['DriverNumber']}")
    print(f"圈數: {lap10['LapNumber']}")
    print(f"圈速: {lap10['LapTime']}")
    print(f"圈開始時間: {lap10['LapStartTime']}")
    
    # 取得遙測
    print(f"\n{'='*70}")
    print("Lap 10 遙測資料")
    print("="*70)
    
    telemetry = lap10.get_telemetry()
    
    print(f"\n總資料點: {len(telemetry)}")
    print(f"\n可用欄位: {list(telemetry.columns)}")
    
    # 速度分析
    speed = telemetry['Speed']
    print(f"\n【速度統計】")
    print(f"  資料點數: {len(speed)}")
    print(f"  最小速度: {speed.min():.1f} km/h")
    print(f"  最大速度: {speed.max():.1f} km/h")
    print(f"  平均速度: {speed.mean():.1f} km/h")
    print(f"  中位數速度: {speed.median():.1f} km/h")
    
    # RPM分析
    rpm = telemetry['RPM']
    print(f"\n【RPM 統計】")
    print(f"  最小 RPM: {rpm.min():.0f}")
    print(f"  最大 RPM: {rpm.max():.0f}")
    print(f"  平均 RPM: {rpm.mean():.0f}")
    
    # Throttle 分析
    throttle = telemetry['Throttle']
    print(f"\n【油門統計】")
    print(f"  平均油門開度: {throttle.mean():.1f}%")
    print(f"  全油門時間: {(throttle == 100).sum()} 個資料點 ({(throttle == 100).sum() / len(throttle) * 100:.1f}%)")
    
    # 煞車分析
    brake = telemetry['Brake']
    print(f"\n【煞車統計】")
    print(f"  煞車次數: {(brake > 0).sum()} 個資料點")
    print(f"  煞車比例: {(brake > 0).sum() / len(brake) * 100:.1f}%")
    
    # 檔位分析
    gear = telemetry['nGear']
    print(f"\n【檔位統計】")
    print(f"  最高檔位: {gear.max():.0f}")
    print(f"  最低檔位: {gear.min():.0f}")
    print(f"  檔位分佈:")
    for g in sorted(gear.unique()):
        count = (gear == g).sum()
        pct = count / len(gear) * 100
        print(f"    檔位 {int(g)}: {count:4d} 點 ({pct:5.1f}%)")
    
    # 顯示前10筆資料
    print(f"\n{'='*70}")
    print("前 10 筆遙測資料樣本")
    print("="*70)
    print(f"\n{'Idx':<4} {'Time':>10} {'Speed':>6} {'RPM':>6} {'Gear':>4} {'Throttle':>8} {'Brake':>5}")
    print("-"*70)
    for i in range(min(10, len(telemetry))):
        row = telemetry.iloc[i]
        time_str = f"{row['Time'].total_seconds():.2f}s"
        print(f"{i+1:<4} {time_str:>10} {row['Speed']:>6.0f} {row['RPM']:>6.0f} {row['nGear']:>4.0f} {row['Throttle']:>8.1f} {row['Brake']:>5.0f}")
    
    print(f"\n... ({len(telemetry) - 20} 筆資料) ...")
    
    # 顯示後10筆資料
    print(f"\n後 10 筆遙測資料樣本")
    print("-"*70)
    for i in range(max(0, len(telemetry)-10), len(telemetry)):
        row = telemetry.iloc[i]
        time_str = f"{row['Time'].total_seconds():.2f}s"
        print(f"{i+1:<4} {time_str:>10} {row['Speed']:>6.0f} {row['RPM']:>6.0f} {row['nGear']:>4.0f} {row['Throttle']:>8.1f} {row['Brake']:>5.0f}")
    
    # 輸出成 CSV
    output_file = "Live_timing_test/HAM_Lap10_telemetry.csv"
    telemetry.to_csv(output_file, index=False)
    print(f"\n[4] 完整資料已儲存至: {output_file}")
    
    print(f"\n{'='*70}")
    print("分析完成!")
    print("="*70)
    
else:
    print(f"[ERROR] HAM 只有 {len(ham_laps)} 圈")
