"""
比較 FastF1 和我們 PKL 的 DRS 數據
檢查每個車手每圈的 DRS 狀況是否一致
"""

import sys
import pickle
from pathlib import Path
from collections import defaultdict, Counter

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import fastf1


def analyze_fastf1_drs(year: int, race: str, session: str):
    """從 FastF1 獲取 DRS 數據"""
    print(f"正在從 FastF1 載入 {year} {race} {session}...")
    
    try:
        # 啟用緩存
        cache_dir = project_root / "f1_analysis_cache"
        fastf1.Cache.enable_cache(str(cache_dir))
        
        # 載入賽事
        session_obj = fastf1.get_session(year, race, session)
        session_obj.load()
        
        print(f"✅ FastF1 載入成功")
        print(f"   總圈數: {session_obj.total_laps}")
        
        # 建立車手代碼到車號的映射
        driver_code_to_number = {}
        for driver_num in session_obj.drivers:
            driver_info = session_obj.get_driver(driver_num)
            driver_code = driver_info['Abbreviation']  # 使用車手代碼 (VER, LEC, etc.)
            driver_number = str(driver_info['DriverNumber'])
            driver_code_to_number[driver_code] = driver_number
        
        print(f"   車手映射: {driver_code_to_number}")
        
        # 統計每個車手每圈的 DRS 數據（使用車號）
        driver_lap_drs = defaultdict(lambda: defaultdict(Counter))
        
        laps = session_obj.laps
        
        processed_laps = 0
        for idx, lap in laps.iterrows():
            driver_code = lap['Driver']
            driver_number = driver_code_to_number.get(driver_code, driver_code)
            lap_num = lap['LapNumber']
            
            # 調試第一圈
            if processed_laps == 0:
                print(f"   調試第一筆: driver_code={driver_code}, driver_number={driver_number}, lap={lap_num}")
            
            # 獲取該圈的遙測數據
            try:
                telemetry = lap.get_telemetry()
                
                if telemetry is not None and 'DRS' in telemetry.columns:
                    drs_values = telemetry['DRS'].dropna()
                    
                    for drs_val in drs_values:
                        if drs_val is not None and str(drs_val) != 'nan':
                            driver_lap_drs[driver_number][lap_num][str(int(drs_val))] += 1
            except Exception as e:
                # 某些圈可能沒有遙測數據
                pass
            
            processed_laps += 1
        
        print(f"   處理完成，實際車手數: {len(driver_lap_drs)}")
        print(f"   車手列表（前5）: {sorted(list(driver_lap_drs.keys()))[:5]}")
        
        return driver_lap_drs, len(laps)
    
    except Exception as e:
        print(f"❌ FastF1 載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None, 0


def analyze_pkl_drs(pkl_path: Path):
    """從我們的 PKL 獲取 DRS 數據"""
    print(f"\n正在從 PKL 載入: {pkl_path}")
    
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        
        snapshots = data.get('snapshots', [])
        print(f"✅ PKL 載入成功")
        print(f"   快照數量: {len(snapshots)}")
        
        # 統計每個車手每圈的 DRS 數據
        driver_lap_drs = defaultdict(lambda: defaultdict(Counter))
        
        for snapshot in snapshots:
            drivers = snapshot.get('drivers', {})
            
            for driver_num, driver_data in drivers.items():
                lap_num = driver_data.get('lap')
                drs_val = driver_data.get('drs')
                
                if lap_num and drs_val is not None and drs_val != '':
                    driver_lap_drs[driver_num][lap_num][str(drs_val)] += 1
        
        return driver_lap_drs
    
    except Exception as e:
        print(f"❌ PKL 載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_drs_data(fastf1_data, pkl_data, total_laps):
    """比較 FastF1 和 PKL 的 DRS 數據"""
    print("\n" + "="*80)
    print("DRS 數據比較分析")
    print("="*80)
    
    if not fastf1_data or not pkl_data:
        print("❌ 數據不完整，無法比較")
        return
    
    # 找出共同的車手
    fastf1_drivers = set(fastf1_data.keys())
    pkl_drivers = set(pkl_data.keys())
    
    common_drivers = fastf1_drivers & pkl_drivers
    
    print(f"\nFastF1 車手數: {len(fastf1_drivers)}")
    print(f"PKL 車手數: {len(pkl_drivers)}")
    print(f"共同車手數: {len(common_drivers)}")
    
    print(f"\n調試 - FastF1 車手列表（前10）: {sorted(list(fastf1_drivers))[:10]}")
    print(f"調試 - PKL 車手列表（前10）: {sorted(list(pkl_drivers))[:10]}")
    
    if not common_drivers:
        print("\n⚠️  沒有共同的車手，可能是車手編號格式不同")
        print(f"FastF1 車手: {sorted(list(fastf1_drivers))[:5]}")
        print(f"PKL 車手: {sorted(list(pkl_drivers))[:5]}")
        return
    
    # 選擇前 3 位車手進行詳細比較
    sample_drivers = sorted(list(common_drivers))[:3]
    
    for driver in sample_drivers:
        print(f"\n{'─'*80}")
        print(f"車手: {driver}")
        print(f"{'─'*80}")
        
        fastf1_laps = fastf1_data[driver]
        pkl_laps = pkl_data[driver]
        
        # 找出共同的圈數
        common_laps = set(fastf1_laps.keys()) & set(pkl_laps.keys())
        
        if not common_laps:
            print("  ⚠️  沒有共同的圈數數據")
            continue
        
        print(f"  共同圈數: {len(common_laps)}")
        
        # 比較前 5 圈
        sample_laps = sorted(list(common_laps))[:5]
        
        for lap_num in sample_laps:
            fastf1_drs = fastf1_laps[lap_num]
            pkl_drs = pkl_laps[lap_num]
            
            print(f"\n  圈數 {lap_num}:")
            print(f"    FastF1 DRS 分佈:")
            total_f1 = sum(fastf1_drs.values())
            for drs_val, count in sorted(fastf1_drs.items()):
                pct = (count / total_f1 * 100) if total_f1 > 0 else 0
                status = get_drs_status(drs_val)
                print(f"      {drs_val:>3s}: {count:>4d} ({pct:>5.1f}%) - {status}")
            
            print(f"    PKL DRS 分佈:")
            total_pkl = sum(pkl_drs.values())
            for drs_val, count in sorted(pkl_drs.items()):
                pct = (count / total_pkl * 100) if total_pkl > 0 else 0
                status = get_drs_status(drs_val)
                print(f"      {drs_val:>3s}: {count:>4d} ({pct:>5.1f}%) - {status}")
            
            # 比較差異
            all_drs_vals = set(fastf1_drs.keys()) | set(pkl_drs.keys())
            differences = []
            
            for drs_val in all_drs_vals:
                f1_count = fastf1_drs.get(drs_val, 0)
                pkl_count = pkl_drs.get(drs_val, 0)
                
                f1_pct = (f1_count / total_f1 * 100) if total_f1 > 0 else 0
                pkl_pct = (pkl_count / total_pkl * 100) if total_pkl > 0 else 0
                
                diff = abs(f1_pct - pkl_pct)
                if diff > 10:  # 差異超過 10%
                    differences.append((drs_val, f1_pct, pkl_pct, diff))
            
            if differences:
                print(f"    ⚠️  顯著差異 (>10%):")
                for drs_val, f1_pct, pkl_pct, diff in differences:
                    status = get_drs_status(drs_val)
                    print(f"      {drs_val} ({status}): FastF1={f1_pct:.1f}% vs PKL={pkl_pct:.1f}% (差異 {diff:.1f}%)")
    
    # 全局統計
    print(f"\n{'═'*80}")
    print("全局 DRS 分佈統計")
    print(f"{'═'*80}")
    
    # FastF1 全局統計
    fastf1_global = Counter()
    for driver_laps in fastf1_data.values():
        for lap_drs in driver_laps.values():
            fastf1_global.update(lap_drs)
    
    # PKL 全局統計
    pkl_global = Counter()
    for driver_laps in pkl_data.values():
        for lap_drs in driver_laps.values():
            pkl_global.update(lap_drs)
    
    print("\nFastF1 全局 DRS 分佈:")
    total_f1_global = sum(fastf1_global.values())
    for drs_val, count in sorted(fastf1_global.items()):
        pct = (count / total_f1_global * 100) if total_f1_global > 0 else 0
        status = get_drs_status(drs_val)
        print(f"  {drs_val:>3s}: {count:>7d} ({pct:>5.2f}%) - {status}")
    
    print("\nPKL 全局 DRS 分佈:")
    total_pkl_global = sum(pkl_global.values())
    for drs_val, count in sorted(pkl_global.items()):
        pct = (count / total_pkl_global * 100) if total_pkl_global > 0 else 0
        status = get_drs_status(drs_val)
        print(f"  {drs_val:>3s}: {count:>7d} ({pct:>5.2f}%) - {status}")


def get_drs_status(drs_val_str: str) -> str:
    """獲取 DRS 狀態描述"""
    try:
        val = int(drs_val_str)
        if val >= 10 and val % 2 == 0:
            return "ON"
        elif val >= 2 and val % 2 == 0:
            return "RDY"
        else:
            return "Disabled"
    except:
        return "?"


def main():
    year = 2025
    race = "Abu Dhabi"
    session = "R"
    
    print("="*80)
    print(f"FastF1 vs PKL DRS 數據比較")
    print(f"賽季: {year} | 賽事: {race} | 賽段: {session}")
    print("="*80)
    
    # 分析 FastF1
    fastf1_data, total_laps = analyze_fastf1_drs(year, race, session)
    
    # 分析 PKL - 使用 data/live_timing_cache 路徑
    pkl_path = project_root / "data" / "live_timing_cache" / "2025" / "2025_Abu_Dhabi_Race.pkl"
    
    if not pkl_path.exists():
        # 嘗試舊格式
        pkl_path = project_root / "data" / "live_timing_cache" / "2025" / "Abu_Dhabi_Race.pkl"
    
    if not pkl_path.exists():
        # 嘗試 dist 路徑
        pkl_path = project_root / "dist" / "live_timing_cache" / "2025" / "2025_Abu_Dhabi_Race.pkl"
    
    if not pkl_path.exists():
        pkl_path = project_root / "dist" / "live_timing_cache" / "2025" / "Abu_Dhabi_Race.pkl"
    
    if not pkl_path.exists():
        print(f"\n❌ 找不到 PKL 檔案")
        print("已嘗試路徑:")
        print("  - data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl")
        print("  - data/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
        print("  - dist/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl")
        print("  - dist/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
        return
    
    pkl_data = analyze_pkl_drs(pkl_path)
    
    # 比較數據
    compare_drs_data(fastf1_data, pkl_data, total_laps)
    
    print("\n" + "="*80)
    print("💡 分析完成")
    print("="*80)


if __name__ == "__main__":
    main()
