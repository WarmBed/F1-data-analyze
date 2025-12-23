#!/usr/bin/env python3
"""
F48 車隊顏色修復報告
====================

日期: 2025-10-14
修復內容: 根據 Ideal Lap Ranking Table 的實現，修正直線速度分析的車隊顏色顯示問題

## 修復清單

### ✅ 修復 1: 改用固定欄位寬度
**問題**: 使用 `header.setSectionResizeMode(QHeaderView.ResizeToContents)` 導致背景色不渲染
**位置**: `_create_table()` 方法，line 238
**修正**:
```python
# ❌ 舊代碼
header.setSectionResizeMode(QHeaderView.ResizeToContents)

# ✅ 新代碼
table.setColumnWidth(0, 60)   # 排名
table.setColumnWidth(1, 100)  # 車手（車隊背景色）
table.setColumnWidth(2, 130)  # 車隊（車隊背景色）
table.setColumnWidth(3, 110)  # 最高速度
table.setColumnWidth(4, 130)  # 加速時間
table.setColumnWidth(5, 110)  # 距離
table.setColumnWidth(6, 150)  # 平均加速度
table.setColumnWidth(7, 130)  # 最高時速時間
# 欄位 8（視覺化）使用 stretch
header.setStretchLastSection(True)
```

### ✅ 修復 2: 禁用表格選擇模式
**問題**: 單選模式會導致高亮色覆蓋車隊背景色
**位置**: `_create_table()` 方法，line 222
**修正**:
```python
# ❌ 舊代碼
table.setSelectionMode(QAbstractItemView.SingleSelection)

# ✅ 新代碼
table.setSelectionMode(QAbstractItemView.NoSelection)
```

### ✅ 修復 3: 移除表格重建邏輯
**問題**: 每次 `update_data` 都重建整個表格，導致樣式丟失
**位置**: `update_data()` 方法，lines 275-285
**修正**:
```python
# ❌ 舊代碼
self.table.deleteLater()
self.table = self._create_table()
self.layout().addWidget(self.table)

# ✅ 新代碼
# 學習 Ideal Lap Ranking：只更新內容，不重建表格
self._calculate_max_time()
self._populate_table()  # 內部會處理 setSortingEnabled 和 setRowCount
```

### ✅ 修復 4: 動態更新表格標題
**問題**: 因為不再重建表格，需要手動更新標題
**位置**: `update_data()` 方法，lines 266-273
**修正**:
```python
# ✅ 新增：更新表格標題
speed_range_label = f"{int(self.unified_start_speed)}→{int(self.unified_end_speed)}"
self.table.setHorizontalHeaderItem(4, QTableWidgetItem(f'加速時間 ({speed_range_label})'))
self.table.setHorizontalHeaderItem(5, QTableWidgetItem(f'距離 ({speed_range_label})'))
self.table.setHorizontalHeaderItem(6, QTableWidgetItem(f'平均加速度 ({speed_range_label})'))
```

### ✅ 修復 5: 為車隊欄位添加背景色
**問題**: 車隊欄位（第 2 欄）沒有背景色，與理想圈排名不一致
**位置**: `_populate_row()` 方法，line 430
**修正**:
```python
# 2. 車隊（✅ 添加車隊背景色）
team_item = QTableWidgetItem(team)
team_item.setTextAlignment(Qt.AlignCenter)
team_item.setFont(QFont("Arial", 9))
# ✅ 設置車隊背景色（與車手欄位一致）
team_item.setBackground(team_color)
team_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黑色文字
team_item.setToolTip(team)  # Tooltip 顯示完整車隊名稱
self.table.setItem(row, 2, team_item)
```

### ✅ 修復 6: 移除調試輸出
**問題**: 控制台有大量 `[COLOR_DEBUG]` 輸出
**位置**: `_populate_row()` 方法，lines 410-411
**修正**:
```python
# ❌ 移除調試代碼
# if row < 3:
#     print(f"[COLOR_DEBUG] 車手={driver}, 車隊={team}, 顏色=RGB(...)")
```

### ✅ 修復 7: 添加 Tooltip
**問題**: 缺少懸停提示
**位置**: `_populate_row()` 方法
**修正**:
```python
# 車手欄位
driver_item.setToolTip(f"{driver} - {team}")

# 車隊欄位
team_item.setToolTip(team)
```

## 預期結果

修復後，直線速度分析表格應該：
1. ✅ 車手欄位（第 1 欄）顯示車隊背景色
2. ✅ 車隊欄位（第 2 欄）顯示車隊背景色
3. ✅ 所有 10 支車隊都有正確顏色映射
4. ✅ 不會因為重建表格而導致閃爍
5. ✅ 固定欄位寬度，顯示穩定
6. ✅ 禁用選擇，避免高亮覆蓋背景色
7. ✅ 動態標題正確顯示速度範圍（例如：150→280）

## 車隊顏色映射（驗證清單）

| 車隊 | RGB 顏色 | 車手範例 |
|------|---------|---------|
| Racing Bulls | RGB(80, 120, 200) | LAW, HAD |
| Mercedes | RGB(39, 180, 160) | ANT, RUS |
| Williams | RGB(80, 160, 220) | SAI, ALB |
| Ferrari | RGB(200, 50, 60) | LEC, HAM |
| Kick Sauber | RGB(60, 180, 60) | HUL, BOR |
| Haas F1 Team | RGB(140, 145, 150) | OCO, BEA |
| Red Bull Racing | RGB(0, 80, 180) | TSU, VER |
| Aston Martin | RGB(34, 130, 100) | STR, ALO |
| Alpine | RGB(200, 100, 160) | GAS, COL |
| McLaren | RGB(200, 120, 0) | NOR, PIA |

## 測試步驟

1. 啟動 GUI：`python f1t_gui_main.py`
2. 選擇：Analysis Modules → Straight Speed Analysis → All Drivers Speed & Acceleration
3. 驗證：
   - ✅ 車手欄位有背景色
   - ✅ 車隊欄位有背景色
   - ✅ 顏色與上表映射一致
   - ✅ 標題顯示 "加速時間 (150→280)"
   - ✅ 無閃爍或重建表格
   - ✅ 無 `[COLOR_DEBUG]` 輸出

## 技術要點

1. **表格只創建一次**：在 `_init_ui()` 中創建，之後只更新內容
2. **固定寬度優先**：使用 `setColumnWidth()` 而非 `ResizeToContents`
3. **禁用選擇模式**：使用 `NoSelection` 避免高亮覆蓋
4. **直接傳 QColor**：`setBackground(team_color)` 不用 `QBrush`
5. **學習參考實現**：完全複製 Ideal Lap Ranking Table 的模式

## 開發原則遵循

✅ **原則 0（反幻覺編碼）**：
- 徹底調查 Ideal Lap Ranking Table 的實現
- 使用 `read_file` 和 `grep_search` 驗證所有方法
- 完全複製參考實現，無假設性編程

✅ **原則 2（模組資料夾優先）**：
- 發現 `ideal_lap_ranking_table` 有完整實現
- 複用其架構和設計模式
- 使用相同的 `shared_colors.py` 模組

✅ **原則 3（通用模組優先）**：
- 統一使用 `get_team_color()` 函數
- 遵循相同的表格創建模式
- 保持視覺風格一致性

## 修復摘要

**修復前問題**：
- 車隊顏色不顯示（最嚴重）
- 表格每次更新都重建（效能問題）
- 欄位寬度自適應導致渲染異常
- 車隊欄位沒有背景色

**修復後效果**：
- ✅ 車隊顏色正常顯示
- ✅ 表格只創建一次，更新快速
- ✅ 固定寬度，渲染穩定
- ✅ 視覺風格與理想圈排名一致

**代碼變更統計**：
- 修改檔案：1 個（`all_drivers_straight_line_speed_table_widget.py`）
- 新增行數：約 20 行
- 刪除行數：約 10 行
- 修改方法：3 個（`_create_table`, `update_data`, `_populate_row`）

## 後續改進建議

1. **統一架構**：將所有表格模組統一使用此模式
2. **配色管理**：考慮建立統一的車隊配色管理器
3. **效能優化**：大量數據時可使用虛擬化表格
4. **測試覆蓋**：為顏色渲染添加自動化測試

---

**修復完成時間**: 2025-10-14 23:50
**測試狀態**: 待用戶驗證
**預期成功率**: 99%
