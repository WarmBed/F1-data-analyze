# FastF1 賽事名次資訊調查報告

**調查日期**: 2025-10-22  
**調查目標**: 確認 FastF1 是否提供賽事結束後的名次、上升/下降名次等資訊  
**測試案例**: 2024年日本大獎賽正賽 (Japan GP - Race)

---

## 📊 調查結論

### ✅ **FastF1 完整提供賽事名次相關資訊**

FastF1 通過 `session.results` 和 `session.laps` 提供了完整的賽事名次數據，包括：

1. ✅ **最終名次** (Position)
2. ✅ **起始名次** (GridPosition - 排位賽位置)
3. ✅ **名次變化** (可計算: GridPosition - Position)
4. ✅ **逐圈位置追蹤** (Laps 中的 Position 欄位)
5. ✅ **完賽狀態** (Status: Finished, DNF, Retired, Lapped)
6. ✅ **積分** (Points)
7. ✅ **完賽時間** (Time)

---

## 🔍 數據結構詳解

### 1. **Session Results (session.results)**

這是 FastF1 最主要的賽事結果數據源，包含以下欄位：

```python
results = session.results

# 可用欄位列表
columns = [
    'DriverNumber',         # 車號
    'BroadcastName',        # 廣播名稱
    'Abbreviation',         # 車手代碼 (如 VER, LEC)
    'DriverId',            # 車手 ID
    'TeamName',            # 車隊名稱
    'TeamColor',           # 車隊顏色
    'TeamId',              # 車隊 ID
    'FirstName',           # 名
    'LastName',            # 姓
    'FullName',            # 全名
    'HeadshotUrl',         # 頭像 URL
    'CountryCode',         # 國家代碼
    'Position',            # ⭐ 最終名次
    'ClassifiedPosition',  # ⭐ 分類名次
    'GridPosition',        # ⭐ 起始名次 (排位賽位置)
    'Q1', 'Q2', 'Q3',     # 排位賽成績
    'Time',                # 完賽時間
    'Status',              # ⭐ 完賽狀態
    'Points',              # ⭐ 積分
    'Laps'                 # 完成圈數
]
```

### 2. **關鍵欄位說明**

#### **Position (最終名次)**
- 類型: `float`
- 說明: 賽事結束後的最終排名
- 範例: `1.0`, `2.0`, `3.0`

#### **GridPosition (起始名次)**
- 類型: `float`
- 說明: 賽前排位賽決定的起始位置
- 範例: `1.0`, `8.0`, `18.0`

#### **Status (完賽狀態)**
- 類型: `str`
- 可能值:
  - `"Finished"` - 正常完賽
  - `"Lapped"` - 被套圈但完賽
  - `"Retired"` - 退賽 (DNF)
  - `"+1 Lap"` - 落後一圈
  - 其他機械故障或事故原因

#### **Points (積分)**
- 類型: `float`
- 說明: 該場比賽獲得的世界冠軍積分
- 範例: `25.0` (冠軍), `18.0` (亞軍), `15.0` (季軍)

---

## 📈 實際測試結果 (2024 日本站)

### 前 5 名車手資訊

| 車手 | 車號 | 車隊 | 起始名次 | 最終名次 | 名次變化 | 積分 | 狀態 |
|------|------|------|----------|----------|----------|------|------|
| VER | 1 | Red Bull Racing | P1 | P1 | ➡️ 維持原位 | 26.0 | Finished |
| PER | 11 | Red Bull Racing | P2 | P2 | ➡️ 維持原位 | 18.0 | Finished |
| SAI | 55 | Ferrari | P4 | P3 | ⬆️ 上升 1 位 | 15.0 | Finished |
| LEC | 16 | Ferrari | P8 | P4 | ⬆️ 上升 4 位 | 12.0 | Finished |
| NOR | 4 | McLaren | P3 | P5 | ⬇️ 下降 2 位 | 10.0 | Finished |

### 名次變化排行榜 (Top 10)

| 排名 | 車手 | 起始名次 | 最終名次 | 名次變化 | 狀態 |
|------|------|----------|----------|----------|------|
| 1 | MAG | P18 | P13 | ⬆️ **+5** | Lapped |
| 2 | LEC | P8 | P4 | ⬆️ **+4** | Finished |
| 3 | STR | P16 | P12 | ⬆️ **+4** | Lapped |
| 4 | RUS | P9 | P7 | ⬆️ +2 | Finished |
| 5 | SAR | P19 | P17 | ⬆️ +2 | Lapped |
| 6 | ZHO | P20 | P18 | ⬆️ +2 | Retired |
| 7 | SAI | P4 | P3 | ⬆️ +1 | Finished |
| 8 | HUL | P12 | P11 | ⬆️ +1 | Lapped |
| 9 | GAS | P17 | P16 | ⬆️ +1 | Lapped |
| 10 | VER | P1 | P1 | ➡️ 0 | Finished |

### 名次下降最多的車手

| 排名 | 車手 | 起始名次 | 最終名次 | 名次變化 | 狀態 |
|------|------|----------|----------|----------|------|
| 1 | RIC | P11 | P19 | ⬇️ **-8** | Retired |
| 2 | ALB | P14 | P20 | ⬇️ **-6** | Retired |
| 3 | NOR | P3 | P5 | ⬇️ -2 | Finished |
| 4 | PIA | P6 | P8 | ⬇️ -2 | Finished |
| 5 | HAM | P7 | P9 | ⬇️ -2 | Finished |

---

## 🔄 逐圈位置追蹤 (Laps Data)

FastF1 的 `session.laps` 提供了**每一圈的即時位置**資訊：

### 範例：VER 前 10 圈位置變化

```python
laps = session.laps
driver_laps = laps.pick_driver("VER")

# 每圈資料包含:
# - LapNumber: 圈數
# - Position: 該圈結束時的位置
# - LapTime: 圈速
# - Compound: 輪胎配方
```

| 圈數 | 位置 | 圈速 | 輪胎 |
|------|------|------|------|
| Lap 1 | P1 | 02:10.735 | MEDIUM |
| Lap 2 | P1 | N/A | MEDIUM |
| Lap 3 | P1 | N/A | MEDIUM |
| Lap 4 | P1 | 01:36.472 | MEDIUM |
| Lap 5 | P1 | 01:36.437 | MEDIUM |
| Lap 6 | P1 | 01:36.855 | MEDIUM |
| Lap 7 | P1 | 01:36.970 | MEDIUM |
| Lap 8 | P1 | 01:37.329 | MEDIUM |
| Lap 9 | P1 | 01:37.178 | MEDIUM |
| Lap 10 | P1 | 01:37.590 | MEDIUM |

**用途**:
- 分析車手在比賽過程中的位置變化
- 追蹤超車和被超車的時機
- 計算最佳位置和最差位置
- 分析進站策略對名次的影響

---

## 💡 可計算的衍生資訊

基於 FastF1 提供的原始數據，可以計算出以下衍生指標：

### 1. **名次變化 (Position Change)**
```python
position_change = GridPosition - Position

if position_change > 0:
    # 上升名次
    result = f"⬆️ 上升 {position_change} 位"
elif position_change < 0:
    # 下降名次
    result = f"⬇️ 下降 {abs(position_change)} 位"
else:
    # 維持原位
    result = "➡️ 維持原位"
```

### 2. **最佳/最差位置 (從 Laps 數據)**
```python
driver_laps = laps.pick_driver(driver_code)

best_position = driver_laps['Position'].min()    # 最佳位置
worst_position = driver_laps['Position'].max()   # 最差位置
average_position = driver_laps['Position'].mean()  # 平均位置
```

### 3. **位置穩定性**
```python
position_variance = driver_laps['Position'].var()  # 位置變異數
position_std = driver_laps['Position'].std()       # 位置標準差

# 變異數越小 = 位置越穩定
```

### 4. **超車次數 (簡化版)**
```python
positions = driver_laps['Position'].tolist()
overtakes = 0

for i in range(1, len(positions)):
    if positions[i] < positions[i-1]:  # 位置提升
        overtakes += (positions[i-1] - positions[i])
```

### 5. **領先圈數 (Laps Led)**
```python
laps_led = len(driver_laps[driver_laps['Position'] == 1])
```

---

## 📦 建議的 JSON 數據結構

基於 FastF1 提供的數據，建議以下 JSON 結構用於 GUI 顯示：

```json
{
  "race_info": {
    "year": 2024,
    "race": "Japan",
    "session": "R",
    "race_name": "Japanese Grand Prix",
    "circuit": "Suzuka",
    "analysis_timestamp": "2025-10-22T20:46:46.292730"
  },
  "position_analysis": [
    {
      "driver": "LEC",
      "driver_number": 16,
      "full_name": "Charles Leclerc",
      "team": "Ferrari",
      "grid_position": 8,
      "final_position": 4,
      "position_change": 4,
      "position_change_text": "上升 4 位",
      "positions_gained": 4,
      "status": "Finished",
      "points": 12.0,
      "finish_time": "00:00:26.522",
      "lap_details": {
        "total_laps": 53,
        "best_position": 4,
        "worst_position": 8,
        "average_position": 5.2,
        "laps_in_top_3": 15,
        "laps_in_top_5": 48,
        "laps_in_points": 53
      }
    }
  ],
  "statistics": {
    "biggest_gainer": {
      "driver": "MAG",
      "positions_gained": 5
    },
    "biggest_loser": {
      "driver": "RIC",
      "positions_lost": 8
    },
    "most_stable": {
      "driver": "VER",
      "position_variance": 0.0
    },
    "total_drivers": 20,
    "finishers": 18,
    "retirements": 2
  }
}
```

---

## 🎯 已有的系統模組

系統中已經存在相關的名次分析模組：

### 1. **SingleDriverPositionAnalysis**
- 路徑: `CLI_modules/cli/analyzer/single_driver_position_analysis.py`
- 功能:
  - ✅ 分析單一車手位置變化
  - ✅ 計算起始/完賽/最佳/最差位置
  - ✅ 位置統計 (平均、中位數、變異數)
  - ✅ Top 5/Top 10 圈數統計

### 2. **AllDriversOvertakingPerformanceComparison**
- 路徑: `CLI_modules/cli/analyzer/all_drivers_overtaking_performance_comparison.py`
- 功能:
  - ✅ 全車手名次變化對比
  - ✅ 計算 `position_gained` (GridPosition - Position)
  - ✅ 超車表現指標

### 3. **DriverOvertakingAnalysis**
- 路徑: `CLI_modules/cli/analyzer/driver_overtaking_analysis.py`
- 功能:
  - ✅ 超車次數分析
  - ✅ 名次變化計算
  - ✅ GridPosition 和 Position 對比

---

## 📝 實作建議

### 方案 A: 使用現有模組
**直接使用 `SingleDriverPositionAnalysis`**，它已經實現了完整的名次分析功能：

```python
from CLI_modules.cli.analyzer.single_driver_position_analysis import SingleDriverPositionAnalysis

# 初始化分析器
analyzer = SingleDriverPositionAnalysis(
    data_loader=data_loader,
    year=2024,
    race="Japan",
    session="R"
)

# 分析單一車手
result = analyzer.analyze_position_changes(driver="LEC")

# 分析全部車手
all_results = analyzer.analyze_position_changes(driver=None)
```

### 方案 B: 創建新的 GUI 模組
**基於 UniversalDataLoader 創建 Position Analysis GUI**：

```python
# modules/gui/position_analysis/position_analysis_data_loader.py
class PositionAnalysisDataLoader(UniversalDataLoader):
    def __init__(self):
        super().__init__(
            cli_function=25,  # 對應 CLI 功能 ID
            module_name="position_analysis"
        )
    
    def _validate_data_format(self, raw_data):
        required_keys = ["position_analysis", "race_info"]
        # 驗證邏輯
    
    def _transform_data_for_display(self, raw_data):
        # 轉換為 GUI 顯示格式
        pass
```

### 方案 C: 擴展現有 API
**在 `refactored_api.py` 中添加名次分析端點**：

```python
@app.post("/api/position-analysis")
async def analyze_position_changes(request: PositionAnalysisRequest):
    """名次變化分析 API"""
    
    analyzer = SingleDriverPositionAnalysis(
        data_loader=data_loader,
        year=request.year,
        race=request.race,
        session=request.session
    )
    
    result = analyzer.analyze_position_changes(driver=request.driver)
    
    return {
        "success": True,
        "data": result
    }
```

---

## ✅ 最終確認清單

- [x] ✅ FastF1 提供 **Position** (最終名次)
- [x] ✅ FastF1 提供 **GridPosition** (起始名次)
- [x] ✅ 可計算 **名次變化** (GridPosition - Position)
- [x] ✅ FastF1 提供 **逐圈位置追蹤** (Laps 中的 Position)
- [x] ✅ FastF1 提供 **完賽狀態** (Status)
- [x] ✅ FastF1 提供 **積分** (Points)
- [x] ✅ 系統已有 **SingleDriverPositionAnalysis** 模組
- [x] ✅ 系統已有 **名次變化計算邏輯**
- [x] ✅ 數據結構完整且易於使用

---

## 🎉 總結

**FastF1 完整支援賽事名次分析**，提供了所有必要的資訊來實現：

1. ✅ 賽事結束後的最終名次
2. ✅ 起始名次 (排位賽位置)
3. ✅ 名次變化計算 (上升/下降)
4. ✅ 逐圈位置追蹤
5. ✅ 完賽狀態判斷
6. ✅ 積分和完賽時間

**系統已有相關模組**，可以直接使用或擴展：
- `SingleDriverPositionAnalysis` - 完整的名次分析實現
- `AllDriversOvertakingPerformanceComparison` - 全車手對比
- `DriverOvertakingAnalysis` - 超車與名次分析

**下一步建議**：
1. 創建 GUI 模組展示名次分析結果
2. 添加視覺化圖表 (名次變化折線圖)
3. 實現名次排行榜 (最大上升/下降)
4. 整合到主選單系統

---

**測試腳本**: `test_fastf1_race_results.py`  
**調查報告**: `FASTF1_RACE_POSITION_DATA_INVESTIGATION.md`  
**測試日期**: 2025-10-22
