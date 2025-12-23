# Lap Analysis 圈數標籤顯示優化報告

## 📋 更新概要

**更新日期**: 2025-10-07  
**更新範圍**: 8 個 Lap Analysis Chart Widget 模組  
**主要變更**: 
1. 單車手雙圈模式改為僅顯示圈數（不含車手代碼）
2. SpeedDiff/DistanceDiff 模組使用 vs 格式標籤

---

## 🎯 變更詳情

### 變更 1: 單車手雙圈模式標籤簡化

**影響模組**: Speed, Acceleration, Brake, RPM, Gear, Throttle (6 個)

**舊版顯示**:
```
🔵 HAM - 第58圈
🔴 HAM - 第60圈
```

**新版顯示**:
```
🔵 第58圈 (Lap 58 in English / 58周目 in Japanese)
🔴 第60圈 (Lap 60 in English / 60周目 in Japanese)
```

**設計理由**:
- 單車手模式下，車手代碼是冗餘資訊
- 圖表標題已顯示車手名稱
- 簡化標籤使圖例更清晰

---

### 變更 2: SpeedDiff/DistanceDiff 模組的 vs 格式

**影響模組**: SpeedDiff, DistanceDiff (2 個)

**標籤格式**:
```
中文: HAM 第59圈 vs 第60圈
英文: HAM Lap 59 vs Lap 60
日文: HAM 59周目 vs 60周目
```

**特殊性說明**:
- 這兩個模組顯示的是**速度差/距離差曲線**（單一曲線）
- 非雙曲線比較，因此使用單一標籤描述兩圈之間的差異
- 標籤需包含車手代碼以識別比較對象

---

## 🔧 技術實現

### 1. 新增翻譯鍵 (core/gui_i18n.py)

```python
# 🆕 單車手雙圈模式 - 僅顯示圈數（不含車手代碼）
'lap_only_format': {
    'zh': '第{lap}圈',
    'en': 'Lap {lap}',
    'ja': '{lap}周目'
},

# 🆕 SpeedDiff/DistanceDiff 專用 - vs 格式（單行標籤）
'lap_vs_lap_format': {
    'zh': '{driver} 第{lap1}圈 vs 第{lap2}圈',
    'en': '{driver} Lap {lap1} vs Lap {lap2}',
    'ja': '{driver} {lap1}周目 vs {lap2}周目'
},
```

---

### 2. 更新模組邏輯

#### A. 主要模組 (Speed, Acceleration, Brake, RPM, Gear, Throttle)

**更新前**:
```python
lap_format = tr('lap_label_format', '{driver} - 第{lap}圈')
driver1_name = lap_format.format(driver=original_driver, lap=lap1)
driver2_name = lap_format.format(driver=original_driver, lap=lap2)
```

**更新後**:
```python
lap_format = tr('lap_only_format', '第{lap}圈')
driver1_name = lap_format.format(lap=lap1)
driver2_name = lap_format.format(lap=lap2)
print(f"[MODULE_CHART] 🔄 雙圈比較模式: {original_driver} {driver1_name} vs {driver2_name}")
```

**Console 輸出範例**:
```
[SPEED_CHART] 🔄 雙圈比較模式: HAM 第58圈 vs 第60圈
[BRAKE_CHART] 🔄 雙圈比較模式: VER Lap 10 vs Lap 12
```

---

#### B. SpeedDiff/DistanceDiff 模組

**更新前**:
```python
original_driver = driver_codes[0]
driver1_name = f"{original_driver} 第{lap1}圈 vs 第{lap2}圈"
print(f"[SPEEDDIFF_CHART] 🔄 雙圈比較模式: {driver1_name}")
```

**更新後**:
```python
original_driver = driver_codes[0]
lap_vs_format = tr('lap_vs_lap_format', '{driver} 第{lap1}圈 vs 第{lap2}圈')
driver1_name = lap_vs_format.format(driver=original_driver, lap1=lap1, lap2=lap2)
print(f"[SPEEDDIFF_CHART] 🔄 雙圈比較模式: {driver1_name}")
```

---

## 📊 修改檔案清單

| # | 檔案 | 變更類型 | 行數 |
|---|------|---------|------|
| 1 | `core/gui_i18n.py` | 新增翻譯鍵 | +6 行 |
| 2 | `speed_analysis_chart_widget.py` | 標籤邏輯更新 | ~10 行 |
| 3 | `acceleration_analysis_chart_widget.py` | 標籤邏輯更新 | ~10 行 |
| 4 | `brake_analysis_chart_widget.py` | 標籤邏輯更新 | ~10 行 |
| 5 | `rpm_analysis_chart_widget.py` | 標籤邏輯更新 | ~10 行 |
| 6 | `gear_analysis_chart_widget.py` | 標籤邏輯更新 | ~10 行 |
| 7 | `throttle_analysis_chart_widget.py` | 標籤邏輯更新 | ~10 行 |
| 8 | `speeddiff_analysis_chart_widget.py` | vs 格式標籤 | ~10 行 |
| 9 | `distancediff_analysis_chart_widget.py` | vs 格式標籤 | ~10 行 |

**總計**: 9 個檔案，約 76 行變更

---

## 🌍 多語言展示

### 主要模組 (Speed, Acceleration, Brake, RPM, Gear, Throttle)

| 語言 | 標籤 1 | 標籤 2 | Console 輸出 |
|------|--------|--------|--------------|
| 中文 (zh) | 第58圈 | 第60圈 | HAM 第58圈 vs 第60圈 |
| 英文 (en) | Lap 58 | Lap 60 | HAM Lap 58 vs Lap 60 |
| 日文 (ja) | 58周目 | 60周目 | HAM 58周目 vs 60周目 |

### SpeedDiff/DistanceDiff 模組

| 語言 | 單一標籤顯示 |
|------|-------------|
| 中文 (zh) | HAM 第59圈 vs 第60圈 |
| 英文 (en) | HAM Lap 59 vs Lap 60 |
| 日文 (ja) | HAM 59周目 vs 60周目 |

---

## 🧪 測試建議

### 測試案例 1: 主要模組雙圈比較

**操作**:
1. 開啟任一主要模組 (例如: Speed Analysis)
2. 選擇單車手 (例如: HAM)
3. 選擇兩個不同圈數 (例如: 第58圈 vs 第60圈)

**預期結果**:
- 圖表圖例顯示: `第58圈` 和 `第60圈`（不含 "HAM -"）
- Console 輸出: `[SPEED_CHART] 🔄 雙圈比較模式: HAM 第58圈 vs 第60圈`

**驗證語言**:
- 中文環境: 第58圈
- 英文環境: Lap 58
- 日文環境: 58周目

---

### 測試案例 2: SpeedDiff/DistanceDiff 模組

**操作**:
1. 開啟 SpeedDiff Analysis
2. 選擇單車手 (例如: HAM)
3. 選擇兩個不同圈數 (例如: 第59圈 vs 第60圈)

**預期結果**:
- 圖表圖例顯示單一標籤: `HAM 第59圈 vs 第60圈`
- Console 輸出: `[SPEEDDIFF_CHART] 🔄 雙圈比較模式: HAM 第59圈 vs 第60圈`

**驗證語言**:
- 中文環境: HAM 第59圈 vs 第60圈
- 英文環境: HAM Lap 59 vs Lap 60
- 日文環境: HAM 59周目 vs 60周目

---

### 測試案例 3: 雙車手模式（確認無迴歸）

**操作**:
1. 開啟任一模組
2. 選擇兩個不同車手 (例如: VER vs HAM)
3. 相同圈數 (例如: 第58圈)

**預期結果**:
- 圖表圖例顯示: `VER` 和 `HAM`（僅車手代碼）
- 不應出現圈數標籤

---

## ✅ 預期效益

### 1. 使用者體驗改進
- ✅ **標籤簡化**: 移除冗餘的車手代碼，圖例更清晰
- ✅ **一致性**: 所有模組的標籤格式統一
- ✅ **國際化**: 支援中文/英文/日文環境

### 2. 視覺清晰度
**舊版**:
```
圖例:
🔵 HAM - 第58圈  (較長，可能被截斷)
🔴 HAM - 第60圈
```

**新版**:
```
圖例:
🔵 第58圈  (簡潔明瞭)
🔴 第60圈
```

### 3. 語言適應性
| 語言 | 字元節省 | 範例 |
|------|---------|------|
| 中文 | 節省 6 字元 | ~~HAM - 第58圈~~ → 第58圈 |
| 英文 | 節省 7 字元 | ~~HAM - Lap 58~~ → Lap 58 |
| 日文 | 節省 6 字元 | ~~HAM - 58周目~~ → 58周目 |

---

## 🐞 已知問題與注意事項

### 1. SpeedDiff/DistanceDiff 的特殊處理

**原因**: 這兩個模組顯示的是**單一差異曲線**，而非雙曲線比較

**標籤邏輯**:
- 主要模組: 兩個獨立標籤 (`第58圈`, `第60圈`)
- Diff 模組: 單一組合標籤 (`HAM 第59圈 vs 第60圈`)

**驗證方法**:
```python
# 確認標籤格式
if "vs" in chart_label:
    # SpeedDiff/DistanceDiff 模組
    assert chart_label == "HAM 第59圈 vs 第60圈"
else:
    # 主要模組
    assert chart_label in ["第58圈", "第60圈"]
```

---

### 2. Console 輸出格式

**主要模組**:
```
[SPEED_CHART] 🔄 雙圈比較模式: HAM 第58圈 vs 第60圈
```

**Diff 模組**:
```
[SPEEDDIFF_CHART] 🔄 雙圈比較模式: HAM 第59圈 vs 第60圈
```

**注意**: Console 輸出仍包含完整資訊（車手代碼 + 圈數），僅圖表圖例簡化

---

### 3. 語言切換

**重要**: 語言切換後需重新載入圖表

**步驟**:
1. 修改 `core/gui_i18n.py` 的 `current_language`
2. 重啟 GUI 或關閉舊圖表
3. 重新執行分析

---

## 📝 更新清單

### 開發階段
- [x] `core/gui_i18n.py` 新增 `lap_only_format` 翻譯鍵
- [x] `core/gui_i18n.py` 新增 `lap_vs_lap_format` 翻譯鍵
- [x] 更新 6 個主要模組 (Speed, Accel, Brake, RPM, Gear, Throttle)
- [x] 更新 2 個 Diff 模組 (SpeedDiff, DistanceDiff)
- [x] 驗證程式碼無語法錯誤

### 測試階段 (待執行)
- [ ] 測試主要模組單車手雙圈模式
- [ ] 測試 SpeedDiff/DistanceDiff 的 vs 格式
- [ ] 測試雙車手模式無迴歸
- [ ] 驗證中文/英文/日文環境
- [ ] 確認 Console 輸出正確

### 文件階段
- [x] 建立更新報告 (本文件)
- [ ] 更新 `LAP_ANALYSIS_I18N_TEST_GUIDE.md`
- [ ] 更新 `LAP_ANALYSIS_I18N_QUICKREF.md`

---

## 🔗 相關文件

- **原始實施報告**: `LAP_ANALYSIS_I18N_IMPLEMENTATION_COMPLETE.md`
- **測試指引**: `LAP_ANALYSIS_I18N_TEST_GUIDE.md`
- **快速參考**: `LAP_ANALYSIS_I18N_QUICKREF.md`

---

## 📧 問題回報

如發現標籤顯示異常，請提供:
1. 模組名稱 (例如: Speed Analysis)
2. 測試模式 (單車手雙圈 / 雙車手單圈)
3. 預期標籤 vs 實際標籤
4. 語言環境 (zh/en/ja)
5. 截圖

---

**更新報告版本**: 1.0  
**建立日期**: 2025-10-07  
**更新類型**: 功能優化 + 國際化增強  
**影響範圍**: 8 個 Lap Analysis 模組 + 核心翻譯系統
