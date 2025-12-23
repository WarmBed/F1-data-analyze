# 🔧 Throttle Line Chart - Flag Markers & Filter 修復報告

## 📅 日期
2025-10-08

## 🎯 問題描述

用戶報告 Throttle Line Chart 模組存在兩個問題：

1. **P 標記未顯示**：即使有進站資料，X 軸上也沒有橘色的 'P' 標記
2. **Filter 功能異常**：在 System Settings 中取消勾選過濾選項後，仍然看不到標記

## 🔍 根本原因分析

### 問題 1：Flag 標記邏輯順序錯誤 ❌

**錯誤的執行順序** (`throttle_line_chart_data_loader.py` Line 147-152)：

```python
# ❌ 錯誤流程
lap_records, filter_stats = self._apply_filters(lap_records, target)  # 1️⃣ 先過濾（移除進站圈）
chart_series = self._build_chart_series(lap_records)                   # 2️⃣ 只用過濾後的資料
helper_sets = self._extract_flag_sets(lap_records)                     # 3️⃣ 從過濾後資料提取標記 ❌
stint_ranges = self._build_stint_segments(lap_records)
```

**問題所在**：
- 如果 `filter_pit_laps = True`（預設值），`_apply_filters()` 會移除所有進站圈
- `_extract_flag_sets()` 只處理過濾後的 `lap_records`
- **結果**：進站圈已經不在資料中，無法生成 'P' 標記！

### 問題 2：標記顯示與資料過濾混淆

**設計缺陷**：
- **標記應該顯示所有事件**（P/Y/S/R），告知用戶哪些圈發生了特殊情況
- **資料點過濾**是用於統計分析，移除異常值

但當前實現將兩者混為一談：
- 過濾進站圈 → P 標記也消失
- 過濾黃旗圈 → Y 標記也消失

這違反了用戶期望：**標記是資訊指示器，不應因過濾而消失**。

---

## ✅ 修復方案

### 修復 1：調整執行順序

**正確的流程** (`throttle_line_chart_data_loader.py` Line 147-156)：

```python
# ✅ 正確流程
lap_records = self._process_lap_records(target.get("laps") or [])
lap_records.sort(key=lambda item: item["lap_number"])

# 🔧 FIX: 先提取標記（從原始資料），再進行過濾
# 這樣即使啟用 filter_pit_laps，P 標記仍會顯示在 X 軸上
helper_sets = self._extract_flag_sets(lap_records)      # 1️⃣ 先提取標記（完整資料）✅
stint_ranges = self._build_stint_segments(lap_records)

# 然後才過濾資料點（用於圖表繪製）
lap_records, filter_stats = self._apply_filters(lap_records, target)  # 2️⃣ 再過濾

chart_series = self._build_chart_series(lap_records)     # 3️⃣ 使用過濾後的資料繪圖
```

**效果**：
- ✅ 標記從**完整的原始資料**生成，包含所有 P/Y/S/R 旗標
- ✅ 圖表數據點使用**過濾後的資料**，符合統計需求
- ✅ 用戶可以看到 "Lap 20 有 P 標記但沒有數據點"（因為進站圈被過濾）

---

### 修復 2：添加調試輸出

為了追蹤過濾設定的同步狀態，添加了詳細的調試日誌：

**1. 過濾狀態追蹤** (`_apply_filters()`)：
```python
self._debug(f"🔧 [Filter Status] filter_pit_laps={self._filter_pit_laps}, filter_yellow_flags={self._filter_yellow_flags}")
self._debug(f"🔍 [Filter Stats] {stats}")
```

**2. 標記生成追蹤** (`_extract_flag_sets()`)：
```python
self._debug(f"🏁 [Flag Markers] pit_laps={sorted(pit_laps)}, flag_labels={flag_labels}")
```

**3. 設定更新追蹤** (`update_filter_settings()`)：
```python
self._debug(f"⚙️ [Settings] filter_pit_laps changed: {old} → {new}")
self._debug(f"🔄 [Reprocess] Rebuilding data with new filter settings...")
```

**4. 全域設定變更追蹤** (`_on_global_filter_settings_changed()`)：
```python
print(f"🌐 [Global Settings Changed] Received: {settings}")
print(f"🌐 [Global Settings Updated] New state: pit={...}, yellow={...}")
```

---

## 🧪 驗證步驟

### 步驟 1：啟動 GUI 並打開 Throttle Line Chart
```powershell
python f1t_gui_main.py
```

### 步驟 2：載入有進站資料的賽事
- 年份：2025
- 賽事：Singapore
- 會話：R (正賽)
- 車手：VER

### 步驟 3：觀察控制台輸出

**預期看到的調試訊息**：
```
🔧 [Filter Status] filter_pit_laps=True, filter_yellow_flags=True
🏁 [Flag Markers] pit_laps=[20, 35], flag_labels={20: 'P', 35: 'P', 15: 'Y'}
🔍 [Filter Stats] {'filter_pit_laps': True, 'removed_pit_laps': 2, ...}
```

### 步驟 4：測試 System Settings 同步

1. 打開 `Tools → System Settings`
2. **取消勾選** "Filter pit laps"
3. 點擊 OK

**預期控制台輸出**：
```
🌐 [Global Settings Changed] Received: {'filter_pit_laps': False, 'filter_yellow_flags': True, ...}
🌐 [Global Settings Updated] New state: pit=False, yellow=True
⚙️ [Settings] filter_pit_laps changed: True → False
🔄 [Reprocess] Rebuilding data with new filter settings...
🔧 [Filter Status] filter_pit_laps=False, filter_yellow_flags=True
🔍 [Filter Stats] {'filter_pit_laps': False, 'removed_pit_laps': 0, ...}
```

### 步驟 5：視覺驗證

**圖表上應該看到**：
- ✅ X 軸底部有橘色 'P' 標記（在進站圈位置）
- ✅ 如果 `filter_pit_laps=True`：P 標記存在，但該圈沒有數據點
- ✅ 如果 `filter_pit_laps=False`：P 標記存在，且該圈有完整數據點

---

## 📊 修復影響範圍

### 修改的檔案

1. **`throttle_line_chart_data_loader.py`** (主要修復)
   - Line 147-156: 調整執行順序（先提取標記，再過濾）
   - Line 202-236: 添加過濾狀態調試輸出
   - Line 370-405: 添加標記生成調試輸出
   - Line 534-570: 添加設定更新調試輸出

2. **`throttle_line_chart_mdi.py`** (調試輸出)
   - Line 819-839: 添加全域設定變更調試輸出

### 不影響的功能

- ✅ Box Plot 模組（使用不同的資料載入器）
- ✅ 其他分析模組
- ✅ API 服務器
- ✅ CLI 後端功能

---

## 🎯 預期效果

### Before（修復前）❌
```
啟用 filter_pit_laps=True:
  - 進站圈被移除
  - _extract_flag_sets() 看不到進站圈
  - 結果：沒有 P 標記

取消勾選 Filter pit laps:
  - 設定可能未正確同步
  - 或者標記已經在過濾時遺失
  - 結果：仍然沒有 P 標記
```

### After（修復後）✅
```
啟用 filter_pit_laps=True:
  - 標記先從原始資料提取（包含 P）
  - 然後才過濾進站圈（用於圖表繪製）
  - 結果：X 軸有 P 標記，但該圈沒有數據點 ✅

取消勾選 Filter pit laps (filter_pit_laps=False):
  - 標記從原始資料提取（包含 P）
  - 不過濾任何圈速
  - 結果：X 軸有 P 標記，且該圈有完整數據點 ✅
```

---

## 💡 設計理念

### 標記 (Flag Markers) 的用途
- **資訊指示器**：告訴用戶哪些圈發生了特殊事件
- **永遠顯示**：不應因為統計過濾而消失
- **視覺提示**：幫助用戶理解為什麼某些圈沒有數據點

### 過濾 (Filter) 的用途
- **統計分析**：移除異常值以獲得更準確的趨勢
- **可選功能**：用戶可以自由開關
- **不影響標記**：過濾只影響數據點，不影響標記顯示

### 正確的邏輯
```
原始資料 (60 laps)
    ↓
提取標記: {20: 'P', 35: 'P', 15: 'Y'} ← 包含所有事件
    ↓
應用過濾: 移除 Lap 20, 35 (進站圈)
    ↓
圖表繪製: 58 個數據點
    ↓
視覺呈現:
  - 圖表顯示 58 個點
  - X 軸底部顯示 P (Lap 20, 35) 和 Y (Lap 15) 標記 ✅
```

---

## ✅ 完成檢查清單

- [x] 調整 `_extract_flag_sets()` 執行順序（在過濾之前）
- [x] 添加過濾狀態調試輸出
- [x] 添加標記生成調試輸出
- [x] 添加設定更新調試輸出
- [x] 添加全域設定變更調試輸出
- [x] 創建修復報告文檔
- [ ] 用戶測試驗證（等待用戶確認）
- [ ] 移除調試輸出（確認修復後）

---

## 📝 後續建議

### 1. 測試完成後清理調試輸出

修復確認後，可以移除或注釋掉調試 print 語句：
```python
# self._debug(f"🔧 [Filter Status] ...")  # 測試完成後可移除
```

### 2. 考慮添加圖例說明

在圖表中添加標記圖例，說明各顏色的含義：
- 🟠 P = Pitstop（進站）
- 🟡 Y = Yellow Flag（黃旗）
- 🔵 S = Safety Car（安全車）
- 🔴 R = Red Flag（紅旗）

### 3. 優化 System Settings 提示

在對話框中添加說明文字：
```
"過濾選項只影響圖表數據點，不影響旗標標記的顯示"
```

---

## 🎓 學習重點

這個 Bug 展示了一個重要的軟體設計原則：

**分離資訊顯示與資料處理邏輯**

- **資訊層**（標記）：應該反映客觀事實，不受用戶設定影響
- **處理層**（過濾）：根據用戶需求調整分析結果

當這兩層混淆時，就會出現 "過濾掉資訊指示器" 的反直覺行為。

---

**修復作者**：GitHub Copilot  
**測試狀態**：等待用戶驗證  
**預計完成**：2025-10-08
