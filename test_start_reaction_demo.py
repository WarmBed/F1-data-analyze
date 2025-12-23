"""
F101 起跑反應分析 DEMO
分析單一車手在每年每場賽道的起跑反應

數據來源: Live Timing TimingData.json + CarData.json

指標:
1. 起跑反應時間 (0-100 km/h 加速時間)
2. 首圈位置變化 (Grid Position vs Lap 1 End Position)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StartReactionResult:
    """起跑反應分析結果"""
    race_name: str
    year: int
    grid_position: Optional[int] = None
    lap1_end_position: Optional[int] = None
    position_delta: Optional[int] = None  # 正數=進步
    time_to_100: Optional[float] = None  # 0-100 km/h 時間 (秒)
    first_corner_delta: Optional[int] = None  # 第一彎後位置變化


def parse_timestamp(ts_str: str) -> float:
    """解析 timestamp 字串為秒數"""
    if not ts_str:
        return 0.0
    parts = ts_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return float(m) * 60 + float(s)
    return float(ts_str)


def get_driver_number_mapping(driverlist_path: str) -> Dict[str, int]:
    """獲取車手代號到車號的映射"""
    mapping = {}
    try:
        with open(driverlist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 格式可能是 records 或直接是 dict
        if 'records' in data:
            for rec in data['records']:
                drivers = rec.get('data', {})
                for num, info in drivers.items():
                    if isinstance(info, dict):
                        abbr = info.get('Tla', info.get('RacingNumber', num))
                        mapping[abbr] = int(num)
        else:
            for num, info in data.items():
                if isinstance(info, dict):
                    abbr = info.get('Tla', info.get('RacingNumber', num))
                    mapping[abbr] = int(num)
    except Exception as e:
        print(f"  [警告] 無法載入 DriverList: {e}")
    
    return mapping


def analyze_position_changes(timingdata_path: str, driver_number: int) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    分析位置變化
    
    Returns:
        (grid_position, lap1_end_position, first_corner_delta)
    """
    try:
        with open(timingdata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [錯誤] 無法載入 TimingData: {e}")
        return None, None, None
    
    records = data.get('records', [])
    
    grid_position = None
    lap1_end_position = None
    first_corner_position = None
    lap1_found = False
    
    driver_key = str(driver_number)
    
    for rec in records:
        lines = rec.get('data', {}).get('Lines', {})
        
        if driver_key in lines:
            driver_data = lines[driver_key]
            if isinstance(driver_data, dict):
                # 獲取位置
                pos = driver_data.get('Position')
                if pos is not None:
                    pos = int(pos) if isinstance(pos, str) else pos
                    
                    if grid_position is None:
                        grid_position = pos
                    
                    # 檢查是否進入第一圈
                    num_laps = driver_data.get('NumberOfLaps', 0)
                    if isinstance(num_laps, str):
                        num_laps = int(num_laps) if num_laps.isdigit() else 0
                    
                    if num_laps == 0 and first_corner_position is None:
                        # 還在第一圈，持續更新
                        first_corner_position = pos
                    
                    if num_laps >= 1 and not lap1_found:
                        lap1_end_position = pos
                        lap1_found = True
                        break
    
    # 計算第一彎後的位置變化
    first_corner_delta = None
    if grid_position is not None and first_corner_position is not None:
        first_corner_delta = grid_position - first_corner_position  # 正數=進步
    
    return grid_position, lap1_end_position, first_corner_delta


def analyze_acceleration(cardata_path: str, driver_number: int) -> Optional[float]:
    """
    分析 0-100 km/h 加速時間
    
    Returns:
        加速時間 (秒) 或 None
    """
    try:
        with open(cardata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [錯誤] 無法載入 CarData: {e}")
        return None
    
    records = data.get('records', [])
    driver_key = str(driver_number)
    
    # 找到真正的起跑時刻 (所有車手速度都接近0，然後開始加速)
    start_time = None
    time_to_100 = None
    found_zero = False
    
    for rec in records:
        ts = rec.get('timestamp', '')
        entries = rec.get('data', {}).get('Entries', [])
        
        if not entries:
            continue
        
        cars = entries[0].get('Cars', {})
        driver_data = cars.get(driver_key, {})
        channels = driver_data.get('Channels', {})
        
        # Channel 2 = Speed (km/h), Channel 0 = RPM
        speed = channels.get('2', 0)
        rpm = channels.get('0', 0)
        
        # 偵測起跑前的靜止狀態 (速度<5 且 RPM 高)
        if speed <= 5 and rpm > 5000:
            found_zero = True
            start_time = parse_timestamp(ts)
        
        # 偵測達到 100 km/h
        if found_zero and speed >= 100 and time_to_100 is None:
            current_time = parse_timestamp(ts)
            time_to_100 = current_time - start_time
            
            # 合理性檢查：起跑加速通常在 3-6 秒之間
            if 2.0 <= time_to_100 <= 10.0:
                return time_to_100
            else:
                # 數據可能不正確，繼續尋找
                time_to_100 = None
                found_zero = False
    
    return time_to_100


def analyze_race_start(race_dir: Path, driver_number: int, year: int) -> StartReactionResult:
    """分析單場比賽的起跑反應"""
    
    race_name = race_dir.name.replace('_Race', '').replace('_', ' ')
    result = StartReactionResult(race_name=race_name, year=year)
    
    # 分析位置變化
    timingdata_path = race_dir / 'TimingData.json'
    if timingdata_path.exists():
        grid_pos, lap1_pos, corner_delta = analyze_position_changes(str(timingdata_path), driver_number)
        result.grid_position = grid_pos
        result.lap1_end_position = lap1_pos
        result.first_corner_delta = corner_delta
        
        if grid_pos is not None and lap1_pos is not None:
            result.position_delta = grid_pos - lap1_pos  # 正數=進步
    
    # 分析加速時間
    cardata_path = race_dir / 'CarData.json'
    if cardata_path.exists():
        result.time_to_100 = analyze_acceleration(str(cardata_path), driver_number)
    
    return result


def scan_available_races() -> Dict[int, List[Path]]:
    """掃描可用的比賽數據"""
    base_path = Path('json/LiveF1')
    races = {}
    
    if not base_path.exists():
        print(f"[錯誤] 找不到 Live Timing 數據目錄: {base_path}")
        return races
    
    for year_dir in sorted(base_path.iterdir()):
        if year_dir.is_dir() and year_dir.name.isdigit():
            year = int(year_dir.name)
            races[year] = []
            
            for race_dir in sorted(year_dir.iterdir()):
                if race_dir.is_dir() and '_Race' in race_dir.name:
                    # 檢查必要文件
                    if (race_dir / 'TimingData.json').exists():
                        races[year].append(race_dir)
    
    return races


def format_position_delta(delta: Optional[int]) -> str:
    """格式化位置變化"""
    if delta is None:
        return "-"
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def format_time(time: Optional[float]) -> str:
    """格式化時間"""
    if time is None:
        return "-"
    return f"{time:.2f}s"


def main():
    print("=" * 70)
    print("F101 起跑反應分析 DEMO")
    print("分析車手在每年每場比賽的起跑表現")
    print("=" * 70)
    
    # 掃描可用數據
    races = scan_available_races()
    
    print("\n可用數據:")
    for year, race_list in sorted(races.items()):
        print(f"  {year}: {len(race_list)} 場比賽")
    
    # 車手設定 (可以改成其他車手)
    driver_abbr = "VER"
    driver_number = 1  # Verstappen
    
    print(f"\n分析車手: {driver_abbr} (#{driver_number})")
    print("-" * 70)
    
    all_results: Dict[int, List[StartReactionResult]] = {}
    
    for year, race_list in sorted(races.items()):
        all_results[year] = []
        print(f"\n{year}賽季: 分析中...")
        
        for race_dir in race_list:
            result = analyze_race_start(race_dir, driver_number, year)
            all_results[year].append(result)
            
            # 即時輸出
            pos_delta = format_position_delta(result.position_delta)
            t100 = format_time(result.time_to_100)
            grid = result.grid_position or "?"
            lap1 = result.lap1_end_position or "?"
            print(f"  {result.race_name:<20} | P{grid} -> P{lap1} ({pos_delta:>3}) | 0-100: {t100}")
    
    # 輸出摘要表格
    print("\n" + "=" * 70)
    print("摘要: 首圈位置變化 (正數=進步)")
    print("=" * 70)
    
    # 收集所有賽道
    all_tracks = set()
    for year_results in all_results.values():
        for r in year_results:
            all_tracks.add(r.race_name)
    
    # 表頭
    years = sorted(all_results.keys())
    header = f"{'賽道':<22}"
    for year in years:
        header += f" | {year:>6}"
    print(header)
    print("-" * 70)
    
    # 資料行
    for track in sorted(all_tracks):
        row = f"{track:<22}"
        for year in years:
            result = next((r for r in all_results.get(year, []) if r.race_name == track), None)
            if result:
                delta = format_position_delta(result.position_delta)
            else:
                delta = "-"
            row += f" | {delta:>6}"
        print(row)
    
    # 統計摘要
    print("\n" + "=" * 70)
    print("年度統計")
    print("=" * 70)
    
    for year in years:
        results = all_results.get(year, [])
        valid_deltas = [r.position_delta for r in results if r.position_delta is not None]
        valid_times = [r.time_to_100 for r in results if r.time_to_100 is not None]
        
        if valid_deltas:
            avg_delta = sum(valid_deltas) / len(valid_deltas)
            gains = sum(1 for d in valid_deltas if d > 0)
            losses = sum(1 for d in valid_deltas if d < 0)
            holds = sum(1 for d in valid_deltas if d == 0)
            
            print(f"\n{year}賽季:")
            print(f"  首圈平均變化: {avg_delta:+.2f} 位置")
            print(f"  起跑進步: {gains} 場 | 維持: {holds} 場 | 退步: {losses} 場")
            
            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                print(f"  平均 0-100 km/h: {avg_time:.2f}秒")


if __name__ == '__main__':
    main()
