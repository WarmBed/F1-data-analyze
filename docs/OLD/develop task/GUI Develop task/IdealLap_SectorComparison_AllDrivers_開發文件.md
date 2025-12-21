# 理想圈分段對比圖 (全車手) - GUI 模組規劃

**模組分類**: GUI Develop Task  
**對應 CLI 功能**: Function 53 - Ideal Lap Analysis (All Drivers)  
**狀態**: 📝 規劃草案  
**建立日期**: 2025-10-09  
**最後更新**: 2025-10-09

---

## 🎯 目標概述

建立一個 GUI 深度視圖，使用 **水平棒狀圖 (Horizontal Bar Chart)** 展示全車手的理想圈分段構成與最快圈對比，協助分析各車手在分段層級的潛力與損失。資料來源為 CLI Function 53 輸出的 JSON (`ideal_lap_detail.sector_sources` 與 `sector_breakdown`)，支援 API-ONLY 模式。

### 關鍵問題
- 各車手的理想圈由哪些圈數的分段組成?
- 車手的最快圈與理想圈在各分段的時間差距?
- 哪些車手在最快圈中已發揮全部分段潛力 (分段時間接近理想)?
- 車隊內兩位車手的分段表現差異?

---

## 📊 視覺化需求

### 主圖表結構

**水平堆疊棒狀圖** - 每位車手顯示兩條棒狀:
1. **理想圈棒** (上方): 顯示 S1 + S2 + S3 的理想分段時間
2. **最快圈棒** (下方): 顯示該車手最快圈的實際分段時間

```
SAI  理想圈 ████████████████████████████████████ 1:30.625
     最快圈 █████████████████████████████████████ 1:31.106
          S1: 31.320 (L42) | S2: 41.605 (L23) | S3: 17.700 (L18)
          S1: 31.488 [+0.168❌] | S2: 41.857 [+0.252❌] | S3: 17.761 [+0.061❌]

ANT  理想圈 ████████████████████████████████████ 1:30.643
     最快圈 ████████████████████████████████████ 1:30.965
          S1: 31.257 (L41) | S2: 41.680 (L29) | S3: 17.706 (L42)
          S1: 31.257 [✓] | S2: 41.821 [+0.141❌] | S3: 17.887 [+0.181❌]
...
```

### 顏色編碼規則
- **分段顏色** (堆疊區塊):
  - S1: 🔵 藍色 (`#1f77b4`)
  - S2: 🟢 綠色 (`#2ca02c`)
  - S3: 🟠 橙色 (`#ff7f0e`)
- **時間差標記**:
  - ✓ 綠色勾號: 該分段在最快圈中為最佳 (差距 < 0.01s)
  - ❌ 紅色叉號: 該分段在最快圈中未達最佳
  - 差距數值顏色: 綠色 (<0.1s) → 黃色 (0.1-0.3s) → 紅色 (>0.3s)

### 資料來源
**來自 JSON 路徑**:
```json
{
  "analysis_result": {
    "ranking": [
      {
        "driver": "SAI",
        "ideal_lap_time": 90.625,
        "fastest_lap_time": 91.106,
        "sector_breakdown": {
          "sector_1": {"time": 31.320, "is_optimal_in_fastest": false},
          "sector_2": {"time": 41.605, "is_optimal_in_fastest": false},
          "sector_3": {"time": 17.700, "is_optimal_in_fastest": false}
        },
        "ideal_lap_detail": {
          "sector_sources": {
            "s1": {"lap": 42, "time": 31.320},
            "s2": {"lap": 23, "time": 41.605},
            "s3": {"lap": 18, "time": 17.700}
          }
        }
      }
    ]
  }
}
```

### 互動功能
1. **懸停提示 (Tooltip)**:
   ```
   車手: SAI
   理想圈 S1: 31.320s (來自 Lap 42)
   最快圈 S1: 31.488s (Lap 41)
   差距: +0.168s (+0.54%)
   狀態: ❌ 未達最佳
   ```

2. **點擊棒狀**:
   - 高亮該車手的兩條棒狀
   - 彈出該車手的逐圈分段趨勢圖 (可選)

3. **排序選項**:
   - 依理想圈總時間排序 (預設)
   - 依最快圈總時間排序
   - 依時間差排序 (理想 vs 最快)
   - 依車隊分組排序

4. **篩選器**:
   - 車隊多選
   - 顯示範圍 (Top 10 / Top 5 / All)
   - 只顯示「有潛力提升」的車手 (時間差 > 0.3s)

### 統計面板
**位於圖表上方**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 分段潛力統計                                             │
├─────────┬──────────┬──────────┬──────────┬─────────────────┤
│ 分段    │ 平均損失 │ 最大損失 │ 最小損失 │ 完美車手數      │
├─────────┼──────────┼──────────┼──────────┼─────────────────┤
│ S1      │ +0.142s  │ +0.325s  │ 0.000s   │ 2 位 (10%)      │
│         │          │ (DOO)    │ (NOR)    │                 │
├─────────┼──────────┼──────────┼──────────┼─────────────────┤
│ S2      │ +0.187s  │ +0.421s  │ 0.000s   │ 1 位 (5%)       │
│         │          │ (DOO)    │ (HAM)    │                 │
├─────────┼──────────┼──────────┼──────────┼─────────────────┤
│ S3      │ +0.098s  │ +0.289s  │ 0.000s   │ 3 位 (15%)      │
│         │          │ (DOO)    │ (SAI)    │                 │
└─────────┴──────────┴──────────┴──────────┴─────────────────┘
```

---

## 🧱 架構設計

### MDI 與元件
- `UniversalAnalysisMDI` 新增「理想圈分段對比」子視窗
- 視窗內容:
  - **上半部**: 統計面板 (`QGroupBox`)
  - **中間部**: 水平棒狀圖主視圖 (`matplotlib.axes.Axes`)
  - **下半部**: 篩選控制面板
- API-ONLY 概念:
  - 使用 `IdealLapSectorComparisonLoader` (共用 Function 53 資料)
  - 複用 `IdealLapRankingDataLoader` 的載入邏輯

### 資料流程
1. **載入階段**:
   ```python
   loader = IdealLapSectorComparisonLoader(year=2025, race="Japan", session="R")
   data = loader.fetch_data()  # 複用 Function 53 JSON
   ```

2. **轉換階段**:
   ```python
   def _transform_data_for_display(self, data):
       comparison_data = []
       for driver in data["analysis_result"]["ranking"]:
           ideal_sectors = [
               driver["sector_breakdown"]["sector_1"]["time"],
               driver["sector_breakdown"]["sector_2"]["time"],
               driver["sector_breakdown"]["sector_3"]["time"]
           ]
           # 從 laps 中找到最快圈的分段時間
           fastest_lap = self._find_fastest_lap(driver["laps"])
           comparison_data.append({
               "driver": driver["driver"],
               "ideal_sectors": ideal_sectors,
               "fastest_sectors": fastest_lap["sectors"],
               "sources": driver["ideal_lap_detail"]["sector_sources"],
               "is_optimal": [
                   driver["sector_breakdown"]["sector_1"]["is_optimal_in_fastest"],
                   driver["sector_breakdown"]["sector_2"]["is_optimal_in_fastest"],
                   driver["sector_breakdown"]["sector_3"]["is_optimal_in_fastest"]
               ]
           })
       return comparison_data
   ```

3. **渲染階段**:
   ```python
   def draw_stacked_bars(self, comparison_data):
       fig, ax = plt.subplots(figsize=(12, 10))
       
       for idx, driver_data in enumerate(comparison_data):
           y_pos_ideal = idx * 2
           y_pos_fastest = idx * 2 + 1
           
           # 理想圈堆疊棒
           ax.barh(y_pos_ideal, driver_data["ideal_sectors"][0], 
                   color="#1f77b4", label="S1" if idx == 0 else "")
           ax.barh(y_pos_ideal, driver_data["ideal_sectors"][1], 
                   left=driver_data["ideal_sectors"][0], 
                   color="#2ca02c", label="S2" if idx == 0 else "")
           ax.barh(y_pos_ideal, driver_data["ideal_sectors"][2], 
                   left=sum(driver_data["ideal_sectors"][:2]), 
                   color="#ff7f0e", label="S3" if idx == 0 else "")
           
           # 最快圈堆疊棒 (類似邏輯)
           # ...
           
           # 添加時間差標記
           self._add_delta_annotations(ax, y_pos_fastest, driver_data)
   ```

---

## 🛠️ 實作步驟 (遵循通用模組模式)

### Phase 1: 模組介面實作 (IdealLapSectorComparisonModule)

**參考**: `modules/gui/rain_analysis/rain_analysis_module.py`

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_module.py
from modules.gui.interfaces.analysis_module import IAnalysisModule

class IdealLapSectorComparisonModule(IAnalysisModule):
    """理想圈 vs 最快圈分段比較模組"""
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        super().__init__(parent)
        
        self._module_name = "IdealLapSectorComparison"
        self._display_name = "📈 Sector Comparison (Ideal vs Fastest)"
        self._version = "1.0.0"
        self._description = "Ideal Lap vs Fastest Lap Sector Breakdown"
        
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        self._comparison_core = None
        self.initialize_module(parent)
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        try:
            if not self._comparison_core:
                from .ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI
                self._comparison_core = IdealLapSectorComparisonMDI(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    parent=parent_widget
                )
            
            self._main_widget = self._comparison_core.get_widget()
            self._is_initialized = True
            print("✅ [COMPARISON_MODULE] 模組已初始化")
            return True
        except Exception as e:
            print(f"❌ [COMPARISON_MODULE] 初始化失敗: {e}")
            return False
    
    # 實作其他 IAnalysisModule 方法...
```

### Phase 2: MDI 視窗實作 (IdealLapSectorComparisonMDI)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_mdi.py
from modules.gui.base.universal_analysis_mdi import UniversalAnalysisMDI

class IdealLapSectorComparisonMDI(UniversalAnalysisMDI):
    """分段比較圖 MDI 視窗"""
    
    def __init__(self, year, race, session, parent=None):
        config = {
            "window_title": f"Sector_Comparison_{year}_{race}_{session}",
            "default_size": (1400, 1000),
            "module_type": "ideal_lap_comparison"
        }
        super().__init__(year, race, session, parent, **config)
        self._init_ui()
        self.load_initial_data()
    
    def _create_data_loader(self):
        from .ideal_lap_sector_comparison_data_loader import IdealLapSectorComparisonDataLoader
        return IdealLapSectorComparisonDataLoader(
            year=self.year,
            race=self.race,
            session=self.session,
            parent=self
        )
    
    def _create_chart_widget(self):
        from .ideal_lap_sector_comparison_widget import IdealLapSectorComparisonWidget
        return IdealLapSectorComparisonWidget(parent=self)
    
    def _init_ui(self):
        # 統計面板
        self.stats_panel = self._create_stats_panel()
        
        # 棒狀圖 (chart_widget)
        self.comparison_chart = self.chart_widget
        
        # 控制面板
        self.control_panel = self._create_control_panel()
        
        self._organize_layout()
    
    def _on_data_loaded(self, data):
        """資料載入完成回調"""
        if not data or not data.get("success"):
            return
        
        # 更新棒狀圖
        self.comparison_chart.draw_comparison_bars(
            data["comparison_data"]
        )
```

### Phase 3: 資料載入器實作 (IdealLapSectorComparisonDataLoader)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_data_loader.py
from modules.gui.base.universal_data_loader_base import UniversalDataLoader

class IdealLapSectorComparisonDataLoader(UniversalDataLoader):
    """分段比較資料載入器"""
    
    CLI_FUNCTION = 53
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    def _validate_data_format(self, data):
        required = ["ranking", "sector_comparison"]
        return all(k in data["analysis_result"] for k in required)
    
    def _transform_data_for_display(self, data):
        """轉換為棒狀圖資料格式"""
        ranking = data["analysis_result"]["ranking"]
        
        comparison_data = []
        for driver_data in ranking:
            # 理想圈分段
            ideal_sectors = driver_data["ideal_lap_detail"]["sector_sources"]
            ideal_times = [
                ideal_sectors["s1"]["time"],
                ideal_sectors["s2"]["time"],
                ideal_sectors["s3"]["time"]
            ]
            
            # 最快圈分段
            fastest_lap = self._find_fastest_lap(driver_data["laps"])
            fastest_times = fastest_lap["sector_times"] if fastest_lap else [0, 0, 0]
            
            # 判斷最佳分段 (is_optimal)
            sector_breakdown = driver_data["sector_breakdown"]
            is_optimal = [
                sector_breakdown["s1"]["is_optimal_in_fastest"],
                sector_breakdown["s2"]["is_optimal_in_fastest"],
                sector_breakdown["s3"]["is_optimal_in_fastest"]
            ]
            
            comparison_data.append({
                "driver": driver_data["driver"],
                "team": driver_data["team"],
                "ideal_sectors": ideal_times,
                "fastest_sectors": fastest_times,
                "is_optimal": is_optimal,
                "delta": [f - i for i, f in zip(ideal_times, fastest_times)]
            })
        
        return {
            "comparison_data": comparison_data,
            **data
        }
    
    def _find_fastest_lap(self, laps):
        """從 laps 陣列中找到最快圈"""
        if not laps:
            return None
        
        fastest = min(laps, key=lambda x: x["lap_time_seconds"])
        return fastest
```

### Phase 4: 棒狀圖元件實作 (IdealLapSectorComparisonWidget)

```python
# modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_widget.py
from modules.gui.base.universal_chart_widget import UniversalChartWidget
from PyQt5.QtCore import pyqtSignal
import numpy as np

class IdealLapSectorComparisonWidget(UniversalChartWidget):
    """分段比較棒狀圖元件"""
    
    bar_clicked = pyqtSignal(str)  # 發射車手代碼
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.comparison_data = None
    
    def draw_comparison_bars(self, comparison_data):
        """繪製堆疊棒狀圖"""
        self.comparison_data = comparison_data
        
        self.ax.clear()
        
        # 準備資料
        drivers = [d["driver"] for d in comparison_data]
        y_pos = np.arange(len(drivers))
        
        # 兩組資料：理想圈 vs 最快圈
        ideal_s1 = [d["ideal_sectors"][0] for d in comparison_data]
        ideal_s2 = [d["ideal_sectors"][1] for d in comparison_data]
        ideal_s3 = [d["ideal_sectors"][2] for d in comparison_data]
        
        fastest_s1 = [d["fastest_sectors"][0] for d in comparison_data]
        fastest_s2 = [d["fastest_sectors"][1] for d in comparison_data]
        fastest_s3 = [d["fastest_sectors"][2] for d in comparison_data]
        
        # 繪製堆疊棒狀圖
        self.ax.barh(y_pos - 0.2, ideal_s1, height=0.4, color='#1f77b4', label='Ideal S1')
        self.ax.barh(y_pos - 0.2, ideal_s2, height=0.4, left=ideal_s1, color='#2ca02c', label='Ideal S2')
        self.ax.barh(y_pos - 0.2, ideal_s3, height=0.4, left=np.array(ideal_s1)+np.array(ideal_s2), color='#ff7f0e', label='Ideal S3')
        
        self.ax.barh(y_pos + 0.2, fastest_s1, height=0.4, color='#1f77b4', alpha=0.5)
        self.ax.barh(y_pos + 0.2, fastest_s2, height=0.4, left=fastest_s1, color='#2ca02c', alpha=0.5)
        self.ax.barh(y_pos + 0.2, fastest_s3, height=0.4, left=np.array(fastest_s1)+np.array(fastest_s2), color='#ff7f0e', alpha=0.5, label='Fastest Lap')
        
        # 添加時間差標記
        self._add_delta_markers(comparison_data, y_pos)
        
        # 設置標籤
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(drivers)
        self.ax.set_xlabel("Lap Time (seconds)")
        self.ax.set_title("Ideal Lap vs Fastest Lap Sector Breakdown")
        self.ax.legend()
        
        self.canvas.draw()
    
    def _add_delta_markers(self, comparison_data, y_pos):
        """添加 ✓/❌ 標記與時間差"""
        for idx, driver_data in enumerate(comparison_data):
            total_ideal = sum(driver_data["ideal_sectors"])
            total_fastest = sum(driver_data["fastest_sectors"])
            delta = total_fastest - total_ideal
            
            # 在棒狀圖右側添加文字
            marker = "✓" if delta < 0.3 else "❌"
            color = "green" if delta < 0.3 else "red"
            
            self.ax.text(
                total_ideal + 1, 
                y_pos[idx], 
                f"{marker} {delta:+.3f}s", 
                color=color,
                va='center'
            )
```

---
    def _update_statistics_panel(self, comparison_data):
        # 計算平均損失、最大損失、完美車手數
        pass
    
    def _on_bar_clicked(self, driver_code):
        # 可選: 打開該車手的逐圈分段趨勢圖
        pass
```

---

## ✅ 測試計畫

| 測試項目 | 說明 |
|----------|------|
| 資料轉換 | 驗證理想圈與最快圈分段資料正確提取 |
| 棒狀圖渲染 | 堆疊區塊寬度與顏色正確，無重疊或間隙 |
| 時間差計算 | 差距數值與 JSON 一致，✓/❌ 標記正確 |
| 顏色編碼 | 分段顏色與差距顏色梯度正確 |
| Tooltip | 懸停顯示完整資訊且不卡頓 |
| 排序功能 | 依不同規則排序後圖表更新正確 |
| 篩選器 | 車隊/範圍篩選正確過濾資料 |
| 統計面板 | 統計數值計算正確 |
| 空資料處理 | 若最快圈缺失分段資料，顯示友善提示 |
| i18n | 支援中英文切換 |

---

## ⚠️ 風險與注意事項

- **最快圈分段提取**: 需從 `laps` 陣列中找到 `lap_time_seconds` 最小的圈，並提取其 `sector_times`
- **堆疊棒渲染**: 需確保分段累加邏輯正確，避免視覺錯位
- **標記位置**: ✓/❌ 標記需避免與棒狀圖重疊，可能需動態調整位置
- **大量車手**: 20 位車手 × 2 條棒 = 40 條，需確保 Y 軸間距足夠清晰
- **API-ONLY 限制**: 若資料不存在，需引導使用者執行 API 分析

---

## 🎨 UI Mock (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 📊 分段潛力統計                                                          │
│ S1: 平均損失 +0.142s | S2: 平均損失 +0.187s | S3: 平均損失 +0.098s    │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ 排序: [理想圈▼]  篩選: [車隊▼] [Top 10▼]  匯出: [PNG] [CSV]           │
└──────────────────────────────────────────────────────────────────────────┘

SAI  理想圈 |████S1████|██████S2██████|█S3█| 1:30.625
     最快圈 |█████S1████|███████S2██████|█S3█| 1:31.106
              ❌ +0.168  ❌ +0.252       ❌ +0.061

ANT  理想圈 |████S1████|██████S2██████|█S3█| 1:30.643
     最快圈 |████S1████|██████S2██████|██S3█| 1:30.965
              ✓ 0.000   ❌ +0.141       ❌ +0.181

PIA  理想圈 |████S1████|██████S2██████|█S3█| 1:30.734
     最快圈 |████S1████|██████S2██████|█S3█| 1:31.039
              ❌ +0.105  ❌ +0.140       ❌ +0.060

...

┌──────────────────────────────────────────────────────────────────────────┐
│ 圖例: 🔵 S1 | 🟢 S2 | 🟠 S3 | ✓ 完美分段 | ❌ 可改進分段              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 下一步建議

1. 建立 `tasks/GUI/IdealLap_SectorComparison/task.md`，規劃驗收清單
2. 確認 matplotlib 堆疊棒狀圖最佳實作方式 (`barh` + `left` 參數)
3. 實作最快圈分段提取邏輯與單元測試
4. 建立棒狀圖視窗原型，預留統計面板接口
5. 設計時間差標記的視覺化方案 (文字顏色、位置、圖示)
6. 制定單元測試 (模擬 JSON 資料)

---

## 💡 進階功能構想 (可選)

### 逐圈分段趨勢圖
點擊某位車手的棒狀圖後，彈出新視窗顯示該車手全部圈速的分段時間趨勢:
```
S1 趨勢折線圖 (圈數 vs 時間)
S2 趨勢折線圖
S3 趨勢折線圖
高亮理想分段來源圈 (星號標記)
```

### 車隊對比模式
並排顯示同車隊兩位車手的分段對比:
```
Mercedes
  ANT  理想圈 |████|██████|█| 1:30.643
       最快圈 |████|███████|██| 1:30.965
  
  RUS  理想圈 |████|██████|█| 1:30.789
       最快圈 |█████|███████|██| 1:31.357
```

---

> 本文件為初版規劃，後續若需求更新，請同步修訂並記錄變更。
