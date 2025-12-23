"""
深度追蹤 DummyThread 的引用鏈
找出是誰在持有這些執行緒的引用
"""
import objgraph
import gc
import threading
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("DummyThread 引用鏈追蹤報告")
print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

# 強制垃圾回收
print("步驟 1: 執行垃圾回收...")
collected = gc.collect()
print(f"  回收了 {collected} 個物件")
print()

# 統計 DummyThread
print("步驟 2: 統計 DummyThread...")
dummy_count_objgraph = objgraph.count("_DummyThread")
active_threads = threading._active
dummy_count_threading = sum(1 for t in active_threads.values() if type(t).__name__ == "_DummyThread")
print(f"  objgraph.count: {dummy_count_objgraph}")
print(f"  threading._active: {dummy_count_threading}")
print()

# 獲取所有 DummyThread 實例
print("步驟 3: 獲取 DummyThread 實例...")
dummies = objgraph.by_type("_DummyThread")
print(f"  找到 {len(dummies)} 個 DummyThread 實例")
print()

if dummies:
    # 分析前 5 個實例的引用鏈
    print("步驟 4: 分析前 5 個 DummyThread 的引用鏈...")
    print("-" * 80)
    
    output_dir = Path("objgraph_traces")
    output_dir.mkdir(exist_ok=True)
    
    for i, dummy in enumerate(dummies[:5], 1):
        print(f"\n🔍 DummyThread #{i}:")
        print(f"   名稱: {dummy.name}")
        print(f"   存活: {dummy.is_alive()}")
        print(f"   Daemon: {dummy.daemon}")
        print(f"   Ident: {dummy.ident}")
        
        # 生成引用圖
        graph_file = output_dir / f"dummythread_{i}_backrefs.png"
        try:
            print(f"   生成引用圖: {graph_file}")
            objgraph.show_backrefs(
                [dummy],
                max_depth=5,
                filename=str(graph_file),
                refcounts=True
            )
            print(f"   ✅ 引用圖已保存")
        except Exception as e:
            print(f"   ❌ 生成引用圖失敗: {e}")
        
        # 列出直接引用者
        print(f"   直接引用者:")
        referrers = gc.get_referrers(dummy)
        for j, ref in enumerate(referrers[:3], 1):
            ref_type = type(ref).__name__
            print(f"     {j}. {ref_type}: {str(ref)[:100]}")
        
        print("-" * 80)
    
    print()
    print("步驟 5: 檢查常見的 DummyThread 來源...")
    print("-" * 80)
    
    # 檢查可能的來源
    potential_sources = [
        ("QThread", "PyQt QThread"),
        ("Thread", "Python threading.Thread"),
        ("ApiWorker", "API Worker 執行緒"),
        ("DataLoader", "數據載入器"),
        ("QNetworkAccessManager", "Qt 網路管理器"),
        ("QTimer", "Qt 計時器"),
    ]
    
    for class_name, description in potential_sources:
        count = objgraph.count(class_name)
        if count > 0:
            print(f"  ✅ {description} ({class_name}): {count} 個")
        else:
            print(f"  ⚪ {description} ({class_name}): 0 個")
    
    print("-" * 80)
    print()
    
    # 生成整體類型統計
    print("步驟 6: 生成整體物件類型統計...")
    stats_file = output_dir / "object_type_stats.txt"
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("物件類型統計（Top 50）\n")
        f.write("=" * 80 + "\n\n")
        objgraph.show_most_common_types(limit=50, file=f)
    print(f"  ✅ 統計已保存至: {stats_file}")
    print()
    
    # 生成成長報告（需要先調用一次 show_growth）
    print("步驟 7: 記錄當前物件狀態（用於後續成長追蹤）...")
    objgraph.show_growth(limit=0)  # 初始化
    print("  ✅ 已記錄當前狀態")
    print()

print("=" * 80)
print("追蹤完成！")
print("=" * 80)
print()
print("📁 輸出檔案位置:")
print(f"  - 引用圖: objgraph_traces/dummythread_*_backrefs.png")
print(f"  - 類型統計: objgraph_traces/object_type_stats.txt")
print()
print("💡 下一步:")
print("  1. 查看引用圖，找出是誰在持有 DummyThread")
print("  2. 檢查對應的模組是否正確實現了 cleanup()")
print("  3. 如果是 Qt 相關，檢查是否正確調用了 deleteLater()")
print("=" * 80)
