"""
重新生成 Abu Dhabi 2025 Race 的 PKL 快取
驗證 DRS=0 修復是否生效
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader


def regenerate_pkl():
    """重新生成 PKL"""
    downloader = F1APIDownloader()
    
    year = 2025
    race = "Abu Dhabi"
    session = "Race"
    
    print("="*80)
    print(f"重新生成 PKL: {year} {race} {session}")
    print("="*80)
    
    # 檢查並刪除舊的 PKL
    cache_path = downloader.get_cache_path(year, race, session)
    if cache_path.exists():
        print(f"刪除舊 PKL: {cache_path}")
        cache_path.unlink()
    
    # 重新下載和處理
    print("\n正在從 F1 API 下載數據...")
    
    def progress_callback(percent, message):
        print(f"[{percent:3d}%] {message}")
    
    result = downloader.download_and_cache(
        year=year,
        race=race,
        session=session,
        progress_callback=progress_callback
    )
    
    if result:
        print(f"\n✅ PKL 生成成功: {cache_path}")
        print(f"   快照數量: {len(result.get('snapshots', []))}")
        
        # 快速驗證 DRS 分佈
        from collections import Counter
        drs_counter = Counter()
        
        for snapshot in result.get('snapshots', []):
            for driver_num, driver_data in snapshot.get('drivers', {}).items():
                drs_val = driver_data.get('drs')
                if drs_val is not None and drs_val != '':
                    drs_counter[str(drs_val)] += 1
        
        total_drs = sum(drs_counter.values())
        print(f"\n   DRS 分佈驗證:")
        for drs_val, count in sorted(drs_counter.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
            pct = (count / total_drs * 100) if total_drs > 0 else 0
            print(f"     {drs_val:>3s}: {count:>6d} ({pct:>5.2f}%)")
        
        if '0' in drs_counter:
            drs_0_pct = (drs_counter['0'] / total_drs * 100)
            print(f"\n   ✅ DRS=0 存在: {drs_0_pct:.2f}% (預期 ~79%)")
            if drs_0_pct > 50:
                print("   🎉 修復成功！DRS=0 已正確記錄！")
            else:
                print("   ⚠️  DRS=0 比例偏低，可能還有其他問題")
        else:
            print(f"\n   ❌ DRS=0 仍然缺失！")
    else:
        print("\n❌ PKL 生成失敗")


if __name__ == "__main__":
    regenerate_pkl()
