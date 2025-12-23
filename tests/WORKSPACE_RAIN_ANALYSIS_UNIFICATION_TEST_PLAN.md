# Workspace Rain Analysis 統一載入測試計畫

## 📅 修改日期: 2025-10-11

## 🎯 修改目標

將 `workspace_serializer.py` 的 `_rebuild_mdi_window()` 方法修改為與手動開啟完全一致的流程。

### 修改前後對比表

| 項目 | 修改前（舊流程） | 修改後（新流程） | 狀態 |
|------|-----------------|-----------------|------|
| **參數來源** | 從 JSON 配置讀取 | 從主視窗 GUI 實時獲取 | ✅ |
| **參數獲取方式** | `parameters.get()` | `parameter_provider` | ✅ |
| **標題來源** | 配置中的 `window_title` | 動態調用 `get_window_title()` | ✅ |
| **標題生成** | 靜態 JSON 字串 | 動態生成（當前 GUI 參數） | ✅ |
| **尺寸設定** | 配置中的 `size` | `analysis_module.get_default_size()` | ✅ |
| **位置設定** | 配置中的 `position` | `_position_subwindow()` 自動計算 | ✅ |
| **PopoutSubWindow** | ✅ 有包裝 | ✅ 有包裝 | ✅ |
| **彈出功能** | ✅ 支援 | ✅ 支援 | ✅ |
| **模組創建** | `_create_module_instance()` | `main_window._create_analysis_module()` | ✅ |
| **信號連結** | ❌ 無 | ✅ `window_closed` | ✅ |
| **追蹤列表** | ❌ 無 | ✅ `active_subwindows` | ✅ |
| **數據來源** | 讀取 JSON 檔案 | 調用 API | ✅ |

## 🔧 修改內容

### 檔案: `core/workspace_serializer.py`

#### 方法: `_rebuild_mdi_window()`

**修改範圍**: Line 672-780

**關鍵變更**:

1. **移除 JSON 參數使用**
   ```python
   # ❌ 舊流程
   parameters = window_config.get('parameters', {})
   year = parameters.get('year')
   
   # ✅ 新流程
   current_year = self.main_window.year_combo.currentText()
   ```

2. **使用主視窗的模組工廠**
   ```python
   # ❌ 舊流程
   analysis_module = self._create_module_instance(window_type, parameters)
   
   # ✅ 新流程
   analysis_module = self.main_window._create_analysis_module(
       window_type,
       module_type_hint=window_type
   )
   ```

3. **動態生成標題**
   ```python
   # ❌ 舊流程
   window_title = window_config.get('window_title', '')
   
   # ✅ 新流程
   window_title = analysis_module.get_window_title(
       current_year,
       clean_race,
       current_session
   )
   ```

4. **添加信號連接**
   ```python
   # ✅ 新增
   if hasattr(analysis_window, 'window_closed'):
       analysis_window.window_closed.connect(
           lambda: self.main_window.on_subwindow_closed(analysis_window)
       )
   ```

5. **添加追蹤列表**
   ```python
   # ✅ 新增
   if hasattr(self.main_window, 'active_subwindows'):
       self.main_window.active_subwindows.append(analysis_window)
   ```

6. **自動計算位置**
   ```python
   # ❌ 舊流程
   subwindow.move(position['x'], position['y'])
   
   # ✅ 新流程
   self.main_window._position_subwindow(mdi_area, analysis_window)
   ```

## 🧪 測試計畫

### 階段 1: 基礎功能測試

#### Test 1.1: Rain Analysis 載入測試
**操作步驟**:
1. 啟動 GUI: `python f1t_gui_main.py`
2. 設置參數: Year=2024, Race=Japan, Session=R
3. 手動開啟 Rain Analysis 模組
4. 保存 Workspace: `File > Save Workspace`
5. 關閉 GUI
6. 重新啟動 GUI
7. 載入 Workspace: `File > Load Workspace`

**預期結果**:
- ✅ Rain Analysis 視窗成功重建
- ✅ 視窗標題使用當前 GUI 參數（而非 JSON 中的舊參數）
- ✅ 視窗尺寸符合模組預設
- ✅ 視窗位置自動計算，不重疊
- ✅ Popout 功能正常運作
- ✅ 視窗關閉時正確觸發 `on_subwindow_closed`
- ✅ 視窗在 `active_subwindows` 列表中

**調試輸出檢查**:
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
[WORKSPACE] ✅ 視窗已重建: 'Rain Analysis - 2024 Japan R'
[WORKSPACE] 📊 使用當前主視窗參數: 2024 Japan R
[WORKSPACE] 🔄 此視窗將調用 API 載入數據（不使用 JSON 緩存）
```

#### Test 1.2: 參數變更後載入測試
**操作步驟**:
1. 保存 Workspace (Year=2024, Race=Japan)
2. 關閉 GUI
3. 重啟 GUI
4. **變更參數**: Year=2025, Race=Australia, Session=Q
5. 載入 Workspace

**預期結果**:
- ✅ 視窗標題顯示新參數: "Rain Analysis - 2025 Australia Q"
- ✅ 模組調用 API 載入 2025 Australia Q 的數據
- ✅ **不會**載入 JSON 中保存的 2024 Japan 數據

**驗證重點**:
- 標題是否反映當前 GUI 參數
- 是否調用 API 而非讀取 JSON
- 數據是否為新參數的數據

### 階段 2: 進階功能測試

#### Test 2.1: Popout 功能測試
**操作步驟**:
1. 載入 Workspace 後 Rain Analysis 視窗重建
2. 點擊視窗的 "彈出" 按鈕
3. 驗證視窗彈出為獨立視窗
4. 點擊 "返回" 按鈕
5. 驗證視窗返回 MDI 區域

**預期結果**:
- ✅ Popout 功能正常運作
- ✅ 彈出後視窗仍可正常操作
- ✅ 返回後視窗位置正確

#### Test 2.2: 視窗關閉測試
**操作步驟**:
1. 載入 Workspace 後 Rain Analysis 視窗重建
2. 關閉視窗
3. 檢查 `active_subwindows` 列表

**預期結果**:
- ✅ 視窗正確關閉
- ✅ `on_subwindow_closed` 被觸發
- ✅ 視窗從 `active_subwindows` 列表中移除

#### Test 2.3: 多視窗載入測試
**操作步驟**:
1. 手動開啟 Rain Analysis, Tire Strategy, Track Analysis
2. 保存 Workspace
3. 關閉 GUI
4. 重啟並載入 Workspace

**預期結果**:
- ✅ 所有三個視窗正確重建
- ✅ 視窗位置不重疊（自動計算）
- ✅ 所有視窗標題使用當前 GUI 參數
- ✅ 所有視窗都在 `active_subwindows` 列表中

### 階段 3: API 調用測試

#### Test 3.1: API 調用驗證
**操作步驟**:
1. 確保 API 服務運行: `python refactored_api.py`
2. 載入 Workspace
3. 觀察網路請求

**預期結果**:
- ✅ Rain Analysis 模組發送 API 請求
- ✅ API 返回數據
- ✅ **不會**讀取本地 JSON 檔案

**API 請求檢查**:
```
POST https://api.f1telemetrystationpro.org/analyze
{
  "function_id": "1",
  "year": "2024",
  "race": "Japan",
  "session": "R"
}
```

#### Test 3.2: API 錯誤處理測試
**操作步驟**:
1. 停止 API 服務
2. 載入 Workspace

**預期結果**:
- ✅ 顯示錯誤訊息
- ✅ 視窗結構正確創建
- ✅ 不會崩潰

### 階段 4: 標題更新測試

#### Test 4.1: 參數變更時標題更新
**操作步驟**:
1. 載入 Workspace (Rain Analysis 已重建)
2. 在主視窗變更參數: Year=2025, Race=Italy
3. 觸發參數更新（如點擊其他功能）

**預期結果**:
- ✅ Rain Analysis 視窗標題自動更新為 "Rain Analysis - 2025 Italy R"
- ✅ 視窗內容重新載入新數據

**驗證機制**:
- `update_local_parameters()` 被調用
- `update_window_title()` 被調用
- MDI 視窗的 `setWindowTitle()` 被調用

## 📊 測試報告模板

### Test 1.1 執行報告

**執行日期**: YYYY-MM-DD  
**測試環境**: Windows 11, Python 3.11  
**API 狀態**: 運行中 / 離線

| 檢查項目 | 狀態 | 備註 |
|---------|------|------|
| 視窗成功重建 | ✅ / ❌ | |
| 標題使用當前參數 | ✅ / ❌ | |
| 尺寸正確 | ✅ / ❌ | |
| 位置不重疊 | ✅ / ❌ | |
| Popout 功能 | ✅ / ❌ | |
| 信號連接 | ✅ / ❌ | |
| 追蹤列表 | ✅ / ❌ | |
| API 調用 | ✅ / ❌ | |

**錯誤日誌**:
```
(貼上錯誤訊息)
```

**截圖**:
(附上測試截圖)

## 🚨 已知風險

### 風險 1: 參數不匹配
**描述**: 如果模組需要的參數與主視窗提供的不一致  
**影響**: 模組創建失敗  
**緩解**: `_create_analysis_module()` 會驗證參數

### 風險 2: API 不可用
**描述**: API 服務未運行或網路問題  
**影響**: 數據載入失敗  
**緩解**: 錯誤處理機制，顯示友好提示

### 風險 3: 舊 Workspace 檔案
**描述**: 舊版本保存的 Workspace 檔案可能缺少必要欄位  
**影響**: 載入失敗或行為異常  
**緩解**: 向後兼容檢查，預設值設定

## 📝 測試結論

### 成功標準
- ✅ 所有測試階段通過
- ✅ 與手動開啟行為完全一致
- ✅ API 調用正常運作
- ✅ 標題動態更新正確

### 失敗處理
- ❌ 如果任何測試失敗，回滾至舊流程
- ❌ 記錄詳細錯誤日誌
- ❌ 提交 Bug Report

## 🔄 回滾計畫

如果測試失敗，使用 Git 回滾：
```powershell
git checkout HEAD~1 core/workspace_serializer.py
```

## 📌 下一步

1. **通過 Rain Analysis 測試** → 擴展至其他模組
2. **驗證 API 調用** → 優化錯誤處理
3. **收集用戶反饋** → 調整細節
4. **文檔更新** → 更新開發指南

---

**修改者**: GitHub Copilot  
**審核者**: (待填)  
**批准日期**: (待填)
