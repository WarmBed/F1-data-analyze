# Brake 模組全域共享參數池實作任務

**創建時間**: 2025-11-13  
**目標**: 完整複製 Speed 模組的全域共享參數池功能到 Brake 模組

## 任務背景

根據開發原則，需要將「取消勾選與主視窗同步車手與圈數」的功能完整複製到 Brake 模組，包含：
- 載入邏輯
- 更改曲線
- 全域更新
- 跨賽事比較

## 實作清單

### ✅ 階段 1: 跨賽事 API Worker
- [x] 新增 `CrossEventBrakeComparisonWorker` 類別
- [x] 實作 API 請求邏輯 (`/api/v2/analysis/cross-event-comparison`)
- [x] 設置 `analysis_type='brake'` 參數
- [x] 實作進度信號

### ✅ 階段 2: 模組初始化增強
- [x] 新增跨賽事參數屬性：
  - `driver1_year`, `driver1_race`, `driver1_session`
  - `driver2_year`, `driver2_race`, `driver2_session`
- [x] 新增循環更新防護 `_updating_from_shared`
- [x] 新增時間軸模式 `use_time_axis`

### ✅ 階段 3: UI 資訊標籤
- [x] 修改 `_setup_ui()` 新增 `info_label`
- [x] 實作 `_update_info_label()` 方法
- [x] 檢查 `sync_driver_lap_enabled` 狀態顯示/隱藏標籤
- [x] 支援跨賽事比較格式與標準比較格式

### ✅ 階段 4: 跨賽事比較功能
- [x] 實作 `update_cross_event_comparison()` 方法
- [x] 保存跨賽事參數
- [x] 設置 `sync_driver_lap_enabled = False`
- [x] 調用 API Worker 並連接信號

### ✅ 階段 5: API 回應處理
- [x] 實作 `_on_api_progress()` 處理進度
- [x] 實作 `_on_cross_event_data_loaded()` 處理成功
- [x] 提取 Brake 遙測數據
- [x] 構建 chart_data 格式
- [x] 實作 `_on_cross_event_load_error()` 處理錯誤

### ✅ 階段 6: 全域參數池同步
- [x] 實作 `update_from_shared_params()` 方法
- [x] 循環更新防護邏輯
- [x] 檢測跨賽事 vs 標準模式
- [x] 調用對應的更新方法
- [x] 更新資訊標籤

### ✅ 階段 7: 時間軸支援驗證
- [x] 驗證 `update_lap_parameters()` 已支援 `use_time_axis`
- [x] 驗證 `brake_chart_widget.set_time_axis_mode()` 存在
- [x] 驗證時間數據提取邏輯

## 參考範本

所有實作完全參照 `modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py`:
- Line 32-120: CrossEventSpeedComparisonWorker
- Line 445-465: __init__ 初始化
- Line 570-625: _setup_ui 和 _update_info_label
- Line 1010-1070: update_cross_event_comparison
- Line 1085-1153: API 回應處理
- Line 1154-1270: update_from_shared_params

## 測試計畫

### 測試案例 1: 跨賽事比較
1. 開啟 Brake Analysis（2025 Brazil Q）
2. 取消勾選「與主視窗同步車手與圈數」
3. 設定為「2025 Japan Q vs 2025 Brazil R」
4. 驗證：
   - ✅ API 調用成功
   - ✅ 圖表正確繪製
   - ✅ 資訊標籤顯示跨賽事資訊
   - ✅ `sync_driver_lap_enabled = False`

### 測試案例 2: 標準比較
1. 開啟 Brake Analysis（2025 Japan R）
2. 取消勾選「與主視窗同步車手與圈數」
3. 設定為「VER vs LEC，第 1 圈 vs 第 1 圈」
4. 驗證：
   - ✅ 調用 `update_lap_parameters()`
   - ✅ 圖表正確繪製
   - ✅ 資訊標籤顯示標準格式

### 測試案例 3: 全域參數池同步
1. 開啟 Speed Analysis（2025 Brazil Q）
2. 開啟 Brake Analysis（2025 Brazil Q）
3. 兩者都取消勾選「同步」
4. 在 Speed 中修改為「2025 Japan R」
5. 驗證：
   - ✅ Brake 自動更新為「2025 Japan R」
   - ✅ 資訊標籤同步更新

### 測試案例 4: 時間軸模式同步
1. 開啟 Speed 和 Brake（都取消同步）
2. 在 Speed 中勾選「使用時間軸」
3. 修改參數並點擊 OK
4. 驗證：
   - ✅ Brake 的時間軸 checkbox 自動勾選
   - ✅ 圖表 X 軸切換為時間

## 已知問題

無

## 完成狀態

- ✅ 所有代碼實作完成（2025-11-13）
- ⏳ 等待用戶測試驗證
