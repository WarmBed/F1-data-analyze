# F120 FP2 彎道全圈數分析 - 開發任務

## 🎯 功能概述

**Function ID**: 120  
**CLI 參數**: `-f 120`  
**Session**: FP2 (Free Practice 2)  
**參考基礎**: Function 47 (全車手彎道速度分析)

### 核心目標
分析 FP2 中所有車手在低/中/高速彎的**全圈數表現**，提供雙模式分析：
- **模式 A**：統一分析（所有有效圈混合）
- **模式 B**：分組分析（長距離 vs 排位模擬）

---

## 📊 功能需求

### 1. 彎道分類（繼承 F47）
- **低速彎**：平均 apex 速度 < 100 km/h
- **中速彎**：平均 apex 速度 100-200 km/h
- **高速彎**：平均 apex 速度 > 200 km/h
- 每類選擇 **1 個代表彎道**

### 2. 雙模式分析

#### 模式 A：統一分析（Unified Analysis）
```python
{
  "mode": "unified",
  "description": "所有有效圈混合分析，不區分燃油狀態",
  "data": {
    "VER": {
      "low_speed_corner_10": {
        "median_speed": 88.5,
        "mean_speed": 87.8,
        "std_dev": 2.3,
        "q1": 86.2,
        "q3": 89.7,
        "min_speed": 83.5,
        "max_speed": 91.2,
        "top3_avg": 90.5,
        "valid_laps": 18,
        "filtered_laps": 5
      }
    }
  }
}
```

#### 模式 B：分組分析（Grouped Analysis）
```python
{
  "mode": "grouped",
  "description": "區分長距離模擬和排位模擬",
  "groups": {
    "long_run": {
      "description": "連續多圈模擬（高燃油）",
      "lap_range": "1-15",
      "data": {
        "VER": {
          "low_speed_corner_10": {
            "median_speed": 87.2,
            "mean_speed": 86.9,
            "std_dev": 1.8,
            "valid_laps": 12
          }
        }
      }
    },
    "quali_sim": {
      "description": "排位模擬（低燃油）",
      "lap_range": "16-22",
      "data": {
        "VER": {
          "low_speed_corner_10": {
            "median_speed": 90.1,
            "mean_speed": 89.8,
            "std_dev": 1.2,
            "valid_laps": 6
          }
        }
      }
    }
  }
}
```

### 3. 統計指標（完整版）

每個彎道計算以下指標：

| 指標 | 說明 | 用途 |
|------|------|------|
| `median_speed` | 中位數速度 | 穩健的中心趨勢（主要指標） |
| `mean_speed` | 平均速度 | 整體趨勢（輔助指標） |
| `std_dev` | 標準差 | 一致性評估（越小越穩定） |
| `q1` | 第一四分位數 (25%) | 統計分布下界 |
| `q3` | 第三四分位數 (75%) | 統計分布上界 |
| `iqr` | 四分位距 (Q3-Q1) | 數據離散程度 |
| `min_speed` | 最慢速度 | 極端值下界 |
| `max_speed` | 最快速度 | 極端值上界 |
| `top3_avg` | 最快 3 圈平均 | 賽車極限性能 |
| `bottom3_avg` | 最慢 3 圈平均 | 最差狀況參考 |
| `valid_laps` | 有效圈數 | 樣本量 |
| `filtered_laps` | 被過濾圈數 | 數據品質指標 |
| `cv` | 變異係數 (std/mean) | 相對穩定度（%） |

---

## 🔍 異常值過濾邏輯（嚴格模式）

### 第一階段：規則過濾
```python
def is_valid_lap(lap, session, all_laps) -> Tuple[bool, str]:
    """
    判斷是否為有效分析圈
    
    Returns:
        (is_valid, filter_reason)
    """
    
    # 1. 基礎過濾（繼承 F47）
    if lap.get('TrackStatus') != '1':  # 非綠旗
        if 'Yellow' in str(lap.get('TrackStatus')):
            return False, "yellow_flag"
        if 'Red' in str(lap.get('TrackStatus')):
            return False, "red_flag"
    
    if 'SafetyCar' in str(lap.get('TrackStatus')):
        return False, "safety_car"
    
    if lap['PitOutTime'] is not pd.NaT or lap['PitInTime'] is not pd.NaT:
        return False, "pit_lap"
    
    # 2. 新增過濾
    if lap.get('IsAccurate') == False:
        return False, "inaccurate_lap"
    
    # In Lap 檢測（下一圈進站）
    lap_number = lap['LapNumber']
    next_lap = all_laps[all_laps['LapNumber'] == lap_number + 1]
    if not next_lap.empty and next_lap.iloc[0]['PitInTime'] is not pd.NaT:
        return False, "in_lap"
    
    # Out Lap 檢測（本圈出站）
    if lap['PitOutTime'] is not pd.NaT:
        return False, "out_lap"
    
    # 首圈過濾
    if lap_number == 1:
        return False, "first_lap"
    
    # 最後一圈過濾（session 結束前可能減速）
    max_lap = all_laps['LapNumber'].max()
    if lap_number == max_lap:
        return False, "last_lap"
    
    return True, "valid"
```

### 第二階段：統計過濾（IQR 方法）
```python
def remove_statistical_outliers(speeds: List[float], corner_name: str) -> Tuple[List[float], int]:
    """
    使用 IQR 方法移除統計異常值
    
    Returns:
        (filtered_speeds, num_outliers)
    """
    if len(speeds) < 4:
        return speeds, 0  # 樣本太少，不過濾
    
    q1 = np.percentile(speeds, 25)
    q3 = np.percentile(speeds, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    filtered = [s for s in speeds if lower_bound <= s <= upper_bound]
    num_outliers = len(speeds) - len(filtered)
    
    print(f"  [FILTER] {corner_name}: {len(speeds)} → {len(filtered)} 圈 "
          f"(移除 {num_outliers} 個異常值, 範圍: {lower_bound:.1f}-{upper_bound:.1f} km/h)")
    
    return filtered, num_outliers
```

### 過濾統計輸出
```json
{
  "filtering_summary": {
    "total_laps": 25,
    "valid_laps": 18,
    "filtered_breakdown": {
      "yellow_flag": 2,
      "safety_car": 1,
      "pit_lap": 1,
      "in_lap": 1,
      "out_lap": 1,
      "first_lap": 1,
      "last_lap": 0,
      "statistical_outliers": 0
    }
  }
}
```

---

## 🔄 Long Run / Quali Sim 分組邏輯

### 自動分組策略

```python
def detect_fp2_phases(driver_laps: pd.DataFrame) -> Dict[str, List[int]]:
    """
    自動識別 FP2 的長距離和排位模擬階段
    
    策略：
    1. 連續 5 圈以上 → Long Run
    2. 進站後單圈 → Quali Sim
    3. 速度分析輔助判斷
    
    Returns:
        {
            "long_run": [1,2,3,...,12],
            "quali_sim": [15,16,19,20],
            "unknown": [13,14,17,18]
        }
    """
    phases = {"long_run": [], "quali_sim": [], "unknown": []}
    
    current_run = []
    
    for idx, lap in driver_laps.iterrows():
        lap_num = lap['LapNumber']
        
        # 檢查是否為進出站圈
        is_pit_related = (
            lap['PitInTime'] is not pd.NaT or 
            lap['PitOutTime'] is not pd.NaT
        )
        
        if is_pit_related:
            # 結束當前 run
            if len(current_run) >= 5:
                phases["long_run"].extend(current_run)
            elif len(current_run) > 0:
                phases["unknown"].extend(current_run)
            current_run = []
        else:
            current_run.append(lap_num)
    
    # 處理最後一個 run
    if len(current_run) >= 5:
        phases["long_run"].extend(current_run)
    elif len(current_run) > 0:
        # 檢查速度是否明顯快於 long run
        # 若是，則視為 quali sim
        phases["quali_sim"].extend(current_run)
    
    return phases
```

### 分組優先級
1. **Long Run 優先**：連續 5 圈以上
2. **Quali Sim 次之**：進站後 1-3 圈
3. **Unknown**：無法分類的圈（不納入分組分析）

---

## 📁 輸出格式

### JSON 結構
```json
{
  "success": true,
  "function_id": "120",
  "year": 2024,
  "race": "Abu Dhabi",
  "session": "FP2",
  "analysis_type": "fp2_corner_all_laps_analysis",
  
  "selected_corners": {
    "low_speed": {
      "corner_number": 10,
      "apex_distance": 2450.5,
      "avg_apex_speed": 85.3
    },
    "mid_speed": {
      "corner_number": 5,
      "apex_distance": 1200.8,
      "avg_apex_speed": 155.7
    },
    "high_speed": {
      "corner_number": 2,
      "apex_distance": 650.2,
      "avg_apex_speed": 225.9
    }
  },
  
  "mode_a_unified": {
    "mode": "unified",
    "description": "所有有效圈統一分析",
    "drivers": [
      {
        "driver": "VER",
        "total_laps": 25,
        "valid_laps": 18,
        "filtering_summary": { /* ... */ },
        "corners": {
          "low_speed_corner_10": {
            "median_speed": 88.5,
            "mean_speed": 87.8,
            "std_dev": 2.3,
            "q1": 86.2,
            "q3": 89.7,
            "iqr": 3.5,
            "min_speed": 83.5,
            "max_speed": 91.2,
            "top3_avg": 90.5,
            "bottom3_avg": 84.1,
            "cv": 2.6,
            "valid_laps": 18,
            "filtered_laps": 7
          }
        }
      }
    ]
  },
  
  "mode_b_grouped": {
    "mode": "grouped",
    "description": "長距離 vs 排位模擬分組分析",
    "groups": {
      "long_run": {
        "description": "連續多圈模擬（高燃油）",
        "drivers": [
          {
            "driver": "VER",
            "lap_range": "1-12",
            "valid_laps": 12,
            "corners": {
              "low_speed_corner_10": {
                "median_speed": 87.2,
                "mean_speed": 86.9,
                "std_dev": 1.8,
                "valid_laps": 12
              }
            }
          }
        ]
      },
      "quali_sim": {
        "description": "排位模擬（低燃油）",
        "drivers": [
          {
            "driver": "VER",
            "lap_range": "15-20",
            "valid_laps": 6,
            "corners": {
              "low_speed_corner_10": {
                "median_speed": 90.1,
                "mean_speed": 89.8,
                "std_dev": 1.2,
                "valid_laps": 6
              }
            }
          }
        ]
      }
    }
  }
}
```

---

## 🧪 測試計劃

### 測試用例 1: 基礎功能測試
```bash
python f1_analysis_modular_main.py -f 120 -y 2024 -r "Abu Dhabi" -s FP2
```

**期望輸出**：
- ✅ 成功分類 3 個彎道（低/中/高速）
- ✅ 模式 A 提供統一分析結果
- ✅ 模式 B 提供分組分析結果
- ✅ 所有車手的統計指標完整
- ✅ JSON 檔案正確生成

### 測試用例 2: 異常值過濾驗證
- 驗證黃旗圈被正確過濾
- 驗證 In/Out Lap 被識別
- 驗證統計異常值被移除
- 檢查過濾統計報告

### 測試用例 3: 分組邏輯驗證
- 驗證 Long Run 正確識別（連續圈）
- 驗證 Quali Sim 正確識別（進站後單圈）
- 檢查分組的合理性

### 測試用例 4: 數據品質警告
```python
# 樣本量不足警告
if valid_laps < 5:
    warnings.append(f"{driver} {corner}: 有效圈數不足 ({valid_laps} < 5)")

# 高變異警告
if cv > 5.0:  # 變異係數 > 5%
    warnings.append(f"{driver} {corner}: 數據變異過大 (CV={cv:.2f}%)")
```

---

## 📌 實作檢查清單

### Phase 1: 核心架構（參考 F47）
- [ ] 建立 `FP2CornerAllLapsAnalysis` 類別
- [ ] 實現彎道分類邏輯（繼承 F47）
- [ ] 實現代表彎道選擇（繼承 F47）

### Phase 2: 異常值過濾
- [ ] 實現規則過濾（9 種過濾條件）
- [ ] 實現統計過濾（IQR 方法）
- [ ] 生成過濾統計報告

### Phase 3: 統計計算
- [ ] 計算 13 種統計指標
- [ ] 實現數據品質警告
- [ ] 處理邊界情況（少於 3 圈）

### Phase 4: 分組分析
- [ ] 實現 Long Run / Quali Sim 檢測
- [ ] 對兩組分別計算統計指標
- [ ] 生成分組報告

### Phase 5: 整合與測試
- [ ] 註冊到 function_mapper.py
- [ ] 建立測試腳本
- [ ] 驗證 JSON 輸出格式
- [ ] 撰寫使用文檔

---

## 🎯 後續視覺化討論

**留待開發完成後討論**：
1. Box Plot（顯示中位數、Q1、Q3、異常值）
2. Violin Plot（顯示完整分布）
3. 長距離 vs 排位模擬對比圖
4. 標準差熱力圖（車手一致性比較）

---

## 📝 開發日誌

### 2025-12-13
- ✅ 需求確認：雙模式分析（統一 + 分組）
- ✅ 確認統計指標：13 種完整指標
- ✅ 確認過濾邏輯：嚴格模式（9 種規則 + IQR）
- ✅ 建立任務文檔
- 🔄 開始實作核心模組...
