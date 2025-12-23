# Box Plot Widget 重構計畫

## 當前問題

1. **未使用通用模組**
   - 當前直接繼承 QWidget
   - 應該像 Rain Analysis 一樣使用 UniversalAnalysisMDI 和 UniversalDataLoader

2. **硬編碼路徑**
   - 當前: `search_paths = ["json", "json_exports"]`
   - 應該: 在 AnalysisConfig 中註冊 `search_directories`

## 重構方案

### 選項 1：完全遵循通用架構（推薦）
創建三個組件：
- `LapTimeBoxPlotDataManager` - 繼承 UniversalDataLoader
- `LapTimeBoxPlotChartWidget` - 繼承 TelemetryChartWidgetBase  
- `LapTimeBoxPlotMDI` - 繼承 UniversalAnalysisMDI

**優點**：
- 完全符合系統架構
- 與其他模組一致
- 可復用所有通用功能

**缺點**：
- 需要重構大量代碼
- 複雜度較高

### 選項 2：保持簡化架構但修正路徑（快速）
保持當前單一 Widget 架構，但：
- 使用 UniversalDataLoader 的配置系統
- 正確設置 search_directories

**優點**：
- 修改量小
- 快速完成
- 功能完整

**缺點**：
- 與其他模組架構不一致

## 建議實作

考慮到時間和複雜度，建議採用**選項 2**，並在未來有需要時再重構為完整架構。

### 快速修正步驟

1. **註冊分析類型**
```python
# 在類初始化前註冊
if "laptime_boxplot" not in UniversalDataLoader.ANALYSIS_TYPES:
    boxplot_config = AnalysisConfig(
        display_name="圈速箱型圖",
        debug_prefix="[BOXPLOT]",
        data_source="json",
        cli_function="28",  # Function 28
        file_patterns=[
            "detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json"
        ],
        search_directories=["json", "json_exports", "cache"],
        cache_enabled=True
    )
    UniversalDataLoader.register_analysis_type("laptime_boxplot", boxplot_config)
```

2. **修改 _search_json_file 使用配置**
```python
def _search_json_file(self, year, race, session) -> Optional[str]:
    """搜尋 JSON 檔案 - 使用配置的目錄"""
    filename = f"detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json"
    
    # 從配置獲取搜尋目錄
    search_dirs = ["json", "json_exports", "cache"]  # 與 Rain Analysis 一致
    
    for base_path in search_dirs:
        full_path = os.path.join(base_path, filename)
        if os.path.exists(full_path):
            self._debug(f"✅ 找到檔案: {full_path}")
            return full_path
    
    return None
```

3. **使用項目根目錄作為基準**
```python
# 確保使用正確的工作目錄
project_root = os.getcwd()  # 或使用其他方法獲取
```

## 測試檢查點

1. ✅ 獨立運行顯示視窗
2. ⏳ JSON 檔案搜尋正確
3. ⏳ 數據載入成功
4. ⏳ 圖表繪製正確
5. ⏳ 主視窗整合正常

## 下一步

用戶確認採用哪個方案後開始實作。
