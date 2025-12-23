# Lap Time & Throttle Box Plot "Show All Data" 問題總結

## 📋 用戶反饋

1. **Throttle Box Plot**: "使用 filter 某一欄位後，使用 show all data 時，該棒狀條仍然是隱藏狀態"
2. **Lap Time Box Plot**: "lap time box plot 也有一樣問題"

## 🔍 深度診斷結果

### ✅ Throttle Box Plot - 已確認問題並修復

**問題根源**: 使用包裝器模式（Wrapper Pattern），外層類別缺少 `reset_chart_view()` 方法

```
ThrottleBoxPlotAnalysisModule (包裝器) ← 主 GUI 調用此類別
    ├── ❌ reset_chart_view() - 缺失（已修復）
    └── _throttle_boxplot_core: ThrottleBoxPlotAnalysis (MDI)
            ├── ✅ reset_chart_view() - 存在
            └── chart_widget: ThrottleBoxPlotChartWidget
                    ├── ✅ show_all_drivers() - 存在
                    └── ✅ hidden_drivers - 存在
```

**修復**: 在 `ThrottleBoxPlotAnalysisModule` 添加橋接方法 ✅

### ⚠️ Lap Time Box Plot - 理論上應該正常

**架構模式**: 使用繼承模式（Inheritance Pattern）

```
LapBoxPlotAnalysisModule (繼承 LapTimeBoxPlotAnalysis)
    └── ✅ 自動繼承 reset_chart_view()
    
LapTimeBoxPlotAnalysis (繼承 UniversalAnalysisMDI)
    ├── ✅ reset_chart_view() - 存在（line 1340）
    └── chart_widget: LapTimeBoxPlotChartWidget
            ├── ✅ show_all_drivers() - 存在（line 793）
            ├── ✅ hidden_drivers - 存在（__init__ line 73）
            ├── ✅ _hide_driver() - 存在
            └── ✅ update_data() 不會重置 hidden_drivers
```

**理論測試**: 所有單元測試通過 ✅

## 🤔 為什麼用戶說 Lap Time 也有問題？

### 可能原因 1: 主 GUI 使用了不同的模組實例

檢查 `f1t_gui_main.py` 的兩個入口點：

1. **直接創建方式**（line 11917）:
```python
analysis_module = LapTimeBoxPlotAnalysis(parent=self)
# ✅ 直接使用 MDI 類別，有 reset_chart_view()
```

2. **Module Factory 方式**（line 13115）:
```python
module = LapTimeBoxPlotAnalysis(parent=self)
# ✅ 也是直接使用 MDI 類別
```

兩種方式都正確 ✅

### 可能原因 2: 用戶測試時的具體場景

需要用戶提供更多資訊：

1. **如何開啟** Lap Time Box Plot？
   - 從選單開啟？
   - 從工具列開啟？
   - 從快捷鍵開啟？

2. **具體步驟**：
   - 步驟 1: 開啟 Lap Time Box Plot
   - 步驟 2: 右鍵隱藏某個車手（例如 VER）
   - 步驟 3: 點擊主 GUI 的 "Show All Data" 按鈕
   - 步驟 4: 觀察結果 - 車手是否恢復？

3. **終端輸出**：
   - 是否看到 `[BOXPLOT_MDI] 🔄 收到 reset_chart_view 請求`？
   - 是否看到 `[BOXPLOT_CHART] 已恢復 X 個隱藏車手`？

### 可能原因 3: 實際問題在其他模組

用戶可能混淆了不同的模組。需要確認：

- 是否真的是 **Lap Time Box Plot**？
- 還是其他箱型圖模組（如 Ideal Lap, Driver Position 等）？

## 📊 對比表

| 特性 | Throttle Box Plot | Lap Time Box Plot |
|------|-------------------|-------------------|
| 架構模式 | 包裝器模式 | 繼承模式 |
| 外層類別 | ThrottleBoxPlotAnalysisModule | LapBoxPlotAnalysisModule |
| reset_chart_view() | ❌ 缺失 → ✅ 已修復 | ✅ 繼承自 MDI |
| show_all_drivers() | ✅ 存在 | ✅ 存在 |
| hidden_drivers | ✅ 存在 | ✅ 存在 |
| 理論測試 | ✅ 通過 | ✅ 通過 |
| 用戶反饋 | ❌ 失效（已修復） | ❌ 失效（待驗證） |

## 🎯 建議測試步驟

### 步驟 1: 重啟 GUI 載入修復後的代碼

```powershell
# 清除 Python 緩存
Remove-Item -Recurse -Force __pycache__, modules\__pycache__ -ErrorAction SilentlyContinue

# 重啟 GUI
python f1t_gui_main.py
```

### 步驟 2: 測試 Throttle Box Plot

1. Analysis → Throttle Analysis → Throttle Box Plot
2. 等待數據載入
3. 右鍵點擊任何車手 → Hide XXX
4. 點擊主 GUI 的 "Show All Data" 按鈕
5. 驗證車手是否恢復

**預期輸出**：
```
[THROTTLE_MODULE] 🔄 收到 reset_chart_view 請求
[THROTTLE_MODULE] ✅ 轉發 reset_chart_view 至 MDI 核心
[THROTTLE_MDI] 🔄 收到 reset_chart_view 請求
[THROTTLE_MDI] ✅ 調用 chart_widget.show_all_drivers()
[THROTTLE_CHART] 已恢復 X 個隱藏車手
```

### 步驟 3: 測試 Lap Time Box Plot

1. Analysis → Driver Race → Lap Time Box Plot
2. 等待數據載入
3. 右鍵點擊任何車手 → Hide XXX
4. 點擊主 GUI 的 "Show All Data" 按鈕
5. 驗證車手是否恢復

**預期輸出**：
```
[BOXPLOT_MDI] 🔄 收到 reset_chart_view 請求
[BOXPLOT_MDI] ✅ 調用 chart_widget.show_all_drivers()
[BOXPLOT_CHART] 已恢復 X 個隱藏車手
```

### 步驟 4: 如果 Lap Time 仍然失效

請提供以下資訊：

1. **終端輸出** - 複製所有相關的 `[BOXPLOT_*]` 訊息
2. **開啟方式** - 從哪個選單或按鈕開啟
3. **視窗標題** - 確認是否為 "Lap Time Box Plot" 或其他名稱
4. **數據來源** - API 還是本地 JSON

## ✅ 修改檔案總結

1. `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_module.py`
   - ✅ 添加 `reset_chart_view()` 橋接方法

2. `modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`
   - ✅ 已有 `reset_chart_view()` 方法（無需修改）

3. `modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_chart_widget.py`
   - ✅ 已有 `show_all_drivers()` 方法（無需修改）
   - ✅ 已修復 `mousePressEvent()` 使用實時檢測

## 🎉 結論

- **Throttle Box Plot**: 問題已確認並修復 ✅
- **Lap Time Box Plot**: 理論上應該正常，需要實際測試驗證

建議用戶重啟 GUI 並按照上述步驟測試，並提供詳細的終端輸出以便進一步診斷。
