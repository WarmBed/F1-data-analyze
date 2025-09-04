# 🌧️ 降雨分析模組 (Rain Analysis Module)

這個資料夾包含了所有與F1降雨分析相關的GUI組件和分析工具。

## 📁 檔案結構

```
modules/gui/rain_analysis/
├── __init__.py                           # 套件初始化檔案
├── rain_analysis_module.py               # 主要降雨分析模組
├── rain_analysis_widget.py               # 降雨分析基礎Widget
├── rain_analysis_chart_widget.py         # 降雨分析圖表Widget
├── rain_analysis_dual_axis_widget.py     # 雙Y軸降雨分析Widget
├── rain_analysis_universal_widget.py     # 通用降雨分析Widget
├── rain_chart_utils.py                   # 降雨圖表工具類
├── rain_intensity_analyzer_json.py       # 降雨強度分析器(JSON版)
├── rain_intensity_analyzer_json_fixed.py # 修復版降雨強度分析器
└── README.md                             # 本說明檔案
```

## 🎯 主要功能

### 1. RainAnalysisModule
- 主要的降雨分析模組
- 整合所有降雨分析功能
- 支援通用圖表系統
- 具備緩存機制

### 2. 圖表組件
- **RainAnalysisWidget**: 基礎降雨分析圖表
- **RainAnalysisChartWidget**: 專門的降雨圖表組件
- **RainAnalysisDualAxisWidget**: 雙Y軸降雨數據視覺化
- **RainAnalysisUniversalWidget**: 通用降雨分析組件

### 3. 工具類
- **WeatherChartFormatter**: 天氣圖表格式化工具
- **rain_intensity_analyzer_json**: 降雨強度分析核心邏輯

## 🔧 使用方式

### 基本用法
```python
from modules.gui.rain_analysis import RainAnalysisModule

# 創建降雨分析模組
rain_module = RainAnalysisModule(
    year=2025,
    race="Japan", 
    session="R"
)
```

### 在GUI中使用
```python
from modules.gui.rain_analysis.rain_analysis_module import RainAnalysisModule

# 在MDI中創建降雨分析視窗
rain_widget = RainAnalysisModule(
    year=params['year'],
    race=params['race'],
    session=params['session']
)
```

## 📊 數據流程

1. **數據載入**: 從FastF1或本地緩存載入天氣數據
2. **分析處理**: 計算降雨強度、時間分布等
3. **視覺化**: 使用通用圖表系統繪製降雨分析圖表
4. **緩存管理**: 自動管理分析結果緩存

## 🔄 與主系統整合

- 透過 `f1t_gui_main.py` 中的選單項目 `[RAIN] 降雨分析` 啟動
- 支援MDI(多文檔介面)架構
- 與通用圖表系統整合
- 遵循架構文檔規範

## ⚙️ 配置選項

- 支援不同賽季、賽事、練習賽/排位賽/正賽
- 可調整降雨閾值和分析參數
- 支援JSON格式的分析結果輸出
- 具備24小時緩存過期機制

## 🐛 故障排除

如果遇到引入錯誤，請確認：
1. 主程式中的引入路徑已更新為 `modules.gui.rain_analysis.rain_analysis_module`
2. 相對引入路徑正確設定
3. `__init__.py` 檔案存在且內容正確

## 📝 更新日誌

- **v1.0.0**: 初始版本，整合所有降雨分析相關檔案
- 支援通用圖表系統
- 完善的緩存機制
- MDI架構支援
