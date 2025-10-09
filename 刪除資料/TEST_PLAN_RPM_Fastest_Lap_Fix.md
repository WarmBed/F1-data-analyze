# 🧪 測試計劃：RPM Fastest Lap 修復驗證

**測試日期**: 待執行  
**修復版本**: 2025-10-07  
**測試重點**: 確認 RPM 模組選擇 Fastest Lap 不再彈出 Pitstop/遙測分析視窗  
**預計時間**: 15 分鐘

---

## 🎯 測試目標

驗證以下修復是否成功：
1. ✅ RPM 模組選擇 Fastest Lap 不彈出視窗
2. ✅ 其他 7 個模組的 Fastest Lap 功能正常
3. ✅ API-ONLY 政策在所有模組中正確執行

---

## 📋 測試前準備

### 步驟 1: 重新打包 EXE
```powershell
# 清理舊檔案
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# 重新打包
pyinstaller F1T_GUI.spec --clean

# 確認生成成功
Test-Path "dist\F1T_GUI\F1T_GUI.exe"
```

### 步驟 2: 準備測試環境
```powershell
# 清理測試用的 JSON 緩存（模擬首次使用）
Remove-Item "json\telemetry_analysis_*.json" -ErrorAction SilentlyContinue

# 確認無遙測 JSON
Get-ChildItem "json\telemetry_analysis_*.json"
# 預期結果：應該找不到任何檔案
```

### 步驟 3: 準備測試數據
```powershell
# 方法 A: 使用 2025 Australian GP（如果有數據）
# 方法 B: 使用 2024 Japanese GP
# 方法 C: 任何已有 FastF1 緩存的賽事
```

---

## 🧪 測試案例

### 測試案例 1: RPM Fastest Lap 無遙測數據（核心修復驗證）

**目的**: 驗證 RPM 模組不再自動彈出視窗

**前置條件**:
- ✅ 無遙測分析 JSON 檔案
- ✅ 啟動 F1T GUI

**測試步驟**:
```
1. 開啟 F1T GUI (dist\F1T_GUI\F1T_GUI.exe)
2. 選擇年份: 2025
3. 選擇賽事: Australia (或任何可用賽事)
4. 選擇會話: R (正賽)
5. 選擇車手: VER
6. 點擊「RPM 分析」開啟 RPM 模組
7. 在 RPM 模組中，將 "Lap Options" 切換為 "Fastest Lap"
8. 觀察是否有視窗彈出
```

**預期結果**:
- ✅ RPM 模組應該顯示 (不彈出任何新視窗)
- ✅ 終端輸出應該顯示:
  ```
  [RPM_MDI] 🔍 [API-ONLY] 檢查遙測分析本地緩存: 2025 Australia R
  ⚠️ [RPM_MDI] [API-ONLY] 遙測分析數據不存在於本地緩存
  💡 [RPM_MDI] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據
  💡 [RPM_MDI] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8
  ```
- ✅ RPM 模組可能顯示 Lap 1（預設）或保持當前圈數

**實際結果**: [待填寫]

**狀態**: [ ] 通過 / [ ] 失敗

---

### 測試案例 2: RPM Fastest Lap 有遙測數據（正常流程）

**目的**: 驗證有數據時 Fastest Lap 功能正常

**前置條件**:
- ✅ 先手動生成遙測 JSON
- ✅ 啟動 F1T GUI

**測試步驟**:
```
1. 先手動執行 CLI 生成遙測數據:
   python f1_analysis_modular_main.py -f 8 -y 2025 -r Australia -s R
   
2. 確認生成 JSON:
   Get-ChildItem "json\telemetry_analysis_*_Australia_*.json"
   
3. 開啟 F1T GUI
4. 選擇: 2025 > Australia > R > VER
5. 開啟「RPM 分析」
6. 切換到 "Fastest Lap"
```

**預期結果**:
- ✅ RPM 模組成功載入 VER 的最速圈數據
- ✅ 不彈出任何新視窗
- ✅ 終端輸出:
  ```
  [RPM_MDI] 🔍 [API-ONLY] 檢查遙測分析本地緩存: 2025 Australia R
  [RPM_MDI] 📂 [API-ONLY] 找到本地遙測分析緩存: json\telemetry_analysis_...json
  [RPM_MDI] ✅ 成功載入最速圈: VER Lap XX
  ```
- ✅ RPM 圖表顯示最速圈的 RPM 數據

**實際結果**: [待填寫]

**狀態**: [ ] 通過 / [ ] 失敗

---

### 測試案例 3: 其他模組 Fastest Lap（回歸測試）

**目的**: 確認其他 7 個模組也符合 API-ONLY

**測試步驟**:
```
對以下模組重複測試案例 1 的步驟:
1. Speed Analysis
2. Gear Analysis  
3. Throttle Analysis
4. Acceleration Analysis
5. Speed Diff Analysis
6. Distance Diff Analysis
7. Brake Analysis
```

**預期結果**: 所有模組行為與 RPM 相同
- ✅ 無遙測數據時：不彈出視窗，顯示 API-ONLY 提示
- ✅ 有遙測數據時：成功載入最速圈，不彈出視窗

**實際結果**: [待填寫]

**狀態**:
- [ ] Speed Analysis: [ ] 通過 / [ ] 失敗
- [ ] Gear Analysis: [ ] 通過 / [ ] 失敗
- [ ] Throttle Analysis: [ ] 通過 / [ ] 失敗
- [ ] Acceleration Analysis: [ ] 通過 / [ ] 失敗
- [ ] Speed Diff Analysis: [ ] 通過 / [ ] 失敗
- [ ] Distance Diff Analysis: [ ] 通過 / [ ] 失敗
- [ ] Brake Analysis: [ ] 通過 / [ ] 失敗

---

### 測試案例 4: 混合場景（壓力測試）

**目的**: 驗證多模組同時使用時無問題

**測試步驟**:
```
1. 無遙測 JSON 狀態
2. 開啟 F1T GUI
3. 同時開啟 3 個模組: RPM + Speed + Gear
4. 在所有 3 個模組中切換到 "Fastest Lap"
5. 觀察是否有視窗彈出或錯誤
```

**預期結果**:
- ✅ 3 個模組都不彈出視窗
- ✅ 3 個模組都顯示 API-ONLY 提示
- ✅ 無錯誤或崩潰

**實際結果**: [待填寫]

**狀態**: [ ] 通過 / [ ] 失敗

---

### 測試案例 5: 通過 GUI 遙測模組生成數據（完整工作流）

**目的**: 驗證正確的用戶工作流程

**測試步驟**:
```
1. 無遙測 JSON 狀態
2. 開啟 F1T GUI
3. 先開啟「遙測分析」模組
4. 選擇: 2025 > Australia > R > VER + LEC
5. 等待遙測分析完成（生成 JSON）
6. 開啟「RPM 分析」
7. 切換到 "Fastest Lap"
```

**預期結果**:
- ✅ 遙測分析模組成功生成 JSON
- ✅ RPM 模組成功載入最速圈
- ✅ 不彈出額外的視窗
- ✅ 整個流程流暢無錯誤

**實際結果**: [待填寫]

**狀態**: [ ] 通過 / [ ] 失敗

---

## 📊 測試結果摘要

### 總體結果
- **執行日期**: [待填寫]
- **執行人員**: [待填寫]
- **總測試案例**: 5 + 7 (回歸測試)
- **通過**: [ ] / 12
- **失敗**: [ ] / 12
- **成功率**: [ ]%

### 關鍵指標
| 測試項目 | 狀態 | 備註 |
|---------|------|------|
| RPM Fastest Lap 無數據 | [ ] | 核心修復 |
| RPM Fastest Lap 有數據 | [ ] | 正常流程 |
| 其他 7 模組回歸 | [ ] | API-ONLY 合規性 |
| 混合場景壓力測試 | [ ] | 穩定性 |
| 完整工作流 | [ ] | 用戶體驗 |

---

## 🐛 Bug 追蹤

### 發現的問題
[如果測試失敗，在此記錄]

#### Bug #1: [標題]
- **描述**: 
- **重現步驟**: 
- **預期行為**: 
- **實際行為**: 
- **嚴重性**: [ ] Critical / [ ] High / [ ] Medium / [ ] Low
- **狀態**: [ ] Open / [ ] Fixed / [ ] Won't Fix

---

## ✅ 測試通過標準

### 必須通過 (Critical)
- [ ] 測試案例 1 通過（RPM Fastest Lap 無數據不彈窗）
- [ ] 測試案例 2 通過（RPM Fastest Lap 有數據正常載入）
- [ ] 無 Critical 或 High severity bugs

### 應該通過 (Important)
- [ ] 測試案例 3 全部通過（7 個模組回歸測試）
- [ ] 測試案例 4 通過（混合場景）
- [ ] 測試案例 5 通過（完整工作流）

### 建議通過 (Optional)
- [ ] 終端輸出清晰易懂
- [ ] 無多餘的錯誤日誌
- [ ] 用戶體驗流暢

---

## 📝 測試備註

### 環境資訊
- **作業系統**: Windows [版本]
- **Python 版本**: [版本]
- **EXE 大小**: [MB]
- **測試數據**: 2025 Australian GP / 2024 Japanese GP / 其他

### 觀察與建議
[測試過程中的觀察、建議、改進點]

---

## 🔄 後續行動

### 如果全部通過
- [ ] 更新版本號
- [ ] 發布 Release Notes
- [ ] 通知用戶
- [ ] 關閉相關 Issues

### 如果有失敗
- [ ] 分析失敗原因
- [ ] 修復 Bug
- [ ] 重新測試
- [ ] 更新修復文檔

---

**測試工程師**: [姓名]  
**測試日期**: [日期]  
**測試版本**: 2025-10-07 修復版  
**報告狀態**: ⏳ 待執行
