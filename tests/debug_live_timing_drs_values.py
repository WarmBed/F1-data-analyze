"""
檢查 Live Timing API 原始數據中的 DRS 值分佈
特別關注 DRS=0 是否存在
"""

import sys
import json
import gzip
import base64
import zlib
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def parse_jsonstream(content: str):
    """解析 jsonStream 格式 (12-char timestamp + base64/zlib payload)"""
    entries = []
    lines = content.strip().split('\r\n')
    
    for line in lines:
        if len(line) < 12:
            continue
        
        timestamp_str = line[:12]
        payload = line[12:]
        
        try:
            # Base64 解碼
            compressed = base64.b64decode(payload)
            # Zlib 解壓縮
            decompressed = zlib.decompress(compressed, -zlib.MAX_WBITS)
            # JSON 解析
            data = json.loads(decompressed.decode('utf-8'))
            entries.append({
                'timestamp': timestamp_str,
                'data': data
            })
        except Exception as e:
            continue
    
    return entries


def download_cardata_from_api():
    """直接從 F1 API 下載 CarData.z"""
    import requests
    
    # 2025 Abu Dhabi Race
    # 根據 F1 API 結構: https://livetiming.formula1.com/static/{year}/{meeting_key}/{session}/CarData.z.jsonStream
    
    # 首先找到 meeting key
    year = 2025
    index_url = f"https://livetiming.formula1.com/static/{year}/Index.json"
    
    print(f"正在獲取 {year} 年索引...")
    resp = requests.get(index_url, timeout=30)
    if resp.status_code != 200:
        print(f"❌ 無法獲取索引: HTTP {resp.status_code}")
        return None
    
    # 處理 UTF-8 BOM
    content = resp.content.decode('utf-8-sig')
    index = json.loads(content)
    meetings = index.get("Meetings", [])
    
    # 找 Abu Dhabi
    abu_dhabi = None
    for meeting in meetings:
        name = meeting.get("Name", "").lower()
        if "abu" in name and "dhabi" in name:
            abu_dhabi = meeting
            break
    
    if not abu_dhabi:
        print("❌ 找不到 Abu Dhabi 賽事")
        return None
    
    print(f"✅ 找到賽事: {abu_dhabi['Name']}")
    
    # 找 Race session
    race_session = None
    for session in abu_dhabi.get("Sessions", []):
        if session.get("Name") == "Race":
            race_session = session
            break
    
    if not race_session:
        print("❌ 找不到 Race 會話")
        return None
    
    session_path = race_session.get("Path")
    print(f"✅ 會話路徑: {session_path}")
    
    # 下載 CarData.z
    cardata_url = f"https://livetiming.formula1.com/static/{session_path}CarData.z.jsonStream"
    print(f"正在下載 CarData.z...")
    print(f"URL: {cardata_url}")
    
    resp = requests.get(cardata_url, timeout=60)
    if resp.status_code != 200:
        print(f"❌ 下載失敗: HTTP {resp.status_code}")
        return None
    
    print(f"✅ 下載成功 ({len(resp.content)} bytes)")
    return resp.content.decode('utf-8-sig')


def analyze_cardata_drs():
    """分析 CarData.z 中的 DRS Channel 45"""
    
    print("="*80)
    print("正在從 F1 Live Timing API 下載 CarData.z")
    print("="*80)
    
    content = download_cardata_from_api()
    if not content:
        return
    
    print("正在解析 jsonStream...")
    entries = parse_jsonstream(content)
    print(f"總共 {len(entries)} 個時間戳記錄\n")
    
    # 統計 DRS 值
    drs_counter = Counter()
    driver_drs_samples = {}  # 每個車手的 DRS 樣本數
    
    entries_with_drs = 0
    total_drs_values = 0
    
    for idx, entry in enumerate(entries):
        data = entry['data']
        
        # 檢查數據結構
        entries_data = None
        if isinstance(data, dict):
            entries_data = data.get('Entries')
        
        if not entries_data:
            continue
        
        has_drs_in_this_entry = False
        
        # Entries 可能是列表或字典
        if isinstance(entries_data, list):
            # 列表格式: [{'Utc': ..., 'Cars': {'1': {'Channels': {...}}, ...}}, ...]
            for timestamp_entry in entries_data:
                if not isinstance(timestamp_entry, dict):
                    continue
                
                cars = timestamp_entry.get('Cars', {})
                if not isinstance(cars, dict):
                    continue
                
                for driver_num, car_data in cars.items():
                    if not isinstance(car_data, dict):
                        continue
                    
                    channels = car_data.get('Channels', {})
                    
                    # Channel 45 = DRS
                    if '45' in channels:
                        drs_value = channels['45']
                        drs_counter[str(drs_value)] += 1
                        total_drs_values += 1
                        has_drs_in_this_entry = True
                        
                        # 統計每個車手
                        if driver_num not in driver_drs_samples:
                            driver_drs_samples[driver_num] = Counter()
                        driver_drs_samples[driver_num][str(drs_value)] += 1
        
        elif isinstance(entries_data, dict):
            # 字典格式: {'1': {'Channels': {...}}, '10': ...}
            for driver_num, car_data in entries_data.items():
                if not isinstance(car_data, dict):
                    continue
                
                channels = car_data.get('Channels', {})
                
                # Channel 45 = DRS
                if '45' in channels:
                    drs_value = channels['45']
                    drs_counter[str(drs_value)] += 1
                    total_drs_values += 1
                    has_drs_in_this_entry = True
                    
                    # 統計每個車手
                    if driver_num not in driver_drs_samples:
                        driver_drs_samples[driver_num] = Counter()
                    driver_drs_samples[driver_num][str(drs_value)] += 1
        
        if has_drs_in_this_entry:
            entries_with_drs += 1
    
    # 輸出統計
    print("="*80)
    print("📊 Live Timing API CarData.z DRS 分佈（Channel 45）")
    print("="*80)
    print(f"包含 DRS 數據的時間戳: {entries_with_drs}/{len(entries)}")
    print(f"總 DRS 樣本數: {total_drs_values}\n")
    
    print("全局 DRS 值分佈:")
    for drs_val, count in sorted(drs_counter.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        pct = (count / total_drs_values * 100) if total_drs_values > 0 else 0
        status = get_drs_status(drs_val)
        print(f"  {drs_val:>3s}: {count:>7d} ({pct:>6.2f}%) - {status}")
    
    # 檢查是否有 DRS=0
    if '0' in drs_counter:
        print(f"\n✅ DRS=0 存在於原始數據中 ({drs_counter['0']} 次)")
    else:
        print(f"\n⚠️  DRS=0 不存在於原始數據中！")
    
    # 顯示前 3 位車手的 DRS 分佈
    print("\n" + "="*80)
    print("前 3 位車手的 DRS 分佈:")
    print("="*80)
    
    for idx, (driver_num, drs_data) in enumerate(sorted(driver_drs_samples.items())[:3]):
        print(f"\n車手 {driver_num}:")
        total_samples = sum(drs_data.values())
        for drs_val, count in sorted(drs_data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
            pct = (count / total_samples * 100) if total_samples > 0 else 0
            status = get_drs_status(drs_val)
            print(f"  {drs_val:>3s}: {count:>5d} ({pct:>5.1f}%) - {status}")


def get_drs_status(drs_val_str: str) -> str:
    """獲取 DRS 狀態描述"""
    try:
        val = int(drs_val_str)
        if val == 0:
            return "Disabled (0)"
        elif val == 1:
            return "Disabled (1)"
        elif val >= 10 and val % 2 == 0:
            return "ON"
        elif val >= 2 and val % 2 == 0:
            return "RDY"
        else:
            return "Unknown"
    except:
        return "?"


if __name__ == "__main__":
    analyze_cardata_drs()
