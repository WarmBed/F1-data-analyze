# 模組完整對比檢查清單

## 使用說明
當需要從 Speed 模組複製功能到其他模組時，必須執行以下完整檢查清單。

---

## 階段 0：功能定義
- [ ] 明確定義要複製的功能（例如：時間軸切換）
- [ ] 確認功能在 Speed 模組中已正常運作
- [ ] 列出所有涉及的方法和屬性

---

## 階段 1：搜索所有相關代碼（Speed 模組）

### 1.1 搜索核心方法
```bash
grep_search "set_time_axis_mode" speed_analysis_mdi.py
grep_search "set_time_axis_mode" speed_analysis_chart_widget.py
grep_search "use_time_axis" speed_analysis_mdi.py
grep_search "use_time_axis" speed_analysis_chart_widget.py
```

### 1.2 搜索數據傳遞
```bash
grep_search "driver1_time" speed_analysis_chart_widget.py
grep_search "driver2_time" speed_analysis_chart_widget.py
grep_search "min_time" speed_analysis_chart_widget.py
grep_search "max_time" speed_analysis_chart_widget.py
```

### 1.3 搜索所有調用點
```bash
grep_search "\.set_time_axis_mode\(" speed_analysis_mdi.py
```

**記錄所有調用位置**：
- 位置 1：________________________ (Line ____)
- 位置 2：________________________ (Line ____)
- 位置 3：________________________ (Line ____)

---

## 階段 2：對比每個方法的完整實現

### 2.1 核心方法對比

#### 方法 1：`set_time_axis_mode()`
- [ ] Speed 模組 Line _____ - _____ 已讀取
- [ ] Brake 模組 Line _____ - _____ 已讀取
- [ ] 逐行對比完成
- [ ] 差異已記錄：________________________________

#### 方法 2：`set_speed_data()` / `set_brake_data()`
- [ ] Speed 模組 Line _____ - _____ 已讀取
- [ ] Brake 模組 Line _____ - _____ 已讀取
- [ ] 逐行對比完成
- [ ] 差異已記錄：________________________________

#### 方法 3：`__init__()`
- [ ] Speed 模組 Line _____ - _____ 已讀取
- [ ] Brake 模組 Line _____ - _____ 已讀取
- [ ] 屬性初始化已對比：
  - [ ] `use_time_axis`
  - [ ] `driver1_time`
  - [ ] `driver2_time`
  - [ ] `min_time`
  - [ ] `max_time`

---

## 階段 3：對比所有調用點

### 3.1 調用點 1：`update_cross_event_comparison()`
- [ ] Speed 模組中的調用位置：Line _____
- [ ] Brake 模組中的對應位置：Line _____
- [ ] 調用順序一致：
  ```
  Speed: set_time_axis_mode() → _update_chart()
  Brake: set_time_axis_mode() → _update_chart()
  ```
- [ ] 差異已記錄：________________________________

### 3.2 調用點 2：`update_lap_parameters()`
- [ ] Speed 模組中的調用位置：Line _____
- [ ] Brake 模組中的對應位置：Line _____
- [ ] 調用時機一致
- [ ] 差異已記錄：________________________________

### 3.3 調用點 3：`_on_cross_event_data_loaded()`
- [ ] Speed 模組中的調用位置：Line _____
- [ ] Brake 模組中的對應位置：Line _____
- [ ] 調用前的數據準備一致
- [ ] 差異已記錄：________________________________

---

## 階段 4：數據流追蹤

### 4.1 時間軸狀態的完整生命週期

#### 初始化階段
- [ ] Speed: `__init__()` 中 `use_time_axis = False`
- [ ] Brake: `__init__()` 中 `use_time_axis = False`

#### 數據載入階段
- [ ] Speed: `set_speed_data()` 中儲存 `driver1_time`, `driver2_time`
- [ ] Brake: `set_brake_data()` 中儲存 `driver1_time`, `driver2_time`
- [ ] Speed: 計算 `min_time`, `max_time`
- [ ] Brake: 計算 `min_time`, `max_time`

#### 狀態切換階段
- [ ] Speed: `set_time_axis_mode(True)` → `min_distance = min_time`
- [ ] Brake: `set_time_axis_mode(True)` → `min_distance = min_time`
- [ ] Speed: `set_time_axis_mode(False)` → `min_distance = min(distance_data)`
- [ ] Brake: `set_time_axis_mode(False)` → `min_distance = min(distance_data)`

#### 繪製階段
- [ ] Speed: `_draw_speed_curves()` 根據 `use_time_axis` 選擇數據源
- [ ] Brake: `_draw_brake_curves()` 根據 `use_time_axis` 選擇數據源
- [ ] Speed: `_draw_axes()` 根據 `use_time_axis` 繪製標題
- [ ] Brake: `_draw_axes()` 根據 `use_time_axis` 繪製標題

---

## 階段 5：錯誤處理對比

### 5.1 異常情況檢查
- [ ] 如果 `driver1_time` 為空，Speed 模組如何處理？
- [ ] 如果 `driver1_time` 為空，Brake 模組如何處理？
- [ ] 如果 `use_time_axis=True` 但沒有時間數據，Speed 如何處理？
- [ ] 如果 `use_time_axis=True` 但沒有時間數據，Brake 如何處理？

---

## 階段 6：整合測試計劃

### 6.1 功能測試場景
- [ ] 場景 1：首次載入數據（時間軸未勾選）
  - [ ] Speed 模組：距離軸 ✅
  - [ ] Brake 模組：距離軸 ✅

- [ ] 場景 2：勾選時間軸 Checkbox
  - [ ] Speed 模組：時間軸 ✅
  - [ ] Brake 模組：時間軸 ✅

- [ ] 場景 3：取消勾選時間軸 Checkbox
  - [ ] Speed 模組：距離軸 ✅
  - [ ] Brake 模組：距離軸 ✅

- [ ] 場景 4：跨賽事模式 + 時間軸
  - [ ] Speed 模組：時間軸 ✅
  - [ ] Brake 模組：時間軸 ✅

- [ ] 場景 5：跨賽事模式 + 取消時間軸
  - [ ] Speed 模組：距離軸 ✅
  - [ ] Brake 模組：距離軸 ✅

### 6.2 回歸測試
- [ ] 原有功能未受影響
- [ ] 圖表縮放功能正常
- [ ] 滑鼠追蹤功能正常
- [ ] 分段標記顯示正常

---

## 階段 7：代碼審查清單

### 7.1 命名一致性
- [ ] 變數命名與 Speed 模組一致
- [ ] 方法命名與 Speed 模組一致
- [ ] 註釋風格與 Speed 模組一致

### 7.2 調試日誌完整性
- [ ] 所有關鍵步驟都有 print 日誌
- [ ] 日誌前綴統一（`[BRAKE_CHART]`, `[brake_MDI]`）
- [ ] 時間軸相關日誌包含 `🕒 [TIME_AXIS]` 標記

### 7.3 性能考量
- [ ] 沒有不必要的重複計算
- [ ] 沒有記憶體洩漏風險
- [ ] repaint() 調用次數合理

---

## 完成標準

✅ **所有檢查項目都勾選完成**
✅ **所有差異都已記錄並修復**
✅ **所有測試場景都通過**
✅ **代碼審查無問題**

---

## 範例：時間軸功能對比記錄

### 發現的差異
1. **Brake 模組缺少 `min_time`, `max_time` 屬性初始化**
   - 位置：`__init__()` Line 73-75
   - 修復：已添加屬性初始化

2. **Brake 模組 `set_brake_data()` 只在 `use_time_axis=True` 時計算時間範圍**
   - 位置：Line 187-201
   - 修復：改為無條件計算時間範圍

3. **Brake 模組 `_on_cross_event_data_loaded()` 缺少 `set_time_axis_mode()` 調用**
   - 位置：Line 745-747
   - 修復：在 `_update_chart()` 前添加 `set_time_axis_mode()` 調用

### 測試結果
- ✅ 場景 1-5 全部通過
- ✅ 回歸測試通過
- ✅ 代碼審查通過
