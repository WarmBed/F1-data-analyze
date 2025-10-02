# Lap Analysis 數據顯示修復任務

## 問題描述

GUI 使用 Lap Analysis (速度分析) 後，API 成功生成了 JSON 檔案，但 GUI 卻沒有顯示曲線資料。

## 問題分析

### 已驗證的正常部分

1. ✅ **JSON 生成** - API 成功生成 `comparison_telemetry_VER_VER_2025_Japan_R_Lap1_Lap1.json`
2. ✅ **JSON 結構** - 檔案包含正確的數據結構：
   - `results.telemetry_comparison.Speed` 包含 `driver1_data`, `driver2_data`, `distance`
   - 每個陣列都有 500 個數據點
3. ✅ **數據處理邏輯** - `TelemetryDataLoader._process_telemetry_data` 正確轉換數據：
   - 從 `driver1_data` 轉換為 `driver1_speed`
   - 從 `driver2_data` 轉換為 `driver2_speed`
4. ✅ **信號發送** - `data_loaded` 信號成功發送，數據結構正確

### 測試腳本驗證結果

```
[SPEED DEBUG] 📊 speed_data 鍵值: ['distance', 'driver1_speed', 'driver2_speed', 'driver1_name', 'driver2_name']
[SPEED DEBUG] 📊 distance 點數: 500
[SPEED DEBUG] 📊 driver1_speed 點數: 500
[SPEED DEBUG] 📊 driver2_speed 點數: 500
[SPEED DEBUG] ✅ data_loaded 信號已發送
[SPEED DEBUG] 📡 信號接收者數量: 1
```

## 可能的問題點

### 1. 信號連接鏈路問題

信號傳遞路徑：
```
TelemetryDataLoader.data_loaded
  ↓
SpeedDataManager._on_data_loaded  
  ↓
SpeedDataManager.data_loaded
  ↓
SpeedAnalysisModule._update_chart
  ↓
SpeedAnalysisChartWidget.update_speed_data
```

需要驗證每個環節的信號連接是否正確。

### 2. GUI 初始化順序問題

可能的問題：
- `speed_chart_widget` 在 `data_manager` 發送信號時還未初始化
- MDI 子視窗還未完全顯示
- Qt 事件循環問題

### 3. Chart Widget 更新問題

即使接收到數據，chart widget 可能：
- 數據驗證失敗
- 繪圖方法沒有被調用
- repaint/update 沒有觸發

## 修復方案

### 階段 1：增強調試輸出（已完成）

在以下位置添加詳細的調試輸出：
- ✅ `TelemetryDataLoader._load_json_file` - 信號發送前後
- ✅ `SpeedDataManager._on_data_loaded` - 信號接收和轉發
- ✅ `SpeedAnalysisModule._update_chart` - 圖表更新回調
- ✅ `SpeedAnalysisChartWidget.update_speed_data` - 數據接收和處理

### 階段 2：驗證信號連接

需要檢查的代碼位置：
1. `SpeedDataManager.load_speed_data` (line 79-82)
   ```python
   speed_loader.data_loaded.connect(self._on_data_loaded)
   speed_loader.load_error.connect(self._on_load_error)
   ```

2. `SpeedAnalysisModule.initialize_module` (line 288-289)
   ```python
   self.data_manager.data_loaded.connect(self._update_chart)
   self.data_manager.error_occurred.connect(self._handle_error)
   ```

### 階段 3：檢查 GUI 初始化順序

需要確認：
1. `SpeedAnalysisModule.initialize_module` 是否在載入數據前完成
2. `speed_chart_widget` 是否已正確初始化
3. MDI 子視窗是否已顯示

### 階段 4：驗證 Chart Widget 繪圖

檢查以下方法：
1. `SpeedChartWidget.set_speed_data` - 是否被調用
2. `SpeedChartWidget.paintEvent` - 是否被觸發
3. `SpeedChartWidget.update()` 或 `repaint()` - 是否被調用

## 下一步行動

1. 運行 F1T GUI 並打開 Speed Analysis
2. 觀察終端調試輸出
3. 確認信號傳遞鏈路是否完整
4. 根據調試輸出定位具體問題點

## 預期結果

- 所有調試信號都應該顯示在終端
- 數據應該正確傳遞到 `SpeedAnalysisChartWidget.update_speed_data`
- 圖表應該顯示速度曲線

## 更新記錄

- 2025-10-02: 任務創建，完成階段 1（增強調試輸出）
