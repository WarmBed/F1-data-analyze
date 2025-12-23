"""
驗證 FastF1 的 DRS 值範圍
檢查是否包含 Ready 狀態
"""

import sys
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import fastf1


def analyze_fastf1_drs_values():
    """分析 FastF1 的 DRS 原始值"""
    
    year = 2025
    race = "Abu Dhabi"
    session = "R"
    
    print("="*80)
    print(f"FastF1 DRS 值範圍分析: {year} {race} {session}")
    print("="*80)
    
    # 啟用緩存
    cache_dir = project_root / "f1_analysis_cache"
    fastf1.Cache.enable_cache(str(cache_dir))
    
    # 載入賽事
    print("正在載入 FastF1 數據...")
    session_obj = fastf1.get_session(year, race, session)
    session_obj.load()
    
    print(f"✅ 載入完成")
    
    # 統計所有 DRS 值
    drs_counter = Counter()
    lap_count = 0
    
    laps = session_obj.laps
    
    for idx, lap in laps.iterrows():
        try:
            telemetry = lap.get_telemetry()
            
            if telemetry is not None and 'DRS' in telemetry.columns:
                drs_values = telemetry['DRS'].dropna()
                
                for drs_val in drs_values:
                    if drs_val is not None and str(drs_val) != 'nan':
                        drs_counter[int(drs_val)] += 1
                
                lap_count += 1
        except Exception:
            pass
    
    print(f"\n處理了 {lap_count} 圈的遙測數據")
    
    # 輸出所有 DRS 值
    print("\n" + "="*80)
    print("FastF1 DRS 值分佈")
    print("="*80)
    
    total = sum(drs_counter.values())
    print(f"總樣本數: {total:,}")
    print()
    
    for drs_val in sorted(drs_counter.keys()):
        count = drs_counter[drs_val]
        pct = (count / total * 100) if total > 0 else 0
        
        # 判斷狀態
        if drs_val == 0:
            status = "Disabled (OFF)"
        elif drs_val == 1:
            status = "Disabled"
        elif drs_val >= 10 and drs_val % 2 == 0:
            status = "Active (ON)"
        elif drs_val >= 2 and drs_val % 2 == 0:
            status = "Ready/Available?"
        else:
            status = "Unknown"
        
        print(f"  {drs_val:>3d}: {count:>8,} ({pct:>6.2f}%) - {status}")
    
    # 分析
    print("\n" + "="*80)
    print("分析結論")
    print("="*80)
    
    has_ready = any(val >= 2 and val <= 8 and val % 2 == 0 for val in drs_counter.keys())
    has_on = any(val >= 10 and val % 2 == 0 for val in drs_counter.keys())
    has_zero = 0 in drs_counter
    has_one = 1 in drs_counter
    
    print(f"✅ DRS = 0 (Disabled/OFF): {'存在' if has_zero else '不存在'}")
    print(f"✅ DRS = 1 (Disabled): {'存在' if has_one else '不存在'}")
    print(f"{'✅' if has_ready else '❌'} DRS = 2,4,6,8 (Ready): {'存在' if has_ready else '不存在'}")
    print(f"✅ DRS = 10,12,14,... (Active/ON): {'存在' if has_on else '不存在'}")
    
    print("\n結論:")
    if not has_ready:
        print("  ⚠️  FastF1 **沒有** Ready 狀態 (2,4,6,8)")
        print("  ✅ FastF1 只有：0/1 (Disabled) 和 10+ (Active)")
        print("  💡 這與 Live Timing API 不同！")
    else:
        print("  ✅ FastF1 包含 Ready 狀態")
    
    # 比較 Live Timing API
    print("\n" + "="*80)
    print("與 Live Timing API 對比")
    print("="*80)
    
    print("\nLive Timing API 的 DRS 值:")
    print("  0 = Disabled (79.47%)")
    print("  1 = Disabled (15.50%)")
    print("  2,8 = Ready/Available (2.14%)")
    print("  10,12,14 = Active/ON (2.86%)")
    
    print("\nFastF1 的 DRS 值:")
    disabled_pct = sum(drs_counter[v] for v in [0, 1] if v in drs_counter) / total * 100
    ready_pct = sum(drs_counter[v] for v in [2, 4, 6, 8] if v in drs_counter) / total * 100
    on_pct = sum(drs_counter[v] for v in drs_counter if v >= 10 and v % 2 == 0) / total * 100
    
    print(f"  0,1 = Disabled ({disabled_pct:.2f}%)")
    print(f"  2,4,6,8 = Ready ({ready_pct:.2f}%)")
    print(f"  10,12,14,... = Active/ON ({on_pct:.2f}%)")
    
    print("\n" + "="*80)
    print("💡 結論")
    print("="*80)
    
    if not has_ready or ready_pct < 1:
        print("FastF1 的 DRS 數據**簡化**了：")
        print("  • 0 = DRS Disabled/OFF")
        print("  • 1 = DRS Disabled (另一種狀態)")
        print("  • 10+ = DRS Active/ON")
        print()
        print("Live Timing API 更詳細：")
        print("  • 0 = Disabled/OFF (賽道上沒有 DRS 區)")
        print("  • 1 = Disabled")
        print("  • 2,8 = Ready/Available (在 DRS 區內，可使用)")
        print("  • 10,12,14 = Active/ON (實際開啟)")
        print()
        print("✅ 所以你的假設**正確**！")
        print("   Live Timing API: 0 = Disabled, 其他值(>0) = Enabled/Ready/ON")
    else:
        print("FastF1 和 Live Timing API 的 DRS 數據結構相似")


if __name__ == "__main__":
    analyze_fastf1_drs_values()
