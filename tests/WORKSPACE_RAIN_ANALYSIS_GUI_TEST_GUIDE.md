# Workspace Rain Analysis 統一載入 - GUI 功能測試指南

## 📅 測試日期: 2025-10-11

## ✅ 前置測試結果

### Import 測試 (test_workspace_unification_import.py)
- ✅ Import WorkspaceSerializer - 通過
- ✅ 方法簽名檢查 - 通過
- ✅ 主視窗方法存在性 - 通過
- ✅ PopoutSubWindow 存在性 - 通過

**結論**: 所有靜態檢查通過，可以進行 GUI 測試

---

## 🧪 GUI 功能測試

### Test 1: 基礎 Workspace 載入測試

#### 步驟 1: 創建 Workspace
```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 等待 GUI 完全載入
```

**操作**:
1. 在主視窗設置參數:
   - Year: `2024`
   - Race: `Japan`
   - Session: `R`

2. 在左側功能樹中找到並點擊:
   - `Rain Weather Analysis` (Function 1)

3. 等待 Rain Analysis 視窗載入完成

4. 檢查視窗標題:
   ```
   預期: "Rain Analysis - 2024 Japan R"
   或: "雨天分析 - 2024 Japan R"
   ```

5. 保存 Workspace:
   - 選單: `File > Save Workspace`
   - 輸入檔名: `test_rain_2024_japan.json`
   - 保存位置: `workspaces/`

6. 關閉 GUI

#### 步驟 2: 測試 Workspace 載入（相同參數）

```powershell
# 重新啟動 GUI
python f1t_gui_main.py
```

**操作**:
1. 確認主視窗參數仍為:
   - Year: `2024`
   - Race: `Japan`
   - Session: `R`

2. 載入 Workspace:
   - 選單: `File > Load Workspace`
   - 選擇: `workspaces/test_rain_2024_japan.json`

**檢查點 ✓**:
- [ ] Rain Analysis 視窗成功重建
- [ ] 視窗標題為: "Rain Analysis - 2024 Japan R"
- [ ] 視窗內容正確顯示（數據圖表）
- [ ] 視窗尺寸合理（約 1200x800）
- [ ] 視窗位置不超出 MDI 區域

**調試輸出檢查**:
在終端查看是否有以下輸出:
```
[WORKSPACE] ========== 開始重建 MDI 視窗（與手動開啟一致） ==========
[WORKSPACE] 📋 視窗類型: rain_analysis
[WORKSPACE] 🔧 調用主視窗的 _create_analysis_module() 方法...
[WORKSPACE] ✅ 模組創建成功: RainAnalysisModuleAdapter
[WORKSPACE] 📊 當前參數: 2024 Japan R
[WORKSPACE] 🏷️ 動態生成標題: 'Rain Analysis - 2024 Japan R'
[WORKSPACE] 📦 PopoutSubWindow 已創建
[WORKSPACE] 🎨 Widget 已設置
[WORKSPACE] 📏 尺寸已設置: 1200x800
[WORKSPACE] ✅ 已添加到 MDI 區域
[WORKSPACE] 🔗 已連接 window_closed 信號
[WORKSPACE] 📋 已添加到 active_subwindows 追蹤列表
[WORKSPACE] 👁️ 視窗已顯示
[WORKSPACE] 📍 位置已自動計算
[WORKSPACE] ========== MDI 視窗重建完成 ==========
```

---

### Test 2: 參數變更測試（關鍵測試）

#### 步驟 1: 保存 Workspace
```powershell
# GUI 已啟動，Rain Analysis 視窗已開啟
# 當前參數: 2024 Japan R
```

**操作**:
1. 保存 Workspace: `File > Save Workspace`
2. 關閉 GUI

#### 步驟 2: 變更參數後載入

```powershell
# 重新啟動 GUI
python f1t_gui_main.py
```

**操作**:
1. **在載入 Workspace 前**，變更主視窗參數:
   - Year: `2025` ← 變更
   - Race: `Australia` ← 變更
   - Session: `Q` ← 變更

2. 載入 Workspace:
   - 選單: `File > Load Workspace`
   - 選擇: `workspaces/test_rain_2024_japan.json`

**檢查點 ✓**:
- [ ] Rain Analysis 視窗成功重建
- [ ] **關鍵**: 視窗標題為 "Rain Analysis - 2025 Australia Q"
  - ❌ 如果顯示 "2024 Japan R" → 測試失敗，仍使用 JSON 參數
  - ✅ 如果顯示 "2025 Australia Q" → 測試成功，使用當前 GUI 參數
- [ ] 視窗內容顯示 2025 Australia Q 的數據（不是 2024 Japan）
- [ ] 終端顯示 API 調用（不是 JSON 讀取）

**調試輸出檢查**:
```
[WORKSPACE] 📊 當前參數: 2025 Australia Q  ← 確認是新參數
[WORKSPACE] 🏷️ 動態生成標題: 'Rain Analysis - 2025 Australia Q'  ← 確認標題正確
[WORKSPACE] 🔄 此視窗將調用 API 載入數據（不使用 JSON 緩存）  ← 確認使用 API
```

**預期行為**:
- ✅ 視窗使用**當前 GUI 參數** (2025 Australia Q)
- ✅ 調用 API 載入新數據
- ❌ **不會**使用 JSON 中保存的舊參數 (2024 Japan R)

---

### Test 3: Popout 功能測試

**前提**: Rain Analysis 視窗已通過 Workspace 載入

**操作**:
1. 在 Rain Analysis 視窗的標題欄找到 "Popout" 按鈕
   - 可能是圖示按鈕或文字按鈕

2. 點擊 "Popout" 按鈕

**檢查點 ✓**:
- [ ] 視窗從 MDI 區域彈出為獨立視窗
- [ ] 彈出後視窗標題保持正確
- [ ] 彈出後視窗內容正常顯示
- [ ] 彈出後視窗可以移動、調整大小

3. 點擊 "Pop Back In" 按鈕（或類似功能）

**檢查點 ✓**:
- [ ] 視窗返回 MDI 區域
- [ ] 返回後視窗標題保持正確
- [ ] 返回後視窗內容正常顯示

---

### Test 4: 視窗關閉測試

**前提**: Rain Analysis 視窗已通過 Workspace 載入

**操作**:
1. 關閉 Rain Analysis 視窗（點擊 X 按鈕）

**檢查點 ✓**:
- [ ] 視窗正確關閉（無錯誤）
- [ ] 終端無異常輸出
- [ ] 主視窗仍正常運行

**調試輸出檢查**:
應該看到 `on_subwindow_closed` 被觸發的相關訊息

---

### Test 5: 多視窗測試

#### 步驟 1: 創建多視窗 Workspace

**操作**:
1. 手動開啟多個分析模組:
   - Rain Analysis
   - Tire Strategy (如果可用)
   - Track Analysis (如果可用)

2. 保存 Workspace: `multi_window_test.json`

3. 關閉 GUI

#### 步驟 2: 載入多視窗 Workspace

```powershell
python f1t_gui_main.py
```

**操作**:
1. 設置參數: 2024 Japan R
2. 載入 Workspace: `multi_window_test.json`

**檢查點 ✓**:
- [ ] 所有視窗成功重建
- [ ] 視窗位置不重疊（自動計算）
- [ ] 所有視窗標題正確
- [ ] 所有視窗內容正常顯示

---

### Test 6: API 調用驗證測試

**前提**:
1. API 服務運行: `python refactored_api.py`
2. 或使用正式 API: `https://localhost:8000`

**操作**:
1. 清空本地 JSON 緩存（可選）:
   ```powershell
   Remove-Item -Path "json/rain_*.json" -Force
   ```

2. 啟動 GUI 並載入 Workspace

**檢查點 ✓**:
- [ ] 終端顯示 API 請求訊息
- [ ] **不會**顯示 "載入 JSON 檔案" 訊息
- [ ] 視窗數據載入成功

**調試輸出檢查**:
應該看到 Rain Analysis 模組的 API 調用日誌

---

### Test 7: 標題動態更新測試

**前提**: Rain Analysis 視窗已通過 Workspace 載入

**操作**:
1. 在主視窗變更參數:
   - Year: `2025`
   - Race: `Italy`
   - Session: `R`

2. 點擊任何其他功能（觸發參數更新）

**檢查點 ✓**:
- [ ] Rain Analysis 視窗標題自動更新為 "Rain Analysis - 2025 Italy R"
- [ ] 視窗內容重新載入（顯示新數據）

**機制驗證**:
- 主視窗發送參數更新信號
- Rain Analysis 模組接收 `update_local_parameters()`
- 模組調用 `update_window_title()`
- MDI 視窗標題更新

---

## 📊 測試結果記錄表

| Test ID | 測試項目 | 狀態 | 備註 |
|---------|---------|------|------|
| Test 1 | 基礎載入（相同參數） | ⬜ | |
| Test 2 | 參數變更測試 | ⬜ | **關鍵測試** |
| Test 3 | Popout 功能 | ⬜ | |
| Test 4 | 視窗關閉 | ⬜ | |
| Test 5 | 多視窗載入 | ⬜ | |
| Test 6 | API 調用驗證 | ⬜ | |
| Test 7 | 標題動態更新 | ⬜ | |

**狀態標記**:
- ⬜ 未測試
- ✅ 通過
- ❌ 失敗
- ⚠️ 部分通過

---

## 🚨 失敗處理

### 如果 Test 2 失敗（視窗仍顯示舊參數）

**症狀**:
- 視窗標題顯示 JSON 中保存的參數（2024 Japan）
- 而非當前 GUI 參數（2025 Australia）

**可能原因**:
1. `get_window_title()` 沒有被正確調用
2. `current_year` 等變數讀取錯誤
3. `_get_race_key_from_display()` 返回錯誤值

**調試步驟**:
1. 檢查終端輸出中的 "📊 當前參數" 行
2. 確認是否顯示正確的當前參數
3. 添加更多 print 調試輸出

---

## 🔍 關鍵成功指標

### 必須通過的測試
- ✅ **Test 2**: 參數變更測試（最關鍵）
  - 證明使用當前 GUI 參數而非 JSON 參數
  
- ✅ **Test 6**: API 調用驗證
  - 證明調用 API 而非讀取 JSON

### 重要測試
- ✅ **Test 1**: 基礎載入
- ✅ **Test 3**: Popout 功能
- ✅ **Test 7**: 標題動態更新

### 可選測試
- ⬜ **Test 4**: 視窗關閉
- ⬜ **Test 5**: 多視窗載入

---

## 📝 測試執行記錄

### 執行環境
- 作業系統: ________________
- Python 版本: ________________
- API 狀態: ☐ 本地 ☐ 正式 ☐ 離線
- 測試日期: ________________
- 測試人員: ________________

### 錯誤日誌
```
(貼上任何錯誤訊息)
```

### 截圖
(附上關鍵測試的截圖)

---

## ✅ 測試完成後

### 如果所有測試通過
1. 記錄測試結果
2. 更新文檔
3. 準備擴展至其他模組

### 如果有測試失敗
1. 記錄詳細錯誤訊息
2. 截圖保存
3. 分析失敗原因
4. 修復後重新測試

---

**測試指南版本**: v1.0  
**建立日期**: 2025-10-11  
**下次更新**: 測試完成後
