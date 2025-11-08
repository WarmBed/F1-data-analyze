"""
針對性記憶體洩漏測試
==========================================
測試策略：單模組 + 詳細日誌 + cleanup() 驗證
"""

import gc
import objgraph

def test_single_module_cleanup():
    """測試單個模組的 cleanup() 效果"""
    print("=" * 80)
    print("🎯 單模組 cleanup() 測試")
    print("=" * 80)
    
    print("\n步驟 1: 基準記憶體快照")
    gc.collect()
    baseline = len(gc.get_objects())
    print(f"基準物件數: {baseline:,}")
    
    print("\n步驟 2: 模擬開啟 Speed Analysis 模組")
    print("（請在 GUI 中手動操作）")
    print("  - 點擊 Tools → Lap Analysis → Speed Analysis")
    print("  - 等待載入完成")
    input("按 Enter 繼續...")
    
    print("\n步驟 3: 開啟後記憶體快照")
    gc.collect()
    after_open = len(gc.get_objects())
    increase = after_open - baseline
    print(f"開啟後物件數: {after_open:,} (+{increase:,})")
    
    # 詳細物件類型統計
    print("\n📊 物件增長前 10 名:")
    objgraph.show_growth(limit=10)
    
    print("\n步驟 4: 關閉模組")
    print("（請在 GUI 中手動操作）")
    print("  - 點擊 Speed Analysis 視窗的關閉按鈕")
    print("  - 等待視窗關閉")
    input("按 Enter 繼續...")
    
    print("\n步驟 5: 關閉後記憶體快照")
    gc.collect()
    after_close = len(gc.get_objects())
    leak = after_close - baseline
    recovered = after_open - after_close
    
    print(f"\n" + "=" * 80)
    print("🔍 測試結果")
    print("=" * 80)
    print(f"基準物件數:   {baseline:,}")
    print(f"開啟後物件數: {after_open:,}  (+{increase:,})")
    print(f"關閉後物件數: {after_close:,}  (+{leak:,})")
    print(f"回收物件數:   {recovered:,}")
    print(f"洩漏物件數:   {leak:,}")
    print()
    
    # 評估
    if leak < 100:
        print("✅ 記憶體洩漏極少 - cleanup() 有效！")
    elif leak < 500:
        print("⚠️  記憶體洩漏適中 - cleanup() 部分有效")
    else:
        print("❌ 記憶體洩漏嚴重 - cleanup() 無效！")
    
    # 詳細洩漏分析
    if leak > 100:
        print("\n📊 洩漏物件類型分析:")
        objgraph.show_growth(limit=20)
        
        # 檢查特定物件類型
        print("\n🔍 關鍵物件類型檢查:")
        for obj_type in ['QTableWidgetItem', 'QLabel', 'QPushButton', 'function', 'dict']:
            count = objgraph.count(obj_type)
            print(f"  {obj_type:25s} : {count:>6,} 個")


def add_cleanup_logging():
    """添加 cleanup() 詳細日誌的指導"""
    print("\n" + "=" * 80)
    print("💡 如何添加 cleanup() 詳細日誌")
    print("=" * 80)
    
    print("""
在 speed_analysis_chart_widget.py 的 cleanup() 方法開頭添加：

```python
def cleanup(self):
    '''清理資源'''
    print(f"\\n[SPEED_CHART] ========== 開始 cleanup() ==========")
    
    # Stage 1: Matplotlib
    print(f"[SPEED_CHART] 階段 1: 清理 Matplotlib")
    if hasattr(self.chart_widget, 'figure') and self.chart_widget.figure:
        print(f"[SPEED_CHART]   - Figure 存在，開始清理...")
        self.chart_widget.figure.clear()
        import matplotlib.pyplot as plt
        plt.close(self.chart_widget.figure)
        self.chart_widget.figure = None
        print(f"[SPEED_CHART]   ✅ Matplotlib 已清理")
    else:
        print(f"[SPEED_CHART]   ⚠️  Figure 不存在")
    
    # Stage 2: QTableWidget
    print(f"[SPEED_CHART] 階段 2: 清理 QTableWidget")
    if hasattr(self, 'stats_table') and self.stats_table:
        row_count = self.stats_table.rowCount()
        col_count = self.stats_table.columnCount()
        print(f"[SPEED_CHART]   - 表格大小: {row_count} 行 x {col_count} 列")
        
        item_count = 0
        for row in range(row_count):
            for col in range(col_count):
                item = self.stats_table.item(row, col)
                if item:
                    self.stats_table.takeItem(row, col)
                    del item
                    item_count += 1
        
        self.stats_table.clear()
        self.stats_table.deleteLater()
        self.stats_table = None
        print(f"[SPEED_CHART]   ✅ 已刪除 {item_count} 個 QTableWidgetItem")
    else:
        print(f"[SPEED_CHART]   ⚠️  stats_table 不存在")
    
    # ... 其他階段類似添加日誌
    
    print(f"[SPEED_CHART] ========== cleanup() 完成 ==========\\n")
```

然後重新測試，檢查終端輸出！
""")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║          針對性記憶體洩漏測試工具                                        ║
║                                                                          ║
║  目的：測試單個模組的 cleanup() 實際效果                                ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    print("⚠️  注意：此測試需要 GUI 手動操作配合")
    print("請確保：")
    print("  1. F1T GUI 已啟動")
    print("  2. 已開啟 Memory Diagnostics 視窗")
    print("  3. 準備好開啟/關閉 Speed Analysis 模組")
    print()
    
    choice = input("是否繼續測試？(y/n): ").strip().lower()
    if choice != 'y':
        print("測試取消")
        return
    
    test_single_module_cleanup()
    add_cleanup_logging()


if __name__ == "__main__":
    main()
