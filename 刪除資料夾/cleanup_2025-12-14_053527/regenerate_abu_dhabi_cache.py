"""
重新生成 Abu Dhabi 2025 Race 的 PKL 快取
使用修正後的 CarData 處理邏輯（不累積舊的 DRS 狀態）
"""

import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader


def main():
    print("="*70)
    print("重新生成 Abu Dhabi 2025 Race PKL 快取")
    print("="*70)
    print()
    
    # 初始化下載器
    downloader = F1APIDownloader()
    
    # 設定快取目錄（使用 dist 目錄）
    cache_dir = project_root / "dist" / "live_timing_cache"
    downloader.cache_dir = cache_dir
    
    print(f"快取目錄: {cache_dir}")
    print()
    
    # 進度回調
    def progress_callback(percent, message):
        print(f"[{percent:>3d}%] {message}")
    
    # 下載並處理數據（強制重新生成）
    print("開始下載並處理數據...")
    print("-"*70)
    
    result = downloader.download_and_cache(
        year=2025,
        race="Abu_Dhabi",
        session="Race",
        force=True,  # 強制重新下載
        progress_callback=progress_callback
    )
    
    if result:
        print("-"*70)
        print("✅ PKL 快取生成成功!")
        print(f"   - 快照數量: {len(result.get('snapshots', []))}")
        print(f"   - 車手數量: {len(result.get('driver_info', {}))}")
        print(f"   - 進站事件: {len(result.get('pit_events', []))}")
        
        # 檢查 DRS 數據
        print()
        print("檢查 DRS 數據分佈...")
        
        from collections import Counter
        drs_counter = Counter()
        total_drivers_with_drs = 0
        
        for snapshot in result.get('snapshots', [])[:1000]:  # 檢查前1000個快照
            for driver_num, driver_data in snapshot.get('drivers', {}).items():
                drs_val = driver_data.get('drs')
                if drs_val is not None and drs_val != '':
                    drs_counter[str(drs_val)] += 1
                    total_drivers_with_drs += 1
        
        print(f"   - 總 DRS 樣本數: {total_drivers_with_drs}")
        print(f"   - DRS 值分佈 (前1000個快照):")
        
        for drs_val, count in sorted(drs_counter.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            percentage = (count / total_drivers_with_drs) * 100 if total_drivers_with_drs > 0 else 0
            
            try:
                val = int(drs_val)
                if val >= 10 and val % 2 == 0:
                    status = "ON"
                elif val >= 2 and val % 2 == 0:
                    status = "RDY"
                else:
                    status = "Disabled"
            except:
                status = "?"
            
            print(f"     {drs_val:>3s}: {count:>6d} ({percentage:>5.2f}%) - {status}")
        
        print()
        print(f"快取檔案位置: {downloader.get_cache_path(2025, 'Abu_Dhabi', 'Race')}")
        print()
        print("="*70)
        print("💡 完成！現在可以在 GUI 中測試 Live Timing 了")
        print("="*70)
    else:
        print("-"*70)
        print("❌ PKL 快取生成失敗")
        print("="*70)


if __name__ == "__main__":
    main()
