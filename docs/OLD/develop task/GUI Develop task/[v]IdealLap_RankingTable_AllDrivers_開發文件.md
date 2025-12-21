# 理想圈排名表格 (全車手) - GUI 模組規劃

**模組分類**: GUI Develop Task  
**對應 CLI 功能**: Function 53 - Ideal Lap Analysis (All Drivers)  
**狀態**: 📝 規劃草案  
**建立日期**: 2025-10-09  
**最後更新**: 2025-10-09

---

## 🎯 目標概述

建立一個 GUI 主視圖，使用 **可排序表格** 展示指定賽事中各車手的理想圈排名，對比車手最快圈與理想圈的時間差，協助分析車手單圈潛力。資料來源為 CLI Function 53 輸出的 JSON (`ideal_lap_ranking_{year}_{race}_{session}.json`)，支援 API-ONLY 模式下的資料載入。

### 關鍵問題
- 各車手的理想圈排名與實際最快圈排名差異如何?
- 哪些車手的理想圈與最快圈差距最大 (未發揮完整潛力)?
- 全場最速圈與理想圈榜首的差異有多少?
- 車隊內兩位車手的理想圈表現差距?

---

## 📊 視覺化需求

### 主表格結構 (每車手一行顯示)

**核心概念**：每位車手顯示為獨立一行，包含其個人最速圈、理想圈、差異，並對照全場最速實際圈。

| 欄位名稱 | 資料來源 | 說明 | 範例 |
|---------|---------|------|------|
| 排名 | `position` | 理想圈排名 (1-20) | 1 |
| 車手 | `driver` | 3 字母代碼，**背景色使用車隊主題色** | VER |
| 車隊 | `team` | 車隊名稱 | Red Bull Racing |
| 車手最速圈 | `fastest_lap_time` | 該車手實際最快圈時間 | 1:31.106 |
| 理想圈 | `ideal_lap_time` | 該車手理想圈時間 (三個最佳分段組合) | 1:30.625 |
| 差異 | `time_gap` | 車手最速圈 - 理想圈 (正值表示未達最佳) | +0.481s |
| 全場最速實際圈 | `session_fastest_lap` | 該場比賽所有車手中的最快實際圈速 | 1:30.965 (ANT) |
| 與全場最速差距 | `gap_to_session_fastest` | 車手最速圈 - 全場最速圈 | +0.141s |
| 分段標記 | `sector_breakdown` | ✓/✗ 指示該車手最快圈是否包含最佳分段 | ✗✗✗ |
| 操作 | - | [詳情] 按鈕 → 跳轉至深度視圖 | [詳情] |

**欄位重點說明**：
- **車手最速圈**：該車手在比賽中跑出的實際最快單圈
- **理想圈**：將該車手所有圈速中的最快 S1、S2、S3 組合而成
- **差異**：顯示車手是否在單圈中同時發揮出三個分段的最佳表現
- **全場最速實際圈**：所有車手中真正跑出的最快單圈（括號內顯示創造者）
- **與全場最速差距**：該車手與全場最速的差距（評估競爭力）

### 表格功能
- **可排序**: 點擊欄位標題升降排序
  - 理想圈時間（預設排序）
  - 車手最速圈
  - 差異（找出潛力未發揮的車手）
  - 與全場最速差距（競爭力排名）
  - 車隊（車隊內對比）
  
- **顏色編碼**:
  - **車手欄位背景色**：使用 FastF1 官方車隊色票
  - **差異欄位梯度**：
    - 綠色 (0-0.2s)：接近完美單圈
    - 黃色 (0.2-0.5s)：中等潛力提升
    - 紅色 (>0.5s)：有明顯改善空間
  - **與全場最速差距**：
    - 深綠色 (<0.5s)：極具競爭力
    - 淺綠色 (0.5-1s)：具競爭力
    - 黃色 (1-2s)：中游
    - 紅色 (>2s)：落後

- **篩選選項**:
  - 車隊篩選 (多選: Mercedes, Ferrari, Red Bull...)
  - 顯示範圍 (Top 10 / Top 5 / All)
  - 隱藏/顯示分段標記欄位

- **懸停提示 (Tooltip)**:
  - **理想圈**: 顯示分段來源  
    ```
    理想圈: 1:30.625
    S1: 31.320s (Lap 42)
    S2: 41.605s (Lap 23)
    S3: 17.700s (Lap 18)
    ```
  - **車手最速圈**: 顯示圈數與分段時間
    ```
    最速圈: 1:31.106 (Lap 38)
    S1: 31.450s
    S2: 41.756s
    S3: 17.900s
    ```
  - **差異**: 顯示百分比與潛力評估
    ```
    差異: +0.481s (+0.53%)
    評估: 有中等提升空間
    最佳改善分段: S2 (-0.151s)
    ```
  - **全場最速圈**: 顯示創造者與圈數
    ```
    全場最速: 1:30.965
    創造者: ANT (Lap 42)
    領先第二: 0.074s
    ```

### 統計摘要面板
**位於表格上方**，顯示 `analysis_result.summary` 與全場統計：

```
📊 賽事統計摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
總車手數: 20
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
理想圈統計:
  最快理想圈: 1:30.625 (SAI)
  最慢理想圈: 1:32.569 (DOO)
  平均理想圈: 1:31.282
  理想圈範圍: 1.944s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
實際圈速統計:
  全場最速實際圈: 1:30.965 (ANT, Lap 42) ⭐
  最速圈所屬車隊: Mercedes
  與最快理想圈差距: +0.340s
  理想圈榜首若達成: 領先實際最速 0.340s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
潛力分析:
  平均差異 (最速-理想): 0.387s
  最大未發揮潛力: 0.734s (TSU)
  最接近完美單圈: 0.074s (PIA)
  完美單圈達成率: 0/20 (0%)
```

**關鍵指標說明**：
- **全場最速實際圈**：所有車手真實跑出的最快單圈（⭐ 標記）
- **與最快理想圈差距**：比較理論最快 vs 實際最快
- **平均差異**：所有車手「最速圈-理想圈」的平均值
- **完美單圈達成率**：有幾位車手在單圈中同時發揮三個分段最佳表現

---

## 🧱 架構設計 (遵循通用模組設計)

### 通用模組三層架構

**完全採用降雨分析模組的設計模式**：

```
IdealLapRankingTableModule (IAnalysisModule)
├── 實作介面層
│   ├── initialize_module()
│   ├── load_data()
│   ├── update_parameters()
│   └── get_widget()
│
├── IdealLapRankingTableMDI (UniversalAnalysisMDI)
│   ├── MDI 視窗管理
│   ├── UI 元件組織
│   └── 事件處理
│
├── IdealLapRankingTableDataLoader (UniversalDataLoader)
│   ├── API 優先載入
│   ├── JSON 本地讀取
│   └── 資料驗證與轉換
│
└── IdealLapRankingTableChartWidget (UniversalChartWidget)
    ├── QTableWidget 表格渲染
    ├── 車隊顏色映射
    └── 排序與篩選邏輯
```

### 模組檔案結構

```
modules/gui/ideal_lap_analysis/
├── __init__.py
├── ideal_lap_ranking_table/
│   ├── __init__.py
│   ├── ideal_lap_ranking_table_module.py      # IAnalysisModule 實作
│   ├── ideal_lap_ranking_table_mdi.py         # UniversalAnalysisMDI 子類
│   ├── ideal_lap_ranking_table_data_loader.py # UniversalDataLoader 子類
│   └── ideal_lap_ranking_table_widget.py      # QTableWidget + 統計面板
│
├── ideal_lap_options_dialog.py  # 選項對話框（共用）
└── README.md
```

### MDI 視窗設計 (IdealLapRankingTableMDI)

**繼承自 `UniversalAnalysisMDI`**，實作以下方法：

```python
class IdealLapRankingTableMDI(UniversalAnalysisMDI):
    """理想圈排名表格 MDI 視窗"""
    
    def __init__(self, year, race, session, parent=None):
        # 配置 MDI 參數
        config = {
            "window_title": f"Ideal Lap Ranking_{year}_{race}_{session}",
            "default_size": (1400, 900),
            "min_size": (1000, 600)
        }
        super().__init__(year, race, session, parent, **config)
    
    def _create_data_loader(self):
        """創建資料載入器"""
        return IdealLapRankingTableDataLoader(
            year=self.year,
            race=self.race,
            session=self.session,
            parent=self
        )
    
    def _create_chart_widget(self):
        """創建圖表元件"""
        return IdealLapRankingTableWidget(parent=self)
    
    def _setup_control_panel(self):
        """設置控制面板"""
        # 車隊篩選器
        # Top N 選擇器
        # 匯出按鈕
        pass
    
    def _on_data_loaded(self, data):
        """資料載入完成回調"""
        self.chart_widget.populate_table(data)
        self.chart_widget.update_statistics_panel(data)
```

### 資料載入器設計 (IdealLapRankingTableDataLoader)

**繼承自 `UniversalDataLoader`**：

```python
class IdealLapRankingTableDataLoader(UniversalDataLoader):
    """理想圈排名表格資料載入器"""
    
    CLI_FUNCTION = 53
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    def _validate_data_format(self, data):
        """驗證 JSON 結構"""
        required_keys = ["ranking", "summary", "team_analysis", "sector_comparison"]
        if "analysis_result" not in data:
            return False
        return all(k in data["analysis_result"] for k in required_keys)
    
    def _transform_data_for_display(self, data):
        """轉換資料為顯示格式"""
        # 計算全場最速圈
        ranking = data["analysis_result"]["ranking"]
        session_fastest = min(
            d["fastest_lap_time"] for d in ranking
            if d["fastest_lap_time"] is not None
        )
        
        # 注入每位車手
        for driver in ranking:
            driver["session_fastest_lap"] = session_fastest
            driver["session_fastest_driver"] = self._find_fastest_driver(ranking, session_fastest)
        
        return data
    
    def _find_fastest_driver(self, ranking, fastest_time):
        """找出創造最速圈的車手"""
        for driver in ranking:
            if driver["fastest_lap_time"] == fastest_time:
                return driver["driver"]
        return "Unknown"
```

### API-ONLY 模式整合

- ✅ **優先 API 載入**: 通過 `refactored_api.py` 調用 Function 53
- ✅ **本地 JSON 備援**: 讀取 `json/ideal_lap_ranking_{year}_{race}_{session}.json`
- ❌ **禁止 CLI 調用**: `_generate_data_via_cli()` 固定返回 `False`

### 資料流程
1. **載入階段**:
   ```python
   loader = IdealLapRankingDataLoader(year=2025, race="Japan", session="R")
   data = loader.fetch_data()  # API or local JSON
   ```

2. **驗證階段**:
   ```python
   def _validate_data_format(self, data):
       required = ["ranking", "summary", "team_analysis"]
       return all(k in data["analysis_result"] for k in required)
   ```

3. **轉換階段**:
   ```python
   def _transform_data_for_display(self, data):
       # 計算全場最速圈 (從所有車手 fastest_lap_time 中取最小值)
       session_fastest = min(
           d["fastest_lap_time"] for d in data["analysis_result"]["ranking"]
           if d["fastest_lap_time"] is not None
       )
       # 注入每列資料
       for driver in data["analysis_result"]["ranking"]:
           driver["session_fastest_lap"] = session_fastest
       return data
   ```

4. **渲染階段**:
   - 填充 `QTableWidget`
   - 套用車隊顏色 (`setBackground()`)
   - 設置排序與篩選

---

## 🛠️ 實作步驟 (遵循通用模組模式)

### Phase 1: 模組介面實作 (IdealLapRankingTableModule)

**參考**: `modules/gui/rain_analysis/rain_analysis_module.py`

```python
# modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_module.py
from modules.gui.interfaces.analysis_module import IAnalysisModule

class IdealLapRankingTableModule(IAnalysisModule):
    """理想圈排名表格模組 - 實作 IAnalysisModule 介面"""
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        super().__init__(parent)
        
        # 模組基本資訊
        self._module_name = "IdealLapRankingTable"
        self._display_name = "🏁 Ideal Lap Ranking Table"
        self._version = "1.0.0"
        self._description = "All Drivers Ideal Lap Ranking Analysis"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 創建內部核心實例
        self._ranking_core = None
        
        # 初始化模組
        self.initialize_module(parent)
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組"""
        try:
            if not self._ranking_core:
                from .ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI
                self._ranking_core = IdealLapRankingTableMDI(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    parent=parent_widget
                )
            
            self._main_widget = self._ranking_core.get_widget()
            self._is_initialized = True
            print("✅ [RANKING_MODULE] 模組已初始化")
            return True
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 初始化失敗: {e}")
            return False
    
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """更新分析參數"""
        try:
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            if self._ranking_core:
                return self._ranking_core.update_analysis_parameters(
                    year=str(year), race=race, session=session
                )
            return False
        except Exception as e:
            print(f"❌ [RANKING_MODULE] 參數更新錯誤: {e}")
            return False
    
    # 實作其他 IAnalysisModule 抽象方法...
    # load_data(), refresh_analysis(), clear_data(), export_data(), get_current_data()
```

### Phase 2: MDI 視窗實作 (IdealLapRankingTableMDI)

**參考**: `modules/gui/rain_analysis/rain_analysis_mdi.py`

```python
# modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py
from modules.gui.base.universal_analysis_mdi import UniversalAnalysisMDI

class IdealLapRankingTableMDI(UniversalAnalysisMDI):
    """理想圈排名表格 MDI 視窗"""
    
    def __init__(self, year, race, session, parent=None):
        config = {
            "window_title": f"Ideal Lap Ranking_{year}_{race}_{session}",
            "default_size": (1400, 900),
            "module_type": "ideal_lap_ranking"
        }
        super().__init__(year, race, session, parent, **config)
        
        # 初始化 UI
        self._init_ui()
        
        # 載入資料
        self.load_initial_data()
    
    def _create_data_loader(self):
        """創建資料載入器（由基類調用）"""
        from .ideal_lap_ranking_table_data_loader import IdealLapRankingTableDataLoader
        return IdealLapRankingTableDataLoader(
            year=self.year,
            race=self.race,
            session=self.session,
            parent=self
        )
    
    def _create_chart_widget(self):
        """創建圖表元件（由基類調用）"""
        from .ideal_lap_ranking_table_widget import IdealLapRankingTableWidget
        return IdealLapRankingTableWidget(parent=self)
    
    def _init_ui(self):
        """初始化 UI 佈局"""
        # 上半部: 統計摘要面板
        self.summary_panel = self._create_summary_panel()
        
        # 中間部: 主表格
        self.table_widget = self.chart_widget  # 來自基類
        
        # 下半部: 控制面板
        self.control_panel = self._create_control_panel()
        
        # 佈局組織
        self._organize_layout()
    
    def _create_summary_panel(self):
        """創建統計摘要面板"""
        panel = QGroupBox("📊 賽事統計摘要")
        # ... 添加統計標籤
        return panel
    
    def _create_control_panel(self):
        """創建控制面板"""
        panel = QWidget()
        # 車隊篩選器
        # Top N 選擇器
        # 匯出按鈕
        return panel
    
    def _on_data_loaded(self, data):
        """資料載入完成回調"""
        if not data or not data.get("success"):
            print("❌ 資料載入失敗")
            return
        
        # 更新表格
        self.table_widget.populate_table(data["analysis_result"]["ranking"])
        
        # 更新統計面板
        self._update_summary_panel(data["analysis_result"]["summary"])
```

### Phase 3: 資料載入器實作 (IdealLapRankingTableDataLoader)

**參考**: `modules/gui/rain_analysis/rain_analysis_data_loader.py`

```python
# modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_data_loader.py
from modules.gui.base.universal_data_loader_base import UniversalDataLoader

class IdealLapRankingTableDataLoader(UniversalDataLoader):
    """理想圈排名表格資料載入器"""
    
    CLI_FUNCTION = 53
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    def __init__(self, year, race, session, parent=None):
        super().__init__(
            cli_function=self.CLI_FUNCTION,
            json_pattern=self.JSON_PATTERN,
            parent=parent
        )
        self.year = year
        self.race = race
        self.session = session
    
    def _validate_data_format(self, data):
        """驗證 JSON 結構"""
        if not isinstance(data, dict):
            return False
        
        if "analysis_result" not in data:
            return False
        
        required = ["ranking", "summary", "team_analysis", "sector_comparison"]
        return all(k in data["analysis_result"] for k in required)
    
    def _transform_data_for_display(self, data):
        """轉換資料為顯示格式"""
        ranking = data["analysis_result"]["ranking"]
        
        # 計算全場最速實際圈 (從所有車手的 fastest_lap_time 中取最小值)
        fastest_laps = [d["fastest_lap_time"] for d in ranking if d["fastest_lap_time"]]
        session_fastest = min(fastest_laps) if fastest_laps else None
        
        # 找出創造全場最速圈的車手與圈數
        fastest_driver = None
        fastest_lap_number = None
        if session_fastest:
            for driver in ranking:
                if driver["fastest_lap_time"] == session_fastest:
                    fastest_driver = driver["driver"]
                    # 從 laps 陣列中找到最快圈的圈數
                    for lap in driver["laps"]:
                        if lap["lap_time_seconds"] == session_fastest:
                            fastest_lap_number = lap["lap_number"]
                            break
                    break
        
        # 注入每位車手的資料
        for driver in ranking:
            # 全場最速圈資訊
            driver["session_fastest_lap"] = session_fastest
            driver["session_fastest_driver"] = fastest_driver
            driver["session_fastest_lap_number"] = fastest_lap_number
            
            # 計算該車手與全場最速的差距
            if driver["fastest_lap_time"] and session_fastest:
                driver["gap_to_session_fastest"] = driver["fastest_lap_time"] - session_fastest
            else:
                driver["gap_to_session_fastest"] = None
        
        # 計算統計摘要
        data["analysis_result"]["summary"]["session_fastest_lap"] = session_fastest
        data["analysis_result"]["summary"]["session_fastest_driver"] = fastest_driver
        data["analysis_result"]["summary"]["session_fastest_lap_number"] = fastest_lap_number
        
        # 計算平均差異 (車手最速圈 - 理想圈)
        gaps = [d["time_gap"] for d in ranking if d.get("time_gap")]
        data["analysis_result"]["summary"]["average_gap"] = sum(gaps) / len(gaps) if gaps else 0
        
        # 找出最大未發揮潛力與最接近完美的車手
        max_gap_driver = max(ranking, key=lambda x: x.get("time_gap", 0))
        min_gap_driver = min(ranking, key=lambda x: x.get("time_gap", float('inf')))
        
        data["analysis_result"]["summary"]["max_potential_driver"] = max_gap_driver["driver"]
        data["analysis_result"]["summary"]["max_potential_gap"] = max_gap_driver["time_gap"]
        data["analysis_result"]["summary"]["closest_perfect_driver"] = min_gap_driver["driver"]
        data["analysis_result"]["summary"]["closest_perfect_gap"] = min_gap_driver["time_gap"]
        
        return data
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        ⚠️ API-ONLY 模式: 禁止 CLI 調用
        """
        self._debug("⚠️ [API-ONLY] CLI 調用已禁用")
        return False
```

### Phase 4: 表格元件實作 (IdealLapRankingTableWidget)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal

class IdealLapRankingTableWidget(QWidget):
    """理想圈排名表格元件"""
    
    detail_requested = pyqtSignal(str)  # 發射車手代碼
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 創建表格
        self.table = QTableWidget()
        self._setup_table_columns()
        
        layout.addWidget(self.table)
    
    def _setup_table_columns(self):
        """設置表格欄位"""
        columns = [
            "排名",           # position
            "車手",           # driver (背景色)
            "車隊",           # team
            "車手最速圈",     # fastest_lap_time
            "理想圈",         # ideal_lap_time
            "差異",           # time_gap (梯度顏色)
            "全場最速實際圈", # session_fastest_lap (創造者)
            "與全場最速差距", # gap_to_session_fastest
            "分段",           # sector_breakdown (✓/✗)
            "操作"            # 詳情按鈕
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setSortingEnabled(True)
        
        # 設置欄位寬度
        self.table.setColumnWidth(0, 60)   # 排名
        self.table.setColumnWidth(1, 80)   # 車手
        self.table.setColumnWidth(2, 150)  # 車隊
        self.table.setColumnWidth(3, 100)  # 車手最速圈
        self.table.setColumnWidth(4, 100)  # 理想圈
        self.table.setColumnWidth(5, 90)   # 差異
        self.table.setColumnWidth(6, 150)  # 全場最速
        self.table.setColumnWidth(7, 120)  # 與全場最速差距
        self.table.setColumnWidth(8, 80)   # 分段
        self.table.setColumnWidth(9, 80)   # 操作
    
    def populate_table(self, ranking_data):
        """填充表格資料"""
        self.table.setRowCount(len(ranking_data))
        
        for row, driver in enumerate(ranking_data):
            # 填充各欄位
            self._set_row_data(row, driver)
            
            # 套用車隊顏色
            self._apply_team_color(row, driver["team"])
    
    def _set_row_data(self, row, driver):
        """設置單行資料"""
        # 排名
        self.table.setItem(row, 0, QTableWidgetItem(str(driver["position"])))
        
        # 車手（套用車隊背景色）
        driver_item = QTableWidgetItem(driver["driver"])
        driver_item.setBackground(self._get_team_color(driver["team"]))
        self.table.setItem(row, 1, driver_item)
        
        # 車隊
        self.table.setItem(row, 2, QTableWidgetItem(driver["team"]))
        
        # 車手最速圈
        fastest_lap_item = QTableWidgetItem(self._format_time(driver["fastest_lap_time"]))
        self.table.setItem(row, 3, fastest_lap_item)
        
        # 理想圈
        ideal_lap_item = QTableWidgetItem(self._format_time(driver["ideal_lap_time"]))
        self.table.setItem(row, 4, ideal_lap_item)
        
        # 差異（套用梯度顏色）
        gap = driver.get("time_gap", 0)
        gap_item = QTableWidgetItem(f"+{gap:.3f}s" if gap > 0 else f"{gap:.3f}s")
        gap_item.setBackground(self._get_gap_color(gap))
        self.table.setItem(row, 5, gap_item)
        
        # 全場最速實際圈（顯示時間 + 創造者）
        session_fastest = driver.get("session_fastest_lap")
        fastest_driver = driver.get("session_fastest_driver")
        fastest_lap_num = driver.get("session_fastest_lap_number", "")
        if session_fastest and fastest_driver:
            session_text = f"{self._format_time(session_fastest)} ({fastest_driver})"
            if fastest_lap_num:
                session_text += f" L{fastest_lap_num}"
        else:
            session_text = "N/A"
        self.table.setItem(row, 6, QTableWidgetItem(session_text))
        
        # 與全場最速差距
        gap_to_fastest = driver.get("gap_to_session_fastest")
        if gap_to_fastest is not None:
            gap_fastest_item = QTableWidgetItem(f"+{gap_to_fastest:.3f}s")
            gap_fastest_item.setBackground(self._get_competitiveness_color(gap_to_fastest))
            self.table.setItem(row, 7, gap_fastest_item)
        else:
            self.table.setItem(row, 7, QTableWidgetItem("N/A"))
        
        # 分段標記
        sector_marks = self._get_sector_marks(driver["sector_breakdown"])
        self.table.setItem(row, 8, QTableWidgetItem(sector_marks))
        
        # 操作按鈕
        detail_btn = QPushButton("詳情")
        detail_btn.clicked.connect(lambda: self.detail_requested.emit(driver["driver"]))
        self.table.setCellWidget(row, 9, detail_btn)
    
    def _format_time(self, seconds):
        """格式化時間為 MM:SS.mmm"""
        if seconds is None:
            return "N/A"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _get_gap_color(self, gap):
        """根據差異返回顏色（綠-黃-紅梯度）"""
        from PyQt5.QtGui import QColor
        if gap < 0.2:
            return QColor(144, 238, 144)  # 淺綠
        elif gap < 0.5:
            return QColor(255, 255, 153)  # 淺黃
        else:
            return QColor(255, 182, 193)  # 淺紅
    
    def _get_competitiveness_color(self, gap):
        """根據與全場最速差距返回顏色"""
        from PyQt5.QtGui import QColor
        if gap < 0.5:
            return QColor(34, 139, 34)   # 深綠
        elif gap < 1.0:
            return QColor(144, 238, 144) # 淺綠
        elif gap < 2.0:
            return QColor(255, 255, 153) # 黃色
        else:
            return QColor(255, 182, 193) # 紅色
    
    def _apply_team_color(self, row, team):
        """套用車隊顏色"""
        # 使用 FastF1 色票
        pass
```

---

## ✅ 測試計畫

| 測試項目 | 說明 |
|----------|------|
| API 響應測試 | 模擬 `/analyze function_id=53` 回傳，驗證 loader 正確解析 |
| 資料完整性 | 檢查 20 位車手資料無遺漏，時間格式正確 |
| 排序功能 | 各欄位升降排序結果正確 |
| 顏色映射 | 車隊背景色與 FastF1 官方色票一致 |
| 篩選器 | 車隊多選、Top N 篩選正確過濾資料 |
| Tooltip | 懸停顯示詳細資訊且不卡頓 |
| 匯出功能 | CSV 匯出包含所有欄位與當前篩選狀態 |
| 空資料處理 | 若 JSON 缺失，顯示友善錯誤訊息 |
| i18n | 支援中英文切換 (欄位名稱、統計文字) |

---

### Phase 5: 對話框整合

**參考**: `modules/gui/driver_race/detailed_lap_analysis/detailed_lap_options_dialog.py`

```python
# modules/gui/ideal_lap_analysis/ideal_lap_options_dialog.py
from PyQt5.QtWidgets import QDialog, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout

class IdealLapAnalysisOptionsDialog(QDialog):
    """理想圈分析選項對話框"""
    
    # 分析類型常數
    TYPE_RANKING_TABLE = "ranking_table"
    TYPE_SECTOR_HEATMAP = "sector_heatmap"
    TYPE_SECTOR_COMPARISON = "sector_comparison"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏁 選擇理想圈分析類型")
        self.resize(450, 400)
        
        self._init_ui()
        self._apply_stylesheet()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # QListWidget 多選清單
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        
        # 添加選項
        self.list_widget.addItem("📊 排名表格 (Ranking Table)")
        self.list_widget.addItem("🔥 分段熱力圖 (Sector Heatmap)")
        self.list_widget.addItem("📈 分段比較圖 (Sector Comparison)")
        
        # 快速選擇按鈕
        btn_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("全選")
        self.btn_clear_all = QPushButton("清空")
        self.btn_select_all.clicked.connect(self.list_widget.selectAll)
        self.btn_clear_all.clicked.connect(self.list_widget.clearSelection)
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_clear_all)
        
        # 確認/取消
        self.btn_ok = QPushButton("確認")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        # 組織佈局
        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)
    
    def _apply_stylesheet(self):
        """套用樣式（複製自 DetailedLapAnalysisOptionsDialog）"""
        # ... 與 lap_analysis_options_dialog.py 相同樣式
        pass
    
    def get_selected_types(self) -> list:
        """獲取選中的分析類型"""
        selected_indices = [i.row() for i in self.list_widget.selectedIndexes()]
        type_map = [
            self.TYPE_RANKING_TABLE,
            self.TYPE_SECTOR_HEATMAP,
            self.TYPE_SECTOR_COMPARISON
        ]
        return [type_map[i] for i in selected_indices]
```

### Phase 6: 主選單整合

**修改**: `f1t_gui_main.py`

```python
# 在 MainWindow 類中添加
def _init_menu_bar(self):
    # ... 既有選單
    
    # ✅ 新增: Ideal Lap Analysis 選單項目
    ideal_lap_action = QAction("🏁 Ideal Lap Analysis", self)
    ideal_lap_action.triggered.connect(self._prompt_ideal_lap_options)
    analysis_menu.addAction(ideal_lap_action)

def _prompt_ideal_lap_options(self):
    """顯示理想圈分析選項對話框"""
    # 先取得賽事參數
    year, race, session, ok = self._show_race_parameter_dialog()
    if not ok:
        return
    
    # 顯示分析類型選擇對話框
    from modules.gui.ideal_lap_analysis.ideal_lap_options_dialog import IdealLapAnalysisOptionsDialog
    dialog = IdealLapAnalysisOptionsDialog(self)
    
    if dialog.exec_() != QDialog.Accepted:
        return
    
    selected_types = dialog.get_selected_types()
    if not selected_types:
        QMessageBox.warning(self, "警告", "請至少選擇一種分析類型")
        return
    
    # 根據選擇創建視窗
    self._create_ideal_lap_windows(selected_types, year, race, session)

def _create_ideal_lap_windows(self, types, year, race, session):
    """創建理想圈分析視窗"""
    for analysis_type in types:
        if analysis_type == "ranking_table":
            self._create_ideal_lap_ranking_window(year, race, session)
        elif analysis_type == "sector_heatmap":
            self._create_ideal_lap_heatmap_window(year, race, session)
        elif analysis_type == "sector_comparison":
            self._create_ideal_lap_comparison_window(year, race, session)

def _create_ideal_lap_ranking_window(self, year, race, session):
    """創建排名表格視窗"""
    from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
    
    module = IdealLapRankingTableModule(
        parent=self,
        year=year,
        race=race,
        session=session
    )
    
    # 包裝進 MDI 子視窗
    sub_window = QMdiSubWindow()
    sub_window.setWidget(module.get_widget())
    sub_window.setWindowTitle(f"Ideal Lap Ranking_{year}_{race}_{session}")
    
    self.mdi_area.addSubWindow(sub_window)
    sub_window.show()
```

---

## ⚠️ 風險與注意事項

- **全場最速圈計算**: 需確認是從所有車手的 `fastest_lap_time` 中取最小值，而非理想圈
- **顏色對比度**: 車隊背景色需確保文字可讀性 (白色/黑色文字自動切換)
- **API-ONLY 限制**: 若資料不存在，需引導使用者「請先執行 API 分析或手動執行 CLI」
- **大表格效能**: 20 車手 x 10 欄位需優化渲染速度，避免卡頓
- **分段標記複雜度**: `sector_breakdown` 中的 `is_optimal_in_fastest` 需清晰標示 (✓/✗ 或顏色)

---

## 🎨 UI Mock (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 📊 賽事統計摘要                                                                          │
│ 總車手數: 20 | 最快理想圈: 1:30.625 (SAI) | 全場最速實際圈: 1:30.965 (ANT, L42) ⭐   │
│ 平均差異: 0.387s | 最大未發揮: 0.734s (TSU) | 最接近完美: 0.074s (PIA)                │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 篩選: [車隊▼] [Top 10▼]  匯出: [PNG] [CSV]                                            │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│排名│車手│車隊        │車手最速圈│理想圈   │差異   │全場最速實際圈│與全場差距│分段│操作│
├────┼────┼────────────┼──────────┼─────────┼───────┼──────────────┼──────────┼────┼────┤
│ 1  │SAI │Williams    │1:31.106  │1:30.625 │+0.481s│1:30.965(ANT) │  +0.141s │✗✗✗│詳情│
│    │    │            │          │         │ 🟡   │  L42 ⭐     │   🟢    │    │    │
├────┼────┼────────────┼──────────┼─────────┼───────┼──────────────┼──────────┼────┼────┤
│ 2  │ANT │Mercedes    │1:30.965  │1:30.643 │+0.322s│1:30.965(ANT) │  +0.000s │✗✗✗│詳情│
│    │    │            │ ⭐      │         │ 🟢   │  L42 ⭐     │   🟢    │    │    │
├────┼────┼────────────┼──────────┼─────────┼───────┼──────────────┼──────────┼────┼────┤
│ 3  │PIA │McLaren     │1:31.039  │1:30.734 │+0.305s│1:30.965(ANT) │  +0.074s │✗✗✓│詳情│
│    │    │            │          │         │ 🟢   │  L42 ⭐     │   🟢    │    │    │
├────┼────┼────────────┼──────────┼─────────┼───────┼──────────────┼──────────┼────┼────┤
│ 4  │VER │Red Bull    │1:31.245  │1:30.785 │+0.460s│1:30.965(ANT) │  +0.280s │✗✗✗│詳情│
│    │    │            │          │         │ 🟡   │  L42 ⭐     │   🟢    │    │    │
├────┼────┼────────────┼──────────┼─────────┼───────┼──────────────┼──────────┼────┼────┤
│...│... │...         │...       │...      │...    │...           │...       │... │... │
└────┴────┴────────────┴──────────┴─────────┴───────┴──────────────┴──────────┴────┴────┘
```

**視覺標記說明**：
- ⭐：全場最速實際圈創造者
- 🟢 綠色：優秀表現（差異小 / 競爭力強）
- 🟡 黃色：中等表現（有提升空間）
- 🔴 紅色：需改善（差異大 / 競爭力弱）

**欄位重點**：
- **車手最速圈**：該車手實際跑出的最快單圈
- **理想圈**：該車手三個最佳分段的理論組合
- **差異**：顯示單圈一致性（越小越接近完美單圈）
- **全場最速實際圈**：所有車手中真實最快圈速（含創造者與圈數）
- **與全場差距**：評估該車手的競爭力

---

## 🎬 選項對話框設計

### 功能需求
建立 `IdealLapAnalysisOptionsDialog`，讓使用者在啟動理想圈分析時**選擇要開啟的子模組**，完全採用現有 `DetailedLapAnalysisOptionsDialog` 的樣式和結構。

### 對話框結構
```python
# modules/gui/ideal_lap_analysis/ideal_lap_options_dialog.py
class IdealLapAnalysisOptionsDialog(QDialog):
    """
    理想圈分析選項對話框
    
    支援多選，讓使用者同時選擇多種分析視圖：
    1. 排名表格總覽 - 全車手理想圈排名與時間差
    2. 分段熱力圖 - 視覺化各車手分段表現
    3. 分段對比圖 - 理想圈 vs 最快圈分段詳細對比
    """
    
    # 分析類型常數
    TYPE_RANKING_TABLE = "ranking_table"      # 排名表格總覽
    TYPE_SECTOR_HEATMAP = "sector_heatmap"    # 分段熱力圖
    TYPE_SECTOR_COMPARISON = "sector_comparison"  # 分段對比圖
```

### UI 配置
```
┌──────────────────────────────────────────────┐
│  Ideal Lap Analysis Options                 │
├──────────────────────────────────────────────┤
│  ┌─ Available Analysis Types ─────────────┐ │
│  │ ☐ 排名表格總覽                         │ │
│  │   全車手理想圈排名與時間差             │ │
│  │                                         │ │
│  │ ☐ 分段熱力圖                           │ │
│  │   視覺化各車手分段表現                 │ │
│  │                                         │ │
│  │ ☐ 分段對比圖                           │ │
│  │   理想圈 vs 最快圈分段詳細對比         │ │
│  └─────────────────────────────────────────┘ │
│                                                │
│  快速選擇: [全選] [清空]                      │
│                                                │
│             [OK]          [Cancel]             │
└────────────────────────────────────────────────┘
```

### 實作要點
1. **繼承自 QDialog**：與 `DetailedLapAnalysisOptionsDialog` 相同結構
2. **使用 QListWidget**：支援多選 (`setSelectionMode(QAbstractItemView.MultiSelection)`)
3. **快速選擇按鈕**：
   - 全選：勾選所有分析類型
   - 清空：取消所有勾選
4. **樣式複製**：完全使用現有對話框的 `_apply_stylesheet()`
5. **i18n 支援**：使用 `core.gui_i18n.tr()` 處理多語言

### 使用範例
```python
# 在主視窗中調用
def _prompt_ideal_lap_options(self):
    """顯示理想圈分析選項並回傳使用者選擇"""
    dialog = IdealLapAnalysisOptionsDialog(self)
    
    if dialog.exec_() == QDialog.Accepted:
        selected_types = dialog.get_selected_types()
        
        # 根據選擇開啟對應的分析視窗
        if IdealLapAnalysisOptionsDialog.TYPE_RANKING_TABLE in selected_types:
            self._create_ideal_lap_ranking_window()
        
        if IdealLapAnalysisOptionsDialog.TYPE_SECTOR_HEATMAP in selected_types:
            self._create_ideal_lap_heatmap_window()
        
        if IdealLapAnalysisOptionsDialog.TYPE_SECTOR_COMPARISON in selected_types:
            self._create_ideal_lap_comparison_window()
    else:
        print("[DIALOG] 使用者取消理想圈分析選項")
```

### 與主選單整合
```python
# f1t_gui_main.py 中新增選單項目
ideal_lap_action = QAction("Ideal Lap Analysis", self)
ideal_lap_action.setStatusTip("Analyze ideal lap potential for all drivers")
ideal_lap_action.triggered.connect(self._prompt_ideal_lap_options)
analysis_menu.addAction(ideal_lap_action)
```

### 測試項目
| 測試項目 | 說明 |
|----------|------|
| 對話框顯示 | 開啟後正確顯示 3 個選項 |
| 多選功能 | 可同時勾選多個分析類型 |
| 全選/清空 | 快速選擇按鈕功能正常 |
| 取消操作 | 點擊 Cancel 不觸發任何分析 |
| 確認操作 | 點擊 OK 後正確開啟選中的視窗 |
| 樣式一致性 | 與現有對話框視覺風格一致 |
| i18n | 中英文切換正常 |

---

## 📌 下一步建議

1. 建立 `tasks/GUI/IdealLap_RankingTable/task.md`，規劃驗收清單
2. 確認 FastF1 車隊顏色映射資源位置 (`core/team_colors.py`)
3. **實作 IdealLapAnalysisOptionsDialog 對話框** ⭐ 新增
4. 實作 DataLoader 骨架與 JSON 解析測試
5. 建立表格視窗原型，預留深度視圖接口
6. **在主視窗選單中添加「Ideal Lap Analysis」入口** ⭐ 新增
7. 制定單元測試 (模擬 JSON 資料)
8. 更新 GUI 使用手冊

---

> 本文件為初版規劃，後續若需求更新，請同步修訂並記錄變更。
