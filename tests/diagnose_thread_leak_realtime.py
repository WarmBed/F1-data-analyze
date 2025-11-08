"""
即時執行緒洩漏診斷工具
監控 GUI 運行時的執行緒變化，特別是 DummyThread
"""

import threading
import time
import sys
from collections import defaultdict
from datetime import datetime

def get_thread_details():
    """獲取當前所有執行緒的詳細資訊"""
    threads = threading.enumerate()
    details = {
        'total': len(threads),
        'by_type': defaultdict(list),
        'by_name': defaultdict(int)
    }
    
    for thread in threads:
        thread_type = type(thread).__name__
        thread_name = thread.name
        thread_info = {
            'name': thread_name,
            'type': thread_type,
            'daemon': thread.daemon,
            'alive': thread.is_alive(),
            'ident': thread.ident
        }
        details['by_type'][thread_type].append(thread_info)
        details['by_name'][thread_name] += 1
    
    return details

def print_thread_summary(details, label=""):
    """打印執行緒摘要"""
    print(f"\n{'='*80}")
    print(f"⏰ {datetime.now().strftime('%H:%M:%S.%f')[:-3]} - {label}")
    print(f"{'='*80}")
    print(f"📊 總執行緒數: {details['total']}")
    print(f"\n📋 依類型分類:")
    
    for thread_type, threads in sorted(details['by_type'].items()):
        print(f"  • {thread_type}: {len(threads)} 個")
        if thread_type == '_DummyThread' or 'Dummy' in thread_type:
            print(f"    ⚠️  DummyThread 詳情:")
            for idx, thread in enumerate(threads, 1):
                print(f"       {idx}. {thread['name']} (ID: {thread['ident']}, Daemon: {thread['daemon']})")
    
    print(f"\n📋 依名稱分類 (前 10 個):")
    for name, count in sorted(details['by_name'].items(), key=lambda x: x[1], reverse=True)[:10]:
        marker = "⚠️ " if count > 1 or 'Dummy' in name else "  "
        print(f"  {marker}{name}: {count} 個")
    print(f"{'='*80}\n")

def compare_threads(before, after):
    """比較兩次執行緒快照的差異"""
    print(f"\n{'🔍 執行緒變化分析':=^80}")
    
    # 總數變化
    delta_total = after['total'] - before['total']
    print(f"總執行緒數變化: {before['total']} → {after['total']} ({delta_total:+d})")
    
    # 類型變化
    print(f"\n📊 依類型變化:")
    all_types = set(before['by_type'].keys()) | set(after['by_type'].keys())
    for thread_type in sorted(all_types):
        count_before = len(before['by_type'].get(thread_type, []))
        count_after = len(after['by_type'].get(thread_type, []))
        delta = count_after - count_before
        
        if delta != 0:
            marker = "🔴" if 'Dummy' in thread_type else "🔵"
            print(f"  {marker} {thread_type}: {count_before} → {count_after} ({delta:+d})")
    
    # 找出新增的 DummyThread
    dummy_before = set(t['ident'] for t in before['by_type'].get('_DummyThread', []))
    dummy_after = set(t['ident'] for t in after['by_type'].get('_DummyThread', []))
    new_dummies = dummy_after - dummy_before
    
    if new_dummies:
        print(f"\n⚠️  新增 {len(new_dummies)} 個 DummyThread:")
        for thread in after['by_type'].get('_DummyThread', []):
            if thread['ident'] in new_dummies:
                print(f"     • {thread['name']} (ID: {thread['ident']})")
    
    print(f"{'='*80}\n")

def monitor_continuous(interval=2):
    """持續監控模式"""
    print(f"\n🔄 開始持續監控（每 {interval} 秒更新一次，按 Ctrl+C 停止）")
    baseline = get_thread_details()
    print_thread_summary(baseline, "初始狀態")
    
    try:
        while True:
            time.sleep(interval)
            current = get_thread_details()
            
            # 檢查是否有變化
            if current['total'] != baseline['total']:
                print(f"\n{'⚠️  偵測到變化！':=^80}")
                compare_threads(baseline, current)
                print_thread_summary(current, f"當前狀態（變化：{current['total'] - baseline['total']:+d}）")
            else:
                # 簡單更新
                dummy_count = len(current['by_type'].get('_DummyThread', []))
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - 總執行緒: {current['total']} (DummyThread: {dummy_count})", end='\r')
    except KeyboardInterrupt:
        print("\n\n✋ 監控已停止")
        final = get_thread_details()
        print_thread_summary(final, "最終狀態")
        compare_threads(baseline, final)

def snapshot_mode():
    """快照模式 - 手動觸發"""
    print("\n📸 快照模式")
    print("  1. 顯示當前狀態")
    print("  2. 保存基準快照")
    print("  3. 與基準快照比較")
    print("  4. 退出")
    
    baseline = None
    
    while True:
        choice = input("\n請選擇操作 (1-4): ").strip()
        
        if choice == '1':
            current = get_thread_details()
            print_thread_summary(current, "當前狀態")
        
        elif choice == '2':
            baseline = get_thread_details()
            print(f"✅ 已保存基準快照（總執行緒: {baseline['total']}）")
        
        elif choice == '3':
            if baseline is None:
                print("❌ 請先保存基準快照（選項 2）")
            else:
                current = get_thread_details()
                compare_threads(baseline, current)
                print_thread_summary(current, "當前狀態")
        
        elif choice == '4':
            print("👋 退出")
            break
        
        else:
            print("❌ 無效選擇，請輸入 1-4")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔍 即時執行緒洩漏診斷工具                              ║
║                                                                            ║
║  用途：監控 F1T GUI 執行時的執行緒變化，特別是 DummyThread 洩漏         ║
║                                                                            ║
║  使用方式：                                                                ║
║    1. 先啟動此工具（選擇模式 1 或 2）                                     ║
║    2. 在另一個終端啟動 F1T GUI                                            ║
║    3. 點擊 "Update All Analysis" 按鈕                                      ║
║    4. 觀察此工具的輸出                                                     ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("選擇監控模式:")
    print("  1. 持續監控模式（自動偵測變化）")
    print("  2. 快照模式（手動觸發比較）")
    print("  3. 單次快照並退出")
    
    mode = input("\n請選擇模式 (1-3): ").strip()
    
    if mode == '1':
        monitor_continuous()
    elif mode == '2':
        snapshot_mode()
    elif mode == '3':
        current = get_thread_details()
        print_thread_summary(current, "當前執行緒狀態")
    else:
        print("❌ 無效選擇")
