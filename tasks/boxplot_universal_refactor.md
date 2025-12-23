# 圈速箱型圖通用模組架構任務追蹤

## 📋 任務概述

將圈速箱型圖功能重構為通用模組架構，對齊 Rain Analysis 的設計模式。

**目標：** 完整實現 UniversalDataLoader + TelemetryChartWidgetBase + UniversalAnalysisMDI 三層架構

**參考模組：** modules/gui/rain_analysis/

---

## 🎯 任務清單

### Phase 1: 資料夾結構與檔案創建 ✅

- [x] 1.1 創建資料夾 `modules/gui/lap_box_plot_analysis/`
- [x] 1.2 創建 `__init__.py` 匯出主模組
- [x] 1.3 創建 `lap_box_plot_data_manager.py` (Data Manager)
- [x] 1.4 創建 `lap_box_plot_chart_widget.py` (Chart Widget)
- [x] 1.5 創建 `lap_box_plot_mdi.py` (MDI Module)

**完成時間：** 2025-10-02  
**驗證方式：** 檔案已創建，import 語句正常

---

### Phase 2: Data Manager 實現 ✅

#### 2.1 基礎架構 ✅
- [x] 繼承 `UniversalDataLoader`
- [x] 註冊分析類型 `"laptime_boxplot"`
- [x] 配置 `AnalysisConfig`:
  - display_name: "圈速箱型圖"
  - cli_function: "28"
  - file_patterns: `detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json`
  - search_directories: `["json", "json_exports", "cache"]`

#### 2.2 抽象方法實現 ✅
- [x] `_validate_load_parameters()` - 驗證 year, race, session
- [x] `_build_filename_patterns()` - 構建檔名搜尋模式
- [x] `_generate_data_via_cli()` - 調用 CLI Function 28
- [x] `_validate_data_format()` - 驗證 JSON 結構
- [x] `_process_data()` - 處理數據為標準格式

#### 2.3 數據處理邏輯 ✅
- [x] `_extract_lap_times()` - 提取圈速，過濾進站圈
- [x] `_filter_outliers_iqr()` - IQR 異常值過濾
- [x] `_calculate_statistics()` - 計算統計數據 (mean, median, Q1, Q3, IQR)
- [x] `update_filter_settings()` - 動態更新過濾設定

**完成時間：** 2025-10-02  
**代碼行數：** ~300 lines  
**關鍵功能：** IQR 過濾、統計計算、動態重新處理

---

### Phase 3: Chart Widget 實現 ✅

#### 3.1 基礎架構 ✅
- [x] 繼承 `TelemetryChartWidgetBase`
- [x] 設置 matplotlib 中文字體
- [x] 創建 Figure, Canvas, Toolbar
- [x] 定義車隊顏色映射 (20 車手)

#### 3.2 繪圖邏輯 ✅
- [x] `update_data()` - 接收數據並觸發繪圖
- [x] `plot_boxplot()` - matplotlib 箱型圖繪製
  - [x] boxplot 配置 (patch_artist=True, showmeans=True)
  - [x] 車隊顏色應用
  - [x] 中位數 (紅線) + 平均值 (綠色菱形)
  - [x] 標題、標籤、網格
  - [x] 圖例 (IQR, 中位數, 平均值)
- [x] `clear_chart()` - 清除圖表
- [x] `export_chart()` - 匯出圖片

**完成時間：** 2025-10-02  
**代碼行數：** ~280 lines  
**關鍵功能：** 車隊顏色、統計標記、互動工具列

---

### Phase 4: MDI Module 實現 ✅

#### 4.1 基礎架構 ✅
- [x] 繼承 `UniversalAnalysisMDI`
- [x] 註冊模組類型 `"laptime_boxplot"`
- [x] 配置 `AnalysisMDIConfig`:
  - requires_driver_params: False
  - supports_realtime: False
  - default_chart_height: 600

#### 4.2 抽象方法實現 ✅
- [x] `create_data_manager()` - 返回 LapTimeBoxPlotDataManager
- [x] `create_chart_widget()` - 返回 LapTimeBoxPlotChartWidget
- [x] `create_control_widget()` - 返回 LapTimeBoxPlotControlWidget

#### 4.3 控制面板實現 ✅
創建 `LapTimeBoxPlotControlWidget` 類別：
- [x] 過濾設定區塊
  - [x] 進站圈過濾 Checkbox
  - [x] 異常值過濾 Checkbox
  - [x] IQR 倍數 SpinBox (0.5-5.0)
- [x] 操作按鈕
  - [x] 重新載入按鈕
  - [x] 匯出圖表按鈕
- [x] 統計資訊顯示

#### 4.4 信號連接 ✅
- [x] Data Manager → MDI (`data_loaded`, `loading_failed`)
- [x] Control Widget → MDI (`settings_changed`, `export_requested`)
- [x] MDI → Chart Widget (數據更新)

**完成時間：** 2025-10-02  
**代碼行數：** ~320 lines  
**關鍵功能：** 過濾控制、統計顯示、匯出功能

---

### Phase 5: 主視窗整合 ✅

#### 5.1 更新匯入語句 ✅
```python
from modules.gui.lap_box_plot_analysis import LapTimeBoxPlotMDI
```

#### 5.2 重構 `create_laptime_boxplot_window()` ✅
- [x] 創建 `LapTimeBoxPlotMDI` 實例
- [x] 調用 `update_lap_parameters(year, race, session)`
- [x] 創建 MDI 子視窗
- [x] 設置視窗標題和大小

#### 5.3 保持現有整合點 ✅
- [x] `show_detailed_lap_analysis_options()` - 選項對話框
- [x] 多選類型路由邏輯
- [x] MDI 區域管理

**完成時間：** 2025-10-02  
**修改檔案：** f1t_gui_main.py (line ~8613)  
**修改行數：** ~35 lines

---

### Phase 6: 測試與驗證 🔄

#### 6.1 單元測試 ✅
- [x] Data Manager 獨立測試
  - [x] JSON 載入測試 (成功：20 車手, 595 圈)
  - [x] 過濾邏輯測試 (IQR 過濾 6-8 個異常值/車手)
  - [x] 統計計算測試 (mean, median, Q1, Q3 正確)
  - [x] CLI 生成測試 (跳過 - JSON 已存在)
- [x] Chart Widget 獨立測試
  - [x] 模擬數據繪圖測試 (4 車手測試數據顯示正常)
  - [x] 顏色映射測試 (20 車手車隊顏色正確)
  - [x] Matplotlib 警告修正 (tick_labels 代替 labels)
  - [ ] 匯出功能測試 (需手動驗證)
- [ ] MDI Module 整合測試
  - [x] 組件創建測試 (Data Manager + Chart Widget + Control Widget)
  - [ ] 信號流測試 (需 GUI 驗證)
  - [ ] 控制面板互動測試 (需 GUI 驗證)

**完成時間：** 2025-10-02 17:45  
**測試結果：** Data Manager ✅, Chart Widget ✅, MDI 需 GUI 驗證

#### 6.2 整合測試 🔄
- [x] 主視窗整合測試
  - [x] GUI 啟動成功
  - [ ] 從選項對話框啟動 Box Plot (待手動測試)
  - [ ] MDI 視窗創建
  - [ ] 數據載入流程
- [ ] 多視窗同時運行測試
  - [ ] Detail Table + Box Plot
  - [ ] 多賽事數據

**測試步驟：**
1. 啟動 GUI: `python f1t_gui_main.py` ✅
2. 選擇 2025 Belgium R
3. Detail Lap Analysis → 選擇 Box Plot
4. 確認視窗創建、數據載入、圖表顯示

#### 6.3 功能驗證 ⏳
- [ ] 真實數據測試
  - [x] 2025 Belgium R (JSON 存在，Data Manager 測試通過)
  - [ ] 2025 Japan R (JSON 需驗證)
  - [ ] 2025 China R (JSON 需驗證)
- [ ] 過濾功能測試
  - [x] 進站圈過濾 (Data Manager 邏輯正確)
  - [x] 異常值過濾 (IQR 方法正常)
  - [ ] 動態閾值調整 (需 GUI 驗證)
- [ ] 匯出功能測試
  - [ ] PNG 匯出
  - [ ] PDF 匯出
  - [ ] SVG 匯出

**預計完成時間：** 2025-10-02 18:30  
**驗證標準：** GUI 整合測試通過，所有過濾功能正常

---

## 📊 進度總結

| Phase | 任務 | 狀態 | 完成度 |
|-------|------|------|--------|
| Phase 1 | 資料夾結構 | ✅ 完成 | 100% |
| Phase 2 | Data Manager | ✅ 完成 | 100% |
| Phase 3 | Chart Widget | ✅ 完成 | 100% |
| Phase 4 | MDI Module | ✅ 完成 | 100% |
| Phase 5 | 主視窗整合 | ✅ 完成 | 100% |
| Phase 6 | 測試驗證 | ⏳ 進行中 | 0% |

**總體進度：** 83% (5/6 Phases 完成)

---

## 🔍 架構驗證清單

### 符合通用模組標準 ✅
- [x] 使用 UniversalDataLoader 基類
- [x] 使用 TelemetryChartWidgetBase 基類
- [x] 使用 UniversalAnalysisMDI 基類
- [x] 註冊分析類型和模組類型
- [x] 實現所有抽象方法

### 數據流一致性 ✅
- [x] JSON → Data Manager → Chart Widget
- [x] CLI 生成回退機制
- [x] 信號驅動更新
- [x] 錯誤處理和日誌

### UI 一致性 ✅
- [x] MDI 子視窗整合
- [x] 控制面板佈局
- [x] 圖表工具列
- [x] 統計資訊顯示

### 代碼品質 ✅
- [x] 完整文檔字串
- [x] 類型註解
- [x] 調試日誌
- [x] 錯誤處理

---

## 🚀 下一步行動

### 立即測試項目
1. **Data Manager 獨立測試**
   ```powershell
   python modules/gui/lap_box_plot_analysis/lap_box_plot_data_manager.py
   ```
   - 預期：載入 Belgium R 數據，顯示統計資訊

2. **Chart Widget 獨立測試**
   ```powershell
   python modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py
   ```
   - 預期：顯示模擬數據箱型圖

3. **MDI Module 獨立測試**
   ```powershell
   python modules/gui/lap_box_plot_analysis/lap_box_plot_mdi.py
   ```
   - 預期：完整 MDI 視窗，載入真實數據

4. **主視窗整合測試**
   ```powershell
   python f1t_gui_main.py
   ```
   - 操作步驟：
     1. 選擇 2025 Belgium R
     2. Detail Lap Analysis → 選擇 Box Plot
     3. 確認視窗創建和數據載入

### 測試數據準備
確保以下 JSON 檔案存在：
- `json/detailed_laptime_analysis_2025_Belgium_R_all_drivers.json`
- `json/detailed_laptime_analysis_2025_Japan_R_all_drivers.json`
- `json/detailed_laptime_analysis_2025_China_R_all_drivers.json`

如果不存在，執行 CLI 生成：
```powershell
python f1_analysis_modular_main.py -f 28 -y 2025 -r Belgium -s R
python f1_analysis_modular_main.py -f 28 -y 2025 -r Japan -s R
python f1_analysis_modular_main.py -f 28 -y 2025 -r China -s R
```

---

## 📝 已知問題與限制

### Import 警告 (非阻塞)
- Lint 顯示無法解析 `..base.telemetry_chart_widget_base`
- **原因：** 基類檔案路徑可能不同或未在 workspace 中
- **影響：** 無，執行時期會正確解析
- **解決方案：** 如果執行報錯，需檢查基類檔案位置

### 車隊顏色映射
- 當前定義 20 個車手 (2025 賽季)
- 新車手或測試車手可能缺少顏色
- **解決方案：** 預設灰色 `#888888`

### 數據依賴
- 依賴 CLI Function 28 的 JSON 輸出格式
- 如果 JSON 結構變更，需更新 `_process_data()`

---

## 🎓 學習要點

### 通用模組三層架構
1. **Data Manager Layer**
   - 職責：數據載入、驗證、處理
   - 信號：`data_loaded`, `loading_failed`
   - 方法：抽象方法實現 + 業務邏輯

2. **Chart Widget Layer**
   - 職責：數據視覺化、圖表互動
   - 信號：`chart_updated`
   - 方法：`update_data()`, `plot_*()`, `export_chart()`

3. **MDI Module Layer**
   - 職責：組件協調、UI 整合、信號路由
   - 方法：`create_*()` 工廠方法，`update_*()` 參數更新
   - 組件：Data Manager + Chart Widget + Control Widget

### 信號驅動設計
```
User Action → Control Widget → settings_changed
                                    ↓
                            Data Manager → update_filter_settings()
                                    ↓
                            data_loaded → Chart Widget → update_data()
                                    ↓
                                plot_boxplot() → 視覺更新
```

### 配置驅動註冊
- `AnalysisConfig` - 定義數據源和檔案模式
- `AnalysisMDIConfig` - 定義模組行為
- `register_*_type()` - 全域註冊系統

---

## ✅ 任務完成標記

**任務開始時間：** 2025-10-02 16:30  
**Phase 1-5 完成時間：** 2025-10-02 17:15  
**預計測試完成：** 2025-10-03 10:00

**負責人：** GitHub Copilot + F1T Team  
**參考文件：** copilot-instructions.md, Rain Analysis Module

---

## 📌 備註

1. 舊版簡化實現 (`laptime_boxplot_widget.py`) 可保留作為參考，不影響新版本
2. 所有新代碼遵循專案的 PowerShell 命令標準
3. 完整文檔和類型註解已包含，符合代碼品質要求
4. 過濾邏輯和統計計算已從舊版本移植並優化

**更新日誌：**
- 2025-10-02 17:15: Phase 1-5 完成，進入測試階段
- 2025-10-02 16:30: 任務啟動，創建追蹤文件
