"""
測試 F1 官方 livetiming API
"""
import requests
import json

def test_livetiming_api():
    print("=== 測試 F1 官方 livetiming API ===\n")
    
    # 1. 獲取 2025 年索引
    url = 'https://livetiming.formula1.com/static/2025/Index.json'
    resp = requests.get(url, timeout=30)
    print(f"Index.json Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"錯誤: {resp.text}")
        return
    
    data = json.loads(resp.content.decode('utf-8-sig'))
    meetings = data.get('Meetings', [])
    print(f"找到 {len(meetings)} 個賽事\n")
    
    # 2. 顯示最後 5 個賽事
    print("最近 5 個賽事:")
    for m in meetings[-5:]:
        name = m.get('Name')
        sessions = m.get('Sessions', [])
        print(f"  {name}: {len(sessions)} 個 sessions")
        for s in sessions:
            print(f"    - {s.get('Name')}: {s.get('Path')}")
    
    # 3. 專門找 Abu Dhabi
    print("\n=== 查找 Abu Dhabi ===")
    abu_dhabi = None
    for m in meetings:
        if 'Abu Dhabi' in m.get('Name', ''):
            abu_dhabi = m
            break
    
    if abu_dhabi:
        print(f"找到: {abu_dhabi.get('Name')}")
        print(f"Sessions:")
        for s in abu_dhabi.get('Sessions', []):
            print(f"  - {s.get('Name')}: {s.get('Path')}")
    else:
        print("未找到 Abu Dhabi 賽事")


def test_fp2_download():
    print("\n=== 測試 FP2 下載 ===\n")
    
    from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader
    
    downloader = F1APIDownloader()
    
    # 測試路徑查找
    print("1. 測試路徑查找...")
    path = downloader._find_session_path(2025, 'Abu Dhabi', 'FP2')
    print(f"   FP2 Path: {path}")
    
    if path:
        # 測試下載
        print("\n2. 測試下載...")
        result = downloader.download_and_cache(2025, 'Abu Dhabi', 'FP2', force=True)
        
        if result:
            snapshots = result.get('snapshots', [])
            print(f"   下載成功!")
            print(f"   Snapshots: {len(snapshots)}")
            if snapshots:
                first = snapshots[0]
                drivers = first.get('drivers', {})
                print(f"   First snapshot drivers: {len(drivers)}")
        else:
            print("   下載失敗")


if __name__ == "__main__":
    test_livetiming_api()
    test_fp2_download()
