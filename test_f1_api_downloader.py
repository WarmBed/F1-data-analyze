"""
測試 F1APIDownloader 功能
"""

from modules.gui.live_timing.core import F1APIDownloader

def test_list_meetings():
    """測試列出賽事"""
    print("=" * 60)
    print("測試 1: 列出 2025 年賽事")
    print("=" * 60)
    
    d = F1APIDownloader()
    meetings = d.list_meetings(2025)
    
    print(f"找到 {len(meetings)} 場賽事:")
    for m in meetings[:5]:
        print(f"  - {m.get('Name')}")
    
    return len(meetings) > 0

def test_find_session_path():
    """測試查找會話路徑"""
    print("\n" + "=" * 60)
    print("測試 2: 查找 Japan 2025 Race 路徑")
    print("=" * 60)
    
    d = F1APIDownloader()
    path = d._find_session_path(2025, "Japan", "R")
    
    print(f"路徑: {path}")
    return path is not None

def test_cache_path():
    """測試快取路徑"""
    print("\n" + "=" * 60)
    print("測試 3: 檢查快取路徑")
    print("=" * 60)
    
    d = F1APIDownloader()
    
    cache_path = d.get_cache_path(2025, "Japan", "Race")
    print(f"快取路徑: {cache_path}")
    
    is_valid = d.is_cache_valid(2025, "Japan", "Race")
    print(f"快取有效: {is_valid}")
    
    return True

def test_download_and_cache():
    """測試下載並快取"""
    print("\n" + "=" * 60)
    print("測試 4: 下載 Japan 2025 Race 並建立 PKL 快取")
    print("=" * 60)
    
    d = F1APIDownloader()
    
    def progress_callback(percent, msg):
        print(f"  [{percent:3d}%] {msg}")
    
    result = d.download_and_cache(
        year=2025,
        race="Japan",
        session="Race",
        force=False,
        progress_callback=progress_callback
    )
    
    if result:
        print(f"\n下載成功!")
        print(f"  快照數量: {len(result.get('snapshots', []))}")
        print(f"  車手數量: {len(result.get('driver_info', {}))}")
        print(f"  版本: {result.get('version')}")
        return True
    else:
        print("下載失敗")
        return False

def main():
    import sys
    
    print("F1APIDownloader 測試")
    print("=" * 60)
    
    results = []
    
    results.append(("列出賽事", test_list_meetings()))
    results.append(("查找會話路徑", test_find_session_path()))
    results.append(("快取路徑", test_cache_path()))
    
    # 只有在指定參數時才執行下載測試
    if len(sys.argv) > 1 and sys.argv[1] == "--download":
        results.append(("下載並快取", test_download_and_cache()))
    else:
        print("\n提示: 執行 'python test_f1_api_downloader.py --download' 進行完整下載測試")
    
    print("\n" + "=" * 60)
    print("測試結果:")
    print("=" * 60)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

if __name__ == "__main__":
    main()
