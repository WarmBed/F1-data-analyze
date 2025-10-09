# 分段熱力圖 (全車手) - GUI 模組規劃

**模組分類**: GUI Develop Task  
**對應 CLI 功能**: Function 53 - Ideal Lap Analysis (All Drivers)  
**狀態**: 📝 規劃草案  
**建立日期**: 2025-10-09  
**最後更新**: 2025-10-09

---

## 🎯 目標概述

建立一個 GUI 視覺化視圖，使用 **熱力圖 (Heatmap)** 展示各車手在三個分段 (S1/S2/S3) 的最佳表現，協助快速識別各車手在不同賽道區段的優勢與劣勢。資料來源為 CLI Function 53 輸出的 JSON (`sector_breakdown` 與 `ideal_lap_detail.sector_sources`)，支援 API-ONLY 模式。

### 關鍵問題
- 哪些車手在 S1/S2/S3 擁有全場最快時間?
- 各車手的分段表現是否均衡，或在特定區段有明顯優勢?
- 車隊內兩位車手的分段表現差異如何?
- 分段時間分佈的整體趨勢 (最快/最慢/平均差距)?

---

## 📊 視覺化需求

### 熱力圖結構

**矩陣佈局**: 3 行 (S1/S2/S3) × 20 列 (車手代碼)

```
        SAI   ANT   PIA   RUS   NOR   HAM   VER   ALB   LEC   ...
S1     31.32  31.26 31.25 31.32 31.23 31.29 31.27 31.39 31.48  ...
S2     41.61  41.68 41.69 41.77 41.77 41.40 41.78 41.68 41.79  ...
S3     17.70  17.71 17.80 17.70 17.81 17.85 17.80 17.89 17.79  ...
```

### 顏色編碼規則
- **綠色梯度**: 該分段的全場最快時間 → 深綠色 (#006400)
- **黃色梯度**: 中等時間 → 黃色 (#FFD700)
- **紅色梯度**: 該分段的全場最慢時間 → 深紅色 (#8B0000)
- **色標 (Colorbar)**: 顯示時間刻度 (秒數)

### 資料來源
**來自 JSON 路徑**:
```json
{
  "analysis_result": {
    "ranking": [
      {
        "driver": "SAI",
        "ideal_lap_detail": {
          "sector_sources": {
            "s1": {"lap": 42, "time": 31.320},
            "s2": {"lap": 23, "time": 41.605},
            "s3": {"lap": 18, "time": 17.700}
          }
        }
      }
    ],
    "sector_comparison": {
      "sector_1": {
        "fastest_time": 31.235,
        "slowest_time": 32.240,
        "fastest_driver": "NOR",
        "slowest_driver": "DOO"
      }
    }
  }
}
```

### 互動功能
1. **懸停提示 (Tooltip)**:
   ```
   車手: SAI
   分段: S1
   時間: 31.320s (Lap 42)
   排名: 全場第 2 快
   差距最快: +0.085s
   ```

2. **點擊單元格**:
   - 高亮該車手的所有分段
   - 彈出該車手的詳細分段對比視圖

3. **排序選項**:
   - 依理想圈總時間排序 (預設)
   - 依車隊分組排序
   - 依特定分段時間排序 (S1/S2/S3)

4. **標記功能**:
   - **星號 (★)**: 該分段為全場最快
   - **圓圈 (○)**: 該車手最快圈中該分段為最佳分段

### 統計面板
**位於熱力圖下方**，顯示 `sector_comparison`:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 分段統計摘要                                             │
├─────────┬──────────┬──────────┬──────────┬─────────────────┤
│ 分段    │ 最快時間 │ 最慢時間 │ 平均時間 │ 時間範圍        │
├─────────┼──────────┼──────────┼──────────┼─────────────────┤
│ S1      │ 31.235s  │ 32.240s  │ 31.669s  │ 1.005s (3.22%)  │
│         │ (NOR)    │ (DOO)    │          │                 │
├─────────┼──────────┼──────────┼──────────┼─────────────────┤
│ S2      │ 41.404s  │ 42.188s  │ 41.701s  │ 0.784s (1.89%)  │
│         │ (HAM)    │ (DOO)    │          │                 │
├─────────┼──────────┼──────────┼──────────┼─────────────────┤
│ S3      │ 17.700s  │ 18.141s  │ 17.911s  │ 0.441s (2.49%)  │
│         │ (SAI)    │ (DOO)    │          │                 │
└─────────┴──────────┴──────────┴──────────┴─────────────────┘
```

---

## 🧱 架構設計

### MDI 與元件
- `UniversalAnalysisMDI` 新增「分段熱力圖」子視窗
- 視窗內容:
  - **上半部**: 熱力圖主視圖 (`matplotlib.axes.Axes` + `imshow` 或 `seaborn.heatmap`)
  - **下半部**: 分段統計面板 (`QTableWidget`)
  - **側邊欄**: 排序控制、標記開關
- API-ONLY 概念:
  - 使用 `IdealLapHeatmapDataLoader` (共用 Function 53 資料)
  - 從 `IdealLapRankingDataLoader` 繼承或直接複用載入邏輯

### 資料流程
1. **載入階段**:
   ```python
   loader = IdealLapHeatmapDataLoader(year=2025, race="Japan", session="R")
   data = loader.fetch_data()  # 複用 Function 53 JSON
   ```

2. **轉換階段**:
   ```python
   def _transform_data_for_display(self, data):
       # 建立 DataFrame: columns=[driver], index=[S1, S2, S3]
       sector_matrix = []
       for driver in data["analysis_result"]["ranking"]:
           s1 = driver["ideal_lap_detail"]["sector_sources"]["s1"]["time"]
           s2 = driver["ideal_lap_detail"]["sector_sources"]["s2"]["time"]
           s3 = driver["ideal_lap_detail"]["sector_sources"]["s3"]["time"]
           sector_matrix.append([s1, s2, s3])
       
       df = pd.DataFrame(
           sector_matrix,
           columns=[d["driver"] for d in data["analysis_result"]["ranking"]],
           index=["S1", "S2", "S3"]
       )
       return df.T  # 轉置: 車手為行，分段為列
   ```

3. **渲染階段**:
   ```python
   import seaborn as sns
   import matplotlib.pyplot as plt
   
   sns.heatmap(
       sector_df,
       annot=True,          # 顯示數值
       fmt=".3f",           # 3 位小數
       cmap="RdYlGn_r",     # 紅黃綠反向 (低值綠色)
       cbar_kws={"label": "Sector Time (s)"},
       linewidths=0.5,
       linecolor="gray"
   )
   ```

---

## 🛠️ 實作步驟 (遵循通用模組模式)

### Phase 1: 模組介面實作 (IdealLapSectorHeatmapModule)

**參考**: `modules/gui/rain_analysis/rain_analysis_module.py`

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_module.py
from modules.gui.interfaces.analysis_module import IAnalysisModule

class IdealLapSectorHeatmapModule(IAnalysisModule):
    """理想圈分段熱力圖模組"""
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        super().__init__(parent)
        
        self._module_name = "IdealLapSectorHeatmap"
        self._display_name = "🔥 Sector Heatmap (All Drivers)"
        self._version = "1.0.0"
        self._description = "Sector Performance Heatmap Visualization"
        
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        self._heatmap_core = None
        self.initialize_module(parent)
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        try:
            if not self._heatmap_core:
                from .ideal_lap_sector_heatmap_mdi import IdealLapSectorHeatmapMDI
                self._heatmap_core = IdealLapSectorHeatmapMDI(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    parent=parent_widget
                )
            
            self._main_widget = self._heatmap_core.get_widget()
            self._is_initialized = True
            print("✅ [HEATMAP_MODULE] 模組已初始化")
            return True
        except Exception as e:
            print(f"❌ [HEATMAP_MODULE] 初始化失敗: {e}")
            return False
    
    # 實作其他 IAnalysisModule 方法...
```

### Phase 2: MDI 視窗實作 (IdealLapSectorHeatmapMDI)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_mdi.py
from modules.gui.base.universal_analysis_mdi import UniversalAnalysisMDI

class IdealLapSectorHeatmapMDI(UniversalAnalysisMDI):
    """分段熱力圖 MDI 視窗"""
    
    def __init__(self, year, race, session, parent=None):
        config = {
            "window_title": f"Sector_Heatmap_{year}_{race}_{session}",
            "default_size": (1200, 800),
            "module_type": "ideal_lap_heatmap"
        }
        super().__init__(year, race, session, parent, **config)
        self._init_ui()
        self.load_initial_data()
    
    def _create_data_loader(self):
        from .ideal_lap_sector_heatmap_data_loader import IdealLapSectorHeatmapDataLoader
        return IdealLapSectorHeatmapDataLoader(
            year=self.year,
            race=self.race,
            session=self.session,
            parent=self
        )
    
    def _create_chart_widget(self):
        from .ideal_lap_sector_heatmap_widget import IdealLapSectorHeatmapWidget
        return IdealLapSectorHeatmapWidget(parent=self)
    
    def _init_ui(self):
        # 統計面板
        self.stats_panel = self._create_stats_panel()
        
        # 熱力圖 (chart_widget)
        self.heatmap = self.chart_widget
        
        # 控制面板 (排序、篩選)
        self.control_panel = self._create_control_panel()
        
        self._organize_layout()
    
    def _on_data_loaded(self, data):
        """資料載入完成回調"""
        if not data or not data.get("success"):
            return
        
        # 更新熱力圖
        self.heatmap.draw_heatmap(
            data["sector_matrix"],
            data["annotations"]
        )
```

### Phase 3: 資料載入器實作 (IdealLapSectorHeatmapDataLoader)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_data_loader.py
from modules.gui.base.universal_data_loader_base import UniversalDataLoader
import pandas as pd

class IdealLapSectorHeatmapDataLoader(UniversalDataLoader):
    """分段熱力圖資料載入器"""
    
    CLI_FUNCTION = 53
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    def _validate_data_format(self, data):
        required = ["ranking", "sector_comparison"]
        return all(k in data["analysis_result"] for k in required)
    
    def _transform_data_for_display(self, data):
        """轉換為熱力圖矩陣 + 標註資訊"""
        ranking = data["analysis_result"]["ranking"]
        
        # 建立 DataFrame (車手 x 分段)
        matrix_data = []
        for driver_data in ranking:
            sectors = driver_data["ideal_lap_detail"]["sector_sources"]
            matrix_data.append({
                "driver": driver_data["driver"],
                "s1": sectors["s1"]["time"],
                "s2": sectors["s2"]["time"],
                "s3": sectors["s3"]["time"]
            })
        
        df = pd.DataFrame(matrix_data)
        df = df.set_index("driver").T  # 轉置為 (S1/S2/S3 x 車手)
        
        # 找出最快車手並標註
        annotations = self._create_annotations(
            df, 
            data["analysis_result"]["sector_comparison"]
        )
        
        return {
            "sector_matrix": df,
            "annotations": annotations,
            **data
        }
    
    def _create_annotations(self, df, sector_comp):
        """創建標註資訊 (★ 標記等)"""
        annotations = {}
        for sector, info in sector_comp.items():
            fastest_driver = info["fastest_driver"]
            annotations[sector] = {
                "fastest": fastest_driver,
                "time": info["fastest_time"]
            }
        return annotations
```

### Phase 4: 熱力圖元件實作 (IdealLapSectorHeatmapWidget)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_widget.py
from modules.gui.base.universal_chart_widget import UniversalChartWidget
import seaborn as sns
from PyQt5.QtCore import pyqtSignal

class IdealLapSectorHeatmapWidget(UniversalChartWidget):
    """分段熱力圖繪製元件"""
    
    cell_clicked = pyqtSignal(str, str)  # (driver, sector)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_df = None
        self.annotations = None
    
    def draw_heatmap(self, sector_df, annotations):
        """繪製熱力圖"""
        self.sector_df = sector_df
        self.annotations = annotations
        
        self.ax.clear()
        
        # 使用 seaborn heatmap
        sns.heatmap(
            sector_df,
            ax=self.ax,
            cmap="RdYlGn_r",  # 紅-黃-綠
            annot=True,
            fmt=".3f",
            cbar_kws={"label": "Sector Time (s)"}
        )
        
        # 添加最快標記 (★)
        self._add_fastest_markers(annotations)
        
        # 設置標籤
        self.ax.set_xlabel("Driver")
        self.ax.set_ylabel("Sector")
        self.ax.set_title("Ideal Lap Sector Performance Heatmap")
        
        # 啟用懸停提示
        self._setup_hover_tooltip()
        
        self.canvas.draw()
    
    def _add_fastest_markers(self, annotations):
        """在最快單元格上添加 ★"""
        for sector, info in annotations.items():
            fastest_driver = info["fastest"]
            # 找到對應位置並繪製星號
            # ... matplotlib 文字標註
            pass
    
    def _setup_hover_tooltip(self):
        """設置懸停提示"""
        # mplcursors 或 matplotlib event handler
        pass
```

---

---

## ✅ 測試計畫

| 測試項目 | 說明 |
|----------|------|
| 資料轉換 | 驗證 DataFrame 結構正確 (20 行 × 3 列) |
| 顏色映射 | 最快時間為綠色，最慢為紅色，梯度平滑 |
| 標記顯示 | 全場最快分段標記 ★，車手最佳分段標記 ○ |
| Tooltip | 懸停顯示完整資訊且不卡頓 |
| 排序功能 | 依不同規則排序後熱力圖更新正確 |
| 點擊事件 | 點擊單元格觸發詳情視圖 |
| 統計面板 | 分段統計數值與 JSON 一致 |
| 空資料處理 | 若分段資料缺失，顯示友善提示 |
| i18n | 支援中英文切換 (分段名稱、統計文字) |

---

## ⚠️ 風險與注意事項

- **Seaborn 依賴**: 需確認專案是否已引入 seaborn，若無需評估是否使用純 matplotlib 實現
- **顏色對比度**: 確保數值文字在各種背景色下可讀 (黑色/白色自動切換)
- **大矩陣渲染**: 20x3 矩陣渲染速度需優化，避免卡頓
- **標記重疊**: 若單元格同時為全場最快 + 車手最佳，需清晰顯示雙重標記
- **API-ONLY 限制**: 若資料不存在，需引導使用者執行 API 分析

---

## 🎨 UI Mock (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 排序: [理想圈總時間▼]  標記: [✓顯示全場最快] [✓顯示車手最佳]          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│        SAI    ANT    PIA    RUS    NOR    HAM    VER    ALB    LEC   ... │
│ S1    31.32  31.26  31.25  31.32  31.23★ 31.29  31.27  31.39  31.48      │
│       [🟢]   [🟢]   [🟢]   [🟢]   [🟢]   [🟢]   [🟢]   [🟡]   [🟡]      │
│                                                                            │
│ S2    41.61  41.68  41.69  41.77  41.77  41.40★ 41.78  41.68  41.79      │
│       [🟢]   [🟢]   [🟢]   [🟡]   [🟡]   [🟢]   [🟡]   [🟢]   [🟡]      │
│                                                                            │
│ S3    17.70★ 17.71  17.80  17.70  17.81  17.85  17.80  17.89  17.79      │
│       [🟢]   [🟢]   [🟡]   [🟢]   [🟡]   [🟡]   [🟡]   [🔴]   [🟡]      │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ 📊 分段統計摘要                                                          │
│ S1: 最快 31.235s (NOR) | 最慢 32.240s (DOO) | 範圍 1.005s              │
│ S2: 最快 41.404s (HAM) | 最慢 42.188s (DOO) | 範圍 0.784s              │
│ S3: 最快 17.700s (SAI) | 最慢 18.141s (DOO) | 範圍 0.441s              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 下一步建議

1. 建立 `tasks/GUI/IdealLap_Heatmap/task.md`，規劃驗收清單
2. 確認是否需要引入 seaborn 或使用純 matplotlib
3. 實作資料轉換邏輯與 DataFrame 建構測試
4. 建立熱力圖視窗原型，預留點擊事件接口
5. 制定單元測試 (模擬 JSON 資料)
6. 設計標記圖示 (★ / ○) 的視覺化方案

---

> 本文件為初版規劃，後續若需求更新，請同步修訂並記錄變更。
