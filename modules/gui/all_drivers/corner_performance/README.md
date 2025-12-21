# 全車手彎道性能分析模組
All Drivers Corner Performance Analysis Module

## 📋 模組概述

基於 Function 47 的 CLI 分析結果，提供全車手在不同彎道類型的速度性能視覺化分析。

### 主要功能
- ✅ 低速彎性能分析 (< 100 km/h)
- ✅ 中速彎性能分析 (100-200 km/h)
- ✅ 高速彎性能分析 (> 200 km/h)
- ✅ XY 散點圖視覺化（進彎速度 vs 出彎速度）
- ✅ 彎中心速度色階顯示
- ✅ API-first 數據載入
- ✅ UniversalDataLoader 架構
- ✅ MDI 視窗管理

## 🏗️ 模組架構

### 檔案結構
```
all_drivers_corner_performance_analysis/
├── __init__.py                                  # 模組初始化
├── corner_performance_loader.py                 # 數據載入器
├── corner_performance_scatter_widget.py         # 散點圖元件
├── all_drivers_corner_performance_mdi.py        # MDI 視窗
├── demo_1_test_loader.py                        # Demo 1: 測試數據載入
├── demo_2_test_scatter_widget.py                # Demo 2: 測試散點圖
├── demo_3_test_mdi.py                          # Demo 3: 測試 MDI
├── demo_4_test_all_corners.py                  # Demo 4: 完整測試
└── README.md                                    # 本文件
```

### 核心組件

#### 1. CornerPerformanceDataLoader
- **功能**：數據載入和驗證
- **基類**：`UniversalDataLoader`
- **數據來源**：
  - 優先：本地 JSON 檔案
  - 備用：REST API (Function 47)
- **數據格式**：`all_drivers_cornering_analysis_{year}_{race}_{session}.json`

#### 2. CornerPerformanceScatterWidget
- **功能**：散點圖視覺化
- **圖表類型**：Matplotlib 散點圖
- **特色**：
  - X 軸：進彎速度 (entry_50m_speed)
  - Y 軸：出彎速度 (exit_50m_speed)
  - 顏色：彎中心速度 (apex_speed) - 紅黃綠色階
  - 標註：車手代碼 (3 字母)

#### 3. AllDriversCornerPerformanceMDI
- **功能**：MDI 視窗管理
- **基類**：`UniversalAnalysisMDI`
- **整合**：載入器 + 散點圖元件

## 🎯 開發原則遵循

### ✅ 原則 1：禁止幻覺編碼
- 所有方法調用前已驗證存在
- 參考 `all_drivers_brake_performance_analysis` 實現

### ✅ 原則 2：模組資料夾優先
- 複用 `UniversalDataLoader` 基類
- 複用 `UniversalAnalysisMDI` 基類
- 參考煞車性能模組架構

### ✅ 原則 3：通用模組優先
- 使用 `UniversalDataLoader` 處理數據流
- 使用 `AnalysisMDIConfig` 註冊模組
- 遵循標準 MDI 架構模式

### ✅ 原則 4：多國語言化
- 所有用戶可見字串使用 `tr()` 包裹
- 無 emoji 使用

### ✅ 原則 5：日誌輸出
- 使用 `print()` 輸出調試資訊
- 自動導出到日誌檔案

## 🚀 快速開始

### Demo 測試執行

#### Demo 1: 測試數據載入器
```powershell
cd "modules/gui/all_drivers_corner_performance analysis"
python demo_1_test_loader.py
```

**測試項目**：
- ✅ 載入本地 JSON 檔案
- ✅ 驗證數據格式
- ✅ 檢查數據結構
- ✅ 顯示前 3 位車手數據

#### Demo 2: 測試散點圖元件
```powershell
python demo_2_test_scatter_widget.py
```

**測試項目**：
- ✅ 創建散點圖元件
- ✅ 載入數據
- ✅ 顯示低速彎散點圖
- ✅ 測試彎道切換功能

#### Demo 3: 測試 MDI 視窗
```powershell
python demo_3_test_mdi.py
```

**測試項目**：
- ✅ 創建 MDI 視窗
- ✅ 初始化模組
- ✅ 載入數據
- ✅ 顯示完整分析介面

#### Demo 4: 完整功能測試
```powershell
python demo_4_test_all_corners.py
```

**測試項目**：
- ✅ 同時顯示三個彎道（標籤頁）
- ✅ 測試數據載入效能
- ✅ 測試圖表切換流暢度
- ✅ 測試批次匯出功能

## 📊 數據格式

### 輸入格式 (JSON)
```json
{
  "success": true,
  "function_id": "47",
  "year": 2024,
  "race": "Japan",
  "session": "R",
  "selected_corners": {
    "low_speed": {
      "corner_number": 11,
      "apex_distance": 2896,
      "avg_apex_speed": 65.8
    },
    "mid_speed": {
      "corner_number": 9,
      "apex_distance": 2446,
      "avg_apex_speed": 126.8
    },
    "high_speed": {
      "corner_number": 13,
      "apex_distance": 3813,
      "avg_apex_speed": 207.4
    }
  },
  "fastest_lap_analysis": {
    "total_drivers": 18,
    "drivers": [
      {
        "driver": "VER",
        "fastest_lap_number": 42,
        "corners": {
          "low_speed_corner_11": {
            "entry_50m_speed": 120.5,
            "apex_speed": 65.8,
            "exit_50m_speed": 95.3
          }
        }
      }
    ]
  }
}
```

## 🎨 視覺化特色

### 散點圖設計
- **X 軸**：進彎速度 (entry_50m_speed) - 顯示車手進彎前的速度
- **Y 軸**：出彎速度 (exit_50m_speed) - 顯示車手出彎後的速度
- **顏色**：彎中心速度 (apex_speed) - 使用 RdYlGn 色階
  - 🔴 紅色：低速（慢）
  - 🟡 黃色：中速
  - 🟢 綠色：高速（快）
- **標註**：車手 3 字母代碼

### 圖表解讀
- **右上角**：進彎快、出彎快 → 整體速度高
- **左下角**：進彎慢、出彎慢 → 整體速度低
- **右下角**：進彎快但出彎慢 → 可能煞車過晚
- **左上角**：進彎慢但出彎快 → 可能煞車過早但加速好

## 🔧 整合到 GUI 主程式

### 註冊模組
```python
# f1t_gui_main.py
from modules.gui.all_drivers_corner_performance_analysis import create_mdi_window

# 在選單中添加
corner_action = analysis_menu.addAction("全車手彎道性能分析")
corner_action.triggered.connect(lambda: self.open_corner_performance_analysis())

def open_corner_performance_analysis(self):
    """開啟彎道性能分析"""
    mdi_window = create_mdi_window(
        parent=self,
        year=self.current_year,
        race=self.current_race,
        session=self.current_session
    )
    
    if mdi_window:
        sub_window = QMdiSubWindow()
        sub_window.setWidget(mdi_window)
        sub_window.setWindowTitle("全車手彎道性能分析")
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
```

## 📝 版本歷史

### v1.0.0 (2025-10-26)
- ✅ 初始版本
- ✅ 實現數據載入器
- ✅ 實現散點圖元件
- ✅ 實現 MDI 視窗
- ✅ 完成 4 個 Demo 測試

## 👥 作者

F1T Team

## 📄 授權

內部專案，不公開發布
