# 方案 A：PopoutSubWindow.analysis_module 保存機制調試計劃

## 📋 問題描述

Workspace 載入時創建了 22 個分析視窗，但 race 變更時只檢測到 11 個視窗。
缺失的 11 個視窗主要是事件級模組（rain, pitstop, accident, tire, track）和賽事級模組（laptime, ideal_lap 系列等）。

## 🔍 問題假設

PopoutSubWindow 的 `analysis_module` 屬性在某個環節丟失或未正確保存，導致 `_get_telemetry_analysis_windows()` 無法通過 `getattr(sub_win, 'analysis_module', None)` 獲取模組引用。

## 🎯 調試目標

### 階段 1：確認問題根源（本次更新）

**已添加的調試點：**

1. **PopoutSubWindow.__init__()** (f1t_gui_main.py 第 2142-2160 行)
   - ✅ 記錄收到的 `analysis_module` 參數
   - ✅ 記錄參數類型和 ID
   - ✅ 記錄 `analysis_type` 屬性值
   - ✅ 驗證 `self.analysis_module` 賦值成功

2. **workspace_serializer._rebuild_mdi_window()** (第 733 行)
   - ✅ 記錄傳入 PopoutSubWindow 的參數
   - ✅ 記錄 `analysis_module` 的類型和 ID
   - ✅ 驗證創建後 `analysis_window.analysis_module` 的值

3. **_get_telemetry_analysis_windows()** (f1t_gui_main.py 第 8483 行)
   - ✅ 記錄每個 PopoutSubWindow 的標題和類型
   - ✅ 記錄 `sub_win.analysis_module` 的值
   - ✅ 記錄模組 ID 和 `analysis_type` 屬性

## 📊 測試步驟

### 步驟 1：清理並重啟 GUI
```powershell
# 清理舊 log
Remove-Item "logs\f1_gui_2025-10-25.log" -ErrorAction SilentlyContinue

# 啟動 GUI
python f1t_gui_main.py
```

### 步驟 2：載入 Workspace ID=38
1. 啟動 GUI 後
2. 點擊 **File → Load Workspace**
3. 選擇 **ID=38** (2025_United States_Mexico (2))
4. 等待載入完成

**預期 log 輸出（workspace 載入時）：**
```
[WORKSPACE] [DEBUG] 準備創建 PopoutSubWindow:
[WORKSPACE] [DEBUG]   - window_title: 'Rain Analysis'
[WORKSPACE] [DEBUG]   - mdi_area: CustomMdiArea
[WORKSPACE] [DEBUG]   - analysis_module: RainAnalysisModuleAdapter
[WORKSPACE] [DEBUG]   - analysis_module.id: 293281138xxxx
[WORKSPACE] [DEBUG]   - analysis_module.analysis_type: rain_weather

[POPOUT_INIT] Title: 'Rain Analysis'
[POPOUT_INIT] analysis_module parameter: RainAnalysisModuleAdapter
[POPOUT_INIT] analysis_module id: 293281138xxxx
[POPOUT_INIT] analysis_module.analysis_type: rain_weather
[POPOUT_INIT] self.analysis_module stored: RainAnalysisModuleAdapter

[WORKSPACE] [DEBUG] PopoutSubWindow 創建後驗證:
[WORKSPACE] [DEBUG]   - analysis_window.analysis_module: RainAnalysisModuleAdapter
[WORKSPACE] [DEBUG]   - stored module id: 293281138xxxx
[WORKSPACE] [DEBUG]   - stored module type: rain_weather
```

### 步驟 3：切換 Race 到 Australia
1. 在任一分頁（例如 throttle analysis）
2. 將 Race 下拉選單切換到 **Australia**
3. 等待批次更新完成

**預期 log 輸出（race 變更時）：**
```
[RACE_CONTROL] 賽事參數已變更
[DEBUG] _get_telemetry_analysis_windows() - 開始搜尋視窗

# 檢查 Overview Tab
Tab 1: 'Overview'
發現 CustomMdiArea，檢查子視窗...
子視窗數量: 5

# 第 1 個子視窗 (Rain Analysis)
[SUB_WIN_CHECK] 檢查子視窗: 'Rain Analysis' (type=PopoutSubWindow)
[SUB_WIN_CHECK] sub_win.analysis_module: RainAnalysisModuleAdapter  ← 🎯 關鍵！
[SUB_WIN_CHECK]   - module_id: 293281138xxxx
[SUB_WIN_CHECK]   - has analysis_type: True
[SUB_WIN_CHECK]   - analysis_type value: rain_weather

找到子視窗候選: RainAnalysisModuleAdapter (analysis_type=rain_weather)  ← 應該顯示這個！
✅ 找到 Tab 視窗 (CustomMdiArea 子視窗): rain_weather
```

### 步驟 4：檢查 log 並診斷

**診斷問題矩陣：**

| 現象 | 可能原因 | 下一步 |
|------|---------|-------|
| ✅ POPOUT_INIT 顯示 module 正確<br>❌ SUB_WIN_CHECK 顯示 None | `self.analysis_module` 在初始化後被覆蓋或清除 | 搜尋代碼中所有 `self.analysis_module =` 的賦值 |
| ✅ POPOUT_INIT 顯示 module 正確<br>✅ SUB_WIN_CHECK 顯示正確<br>❌ 但未添加到結果 | `analysis_type` 不在 `all_analysis_types` 中 | 檢查 `all_analysis_types` 集合定義 |
| ❌ POPOUT_INIT 顯示 None | PopoutSubWindow 收到的參數為 None | 檢查 workspace_serializer 傳入參數 |
| ❌ WORKSPACE DEBUG 未出現 | `_rebuild_mdi_window()` 未被調用 | 檢查 workspace 載入流程 |

## 📝 預期結果

**成功情況：**
- 所有 22 個視窗的 `analysis_module` 都正確保存
- Race 變更時檢測到所有 22 個視窗
- Log 顯示所有模組的 `analysis_type` 正確匹配

**失敗情況 1（module 丟失）：**
- POPOUT_INIT 顯示正確，但 SUB_WIN_CHECK 顯示 None
- → 需要追蹤 `self.analysis_module` 的生命週期

**失敗情況 2（module 存在但未檢測）：**
- SUB_WIN_CHECK 顯示正確，但未添加到結果列表
- → 需要檢查 `all_analysis_types` 或檢測邏輯

## 🔧 後續修復方案（根據診斷結果）

### 修復 A1：防止 analysis_module 被覆蓋
```python
# 在 PopoutSubWindow 中搜尋所有 self.analysis_module 賦值
# 確保沒有其他代碼意外清除這個屬性
```

### 修復 A2：補充缺失的 analysis_type
```python
# 如果某些模組的 analysis_type 不在 all_analysis_types 中
# 需要添加到集合中
```

### 修復 A3：改用 active_subwindows 追蹤
```python
# 如果 getattr(sub_win, 'analysis_module') 不可靠
# 改為直接從 self.active_subwindows 列表獲取
```

## ✅ 完成標準

- [ ] Log 中所有 POPOUT_INIT 都顯示正確的 `analysis_module`
- [ ] Log 中所有 SUB_WIN_CHECK 都顯示正確的 `analysis_module`
- [ ] Race 變更時檢測到所有 22 個視窗
- [ ] 所有視窗都能正確更新參數

---

**創建時間：** 2025-10-25  
**最後更新：** 2025-10-25  
**狀態：** 🟡 調試中 - 等待測試結果
