"""
從官方 F1 Live Timing API 下載並分析原始 DRS 數據
檢查 CarData.z 的 Channel 45 (DRS) 原始值
"""

import sys
import requests
import json
import zlib
import base64
from collections import Counter

def download_and_analyze_drs(year: int, meeting: str, session: str):
    """
    從官方 API 下載並分析 DRS 數據
    
    Args:
        year: 賽季年份 (例如: 2025)
        meeting: 賽事名稱 (例如: "Abu_Dhabi")
        session: 賽段 (例如: "Race")
    """
    base_url = "https://livetiming.formula1.com/static"
    
    # 步驟 1: 獲取年度索引找到正確的路徑
    print(f"正在查詢 {year} 年度索引...")
    index_url = f"{base_url}/{year}/Index.json"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(index_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 解碼 UTF-8-BOM
        content = response.content.decode('utf-8-sig')
        index_data = json.loads(content)
        
        meetings = index_data.get('Meetings', [])
        print(f"✅ 找到 {len(meetings)} 場賽事")
        
        # 尋找對應的賽事
        target_meeting = None
        for m in meetings:
            if meeting.lower() in m.get('Name', '').lower().replace(' ', '_'):
                target_meeting = m
                break
        
        if not target_meeting:
            print(f"❌ 找不到賽事: {meeting}")
            print(f"可用賽事: {[m.get('Name') for m in meetings]}")
            return
        
        print(f"✅ 找到賽事: {target_meeting.get('Name')}")
        
        # 尋找對應的賽段
        sessions = target_meeting.get('Sessions', [])
        target_session = None
        
        session_map = {
            'race': 'Race',
            'r': 'Race',
            'qualifying': 'Qualifying',
            'q': 'Qualifying',
            'fp1': 'Practice 1',
            'fp2': 'Practice 2',
            'fp3': 'Practice 3',
        }
        
        session_normalized = session_map.get(session.lower(), session)
        
        for s in sessions:
            if session_normalized.lower() in s.get('Name', '').lower():
                target_session = s
                break
        
        if not target_session:
            print(f"❌ 找不到賽段: {session}")
            print(f"可用賽段: {[s.get('Name') for s in sessions]}")
            return
        
        print(f"✅ 找到賽段: {target_session.get('Name')}")
        
        # 構建 CarData.z.jsonStream 的 URL
        session_path = target_session.get('Path', '').strip('/')
        cardata_url = f"{base_url}/{session_path}/CarData.z.jsonStream"
        
        print(f"\n正在下載 CarData.z 數據...")
        print(f"URL: {cardata_url}")
        print("="*70)
        
        response = requests.get(cardata_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✅ 下載成功 ({len(response.content)} bytes)")
        
        # 解析 jsonStream 格式 (每行一個 JSON)
        lines = response.text.strip().split('\n')
        print(f"✅ 共 {len(lines)} 筆記錄")
        
        # 統計 DRS 值分佈
        drs_distribution = Counter()
        drs_by_driver = {}
        total_samples = 0
        records_with_drs = 0
        
        for line_num, line in enumerate(lines, 1):
            try:
                # jsonStream 格式: 前12字符是時間戳，後面是 JSON
                if len(line) <= 12:
                    continue
                
                timestamp = line[:12]
                payload_text = line[12:]
                
                # 解壓縮 (base64 + zlib for .z files)
                try:
                    decoded = base64.b64decode(payload_text)
                    decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                    data = json.loads(decompressed.decode('utf-8'))
                except:
                    # 可能不是壓縮格式
                    try:
                        data = json.loads(payload_text)
                    except:
                        continue
                
                # 提取 Entries
                entries = data.get('Entries', [])
                
                if not isinstance(entries, list) or not entries:
                    continue
                
                # 取最新的 entry
                latest_entry = entries[-1] if entries else {}
                cars = latest_entry.get('Cars', {})
                
                if not cars:
                    continue
                
                records_with_drs += 1
                
                # 遍歷所有車手
                for driver_num, car_info in cars.items():
                    channels = car_info.get('Channels', {})
                    
                    # Channel 45 = DRS
                    drs_val = channels.get('45') or channels.get(45)
                    
                    if drs_val is not None and drs_val != '':
                        total_samples += 1
                        drs_str = str(drs_val)
                        
                        # 全局統計
                        drs_distribution[drs_str] += 1
                        
                        # 按車手統計
                        if driver_num not in drs_by_driver:
                            drs_by_driver[driver_num] = Counter()
                        drs_by_driver[driver_num][drs_str] += 1
                
                # 進度顯示
                if line_num % 100 == 0:
                    print(f"處理進度: {line_num}/{len(lines)} ({line_num/len(lines)*100:.1f}%)", end='\r')
            
            except Exception as e:
                if line_num <= 5:  # 只顯示前幾筆的錯誤
                    print(f"⚠️  行 {line_num} 解析錯誤: {e}")
                continue
        
        print(f"\n{'='*70}")
        print(f"✅ 解析完成")
        print(f"   - 有效記錄: {records_with_drs}/{len(lines)}")
        print(f"   - DRS 樣本數: {total_samples}")
        print(f"{'='*70}\n")
        
        # 顯示 DRS 值分佈
        print(f"📊 DRS 值分佈 (總樣本數: {total_samples})")
        print("="*70)
        
        if total_samples == 0:
            print("⚠️  沒有找到任何 DRS 數據!")
            return
        
        # 按 DRS 值排序
        sorted_drs = sorted(drs_distribution.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
        
        for drs_val, count in sorted_drs:
            percentage = (count / total_samples) * 100
            
            # 判斷狀態
            try:
                val = int(drs_val)
                if val >= 10 and val % 2 == 0:
                    status = "ON (實際開啟)"
                elif val >= 2 and val % 2 == 0:
                    status = "RDY (可用未開)"
                elif val % 2 == 1:
                    status = "Disabled (禁用)"
                else:
                    status = "Off"
            except:
                status = "Unknown"
            
            print(f"  {drs_val:>3s}: {count:>7d} ({percentage:>6.2f}%) - {status}")
        
        # 顯示車手統計
        print(f"\n📊 按車手統計 (前 5 名)")
        print("="*70)
        
        sample_drivers = sorted(drs_by_driver.keys())[:5]
        
        for driver_num in sample_drivers:
            driver_stats = drs_by_driver[driver_num]
            driver_total = sum(driver_stats.values())
            
            print(f"\n車手 {driver_num} (樣本數: {driver_total})")
            
            sorted_driver_drs = sorted(driver_stats.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
            
            for drs_val, count in sorted_driver_drs:
                percentage = (count / driver_total) * 100
                
                try:
                    val = int(drs_val)
                    if val >= 10 and val % 2 == 0:
                        status = "ON"
                    elif val >= 2 and val % 2 == 0:
                        status = "RDY"
                    else:
                        status = "OFF/Disabled"
                except:
                    status = "?"
                
                print(f"  {drs_val:>3s}: {count:>6d} ({percentage:>6.2f}%) - {status}")
        
        print(f"\n{'='*70}")
        print("💡 分析完成")
        print(f"{'='*70}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下載失敗: {e}")
        return
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 預設測試: 2025 Abu Dhabi Race
    if len(sys.argv) >= 4:
        year = int(sys.argv[1])
        meeting = sys.argv[2]
        session = sys.argv[3]
    else:
        year = 2025
        meeting = "Abu_Dhabi"
        session = "Race"
    
    print("="*70)
    print(f"F1 Live Timing API - DRS 數據分析")
    print(f"賽季: {year} | 賽事: {meeting} | 賽段: {session}")
    print("="*70)
    print()
    
    download_and_analyze_drs(year, meeting, session)
