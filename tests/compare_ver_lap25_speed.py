"""
比較 VER 第 25 圈速度資料：Live Timing API vs FastF1
========================================================

目標：
1. 從 Live Timing PKL 中提取 VER 第 25 圈的速度資料點
2. 從 FastF1 中提取相同圈數的速度資料點
3. 比較兩者的資料點數量、時間戳記、速度值
"""

import pickle
import fastf1
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 啟用 FastF1 緩存
fastf1.Cache.enable_cache('f1_analysis_cache')


def load_live_timing_data(pkl_path: str) -> Dict:
    """載入 Live Timing PKL 資料"""
    print(f"📂 載入 Live Timing 資料: {pkl_path}")
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    
    print(f"✅ 載入完成")
    print(f"   - 快照數量: {len(data.get('snapshots', []))}")
    print(f"   - 賽事資訊: {data.get('race_info', {})}")
    return data


def extract_ver_lap25_from_livetiming(data: Dict) -> List[Dict]:
    """
    從 Live Timing 資料中提取 VER 第 25 圈的速度資料
    
    Returns:
        List[Dict]: 每個字典包含 {'timestamp', 'speed', 'distance', ...}
    """
    print("\n🔍 搜尋 VER 第 25 圈的資料...")
    
    snapshots = data.get('snapshots', [])
    ver_lap25_data = []
    
    # 尋找 VER 的車號
    ver_number = None
    for snapshot in snapshots:
        drivers = snapshot.get('drivers', {})
        for num, driver_data in drivers.items():
            # 正確的欄位名稱是 driver_tla
            if driver_data.get('driver_tla') == 'VER':
                ver_number = num
                break
        if ver_number:
            break
    
    if not ver_number:
        print("❌ 找不到 VER 的車號")
        return []
    
    print(f"✅ VER 車號: {ver_number}")
    
    # 收集第 25 圈的所有資料點
    lap25_count = 0
    for snapshot in snapshots:
        drivers = snapshot.get('drivers', {})
        if ver_number not in drivers:
            continue
        
        ver_data = drivers[ver_number]
        current_lap = ver_data.get('lap', 0)  # 正確的欄位名稱是 'lap'
        
        # 檢查是否為第 25 圈
        if current_lap == 25:
            lap25_count += 1
            speed = ver_data.get('speed')
            
            # 建立資料點
            data_point = {
                'timestamp': snapshot.get('race_time_seconds'),  # 使用秒數版本
                'race_time_display': snapshot.get('race_time'),
                'snapshot_time': snapshot.get('timestamp'),
                'current_lap': current_lap,
                'speed': speed,
                'position': ver_data.get('position'),
                'gap_to_leader': ver_data.get('gap_to_leader'),
                'last_lap_time': ver_data.get('last_lap_time'),
                'tyre_compound': ver_data.get('tyre_compound'),
                'tyre_age': ver_data.get('tyre_age'),
            }
            
            ver_lap25_data.append(data_point)
    
    print(f"✅ 找到 {len(ver_lap25_data)} 個第 25 圈的資料點")
    
    if ver_lap25_data:
        print(f"   - 第一個資料點時間: {ver_lap25_data[0].get('race_time_display')}")
        print(f"   - 最後資料點時間: {ver_lap25_data[-1].get('race_time_display')}")
        speeds_with_value = [d['speed'] for d in ver_lap25_data if d['speed'] is not None]
        if speeds_with_value:
            print(f"   - 速度範圍: {min(speeds_with_value)} - {max(speeds_with_value)} km/h")
    
    return ver_lap25_data


def load_fastf1_data(year: int, race: str, session: str) -> Optional[fastf1.core.Session]:
    """載入 FastF1 資料"""
    print(f"\n📂 載入 FastF1 資料: {year} {race} {session}")
    
    try:
        session_obj = fastf1.get_session(year, race, session)
        session_obj.load()
        print(f"✅ FastF1 資料載入完成")
        return session_obj
    except Exception as e:
        print(f"❌ FastF1 載入失敗: {e}")
        return None


def extract_ver_lap25_from_fastf1(session: fastf1.core.Session) -> Optional[pd.DataFrame]:
    """
    從 FastF1 中提取 VER 第 25 圈的遙測資料
    
    Returns:
        pd.DataFrame: 包含 Time, Speed, Distance 等欄位
    """
    print("\n🔍 從 FastF1 提取 VER 第 25 圈資料...")
    
    try:
        # 取得 VER 的圈速資料
        ver_laps = session.laps.pick_driver('VER')
        
        if len(ver_laps) < 25:
            print(f"❌ VER 只有 {len(ver_laps)} 圈資料，無法取得第 25 圈")
            return None
        
        # 取得第 25 圈（索引從 0 開始，所以是 24）
        lap25 = ver_laps.iloc[24]
        
        print(f"✅ VER 第 25 圈資訊:")
        print(f"   - 圈速: {lap25['LapTime']}")
        print(f"   - 輪胎: {lap25.get('Compound', 'N/A')}")
        print(f"   - 胎齡: {lap25.get('TyreLife', 'N/A')}")
        
        # 取得遙測資料
        telemetry = lap25.get_telemetry()
        
        print(f"✅ 遙測資料點數量: {len(telemetry)}")
        print(f"   - 可用欄位: {telemetry.columns.tolist()}")
        
        if 'Speed' in telemetry.columns:
            print(f"   - 速度範圍: {telemetry['Speed'].min():.1f} - {telemetry['Speed'].max():.1f} km/h")
        
        return telemetry
        
    except Exception as e:
        print(f"❌ 提取 FastF1 資料失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_speed_data(livetiming_data: List[Dict], fastf1_data: pd.DataFrame):
    """比較兩個資料源的速度資料"""
    print("\n" + "=" * 80)
    print("📊 資料比較分析")
    print("=" * 80)
    
    # 基本統計
    print(f"\n1️⃣ 資料點數量比較:")
    print(f"   - Live Timing: {len(livetiming_data)} 個資料點")
    print(f"   - FastF1:      {len(fastf1_data)} 個資料點")
    print(f"   - 比例:        1 : {len(fastf1_data) / len(livetiming_data):.2f}")
    
    # 速度統計
    lt_speeds = [d['speed'] for d in livetiming_data if d['speed'] is not None]
    ff_speeds = fastf1_data['Speed'].dropna().values
    
    print(f"\n2️⃣ 速度統計 (km/h):")
    print(f"   {'':20s} {'Live Timing':>15s} {'FastF1':>15s} {'差異':>15s}")
    print(f"   {'-'*65}")
    print(f"   {'最小值':20s} {np.min(lt_speeds):>15.2f} {np.min(ff_speeds):>15.2f} {np.min(lt_speeds) - np.min(ff_speeds):>15.2f}")
    print(f"   {'最大值':20s} {np.max(lt_speeds):>15.2f} {np.max(ff_speeds):>15.2f} {np.max(lt_speeds) - np.max(ff_speeds):>15.2f}")
    print(f"   {'平均值':20s} {np.mean(lt_speeds):>15.2f} {np.mean(ff_speeds):>15.2f} {np.mean(lt_speeds) - np.mean(ff_speeds):>15.2f}")
    print(f"   {'中位數':20s} {np.median(lt_speeds):>15.2f} {np.median(ff_speeds):>15.2f} {np.median(lt_speeds) - np.median(ff_speeds):>15.2f}")
    print(f"   {'標準差':20s} {np.std(lt_speeds):>15.2f} {np.std(ff_speeds):>15.2f} {np.std(lt_speeds) - np.std(ff_speeds):>15.2f}")
    
    # 採樣率分析
    print(f"\n3️⃣ 採樣率分析:")
    if len(livetiming_data) > 1:
        # Live Timing 的時間間隔（假設 race_time 是秒數）
        lt_times = [d['timestamp'] for d in livetiming_data if d['timestamp'] is not None]
        if len(lt_times) > 1:
            lt_intervals = np.diff(lt_times)
            print(f"   Live Timing 平均間隔: {np.mean(lt_intervals):.3f} 秒")
            print(f"   Live Timing 採樣率: {1/np.mean(lt_intervals):.2f} Hz")
    
    if 'Time' in fastf1_data.columns and len(fastf1_data) > 1:
        # FastF1 的時間間隔
        ff_times = fastf1_data['Time'].dt.total_seconds().values
        ff_intervals = np.diff(ff_times)
        ff_intervals = ff_intervals[ff_intervals > 0]  # 過濾掉 0 或負值
        if len(ff_intervals) > 0:
            print(f"   FastF1 平均間隔: {np.mean(ff_intervals):.3f} 秒")
            print(f"   FastF1 採樣率: {1/np.mean(ff_intervals):.2f} Hz")
    
    # 顯示前 10 個資料點對比
    print(f"\n4️⃣ 前 10 個資料點對比:")
    print(f"   {'序號':>5s} {'LT Speed':>12s} {'FF Speed':>12s} {'差異':>10s}")
    print(f"   {'-'*45}")
    
    for i in range(min(10, len(livetiming_data), len(fastf1_data))):
        lt_speed = livetiming_data[i]['speed'] if livetiming_data[i]['speed'] is not None else 0
        ff_speed = fastf1_data.iloc[i]['Speed']
        diff = lt_speed - ff_speed
        print(f"   {i+1:>5d} {lt_speed:>12.2f} {ff_speed:>12.2f} {diff:>10.2f}")
    
    # 顯示後 10 個資料點對比
    print(f"\n5️⃣ 後 10 個資料點對比:")
    print(f"   {'序號':>5s} {'LT Speed':>12s} {'FF Speed':>12s} {'差異':>10s}")
    print(f"   {'-'*45}")
    
    start_idx = max(len(livetiming_data) - 10, 0)
    for i in range(start_idx, len(livetiming_data)):
        lt_speed = livetiming_data[i]['speed'] if livetiming_data[i]['speed'] is not None else 0
        
        # 找到對應的 FastF1 資料點（按比例映射）
        ff_idx = int(i * len(fastf1_data) / len(livetiming_data))
        if ff_idx < len(fastf1_data):
            ff_speed = fastf1_data.iloc[ff_idx]['Speed']
            diff = lt_speed - ff_speed
            print(f"   {i+1:>5d} {lt_speed:>12.2f} {ff_speed:>12.2f} {diff:>10.2f}")


def main():
    """主程式"""
    print("=" * 80)
    print("VER 第 25 圈速度資料比較：Live Timing vs FastF1")
    print("=" * 80)
    
    # 1. 載入 Live Timing 資料
    pkl_path = "data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl"
    if not Path(pkl_path).exists():
        print(f"❌ 找不到檔案: {pkl_path}")
        return
    
    lt_data = load_live_timing_data(pkl_path)
    
    # 2. 提取 VER 第 25 圈的 Live Timing 資料
    ver_lap25_lt = extract_ver_lap25_from_livetiming(lt_data)
    
    if not ver_lap25_lt:
        print("❌ 無法提取 Live Timing 資料")
        return
    
    # 3. 載入 FastF1 資料
    ff_session = load_fastf1_data(2025, 'Abu Dhabi', 'R')
    
    if ff_session is None:
        print("❌ 無法載入 FastF1 資料")
        return
    
    # 4. 提取 VER 第 25 圈的 FastF1 資料
    ver_lap25_ff = extract_ver_lap25_from_fastf1(ff_session)
    
    if ver_lap25_ff is None:
        print("❌ 無法提取 FastF1 資料")
        return
    
    # 5. 比較兩個資料源
    compare_speed_data(ver_lap25_lt, ver_lap25_ff)
    
    print("\n" + "=" * 80)
    print("✅ 分析完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
