# Objgraph Memory Diagnostic - Snapshot State 功能說明

## 📸 功能概述

**Snapshot State** 按鈕現在提供全面的記憶體診斷功能，自動整合 **Object Scan** 和 **Growth Track**。

## 🎯 核心功能

### 1. **全面物件記錄**
- ✅ 記錄**所有物件類型**（limit=200），不只 Top 5
- ✅ 包含物件數量和百分比
- ✅ 格式化輸出，易於閱讀

### 2. **自動 Growth Track**
- ✅ 第二次 Snapshot 自動觸發成長追蹤
- ✅ 記錄所有類型的變化（增加/減少）
- ✅ 與 Growth Track Tab 同步更新

### 3. **操作記錄整合**
- ✅ 每次 Snapshot 自動添加到操作記錄
- ✅ 顯示總物件數和變化量
- ✅ 支持顏色標示（紅色=增加，綠色=減少）

### 4. **完整日誌記錄**
- ✅ 所有物件統計記錄到診斷日誌
- ✅ Growth 變化完整記錄
- ✅ 可導出為 .txt 報告

## 📋 使用流程

### 基本使用

```
1. 點擊「快照當前狀態」→ 建立基準
   [SNAPSHOT] 總物件數: 106017
   [SNAPSHOT] 物件統計（所有 137 種類型）:
     1. function                                  22622  ( 21.34%)
     2. tuple                                     13367  ( 12.61%)
     3. dict                                      11054  ( 10.43%)
     ...
   137. SocketError                                   1  (  0.00%)

2. 執行一些操作（開啟模組、分析數據等）

3. 再次點擊「快照當前狀態」→ 觸發 Growth Track
   [SNAPSHOT + GROWTH] 已拍攝快照並追蹤成長
   [SNAPSHOT] 總物件數: 108449
   
   [GROWTH] 發現 45 種類型有變化:
     1. ↑ QTableWidgetItem                        4520 (+453)
     2. ↑ QLabel                                  1890 (+147)
     3. ↑ QPushButton                              982 (+90)
     ...
```

### 進階使用

#### 配合操作記錄
```
1. 添加操作記錄："開啟 9 個 Lap Analysis 模組"
2. 點擊 Snapshot State
3. 關閉所有模組
4. 添加操作記錄："關閉所有模組"
5. 點擊 Snapshot State
6. 查看 Growth Track - 發現記憶體洩漏
```

#### 導出完整報告
```
點擊「導出報告」→ 生成 objgraph_report_YYYYMMDD_HHMMSS.txt

報告內容:
• 操作記錄摘要（時間線 + 物件變化）
• 當前物件統計（所有類型）
• 成長追蹤記錄（所有變化）
• 完整診斷日誌（所有 Snapshot 和 Growth 記錄）
```

## 🔍 輸出格式

### 日誌格式（所有物件類型）

```
================================================================================
[SNAPSHOT + GROWTH] 已拍攝快照並追蹤成長
[SNAPSHOT] 總物件數: 108449
[SNAPSHOT] 物件統計（所有 137 種類型）:
    1. function                                  22622  ( 20.86%)
    2. tuple                                     13367  ( 12.32%)
    3. dict                                      11054  ( 10.19%)
    4. wrapper_descriptor                         6538  (  6.03%)
    5. ReferenceType                              5342  (  4.92%)
   ...
  137. SocketError                                    1  (  0.00%)

[GROWTH] 發現 45 種類型有變化:
    1. ↑ QTableWidgetItem                        4520 (+453)
    2. ↑ QLabel                                  1890 (+147)
    3. ↑ QPushButton                              982 (+90)
    4. ↑ QVBoxLayout                              455 (+45)
    5. ↓ weakref                                 3210 (-50)
   ...
================================================================================
```

### 操作記錄格式

| 時間 | 操作描述 | 物件總數 | 變化 |
|------|---------|---------|------|
| 16:17:11 | 快照 - 總計 105682 個物件 | Top 5: ... | 105,682 | 0 |
| 16:17:44 | 快照 - 總計 108449 個物件 | Top 5: ... | 108,449 | +2,769 |

## 💡 實戰範例

### 範例 1: 發現記憶體洩漏

```
[步驟 1] 點擊 Snapshot State（基準）
  → 物件總數: 105,682

[步驟 2] 開啟 9 個 Lap Analysis 模組
  → 添加操作記錄: "開啟 9 個模組"

[步驟 3] 點擊 Snapshot State（檢查點 1）
  → 物件總數: 105,680 (-2)
  → 正常，輕微波動

[步驟 4] 關閉所有模組
  → 添加操作記錄: "關閉所有模組"

[步驟 5] 點擊 Snapshot State（檢查點 2）
  → 物件總數: 108,449 (+2,769) ⚠️ 異常！
  → [GROWTH] 顯示:
      • QTableWidgetItem: +453
      • QLabel: +147
      • QPushButton: +90
  → 結論: Lap Analysis 模組關閉時未正確清理資源
```

### 範例 2: 驗證修復效果

```
[步驟 1] 修復 closeEvent() 添加 cleanup()
[步驟 2] Snapshot State（基準）: 105,682
[步驟 3] 開啟 9 個模組
[步驟 4] Snapshot State（檢查點 1）: 108,450 (+2,768)
[步驟 5] 關閉所有模組
[步驟 6] Snapshot State（檢查點 2）: 105,700 (+18) ✅
[步驟 7] 強制 GC
[步驟 8] Snapshot State（最終）: 105,685 (+3) ✅

結論: 修復成功，關閉後物件數恢復正常
```

## 📊 統計資訊

### 記錄範圍
- **物件類型數**: 最多 200 種（limit=200）
- **Growth Track**: 最多 200 種變化
- **操作記錄**: 無限制（所有 Snapshot 和手動記錄）

### 日誌詳細度
- **物件統計**: 每種類型 1 行（名稱、數量、百分比）
- **Growth Track**: 每種變化 1 行（名稱、數量、增減量）
- **操作記錄**: 每次操作 2 行（時間戳、描述、物件數、變化）

## 🛠️ 技術細節

### 實作邏輯

```python
def _on_snapshot(self):
    # 1. 獲取所有物件（limit=200）
    all_objects = objgraph.most_common_types(limit=200)
    total_objects = sum(count for name, count in all_objects)
    
    # 2. 如果有上次掃描結果，觸發 Growth Track
    if self.last_scan_result:
        growth_data = objgraph.growth(limit=200)
        # 記錄所有變化到日誌
        for name, count, delta in growth_data:
            self._log(f"  ↑/↓ {name}: {count} ({delta:+d})")
        # 更新 Growth Track Tab
        self._populate_growth_table(growth_data)
    
    # 3. 記錄所有物件類型到日誌
    for idx, (name, count) in enumerate(all_objects, 1):
        percentage = (count / total_objects * 100)
        self._log(f"  {idx:3d}. {name:40s} {count:8d}  ({percentage:5.2f}%)")
    
    # 4. 添加到操作記錄
    self._add_action_to_history(snapshot_text)
    
    # 5. 儲存為下次比較基準
    self.last_scan_result = {name: count for name, count in all_objects}
```

### 與其他功能的關係

```
┌─────────────────────────────────────────────────────────────┐
│                     Snapshot State                          │
│  （一鍵觸發所有診斷功能）                                      │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─→ [Object Scan] 掃描所有物件類型
             │   └─→ 更新「物件統計」Tab
             │
             ├─→ [Growth Track] 自動追蹤變化
             │   └─→ 更新「成長追蹤」Tab
             │
             ├─→ [Action Log] 添加操作記錄
             │   └─→ 更新「操作記錄」Tab
             │
             └─→ [Diagnostic Log] 記錄所有詳細資訊
                 └─→ 更新「診斷日誌」Tab
```

## 🎓 最佳實踐

### 1. 建立記憶體追蹤基準
```
啟動 GUI → 立即 Snapshot State → 作為基準
```

### 2. 測試前後對比
```
Snapshot State → 執行測試 → Snapshot State → 比較差異
```

### 3. 定期快照
```
使用「自動刷新」+ 手動 Snapshot State
- 自動刷新: 每 5 秒掃描物件
- 手動 Snapshot: 關鍵操作前後
```

### 4. 導出報告存檔
```
測試結束 → 點擊「導出報告」→ 保存為 .txt
- 檔案命名: objgraph_report_YYYYMMDD_HHMMSS.txt
- 包含完整時間線和所有記錄
```

## ⚠️ 注意事項

1. **首次 Snapshot 無 Growth 數據**
   - 第一次只建立基準，不會有變化記錄
   - 需要第二次 Snapshot 才會顯示 Growth

2. **limit=200 可能不夠**
   - 如果物件類型超過 200 種，部分不會記錄
   - 可修改 `objgraph.most_common_types(limit=200)` 增加 limit

3. **記憶體占用**
   - 每次 Snapshot 會儲存所有物件統計
   - 長時間運行建議定期清空操作記錄

4. **GC 影響**
   - Snapshot 前可先點擊「強制垃圾回收」
   - 確保比較的是穩定狀態

## 📚 相關文檔

- [Objgraph 整合完成報告](./OBJGRAPH_INTEGRATION_COMPLETE.md)
- [記憶體洩漏分析報告](./MEMORY_LEAK_ANALYSIS_20251015.md)
- [Lap Analysis 執行緒洩漏修復](./LAP_ANALYSIS_THREAD_LEAK_FIX_v1.md)

---

**更新日期**: 2025-10-15  
**功能版本**: v2.0 - 完整記錄版本  
**狀態**: ✅ 已實作並測試
