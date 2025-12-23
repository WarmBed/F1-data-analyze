# All Drivers Max Speed Analysis Module

## 概述

全車手最高速度分析模組，使用 **F121 (Straight Line All Laps Analysis)** API 獲取所有車手在整場賽事中的最高速度統計數據。

## 功能

- 顯示所有車手的最高速度統計（全部圈數）
- 包含速度中位數、標準差
- 100→300 km/h 加速時間統計
- 到達最高速度的時間統計
- 依據 `absolute_max_speed_kmh` 降序排列

## 文件結構

```
all_drivers_max_speed_analysis/
├── __init__.py                           # 模組初始化和導出
├── register_module.py                    # 模組工廠註冊
├── max_speed_data_loader.py              # 數據載入器 (F121 API)
├── all_drivers_max_speed_table_widget.py # 表格顯示元件
├── all_drivers_max_speed_mdi.py          # MDI 視窗整合
├── all_drivers_max_speed_module.py       # IAnalysisModule 實作
└── README.md                             # 本文件
```

## 數據來源

- **API**: F121 (Straight Line All Laps Analysis)
- **端點**: `POST /api/v2/analysis/execute`
- **參數**: 
  - `function_id`: 121
  - `year`: 賽季年份
  - `race`: 賽事名稱
  - `session`: 會話類型 (FP1/FP2/FP3/Q/R)

## 表格欄位

| 欄位 | 說明 |
|------|------|
| Rank | 排名（依最高速度） |
| Driver | 車手代碼 |
| Max Speed (km/h) | 絕對最高速度 |
| Max Speed Lap | 達到最高速度的圈數 |
| Median Speed (km/h) | 速度中位數 |
| Speed StdDev | 速度標準差 |
| Accel 100-300 (s) | 100→300 km/h 加速時間中位數 |
| Time to Max (s) | 到達最高速度時間中位數 |

## 使用方式

### GUI 選單

1. 開啟 F1T GUI
2. 進入 `Historical Analysis` → `Speed & Corner Analysis`
3. 點擊 `All Drivers Max Speed`

### 程式呼叫

```python
from modules.gui.all_drivers_max_speed_analysis import AllDriversMaxSpeedMDI

# 創建 MDI 實例
mdi = AllDriversMaxSpeedMDI(parent=self)
mdi.current_year = "2025"
mdi.current_race = "Japan"
mdi.current_session = "R"

# 初始化並載入數據
mdi.initialize_module()
mdi.load_initial_data()
```

## F121 JSON 結構

```json
{
  "year": 2025,
  "race": "Japan",
  "session_type": "R",
  "analysis_type": "straight_line_all_laps",
  "drivers": [
    {
      "driver": "VER",
      "total_laps": 52,
      "absolute_max_speed_kmh": 318.5,
      "absolute_max_speed_lap": 15,
      "speed_stats": {
        "max": 318.5,
        "min": 298.2,
        "median": 312.4,
        "std_dev": 4.3
      },
      "acceleration_100_300_stats": {
        "median": 5.82,
        "std_dev": 0.18
      },
      "time_to_max_speed_stats": {
        "median": 7.15,
        "std_dev": 0.25
      }
    }
  ]
}
```

## 版本

- **v1.0.0** (2025-10-20): 初始版本

## 作者

F1T Team
