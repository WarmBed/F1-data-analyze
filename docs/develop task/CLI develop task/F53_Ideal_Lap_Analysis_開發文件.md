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
區間效率 = 各區間在最快圈中的表現 vs 理想區間時間
```

---

## 📊 輸入參數

### CLI 參數規格

```powershell
python f1_analysis_modular_main.py -f 53 -y <YEAR> -r <RACE> -s <SESSION>
```

| 參數 | 必填 | 說明 | 範例 |
|------|------|------|------|
| `-f` | ✅ | 功能編號 (固定為 53) | `53` |
| `-y` / `--year` | ✅ | 賽季年份 | `2024`, `2025` |
| `-r` / `--race` | ✅ | 賽事名稱 | `Japan`, `Monaco`, `Bahrain` |
| `-s` / `--session` | ✅ | 賽事階段 | `R` (正賽), `Q` (排位賽), `FP1/2/3` |

> Function 53 只提供**全車手模式**：執行時會一次載入該場次所有車手的圈速資料，並輸出跨車手的理想圈排名及比較分析。

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
│ - 分析每個區間的效率: sector_efficiency[i] = ...             │
│ - 判定哪些區間在最快圈中達到最佳                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 步驟 6: 統計計算                                              │
│ - 計算每個區間的統計值 (平均、標準差等)                       │
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

#### 單一車手理想圈計算（內部邏輯）

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
                'potential_improvement': round(time_gap, 3),
                'sector_efficiency': sector_efficiency
            },
            'statistics': {
                'sectors': sector_stats
            }
        }
    
    return None
```

#### 全車手理想圈排名輸出

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

### 全車手模式輸出

**檔案命名**: `ideal_lap_ranking_{year}_{race}_{session}.json`

```json
{
  "metadata": {
    "function_id": 53,
    "function_name": "Ideal Lap Analysis - All Drivers",
    "year": 2025,
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
      "ideal_lap_spread": 3.199
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
        },
        "laps": [
          {
            "lap_number": 15,
            "lap_time_seconds": 92.345,
            "lap_time_formatted": "1:32.345",
            "sector_times": {
              "s1": 25.456,
              "s2": 38.567,
              "s3": 28.322
            },
            "is_valid": true
          },
          {
            "lap_number": 23,
            "lap_time_seconds": 91.625,
            "lap_time_formatted": "1:31.625",
            "sector_times": {
              "s1": 25.123,
              "s2": 38.598,
              "s3": 27.904
            },
            "is_valid": true
          }
          // ...其餘圈次
        ],
        "ideal_lap_detail": {
          "total_time": 91.368,
          "formatted_time": "1:31.368",
          "sector_sources": {
            "s1": { "lap": 15, "time": 25.123 },
            "s2": { "lap": 23, "time": 38.456 },
            "s3": { "lap": 18, "time": 27.789 }
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
        },
        "laps": [ /* 同上，列出實際圈速與區段時間 */ ],
        "ideal_lap_detail": {
          "total_time": 91.456,
          "formatted_time": "1:31.456",
          "sector_sources": {
            "s1": { "lap": 20, "time": 25.234 },
            "s2": { "lap": 21, "time": 38.567 },
            "s3": { "lap": 18, "time": 27.655 }
          }
        }
      }
      // ...其餘車手
    ],
    "team_analysis": {
      "Red Bull Racing": {
        "drivers": ["VER", "PER"],
        "average_ideal_lap": 91.567,
        "best_driver": "VER"
      },
      "Ferrari": {
        "drivers": ["LEC", "SAI"],
        "average_ideal_lap": 91.678,
        "best_driver": "LEC"
      }
      // ...其他車隊
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

> 每位車手的資料皆包含：
> - `laps`：該場次所有有效圈的圈速與三段時間，可支援後續分析或 GUI 繪圖。
> - `ideal_lap_detail`：整合理想圈總時間與各區段來源圈次。

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

### 3. 異常處理

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

## 📝 開發檢查清單

### Phase 1: 核心演算法實現 ✅
- [ ] 建立 `ideal_lap_analysis.py` 檔案
- [ ] 實現單一車手理想圈計算函數
- [ ] 實現全車手理想圈排名函數
- [ ] 實現數據驗證函數
- [ ] 實現時間格式化函數
- [ ] 實現異常處理機制

### Phase 2: JSON 輸出格式 ✅
- [ ] 設計全車手 JSON 結構
- [ ] 實現 JSON 序列化函數
- [ ] 實現檔案命名規則
- [ ] 實現檔案儲存邏輯

### Phase 3: CLI 整合 ✅
- [ ] 在 `function_mapper.py` 註冊 Function 53
- [ ] 實現 CLI 參數解析
- [ ] 實現全車手模式
- [ ] 實現進度顯示

### Phase 4: 測試與驗證 ✅
- [ ] 測試全車手模式 (2025 Japan R)
- [ ] 驗證 JSON 格式正確性
- [ ] 測試異常情況處理
- [ ] 效能測試 (大數據量)

### Phase 5: 文檔與發布 ✅
- [ ] 更新此開發文件

---

## 🧪 測試計畫

### 測試案例

```powershell
# 測試 1: 全車手 (2025 日本站正賽)
python f1_analysis_modular_main.py -f 53 -y 2025 -r Japan -s R

# 測試 2: 全車手 (2024 摩納哥站排位賽)
python f1_analysis_modular_main.py -f 53 -y 2024 -r Monaco -s Q

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
├── ideal_lap_ranking_2025_Japan_R.json
├── ideal_lap_ranking_2024_Monaco_Q.json
├── ideal_lap_ranking_2024_Bahrain_R.json
└── ideal_lap_ranking_2025_Australia_Q.json
```

---

##  參考資料

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
