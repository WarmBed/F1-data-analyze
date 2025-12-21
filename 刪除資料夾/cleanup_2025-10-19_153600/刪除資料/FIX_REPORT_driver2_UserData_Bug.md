# 🐛 Driver2 UserData Bug 修復報告

## 問題總結

**症狀**：日語模式下選擇 driver2 為 LEC 後，圈速分析視窗沒有更新為雙車手比較模式。

**根本原因**：`driver2_combo` 的所有項目 UserData 都是 `None`，導致無法判斷使用者是否選擇了車手。

---

## 🔍 診斷過程

### 1. 初步觀察
日誌顯示 `driver2 = None`，但使用者確實選擇了 LEC：
```log
17:45:18 | 圈速控制 - 更新參數: VER vs None
```

### 2. 添加診斷日誌
在 `update_all_lap_analysis` 中添加詳細狀態檢查：
```python
logger.info(f"[DEBUG] 🔍 driver2_combo 詳細狀態檢查:")
logger.info(f"  currentIndex: {self.driver2_combo.currentIndex()}")
logger.info(f"  currentText: '{self.driver2_combo.currentText()}'")
logger.info(f"  currentData: {self.driver2_combo.currentData()}")
```

### 3. 發現關鍵證據
日誌顯示：
```log
17:52:42 | currentIndex: 3
17:52:42 | currentText: 'LEC'  ✅ 文字正確
17:52:42 | currentData: None   ❌ UserData 錯誤！

所有項目列表:
  [0] text='なし', data=None
  [1] text='VER', data=None   ❌ 應該是 'VER'
  [2] text='PER', data=None   ❌ 應該是 'PER'  
  [3] text='LEC', data=None   ❌ 應該是 'LEC'
```

**結論**：所有車手項目的 UserData 都是 `None`！

### 4. 定位問題程式碼
在 `f1t_gui_main.py` line 5973：
```python
# ❌ 錯誤：addItems() 不支援設定 UserData
self.driver2_combo.addItems(drivers)
```

**原因**：`QComboBox.addItems()` 只能批次添加文字，無法設定每個項目的 UserData。

---

## ✅ 修復方案

### 修改位置
`f1t_gui_main.py` line 5965-5975

### 修改前（錯誤）
```python
self.driver1_combo.clear()
self.driver1_combo.addItems(drivers)  # ❌ 沒有 UserData

self.driver2_combo.clear()
self.driver2_combo.addItem(tr("none_option", "None"))  # ⚠️ 沒有設定 UserData 為 None
self.driver2_combo.addItems(drivers)  # ❌ 沒有 UserData
```

### 修改後（正確）
```python
self.driver1_combo.clear()
# 🔧 修復：使用 addItem 並設定 UserData
for driver in drivers:
    self.driver1_combo.addItem(driver, driver)

self.driver2_combo.clear()
# 🔧 修復：第一個選項的 UserData 設為 None
self.driver2_combo.addItem(tr("none_option", "None"), None)
# 🔧 修復：使用 addItem 並設定 UserData
for driver in drivers:
    self.driver2_combo.addItem(driver, driver)
```

### 關鍵變更
1. **driver1_combo**：改用 `for` 迴圈逐個添加，設定 `UserData = driver`
2. **driver2_combo**：
   - "無" 選項明確設定 `UserData = None`
   - 車手選項逐個添加，設定 `UserData = driver`

---

## 🧪 驗證測試

### 預期修復後的日誌
```log
[DEBUG] 🔍 driver2_combo 詳細狀態檢查:
  currentIndex: 3
  currentText: 'LEC'
  currentData: 'LEC'  ✅ 正確！

所有項目列表:
  [0] text='なし', data=None      ✅ 正確
  [1] text='VER', data='VER'      ✅ 正確
  [2] text='PER', data='PER'      ✅ 正確
  [3] text='LEC', data='LEC'      ✅ 正確
  
  → 最終 driver2 判斷: driver2_data='LEC' → driver2='LEC'  ✅
```

### 預期行為
1. 使用者選擇 driver2 為 LEC
2. 系統正確讀取 `driver2 = 'LEC'`
3. 圈速分析視窗執行雙車手比較（VER vs LEC）
4. 所有遙測模組顯示兩條曲線

---

## 📊 影響範圍

### 受影響功能
- ✅ 圈速控制面板的 driver2 選擇
- ✅ 所有遙測分析模組（速度、煞車、油門、RPM 等）
- ✅ 雙車手比較功能

### 相關檔案
- `f1t_gui_main.py` (line 5965-5975)

### 受影響的語言模式
- ✅ 中文模式
- ✅ 英文模式
- ✅ **日語模式**（最初發現問題的模式）

---

## 🎯 根本原因分析

### Qt API 知識點

**QComboBox 添加項目的方法**：

1. **addItem(text, userData)**
   - 添加單個項目
   - ✅ 支援設定 UserData
   - 用法：`combo.addItem("VER", "VER")`

2. **addItems(texts)**
   - 批次添加多個項目
   - ❌ **不支援設定 UserData**
   - UserData 全部預設為 `None`
   - 用法：`combo.addItems(["VER", "LEC", "PER"])`

### 程式邏輯依賴

在 `update_all_lap_analysis` 中：
```python
driver2_data = self.driver2_combo.currentData()  # 依賴 UserData
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
```

**邏輯**：
- 如果 `currentData()` 返回 `None`，表示選擇了 "無" → `driver2 = None`
- 如果 `currentData()` 返回車手代碼，表示選擇了車手 → `driver2 = currentData()`

**問題**：當所有項目的 UserData 都是 `None` 時，即使選擇了 "LEC"，`currentData()` 仍返回 `None`，導致誤判！

---

## 💡 經驗教訓

1. **使用 addItems() 時要注意限制**
   - 只適合純文字顯示，不需要 UserData 的場景
   - 如需 UserData，必須使用 `addItem()` 逐個添加

2. **調試工具的重要性**
   - 詳細的日誌診斷快速定位問題
   - 顯示 `currentData()` 是關鍵

3. **測試覆蓋**
   - 應該測試所有語言模式下的 driver2 選擇
   - 驗證 UserData 是否正確設定

---

## ✅ 修復狀態

- [x] 問題定位
- [x] 程式碼修復
- [ ] 重啟測試驗證
- [ ] 多語言測試
- [ ] 使用者確認

---

## 下一步行動

1. **立即執行**：重啟 GUI 測試修復效果
2. **驗證步驟**：
   - 切換到日語模式
   - 選擇 driver2 為 LEC
   - 點擊更新按鈕
   - 檢查日誌中 `currentData` 是否為 'LEC'
   - 確認遙測模組顯示雙車手比較

3. **測試其他語言**：
   - 中文模式測試
   - 英文模式測試

---

**修復時間**：2025-10-06 17:54  
**修復者**：GitHub Copilot  
**驗證狀態**：待測試 ⏳
