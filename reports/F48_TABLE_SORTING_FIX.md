# F48 表格排序修正報告

## 問題描述

用戶反映點擊「加速時間」欄位標題時，排序順序混亂：
- 預期：7.119s → 8.160s → 8.400s（升序）
- 實際：9.920s → 8.560s → ...（無規律）

## 問題根因

### ❌ 原始錯誤代碼（Line 360-381）

```python
def _populate_table(self):
    """填充表格數據"""
    self.table.setSortingEnabled(False)
    
    # ❌ 問題：預先按最高速度排序
    sorted_data = sorted(
        self.driver_speeds_data, 
        key=lambda x: x.get("max_speed_kmh", 0), 
        reverse=True  # 降序：338 km/h → 326 km/h
    )
    
    for row, driver_data in enumerate(sorted_data):
        self._populate_row(row, row + 1, driver_data)
    
    self.table.setSortingEnabled(True)  # 啟用排序
```

**問題分析**：
1. 表格在填充前就已經按 `max_speed_kmh` **降序排列**
2. 這導致 Qt 內建排序功能的**初始狀態**是「已按最高速度降序」
3. 當用戶點擊「加速時間」欄位時，Qt 嘗試從當前狀態切換排序
4. 但因為初始數據已被預先排序，Qt 的排序邏輯無法正確追蹤排序狀態
5. 結果：排序順序完全混亂

### ✅ 正確模式：Ideal Lap Ranking Table

對比 `ideal_lap_ranking_table_widget.py`（參考實現）：

```python
def populate_table(self, ranking_data: List[Dict[str, Any]]):
    self.table.setSortingEnabled(False)  # 暫時禁用排序
    
    # ✅ 直接按原始順序填充（不預先排序）
    for row, driver in enumerate(ranking_data):
        self._set_row_data(row, driver)
    
    self.table.setSortingEnabled(True)  # ✅ 重新啟用排序
```

**正確邏輯**：
- 表格按**原始順序**填充（通常是字母順序或 API 返回順序）
- Qt 內建排序功能從「未排序狀態」開始
- 用戶點擊任何欄位標題時，Qt 能正確追蹤排序狀態
- 第一次點擊：升序，第二次點擊：降序，第三次點擊：恢復原始順序

## 修正方案

### 修正後的代碼（Line 360-382）

```python
def _populate_table(self):
    """填充表格數據"""
    self.table.setSortingEnabled(False)
    
    # ✅ 修正：學習 Ranking Table - 不預先排序，讓 Qt 內建排序功能處理
    # ❌ 舊代碼：預先按最高速度排序，導致 Qt 排序功能混亂
    # sorted_data = sorted(
    #     self.driver_speeds_data, 
    #     key=lambda x: x.get("max_speed_kmh", 0), 
    #     reverse=True
    # )
    
    # ✅ 直接按原始順序填充（通常是按車手代碼字母順序）
    for row, driver_data in enumerate(self.driver_speeds_data):
        self._populate_row(row, row + 1, driver_data)
    
    self.table.setSortingEnabled(True)
```

## 驗證結果

### 測試數據：Azerbaijan 2025

| 車手 | 加速時間 (100→320 km/h) | 預期升序排名 |
|------|-------------------------|-------------|
| LEC  | 20.120s                 | 1           |
| HAM  | 20.321s                 | 2           |
| ANT  | 20.481s                 | 3           |
| ...  | ...                     | ...         |
| STR  | 24.040s                 | 19          |

### 預期行為

**第一次點擊「加速時間」欄位**（升序）：
```
1. LEC: 20.120s （最快）
2. HAM: 20.321s
3. ANT: 20.481s
...
19. STR: 24.040s （最慢）
```

**第二次點擊「加速時間」欄位**（降序）：
```
1. STR: 24.040s （最慢）
2. SAI: 23.320s
3. RUS: 23.081s
...
19. LEC: 20.120s （最快）
```

**第三次點擊「加速時間」欄位**（恢復原始順序）：
```
按車手代碼字母順序（A-Z）
ALB, ALO, ANT, BEA, COL, ...
```

## 關鍵修正點

### 1. 移除預先排序邏輯
- **Before**: `sorted_data = sorted(...)`
- **After**: 直接遍歷 `self.driver_speeds_data`

### 2. 讓 Qt 管理排序狀態
- **Before**: 開發者控制初始排序順序
- **After**: Qt `setSortingEnabled(True)` 完全管理排序

### 3. 保持數據完整性
- 每個 Item 的 `Qt.UserRole` 必須存儲正確的排序鍵
- 欄位 4（加速時間）：`accel_100_300_time`
- 欄位 3（最高速度）：`max_speed`

## 技術債務清理

### 相關代碼變更
1. **Line 367-371**：註釋掉舊的排序邏輯
2. **Line 373**：改為直接遍歷原始數據
3. **保留**：所有 `Qt.UserRole` 設置邏輯（用於排序）

### 後續優化建議
1. 考慮移除 `position` 參數（Line 373），因為它不再反映實際排名
2. 可選：添加初始排序提示（例如默認按車手代碼升序）
3. 統一所有表格模組使用相同的排序模式

## 參考實現

**遵循 Ranking Table 模式**：
- `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_widget.py`
- Line 284-304: `populate_table()` 方法
- 核心原則：**不預先排序，讓 Qt 處理所有排序邏輯**

## 測試清單

- [ ] 點擊「加速時間」欄位標題
- [ ] 驗證升序：LEC (20.120s) 第一名
- [ ] 驗證降序：STR (24.040s) 第一名
- [ ] 驗證其他欄位排序（車手、車隊、最高速度）
- [ ] 多次切換排序順序（確保無混亂）

## 結論

**問題**：預先排序導致 Qt 內建排序功能狀態追蹤失敗
**解決方案**：移除所有預先排序邏輯，讓 Qt 完全管理排序狀態
**學習來源**：參考 Ideal Lap Ranking Table 的正確實現

---

**修正日期**: 2025-10-15  
**相關檔案**: `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`  
**修正行數**: Line 360-382
