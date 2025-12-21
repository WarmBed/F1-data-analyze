# All Drivers Brake Performance Analysis Module

全車手煞車性能分析模組

## 📋 模組概述

此模組分析所有車手的煞車性能，包括：
- 最大減速度 (m/s²)
- 煞車起始/結束速度 (km/h)
- 煞車距離 (m)
- 煞車時間 (s)

## 🎯 功能特點

- 基於 CLI Function 34 (Brake Performance Analyzer)
- 使用 UniversalAnalysisMDI 架構
- QTableWidget 表格展示
- 支援點擊排序
- 車隊配色背景

## 📊 數據來源

- **CLI 功能**: Function 34
- **JSON 格式**: `brake_performance_{year}_{race}_{session}.json`
- **API 端點**: `/api/v2/analysis/execute?function_id=34`

## 🏗️ 架構設計

```
all_drivers_brake_performance_analysis/
├── __init__.py                                    # 模組初始化
├── all_drivers_brake_performance_module.py        # IAnalysisModule 實現
├── all_drivers_brake_performance_mdi.py           # UniversalAnalysisMDI 實現
├── all_drivers_brake_performance_table_widget.py  # 表格元件
├── brake_performance_loader.py                    # UniversalDataLoader 實現
├── register_module.py                             # 模組註冊
└── README.md                                      # 本文件
```

## 📝 使用範例

### CLI 執行
```powershell
python f1_analysis_modular_main.py -f 34 -y 2025 -r Australia -s R
```

### GUI 使用
```python
from modules.gui.all_drivers_brake_performance_analysis import AllDriversBrakePerformanceModule

module = AllDriversBrakePerformanceModule(year=2025, race="Australia", session="R")
module.initialize_module()
widget = module.get_widget()
```

## 🔧 技術細節

- **基礎類別**: UniversalAnalysisMDI
- **數據載入器**: BrakePerformanceDataLoader
- **視覺化**: QTableWidget + Custom Delegate
- **國際化**: 支援 tr() 翻譯

## 📅 版本歷史

- **1.0.0** (2025-10-18) - 初始版本，複製自 Straight Line Speed Analysis

## 👥 作者

F1T Team

## 📄 授權

與主專案相同
