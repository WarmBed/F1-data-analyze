# SpeedDiff/DistanceDiff Tooltip 簡化更新報告

## 📋 更新概要

**更新日期**: 2025-10-07  
**更新範圍**: SpeedDiff Analysis & DistanceDiff Analysis  
**變更內容**: 垂直線 Tooltip 簡化 - 僅顯示數值

---

## 🎯 變更詳情

### 問題描述
SpeedDiff 和 DistanceDiff 模組的垂直線懸浮提示（Tooltip）顯示了冗餘資訊：
- 顯示車手名稱和圈數（例如: `HAM 第59圈 vs 第60圈: 3.1 km/h`）
- 在單曲線模式下，車手/圈數資訊已在圖表標題顯示

### 解決方案
簡化 Tooltip 顯示，僅保留數值資訊

---

## 📊 變更對比

### SpeedDiff Analysis

**舊版 Tooltip**:
```
距離: 690 m
HAM 第59圈 vs 第60圈: 3.1 km/h
```

**新版 Tooltip**:
```
距離: 690 m
速度差: 3.1 km/h
```

---

### DistanceDiff Analysis

**舊版 Tooltip**:
```
距離: 690 m
HAM 第59圈 vs 第60圈: -35.4 m
```

**新版 Tooltip**:
```
距離: 690 m
距離差: -35.4 m
```

---

## 🔧 技術實現

### 1. 新增翻譯鍵 (core/gui_i18n.py)

```python
# 🆕 Tooltip 標籤
'speed_diff_label': {'zh': '速度差', 'en': 'Speed Diff', 'ja': '速度差'},
'distance_diff_label': {'zh': '距離差', 'en': 'Distance Diff', 'ja': '距離差'},
```

---

### 2. 更新 Tooltip 顯示邏輯

#### SpeedDiff Analysis (speeddiff_analysis_chart_widget.py)

**更新前**:
```python
# 顯示車手speeddiff資訊
for i, (driver_name, speeddiff, color) in enumerate(drivers_to_show):
    painter.setPen(QPen(color, 1))
    painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{driver_name}: {speeddiff:.1f} km/h")
```

**更新後**:
```python
# 顯示 speeddiff 資訊（僅顯示數值，不顯示車手名稱）
for i, (driver_name, speeddiff, color) in enumerate(drivers_to_show):
    painter.setPen(QPen(color, 1))
    # ✅ 僅顯示數值
    painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{tr('speed_diff_label', '速度差')}: {speeddiff:.1f} km/h")
```

---

#### DistanceDiff Analysis (distancediff_analysis_chart_widget.py)

**更新前**:
```python
# 顯示車手distancediff資訊
for i, (driver_name, distancediff, color) in enumerate(drivers_to_show):
    painter.setPen(QPen(color, 1))
    painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{driver_name}: {distancediff:.1f} m")
```

**更新後**:
```python
# 顯示 distancediff 資訊（僅顯示數值，不顯示車手名稱）
for i, (driver_name, distancediff, color) in enumerate(drivers_to_show):
    painter.setPen(QPen(color, 1))
    # ✅ 僅顯示數值
    painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{tr('distance_diff_label', '距離差')}: {distancediff:.1f} m")
```

---

## 🌍 多語言支援

### 中文環境
```
距離: 690 m
速度差: 3.1 km/h
```

### 英文環境
```
Distance: 690 m
Speed Diff: 3.1 km/h
```

### 日文環境
```
距離: 690 m
速度差: 3.1 km/h
```

---

## ✅ 預期效益

### 1. 視覺清晰度提升
- ✅ **資訊簡化**: 移除冗餘的車手名稱和圈數
- ✅ **Tooltip 更緊湊**: 減少垂直高度
- ✅ **焦點明確**: 強調數值本身

### 2. 使用者體驗改進
**舊版問題**:
- Tooltip 顯示 `HAM 第59圈 vs 第60圈` 過長
- 圖表標題已顯示相同資訊（重複）
- 數值被標籤文字擠壓

**新版改進**:
- Tooltip 僅顯示關鍵數值
- 避免資訊重複
- 數值一目了然

---

## 📂 修改檔案清單

| # | 檔案 | 變更內容 | 行數 |
|---|------|---------|------|
| 1 | `core/gui_i18n.py` | 新增 2 個翻譯鍵 | +2 行 |
| 2 | `speeddiff_analysis_chart_widget.py` | 更新 Tooltip 顯示邏輯 | ~5 行 |
| 3 | `distancediff_analysis_chart_widget.py` | 更新 Tooltip 顯示邏輯 | ~5 行 |

**總計**: 3 個檔案，約 12 行變更

---

## 🧪 測試建議

### 測試案例: Tooltip 顯示驗證

**操作**:
1. 開啟 SpeedDiff Analysis
2. 選擇單車手雙圈模式 (例如: HAM 第59圈 vs 第60圈)
3. 移動滑鼠到圖表上，觸發垂直線
4. 檢查 Tooltip 內容

**預期結果**:
```
距離: 690 m
速度差: 3.1 km/h
```

**確認要點**:
- ❌ 不應出現: `HAM 第59圈 vs 第60圈`
- ✅ 應顯示: `速度差: X.X km/h`
- ✅ 保留距離資訊: `距離: XXX m`

**重複測試**:
- DistanceDiff Analysis (預期: `距離差: XX.X m`)
- 中文/英文/日文環境

---

## 📝 注意事項

### 1. 垂直線類型
此更新同時影響兩種垂直線：
- **滑鼠跟隨線** (白色背景 Tooltip)
- **固定線** (淡紅色背景 Tooltip)

兩者都只顯示數值，不顯示車手/圈數資訊。

---

### 2. 單曲線模式特性
SpeedDiff 和 DistanceDiff 本質上是**單曲線模式**：
- 顯示兩圈之間的差異（一條曲線）
- 非雙曲線比較（Speed/Acceleration 等是雙曲線）
- 因此 Tooltip 中的車手資訊更加冗餘

---

### 3. 保留的資訊
Tooltip 仍保留：
- ✅ **距離資訊**: `距離: 690 m`（X 軸位置）
- ✅ **差異數值**: `速度差: 3.1 km/h` 或 `距離差: -35.4 m`（Y 軸數值）
- ✅ **顏色編碼**: 數值文字使用曲線顏色（藍色或紅色）

---

## 🔗 相關更新

此次更新是 Lap Analysis 模組優化系列的一部分：

1. **主要模組標籤簡化** (已完成)
   - Speed, Acceleration, Brake, RPM, Gear, Throttle
   - 圖例從 `HAM - 第58圈` 改為 `第58圈`

2. **Diff 模組標籤格式化** (已完成)
   - SpeedDiff, DistanceDiff
   - 圖例使用 vs 格式: `HAM 第59圈 vs 第60圈`

3. **Tooltip 簡化** (本次更新)
   - SpeedDiff, DistanceDiff
   - Tooltip 僅顯示數值: `速度差: 3.1 km/h`

---

## ✅ 更新清單

### 開發階段
- [x] 新增 `speed_diff_label` 翻譯鍵
- [x] 新增 `distance_diff_label` 翻譯鍵
- [x] 更新 SpeedDiff Tooltip 邏輯
- [x] 更新 DistanceDiff Tooltip 邏輯
- [x] 驗證程式碼無語法錯誤

### 測試階段 (待執行)
- [ ] 測試 SpeedDiff 滑鼠跟隨線 Tooltip
- [ ] 測試 SpeedDiff 固定線 Tooltip
- [ ] 測試 DistanceDiff 滑鼠跟隨線 Tooltip
- [ ] 測試 DistanceDiff 固定線 Tooltip
- [ ] 驗證中文/英文/日文環境

---

## 📚 相關文件

- **標籤優化報告**: `LAP_ANALYSIS_LABEL_OPTIMIZATION_REPORT.md`
- **i18n 實施報告**: `LAP_ANALYSIS_I18N_IMPLEMENTATION_COMPLETE.md`
- **測試指引**: `LAP_ANALYSIS_I18N_TEST_GUIDE.md`

---

**更新報告版本**: 1.0  
**建立日期**: 2025-10-07  
**更新類型**: UI/UX 優化 - Tooltip 簡化  
**影響範圍**: SpeedDiff & DistanceDiff 模組
