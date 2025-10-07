# F53 理想圈分析 (Ideal Lap Analysis) - 開發文件

**功能編號**: Function 53  
**CLI 指令**: `-f 53`  
**開發狀態**: 📝 規劃階段  
**目標版本**: v1.0.0  
**建立日期**: 2025-10-07  
**最後更新**: 2025-10-07

---

## 🎯 功能目的

**理想圈分析 (Ideal Lap Analysis)** 是一個專業的賽車數據分析功能，用於計算車手在特定賽事中的「理想圈速」，並與實際最快圈進行比較，找出車手的潛在進步空間與一致性表現。

### 核心概念

**理想圈 (Ideal Lap)**:
- 將車手所有完成的圈速中，每個區間 (Sector 1, 2, 3) 的最佳時間組合起來
- 代表車手在該賽事中「理論上能達到的最快圈速」
- 用於評估車手在單圈中的一致性與穩定性

**計算公式**:
```
理想圈時間 = Min(所有圈的 Sector1) + Min(所有圈的 Sector2) + Min(所有圈的 Sector3)
```

**與最快圈比較**:
```
潛在進步空間 = 最快圈時間 - 理想圈時間
一致性分數 = (理想圈時間 / 最快圈時間) × 100%
區間效率 = 各區間在最快圈中的表現 vs 理想區間時間
```

---

## 📊 輸入參數

### CLI 參數規格

```powershell
python f1_analysis_modular_main.py -f 53 -y <YEAR> -r <RACE> -s <SESSION> [-d <DRIVER>]
```

| 參數 | 必填 | 說明 | 範例 |
|------|------|------|------|
| `-f` | ✅ | 功能編號 (固定為 53) | `53` |
| `-y` / `--year` | ✅ | 賽季年份 | `2024`, `2025` |
| `-r` / `--race` | ✅ | 賽事名稱 | `Japan`, `Monaco`, `Bahrain` |
| `-s` / `--session` | ✅ | 賽事階段 | `R` (正賽), `Q` (排位賽), `FP1/2/3` |
| `-d` / `--driver` | ❌ | 車手代碼 (可選) | `VER`, `LEC`, `HAM` |

### 參數行為

1. **指定車手模式** (`-d` 提供):
   - 僅分析指定車手的理想圈
   - 輸出單一車手的詳細分析結果

2. **全車手模式** (`-d` 未提供):
   - 分析所有參賽車手的理想圈
   - 輸出全車手的理想圈排名比較
   - 包含車手間的理想圈差距分析

---

## 🔬 演算法設計

### 核心演算法流程

```
┌─────────────────────────────────────────────────────────────┐
│ 步驟 1: 數據載入                                              │
│ - 使用 FastF1 載入賽事數據                                    │
│ - 獲取所有車手的圈速數據 (Laps)                               │
│ - 過濾無效圈速 (IsAccurate == False)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 2: 區間時間提取                                          │
│ - 提取每一圈的 Sector1Time, Sector2Time, Sector3Time        │
│ - 轉換 Timedelta 為秒數 (total_seconds())                    │
│ - 過濾 NaN 和異常值                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 3: 理想圈計算                                            │
│ - 找出 Sector 1 的最小值 → ideal_s1                          │
│ - 找出 Sector 2 的最小值 → ideal_s2                          │
│ - 找出 Sector 3 的最小值 → ideal_s3                          │
│ - 計算理想圈總時間: ideal_lap = ideal_s1 + ideal_s2 + ideal_s3│
│ - 記錄每個最佳區間來自哪一圈                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 4: 最快圈分析                                            │
│ - 找出最快圈 (LapTime.min())                                  │
│ - 提取最快圈的區間時間                                        │
│ - 記錄最快圈的圈數                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 5: 比較分析                                              │
│ - 計算時間差距: gap = fastest_lap_time - ideal_lap_time      │
│ - 計算一致性分數: consistency = (ideal / fastest) × 100%     │
│ - 分析每個區間的效率: sector_efficiency[i] = ...             │
│ - 判定哪些區間在最快圈中達到最佳                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 6: 統計計算                                              │
│ - 計算每個區間的標準差 (一致性指標)                           │
│ - 計算區間改進潛力                                            │
│ - 識別最具改進空間的區間                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 7: JSON 輸出                                             │
│ - 生成結構化 JSON 數據                                        │
│ - 儲存到 json/ 目錄                                           │
│ - 返回成功訊息                                                │
└─────────────────────────────────────────────────────────────┘
```

---

### 詳細演算法實現

#### 1. 單一車手理想圈計算

```python
def calculate_ideal_lap(driver_laps):
    """
    計算單一車手的理想圈
    
    Args:
        driver_laps: DataFrame - 車手的所有圈速數據
        
    Returns:
        dict - 理想圈分析結果
    """
    # 1. 過濾有效圈速
    valid_laps = driver_laps[driver_laps['IsAccurate'] == True].copy()
    
    # 2. 提取區間數據
    sectors = ['Sector1Time', 'Sector2Time', 'Sector3Time']
    ideal_sectors = {}
    
    for i, sector_col in enumerate(sectors, 1):
        if sector_col in valid_laps.columns:
            # 移除 NaN
            sector_data = valid_laps[[sector_col, 'LapNumber']].dropna()
            
            if len(sector_data) > 0:
                # 找出最快區間時間
                min_idx = sector_data[sector_col].idxmin()
                min_sector_time = sector_data.loc[min_idx, sector_col]
                min_lap_number = sector_data.loc[min_idx, 'LapNumber']
                
                # 轉換為秒數
                if hasattr(min_sector_time, 'total_seconds'):
                    sector_seconds = min_sector_time.total_seconds()
                else:
                    sector_seconds = float(min_sector_time)
                
                ideal_sectors[f'sector_{i}'] = {
                    'time_seconds': round(sector_seconds, 3),
                    'lap_number': int(min_lap_number),
                    'formatted_time': f"{sector_seconds:.3f}s"
                }
    
    # 3. 計算理想圈總時間
    if len(ideal_sectors) == 3:
        ideal_lap_time = sum(s['time_seconds'] for s in ideal_sectors.values())
        
        # 4. 獲取最快圈數據
        fastest_lap_idx = valid_laps['LapTime'].idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        fastest_lap_time = fastest_lap['LapTime'].total_seconds()
        fastest_lap_num = int(fastest_lap['LapNumber'])
        
        # 5. 提取最快圈的區間時間
        fastest_lap_sectors = {}
        for i, sector_col in enumerate(sectors, 1):
            if sector_col in fastest_lap.index:
                sector_time = fastest_lap[sector_col]
                if pd.notna(sector_time):
                    if hasattr(sector_time, 'total_seconds'):
                        sector_seconds = sector_time.total_seconds()
                    else:
                        sector_seconds = float(sector_time)
                    
                    fastest_lap_sectors[f'sector_{i}'] = {
                        'time_seconds': round(sector_seconds, 3),
                        'formatted_time': f"{sector_seconds:.3f}s"
                    }
        
        # 6. 計算比較指標
        time_gap = fastest_lap_time - ideal_lap_time
        consistency_score = (ideal_lap_time / fastest_lap_time) * 100
        
        # 7. 區間效率分析
        sector_efficiency = {}
        for i in range(1, 4):
            sector_key = f'sector_{i}'
            ideal_time = ideal_sectors[sector_key]['time_seconds']
            fastest_time = fastest_lap_sectors[sector_key]['time_seconds']
            
            sector_gap = fastest_time - ideal_time
            is_optimal = abs(sector_gap) < 0.01  # 誤差小於 0.01 秒視為最佳
            
            sector_efficiency[sector_key] = {
                'ideal_time': ideal_time,
                'fastest_lap_time': fastest_time,
                'gap': round(sector_gap, 3),
                'is_optimal': is_optimal,
                'efficiency_percentage': round((ideal_time / fastest_time) * 100, 2)
            }
        
        # 8. 統計分析
        sector_stats = {}
        for i, sector_col in enumerate(sectors, 1):
            sector_times = valid_laps[sector_col].dropna()
            if len(sector_times) > 0:
                times_seconds = [t.total_seconds() if hasattr(t, 'total_seconds') else float(t) 
                                for t in sector_times]
                
                sector_stats[f'sector_{i}'] = {
                    'mean': round(np.mean(times_seconds), 3),
                    'std_dev': round(np.std(times_seconds), 3),
                    'min': round(min(times_seconds), 3),
                    'max': round(max(times_seconds), 3),
                    'range': round(max(times_seconds) - min(times_seconds), 3)
                }
        
        return {
            'ideal_lap': {
                'total_time': round(ideal_lap_time, 3),
                'sectors': ideal_sectors
            },
            'fastest_lap': {
                'total_time': round(fastest_lap_time, 3),
                'lap_number': fastest_lap_num,
                'sectors': fastest_lap_sectors
            },
            'comparison': {
                'time_gap': round(time_gap, 3),
                'consistency_score': round(consistency_score, 2),
                'potential_improvement': round(time_gap, 3),
                'sector_efficiency': sector_efficiency
            },
            'statistics': {
                'sectors': sector_stats
            }
        }
    
    return None
```

#### 2. 全車手理想圈排名

```python
def calculate_all_drivers_ideal_laps(session):
    """
    計算所有車手的理想圈並排名
    
    Args:
        session: FastF1 Session 對象
        
    Returns:
        dict - 全車手理想圈分析結果
    """
    results = []
    
    # 獲取所有車手
    drivers = session.laps['Driver'].unique()
    
    for driver in drivers:
        driver_laps = session.laps[session.laps['Driver'] == driver]
        
        # 計算該車手的理想圈
        ideal_lap_data = calculate_ideal_lap(driver_laps)
        
        if ideal_lap_data:
            results.append({
                'driver': driver,
                'team': driver_laps.iloc[0]['Team'] if 'Team' in driver_laps.columns else 'N/A',
                'ideal_lap_time': ideal_lap_data['ideal_lap']['total_time'],
                'fastest_lap_time': ideal_lap_data['fastest_lap']['total_time'],
                'time_gap': ideal_lap_data['comparison']['time_gap'],
                'consistency_score': ideal_lap_data['comparison']['consistency_score'],
                'details': ideal_lap_data
            })
    
    # 按理想圈時間排序
    results.sort(key=lambda x: x['ideal_lap_time'])
    
    # 計算與榜首的差距
    if len(results) > 0:
        leader_time = results[0]['ideal_lap_time']
        for i, result in enumerate(results):
            result['position'] = i + 1
            result['gap_to_leader'] = round(result['ideal_lap_time'] - leader_time, 3)
    
    return {
        'drivers': results,
        'total_drivers': len(results)
    }
```

---

## 📤 JSON 輸出格式

### 1. 單一車手模式輸出

**檔案命名**: `ideal_lap_analysis_{year}_{race}_{session}_{driver}_{timestamp}.json`

```json
{
  "metadata": {
    "function_id": 53,
    "function_name": "Ideal Lap Analysis",
    "year": 2024,
    "race": "Japan",
    "session": "R",
    "driver": "VER",
    "analysis_timestamp": "2025-10-07T14:30:00.123456",
    "api_source": "FastF1",
    "data_version": "1.0.0"
  },
  "analysis_result": {
    "driver_info": {
      "driver_code": "VER",
      "driver_name": "Max VERSTAPPEN",
      "team": "Red Bull Racing",
      "car_number": 1
    },
    "ideal_lap": {
      "total_time": 91.368,
      "formatted_time": "1:31.368",
      "sectors": {
        "sector_1": {
          "time_seconds": 25.123,
          "formatted_time": "25.123s",
          "lap_number": 15,
          "percentage_of_lap": 27.5
        },
        "sector_2": {
          "time_seconds": 38.456,
          "formatted_time": "38.456s",
          "lap_number": 23,
          "percentage_of_lap": 42.1
        },
        "sector_3": {
          "time_seconds": 27.789,
          "formatted_time": "27.789s",
          "lap_number": 18,
          "percentage_of_lap": 30.4
        }
      }
    },
    "fastest_lap": {
      "total_time": 91.625,
      "formatted_time": "1:31.625",
      "lap_number": 23,
      "sectors": {
        "sector_1": {
          "time_seconds": 25.123,
          "formatted_time": "25.123s"
        },
        "sector_2": {
          "time_seconds": 38.598,
          "formatted_time": "38.598s"
        },
        "sector_3": {
          "time_seconds": 27.904,
          "formatted_time": "27.904s"
        }
      }
    },
    "comparison": {
      "time_gap": 0.257,
      "formatted_gap": "+0.257s",
      "consistency_score": 99.72,
      "consistency_rating": "Excellent",
      "potential_improvement": 0.257,
      "sector_efficiency": {
        "sector_1": {
          "ideal_time": 25.123,
          "fastest_lap_time": 25.123,
          "gap": 0.000,
          "is_optimal": true,
          "efficiency_percentage": 100.00,
          "status": "Perfect"
        },
        "sector_2": {
          "ideal_time": 38.456,
          "fastest_lap_time": 38.598,
          "gap": 0.142,
          "is_optimal": false,
          "efficiency_percentage": 99.63,
          "status": "Near Optimal",
          "improvement_potential": 0.142
        },
        "sector_3": {
          "ideal_time": 27.789,
          "fastest_lap_time": 27.904,
          "gap": 0.115,
          "is_optimal": false,
          "efficiency_percentage": 99.59,
          "status": "Near Optimal",
          "improvement_potential": 0.115
        }
      },
      "optimal_sectors_count": 1,
      "total_sectors": 3,
      "optimal_percentage": 33.33
    },
    "statistics": {
      "total_laps_analyzed": 53,
      "valid_laps": 48,
      "sectors": {
        "sector_1": {
          "mean": 25.678,
          "std_dev": 0.234,
          "min": 25.123,
          "max": 26.789,
          "range": 1.666,
          "consistency_rating": "Good"
        },
        "sector_2": {
          "mean": 39.012,
          "std_dev": 0.456,
          "min": 38.456,
          "max": 40.234,
          "range": 1.778,
          "consistency_rating": "Average"
        },
        "sector_3": {
          "mean": 28.123,
          "std_dev": 0.189,
          "min": 27.789,
          "max": 28.901,
          "range": 1.112,
          "consistency_rating": "Excellent"
        }
      }
    },
    "insights": {
      "overall_assessment": "Driver shows excellent consistency with 99.72% efficiency. Sector 1 achieved perfect performance in fastest lap.",
      "strongest_sector": "sector_3",
      "weakest_sector": "sector_2",
      "improvement_opportunities": [
        "Sector 2 has 0.142s improvement potential",
        "Sector 3 has 0.115s improvement potential"
      ],
      "consistency_highlights": [
        "Sector 1: Perfect execution in fastest lap",
        "Sector 3: Excellent consistency (std_dev: 0.189s)"
      ]
    }
  },
  "export_info": {
    "file_format": "JSON",
    "encoding": "UTF-8",
    "generated_by": "F1T CLI Function 53",
    "cli_version": "1.0.0"
  }
}
```

---

### 2. 全車手模式輸出

**檔案命名**: `ideal_lap_ranking_{year}_{race}_{session}_all_drivers_{timestamp}.json`

```json
{
  "metadata": {
    "function_id": 53,
    "function_name": "Ideal Lap Analysis - All Drivers",
    "year": 2024,
    "race": "Japan",
    "session": "R",
    "analysis_timestamp": "2025-10-07T14:30:00.123456",
    "api_source": "FastF1",
    "data_version": "1.0.0"
  },
  "analysis_result": {
    "summary": {
      "total_drivers": 20,
      "fastest_ideal_lap": 91.368,
      "slowest_ideal_lap": 94.567,
      "average_ideal_lap": 92.789,
      "ideal_lap_spread": 3.199,
      "average_consistency_score": 98.45
    },
    "ranking": [
      {
        "position": 1,
        "driver": "VER",
        "driver_name": "Max VERSTAPPEN",
        "team": "Red Bull Racing",
        "ideal_lap_time": 91.368,
        "fastest_lap_time": 91.625,
        "time_gap": 0.257,
        "gap_to_leader": 0.000,
        "consistency_score": 99.72,
        "optimal_sectors": 1,
        "sector_breakdown": {
          "sector_1": {
            "time": 25.123,
            "is_optimal_in_fastest": true
          },
          "sector_2": {
            "time": 38.456,
            "is_optimal_in_fastest": false
          },
          "sector_3": {
            "time": 27.789,
            "is_optimal_in_fastest": false
          }
        }
      },
      {
        "position": 2,
        "driver": "LEC",
        "driver_name": "Charles LECLERC",
        "team": "Ferrari",
        "ideal_lap_time": 91.456,
        "fastest_lap_time": 91.789,
        "time_gap": 0.333,
        "gap_to_leader": 0.088,
        "consistency_score": 99.58,
        "optimal_sectors": 2,
        "sector_breakdown": {
          "sector_1": {
            "time": 25.234,
            "is_optimal_in_fastest": true
          },
          "sector_2": {
            "time": 38.567,
            "is_optimal_in_fastest": true
          },
          "sector_3": {
            "time": 27.655,
            "is_optimal_in_fastest": false
          }
        }
      }
      // ... 其他車手數據
    ],
    "team_analysis": {
      "Red Bull Racing": {
        "drivers": ["VER", "PER"],
        "average_ideal_lap": 91.567,
        "average_consistency": 99.45,
        "best_driver": "VER"
      },
      "Ferrari": {
        "drivers": ["LEC", "SAI"],
        "average_ideal_lap": 91.678,
        "average_consistency": 99.23,
        "best_driver": "LEC"
      }
      // ... 其他車隊
    },
    "sector_comparison": {
      "sector_1": {
        "fastest_time": 25.123,
        "fastest_driver": "VER",
        "slowest_time": 26.234,
        "slowest_driver": "BOT",
        "average_time": 25.678,
        "spread": 1.111
      },
      "sector_2": {
        "fastest_time": 38.456,
        "fastest_driver": "VER",
        "slowest_time": 39.789,
        "slowest_driver": "TSU",
        "average_time": 39.012,
        "spread": 1.333
      },
      "sector_3": {
        "fastest_time": 27.655,
        "fastest_driver": "LEC",
        "slowest_time": 28.901,
        "slowest_driver": "SAR",
        "average_time": 28.234,
        "spread": 1.246
      }
    }
  },
  "export_info": {
    "file_format": "JSON",
    "encoding": "UTF-8",
    "generated_by": "F1T CLI Function 53",
    "cli_version": "1.0.0"
  }
}
```

---

## 🔧 技術實現細節

### 1. 數據驗證

```python
def validate_sector_data(driver_laps):
    """
    驗證區間數據的完整性
    
    Returns:
        tuple: (is_valid, missing_sectors)
    """
    required_columns = ['Sector1Time', 'Sector2Time', 'Sector3Time']
    missing = [col for col in required_columns if col not in driver_laps.columns]
    
    if missing:
        return False, missing
    
    # 檢查是否有足夠的有效數據
    valid_count = 0
    for col in required_columns:
        valid_count += driver_laps[col].notna().sum()
    
    # 至少需要每個區間有一個有效數據
    return valid_count >= 3, []
```

### 2. 時間格式化

```python
def format_lap_time(seconds):
    """
    將秒數格式化為 MM:SS.mmm 格式
    
    Args:
        seconds: float - 總秒數
        
    Returns:
        str - 格式化後的時間字串
    """
    if seconds is None or np.isnan(seconds):
        return "N/A"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes > 0:
        return f"{minutes}:{remaining_seconds:06.3f}"
    else:
        return f"{remaining_seconds:.3f}s"
```

### 3. 一致性評級

```python
def get_consistency_rating(consistency_score):
    """
    根據一致性分數給予評級
    
    Args:
        consistency_score: float - 一致性分數 (0-100)
        
    Returns:
        str - 評級字串
    """
    if consistency_score >= 99.5:
        return "Excellent"
    elif consistency_score >= 99.0:
        return "Very Good"
    elif consistency_score >= 98.5:
        return "Good"
    elif consistency_score >= 98.0:
        return "Average"
    else:
        return "Needs Improvement"
```

### 4. 異常處理

```python
def safe_calculate_ideal_lap(driver_laps, driver_code):
    """
    安全地計算理想圈，包含完整的異常處理
    
    Returns:
        dict or None
    """
    try:
        # 驗證數據
        is_valid, missing = validate_sector_data(driver_laps)
        if not is_valid:
            print(f"[WARNING] 車手 {driver_code} 缺少區間數據: {missing}")
            return None
        
        # 過濾有效圈速
        valid_laps = driver_laps[driver_laps['IsAccurate'] == True]
        if len(valid_laps) < 3:
            print(f"[WARNING] 車手 {driver_code} 有效圈速不足 (< 3 圈)")
            return None
        
        # 執行計算
        result = calculate_ideal_lap(valid_laps)
        return result
        
    except Exception as e:
        print(f"[ERROR] 計算車手 {driver_code} 理想圈時發生錯誤: {str(e)}")
        return None
```

---

## 🎨 GUI 繪圖建議

### 推薦的視覺化圖表

1. **理想圈 vs 最快圈比較圖** (Bar Chart)
   - X 軸: 區間 (S1, S2, S3, Total)
   - Y 軸: 時間 (秒)
   - 兩組柱狀圖: 理想圈、最快圈

2. **區間效率雷達圖** (Radar Chart)
   - 三個軸: Sector 1, 2, 3
   - 顯示各區間的效率百分比

3. **全車手理想圈排名** (Horizontal Bar Chart)
   - Y 軸: 車手代碼
   - X 軸: 理想圈時間
   - 顏色: 車隊顏色

4. **一致性分數儀表板** (Gauge Chart)
   - 顯示 0-100% 的一致性分數
   - 顏色分級: 綠色 (>99%), 黃色 (98-99%), 紅色 (<98%)

5. **區間時間分佈圖** (Box Plot)
   - 顯示每個區間的時間分佈
   - 標示最佳時間點

---

## 📝 開發檢查清單

### Phase 1: 核心演算法實現 ✅
- [ ] 建立 `ideal_lap_analysis.py` 檔案
- [ ] 實現單一車手理想圈計算函數
- [ ] 實現全車手理想圈排名函數
- [ ] 實現數據驗證函數
- [ ] 實現時間格式化函數
- [ ] 實現異常處理機制

### Phase 2: JSON 輸出格式 ✅
- [ ] 設計單一車手 JSON 結構
- [ ] 設計全車手 JSON 結構
- [ ] 實現 JSON 序列化函數
- [ ] 實現檔案命名規則
- [ ] 實現檔案儲存邏輯

### Phase 3: CLI 整合 ✅
- [ ] 在 `function_mapper.py` 註冊 Function 53
- [ ] 實現 CLI 參數解析
- [ ] 實現單一車手模式
- [ ] 實現全車手模式
- [ ] 實現進度顯示

### Phase 4: 測試與驗證 ✅
- [ ] 測試單一車手模式 (VER, 2024 Japan R)
- [ ] 測試全車手模式 (2024 Japan R)
- [ ] 驗證 JSON 格式正確性
- [ ] 測試異常情況處理
- [ ] 效能測試 (大數據量)

### Phase 5: 文檔與發布 ✅
- [ ] 完成 API 文檔
- [ ] 完成使用範例
- [ ] 更新 README.md
- [ ] 更新 CHANGELOG.md
- [ ] 發布 v1.0.0

---

## 🧪 測試計畫

### 測試案例

```powershell
# 測試 1: 單一車手 - VER (2024 日本站正賽)
python f1_analysis_modular_main.py -f 53 -y 2024 -r Japan -s R -d VER

# 測試 2: 單一車手 - LEC (2024 摩納哥站排位賽)
python f1_analysis_modular_main.py -f 53 -y 2024 -r Monaco -s Q -d LEC

# 測試 3: 全車手 (2024 巴林站正賽)
python f1_analysis_modular_main.py -f 53 -y 2024 -r Bahrain -s R

# 測試 4: 全車手 (2025 澳洲站排位賽)
python f1_analysis_modular_main.py -f 53 -y 2025 -r Australia -s Q

# 測試 5: 異常情況 - 不存在的賽事
python f1_analysis_modular_main.py -f 53 -y 2024 -r InvalidRace -s R
```

### 預期輸出檔案

```
json/
├── ideal_lap_analysis_2024_Japan_R_VER_20251007_143000.json
├── ideal_lap_analysis_2024_Monaco_Q_LEC_20251007_143100.json
├── ideal_lap_ranking_2024_Bahrain_R_all_drivers_20251007_143200.json
└── ideal_lap_ranking_2025_Australia_Q_all_drivers_20251007_143300.json
```

---

## 📊 效能考量

### 預估執行時間

| 模式 | 資料量 | 預估時間 |
|------|--------|----------|
| 單一車手 | ~50 圈 | 0.5-1 秒 |
| 全車手 (20 位) | ~1000 圈 | 3-5 秒 |

### 記憶體使用

- 單一車手: ~10 MB
- 全車手: ~50 MB

### 優化建議

1. 使用 `pandas` 向量化操作
2. 避免不必要的迴圈
3. 快取中間計算結果
4. 使用 `numba` 加速關鍵計算 (選擇性)

---

## 🚀 未來擴展功能

### v1.1.0 計畫
- [ ] 理想圈趨勢分析 (整個賽季)
- [ ] 輪胎類型對理想圈的影響
- [ ] 燃油負載修正

### v1.2.0 計畫
- [ ] 機器學習預測理想圈
- [ ] 賽道條件對理想圈的影響
- [ ] 多賽事理想圈比較

### v2.0.0 計畫
- [ ] 即時理想圈計算 (Live Timing)
- [ ] 理想圈視覺化動畫
- [ ] 賽車模擬整合

---

## 📚 參考資料

### FastF1 API 文檔
- [Laps API](https://docs.fastf1.dev/core.html#laps)
- [Sector Times](https://docs.fastf1.dev/core.html#fastf1.core.Laps.Sector1Time)

### F1 官方規則
- [Sector Definition](https://www.fia.com/regulation/category/110)

### 相關研究
- Motorsport Data Analysis Best Practices
- Formula 1 Performance Engineering

---

## ✅ 簽核

| 角色 | 姓名 | 日期 | 簽名 |
|------|------|------|------|
| 開發者 | GitHub Copilot | 2025-10-07 | ✅ |
| 審核者 | - | - | - |
| 批准者 | - | - | - |

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-10-07  
**下次審核**: 實現完成後
