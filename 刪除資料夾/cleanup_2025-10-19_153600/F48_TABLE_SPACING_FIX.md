# F48 棒狀圖與文字間距修正報告

## 問題分析

### 原始問題
- 文字位置跟隨棒狀圖長度：`text_x = base_x + speed_max_pos + text_margin`
- 當棒狀圖最長時，文字會超出預留空間，導致重疊或超出邊界

### Sector Comparison 的正確做法
```python
bar_max_width = option.rect.width() - 100  # 預留100像素文字空間
# ... 棒狀圖最大寬度受限於 bar_max_width ...
text_x = int(option.rect.x() + bar_width + 10)
```

**關鍵策略：**
1. 預留固定文字空間（100px）
2. 棒狀圖使用剩餘空間
3. 文字位置跟隨棒狀圖結尾（bar_width ≤ bar_max_width）

## 修正方案

### 1. 簡化空間計算
**修改前：**
```python
text_label_width = 110
left_margin = 10
text_margin = 15
bar_max_width = total_width - left_margin - text_label_width - text_margin
```

**修改後：**
```python
text_reserved_width = 100  # 固定預留（與 sector comparison 一致）
left_margin = 10
text_margin = 10
bar_max_width = total_width - left_margin - text_reserved_width
```

### 2. 確保棒狀圖不超出限制
**修改前：**
```python
speed_max_pos = bar_max_width * relative_ratio  # 可能 = bar_max_width
```

**修改後：**
```python
speed_max_pos = min(bar_max_width * relative_ratio, bar_max_width)  # 強制限制
```

### 3. 使用固定文字位置
**修改前：**
```python
text_x = int(base_x + speed_max_pos + text_margin)  # 跟隨棒狀圖
```

**修改後：**
```python
text_x = int(base_x + bar_max_width + text_margin)  # 固定位置
```

## 修正效果

### 視覺佈局
```
┌────────────────────────────────────────────────────────────────┐
│  [棒狀圖區域 - 最大寬度固定]      [文字區域 - 100px 固定]     │
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░              20.120s                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░          21.600s                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░       24.040s                        │
│  └─ 實心 ──┘└─ 延伸 ─┘         └─ 固定位置 ─┘                 │
└────────────────────────────────────────────────────────────────┘
```

### 修正前後對比
| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| 文字預留空間 | 110px + 15px = 125px（變動） | 100px（固定） |
| 棒狀圖最大寬度 | 可能超出 | 強制限制 |
| 文字位置 | 跟隨棒狀圖（變動） | 固定位置 |
| 重疊問題 | 最慢車手會重疊 ✗ | 永不重疊 ✓ |

## 測試方法

執行測試腳本：
```powershell
python test_f48_table_spacing.py
```

檢查重點：
1. ✅ 所有車手的文字都在同一垂直線上（固定位置）
2. ✅ 最慢車手（STR, 24.040s）的文字不會超出邊界
3. ✅ 最快車手（LEC, 20.120s）的文字與棒狀圖保持間距
4. ✅ 棒狀圖長度正確反映相對時間差異

## 參考實現

- **Sector Comparison**: `modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_table_widget.py`
- **修正後的 All Drivers Speed**: `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`

## 結論

採用 Sector Comparison 的固定文字預留策略，解決了棒狀圖與文字重疊問題。
關鍵是**文字使用固定位置，而不是跟隨棒狀圖長度**。
