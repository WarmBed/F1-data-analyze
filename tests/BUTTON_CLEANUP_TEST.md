# F1T GUI 按鈕清理測試清單
# 日期: 2025-10-15
# 測試目標: 確認「Update All Analysis」和「Lap Linkage」按鈕都能正確清理

## 測試步驟

### 步驟 1: 初始狀態檢查
- [ ] 重啟 F1T GUI（應用最新修復）
- [ ] 確認主工具欄中**沒有**「Update All Analysis」按鈕
- [ ] 確認主工具欄中**沒有**「Lap Linkage」按鈕

### 步驟 2: 開啟 Speed Analysis 模組
- [ ] 在 GUI 中開啟 Speed Analysis 模組
- [ ] 確認「Update All Analysis」按鈕**出現**在工具欄
- [ ] 確認「Lap Linkage」按鈕**出現**在工具欄
- [ ] 記錄工具欄按鈕數量: _______

### 步驟 3: 關閉視窗（使用 Close All Windows）
- [ ] 點擊 「View」→「Close All Windows」
- [ ] 確認 Speed Analysis 視窗已關閉
- [ ] 等待 2 秒（讓清理邏輯執行）

### 步驟 4: 檢查按鈕清理結果
- [ ] 檢查「Update All Analysis」按鈕是否消失？ 預期: **應該消失**
- [ ] 檢查「Lap Linkage」按鈕是否消失？ 預期: **應該消失**
- [ ] 記錄工具欄按鈕數量: _______

### 步驟 5: Force GC 測試（如果按鈕仍存在）
- [ ] 點擊「Force GC」按鈕 10 次
- [ ] 每次點擊後觀察終端輸出的 GC 回收物件數
- [ ] 記錄是否有物件被回收: _______

### 步驟 6: Objgraph 記憶體分析（如果按鈕仍存在）
- [ ] 點擊「Snapshot」建立記憶體快照
- [ ] 檢查報告中 QAction 的數量
- [ ] 記錄是否有異常增長: _______

## 測試結果

### 修復前（預期）:
- ❌ 「Update All Analysis」按鈕仍然顯示
- ✅ 「Lap Linkage」按鈕消失（已修復）

### 修復後（目標）:
- ✅ 「Update All Analysis」按鈕應該消失
- ✅ 「Lap Linkage」按鈕應該消失

## 如果測試失敗

### 情況 A: 兩個按鈕都還在
**問題**: `hide_lap_controls()` 沒有被調用
**檢查**:
1. 終端輸出是否有 `[LAP_CONTROL] 🔴 開始隱藏圈速分析控件`
2. 是否有錯誤訊息

### 情況 B: 只有「Update All Analysis」還在
**問題**: `update_all_action` 引用不正確或移除邏輯有問題
**檢查**:
1. 終端輸出是否有 `[LAP_CONTROL] ✅ 圈速分析控件成功從工具欄移除`
2. 使用 Python Debug Console 執行: `print(hasattr(main_window, 'update_all_action'))`

### 情況 C: 兩個按鈕都消失了
**結果**: ✅ 修復成功！記憶體洩漏源已找到並修復

## 後續動作

如果測試成功:
1. 提交代碼變更
2. 更新修復文檔
3. 長期監控記憶體使用量

如果測試失敗:
1. 提供終端完整日誌
2. 執行內嵌式 objgraph 分析
3. 進行更深入的引用鏈追蹤
