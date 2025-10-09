# 🧪 測試計劃：圈數精確匹配修復驗證

**測試對象**: Lap Analysis 圈數精確匹配功能  
**修復版本**: 2025-10-07  
**測試目標**: 驗證移除萬用字元模式後，系統只載入精確匹配的圈數數據  
**相關文件**: `FIX_REPORT_Lap_Number_Exact_Match.md`

---

## 📋 測試環境準備

### 1. 測試數據檔案準備

**目錄**: `d:\OneDrive\Code\F1-data-analyze\json\`

**需要的測試檔案**:
```
✅ comparison_telemetry_LEC_LEC_2025_Australia_R_Lap10_Lap50.json
✅ comparison_telemetry_LEC_LEC_2025_Australia_R_Lap15_Lap52.json
✅ comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap53.json
❌ comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json (不存在，測試用)
```

**檢查命令**:
```powershell
Get-ChildItem -Path "d:\OneDrive\Code\F1-data-analyze\json\" -Filter "comparison_telemetry_LEC_LEC_2025_Australia_R_Lap*.json" | Select-Object Name, LastWriteTime
```

### 2. 啟動 F1T GUI

```powershell
python f1t_gui_main.py
```

### 3. 開啟調試模式

在 `modules/gui/lap_analysis/telemetry_data_loader_base.py` 中：
```python
self._debug_enabled = True  # 確保設為 True
```

---

## 🎯 測試案例

### 測試案例 1: 精確匹配 - 檔案存在（單圈模式）

**測試步驟**:
1. 打開 F1T GUI → Lap Analysis
2. 設定參數：
   - Year: 2025
   - Race: Australia
   - Session: R
   - Driver 1: LEC
   - Lap 1: 17
   - Driver 2: LEC
   - Lap 2: 53
3. 點擊 "Update All Analysis"

**預期結果**:
```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 🏎️ 同車手檔案搜尋模式（精確匹配）:
[DEBUG]    1. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json
[DEBUG]    2. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap53.json
[DEBUG]    🔍 模式 1: ...Lap17.json
[DEBUG]    ❌ 模式 1 無匹配
[DEBUG]    🔍 模式 2: ...Lap17_Lap53.json
[DEBUG]    ✅ 找到檔案: Lap17_Lap53.json
[SUCCESS] ✅ 載入成功: Lap17_Lap53.json
```

**驗證點**:
- ✅ 載入的是 `Lap17_Lap53.json`
- ✅ 圖表顯示 "LEC - 第17圈" vs "LEC - 第53圈"
- ✅ 遙測數據對應 Lap17 和 Lap53
- ❌ 沒有載入其他圈數的檔案（如 Lap15_Lap52）

**測試狀態**: ⬜ 未測試 / ✅ 通過 / ❌ 失敗

---

### 測試案例 2: 精確匹配 - 檔案不存在（應觸發錯誤或 API）

**測試步驟**:
1. 打開 F1T GUI → Lap Analysis
2. 設定參數：
   - Year: 2025
   - Race: Australia
   - Session: R
   - Driver 1: LEC
   - Lap 1: 17
   - Driver 2: LEC
   - Lap 2: 52
3. 點擊 "Update All Analysis"

**預期結果**:
```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 🏎️ 同車手檔案搜尋模式（精確匹配）:
[DEBUG]    1. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json
[DEBUG]    2. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json
[DEBUG]    🔍 模式 1: ...Lap17.json
[DEBUG]    ❌ 模式 1 無匹配
[DEBUG]    🔍 模式 2: ...Lap17_Lap52.json
[DEBUG]    ❌ 模式 2 無匹配
[ERROR] ⚠️ 找不到精確匹配的檔案
[INFO] 💡 提示: 請使用 API 獲取數據或手動執行 CLI
```

**驗證點**:
- ✅ 顯示錯誤訊息（找不到檔案）
- ✅ 沒有載入其他圈數的檔案（如 Lap15_Lap52）
- ✅ （可選）提示用戶通過 API 生成數據
- ✅ （可選）自動觸發 API 請求生成 Lap17_Lap52.json

**測試狀態**: ⬜ 未測試 / ✅ 通過 / ❌ 失敗

---

### 測試案例 3: 雙車手模式 - 精確匹配

**測試步驟**:
1. 打開 F1T GUI → Lap Analysis
2. 設定參數：
   - Year: 2025
   - Race: Australia
   - Session: R
   - Driver 1: VER
   - Lap 1: 10
   - Driver 2: LEC
   - Lap 2: 15
3. 點擊 "Update All Analysis"

**預期結果**:
```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 🔄 雙車手檔案搜尋模式（精確匹配）:
[DEBUG]    1. comparison_telemetry_VER_LEC_2025_Australia_R_Lap10_Lap15.json
[DEBUG]    🔍 模式 1: ...Lap10_Lap15.json
[DEBUG]    ✅ 找到檔案: Lap10_Lap15.json
[SUCCESS] ✅ 載入成功
```

**驗證點**:
- ✅ 搜尋模式只有 1 個（雙車手精確匹配）
- ✅ 載入的是 `VER_LEC_Lap10_Lap15.json`
- ✅ 沒有萬用字元回退模式
- ✅ 圖表顯示 VER vs LEC 的對比

**測試狀態**: ⬜ 未測試 / ✅ 通過 / ❌ 失敗

---

### 測試案例 4: 同圈數模式（Lap17 vs Lap17）

**測試步驟**:
1. 打開 F1T GUI → Lap Analysis
2. 設定參數：
   - Year: 2025
   - Race: Australia
   - Session: R
   - Driver 1: LEC
   - Lap 1: 17
   - Driver 2: LEC
   - Lap 2: 17
3. 點擊 "Update All Analysis"

**預期結果**:
```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 🏎️ 同車手檔案搜尋模式（精確匹配）:
[DEBUG]    1. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json
[DEBUG]    2. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap17.json
[DEBUG]    🔍 模式 1: ...Lap17.json
[DEBUG]    ✅ 找到檔案: Lap17.json
[SUCCESS] ✅ 載入成功
```

**驗證點**:
- ✅ 載入單圈檔案 `Lap17.json`
- ✅ 圖表顯示單一遙測線（單車手單圈模式）
- ✅ 沒有載入雙圈檔案（如 Lap17_Lap53）

**測試狀態**: ⬜ 未測試 / ✅ 通過 / ❌ 失敗

---

### 測試案例 5: 防止萬用字元回退（修復前 BUG 重現測試）

**測試步驟**:
1. 打開 F1T GUI → Lap Analysis
2. 設定參數：
   - Year: 2025
   - Race: Australia
   - Session: R
   - Driver 1: LEC
   - Lap 1: 17
   - Driver 2: LEC
   - Lap 2: 52
3. **檢查檔案不存在**: `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json`
4. 點擊 "Update All Analysis"

**修復前的錯誤行為**:
```
[DEBUG] 🔍 模式 3: ...Lap*.json
[DEBUG] ✅ 找到檔案: Lap15_Lap52.json ❌ (錯誤！)
```

**修復後的正確行為**:
```
[DEBUG] 🔍 模式 1: ...Lap17.json
[DEBUG] ❌ 模式 1 無匹配
[DEBUG] 🔍 模式 2: ...Lap17_Lap52.json
[DEBUG] ❌ 模式 2 無匹配
[ERROR] ⚠️ 找不到精確匹配的檔案
```

**驗證點**:
- ✅ **絕對不會**載入 `Lap15_Lap52.json`
- ✅ **絕對不會**載入 `Lap17_Lap53.json`
- ✅ **絕對不會**載入 `Lap10_Lap50.json`
- ✅ 顯示錯誤訊息或觸發 API 生成

**測試狀態**: ⬜ 未測試 / ✅ 通過 / ❌ 失敗

---

### 測試案例 6: 雙圈比較模式（同車手不同圈）

**測試步驟**:
1. 打開 F1T GUI → Lap Analysis → Speed Analysis
2. 設定參數：
   - Year: 2025
   - Race: Australia
   - Session: R
   - Driver 1: LEC
   - Lap 1: 10
   - Driver 2: LEC
   - Lap 2: 50
3. 點擊 "Update All Analysis"

**預期結果**:
```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 🏎️ 同車手檔案搜尋模式（精確匹配）:
[DEBUG]    1. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap10.json
[DEBUG]    2. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap10_Lap50.json
[DEBUG]    🔍 模式 1: ...Lap10.json
[DEBUG]    ❌ 模式 1 無匹配
[DEBUG]    🔍 模式 2: ...Lap10_Lap50.json
[DEBUG]    ✅ 找到檔案: Lap10_Lap50.json
[SUCCESS] ✅ 載入成功
```

**驗證點**:
- ✅ 載入 `Lap10_Lap50.json`
- ✅ 圖表顯示兩條線：
  - "LEC - 第10圈" (紅色)
  - "LEC - 第50圈" (藍色)
- ✅ 雙圈比較模式正常運作
- ✅ 遙測數據正確對應兩個圈數

**測試狀態**: ⬜ 未測試 / ✅ 通過 / ❌ 失敗

---

## 🔍 調試檢查清單

### 搜尋模式驗證

**檢查點**: `telemetry_data_loader_base.py:493-519`

```python
# 同車手模式應該只有 2 個模式
if driver2_norm and driver2_norm != driver1_norm:
    filename_patterns = [
        f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
    ]
else:
    filename_patterns = [
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}.json",
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
    ]
```

**驗證**:
- ✅ 雙車手模式只有 **1** 個模式
- ✅ 同車手模式只有 **2** 個模式
- ❌ 沒有 `Lap*.json` 萬用字元
- ❌ 沒有 `Lap*_Lap*.json` 萬用字元

---

### 調試輸出驗證

**檢查終端輸出**應該包含：

```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 🏎️ 同車手檔案搜尋模式（精確匹配）:
[DEBUG]    1. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json
[DEBUG]    2. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json
[DEBUG]    🔍 模式 1: d:\OneDrive\Code\F1-data-analyze\json\comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json
[DEBUG]    ❌ 模式 1 無匹配
[DEBUG]    🔍 模式 2: d:\OneDrive\Code\F1-data-analyze\json\comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json
[DEBUG]    ❌ 模式 2 無匹配
```

**不應該出現**:
```
❌ [DEBUG]    🔍 模式 3: ...Lap*.json
❌ [DEBUG]    🔍 模式 4: ...Lap*_Lap*.json
```

---

## 📊 測試結果記錄

### 測試執行記錄表

| 測試案例 | 日期 | 測試者 | 結果 | 備註 |
|---------|------|--------|------|------|
| 案例 1: 精確匹配存在 | - | - | ⬜ | - |
| 案例 2: 精確匹配不存在 | - | - | ⬜ | - |
| 案例 3: 雙車手模式 | - | - | ⬜ | - |
| 案例 4: 同圈數模式 | - | - | ⬜ | - |
| 案例 5: 防止萬用字元回退 | - | - | ⬜ | - |
| 案例 6: 雙圈比較模式 | - | - | ⬜ | - |

**符號說明**:
- ⬜ 未測試
- ✅ 通過
- ❌ 失敗
- ⚠️ 部分通過

---

## 🐞 BUG 追蹤

### 發現的問題

| 問題 ID | 描述 | 嚴重性 | 狀態 |
|---------|------|--------|------|
| - | - | - | - |

---

## ✅ 驗收標準

### 必須通過的條件

1. ✅ **精確匹配優先**: 檔案存在時，只載入精確圈數匹配的檔案
2. ✅ **不使用萬用字元**: 任何情況下都不會使用 `Lap*.json` 模式
3. ✅ **檔案不存在處理**: 檔案不存在時，顯示錯誤或觸發 API 生成
4. ✅ **雙圈比較模式**: 同車手不同圈時，正確顯示兩條遙測線
5. ✅ **調試訊息正確**: 終端輸出顯示正確的搜尋模式（只有 1-2 個）
6. ✅ **無回歸 BUG**: 修復前的 BUG（載入錯誤圈數）不再發生

---

## 📝 測試報告模板

### 測試完成後填寫

**測試日期**: _____________  
**測試者**: _____________  
**測試環境**: Windows 11 / Python 3.x / PyQt5  
**F1T 版本**: 2025-10-07 修復版  

**測試結果**:
- 通過案例: _____ / 6
- 失敗案例: _____ / 6
- 跳過案例: _____ / 6

**總體評價**: ⬜ 通過 / ⬜ 失敗 / ⬜ 需要進一步測試

**問題記錄**: 
_____________________________________________

**建議**: 
_____________________________________________

---

## 🚀 下一步

測試通過後：
1. ✅ 標記 BUG 為已修復
2. ✅ 更新用戶文檔
3. ✅ 考慮添加批次預生成功能（可選）
4. ✅ 將修復方案應用到其他模組（Throttle, RPM, Brake 等）

測試失敗時：
1. ❌ 記錄失敗案例和錯誤訊息
2. ❌ 重新檢查修復代碼
3. ❌ 調整修復方案並重新測試

---

**測試計劃建立日期**: 2025-10-07  
**相關文件**: 
- `FIX_REPORT_Lap_Number_Exact_Match.md` - 修復報告
- `BUG_REPORT_Lap_Number_Mismatch.md` - BUG 診斷
- `IMPLEMENTATION_Dual_Lap_Comparison_Mode.md` - 雙圈比較模式實施

