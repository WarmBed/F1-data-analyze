# 🏎️ 功能 70：全年度車手一致性分析 (Season Driver Consistency Analysis)

**功能 ID**: 70 (待分配)  
**功能名稱**: Ideal Lap Season Consistency Analysis  
**開發狀態**: 📋 規劃階段  
**依賴功能**: 功能 53 (Ideal Lap Analysis - All Drivers)  
**目標賽季**: 2025  
**分析會話**: 僅正賽 (Race)

---

## 📊 功能概述

### 核心目標
分析整個賽季所有車手的**理想圈一致性表現**，通過統計學方法量化車手在全年度的穩定性、完美執行能力和進步趨勢。

### 分析維度
此功能基於**理想圈差距 (time_gap)** 進行深度統計分析：

```
理想圈差距 = 實際最快圈速 - 理想圈速
意義: 車手能否在單圈中完美串聯三個賽段的能力
差距越小 = 一致性越高 = 執行力越強
```

---

## 🎯 四大核心指標

### 1️⃣ **Mean Gap (平均差距)**
```python
平均差距 = Σ(每場理想圈差距) / 總場次
單位: 秒 (s)
```

**意義**: 整個賽季的綜合一致性水平  
**評價標準**:
- 🟢 優秀: < 0.10s
- 🟡 普通: 0.10-0.15s
- 🔴 需改善: > 0.15s

**統計補充**:
- 中位數 (Median Gap): 排除極端值的穩定性
- 標準差 (Std Dev): 表現波動程度

---

### 2️⃣ **Perfect Lap Rate (完美圈率)**
```python
完美圈率 = (理想圈 = 實際圈的賽事數) / 總賽事數 × 100%
判定標準: 理想圈與實際圈誤差 < 0.01s
```

**意義**: 車手在單圈中完美串聯三個賽段的能力  
**評價標準**:
- 🟢 頂尖: > 25% (約 6/24 賽事)
- 🟡 中等: 15-25%
- 🔴 較差: < 15%

**專業術語**: Sector Execution Consistency

---

### 3️⃣ **Sector Consistency Score (分段一致性分數)**
```python
# 計算每個賽段的變異係數 (Coefficient of Variation)
CV_S1 = (StdDev_S1 / Mean_S1) × 100
CV_S2 = (StdDev_S2 / Mean_S2) × 100
CV_S3 = (StdDev_S3 / Mean_S3) × 100

# 轉換為一致性分數 (越低越好 → 越高越好)
Sector_Consistency_Score = 100 - ((CV_S1 + CV_S2 + CV_S3) / 3)
```

**意義**: 各賽段表現的穩定程度，區分「運氣好」vs「真實力」  
**評價標準**:
- 🟢 非常穩定: > 90%
- 🟡 穩定: 85-90%
- 🔴 不穩定: < 85%

---

### 4️⃣ **Gap Improvement Trend (差距改善趨勢)**
```python
# 線性迴歸分析
import numpy as np
from scipy import stats

x = np.arange(1, num_races + 1)  # 賽事順序 (1, 2, 3, ...)
y = mean_gaps_per_race           # 每場理想圈差距

slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

# 趨勢判定
if slope < -0.002:
    trend = "顯著進步"
elif slope > +0.002:
    trend = "退步"
else:
    trend = "穩定"

# 顯著性檢驗
if r_value ** 2 > 0.6:
    significance = "趨勢顯著"
else:
    significance = "趨勢不明顯"
```

**意義**: 車手是否隨賽季進步  
**評價標準**:
- 🟢 顯著進步: slope < -0.002 且 R² > 0.6
- 🟡 穩定: -0.002 ≤ slope ≤ +0.002
- 🔴 退步: slope > +0.002 且 R² > 0.6

**專業術語**: Performance Development Trajectory

---

## 🧮 綜合一致性分數 (Overall Consistency Score)

```python
# 加權計算綜合分數 (0-100)
Consistency_Score = (
    0.30 × (100 - Mean_Gap_Normalized) +      # 平均差距 (30% 權重)
    0.25 × Perfect_Lap_Rate +                  # 完美圈率 (25% 權重)
    0.25 × Sector_Consistency_Score +          # 分段一致性 (25% 權重)
    0.20 × Trend_Score                         # 改善趨勢 (20% 權重)
)

# 正規化處理
Mean_Gap_Normalized = (Mean_Gap / Max_Mean_Gap_in_Season) × 100

# 趨勢分數轉換
if slope < 0:
    Trend_Score = 100  # 進步給滿分
else:
    Trend_Score = max(0, 100 - abs(slope) × 1000)
```

**分數解讀**:
- 95-100: 頂尖一致性 (Championship Contender)
- 90-95: 優秀一致性 (Top Tier)
- 85-90: 良好一致性 (Mid-Pack Leader)
- 80-85: 中等一致性 (Developing Driver)
- < 80: 需改善 (Inconsistent)

---

## 📋 數據流程

### 輸入數據
```
來源: json/ 目錄中所有 2025 賽季正賽的功能 53 JSON 檔案
格式: ideal_lap_ranking_2025_{Race}_R.json
數量: 24 場賽事 (完整賽季)
```

### 處理邏輯
```python
1. 掃描 json/ 目錄，篩選出 2025 年正賽的功能 53 檔案
2. 解析每個 JSON，提取每位車手的:
   - ideal_lap_time
   - fastest_lap_time
   - time_gap
   - sector_breakdown (S1/S2/S3 時間)
3. 按車手代碼分組，計算賽季統計
4. 執行回歸分析、變異係數計算
5. 生成綜合排名和車隊對比
6. 導出完整 JSON 報告
```

### 輸出數據
```
檔案名稱: season_consistency_2025_Race.json
位置: json/
格式: 詳見下方 JSON 結構
```

---

## 💾 JSON 數據結構設計

```json
{
  "success": true,
  "metadata": {
    "function_id": 70,
    "function_name": "Season Driver Consistency Analysis",
    "season": 2025,
    "session_type": "Race",
    "total_races": 24,
    "analysis_timestamp": "2025-10-10T14:30:00.123456",
    "api_source": "Derived from Function 53"
  },
  
  "summary": {
    "total_drivers": 20,
    "races_analyzed": 24,
    "most_consistent_driver": {
      "driver": "VER",
      "consistency_score": 95.2
    },
    "highest_perfect_rate": {
      "driver": "VER",
      "rate": 33.3
    },
    "most_improved": {
      "driver": "ANT",
      "slope": -0.008,
      "improvement": -0.160
    }
  },
  
  "drivers": {
    "VER": {
      "driver_name": "Max Verstappen",
      "team": "Red Bull Racing",
      
      "core_metrics": {
        "mean_gap": 0.082,
        "median_gap": 0.075,
        "std_dev": 0.045,
        "min_gap": 0.000,
        "max_gap": 0.185,
        "perfect_lap_rate": 33.3,
        "perfect_lap_count": 8,
        "sector_consistency_score": 94.5,
        "trend_slope": -0.002,
        "trend_r_squared": 0.35,
        "overall_consistency_score": 95.2
      },
      
      "race_by_race": [
        {
          "race": "Bahrain",
          "round": 1,
          "ideal_lap": 91.447,
          "fastest_lap": 91.447,
          "gap": 0.000,
          "is_perfect": true,
          "sector_times": {
            "s1": 26.85,
            "s2": 27.45,
            "s3": 26.64
          },
          "sector_consistency": {
            "s1_cv": 2.3,
            "s2_cv": 1.8,
            "s3_cv": 2.1,
            "overall_score": 97.9
          }
        },
        {
          "race": "Saudi Arabia",
          "round": 2,
          "ideal_lap": 89.205,
          "fastest_lap": 89.205,
          "gap": 0.000,
          "is_perfect": true,
          "sector_times": {...},
          "sector_consistency": {...}
        }
        // ... 其他 22 場賽事
      ],
      
      "sector_analysis": {
        "sector_1": {
          "mean_time": 26.85,
          "std_dev": 0.62,
          "cv": 2.31,
          "consistency_score": 97.7,
          "best_race": "Monaco",
          "worst_race": "Spa"
        },
        "sector_2": {
          "mean_time": 27.52,
          "std_dev": 0.48,
          "cv": 1.74,
          "consistency_score": 98.3,
          "best_race": "Austria",
          "worst_race": "Singapore"
        },
        "sector_3": {
          "mean_time": 26.64,
          "std_dev": 0.55,
          "cv": 2.07,
          "consistency_score": 97.9,
          "best_race": "Monza",
          "worst_race": "Monaco"
        }
      },
      
      "trend_analysis": {
        "first_5_races": {
          "avg_gap": 0.088,
          "perfect_rate": 40.0
        },
        "last_5_races": {
          "avg_gap": 0.075,
          "perfect_rate": 60.0
        },
        "improvement": -0.013,
        "slope": -0.002,
        "intercept": 0.095,
        "r_squared": 0.35,
        "p_value": 0.002,
        "trend_direction": "stable",
        "trend_significance": "not_significant"
      },
      
      "rankings": {
        "by_mean_gap": 1,
        "by_perfect_rate": 1,
        "by_sector_consistency": 1,
        "by_improvement": 4,
        "overall": 1
      }
    }
    // ... 其他 19 位車手 (NOR, LEC, PIA, HAM, ...)
  },
  
  "team_analysis": {
    "Red Bull Racing": {
      "drivers": ["VER", "TSU"],
      "avg_consistency_score": 90.2,
      "best_driver": "VER",
      "best_driver_score": 95.2,
      "team_gap_spread": 10.3,
      "avg_perfect_rate": 26.5
    },
    "McLaren": {
      "drivers": ["NOR", "PIA"],
      "avg_consistency_score": 92.3,
      "best_driver": "NOR",
      "best_driver_score": 93.8,
      "team_gap_spread": 3.5,
      "avg_perfect_rate": 25.0
    }
    // ... 其他車隊
  },
  
  "rankings": {
    "by_consistency_score": [
      {"position": 1, "driver": "VER", "score": 95.2},
      {"position": 2, "driver": "NOR", "score": 93.8},
      {"position": 3, "driver": "LEC", "score": 91.5}
      // ... 其他車手
    ],
    "by_mean_gap": [
      {"position": 1, "driver": "VER", "gap": 0.082},
      {"position": 2, "driver": "NOR", "gap": 0.095},
      {"position": 3, "driver": "LEC", "gap": 0.108}
    ],
    "by_perfect_rate": [
      {"position": 1, "driver": "VER", "rate": 33.3},
      {"position": 2, "driver": "NOR", "rate": 29.2},
      {"position": 3, "driver": "PIA", "rate": 25.0}
    ],
    "by_sector_consistency": [
      {"position": 1, "driver": "VER", "score": 94.5},
      {"position": 2, "driver": "NOR", "score": 92.8},
      {"position": 3, "driver": "LEC", "score": 90.3}
    ],
    "by_improvement": [
      {"position": 1, "driver": "ANT", "slope": -0.008, "improvement": -0.160},
      {"position": 2, "driver": "PIA", "slope": -0.003, "improvement": -0.046},
      {"position": 3, "driver": "HAM", "slope": -0.002, "improvement": -0.034}
    ]
  },
  
  "statistical_summary": {
    "mean_gap": {
      "min": 0.082,
      "max": 0.245,
      "mean": 0.135,
      "median": 0.128,
      "std_dev": 0.042
    },
    "perfect_rate": {
      "min": 4.2,
      "max": 33.3,
      "mean": 18.5,
      "median": 16.7
    },
    "sector_consistency": {
      "min": 82.3,
      "max": 94.5,
      "mean": 88.7,
      "median": 89.2
    }
  }
}
```

---

## � CLI 開發指南

> **💡 注意**: GUI 介面設計已移至獨立文件  
> 📄 詳見：`docs/develop task/GUI develop task/F70_GUI_ideal_lap全年度分析介面設計.md`

### 命令格式
```bash
python f1_analysis_modular_main.py -f 70 -y 2025 -s R
```

### 參數說明
```
-f 70        功能 ID (Season Consistency Analysis)
-y 2025      賽季年份
-s R         會話類型 (僅支援正賽)
```

### 實現步驟

#### 階段 1: 數據收集
```python
def _collect_season_data(self, year: int, session_type: str) -> dict:
    """
    收集整個賽季的功能 53 數據
    
    Returns:
        {
            'VER': [race1_data, race2_data, ...],
            'NOR': [race1_data, race2_data, ...],
            ...
        }
    """
    json_dir = Path("json")
    pattern = f"ideal_lap_ranking_{year}_*_{session_type}.json"
    
    season_data = defaultdict(list)
    
    for json_file in json_dir.glob(pattern):
        data = self._load_json(json_file)
        
        for driver_data in data['analysis_result']['ranking']:
            driver = driver_data['driver']
            season_data[driver].append({
                'race': data['metadata']['race'],
                'round': extract_round_number(json_file.name),
                'ideal_lap': driver_data['ideal_lap_time'],
                'fastest_lap': driver_data['fastest_lap_time'],
                'gap': driver_data['time_gap'],
                'sectors': driver_data['sector_breakdown']
            })
    
    return season_data
```

#### 階段 2: 統計計算
```python
def _calculate_core_metrics(self, driver_races: list) -> dict:
    """計算 4 個核心指標"""
    gaps = [race['gap'] for race in driver_races]
    
    # 1. Mean Gap
    mean_gap = np.mean(gaps)
    median_gap = np.median(gaps)
    std_dev = np.std(gaps)
    
    # 2. Perfect Lap Rate
    perfect_count = sum(1 for gap in gaps if gap < 0.01)
    perfect_rate = (perfect_count / len(gaps)) * 100
    
    # 3. Sector Consistency Score
    sector_consistency = self._calculate_sector_consistency(driver_races)
    
    # 4. Trend Slope
    trend_analysis = self._calculate_trend(gaps)
    
    return {
        'mean_gap': mean_gap,
        'median_gap': median_gap,
        'std_dev': std_dev,
        'perfect_lap_rate': perfect_rate,
        'perfect_lap_count': perfect_count,
        'sector_consistency_score': sector_consistency,
        'trend_slope': trend_analysis['slope'],
        'trend_r_squared': trend_analysis['r_squared']
    }
```

#### 階段 3: 回歸分析
```python
def _calculate_trend(self, gaps: list) -> dict:
    """線性迴歸計算趨勢"""
    from scipy import stats
    
    x = np.arange(1, len(gaps) + 1)
    y = np.array(gaps)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # 計算前 5 場和後 5 場平均
    first_5_avg = np.mean(gaps[:5])
    last_5_avg = np.mean(gaps[-5:])
    improvement = last_5_avg - first_5_avg
    
    # 判斷趨勢方向
    if slope < -0.002 and r_value ** 2 > 0.6:
        direction = "significant_improvement"
    elif slope > 0.002 and r_value ** 2 > 0.6:
        direction = "regression"
    else:
        direction = "stable"
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'first_5_avg': first_5_avg,
        'last_5_avg': last_5_avg,
        'improvement': improvement,
        'trend_direction': direction
    }
```

#### 階段 4: 分段一致性
```python
def _calculate_sector_consistency(self, driver_races: list) -> float:
    """計算分段一致性分數"""
    s1_times = []
    s2_times = []
    s3_times = []
    
    for race in driver_races:
        sectors = race['sectors']
        s1_times.append(sectors['sector_1']['time'])
        s2_times.append(sectors['sector_2']['time'])
        s3_times.append(sectors['sector_3']['time'])
    
    # 計算每個賽段的變異係數 (CV)
    cv_s1 = (np.std(s1_times) / np.mean(s1_times)) * 100
    cv_s2 = (np.std(s2_times) / np.mean(s2_times)) * 100
    cv_s3 = (np.std(s3_times) / np.mean(s3_times)) * 100
    
    # 轉換為一致性分數 (0-100)
    avg_cv = (cv_s1 + cv_s2 + cv_s3) / 3
    consistency_score = max(0, 100 - avg_cv)
    
    return consistency_score
```

#### 階段 5: 綜合分數
```python
def _calculate_consistency_score(self, metrics: dict, all_drivers_metrics: dict) -> float:
    """計算綜合一致性分數"""
    # 正規化 Mean Gap (0-100)
    all_gaps = [d['mean_gap'] for d in all_drivers_metrics.values()]
    max_gap = max(all_gaps)
    mean_gap_normalized = (metrics['mean_gap'] / max_gap) * 100
    mean_gap_score = 100 - mean_gap_normalized
    
    # 完美圈率分數 (已經是 0-100)
    perfect_rate_score = metrics['perfect_lap_rate']
    
    # 分段一致性分數 (已經是 0-100)
    sector_score = metrics['sector_consistency_score']
    
    # 趨勢分數轉換
    slope = metrics['trend_slope']
    if slope < 0:
        trend_score = 100  # 進步給滿分
    else:
        trend_score = max(0, 100 - abs(slope) * 1000)
    
    # 加權計算
    consistency_score = (
        0.30 * mean_gap_score +
        0.25 * perfect_rate_score +
        0.25 * sector_score +
        0.20 * trend_score
    )
    
    return round(consistency_score, 1)
```

---

## 🧪 測試計畫

### 單元測試
```python
# tests/test_season_consistency.py

def test_mean_gap_calculation():
    """測試平均差距計算"""
    gaps = [0.05, 0.08, 0.12, 0.10, 0.06]
    expected = 0.082
    result = calculate_mean_gap(gaps)
    assert abs(result - expected) < 0.001

def test_perfect_lap_rate():
    """測試完美圈率計算"""
    gaps = [0.000, 0.005, 0.150, 0.000, 0.008]
    expected = 40.0  # 2/5 = 40%
    result = calculate_perfect_lap_rate(gaps, threshold=0.01)
    assert result == expected

def test_sector_consistency():
    """測試分段一致性計算"""
    s1_times = [26.8, 26.9, 26.7, 26.85, 26.75]
    cv = (np.std(s1_times) / np.mean(s1_times)) * 100
    consistency = 100 - cv
    assert consistency > 95.0  # 預期非常穩定

def test_trend_regression():
    """測試趨勢回歸分析"""
    # 模擬進步趨勢
    gaps = [0.15, 0.14, 0.12, 0.10, 0.09, 0.08]
    result = calculate_trend(gaps)
    assert result['slope'] < 0  # 負斜率 = 進步
    assert result['trend_direction'] == 'significant_improvement'
```

### 整合測試
```bash
# 測試完整流程
python f1_analysis_modular_main.py -f 70 -y 2025 -s R

# 驗證輸出 JSON
python -c "
import json
with open('json/season_consistency_2025_Race.json', 'r') as f:
    data = json.load(f)
    assert data['success'] == True
    assert len(data['drivers']) >= 20
    assert 'VER' in data['drivers']
    print('✅ JSON 結構驗證通過')
"
```

---

## 📝 開發檢查清單

### 階段 1: CLI 後端 (預計 3-4 小時)
- [ ] 在 `F1AnalysisFunctionMapper` 添加功能 70 映射
- [ ] 實現 `_execute_season_consistency_analysis()` 方法
- [ ] 掃描並載入所有正賽的功能 53 JSON
- [ ] 計算 4 個核心指標
- [ ] 執行統計分析（回歸、變異係數、四分位數）
- [ ] 生成車隊對比數據
- [ ] 導出完整 JSON 到 `json/` 目錄
- [ ] 終端輸出格式化摘要報告

### 階段 2: 數據驗證 (預計 1 小時)
- [ ] 單元測試：平均差距計算
- [ ] 單元測試：完美圈率計算
- [ ] 單元測試：分段一致性計算
- [ ] 單元測試：趨勢回歸分析
- [ ] 整合測試：完整 CLI 執行
- [ ] JSON 結構驗證
- [ ] 統計結果人工核對（抽樣 3 位車手）

### 階段 3: GUI 前端 (預計 6-8 小時)
- [ ] 創建 `modules/gui/season_consistency/` 目錄
- [ ] 實現 `SeasonConsistencyLoader(UniversalDataLoader)`
- [ ] 實現 `SeasonConsistencyMDI` 主窗口
- [ ] Tab 1: 四指標雷達圖 + 排名表
- [ ] Tab 2: 完美圈分析 + 逐場追蹤
- [ ] Tab 3: 分段熱力圖 + 一致性排名
- [ ] Tab 4: 趨勢線圖 + 統計表格
- [ ] Tab 5: 詳細數據表 + 匯出功能 (新增)
  - [ ] 完整 20 位車手統計表格
  - [ ] 顏色編碼系統 (🟢🟡🔴)
  - [ ] 可排序欄位（點擊表頭排序）
  - [ ] 車隊篩選下拉選單
  - [ ] CSV 匯出功能
  - [ ] 複製到剪貼簿功能
- [ ] 整合到 `f1t_gui_main.py` 選單
- [ ] 錯誤處理和載入動畫

### 階段 4: 測試與優化 (預計 2 小時)
- [ ] GUI 啟動測試
- [ ] 數據載入測試
- [ ] 圖表渲染測試
- [ ] 多車手對比功能測試
- [ ] 匯出 CSV 功能測試
- [ ] 效能優化（大量數據載入）
- [ ] 中文字體顯示測試

### 階段 5: 文檔完善 (預計 1 小時)
- [ ] 更新 `README.md` 功能列表
- [ ] 更新 CLI 幫助文檔
- [ ] 添加使用範例截圖
- [ ] 撰寫 API 端點文檔（未來 API 整合）
- [ ] 更新 `copilot-instructions.md`

---

## 🎯 成功標準

### CLI 後端
- ✅ 能正確掃描並載入 24 場賽事的功能 53 JSON
- ✅ 4 個核心指標計算結果正確（手動驗證 3 位車手）
- ✅ 統計分析結果符合預期（R² 值、CV 值合理）
- ✅ JSON 導出結構完整，無缺失欄位
- ✅ 執行時間 < 5 秒（本地 JSON 讀取）

### GUI 前端
- ✅ 所有 4 個標籤頁正常渲染
- ✅ 雷達圖、熱力圖、趨勢圖正確顯示
- ✅ 車手選擇功能正常切換
- ✅ 排名表可排序、可篩選
- ✅ 中文字體正常顯示
- ✅ 匯出 CSV 功能正常
- ✅ 無記憶體洩漏（長時間運行測試）

---

## 🔮 未來擴展

### 進階功能
1. **多賽季對比**: 比較 2024 vs 2025 車手一致性變化
2. **賽道分類分析**: 街道賽 vs 永久賽道的一致性差異
3. **輪胎影響分析**: 不同輪胎配方對一致性的影響
4. **天氣影響**: 雨戰 vs 乾地的一致性對比
5. **排位賽對比**: 正賽一致性 vs 排位賽一致性

### API 整合
```python
# 未來 API 端點
POST /api/v1/season-consistency
{
    "season": 2025,
    "session_type": "Race",
    "drivers": ["VER", "NOR", "LEC"]  # 可選篩選
}

Response:
{
    "success": true,
    "data": { ... }  # 完整 JSON 結構
}
```

---

## 📚 參考資料

### 統計學概念
- **變異係數 (CV)**: https://en.wikipedia.org/wiki/Coefficient_of_variation
- **線性迴歸**: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html
- **箱型圖**: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html

### F1 數據分析
- **FastF1 文檔**: https://docs.fastf1.dev/
- **理想圈分析範例**: https://medium.com/towards-formula-1-analysis

### PyQt5 視覺化
- **Matplotlib + PyQt5**: https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
- **雷達圖教學**: https://matplotlib.org/stable/gallery/specialty_plots/radar_chart.html

---

## 📞 聯絡資訊

**開發者**: AI Assistant  
**功能負責人**: 待分配  
**最後更新**: 2025-10-10  
**版本**: v1.0.0-draft

---

**🏁 準備開始開發！讓我們打造一個專業的賽車數據分析工具！**
