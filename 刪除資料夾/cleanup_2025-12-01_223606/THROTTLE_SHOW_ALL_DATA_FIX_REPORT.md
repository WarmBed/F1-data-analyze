# Throttle Box Plot "Show All Data" 失效根本原因診斷報告

## 🔍 問題重現

**用戶反饋**：
> 使用 Throttle Box Plot filter 某一車手後，點擊 "Show All Data" 按鈕，該車手仍然保持隱藏狀態

## ❌ 根本原因

### 架構差異導致的調用鏈斷裂

**Throttle Box Plot** 使用**包裝器模式（Wrapper Pattern）**：
```
ThrottleBoxPlotAnalysisModule (包裝器)
    └── _throttle_boxplot_core: ThrottleBoxPlotAnalysis (MDI 實例)
            └── chart_widget: ThrottleBoxPlotChartWidget
                    └── show_all_drivers() 方法
```

**Lap Time Box Plot** 使用**繼承模式（Inheritance Pattern）**：
```
LapBoxPlotAnalysisModule (繼承自 LapTimeBoxPlotAnalysis)
    └── chart_widget: LapTimeBoxPlotChartWidget
            └── show_all_drivers() 方法
```

### 關鍵問題

**ThrottleBoxPlotAnalysisModule（包裝器）缺少 `reset_chart_view()` 方法**

主 GUI 的調用鏈：
```
用戶點擊 "Show All Data"
    ↓
f1t_gui_main.show_all_data_in_current_tab()
    ↓
遍歷 MDI 子視窗
    ↓
sub_window.analysis_module.reset_chart_view()  ← 調用包裝器
    ↓
❌ ThrottleBoxPlotAnalysisModule 沒有此方法！
    ↓
調用失敗，隱藏狀態未清除
```

## ✅ 解決方案

### 已修復：添加 `reset_chart_view()` 橋接方法

在 `ThrottleBoxPlotAnalysisModule` 中添加：

```python
def reset_chart_view(self) -> None:
    """
    重置圖表視圖（主 GUI "Show All Data" 按鈕調用）
    
    這個方法橋接主 GUI 與內部 MDI 實例的 reset_chart_view()
    """
    try:
        print("[THROTTLE_MODULE] 🔄 收到 reset_chart_view 請求")
        
        if not self._throttle_boxplot_core:
            print("[THROTTLE_MODULE] ⚠️  MDI 核心實例不存在")
            return
        
        if not hasattr(self._throttle_boxplot_core, 'reset_chart_view'):
            print("[THROTTLE_MODULE] ⚠️  MDI 核心沒有 reset_chart_view 方法")
            return
        
        # 轉發到內部 MDI 實例
        print("[THROTTLE_MODULE] ✅ 轉發 reset_chart_view 至 MDI 核心")
        self._throttle_boxplot_core.reset_chart_view()
        
    except Exception as exc:
        print(f"❌ [THROTTLE_MODULE] reset_chart_view 失敗: {exc}")
        import traceback
        traceback.print_exc()
```

### 修復後的調用鏈

```
用戶點擊 "Show All Data"
    ↓
f1t_gui_main.show_all_data_in_current_tab()
    ↓
ThrottleBoxPlotAnalysisModule.reset_chart_view()  ✅ 新增的橋接方法
    ↓
ThrottleBoxPlotAnalysis.reset_chart_view()  ✅ MDI 實例
    ↓
ThrottleBoxPlotChartWidget.show_all_drivers()  ✅ Widget 方法
    ↓
hidden_drivers.clear()  ✅ 清空隱藏集合
    ↓
update()  ✅ 重繪圖表
```

## 📊 架構模式對比

| 特性 | Throttle Box Plot | Lap Time Box Plot |
|------|-------------------|-------------------|
| 架構模式 | 包裝器模式 | 繼承模式 |
| 外層類別 | ThrottleBoxPlotAnalysisModule | LapBoxPlotAnalysisModule |
| 內層類別 | ThrottleBoxPlotAnalysis (MDI) | LapTimeBoxPlotAnalysis (MDI) |
| 方法調用 | Module → MDI → Widget | Module (繼承) → Widget |
| reset_chart_view() | ❌ 缺失（已修復） | ✅ 繼承自 MDI |
| 複雜度 | 高（需要橋接） | 低（直接繼承） |

## 🎯 為什麼 Lap Time 沒問題？

**Lap Time Box Plot** 使用**繼承模式**：
```python
class LapBoxPlotAnalysisModule(LapTimeBoxPlotAnalysis):
    """向後相容的別名，供既有匯入路徑使用"""
    pass
```

- `LapBoxPlotAnalysisModule` **繼承** `LapTimeBoxPlotAnalysis`
- `LapTimeBoxPlotAnalysis` **繼承** `UniversalAnalysisMDI`
- `UniversalAnalysisMDI` 已經實現 `reset_chart_view()`
- **自動繼承所有方法**，無需額外橋接

## 🔧 其他使用包裝器模式的模組

需要檢查是否也有同樣問題：

```bash
# 搜尋其他使用包裝器模式的模組
grep -r "self\._.*_core" modules/gui/ --include="*_module.py"
```

可能需要修復的模組：
1. ✅ **Throttle Box Plot** - 已修復
2. ⚠️ **其他使用 `_xxx_core` 模式的模組** - 待檢查

## 📝 修改檔案

- `modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_module.py`
  - ✅ 添加 `reset_chart_view()` 橋接方法

## 🧪 測試驗證

### 測試步驟

1. **啟動 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟 Throttle Box Plot**
   - Analysis → Throttle Analysis → Throttle Box Plot

3. **測試 Filter 功能**
   - 右鍵點擊任何車手
   - 選擇 "Hide XXX"
   - 驗證車手被隱藏

4. **測試 Show All Data 按鈕**
   - 點擊主 GUI 的 "Show All Data" 按鈕
   - 檢查終端輸出是否顯示：
     ```
     [THROTTLE_MODULE] 🔄 收到 reset_chart_view 請求
     [THROTTLE_MODULE] ✅ 轉發 reset_chart_view 至 MDI 核心
     [THROTTLE_MDI] 🔄 收到 reset_chart_view 請求
     [THROTTLE_MDI] ✅ 調用 chart_widget.show_all_drivers()
     [THROTTLE_CHART] 已恢復 X 個隱藏車手
     ```
   - 驗證所有車手恢復顯示

### 預期結果

✅ "Show All Data" 按鈕正常工作  
✅ 所有隱藏車手恢復顯示  
✅ Y 軸範圍正確調整  
✅ 終端輸出顯示完整調用鏈  

## 🎉 結論

**問題根源**：架構模式差異導致方法調用鏈斷裂

- Throttle Box Plot 使用**包裝器模式**，外層類別缺少橋接方法
- Lap Time Box Plot 使用**繼承模式**，自動繼承所有方法

**修復方式**：在包裝器類別添加橋接方法轉發調用

**經驗教訓**：
1. 包裝器模式需要手動實現所有需要的介面方法
2. 繼承模式自動繼承所有方法，維護成本更低
3. 遵循 DRY 原則時，優先考慮繼承而非包裝

## 📌 遵循原則 0

✅ **禁止幻覺編碼**：
- 使用 `grep_search` 確認實際代碼結構
- 使用 `read_file` 驗證方法是否存在
- 創建測試腳本模擬問題場景

✅ **深度確認**：
- 檢查完整調用鏈
- 對比兩個模組的架構差異
- 找出根本原因而非表面症狀
