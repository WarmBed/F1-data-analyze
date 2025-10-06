# 🔍 Driver2 更新問題診斷報告

## 問題現象
使用者報告：在日語模式下，選擇 driver2 為 LEC 後，圈速分析視窗沒有更新顯示 LEC 的數據。

## 日誌證據分析

### 證據 1: Driver2 Combo 初始狀態
```log
2025-10-06 17:45:10 | INFO | f1.console | [LAP_CONTROL]   driver2_combo當前文字: 'なし'
2025-10-06 17:45:10 | INFO | f1.console | [LAP_CONTROL]   driver2_combo項目數: 21
```
**解讀**：driver2_combo 有 21 個項目（"なし" + 20位車手），當前選擇是 "なし"（日語的「無」）

### 證據 2: update_all_lap_analysis 接收的參數
```log
2025-10-06 17:45:18 | INFO | f1.gui.main | 圈速控制 - 更新參數: VER vs None, 第1圈 vs 第1圈, 最速圈: False
```
**解讀**：`driver2 = None`，表示在呼叫更新函數時，driver2 仍然是 None

### 證據 3: 模組更新時收到的參數
```log
2025-10-06 17:45:20 | INFO | f1.console | [REFRESH] [MODULE] RPM分析_2025_Australia_R 參數已更新: {'year': '2025', 'race': 'Australia', 'session': 'R', 'driver1': 'VER', 'driver2': None, 'lap1': 1, 'lap2': 1}
```
**解讀**：所有遙測模組接收到的 `driver2` 參數都是 `None`

### 證據 4: 單車手模式被觸發
```log
2025-10-06 17:45:09 | INFO | f1.console | [SPEED DEBUG] 單車手模式啟動，driver2 將使用 VER
2025-10-06 17:45:09 | INFO | f1.console | [SPEED DEBUG] 參數: {'year': 2025, 'race': 'Australia', 'session': 'R', 'driver1': 'VER', 'driver2': 'VER', 'lap1': 1, 'lap2': 1, 'force_refresh': False}
```
**解讀**：由於 driver2 是 None，系統自動啟用單車手模式，將 driver2 設定為與 driver1 相同（VER vs VER）

## 問題根本原因

### 假設 A: UI 事件未正確觸發
使用者在下拉選單中選擇 "LEC"，但是 `driver2_combo` 的 `currentIndexChanged` 或 `currentTextChanged` 事件沒有被觸發或處理。

**檢查點**：
- driver2_combo 是否有連接任何信號槽？
- 日語模式下的選項文字是否與預期一致？

### 假設 B: 選項的 UserData 未正確設置
在添加 driver2_combo 的選項時，可能沒有正確設置 `currentData()`。

**檢查程式碼**：
```python
# 在 _load_available_drivers() 中
self.driver2_combo.addItem(none_label, None)  # ✅ 正確設置 UserData 為 None
for driver in drivers:
    self.driver2_combo.addItem(driver, driver)  # ✅ 正確設置 UserData 為 driver
```
**結論**：程式碼正確

### 假設 C: 時間順序問題
使用者選擇 LEC 的時間點與 `update_all_lap_analysis` 被呼叫的時間點之間存在競態條件。

**時間線分析**：
```
17:45:10 - driver2_combo 顯示為 'なし'
17:45:18 - update_all_lap_analysis 被呼叫，driver2=None
```
**推測**：使用者可能在 17:45:10 到 17:45:18 之間選擇了 LEC，但系統沒有捕捉到這個變更。

### 假設 D: 日語模式翻譯問題 ⚠️ **最可能**
driver2_combo 的文字顯示為日語，但在獲取 `currentData()` 時可能因為翻譯鍵值不一致導致問題。

**檢查 tr() 函數**：
```python
# f1t_gui_main.py line 6295
driver2_data = self.driver2_combo.currentData()
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
```

**邏輯分析**：
1. 如果 `driver2_data` 是 `None`（選擇"なし"），則 `driver2 = None` ✅
2. 如果 `driver2_data` 是 `"LEC"`（選擇 LEC），則 `driver2 = "LEC"` ✅
3. **但是**：如果選擇了 LEC 但 `currentData()` 返回 `None`，則會誤判！❌

## 診斷結論

**主要問題**：使用者在日語介面中選擇 driver2 為 LEC 後，`update_all_lap_analysis` 函數讀取 `driver2_combo.currentData()` 時返回 `None`，導致系統認為使用者沒有選擇 driver2。

**可能原因**：
1. ✅ 程式碼邏輯正確（已確認）
2. ❓ UI 事件處理遺失
3. ❓ 時間競態條件
4. ⚠️ **最可能**：driver2_combo 的索引沒有正確切換到 LEC 項目

## 建議解決方案

### 方案 1: 增加調試日誌
在 `update_all_lap_analysis` 函數中增加詳細的日誌：

```python
# 在 f1t_gui_main.py line 6290 附近添加
logger.info(f"[DEBUG] driver2_combo 狀態檢查:")
logger.info(f"  currentIndex: {self.driver2_combo.currentIndex()}")
logger.info(f"  currentText: {self.driver2_combo.currentText()}")
logger.info(f"  currentData: {self.driver2_combo.currentData()}")
logger.info(f"  count: {self.driver2_combo.count()}")
for i in range(self.driver2_combo.count()):
    logger.info(f"    [{i}] text='{self.driver2_combo.itemText(i)}', data={self.driver2_combo.itemData(i)}")

driver2_data = self.driver2_combo.currentData()
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
logger.info(f"  → 最終 driver2 = {driver2}")
```

### 方案 2: 強制刷新 driver2_combo
在選擇變更時強制觸發更新：

```python
# 在 driver2_combo 初始化時添加信號連接
self.driver2_combo.currentIndexChanged.connect(self._on_driver2_changed)

def _on_driver2_changed(self, index):
    """當 driver2 選擇變更時的處理"""
    driver2_text = self.driver2_combo.currentText()
    driver2_data = self.driver2_combo.currentData()
    logger.info(f"[DRIVER2_CHANGED] 索引={index}, 文字='{driver2_text}', 數據={driver2_data}")
```

### 方案 3: 修改 driver2 獲取邏輯（更穩健）
改為優先使用 `currentText()` 並與 "None" 選項比較：

```python
# 修改 f1t_gui_main.py line 6295
driver2_text = self.driver2_combo.currentText()
none_labels = [tr("none_option", "None"), "None", "無", "なし"]  # 所有語言的 "無" 選項
driver2 = None if driver2_text in none_labels else driver2_text
logger.info(f"圈速控制 - driver2 判斷: currentText='{driver2_text}' → driver2={driver2}")
```

## 下一步行動

1. **立即執行**：添加方案 1 的調試日誌，重新測試並觀察日誌輸出
2. **中期執行**：實施方案 2，添加 driver2 變更事件處理
3. **長期優化**：實施方案 3，使用更穩健的判斷邏輯

## 預期測試結果

執行方案 1 後，日誌應該顯示：
```log
[DEBUG] driver2_combo 狀態檢查:
  currentIndex: X  # 應該是 LEC 的索引（例如 2 或 3）
  currentText: 'LEC'  # 或 'なし' 如果未選擇
  currentData: 'LEC'  # 或 None
  count: 21
    [0] text='なし', data=None
    [1] text='VER', data='VER'
    [2] text='LEC', data='LEC'
    ...
  → 最終 driver2 = 'LEC'  # 期望值
```

如果 `currentIndex` 仍然是 0 且 `currentText` 是 "なし"，則確定是 UI 事件未觸發的問題。
