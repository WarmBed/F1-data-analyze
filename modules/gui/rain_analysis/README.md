# F1T 下雨分析模組

基於通用 MDI 架構實現的 F1 比賽降雨天氣分析模組，支援多種天氣數據的視覺化和分析。

## 功能特色

### 數據分析
- **降雨狀態分析** - 追蹤比賽過程中的降雨情況（有雨/無雨）
- **溫度變化監測** - 同時監控氣溫和賽道溫度變化
- **濕度分析** - 追蹤環境濕度變化對比賽的影響
- **風速監測** - 分析風速變化趨勢
- **氣壓分析** - 監控大氣壓力變化

### 圖表類型
- **主要圖表** - 降雨狀態 + 氣溫雙Y軸顯示
- **溫度對比圖** - 氣溫 vs 賽道溫度對比
- **濕度風速圖** - 濕度 + 風速雙Y軸顯示
- **氣壓變化圖** - 單軸氣壓趨勢圖

### 技術特色
- 基於 UniversalAnalysisMDI 架構
- 支援 JSON 數據格式
- PyQt5 原生繪圖引擎
- 模組化設計，易於擴展
- 統一的錯誤處理和除錯機制

## 檔案結構

```
modules/gui/rain_analysis/
├── __init__.py                    # 模組匯出和便利函數
├── rain_analysis_module.py        # 主要模組入口
├── rain_analysis_mdi.py          # 通用下雨分析 MDI 實現
├── rain_analysis_chart_widget.py  # 專用圖表組件
├── rain_data_loader.py           # 專用數據載入器
├── test_rain_analysis.py         # 測試檔案
└── README.md                      # 本說明檔案
```

## 使用方法

### 1. 基本導入和使用

```python
from modules.gui.rain_analysis import RainAnalysisModule, create_rain_analysis_module

# 創建模組實例
rain_module = create_rain_analysis_module()

# 獲取模組資訊
info = rain_module.get_module_info()
print(f"模組名稱: {info['name']}")
print(f"版本: {info['version']}")
```

### 2. 數據載入

```python
from modules.gui.rain_analysis.rain_analysis_mdi import RainAnalysisDataManager

# 創建數據管理器
data_manager = RainAnalysisDataManager()

# 載入 JSON 數據
with open('enhanced_rain_analysis_2025_belgium_R.json', 'r') as f:
    raw_data = json.load(f)
    
# 處理數據
processed_data = data_manager.process_loaded_data(raw_data)

# 獲取摘要統計
summary = data_manager.get_rain_summary()
print(f"總圈數: {summary['total_laps']}")
print(f"降雨圈數: {summary['rain_laps']}")
```

### 3. 圖表組件使用

```python
from modules.gui.rain_analysis.rain_analysis_chart_widget import RainAnalysisChartWidget

# 創建圖表組件（需要 QApplication）
chart_widget = RainAnalysisChartWidget()

# 更新數據
chart_widget.update_chart_data(processed_data)

# 切換圖表類型
chart_widget.switch_chart_type("temperature")  # 溫度對比圖
chart_widget.switch_chart_type("humidity_wind")  # 濕度風速圖
chart_widget.switch_chart_type("pressure")  # 氣壓變化圖
```

## 支援的數據格式

模組支援以下 JSON 數據格式：

### 檔案命名模式
- `enhanced_rain_analysis_{year}_{race}_{session}.json`
- `rain_analysis_{year}_{race}_{session}.json`
- `weather_data_{year}_{race}_{session}.json`

### JSON 結構
```json
{
  "metadata": {
    "analysis_type": "Simplified Rain Status Analysis",
    "year": 2025,
    "race_name": "Belgium",
    "session_type": "R"
  },
  "lap_weather_data": {
    "1": {
      "time": "0 days 02:17:49.312000",
      "temperature": {
        "air_temp": 17.6,
        "track_temp": 25.1
      },
      "weather": {
        "rainfall": false,
        "pressure": 964.8
      },
      "humidity": 82.0,
      "wind": {
        "speed": 1.5,
        "direction": 285.0
      }
    }
  },
  "summary": {
    "total_laps": 44,
    "rain_laps": 0,
    "rain_percentage": 0.0,
    "has_rain_data": true
  }
}
```

## 測試

執行以下命令進行模組測試：

```bash
cd F1-data-analyze
python modules\gui\rain_analysis\test_rain_analysis.py
```

測試包含：
- ✅ 模組導入測試
- ✅ 數據載入測試
- ✅ 圖表組件測試
- ✅ 基礎類別整合測試
- ✅ 模組實例化測試

## 架構說明

### 繼承關係
```
RainAnalysisModule
└── RainAnalysisUniversal
    └── UniversalAnalysisMDI
        └── IAnalysisModule

RainAnalysisDataManager
└── UniversalDataLoader

RainAnalysisChartWidget
└── TelemetryChartWidgetBase
```

### 數據流程
1. **數據註冊** - 向 UniversalDataLoader 註冊 "rain_weather" 類型
2. **檔案搜尋** - 在指定目錄搜尋符合模式的 JSON 檔案
3. **數據驗證** - 驗證 JSON 結構和必要欄位
4. **數據處理** - 轉換為圖表可用格式
5. **圖表繪製** - 使用 PyQt5 原生繪圖

### MDI 整合
- 自動註冊到 UniversalAnalysisMDI 系統
- 支援標準 MDI 視窗管理
- 統一的參數驗證和錯誤處理
- 與其他分析模組無縫整合

## 擴展功能

### 新增圖表類型
1. 在 `RainAnalysisChartWidget` 中新增圖表類型
2. 實現對應的繪製方法
3. 更新控制面板選項

### 新增數據來源
1. 在 `AnalysisConfig` 中新增檔案模式
2. 實現數據格式轉換邏輯
3. 更新驗證邏輯

### 新增分析功能
1. 擴展 `RainAnalysisDataManager` 處理邏輯
2. 新增摘要統計計算
3. 更新圖表數據結構

## 版本資訊

- **版本**: 1.0.0
- **作者**: F1T Team
- **日期**: 2025-09-10
- **授權**: F1T 專案授權

## 相依套件

- PyQt5 - GUI 框架
- Python 3.7+ - 執行環境
- modules.gui.base - 通用基礎類別

## 故障排除

### 常見問題

1. **ModuleNotFoundError**
   - 確認專案路徑正確
   - 檢查 PYTHONPATH 設定

2. **數據載入失敗**
   - 驗證 JSON 檔案格式
   - 檢查檔案路徑和命名

3. **圖表顯示異常**
   - 確認 QApplication 已初始化
   - 檢查數據範圍計算

### 除錯模式
```python
# 啟用除錯輸出
data_manager = RainAnalysisDataManager()
data_manager._debug("除錯訊息")
```

---

如有問題或建議，請聯繫 F1T 開發團隊。
