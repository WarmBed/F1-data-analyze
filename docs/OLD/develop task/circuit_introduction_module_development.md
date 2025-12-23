# 任務：Circuit Introduction Module（賽道講解模組）完整開發

- **目標**：建立一個全新的 F1 賽道講解與資訊展示系統，整合 f1-circuits-master 地理資料與 FastF1 遙測數據，提供專業的賽道特性分析與視覺化展示。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-11-09
- **模組類型**：CLI + GUI 雙重架構模組
- **功能編號**：Function ID 53 (F53)

---

## 📋 專案概述

### 核心目標
建立一個綜合性的賽道講解模組，整合多元數據源，提供：
1. **賽道地理資訊**：經緯度、海拔、賽道長度、路線座標
2. **賽道特性分析**：彎道分佈、直線速度區間、高低差分析
3. **歷史數據統計**：單圈紀錄、平均速度、最快圈速車手
4. **視覺化展示**：賽道地圖、高程圖、速度熱力圖、彎道難度分析
5. **多語言支援**：中英文切換，符合 F1T 國際化標準

### 資料來源整合
```
┌─────────────────────────────────────────────────────────────┐
│                   Circuit Introduction Module                │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
        │ f1-circuits- │ │ FastF1 │ │  OpenF1    │
        │   master     │ │  API   │ │   API      │
        │  (GeoJSON)   │ │        │ │            │
        └──────────────┘ └────────┘ └────────────┘
                │             │             │
        ┌───────▼─────────────▼─────────────▼───────┐
        │    CLI Backend (Function 53)              │
        │    - 資料抓取與處理                          │
        │    - JSON 結構化輸出                        │
        │    - 緩存管理                               │
        └───────────────┬───────────────────────────┘
                        │
                ┌───────▼────────┐
                │  FastAPI       │
                │  Endpoint      │
                │  /api/v2/      │
                │  circuit/info  │
                └───────┬────────┘
                        │
        ┌───────────────▼───────────────┐
        │  GUI Frontend                 │
        │  - CircuitIntroductionMDI     │
        │  - CircuitMapWidget           │
        │  - CircuitDataLoader          │
        └───────────────────────────────┘
```

---

## 🏗️ 架構設計

### CLI 模組架構（Backend）

#### 1. 功能映射註冊
**檔案位置**：`CLI_modules/cli/core/function_mapper.py`

```python
# 在 function_mapping 字典中新增
53: self._execute_circuit_introduction_analysis,  # 賽道講解與資訊展示 (F53) (2025-11-09)
```

#### 2. CLI 分析實現
**檔案位置**：`CLI_modules/cli/analyzer/circuit_introduction_analysis.py` (新建)

**核心功能**：
```python
def run_circuit_introduction_analysis(year, race_name, session_type, **kwargs):
    """
    執行賽道講解分析
    
    參數:
        year (int): 賽季年份
        race_name (str): 賽事名稱（如 "Japan", "Italy"）
        session_type (str): 會話類型（"R", "Q", "FP1"等）
        
    返回:
        dict: 包含以下結構的字典
        {
            "success": True,
            "message": "賽道分析完成",
            "function_id": "53",
            "circuit_info": {
                "basic_info": { ... },      # 基本資訊
                "geographic_data": { ... }, # 地理資料
                "track_characteristics": { ... }, # 賽道特性
                "historical_data": { ... }, # 歷史數據
                "telemetry_analysis": { ... }, # 遙測分析
                "visualization_data": { ... }  # 視覺化資料
            },
            "metadata": { ... }
        }
    """
```

**資料處理流程**：
1. **載入 GeoJSON 資料**：從 `json/f1-circuits-master/` 讀取賽道資料
2. **抓取 FastF1 數據**：獲取該賽道的最快圈速、車手遙測數據
3. **計算賽道特性**：
   - 彎道數量與分類（低速/中速/高速彎）
   - 直線長度與速度區間
   - 高程變化分析（基於座標計算）
   - DRS 區域標註
4. **歷史數據統計**：
   - 賽道單圈紀錄（最快圈速）
   - 平均圈速與標準差
   - 前三名車手統計
5. **輸出 JSON**：結構化資料存入 `json/circuit_introduction_{race}_{year}.json`

#### 3. JSON 輸出結構
```json
{
    "success": true,
    "message": "賽道分析完成",
    "function_id": "53",
    "circuit_info": {
        "basic_info": {
            "id": "jp-1962",
            "name": "Suzuka International Racing Course",
            "name_zh": "鈴鹿國際賽車場",
            "location": "Suzuka, Japan",
            "location_zh": "日本鈴鹿",
            "opened": 1962,
            "first_gp": 1987,
            "length_meters": 5807,
            "length_km": 5.807,
            "latitude": 34.844,
            "longitude": 136.534,
            "altitude_meters": 60,
            "lap_record": {
                "time": "1:30.983",
                "driver": "Lewis Hamilton",
                "year": 2019,
                "team": "Mercedes"
            }
        },
        "geographic_data": {
            "bbox": [136.521928, 34.838956, 136.543422, 34.848374],
            "coordinates": [
                [136.540283, 34.843344],
                [136.541609, 34.842034],
                // ... 160+ 個座標點
            ],
            "elevation_profile": [
                {"distance": 0, "elevation": 60},
                {"distance": 500, "elevation": 65},
                // ... 高程剖面數據
            ],
            "zoom_level": 15
        },
        "track_characteristics": {
            "total_corners": 18,
            "corner_classification": {
                "slow_speed": 4,    // < 100 km/h
                "medium_speed": 8,  // 100-200 km/h
                "high_speed": 6     // > 200 km/h
            },
            "famous_corners": [
                {
                    "number": 1,
                    "name": "Turn 1 (First Corner)",
                    "name_zh": "第一彎",
                    "type": "medium_speed",
                    "difficulty": "medium",
                    "description": "Tight right-hander after the start/finish straight",
                    "description_zh": "起跑直線後的緊急右彎"
                },
                {
                    "number": 8,
                    "name": "Turn 8 (Degner Curve)",
                    "name_zh": "登納彎",
                    "type": "medium_speed",
                    "difficulty": "high",
                    "description": "Double-apex right-hander",
                    "description_zh": "雙頂點右彎"
                },
                {
                    "number": 15,
                    "name": "Turn 15 (Spoon Curve)",
                    "name_zh": "湯匙彎",
                    "type": "high_speed",
                    "difficulty": "high",
                    "description": "Long, sweeping left-hander",
                    "description_zh": "長距離高速左彎"
                },
                {
                    "number": 17,
                    "name": "Turn 17 (130R)",
                    "name_zh": "130R彎",
                    "type": "high_speed",
                    "difficulty": "very_high",
                    "description": "One of F1's most challenging corners",
                    "description_zh": "F1最具挑戰性的彎道之一"
                }
            ],
            "straight_sections": [
                {
                    "name": "Start/Finish Straight",
                    "name_zh": "起跑直線",
                    "length_meters": 735,
                    "top_speed_kmh": 315,
                    "drs_zone": true
                },
                {
                    "name": "Back Straight",
                    "name_zh": "後直線",
                    "length_meters": 560,
                    "top_speed_kmh": 290,
                    "drs_zone": false
                }
            ],
            "elevation_change": {
                "max_elevation": 65,
                "min_elevation": 55,
                "total_change": 10,
                "description": "Relatively flat circuit with minor elevation changes",
                "description_zh": "相對平坦的賽道，高低差較小"
            },
            "track_surface": "Asphalt",
            "track_direction": "Clockwise",
            "track_type": "Permanent road course"
        },
        "historical_data": {
            "session_info": {
                "year": 2025,
                "race_name": "Japanese Grand Prix",
                "race_name_zh": "日本大獎賽",
                "session_type": "Race",
                "session_date": "2025-04-06",
                "total_laps": 53
            },
            "fastest_lap_stats": {
                "fastest_driver": "Max Verstappen",
                "fastest_time": "1:31.447",
                "fastest_lap_number": 42,
                "average_lap_time": "1:32.856",
                "lap_time_std_dev": 1.234,
                "top_3_drivers": [
                    {"driver": "VER", "time": "1:31.447", "team": "Red Bull Racing"},
                    {"driver": "LEC", "time": "1:31.682", "team": "Ferrari"},
                    {"driver": "NOR", "time": "1:31.901", "team": "McLaren"}
                ]
            },
            "speed_statistics": {
                "max_speed_kmh": 318.5,
                "max_speed_driver": "VER",
                "max_speed_location": "Start/Finish Straight",
                "average_top_speed": 312.4,
                "min_speed_kmh": 85.2,
                "min_speed_location": "Turn 11 (Hairpin)"
            },
            "weather_conditions": {
                "temperature_celsius": 24,
                "track_temp_celsius": 38,
                "humidity_percent": 65,
                "rainfall": false,
                "conditions": "Dry"
            }
        },
        "telemetry_analysis": {
            "throttle_zones": [
                {"section": "Start/Finish Straight", "full_throttle_percent": 98.5},
                {"section": "Turn 1-2 Complex", "full_throttle_percent": 35.2},
                {"section": "Spoon Curve", "full_throttle_percent": 72.8}
            ],
            "brake_points": [
                {
                    "corner": "Turn 1",
                    "brake_distance_meters": 120,
                    "brake_pressure_bar": 145,
                    "g_force": -5.2
                },
                {
                    "corner": "Turn 11 (Hairpin)",
                    "brake_distance_meters": 95,
                    "brake_pressure_bar": 150,
                    "g_force": -5.5
                }
            ],
            "gear_distribution": {
                "1st_gear": 2.5,
                "2nd_gear": 8.3,
                "3rd_gear": 15.7,
                "4th_gear": 22.1,
                "5th_gear": 28.4,
                "6th_gear": 18.6,
                "7th_gear": 4.4,
                "8th_gear": 0.0
            }
        },
        "visualization_data": {
            "track_map_svg": "base64_encoded_svg_data",
            "elevation_chart_data": [...],
            "speed_heatmap_data": [...],
            "corner_difficulty_radar": [...]
        }
    },
    "metadata": {
        "generated_at": "2025-11-09T10:30:00Z",
        "data_sources": ["f1-circuits-master", "FastF1", "OpenF1"],
        "analysis_version": "1.0.0",
        "cache_used": false
    }
}
```

---

### GUI 模組架構（Frontend）

#### 1. 模組結構
**檔案位置**：`modules/gui/circuit_introduction/`

```
circuit_introduction/
├── __init__.py
├── circuit_introduction_mdi.py        # MDI 視窗管理
├── circuit_introduction_module.py     # 主要分析模組
├── circuit_data_loader.py             # 資料載入器（繼承 UniversalDataLoader）
├── circuit_map_widget.py              # 賽道地圖視覺化
├── circuit_info_widget.py             # 資訊展示面板
└── circuit_stats_widget.py            # 統計圖表元件
```

#### 2. MDI 視窗實現
**檔案**：`circuit_introduction_mdi.py`

**參考範本**：`modules/gui/rain_analysis/rain_analysis_mdi.py`

```python
from PyQt5.QtWidgets import QMdiSubWindow
from modules.gui.circuit_introduction.circuit_introduction_module import CircuitIntroductionModule

class CircuitIntroductionMDI(QMdiSubWindow):
    """賽道講解 MDI 視窗"""
    
    def __init__(self, year, race_name, session_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("賽道講解與資訊"))
        
        # 初始化主模組
        self.circuit_module = CircuitIntroductionModule(
            year=year,
            race_name=race_name,
            session_type=session_type,
            parent=self
        )
        
        self.setWidget(self.circuit_module)
        self.resize(1200, 800)
```

#### 3. 主模組實現
**檔案**：`circuit_introduction_module.py`

**核心功能**：
- 繼承 `QWidget`
- 使用 `CircuitDataLoader` 載入資料
- 多分頁展示：
  - Tab 1: 賽道地圖與基本資訊
  - Tab 2: 賽道特性分析
  - Tab 3: 歷史數據統計
  - Tab 4: 遙測數據分析

```python
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from modules.gui.circuit_introduction.circuit_data_loader import CircuitDataLoader
from modules.gui.circuit_introduction.circuit_map_widget import CircuitMapWidget
from modules.gui.circuit_introduction.circuit_info_widget import CircuitInfoWidget

class CircuitIntroductionModule(QWidget):
    """賽道講解主模組"""
    
    def __init__(self, year, race_name, session_type, parent=None):
        super().__init__(parent)
        self.year = year
        self.race_name = race_name
        self.session_type = session_type
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 創建分頁控制項
        self.tab_widget = QTabWidget()
        
        # Tab 1: 賽道地圖
        self.map_widget = CircuitMapWidget()
        self.tab_widget.addTab(self.map_widget, self.tr("賽道地圖"))
        
        # Tab 2: 賽道資訊
        self.info_widget = CircuitInfoWidget()
        self.tab_widget.addTab(self.info_widget, self.tr("賽道資訊"))
        
        # Tab 3: 統計數據
        self.stats_widget = CircuitStatsWidget()
        self.tab_widget.addTab(self.stats_widget, self.tr("統計數據"))
        
        layout.addWidget(self.tab_widget)
    
    def _load_data(self):
        """載入資料"""
        self.data_loader = CircuitDataLoader(
            cli_function=53,
            debug_enabled=True
        )
        
        # 連接信號
        self.data_loader.load_completed.connect(self._on_data_loaded)
        self.data_loader.load_error.connect(self._on_error)
        
        # 開始載入
        self.data_loader.load_analysis_data(
            year=self.year,
            race=self.race_name,
            session=self.session_type
        )
    
    def _on_data_loaded(self, data):
        """資料載入完成"""
        circuit_info = data.get("circuit_info", {})
        
        # 更新各個 Widget
        self.map_widget.update_map(circuit_info)
        self.info_widget.update_info(circuit_info)
        self.stats_widget.update_stats(circuit_info)
```

#### 4. 資料載入器實現
**檔案**：`circuit_data_loader.py`

**參考範本**：`modules/gui/rain_analysis/rain_analysis_module.py` 中的 `RainAnalysisDataManager`

```python
from modules.gui.base.universal_data_loader import UniversalDataLoader

class CircuitDataLoader(UniversalDataLoader):
    """賽道講解資料載入器"""
    
    def __init__(self, cli_function=53, debug_enabled=True):
        super().__init__(
            cli_function=cli_function,
            debug_enabled=debug_enabled
        )
    
    def _validate_data_format(self, raw_data):
        """驗證 JSON 資料格式"""
        if not isinstance(raw_data, dict):
            return False
        
        if "circuit_info" not in raw_data:
            return False
        
        circuit_info = raw_data["circuit_info"]
        required_keys = ["basic_info", "geographic_data", "track_characteristics"]
        
        return all(key in circuit_info for key in required_keys)
    
    def _transform_data_for_display(self, raw_data):
        """轉換資料格式以供 GUI 顯示"""
        # 可以在這裡進行額外的資料處理
        return raw_data
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取數據或手動執行 CLI")
        return False
```

#### 5. 賽道地圖 Widget
**檔案**：`circuit_map_widget.py`

**核心功能**：
- 使用 Matplotlib 繪製賽道路線
- 標註彎道位置與名稱
- 顯示 DRS 區域
- 速度熱力圖疊加
- 支援縮放與拖曳

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class CircuitMapWidget(QWidget):
    """賽道地圖視覺化 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 創建 Matplotlib 圖表
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        layout.addWidget(self.canvas)
    
    def update_map(self, circuit_info):
        """更新賽道地圖"""
        self.ax.clear()
        
        # 獲取座標資料
        geographic_data = circuit_info.get("geographic_data", {})
        coordinates = geographic_data.get("coordinates", [])
        
        if not coordinates:
            self.ax.text(0.5, 0.5, "無賽道資料", ha='center', va='center')
            self.canvas.draw()
            return
        
        # 繪製賽道路線
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        self.ax.plot(lons, lats, 'b-', linewidth=3, label='賽道路線')
        
        # 標註起點/終點
        self.ax.plot(lons[0], lats[0], 'go', markersize=10, label='起點/終點')
        
        # 標註著名彎道
        track_chars = circuit_info.get("track_characteristics", {})
        famous_corners = track_chars.get("famous_corners", [])
        
        for corner in famous_corners:
            # 這裡需要計算彎道位置（基於座標索引）
            # 簡化示範，實際需要更精確的位置計算
            pass
        
        self.ax.set_xlabel('經度 (Longitude)')
        self.ax.set_ylabel('緯度 (Latitude)')
        self.ax.set_title(circuit_info.get("basic_info", {}).get("name", "賽道地圖"))
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        self.canvas.draw()
```

---

## 🔌 API 整合

### FastAPI 端點
**檔案位置**：`api/routers/circuit_analysis.py` (新建)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

router = APIRouter(prefix="/api/v2/circuit", tags=["Circuit Analysis"])

class CircuitInfoRequest(BaseModel):
    year: int
    race_name: str
    session_type: str = "R"
    force_refresh: bool = False

@router.post("/info")
async def get_circuit_info(request: CircuitInfoRequest):
    """
    獲取賽道講解與資訊
    
    參數:
        - year: 賽季年份
        - race_name: 賽事名稱
        - session_type: 會話類型（預設 "R"）
        - force_refresh: 是否強制刷新（忽略緩存）
    
    返回:
        完整的賽道資訊 JSON
    """
    try:
        # 檢查緩存
        if not request.force_refresh:
            cached_data = check_circuit_cache(
                request.year, 
                request.race_name
            )
            if cached_data:
                return cached_data
        
        # 調用 CLI 後端
        from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
        
        mapper = F1AnalysisFunctionMapper()
        result = await asyncio.to_thread(
            mapper.execute_function,
            function_id=53,
            year=request.year,
            race_name=request.race_name,
            session_type=request.session_type
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=result.get("message", "賽道分析失敗")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## ✅ 開發檢查清單

### Phase 1: CLI 後端開發
- [ ] **步驟 1.1**：在 `function_mapper.py` 註冊 Function 53
- [ ] **步驟 1.2**：建立 `circuit_introduction_analysis.py`
- [ ] **步驟 1.3**：實現 GeoJSON 資料讀取功能
- [ ] **步驟 1.4**：整合 FastF1 遙測數據抓取
- [ ] **步驟 1.5**：計算賽道特性（彎道分類、速度區間等）
- [ ] **步驟 1.6**：實現 JSON 結構化輸出
- [ ] **步驟 1.7**：測試 CLI 獨立執行：
  ```powershell
  python f1_analysis_modular_main.py -f 53 -y 2025 -r Japan -s R
  ```
- [ ] **步驟 1.8**：驗證 JSON 輸出結構完整性

### Phase 2: API 端點開發
- [ ] **步驟 2.1**：建立 `api/routers/circuit_analysis.py`
- [ ] **步驟 2.2**：實現 `/api/v2/circuit/info` 端點
- [ ] **步驟 2.3**：整合緩存機制
- [ ] **步驟 2.4**：測試 API 端點：
  ```powershell
  # 啟動 API 服務器
  python refactored_api.py
  
  # 測試 API 調用
  curl -X POST http://localhost:8000/api/v2/circuit/info \
    -H "Content-Type: application/json" \
    -d '{"year": 2025, "race_name": "Japan", "session_type": "R"}'
  ```

### Phase 3: GUI 前端開發
- [ ] **步驟 3.1**：建立 `modules/gui/circuit_introduction/` 資料夾結構
- [ ] **步驟 3.2**：實現 `CircuitDataLoader`（繼承 `UniversalDataLoader`）
- [ ] **步驟 3.3**：實現 `CircuitIntroductionModule` 主模組
- [ ] **步驟 3.4**：實現 `CircuitIntroductionMDI` 視窗管理
- [ ] **步驟 3.5**：實現 `CircuitMapWidget` 賽道地圖
- [ ] **步驟 3.6**：實現 `CircuitInfoWidget` 資訊面板
- [ ] **步驟 3.7**：實現 `CircuitStatsWidget` 統計圖表
- [ ] **步驟 3.8**：整合多語言支援（`tr()` 函數）

### Phase 4: GUI 整合測試
- [ ] **步驟 4.1**：在 `f1t_gui_main.py` 新增選單項目
- [ ] **步驟 4.2**：測試模組啟動與視窗初始化
- [ ] **步驟 4.3**：測試 API 資料載入流程
- [ ] **步驟 4.4**：測試本地 JSON 後備機制
- [ ] **步驟 4.5**：測試多語言切換功能
- [ ] **步驟 4.6**：測試圖表交互功能（縮放、拖曳等）

### Phase 5: 完整功能測試
- [ ] **步驟 5.1**：測試多個賽道（Japan, Italy, Monaco, Spa）
- [ ] **步驟 5.2**：測試不同年份資料
- [ ] **步驟 5.3**：測試錯誤處理（無資料、API 失敗等）
- [ ] **步驟 5.4**：性能測試（載入時間、記憶體使用）
- [ ] **步驟 5.5**：使用者體驗測試
- [ ] **步驟 5.6**：撰寫使用者文檔

---

## 🧪 測試計畫

### 單元測試
```powershell
# CLI 模組測試
python -m pytest tests/test_circuit_introduction_cli.py -v

# GUI 模組測試
python -m pytest tests/test_circuit_introduction_gui.py -v

# API 端點測試
python -m pytest tests/test_circuit_api.py -v
```

### 整合測試腳本
**檔案位置**：`test_circuit_introduction_integration.py` (新建)

```python
"""
賽道講解模組整合測試
"""
import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.circuit_introduction.circuit_introduction_mdi import CircuitIntroductionMDI

def test_circuit_introduction_module():
    """測試賽道講解模組"""
    app = QApplication(sys.argv)
    
    # 測試案例：2025 日本大獎賽
    circuit_window = CircuitIntroductionMDI(
        year=2025,
        race_name="Japan",
        session_type="R"
    )
    
    circuit_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_circuit_introduction_module()
```

### 手動測試檢查清單
- [ ] ✅ CLI 可獨立執行並生成 JSON
- [ ] ✅ API 端點回應正確
- [ ] ✅ GUI 模組可正常啟動
- [ ] ✅ 賽道地圖正確顯示
- [ ] ✅ 資訊面板資料完整
- [ ] ✅ 統計圖表正確繪製
- [ ] ✅ 多語言切換正常
- [ ] ✅ 錯誤處理正確觸發

---

## 📊 資料流程圖

```
使用者操作
    │
    ▼
[GUI Menu] → 選擇「賽道講解」
    │
    ▼
[CircuitIntroductionMDI] 創建 MDI 視窗
    │
    ▼
[CircuitIntroductionModule] 初始化主模組
    │
    ▼
[CircuitDataLoader] 開始載入資料
    │
    ├─→ [檢查本地 JSON] → 存在？
    │       │ Yes: 讀取檔案
    │       │ No: ↓
    │       ▼
    ├─→ [API 請求] → POST /api/v2/circuit/info
    │       │
    │       ▼
    │   [FastAPI Server]
    │       │
    │       ├─→ [檢查緩存] → 存在？
    │       │       │ Yes: 返回緩存
    │       │       │ No: ↓
    │       │       ▼
    │       ├─→ [調用 CLI Backend] → Function 53
    │       │       │
    │       │       ▼
    │       │   [circuit_introduction_analysis.py]
    │       │       │
    │       │       ├─→ 讀取 GeoJSON
    │       │       ├─→ 抓取 FastF1 資料
    │       │       ├─→ 計算賽道特性
    │       │       ├─→ 生成 JSON
    │       │       │
    │       │       ▼
    │       │   返回分析結果
    │       │       │
    │       │       ▼
    │       └─→ [返回 API 回應]
    │               │
    │               ▼
    └─→ [資料驗證] → _validate_data_format()
            │
            ▼
        [資料轉換] → _transform_data_for_display()
            │
            ▼
        [觸發信號] → load_completed.emit(data)
            │
            ▼
        [更新 GUI]
            │
            ├─→ [CircuitMapWidget] 繪製賽道地圖
            ├─→ [CircuitInfoWidget] 顯示資訊
            └─→ [CircuitStatsWidget] 繪製統計圖表
```

---

## 🎨 UI 設計規範

### 視窗布局
```
┌─────────────────────────────────────────────────────────────┐
│  賽道講解與資訊 - Suzuka International Racing Course       │
├─────────────────────────────────────────────────────────────┤
│  [賽道地圖] [賽道資訊] [統計數據] [遙測分析]              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Tab 1: 賽道地圖                                            │
│   ┌───────────────────────────────────────────────────┐    │
│   │                                                     │    │
│   │              [賽道路線視覺化]                        │    │
│   │                                                     │    │
│   │   • 起點/終點標記                                   │    │
│   │   • 彎道編號與名稱                                  │    │
│   │   • DRS 區域標註                                    │    │
│   │   • 速度熱力圖疊加                                  │    │
│   │                                                     │    │
│   └───────────────────────────────────────────────────┘    │
│                                                               │
│   基本資訊面板：                                             │
│   ┌───────────────────────────────────────────────────┐    │
│   │  名稱：鈴鹿國際賽車場                                │    │
│   │  長度：5.807 km                                     │    │
│   │  彎道數：18                                         │    │
│   │  圈速紀錄：1:30.983 (Hamilton, 2019)               │    │
│   └───────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 色彩方案
- **賽道路線**：藍色 (`#1E88E5`)
- **起點/終點**：綠色 (`#43A047`)
- **高速彎**：紅色 (`#E53935`)
- **中速彎**：橙色 (`#FB8C00`)
- **低速彎**：黃色 (`#FDD835`)
- **DRS 區域**：紫色半透明 (`#9C27B0` + alpha 0.3)

---

## 🌐 多語言支援

### 翻譯鍵值對照表
| 中文 | 英文 | 翻譯鍵 |
|-----|------|--------|
| 賽道講解與資訊 | Circuit Introduction | `circuit_introduction` |
| 賽道地圖 | Track Map | `track_map` |
| 賽道資訊 | Circuit Information | `circuit_info` |
| 統計數據 | Statistics | `statistics` |
| 遙測分析 | Telemetry Analysis | `telemetry_analysis` |
| 基本資訊 | Basic Information | `basic_info` |
| 賽道長度 | Track Length | `track_length` |
| 彎道數量 | Number of Corners | `corner_count` |
| 圈速紀錄 | Lap Record | `lap_record` |
| 高速彎 | High-Speed Corner | `high_speed_corner` |
| 中速彎 | Medium-Speed Corner | `medium_speed_corner` |
| 低速彎 | Low-Speed Corner | `low_speed_corner` |
| 直線區間 | Straight Section | `straight_section` |
| DRS 區域 | DRS Zone | `drs_zone` |
| 高程變化 | Elevation Change | `elevation_change` |

---

## 📝 開發注意事項

### ⚠️ 必須遵守的原則

#### 反幻覺編碼五原則
1. **禁止幻覺編碼**：任何方法調用前必須用 `grep_search` 或 `read_file` 驗證
2. **模組資料夾優先**：開發前檢查 `modules/gui/` 是否有類似實現
3. **通用模組優先**：必須使用 `UniversalDataLoader`、`UniversalChartWidget`
4. **模組多國語言化**：所有用戶可見字串使用 `tr()` 包裹
5. **print 輸出會被 logger 導出到 log**

#### API-ONLY 模式政策
- ❌ **禁止 GUI 呼叫 CLI**：絕不允許直接啟動 CLI 進程
- ✅ **僅允許 API 獲取數據**：通過 REST API 獲取分析數據
- ✅ **本地 JSON 讀取**：允許讀取已存在的 JSON 檔案
- ✅ **手動 CLI 執行**：開發時需要新數據，手動執行 CLI 命令

#### 統一架構模式
- **參考範本**：以 `rain_analysis` 為標準範本
- **基礎類別**：繼承 `UniversalDataLoader` 進行資料載入
- **圖表元件**：使用 `UniversalChartWidget` 進行視覺化
- **MDI 管理**：使用 `CustomMdiArea` 管理子視窗

### 開發前檢查清單
- [ ] ✅ 用 `semantic_search` 搜索相關功能是否已存在
- [ ] ✅ 用 `file_search` 檢查 `modules/gui/` 是否有類似模組
- [ ] ✅ 用 `grep_search` 驗證要調用的方法確實存在
- [ ] ✅ 閱讀 `rain_analysis` 的實現作為參考範本
- [ ] ✅ 確認使用 `UniversalDataLoader` 和 `UniversalChartWidget`
- [ ] ❌ 沒有任何假設性編碼或憑空想像的方法調用

---

## 📚 參考資料

### 系統架構參考
- **通用資料載入器**：`modules/gui/base/universal_data_loader.py`
- **通用圖表元件**：`modules/gui/universal_chart_widget.py`
- **Rain Analysis 範本**：`modules/gui/rain_analysis/`
- **CLI 功能映射**：`CLI_modules/cli/core/function_mapper.py`
- **API 路由範例**：`api/routers/rain_analysis.py`

### 資料來源文檔
- **f1-circuits-master**：`json/f1-circuits-master/README.md`
- **FastF1 文檔**：https://docs.fastf1.dev/
- **OpenF1 API**：https://openf1.org/

### 開發指南
- **反幻覺編碼原則**：`.github/copilot-instructions.md`
- **API-ONLY 模式**：`.github/copilot-instructions.md` (Section 4)
- **多語言支援**：`.github/copilot-instructions.md` (i18n Framework)

---

## 🎯 里程碑與時間規劃

### 預估開發時間
- **Phase 1 (CLI 後端)**：4-6 小時
- **Phase 2 (API 端點)**：2-3 小時
- **Phase 3 (GUI 前端)**：6-8 小時
- **Phase 4 (整合測試)**：3-4 小時
- **Phase 5 (完整測試)**：2-3 小時
- **總計**：17-24 小時

### 交付成果
1. ✅ CLI 功能 (Function 53) 可獨立執行
2. ✅ FastAPI 端點 `/api/v2/circuit/info` 正常運作
3. ✅ GUI 模組完整實現並整合至主程式
4. ✅ 多語言支援（中英文）
5. ✅ 完整的測試報告與使用者文檔

---

## 📞 支援與協助

如有開發問題，請參考：
- **系統架構問題**：查閱 `.github/copilot-instructions.md`
- **API 整合問題**：查閱 `api/README.md`
- **GUI 開發問題**：參考 `rain_analysis` 模組實現
- **資料格式問題**：檢查 `json/` 目錄中的範例檔案

---

**文件版本**：1.1.0（已更新可行性調查）  
**最後更新**：2025-11-09  
**狀態**：✅ 可行性驗證完成，準備開發

---

## 🔍 功能可行性調查報告 (2025-11-09)

### 調查範圍
基於用戶需求，對以下功能進行了完整的代碼驗證（遵循反幻覺編碼原則）：

### ✅ 調查結果

#### 1. **賽道地圖繪製（使用 f1-circuits-master 資料）**
**可行性**：✅ **完全可行**

**現有實現**：
- **GUI Widget**：`modules/gui/track_analysis/track_map_widget.py`
- **資料來源**：`json/f1-circuits-master/circuits/jp-1962.geojson`（日本鈴鹿賽道範例）

**核心功能已存在**：
```python
# TrackMapWidget 類別（第 50 行）
class TrackMapWidget(QWidget):
    def load_track_data(self, track_data: Dict[str, Any]) -> bool:
        # 載入賽道資料
        
    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        # 座標轉換
        
    def _draw_official_corners(self, painter: QPainter) -> None:
        # 繪製官方彎道標記（第 373 行）
```

**整合計畫**：
- ✅ 讀取 f1-circuits-master 的 GeoJSON `coordinates` 陣列
- ✅ 使用現有的 `world_to_screen()` 轉換座標
- ✅ 使用現有的 QPainter 繪圖邏輯
- ⚠️ 需要轉換 GeoJSON 經緯度 → FastF1 X/Y 座標系統

---

#### 2. **彎道號碼標記整合**
**可行性**：✅ **完全可行，已有實現**

**現有實現位置**：
- **檔案**：`modules/gui/track_analysis/track_map_widget.py`
- **方法**：`_draw_official_corners()` (第 373-422 行)
- **數據來源**：`self.official_corners` (從 `track_data["official_corners"]` 載入)

**實際代碼驗證**：
```python
def _draw_official_corners(self, painter: QPainter) -> None:
    """繪製 FastF1 官方彎道標記 - 白底黑字，智能偏移避免與賽道重疊"""
    if not self.official_corners:
        return
    
    # 設定彎道標記樣式 - 白底黑字
    bg_color = QColor(255, 255, 255, 240)  # 半透明白色背景
    border_color = QColor(0, 0, 0)  # 黑色邊框
    text_color = QColor(0, 0, 0)  # 黑色文字
    
    for corner in self.official_corners:
        corner_x = corner.get("x", 0.0)
        corner_y = corner.get("y", 0.0)
        corner_num = corner.get("number", 0)
        
        # 計算智能偏移（第 394 行）
        offset_x, offset_y = self._calculate_corner_offset(
            corner_x, corner_y, offset_distance
        )
```

**數據結構**（來自 CLI backend）：
```python
"official_corners": {
    "available": True,
    "corners": [
        {"number": 1, "x": 123.45, "y": 678.90, "distance": 500.0},
        {"number": 2, "x": 234.56, "y": 789.01, "distance": 1200.0},
        # ... 更多彎道
    ]
}
```

**整合計畫**：
- ✅ 直接複用 `_draw_official_corners()` 方法
- ✅ 已有智能偏移算法 `_calculate_corner_offset()`（避免標記與賽道重疊）
- ✅ 支援顯示/隱藏開關 `self.show_official_corners`
- 🔧 需要將 f1-circuits-master 的彎道位置與 FastF1 座標系統對應

---

#### 3. **高度圖（高低差分析）**
**可行性**：✅ **可行（需要開發）**

**資料來源驗證**：
- **f1-circuits-master 提供**：
  - ✅ `altitude` (海拔高度，單一值)：`"altitude": 60` (公尺)
  - ✅ `coordinates` (賽道路線座標)：160+ 個 GPS 座標點
  - ❌ **不直接提供**：完整的高程剖面 (elevation profile)

**資料範例（日本鈴鹿賽道）**：
```json
{
  "properties": {
    "altitude": 60
  },
  "geometry": {
    "coordinates": [
      [136.540283, 34.843344],
      [136.541609, 34.842034],
      // ... 160+ 個座標點
    ]
  }
}
```

**解決方案**：
1. **選項 A：使用外部高程 API**（推薦）
   - 使用 Google Elevation API 或 Open-Elevation API
   - 將 GPS 座標批次查詢高程數據
   - 精確度高，實時更新
   
2. **選項 B：簡化高程模型**
   - 基於單一 `altitude` 值假設平坦賽道
   - 根據賽道特性（如 Spa 的 Eau Rouge）手動標註關鍵高低差
   - 適合快速開發，但不夠精確

**推薦方案**：選項 A（使用 Open-Elevation API，免費無需 API Key）

**實現範例**：
```python
import requests

def fetch_elevation_profile(coordinates):
    """使用 Open-Elevation API 獲取高程數據"""
    url = "https://api.open-elevation.com/api/v1/lookup"
    
    # 批次查詢（每次最多 100 個點）
    locations = [
        {"latitude": lat, "longitude": lon} 
        for lon, lat in coordinates
    ]
    
    response = requests.post(url, json={"locations": locations})
    if response.status_code == 200:
        data = response.json()
        return [point["elevation"] for point in data["results"]]
    return None
```

**整合計畫**：
- 🔧 開發新函數：`fetch_elevation_profile()`
- 🔧 繪製高程圖：使用 Matplotlib（參考 `UniversalChartWidget`）
- 🔧 數據緩存：避免重複 API 查詢

---

#### 4. **每年超車次數統計**
**可行性**：✅ **完全可行，已有 CLI 實現**

**現有實現位置**：
- **CLI 模組**：`CLI_modules/cli/analyzer/all_drivers_annual_overtaking_statistics.py`
- **功能 ID**：16.1
- **GUI 整合**：未實現（需要開發）

**核心方法驗證**：
```python
def run_all_drivers_annual_overtaking_statistics(
    data_loader, dynamic_team_mapping, f1_analysis_instance
):
    """
    執行全部車手年度超車統計分析 (功能 16.1)
    
    Returns:
        - overtakes_made: 超車次數
        - overtaken_by: 被超車次數
        - net_overtaking: 淨超車數
        - success_rate: 超車成功率
    """
```

**數據來源**：
- FastF1 `position_data`（位置變化分析）
- 邏輯：位置前進（負數變化）= 超車，位置後退（正數變化）= 被超車

**整合計畫**：
- ✅ CLI 功能已完整實現
- 🔧 需要開發：GUI 模組（參考 `rain_analysis` 架構）
- 🔧 需要擴展：按賽道統計（目前是單場賽事統計）
- � 需要開發：歷史年份對比功能（2020-2025）

**實現範例**（CLI 調用）：
```powershell
# 獲取 2025 年日本站超車統計
python f1_analysis_modular_main.py -f 16.1 -y 2025 -r Japan -s R
```

---

#### 5. **紅黃旗與安全車統計（按彎道分佈）**
**可行性**：✅ **部分可行，已有基礎實現**

**現有實現位置**：
- **事故統計模組**：`modules/gui/accident_analysis/accident_statistics_summary.py`
- **功能 ID**：6（事故統計摘要）
- **黃旗過濾**：`modules/gui/Throttle_analysis/throttle_line_chart_analysis/` (已實現)

**核心功能驗證**：
```python
def analyze_accident_statistics(session):
    """分析事故統計數據"""
    statistics = {
        'incident_types': {
            'safety_cars': 0,      # ✅ 安全車統計
            'red_flags': 0,        # ✅ 紅旗統計
            'flags': 0             # ✅ 黃旗統計（包含 YELLOW FLAG）
        },
        'incident_distribution_by_lap': {},  # ✅ 按圈數分佈
    }
    
    # 關鍵字識別（第 117-133 行）
    if 'SAFETY CAR' in msg_text:
        statistics['incident_types']['safety_cars'] += 1
    elif 'RED FLAG' in msg_text:
        statistics['incident_types']['red_flags'] += 1
    elif 'YELLOW FLAG' in msg_text:
        statistics['incident_types']['flags'] += 1
```

**資料來源**：
- **FastF1 `race_control_messages`**：包含所有賽會訊息
- **已實現功能**：
  - ✅ 識別 SAFETY CAR、RED FLAG、YELLOW FLAG
  - ✅ 統計按圈數分佈 (`incident_distribution_by_lap`)
  - ✅ 提取涉及車號 (`CAR 44`, `CAR 1`)

**缺少功能**：
- ❌ **彎道位置標註**（race_control_messages 不直接提供彎道號碼）
- ❌ **多年歷史對比**（目前僅支援單場賽事）

**解決方案**：
1. **推斷彎道位置**：
   - 通過 `race_control_messages` 的 `Time` 欄位對應遙測數據
   - 查找該時間點的 `Distance` 或 `position_x/y`
   - 比對 `official_corners` 數據推斷最近的彎道
   
2. **多年統計**：
   - 開發新 CLI 功能：批次載入多年賽事數據
   - 聚合統計：`{"2020": {"red_flags": 2}, "2021": {"red_flags": 1}, ...}`

**實現範例**：
```python
def map_incident_to_corner(incident_time, telemetry_data, corners):
    """將事故時間映射到最近的彎道"""
    # 1. 找到事故時間點的位置數據
    incident_position = telemetry_data[
        telemetry_data['Time'] == incident_time
    ]['Distance'].iloc[0]
    
    # 2. 找到最近的彎道
    closest_corner = min(
        corners, 
        key=lambda c: abs(c['distance'] - incident_position)
    )
    
    return closest_corner['number']
```

**整合計畫**：
- ✅ 複用現有的 `analyze_accident_statistics()`
- 🔧 開發新功能：`map_incident_to_corner()`（事故-彎道映射）
- 🔧 開發新功能：多年歷史統計（CLI Function 53.1）
- 🔧 整合至 GUI：賽道地圖上標註事故熱點

---

## 📊 整合開發優先級建議

### Phase 1: 基礎架構（優先）
- [x] **賽道地圖繪製**（複用 TrackMapWidget）
- [x] **彎道號碼標記**（複用 `_draw_official_corners()`）
- [ ] **座標系統轉換**（f1-circuits-master GeoJSON → FastF1 X/Y）

### Phase 2: 數據整合（中優先）
- [ ] **高程剖面圖**（整合 Open-Elevation API）
- [ ] **超車統計顯示**（GUI 模組開發，複用 CLI Function 16.1）
- [ ] **紅黃旗統計**（複用 Function 6，擴展彎道映射）

### Phase 3: 進階功能（低優先）
- [ ] **多年歷史對比**（開發新 CLI 功能）
- [ ] **賽道事故熱點圖**（疊加紅黃旗位置在地圖上）
- [ ] **安全車影響分析**（圈速變化、策略影響）

---

## 🎯 關鍵技術挑戰與解決方案

### 挑戰 1：座標系統差異
**問題**：f1-circuits-master 使用 GPS 經緯度，FastF1 使用 X/Y 座標
**解決方案**：
```python
def convert_gps_to_fastf1_coordinates(gps_coords, track_bounds):
    """將 GPS 經緯度轉換為 FastF1 座標系統"""
    # 1. 提取邊界框
    lon_min, lat_min, lon_max, lat_max = track_bounds
    
    # 2. 線性縮放（簡化版，實際可能需要 Mercator 投影）
    def scale_coord(lon, lat):
        x = ((lon - lon_min) / (lon_max - lon_min)) * 5000  # 假設賽道寬度 5000m
        y = ((lat - lat_min) / (lat_max - lat_min)) * 3000  # 假設賽道高度 3000m
        return x, y
    
    return [scale_coord(lon, lat) for lon, lat in gps_coords]
```

### 挑戰 2：高程數據缺失
**問題**：f1-circuits-master 僅提供單一海拔值
**解決方案**：
- **短期**：使用 Open-Elevation API 實時查詢
- **長期**：建立本地高程數據庫（緩存所有 F1 賽道）

### 挑戰 3：彎道位置推斷
**問題**：race_control_messages 不直接提供彎道號碼
**解決方案**：
```python
# 方法 1: 時間戳映射（推薦）
incident_lap = message['Lap']
incident_time = message['Time']
telemetry_at_time = session.laps[session.laps['LapNumber'] == incident_lap].iloc[0]
position = telemetry_at_time['Distance']

# 方法 2: 關鍵字識別（輔助）
if 'TURN 1' in message['Message']:
    corner_number = 1
```

---

## 📋 更新的開發檢查清單

### Phase 1: 賽道地圖與彎道標記
- [ ] **步驟 1.1**：複製 `TrackMapWidget` 到新模組
- [ ] **步驟 1.2**：讀取 f1-circuits-master GeoJSON 資料
- [ ] **步驟 1.3**：實現 GPS → FastF1 座標轉換
- [ ] **步驟 1.4**：整合 `_draw_official_corners()` 方法
- [ ] **步驟 1.5**：測試：鈴鹿賽道地圖 + 18 個彎道標記

### Phase 2: 高程剖面圖
- [ ] **步驟 2.1**：整合 Open-Elevation API
- [ ] **步驟 2.2**：實現 `fetch_elevation_profile()`
- [ ] **步驟 2.3**：繪製高程圖（Matplotlib）
- [ ] **步驟 2.4**：添加緩存機制（避免重複 API 查詢）
- [ ] **步驟 2.5**：測試：Spa 賽道高程變化（Eau Rouge）

### Phase 3: 超車統計整合
- [ ] **步驟 3.1**：在 GUI 調用 CLI Function 16.1
- [ ] **步驟 3.2**：開發新 GUI Widget：超車統計表格
- [ ] **步驟 3.3**：實現多年對比功能（2020-2025）
- [ ] **步驟 3.4**：繪製超車趨勢圖（按賽道）
- [ ] **步驟 3.5**：測試：2025 日本站 vs 2024 日本站

### Phase 4: 紅黃旗與安全車統計
- [ ] **步驟 4.1**：複用 `analyze_accident_statistics()`
- [ ] **步驟 4.2**：實現 `map_incident_to_corner()`
- [ ] **步驟 4.3**：開發 CLI Function 53.1：多年事故統計
- [ ] **步驟 4.4**：在賽道地圖上標註事故位置（紅點）
- [ ] **步驟 4.5**：統計表格：按彎道排序的事故次數
- [ ] **步驟 4.6**：測試：Monaco 賽道事故熱點（Turn 1, Sainte Devote）
