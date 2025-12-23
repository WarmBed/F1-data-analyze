# P2 追趕 P1 策略建議模組 - 設計文件

**創建日期**: 2025-12-08  
**狀態**: 討論階段  
**優先級**: 高

---

## 📋 目錄
- [模組概述](#模組概述)
- [核心場景分析](#核心場景分析)
- [數據需求](#數據需求)
- [計算邏輯](#計算邏輯)
- [技術架構](#技術架構)
- [實現計劃](#實現計劃)

---

## 🎯 模組概述

### 目標
當 P2（第二名）想要追上 P1（領先者）時，系統分析並建議**實際可行的追趕策略**，評估：
- **可追回的時間** - P2 在剩餘圈數內能縮小多少差距
- **最佳策略建議** - 推薦最有效的追趕方法（輪胎策略、進站時機等）
- **預計追上圈數** - 如果策略成功，P2 將在第幾圈追上 P1

**注意**：本模組僅評估「能否追近到 P1」，不預測超車成功率（超車成功取決於賽道特性、車手技術等不可控因素）

### 核心問題
**「P2 在剩餘圈數內，能否追近到 P1？需要多少圈？用什麼策略？」**

### 應用場景
1. **賽事直播分析**：Live Timing 中實時計算追趕可能性
2. **賽後策略回顧**：分析「如果改用 X 策略會如何？」
3. **策略模擬訓練**：為車隊策略師提供決策參考

---

## 🏎️ 核心場景分析

### 場景 1: 輪胎策略差異 🛞（核心場景）

#### 1.1 新胎 vs 舊胎優勢
**定義**: P2 使用較新的輪胎，P1 繼續使用舊胎

**關鍵參數**:
```python
scenario_tire_age_delta = {
    "p1_tire_age": 15,           # P1 輪胎已使用圈數
    "p2_tire_age": 3,            # P2 輪胎已使用圈數
    "tire_degradation_rate": 0.08,  # 每圈衰退率 (秒/圈)
    "remaining_laps": 20         # 剩餘比賽圈數
}
```

**計算邏輯**:
```
輪胎年齡差距 = p1_tire_age - p2_tire_age = 12 圈
每圈速度優勢 = 輪胎年齡差距 × tire_degradation_rate = 12 × 0.08 = 0.96s/lap

可追回時間 = 每圈速度優勢 × remaining_laps = 0.96 × 20 = 19.2s
```

**可行性判斷**:
```python
if 可追回時間 >= 當前差距:
    追上圈數 = 當前圈 + ceil(當前差距 / 每圈速度優勢)
    return f"✅ 可行：預計第 {追上圈數} 圈追上 P1"
else:
    return "❌ 不可行：輪胎優勢不足以追上"
```

**車手推進模式調整**（可選）:
```python
# 預設：兩車手推進強度相同
default_mode = "normal"

# 進階選項：允許用戶調整
p1_mode = "tire_management"  # P1 管理輪胎（每圈慢 0.1-0.2s）
p2_mode = "attack"           # P2 攻擊模式（每圈快 0.1s，但輪胎衰退加速）

if p1_mode == "tire_management":
    每圈速度優勢 += 0.15  # P1 管理模式，P2 額外優勢
if p2_mode == "attack":
    每圈速度優勢 += 0.10  # P2 攻擊模式，額外優勢
    輪胎壽命 -= 3         # 但輪胎壽命縮短
```

#### 1.2 配方選擇差異
**定義**: P2 使用更軟/更快的配方（如 Soft vs Medium）

**關鍵參數**:
```python
scenario_compound_delta = {
    "p1_compound": "MEDIUM",     # P1 使用配方
    "p2_compound": "SOFT",       # P2 使用配方
    "compound_delta_per_lap": 0.4,  # 配方單圈速度差 (秒/圈)
    "p2_compound_life": 15,      # P2 配方預期壽命 (圈)
    "remaining_laps": 20
}
```

**計算邏輯**:
### 場景 2: 進站策略差異 🔧（核心場景）
有效推進圈數 = min(p2_compound_life, remaining_laps) = 15 圈
可追回時間 = compound_delta_per_lap × 有效推進圈數 = 0.4 × 15 = 6.0s

但需考慮額外進站成本:
if p2_compound_life < remaining_laps:
    額外進站損失 = pit_loss_time = ~22s
    淨可追回時間 = 6.0 - 22 = -16s (不可行)
```

**權衡分析**:
- **優勢**: 短期內有明顯速度優勢
- **風險**: 可能需要額外進站，損失更多時間
- **適用**: 剩餘圈數少於配方壽命時最有效

---

### 場景 2: 進站策略差異 🔧

#### 2.1 進站次數優勢（Undercut/Overcut）
**定義**: P2 通過巧妙的進站時機在 P1 進站時完成超越

**A. Undercut 策略（提前進站）**
```python
scenario_undercut = {
    "current_gap": 3.5,          # 當前差距 (秒)
    "pit_loss_time": 22.0,       # 進站損失時間
    "new_tire_advantage": 1.2,   # 新胎每圈優勢 (秒/圈)
    "p1_planned_pit_lap": 25,    # P1 計劃進站圈
    "p2_pit_lap": 22             # P2 提前進站圈
}
```

**計算邏輯**:
```
步驟 1: P2 第 22 圈進站，損失 22s
步驟 2: P2 出站後用新胎追 P1（舊胎）
       追趕圈數 = 25 - 22 = 3 圈
       可追回時間 = 1.2 × 3 = 3.6s
       
步驟 3: P1 第 25 圈進站，損失 22s
步驟 4: P2 在 P1 進站期間的領先優勢
       領先時間 = 可追回時間 - 原始差距 = 3.6 - 3.5 = 0.1s

結論: ✅ Undercut 成功，P2 領先 0.1s
```

**B. Overcut 策略（延後進站）**
```python
scenario_overcut = {
    "current_gap": 3.5,
    "p1_pit_lap": 20,            # P1 先進站
    "p2_pit_lap": 25,            # P2 延後進站
    "old_tire_degradation": 0.3  # 舊胎每圈衰退 (秒/圈)
}
```

**計算邏輯**:
```
步驟 1: P1 第 20 圈進站，P2 繼續跑
步驟 2: P2 用舊胎維持速度（輕油 + 清空賽道）
       維持圈數 = 25 - 20 = 5 圈
       每圈損失 ≈ 0.3s (輪胎衰退) - 0.2s (輕油優勢) = 0.1s
       總損失 = 0.1 × 5 = 0.5s
       
步驟 3: P1 進站損失 = 22s
步驟 4: P2 第 25 圈進站後位置計算
       淨優勢 = 22 - 3.5 - 0.5 = 18s

結論: ✅ Overcut 成功，P2 領先 18s
```

#### 2.2 進站次數減少策略
**定義**: P2 少進站一次，節省 pit loss 時間

**關鍵參數**:
```python
scenario_fewer_stops = {
    "p1_total_stops": 2,         # P1 總進站次數
    "p2_total_stops": 1,         # P2 總進站次數
    "pit_loss_per_stop": 22.0,   # 每次進站損失
    "tire_life_difference": 8,   # 輪胎壽命劣勢 (圈)
    "degradation_penalty": 0.15  # 舊胎每圈懲罰 (秒/圈)
}
### 場景 3: Safety Car 機會 🚨（機會場景）

#### 3.1 Safety Car (SC) 窗口
**定義**: 假設 SC 出現，P2 利用 SC 期間進站，可節省多少時間

**關鍵參數**:
```python
scenario_safety_car = {
    "normal_pit_loss": 22.0,     # 正常進站損失
    "sc_pit_loss": 8.0,          # SC 期間進站損失
    "remaining_laps": 20,
    "p1_tire_age": 15,
    "p2_tire_age": 8
}
```

**計算邏輯**:
```
假設 SC 出現，P2 進站：
  節省時間 = normal_pit_loss - sc_pit_loss = 22 - 8 = 14s
  
  SC 重啟後 P2 優勢:
    進站損失節省 = 14s
    新胎優勢 = 輪胎年齡差 × 衰退率 × 剩餘圈數
    
  總優勢 = 14s + 新胎優勢時間
  
顯示結果:
  "💡 機會：如果 SC 出現，P2 可通過進站獲得 14s 優勢"
  "預計追上：P2 可在 SC 重啟後 X 圈追上 P1"
```

**注意**：
- 不計算 SC 出現機率（因為 SC 是偶發事件）
- 僅顯示「如果 SC 出現，能獲得多少優勢」
- 這是最佳追趕機會窗口

#### 3.2 Virtual Safety Car (VSC)
**定義**: 假設 VSC 出現，P2 進站可節省時間（效果不如 SC）

**關鍵參數**:
```python
scenario_vsc = {
    "normal_pit_loss": 22.0,
    "vsc_pit_loss": 15.0,        # VSC 期間進站損失
    "vsc_duration_avg": 3.5      # 平均持續圈數
}
```

**計算邏輯**:
```
假設 VSC 出現，P2 進站：
  節省時間 = 22 - 15 = 7s
  
  VSC 重啟後 P2 優勢:
    進站損失節省 = 7s
    新胎優勢 = 輪胎優勢時間
    
顯示結果:
  "💡 機會：如果 VSC 出現，P2 可獲得 7s 優勢（小於 SC）"
```鍵參數**:
```python
scenario_vsc = {
    "normal_pit_loss": 22.0,
    "vsc_pit_loss": 15.0,        # VSC 期間進站損失
    "vsc_probability": 0.42,     # VSC 機率 > SC
    "vsc_duration_avg": 3.5      # 平均持續圈數
}
```

**計算邏輯**:
```
VSC 進站優勢 = 22 - 15 = 7s

但 VSC 結束後位置計算:
if P1 未進站 and P2 已進站:
    淨優勢 = 7s + (新胎優勢 × 剩餘圈數)
```

---

### 場景 4: DRS 效應與超車點 🏁

#### 4.1 DRS 追趕計算
---

### 場景 4: DRS 縮小差距 🏁（輔助場景）

**定義**: 當 P2 在 DRS 範圍內（< 1 秒），DRS 可加速縮小差距

**關鍵參數**:
```python
scenario_drs = {
    "current_gap": 0.8,          # 當前差距 (秒) - 在 DRS 範圍內
    "drs_advantage": 0.35,       # DRS 每圈優勢 (秒)
    "track_drs_zones": 2,        # 該賽道 DRS 區數量
}
```

**計算邏輯**:
```
if current_gap < 1.0:  # 在 DRS 範圍內
    每圈額外縮小差距 = drs_advantage × track_drs_zones = 0.35 × 2 = 0.7s
    
    追上所需圈數 = current_gap / 每圈縮小差距 = 0.8 / 0.7 = 2 圈
    預計追上圈數 = 當前圈 + 2 圈
    
顯示結果:
  "✅ DRS 輔助：P2 在 DRS 範圍內，每圈可額外縮小 0.7s"
  "預計追上：第 X 圈追上 P1（不保證能超車）"
else:
  "❌ 超出 DRS 範圍：需先通過其他策略縮小至 1 秒內"
```

**注意**：
- 僅計算 DRS 對縮小差距的影響
- 不預測超車成功率（超車取決於賽道特性和車手技術）
- DRS 是「加速追近」的工具，不是「保證超車」的手段

---

### 場景 5: Traffic（慢車）機會 🚦（輔助場景）

#### 5.1 P1 遇到慢車的時機評估
    "lapped_cars_ahead": 3,      # P1 前方待超慢車數
    "time_loss_per_car": 1.2,    # 每輛慢車平均損失 (秒)
    "p2_track_clear": True       # P2 賽道是否清空
}
```

**計算邏輯**:
**定義**: 評估 P1 何時會遇到慢車，以及 P2 能否利用這個機會

**關鍵參數**:
```python
scenario_traffic = {
    "lapped_cars": [
        {"driver": "LAT", "position_km": 3.2, "lap": 24},  # 慢車位置
        {"driver": "SAR", "position_km": 4.1, "lap": 23},
        {"driver": "ZHO", "position_km": 5.5, "lap": 22}
    ],
    "p1_position_km": 2.8,       # P1 當前位置
    "p1_lap_time": 78.5,         # P1 單圈時間
    "track_length_km": 5.8,      # 賽道長度
    "time_loss_per_car": 1.2     # 每輛慢車平均損失 (秒)
}
```

**計算邏輯**:
```
步驟 1: 計算 P1 何時追上慢車
  for each lapped_car:
     "spin": {"probability": 0.01, "time_loss": 8.0}
    },
    "remaining_laps": 20
}
```

**計算邏輯**:
```
預期失誤次數 = track_error_rate × remaining_laps = 0.08 × 20 = 1.6 次

期望損失時間計算:
  鎖死: 0.05 × 20 × 1.5 = 1.5s
  賽道邊界: 0.02 × 20 × 0.3 = 0.12s
  打轉: 0.01 × 20 × 8.0 = 1.6s
  
總期望損失 = 1.5 + 0.12 + 1.6 = 3.22s

結論: P2 平均可期望獲得 3.2s 的機會
```

---

## 📊 數據需求

### 必需數據（Mandatory）

#### 1. 即時賽事數據（Live Timing API）
```python
live_race_data = {
    # 位置與差距
    "p1": {
        "driver": "VER",
        "position": 1,
        "lap": 25,
        "tire_age": 12,
        "tire_compound": "MEDIUM",
        "last_lap_time": 78.234
    },
    "p2": {
        "driver": "LEC",
        "position": 2,
        "gap_to_leader": 3.456,  # 秒
        "lap": 25,
        "tire_age": 8,
        "tire_compound": "MEDIUM",
        "last_lap_time": 78.567
    },
    
    # 比賽狀態
    "race_status": {
        "total_laps": 53,
        "current_lap": 25,
        "remaining_laps": 28,
        "track_status": "GREEN",  # GREEN/YELLOW/SC/VSC/RED
        "weather": "DRY"
    }
}
```

#### 2. 歷史輪胎數據（Tire Degradation Database）
```python
tire_degradation_db = {
    "circuit": "Suzuka",
    "compounds": {
        "SOFT": {
            "base_lap_time": 90.5,
            "degradation_rate": 0.12,  # 每圈衰退 (秒)
            "cliff_lap": 18,           # 衰竭圈數
            "optimal_stint": "10-15"
        },
        "MEDIUM": {
            "base_lap_time": 91.2,
            "degradation_rate": 0.08,
            "cliff_lap": 28,
            "optimal_stint": "18-25"
        },
        "HARD": {
            "base_lap_time": 92.0,
            "degradation_rate": 0.05,
            "cliff_lap": 40,
            "optimal_stint": "30+"
        }
    }
}
```

#### 3. 賽道特性資料庫（Track Features Database）
```python
track_features_db = {
    "circuit": "Suzuka",
    "official_name": "Suzuka International Racing Course",
    
    # 進站資料
    "pit_loss_time": 21.5,       # 進站損失時間 (秒)
    "pit_entry_speed_limit": 80,  # km/h
    "pit_lane_length": 385,       # 公尺
    
    # 超車特性
    "overtaking_difficulty": "medium",
    "drs_zones": 2,
    "drs_advantage_per_zone": 0.3,
    "main_overtaking_points": ["Turn 1", "Spoon Curve"],
    
    # 賽道事件
    "safety_car_probability": 0.32,
    "vsc_probability": 0.45,
    "average_sc_duration": 4.5,  # 圈
    
    # 賽道特徵
    "track_length_km": 5.807,
    "track_abrasiveness": "high",
    "tire_stress_level": "very_high"
}
```

### 可選數據（Optional）

#### 4. 車隊策略歷史（Team Strategy History）
```python
team_strategy_history = {
    "Red Bull": {
        "avg_pit_stops_per_race": 1.8,
        "aggressive_undercut_rate": 0.65,
        "fuel_saving_usage": "low",
        "risk_taking_score": 7.5  # 1-10
    },
    "Ferrari": {
        "avg_pit_stops_per_race": 2.1,
        "aggressive_undercut_rate": 0.42,
        "fuel_saving_usage": "medium",
        "risk_taking_score": 5.8
    }
}
```

#### 5. 車手表現數據（Driver Performance）
```python
driver_performance = {
    "VER": {
        "tire_management_rating": 9.2,  # 1-10
        "avg_error_rate": 0.05,         # 每圈失誤機率
        "pressure_performance": 8.8,
        "overtaking_success_rate": 0.78
    },
    "LEC": {
        "tire_management_rating": 7.8,
        "avg_error_rate": 0.08,
        "pressure_performance": 7.5,
        "overtaking_success_rate": 0.72
    }
}
```

---

## 🧮 計算邏輯

### 核心算法：智能推薦引擎（根據差距自動判斷）

```python
def evaluate_catch_up_feasibility(p1_data, p2_data, race_status, track_features):
    """
    評估 P2 追趕 P1 的可行性
    
    核心邏輯：根據當前差距自動判斷並推薦最可行的策略
    
    Returns:
        {
            "feasible": bool,
            "gap_category": str,  # "極小", "中等", "大", "極大"
            "recommended_strategy": str,
            "scenarios": List[Dict],
            "success_probability": float
        }
    """
    
    # 1. 計算當前差距與剩餘時間
    current_gap = p2_data["gap_to_leader"]  # 秒
    remaining_laps = race_status["remaining_laps"]
    
    # 2. 差距分級（關鍵判斷邏輯）
    gap_category = classify_gap(current_gap)
    # "極小" (0-3s), "中等" (3-8s), "大" (8-15s), "極大" (>15s)
    # 2. 差距分級（關鍵判斷邏輯）
    gap_category = classify_gap(current_gap)
    # "極小" (0-3s), "中等" (3-8s), "大" (8-15s), "極大" (>15s)
    
    # 3. 根據差距類別篩選適用策略
    scenarios = []
    
    if gap_category == "極小":  # 0-3s
        # 極小差距：優先 DRS、輪胎優勢，避免進站
        if current_gap < 1.0:
            drs_scenario = evaluate_drs_gap_reduction(current_gap, remaining_laps, track_features)
            scenarios.append(drs_scenario)
        
        tire_scenario = evaluate_tire_strategy_delta(p1_data, p2_data, remaining_laps)
        if tire_scenario["catchable_time"] > 0:
            scenarios.append(tire_scenario)
        
        # 極小差距不推薦 Undercut（進站損失太大）
        
    elif gap_category == "中等":  # 3-8s
        # 中等差距：Undercut 最佳，配方差異次之
        pit_scenario = evaluate_pit_strategy_options(
            p1_data, p2_data, race_status, track_features["pit_loss_time"]
        )
        scenarios.append(pit_scenario)
        
        tire_scenario = evaluate_tire_strategy_delta(p1_data, p2_data, remaining_laps)
        scenarios.append(tire_scenario)
        
        # Traffic 機會作為輔助
        traffic_scenario = evaluate_traffic_opportunity(
            p1_data, p2_data, race_status, lapped_cars
        )
        if traffic_scenario["feasible"]:
            scenarios.append(traffic_scenario)
    
    elif gap_category == "大":  # 8-15s
        # 大差距：SC 機會為主，少進站次數策略輔助
        sc_scenario = evaluate_safety_car_opportunity(
            current_gap, remaining_laps, track_features
        )
        scenarios.append(sc_scenario)
        
        fewer_stops_scenario = evaluate_fewer_pit_stops(
            p1_data, p2_data, remaining_laps
        )
        if fewer_stops_scenario["feasible"]:
            scenarios.append(fewer_stops_scenario)
        
        # 大差距不推薦常規 Undercut（追不上）
    
    elif gap_category == "極大":  # >15s
        # 極大差距：僅顯示 SC 機會，其他策略不可行
        sc_scenario = evaluate_safety_car_opportunity(
            current_gap, remaining_laps, track_features
        )
        scenarios.append(sc_scenario)
        
        # 其他策略標記為不可行
        scenarios.append({
            "name": "常規策略",
            "success_probability": 0.0,
            "feasible": False,
            "message": "差距過大，建議保持當前位置"
        })
    
    # 4. 排序場景（按成功機率）
    scenarios.sort(key=lambda x: x.get("success_probability", 0), reverse=True)
    
    # 5. 選擇最佳策略
    best_scenario = scenarios[0] if scenarios else None
    feasible = best_scenario and best_scenario.get("success_probability", 0) > 0.3
    
    return {
        "feasible": feasible,
        "gap_category": gap_category,
        "current_gap": current_gap,
        "recommended_strategy": best_scenario["name"] if best_scenario else "無可行策略",
        "scenarios": scenarios,
        "success_probability": best_scenario.get("success_probability", 0) if best_scenario else 0,
        "detailed_plan": best_scenario.get("action_plan", "") if best_scenario else ""
    }
```

### 差距分級函數

```python
def classify_gap(gap: float) -> str:
    """
    根據差距分類策略適用性
    
    Args:
        gap: 當前差距（秒）
        
    Returns:
        "極小" | "中等" | "大" | "極大"
    """
    if gap < 3.0:
        return "極小"
    elif gap < 8.0:
        return "中等"
    elif gap < 15.0:
        return "大"
    else:
        return "極大"
```

### 策略可行性矩陣

```python
STRATEGY_FEASIBILITY_MATRIX = {
    "極小": {  # 0-3s
        "DRS": {"priority": 1, "min_gap": 0, "max_gap": 1.0},
        "輪胎年齡優勢": {"priority": 2, "min_gap": 0, "max_gap": 3.0},
        "Undercut": {"priority": -1, "reason": "進站損失過大"},  # 不推薦
    },
    "中等": {  # 3-8s
        "Undercut": {"priority": 1, "min_gap": 3.0, "max_gap": 8.0},
        "配方差異": {"priority": 2, "min_gap": 3.0, "max_gap": 8.0},
        "輪胎年齡優勢": {"priority": 3, "min_gap": 3.0, "max_gap": 8.0},
        "Traffic 機會": {"priority": 4, "role": "輔助"},
    },
    "大": {  # 8-15s
        "SC 機會": {"priority": 1, "min_gap": 8.0, "max_gap": 15.0},
        "少進站次數": {"priority": 2, "min_gap": 8.0, "max_gap": 15.0},
        "Undercut": {"priority": -1, "reason": "差距過大"},  # 不推薦
    },
    "極大": {  # >15s
        "SC 機會": {"priority": 1, "min_gap": 15.0, "max_gap": float('inf')},
        "所有常規策略": {"priority": -1, "reason": "差距過大，無法追上"},
    }
}
```

---
    
    # 場景 1: 輪胎策略差異
    tire_scenario = evaluate_tire_strategy_delta(p1_data, p2_data, remaining_laps)
    scenarios.append(tire_scenario)
    
    # 場景 2: 進站策略（Undercut/Overcut）
    pit_scenario = evaluate_pit_strategy_options(
        p1_data, p2_data, race_status, track_features["pit_loss_time"]
    )
    scenarios.append(pit_scenario)
    
    # 場景 3: Safety Car 機會
    sc_scenario = evaluate_safety_car_opportunity(
        current_gap, remaining_laps, track_features["safety_car_probability"]
    )
    scenarios.append(sc_scenario)
    
    # 場景 4: DRS 追趕
    drs_scenario = evaluate_drs_catch_up(
        current_gap, remaining_laps, track_features
    )
    scenarios.append(drs_scenario)
    
    # 場景 5: 油量策略
    fuel_scenario = evaluate_fuel_strategy(p1_data, p2_data, remaining_laps)
    scenarios.append(fuel_scenario)
    
    # 場景 6: 推進模式
    push_scenario = evaluate_push_mode(p1_data, p2_data, remaining_laps)
    scenarios.append(push_scenario)
    
    # 3. 排序場景（按成功機率）
    scenarios.sort(key=lambda x: x["success_probability"], reverse=True)
    
    # 4. 選擇最佳策略
    best_scenario = scenarios[0]
    feasible = best_scenario["success_probability"] > 0.3  # 30% 門檻
    
    return {
        "feasible": feasible,
        "recommended_strategy": best_scenario["name"],
        "scenarios": scenarios,
        "success_probability": best_scenario["success_probability"],
        "detailed_plan": best_scenario["action_plan"]
    }
```

### 子算法：輪胎策略差異評估

```python
def evaluate_tire_strategy_delta(p1_data, p2_data, remaining_laps):
    """
    評估基於輪胎差異的追趕策略
    
    Returns:
        {
            "name": "tire_age_delta",
            "success_probability": float,
            "catchable_time": float,
            "action_plan": str
        }
    """
    # 輪胎年齡差距
    tire_age_delta = p1_data["tire_age"] - p2_data["tire_age"]
    
    # 獲取輪胎衰退率
    p1_compound = p1_data["tire_compound"]
    p2_compound = p2_data["tire_compound"]
    
    degradation_rate_p1 = get_tire_degradation_rate(p1_compound, p1_data["tire_age"])
    degradation_rate_p2 = get_tire_degradation_rate(p2_compound, p2_data["tire_age"])
    
    # 每圈速度差距
    per_lap_delta = (
        (degradation_rate_p1 * p1_data["tire_age"]) - 
        (degradation_rate_p2 * p2_data["tire_age"])
    )
    
    # 可追回時間
    catchable_time = per_lap_delta * remaining_laps
    current_gap = p2_data["gap_to_leader"]
    
    # 成功機率計算
    if catchable_time >= current_gap + 1.0:  # 需額外 1s 超車
        success_prob = 0.85
    elif catchable_time >= current_gap:
        success_prob = 0.60
    elif catchable_time >= current_gap * 0.8:
        success_prob = 0.35
    else:
        success_prob = 0.10
    
    # 生成行動計劃
    action_plan = f"""
    ✅ 輪胎年齡優勢策略
    
    📊 當前狀況:
    - P1 輪胎年齡: {p1_data['tire_age']} 圈 ({p1_compound})
    - P2 輪胎年齡: {p2_data['tire_age']} 圈 ({p2_compound})
    - 年齡差距: {tire_age_delta} 圈
    - 當前差距: {current_gap:.2f}s
    
    🎯 預測結果:
    - 每圈可追回: {per_lap_delta:.3f}s
    - 剩餘 {remaining_laps} 圈總可追回: {catchable_time:.2f}s
    - 追上機率: {success_prob*100:.1f}%
    
    🏁 建議行動:
    - P2 全力推進，維持輪胎在性能窗口
    - 預計第 {int(current_gap / per_lap_delta) + p2_data['lap']} 圈追上 P1
    - 準備 DRS 超車
    """
    
    return {
        "name": "tire_age_delta",
        "success_probability": success_prob,
        "catchable_time": catchable_time,
    # 場景 4: DRS 縮小差距（如果在 DRS 範圍內）
    if current_gap < 1.0:
        drs_scenario = evaluate_drs_gap_reduction(
            current_gap, remaining_laps, track_features
        )
        scenarios.append(drs_scenario)
    
    # 場景 5: Traffic 機會（評估 P1 是否會遇到慢車）
    traffic_scenario = evaluate_traffic_opportunity(
        p1_data, p2_data, race_status, lapped_cars
    )
    if traffic_scenario["feasible"]:
        scenarios.append(traffic_scenario)
        {
            "name": "undercut",
            "success_probability": float,
            "optimal_p2_pit_lap": int,
            "action_plan": str
        }
    """
    current_lap = race_status["current_lap"]
    current_gap = p2_data["gap_to_leader"]
    
    # P1 預計進站圈（基於輪胎年齡）
    p1_tire_life = get_tire_optimal_stint(p1_data["tire_compound"])
    p1_expected_pit_lap = current_lap + (p1_tire_life - p1_data["tire_age"])
    
    # P2 提前進站策略
    p2_pit_lap = p1_expected_pit_lap - 3  # 提前 3 圈
    
    # 新胎優勢計算
    new_tire_advantage = 1.2  # 新胎每圈快 1.2s (vs 舊胎)
    chase_laps = p1_expected_pit_lap - p2_pit_lap
    
    # Undercut 效果
    catchable_time = new_tire_advantage * chase_laps
    
    # 計算出站後相對位置
    # P2 進站損失 pit_loss_time，但在 P1 進站時領先 catchable_time
    net_advantage = catchable_time - current_gap
    
    if net_advantage > 0:
        success_prob = min(0.90, 0.60 + net_advantage * 0.05)
    else:
        success_prob = 0.20
    
    action_plan = f"""
    🔧 Undercut 策略（提前進站）
    
    📊 當前狀況:
    - 當前差距: {current_gap:.2f}s
    - P1 預計進站圈: 第 {p1_expected_pit_lap} 圈
    - P1 輪胎年齡: {p1_data['tire_age']} 圈
    
    🎯 策略細節:
    - P2 建議進站圈: 第 {p2_pit_lap} 圈 (提前 {chase_laps} 圈)
    - 新胎優勢: {new_tire_advantage}s/lap
    - 追趕圈數: {chase_laps} 圈
    - 可追回時間: {catchable_time:.2f}s
    
    🏁 預測結果:
    - P1 進站時 P2 領先: {net_advantage:.2f}s
    - 成功機率: {success_prob*100:.1f}%
    
    ⚠️ 風險:
    - P1 可能提前進站反制
    - 需確保 P2 新胎圈速優勢
    """
    
    return {
        "name": "undercut",
        "success_probability": success_prob,
        "optimal_p2_pit_lap": p2_pit_lap,
        "action_plan": action_plan,
        "net_advantage": net_advantage
    }
```

### 綜合決策樹

```python
def recommend_optimal_strategy(evaluation_result):
    """
    根據評估結果推薦最佳策略
    
    決策邏輯:
    1. 成功機率 > 60%: 強烈推薦
    2. 成功機率 30-60%: 謹慎推薦，需評估風險
    3. 成功機率 < 30%: 不推薦，建議保守策略
    """
    best_scenario = evaluation_result["scenarios"][0]
    success_prob = best_scenario["success_probability"]
    
    if success_prob > 0.60:
        recommendation = {
            "level": "STRONG_RECOMMEND",
            "confidence": "高",
            "message": f"✅ 強烈推薦：{best_scenario['name']} 策略",
            "action": best_scenario["action_plan"]
        }
    elif success_prob > 0.30:
        recommendation = {
            "level": "CAUTIOUS_RECOMMEND",
            "confidence": "中等",
            "message": f"⚠️ 謹慎推薦：{best_scenario['name']} 策略",
            "action": best_scenario["action_plan"] + "\n\n⚠️ 建議評估替代方案"
        }
    else:
        recommendation = {
            "level": "NOT_RECOMMEND",
            "confidence": "低",
            "message": "❌ 追趕機率較低，建議保守策略",
            "action": "建議：\n- 維持當前策略\n- 等待 Safety Car 機會\n- 保住第二名位置"
        }
    
    return recommendation
```

---

## 🏗️ 技術架構

### 模組結構

```
modules/gui/strategy_advisor/
├── __init__.py
├── strategy_advisor_mdi.py          # MDI 容器（繼承 UniversalAnalysisMDI）
├── strategy_advisor_loader.py       # 數據載入器（繼承 UniversalDataLoader）
├── strategy_advisor_widget.py       # 主要 UI 組件
└── strategy_advisor_calculator.py   # 策略計算引擎
```

### 類別關係圖

```
┌─────────────────────────────────────┐
│   UniversalAnalysisMDI (Base)       │
│   - MDI 視窗管理                     │
│   - 生命週期控制                     │
└─────────────────────────────────────┘
                  ▲
                  │ 繼承
                  │
┌─────────────────────────────────────┐
│   StrategyAdvisorMDI                │
│   - 模組初始化                       │
│   - 參數配置                         │
│   - 視窗標題/大小                    │
└─────────────────────────────────────┘
                  │ 包含
                  ▼
┌─────────────────────────────────────┐
│   StrategyAdvisorLoader              │
│   (繼承 UniversalDataLoader)         │
│   - API/JSON 數據獲取                │
│   - 數據格式驗證                     │
│   - 數據轉換                         │
└─────────────────────────────────────┘
                  │ 提供數據
                  ▼
┌─────────────────────────────────────┐
│   StrategyAdvisorWidget              │
│   - 場景選擇 UI                      │
│   - 參數輸入表單                     │
│   - 結果視覺化                       │
└─────────────────────────────────────┘
                  │ 使用
                  ▼
┌─────────────────────────────────────┐
│   StrategyCalculator                 │
│   - 場景計算邏輯                     │
│   - 數學模型                         │
│   - 機率評估                         │
└─────────────────────────────────────┘
```

### 數據流

```
用戶操作 → StrategyAdvisorMDI → API/JSON 數據
                ↓
        StrategyAdvisorLoader (數據載入)
                ↓
        StrategyCalculator (策略計算)
                ↓
        StrategyAdvisorWidget (結果顯示)
                ↓
        UniversalChartWidget (圖表繪製)
```

---

## 🎨 UI 設計草稿

### 主介面佈局

```
┌─────────────────────────────────────────────────────────────┐
│  P2 → P1 策略建議分析                            [ X ]      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 當前賽況                                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  P1: VER  |  Lap 25/53  |  Tire: MED (12 laps)        │  │
│  │  P2: LEC  |  Gap: 3.5s  |  Tire: MED (8 laps)         │  │
│  │  Track: Suzuka  |  Status: GREEN  |  SC Prob: 32%     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  🎯 推薦策略                                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ✅ Undercut 策略 (成功機率: 78%)                      │  │
│  │                                                         │  │
│  │  建議行動:                                              │  │
│  │  - 第 22 圈進站（提前 P1 3 圈）                        │  │
│  │  - 換上 SOFT 配方                                      │  │
│  │  - 預計追回 4.2s                                       │  │
│  │  - 預計第 25 圈完成超越                                │  │
│  │                                                         │  │
│  │  [📊 查看詳細計算]  [🎲 模擬其他場景]                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📋 所有可行場景                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Scenario            | Success % | Catchable Time     │  │
│  │  ─────────────────────────────────────────────────────│  │
│  │  ✅ Undercut          |   78%    |   +4.2s           │  │
│  │  ⚠️  Tire Age Delta   |   52%    |   +2.8s           │  │
│  │  ⚠️  Safety Car       |   45%    |   +14s (if SC)    │  │
│  │  ❌ DRS Only          |   28%    |   +1.4s           │  │
│  │  ❌ Fuel Saving       |   15%    |   -0.8s           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📈 追趕進度模擬圖                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │    Gap (s)                                              │  │
│  │  4.0 │                                                  │  │
│  │  3.0 │     ╲                                            │  │
│  │  2.0 │       ╲                                          │  │
│  │  1.0 │         ╲                                        │  │
│  │  0.0 │___________╲____[超車點]________________________ │  │
│  │      25   26   27   28   29   30  (Lap)                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  [🔄 更新數據]  [💾 導出報告]  [❓ 幫助]                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 實現計劃

### Phase 1: 核心計算引擎（Week 1-2）
- [ ] 實現 `StrategyCalculator` 類別
- [ ] 完成輪胎策略差異計算
- [ ] 完成 Undercut/Overcut 計算
- [ ] 單元測試覆蓋率 > 80%

### Phase 2: 數據整合（Week 3）
- [ ] 創建 `StrategyAdvisorLoader`
- [ ] 整合 Live Timing API 數據源
- [ ] 讀取輪胎/賽道資料庫
- [ ] 數據驗證與錯誤處理

### Phase 3: GUI 開發（Week 4-5）
- [ ] 實現 `StrategyAdvisorWidget` UI
  - [ ] 賽況顯示區
  - [ ] 車手模式選擇下拉選單（P1/P2）
  - [ ] 最佳策略推薦卡片
  - [ ] 場景對比表格（QTableWidget）
    - [ ] 實現右鍵選單（contextMenuEvent）
    - [ ] 選單選項：顯示曲線圖、對比、導出
  - [ ] 追趕進度時間線圖（matplotlib 嵌入）
  - [ ] 機會視窗顯示（SC/Traffic）
- [ ] 實現詳細曲線圖視窗（獨立 QDialog）
  - [ ] matplotlib Figure 繪製圈數曲線
  - [ ] 關鍵事件標註（進站、SC、追上點）
  - [ ] 曲線特徵說明（進站損失、線性追趕、突變點）
  - [ ] 導出圖表功能（PNG/PDF）
- [ ] 與 `UniversalChartWidget` 整合

### Phase 4: MDI 整合（Week 6）
- [ ] 創建 `StrategyAdvisorMDI`
- [ ] 整合到 `f1t_gui_main.py`
- [ ] 選單項目與快捷鍵
- [ ] MDI 視窗管理

### Phase 5: 進階功能（Week 7-8）
- [ ] Safety Car 機率模型
- [ ] 車手表現評估
- [ ] Monte Carlo 模擬（可選）
- [ ] 策略報告導出

### Phase 6: 測試與優化（Week 9-10）
- [ ] 集成測試
- [ ] 真實賽事數據驗證
- [ ] 性能優化
- [ ] 用戶文檔撰寫

---

## 🎲 未來擴展

## 🎨 UI 設計與呈現方式

### 主介面佈局（PyQt5 MDI 視窗）

```
┌─────────────────────────────────────────────────────────────────────────┐
│  P2 追趕 P1 策略分析                                    [ _ ]  [ □ ]  [ X ] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  📊 當前賽況                                    [ P1 模式: Normal ▼]    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  P1: VER (#1)  │ Lap 25/53 │ Tire: MEDIUM (12 laps) │ 78.234s    │  │
│  │  P2: LEC (#2)  │ Gap: 3.5s │ Tire: MEDIUM (8 laps)  │ 78.567s    │  │
│  │  Track: Suzuka │ Status: GREEN │ Remaining: 28 laps               │  │
│  │                                                                     │  │
│  │  差距評估: 中等差距（3-8s）- 建議 Undercut 或配方差異策略          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                              [ P2 模式: Normal ▼]        │
│                                                                           │
│  🎯 最佳策略推薦                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ✅ Undercut 策略（提前進站）                                      │  │
│  │                                                                     │  │
│  │  📍 可追回時間: +4.2 秒                                            │  │
│  │  🏁 預計追上圈數: 第 28 圈                                         │  │
│  │  📋 執行計劃:                                                      │  │
│  │     1. 第 22 圈進站（提前 P1 3 圈）                                │  │
│  │     2. 換上 SOFT 配方（或保持 MEDIUM）                            │  │
│  │     3. 出站後全力推進，利用新胎優勢追趕                            │  │
│  │     4. P1 第 25 圈進站時，P2 將領先 0.7s                          │  │
│  │                                                                     │  │
│  │  ⚠️  關鍵風險: P1 可能提前進站反制                                │  │
│  │                                                                     │  │
│  │  [ 📊 詳細計算 ]  [ 🔄 重新計算 ]  [ 💾 導出報告 ]              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  📋 所有可行場景對比（右鍵點選查看詳細曲線圖）                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 場景                   │ 可追回時間 │ 預計追上圈數 │ 可行性        │  │
│  │ ──────────────────────┼───────────┼─────────────┼──────────────│  │
│  │ ✅ Undercut (提前進站)  │   +4.2s   │   第 28 圈   │ 強烈推薦     │◄ 右鍵
│  │ ⚠️  輪胎年齡優勢        │   +2.8s   │   第 35 圈   │ 可行         │  │
│  │ 💡 SC 機會（假設出現）  │  +14.0s   │   第 26 圈   │ 最佳機會     │  │
│  │ ⚠️  DRS 輔助（<1s 內）  │   +1.4s   │   第 30 圈   │ 輔助手段     │  │
│  │ 💡 Traffic（P1 遇慢車） │   +1.2s   │   第 32 圈   │ 短期機會     │  │
│  │ ❌ Overcut (延後進站)   │   -0.5s   │     N/A     │ 不可行       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  右鍵選單:                                                               │
│    → 顯示詳細圈數曲線圖（matplotlib）                                   │
│    → 導出該場景報告（CSV）                                               │
│    → 與其他場景對比                                                     │
│                                                                           │
│  📈 追趕進度時間線                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Gap (s)                                                            │  │
│  │   4.0 │                                                             │  │
│  │       │  ●───────────────────────────────────────                  │  │
│  │   3.0 │      ╲ 當前                                                │  │
│  │       │       ╲                                                     │  │
│  │   2.0 │        ╲                                                    │  │
│  │       │         ╲ [P2 進站 Lap 22]                                 │  │
│  │   1.0 │          ╲                                                  │  │
---

## 💻 技術實現細節

### 右鍵選單實現（QTableWidget）

```python
class ScenarioComparisonTable(QTableWidget):
    """場景對比表格，支援右鍵選單"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.scenario_data = {}  # 儲存每個場景的詳細數據
        
    def _show_context_menu(self, position):
        """顯示右鍵選單"""
        selected_row = self.rowAt(position.y())
        if selected_row < 0:
            return
            
        menu = QMenu(self)
        
        # 選單選項
        action_show_chart = menu.addAction(self.tr("顯示詳細圈數曲線圖"))
        action_compare = menu.addAction(self.tr("與其他場景對比"))
        menu.addSeparator()
        action_export_csv = menu.addAction(self.tr("導出該場景報告 (CSV)"))
        action_detail = menu.addAction(self.tr("查看計算細節"))
        
        # 執行選單
        action = menu.exec_(self.mapToGlobal(position))
        
        if action == action_show_chart:
            self._show_lap_chart(selected_row)
        elif action == action_compare:
            self._compare_scenarios(selected_row)
        elif action == action_export_csv:
            self._export_scenario_csv(selected_row)
        elif action == action_detail:
            self._show_calculation_detail(selected_row)
    
    def _show_lap_chart(self, row: int):
        """顯示詳細圈數曲線圖"""
        scenario_name = self.item(row, 0).text()
        scenario_data = self.scenario_data.get(scenario_name)
        
        if not scenario_data:
            return
            
        # 創建詳細曲線圖視窗
        chart_dialog = LapChartDialog(scenario_name, scenario_data, self)
        chart_dialog.exec_()
```

---

### 詳細曲線圖視窗實現（matplotlib）

```python
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class LapChartDialog(QDialog):
    """詳細圈數曲線圖視窗"""
    
    def __init__(self, scenario_name: str, scenario_data: dict, parent=None):
        super().__init__(parent)
        self.scenario_name = scenario_name
        self.scenario_data = scenario_data
        
        self.setWindowTitle(f"{scenario_name} - 詳細圈數曲線圖")
        self.resize(1200, 800)
        
        self._setup_ui()
        self._plot_lap_chart()
    
    def _setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        
        # matplotlib Figure
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 按鈕區
        button_layout = QHBoxLayout()
        
        btn_export = QPushButton(self.tr("導出圖表"))
        btn_export.clicked.connect(self._export_chart)
        
        btn_resimulate = QPushButton(self.tr("重新模擬"))
        btn_resimulate.clicked.connect(self._resimulate)
        
        btn_close = QPushButton(self.tr("關閉"))
        btn_close.clicked.connect(self.close)
        
        button_layout.addWidget(btn_export)
        button_layout.addWidget(btn_resimulate)
        button_layout.addStretch()
        button_layout.addWidget(btn_close)
        
        layout.addLayout(button_layout)
    
    def _plot_lap_chart(self):
        """繪製圈數曲線圖"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 根據場景類型繪製不同曲線
        if "Undercut" in self.scenario_name:
            self._plot_undercut_curve(ax)
        elif "輪胎年齡優勢" in self.scenario_name:
            self._plot_tire_age_curve(ax)
        elif "SC" in self.scenario_name or "Safety Car" in self.scenario_name:
            self._plot_sc_curve(ax)
        
        self.canvas.draw()
    
    def _plot_undercut_curve(self, ax):
        """繪製 Undercut 策略曲線（進站損失 + 追趕）"""
        laps = self.scenario_data["laps"]
        gaps = self.scenario_data["gaps"]
        
        # 找出關鍵點
        p2_pit_lap = self.scenario_data["p2_pit_lap"]
        p1_pit_lap = self.scenario_data["p1_pit_lap"]
        
        # 繪製曲線
        ax.plot(laps, gaps, 'b-', linewidth=2, label='差距變化')
        
        # 標註關鍵事件
        # P2 進站點（差距突然增加）
        p2_pit_idx = laps.index(p2_pit_lap)
        ax.plot(p2_pit_lap, gaps[p2_pit_idx], 'ro', markersize=10, 
                label=f'P2 進站 (Lap {p2_pit_lap})')
        ax.annotate(f'進站損失\n+22s', 
                    xy=(p2_pit_lap, gaps[p2_pit_idx]),
                    xytext=(p2_pit_lap - 1, gaps[p2_pit_idx] + 5),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, color='red')
        
        # P1 進站點（P2 開始領先）
        p1_pit_idx = laps.index(p1_pit_lap)
        ax.plot(p1_pit_lap, gaps[p1_pit_idx], 'go', markersize=10,
                label=f'P1 進站 (Lap {p1_pit_lap})')
        ax.annotate(f'P2 領先\n{abs(gaps[p1_pit_idx]):.1f}s',
                    xy=(p1_pit_lap, gaps[p1_pit_idx]),
                    xytext=(p1_pit_lap + 1, gaps[p1_pit_idx] - 5),
                    arrowprops=dict(arrowstyle='->', color='green'),
                    fontsize=10, color='green')
        
        # 追趕階段標註
        chase_start = p2_pit_idx + 1
        chase_end = p1_pit_idx
        ax.fill_between(laps[chase_start:chase_end], 
                        gaps[chase_start:chase_end], 
                        alpha=0.2, color='blue', label='新胎追趕階段')
        
        # 設置圖表
        ax.set_xlabel('Lap Number', fontsize=12)
        ax.set_ylabel('Gap to P1 (seconds)', fontsize=12)
        ax.set_title(f'{self.scenario_name} - 圈數曲線圖', fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        
    def _plot_tire_age_curve(self, ax):
        """繪製輪胎年齡優勢策略曲線（線性追趕）"""
        laps = self.scenario_data["laps"]
        gaps = self.scenario_data["gaps"]
        
        # 繪製線性曲線
        ax.plot(laps, gaps, 'b-', linewidth=2, label='差距變化')
        
        # 標註 DRS 範圍
        drs_lap = None
        for i, gap in enumerate(gaps):
            if gap < 1.0:
                drs_lap = laps[i]
                break
        
        if drs_lap:
            drs_idx = laps.index(drs_lap)
            ax.axvspan(drs_lap, laps[-1], alpha=0.2, color='yellow', 
                      label='DRS 範圍')
            ax.annotate('進入 DRS 範圍',
                       xy=(drs_lap, gaps[drs_idx]),
                       xytext=(drs_lap - 2, gaps[drs_idx] + 0.5),
                       arrowprops=dict(arrowstyle='->', color='orange'),
                       fontsize=10, color='orange')
        
        # 追上點
        catch_lap = laps[-1]
        ax.plot(catch_lap, 0, 'go', markersize=12, label=f'追上 (Lap {catch_lap})')
        
        # 設置圖表
        ax.set_xlabel('Lap Number', fontsize=12)
        ax.set_ylabel('Gap to P1 (seconds)', fontsize=12)
        ax.set_title(f'{self.scenario_name} - 圈數曲線圖', fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
    
    def _plot_sc_curve(self, ax):
        """繪製 SC 機會策略曲線（等待 + 突變）"""
        laps = self.scenario_data["laps"]
        gaps = self.scenario_data["gaps"]
        sc_lap = self.scenario_data["sc_lap"]
        
        # 繪製曲線
        ax.plot(laps, gaps, 'b-', linewidth=2, label='差距變化')
        
        # 標註 SC 出現點（差距突然減少）
        sc_idx = laps.index(sc_lap)
        ax.plot(sc_lap, gaps[sc_idx], 'ro', markersize=12, label=f'SC 出現 (Lap {sc_lap})')
        ax.annotate('SC 進站\n節省 14s',
                   xy=(sc_lap, gaps[sc_idx]),
                   xytext=(sc_lap - 2, gaps[sc_idx] + 5),
                   arrowprops=dict(arrowstyle='->', color='red'),
                   fontsize=10, color='red')
        
        # 等待階段
        ax.axvspan(laps[0], sc_lap, alpha=0.1, color='gray', label='等待 SC 階段')
        
        # SC 重啟後快速追趕
        ax.axvspan(sc_lap, laps[-1], alpha=0.2, color='green', label='SC 重啟追趕')
        
        # 設置圖表
        ax.set_xlabel('Lap Number', fontsize=12)
        ax.set_ylabel('Gap to P1 (seconds)', fontsize=12)
        ax.set_title(f'{self.scenario_name} - 圈數曲線圖', fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='k', linestyle='--', linewidth=1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
    
    def _export_chart(self):
        """導出圖表"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("導出圖表"),
            f"{self.scenario_name}_lap_chart.png",
            "PNG Files (*.png);;PDF Files (*.pdf)"
        )
        
        if file_path:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
    
    def _resimulate(self):
        """重新模擬（重新繪製圖表）"""
        self._plot_lap_chart()
```

---

### 數據結構（場景數據格式）

```python
# Undercut 策略數據範例
undercut_data = {
    "name": "Undercut 策略",
    "laps": [22, 23, 24, 25, 26, 27, 28],  # 圈數
    "gaps": [3.5, 25.5, 24.3, 23.0, -0.7, -2.0, -3.5],  # 差距（秒）
    "p2_pit_lap": 22,  # P2 進站圈
    "p1_pit_lap": 25,  # P1 進站圈
    "pit_loss": 22.0,  # 進站損失時間
    "new_tire_advantage": 1.2,  # 新胎優勢（每圈）
    "catchable_time": 4.2,  # 可追回時間
    "catch_lap": 28,  # 預計追上圈數
    "key_events": [
        {"lap": 22, "event": "P2 進站", "gap_change": +22.0},
        {"lap": 23, "event": "新胎追趕開始", "gap_change": -1.2},
        {"lap": 25, "event": "P1 進站，P2 領先", "gap_change": -23.7},
    ]
}

# 輪胎年齡優勢策略數據範例
tire_age_data = {
    "name": "輪胎年齡優勢策略",
    "laps": list(range(25, 36)),  # Lap 25-35
    "gaps": [3.5, 3.35, 3.2, 3.05, 2.9, 2.75, 2.6, 2.45, 2.3, 2.15, 0.0],
    "per_lap_delta": 0.15,  # 每圈縮小差距
    "drs_lap": 32,  # 進入 DRS 範圍的圈數
    "catch_lap": 35,  # 預計追上圈數
    "key_events": [
        {"lap": 32, "event": "進入 DRS 範圍", "gap_change": 0},
        {"lap": 35, "event": "追上 P1", "gap_change": 0},
    ]
}

# SC 機會策略數據範例
sc_data = {
    "name": "Safety Car 機會策略",
    "laps": list(range(25, 33)),  # Lap 25-32
    "gaps": [4.2, 4.2, 4.2, 12.2, 10.7, 8.9, 6.9, 0.0],
    "sc_lap": 28,  # SC 出現圈
    "sc_pit_loss": 8.0,  # SC 期間進站損失
    "normal_pit_loss": 22.0,  # 正常進站損失
    "saved_time": 14.0,  # 節省時間
    "catch_lap": 32,  # 預計追上圈數
    "key_events": [
        {"lap": 28, "event": "SC 出現，P2 進站", "gap_change": +8.0},
        {"lap": 29, "event": "SC 重啟，新胎追趕", "gap_change": -1.5},
        {"lap": 32, "event": "追上 P1", "gap_change": -6.9},
    ]
}
```

---

## 🎬 Demo 場景示範（ASCII 視覺化）

### Phase 1: 核心計算引擎（Week 1-2）
- [ ] 實現 `StrategyCalculator` 類別
- [ ] 完成輪胎策略差異計算（含車手模式調整）
- [ ] 完成 Undercut/Overcut 計算
- [ ] 完成 Traffic 機會評估（P1 何時遇慢車）
- [ ] 單元測試覆蓋率 > 80%

### Phase 2: 數據整合（Week 3）
- [ ] 創建 `StrategyAdvisorLoader`
- [ ] 整合 Live Timing API 數據源
- [ ] 讀取輪胎/賽道資料庫
- [ ] 獲取慢車位置數據（Lapped Cars）
- [ ] 數據驗證與錯誤處理

### Phase 3: GUI 開發（Week 4-5）
- [ ] 實現 `StrategyAdvisorWidget` UI
  - [ ] 賽況顯示區
  - [ ] 車手模式選擇下拉選單（P1/P2）
  - [ ] 最佳策略推薦卡片
  - [ ] 場景對比表格
  - [ ] 追趕進度時間線圖（ASCII 或 matplotlib）
  - [ ] 機會視窗顯示（SC/Traffic）
- [ ] 與 `UniversalChartWidget` 整合

### Phase 4: MDI 整合（Week 6）
- [ ] 創建 `StrategyAdvisorMDI`
- [ ] 整合到 `f1t_gui_main.py`
- [ ] 選單項目與快捷鍵
- [ ] MDI 視窗管理

### Phase 5: 進階功能（Week 7-8）
- [ ] DRS 縮小差距計算
- [ ] Traffic 機會視覺化（賽道地圖）
- [ ] 策略報告導出（CSV/PDF）
- [ ] 歷史策略回顧功能

### Phase 6: 測試與優化（Week 9-10）
- [ ] 集成測試（使用真實 Live Timing 數據）
- [ ] 真實賽事數據驗證（2024/2025 賽季）
- [ ] Demo 場景測試（Undercut/SC/Traffic）
- [ ] 性能優化
- [ ] 用戶文檔撰寫───────────┼──────────────┼─────────────
Lap 22  │  領先        │  進站        │  +25.5s
Lap 23  │  78.5s       │  77.3s       │  +24.3s (-1.2s)
Lap 24  │  78.7s       │  77.4s       │  +23.0s (-1.3s)

視覺化:
─────────────────────────────────────────────────────────
Lap 23: P1 ──●────────────────────────────────────────●── P2
           差距: 24.3s
           
Lap 24: P1 ──●──────────────────────────────────●── P2
           差距: 23.0s (P2 快速追近)
─────────────────────────────────────────────────────────
```

**P1 第 25 圈進站**
```
動作:
─────────────────────────────────────────────────────────
         P1 (VER) ────[PIT]──→         進站 22s
                       
         P2 (LEC) ──●───────────────→  繼續跑（新胎）
─────────────────────────────────────────────────────────

關鍵時刻:
P1 進站損失: 22s
P2 在 P1 進站時已縮小差距: 25.5s → 21.7s
P1 出站後實際差距: 21.7s - 22s = -0.3s

結果: ✅ P2 領先 0.3s！Undercut 成功！
```

**最終位置（第 25 圈出站後）**
```
─────────────────────────────────────────────────────────
         P2 (LEC) ──●                   [新 P1]
                      ────→ 0.3s 領先
         P1 (VER) ─────●                [新 P2]
─────────────────────────────────────────────────────────

策略結果:
✅ Undercut 成功
✅ P2 通過提前 3 圈進站完成位置交換
✅ 領先優勢: 0.3s
```

---

### Demo 2: Safety Car 機會場景

**第 28 圈：SC 出現**
```
初始狀態:
─────────────────────────────────────────────────────────
         P1 (VER) ──●        Gap: 4.2s    Tire: MED (18 laps)
                      ────→
         P2 (LEC) ──────●                 Tire: MED (15 laps)
─────────────────────────────────────────────────────────

事件: 🚨 SAFETY CAR DEPLOYED (Lap 28)
原因: Turn 7 事故（SAR 撞牆）
```

**SC 期間：P2 進站決策**
---

## 📌 關鍵設計決策摘要

根據用戶反饋，最終設計決策：

1. **DRS 處理**：✅ 保留 DRS 縮小差距計算，不預測超車成功率
2. **Traffic 處理**：✅ 保留，但先評估 P1 是否能追上慢車
3. **推進模式**：✅ 預設簡化版，允許用戶切換 P1/P2 模式（Normal/Attack/Management）
4. **SC 機會**：✅ 顯示「假設 SC 出現可節省幾秒」，不計算機率
5. **輸出內容**：✅ 可追回時間、建議、追上圈數（不含超車成功率）

**移除的場景**：
- ❌ 場景 5: 油量策略（無法獲取數據）
- ❌ 場景 6: 車手表現與失誤（不可控因素）

---

**最後更新**: 2025-12-08  
**版本**: v2.0  
**狀態**: 設計確認完成 → 準備進入開發階段
P1 (VER) │──●─ 跟隨 SC（不進站）Tire: MED (18 laps)
         │
P2 (LEC) │────[PIT]─→ SC 期間進站！
         └─ 進站損失: 8s（vs 正常 22s）
            換上 SOFT 胎
─────────────────────────────────────────────────────────

時間計算:
正常進站損失: 22s
SC 期間損失:   8s
節省時間:     14s

原本差距: 4.2s
進站後差距: 4.2s + 8s = 12.2s
但 P1 沒進站，輪胎劣勢增加

SC 結束後:
P2 新 SOFT 胎 vs P1 舊 MED 胎 (18 laps)
每圈優勢: 1.5s
```

**SC 重啟後：追趕階段**
```
圈數    │ P1 (舊 MED)  │ P2 (新 SOFT) │ 差距變化
────────┼──────────────┼──────────────┼─────────────
Lap 31  │ SC 重啟      │ SC 重啟      │  12.2s
Lap 32  │  78.8s       │  77.3s       │  10.7s (-1.5s)
Lap 33  │  79.2s       │  77.4s       │   8.9s (-1.8s)
Lap 34  │  79.5s       │  77.5s       │   6.9s (-2.0s)
Lap 35  │  79.8s       │  77.6s       │   4.7s (-2.2s)
Lap 36  │  80.1s       │  77.7s       │   2.5s (-2.2s)
Lap 37  │  80.4s       │  77.8s       │   0.1s (-2.4s)

視覺化:
─────────────────────────────────────────────────────────
Lap 31: P1 ──●────────────────────────────────────────────────●── P2
           差距: 12.2s
           
Lap 34: P1 ──●────────────────────────────●── P2
           差距: 6.9s (快速縮小)
           
Lap 37: P1 ──●●── P2  (0.1s！)
           DRS 範圍內！
─────────────────────────────────────────────────────────

結果: ✅ P2 在第 37 圈追上 P1（SC 重啟後 6 圈）
     ✅ 進入 DRS 範圍，準備超車
     💡 SC 機會是最佳追趕窗口！
```

---

### Demo 3: Traffic 機會場景

**第 29 圈：P1 接近慢車**
```
賽道狀況:
─────────────────────────────────────────────────────────
         慢車 LAT (#20) ──●         (即將被套圈)
                            │
         P1 (VER) ─────────────●   Gap: 5.2s
                                  ────→
         P2 (LEC) ────────────────────●
─────────────────────────────────────────────────────────

計算:
P1 與 LAT 距離: 800m
P1 速度: 250 km/h → 每秒 69.4m
追上時間: 800m / 69.4m/s ≈ 11.5s
→ P1 將在第 29 圈追上 LAT
```

**P1 遇到 LAT（第 29 圈）**
```
場景:
─────────────────────────────────────────────────────────
Turn 12 ──→ Turn 13 ──→ Turn 14 (主要超車點)
            │
P1 (VER) ─────●─ 接近 LAT，需要超車
            │     
LAT (#20) ─●─ 防守線不佳，P1 需要等待時機
            │
            └─ P1 損失時間: 1.2s
─────────────────────────────────────────────────────────

時間變化:
原本差距: 5.2s
P1 遇 LAT 損失: 1.2s
P2 清空賽道: 無損失
新差距: 5.2s - 1.2s = 4.0s

視覺化:
Lap 28: P1 ──●────────────────────────────●── P2 (5.2s)
                                            
Lap 29: P1 ──●──[遇 LAT 減速]──────────●── P2 (4.0s)
            └─ 損失 1.2s

結果: ✅ P2 利用 Traffic 機會縮小差距 1.2s
     ⚠️  短期機會，效果有限
     💡 需結合其他策略才能追上
```

---

## 📝 實現計劃 │              ╲                                              │  │
│  │  -1.0 │               ╲ P2 領先                                    │  │
│  │       └─┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴─             │  │
│  │        22 23 24 25 26 27 28 29 30 31 32 33 34 35 36  (Lap)        │  │
│  │                                                                     │  │
│  │  圖例: ● 關鍵節點  ╲ 差距變化  🛞 進站  🏁 追上                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  💡 機會視窗                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  🚨 Safety Car 機會                                                │  │
│  │     如果 SC 出現，P2 進站可節省 14s（vs 正常進站 22s）              │  │
│  │     SC 重啟後 P2 優勢: 14s + 新胎優勢 = 總可追回 16.5s             │  │
│  │     → 預計 SC 重啟後 2-3 圈內追上 P1                               │  │
│  │                                                                     │  │
│  │  🚦 Traffic 機會                                                   │  │
│  │     P1 預計第 27 圈遇到 LAT (#20，慢車）                           │  │
│  │     預期損失: 1.2s                                                 │  │
│  │     → P2 可利用此機會縮小差距至 2.3s                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  [ 🔄 更新數據 ]  [ ⚙️  進階設定 ]  [ 💾 導出 CSV ]  [ ❓ 說明 ]      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 差距分級視覺化顯示

**根據當前差距，系統自動調整推薦策略**

#### 情境 1：極小差距（0-3s）示範

```
差距評估: 極小差距（0-3s）- 建議 DRS 或輪胎優勢策略
警告: 不建議進站（進站損失 22s 會丟失所有優勢）

推薦策略:
✅ 輪胎年齡優勢策略（成功機率 85%）
⚠️  DRS 輔助（需先縮小至 1s 內）
❌ Undercut（進站損失過大，不可行）
```

#### 情境 2：中等差距（3-8s）示範

```
差距評估: 中等差距（3-8s）- Undercut 或配方差異策略最佳
機會: 進站時機視窗開啟

推薦策略:
✅ Undercut 策略（成功機率 78%）
⚠️  配方差異 SOFT（成功機率 62%）
⚠️  輪胎年齡優勢（較慢但穩定）
💡 Traffic 機會（輔助策略）
```

#### 情境 3：大差距（8-15s）示範

```
差距評估: 大差距（8-15s）- 僅 SC 機會或特殊策略可行
警告: 常規策略無法追上

推薦策略:
💡 SC 機會策略（唯一可行，成功機率 45%）
⚠️  少進站一次（不足以追上）
❌ 常規 Undercut（差距太大）
```

#### 情境 4：極大差距（>15s）示範

```
差距評估: 極大差距（>15s）- 無實際可行策略
建議: 保持 P2 位置，管理輪胎確保完賽

分析結果:
❌ 所有常規策略不可行
💡 唯一機會: SC + P1 失誤 + Traffic（機率極低 <5%）
建議行動: 接受現實，專注於完賽積分
```

---

### 右鍵選單 → 詳細圈數曲線圖視窗

**觸發方式**：在「場景對比表」中的任一場景上右鍵點選

**選單選項**：
```
┌────────────────────────────────┐
│ 顯示詳細圈數曲線圖             │
│ 與其他場景對比                 │
│ 導出該場景報告 (CSV)           │
│ 查看計算細節                   │
└────────────────────────────────┘
```

---

#### 詳細曲線圖範例 1: Undercut 策略

**關鍵理解：Undercut 會先有進站損失（差距突然增加），然後才開始追趕**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Undercut 策略 - 詳細圈數曲線圖                         [ _ ]  [ □ ]  [ X ] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Gap to P1 (seconds)                                                     │
│   30 │                                                                   │
│      │                                                                   │
│   25 │      ●────────────────────────────────────────                   │
│      │      ↑進站損失階段                                               │
│   20 │      │(+22s)                                                     │
│      │      │                                                           │
│   15 │      │                                                           │
│      │      ▼                                                           │
│   10 │      ●                                                           │
│      │       ╲                                                          │
│    5 │        ╲ 新胎追趕階段                                            │
│      │         ╲ (每圈 -1.2s)                                           │
│    0 │          ╲╲╲╲╲╲╲╲                                                │
│      │               ● P1 進站 (Lap 25)                                 │
│   -5 │                ────────────────────                              │
│      │                P2 領先 0.7s                                       │
│      └─┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴─                  │
│       22 23 24 25 26 27 28 29 30 31 32 33 34 35 36  (Lap Number)       │
│                                                                           │
│  關鍵事件標註:                                                           │
│  Lap 22: P2 進站 → 差距從 3.5s 增加至 25.5s（進站損失 22s）             │
│  Lap 23-24: P2 新胎追趕 → 每圈縮小 1.2s                                 │
│  Lap 25: P1 進站 → P2 領先 0.7s（Undercut 成功）                        │
│  Lap 28: 預計追上圈數（如果 P1 未反制）                                 │
│                                                                           │
│  策略摘要:                                                               │
│  - 可追回時間: +4.2s                                                     │
│  - 成功關鍵: P2 必須在 Lap 22 進站（提前 P1 3 圈）                      │
│  - 風險因素: P1 可能提前進站反制                                         │
│                                                                           │
│  曲線特徵:                                                               │
│  1. 突然上升: Lap 22 進站時，差距從 3.5s 暴增至 25.5s (+22s)            │
│  2. 斜線下降: Lap 23-24，P2 用新胎追趕，每圈縮小 1.2s                   │
│  3. 突然反轉: Lap 25，P1 進站時，P2 從落後變領先 (-0.7s)                │
│                                                                           │
│  [ 導出圖表 ]  [ 重新模擬 ]  [ 關閉 ]                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

#### 詳細曲線圖範例 2: 輪胎年齡優勢策略

**與 Undercut 不同：無進站變化，穩定線性追趕**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  輪胎年齡優勢策略 - 詳細圈數曲線圖                      [ _ ]  [ □ ]  [ X ] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Gap to P1 (seconds)                                                     │
│  4.0 │  ●───────────────────────────────────────────                    │
│      │   ╲                                                               │
│  3.5 │    ╲                                                              │
│      │     ╲ 線性追趕階段                                                │
│  3.0 │      ╲ (每圈 -0.15s)                                              │
│      │       ╲ 無突變，穩定縮小                                          │
│  2.5 │        ╲                                                          │
│      │         ╲                                                         │
│  2.0 │          ╲                                                        │
│      │           ╲                                                       │
│  1.5 │            ╲                                                      │
│      │             ╲                                                     │
│  1.0 │              ╲ DRS 範圍                                           │
│      │               ╲                                                   │
│  0.5 │                ╲                                                  │
│      │                 ╲                                                 │
│  0.0 │                  ●───────────────────────────                    │
│      │                  追上（Lap 35）                                   │
│      └─┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴─                  │
│       25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 (Lap Number)     │
│                                                                           │
│  關鍵事件標註:                                                           │
│  Lap 25-34: 穩定追趕階段 → 每圈縮小 0.15s（無進站變化）                 │
│  Lap 32: 進入 DRS 範圍（<1s）→ 加速縮小差距                             │
│  Lap 35: 預計追上 P1                                                     │
│                                                                           │
│  策略摘要:                                                               │
│  - 可追回時間: +2.8s                                                     │
│  - 成功關鍵: P2 輪胎年齡優勢（P2: 8 圈 vs P1: 12 圈）                   │
│  - 特點: 無進站風險，線性追趕，較穩定                                    │
│                                                                           │
│  曲線特徵:                                                               │
│  1. 平滑斜線: 無進站突變，純粹靠輪胎優勢每圈縮小 0.15s                  │
│  2. 斜率不變: 線性追趕，無策略變化                                       │
│  3. DRS 加速: 接近 1s 時進入 DRS 範圍，追趕加速                          │
│                                                                           │
│  [ 導出圖表 ]  [ 重新模擬 ]  [ 關閉 ]                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

#### 詳細曲線圖範例 3: SC 機會策略

**先等待維持差距，SC 出現後突然獲得巨大優勢**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Safety Car 機會策略 - 詳細圈數曲線圖                   [ _ ]  [ □ ]  [ X ] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Gap to P1 (seconds)                                                     │
│   15 │  ●───────────────────────────────────────────                    │
│      │  │等待階段                                                       │
│   10 │  │維持差距                                                       │
│      │  │                                                               │
│    5 │  │                                                               │
│      │  │                                                               │
│    0 │  │        SC 出現                                                │
│      │  │        ↓                                                      │
│   -5 │  │        ●────────────────────                                  │
│      │  │         ╲╲╲╲╲╲                                                │
│  -10 │  │               ╲ SC 重啟，快速追趕                              │
│      │  │                ╲ (每圈 -2.2s)                                 │
│  -15 │  │                 ●────────────────                             │
│      │  │                 P2 領先 18s                                    │
│  -20 │  │                                                               │
│      └─┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴─                  │
│       25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 (Lap Number)     │
│                                                                           │
│  關鍵事件標註:                                                           │
│  Lap 25-27: 等待 SC 階段 → 維持差距 4.2s                                │
│  Lap 28: SC 出現，P2 進站（損失 8s vs 正常 22s，節省 14s）              │
│  Lap 28: P1 未進站 → 繼續使用舊胎（18 圈）                              │
│  Lap 29-31: SC 重啟，P2 新胎 vs P1 舊胎 → 每圈縮小 2.2s                 │
│  Lap 31: P2 領先 18s（SC 機會成功）                                      │
│                                                                           │
│  策略摘要:                                                               │
│  - 可追回時間: +14.0s（SC 進站節省時間）                                 │
│  - 成功關鍵: SC 必須在 P2 需要進站時出現                                 │
│  - 注意: 這是「機會場景」，無法主動觸發                                  │
│                                                                           │
│  曲線特徵:                                                               │
│  1. 平坦水平線: Lap 25-27，等待 SC，差距維持 4.2s                        │
│  2. 突然下跳: Lap 28，SC 出現時 P2 進站，獲得節省時間優勢                │
│  3. 陡峭下降: SC 重啟後，P2 新胎 vs P1 舊胎，每圈縮小 2.2s（最快）      │
│                                                                           │
│  [ 導出圖表 ]  [ 重新模擬 ]  [ 關閉 ]                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 車手模式選擇下拉選單

```
P1 模式下拉選單:
┌────────────────────────────┐
│ ● Normal（正常）           │  ← 預設
│   Tire Management（管理）  │  → P1 每圈慢 0.15s
│   Attack（攻擊）           │  → P1 每圈快 0.10s
└────────────────────────────┘

P2 模式下拉選單:
┌────────────────────────────┐
│ ● Normal（正常）           │  ← 預設
│   Attack（攻擊）           │  → P2 每圈快 0.10s，輪胎壽命 -3 圈
│   Tire Management（管理）  │  → P2 每圈慢 0.15s
└────────────────────────────┘
```
### 文檔
- `docs/develop_task/LIVE_RACE_INSIGHTS_ROADMAP.md` - Live Race Insights 路線圖
- `docs/develop_task/OVERTAKE_PREDICTION_LLM_SYSTEM.md` - 超車預測系統

---

## ✅ Demo 驗證結果（2025-12-08）

### Demo 1: FastF1 數據驗證

**檔案**: `demo_p2_to_p1_strategy.py`

**測試結果**:
```
✅ FastF1 數據載入成功（2024 Japan GP, VER vs PER）
✅ Gap Classification 正確（0.74s → 極小差距）
✅ 推薦引擎正確過濾（僅推薦輪胎優勢策略）
✅ 計算邏輯正確（0.320s/lap, 預計第 32 圈追上）
```

---

### Demo 2: Live Timing PKL 數據驗證 ⭐

**檔案**: `demo_p2_to_p1_strategy_livetiming.py`

**數據源**: `data/live_timing_cache/2025/Abu_Dhabi_Race.pkl`

**PKL 數據結構**:
```python
{
    'version': '2.0',
    'snapshots': [20943 個快照],
    'race_info': {
        'year': 2025,
        'race': 'Abu Dhabi',
        'total_laps': 58
    },
    'driver_stints': {  # 輪胎 Stint 資訊
        '1': [
            {'lap_start': 1, 'lap_end': 30, 'compound': 'MEDIUM', ...}
        ]
    },
    'snapshots[i]': {
        'current_lap': 30,
        'race_time_seconds': 6189.6,
        'drivers': {
            '81': {  # Piastri
                'driver_tla': 'PIA',
                'driver_name': 'O PIASTRI',
                'team_name': 'McLaren',
                'position': 1,
                'gap_to_leader': 0.0,
                'last_lap_time': '1:29.119',
                'best_lap_time': '1:28.927'
            },
            '1': {  # Verstappen
                'driver_tla': 'VER',
                'position': 2,
                'gap_to_leader': 13.96,
                'last_lap_time': '1:28.003'
            }
        }
    }
}
```

**測試結果**:
```
✅ PKL 載入成功（20943 個快照）
✅ 位置資料提取成功（PIA P1, VER P2）
✅ 輪胎資訊提取成功（從 driver_stints）
✅ 差距計算正確（13.96s → 大差距）
✅ 推薦引擎正確（僅推薦 SC 機會策略）
✅ 完整資訊顯示（車手/車隊/圈速）
```

**關鍵發現**:
1. **輪胎資訊**: 不在 snapshot 中，需從 `driver_stints` 交叉比對
2. **時間格式**: 同時提供 `race_time` (字串) 和 `race_time_seconds` (浮點數)
3. **差距計算**: 使用 `gap_to_leader` 欄位直接計算 P2 與 P1 差距
4. **圈速資訊**: 提供 `last_lap_time` 和 `best_lap_time`

---

## 📊 數據源整合策略

### 雙重數據源架構

| 數據源 | 使用場景 | 優點 | 缺點 |
|--------|---------|------|------|
| **FastF1 API** | 歷史賽事完整分析 | 完整遙測數據、豐富計算功能 | 載入較慢、無即時模式 |
| **Live Timing PKL** | 即時模式、快速分析 | 極快載入（20K+ 快照）、即時更新 | 無原始遙測、需手動計算 |

### 數據載入器設計

**基礎類別**: `UniversalDataLoader`（繼承既有架構）

**新增方法**:
```python
def _load_position_data_from_pkl(self, pkl_path: str, target_lap: int) -> Dict:
    """從 Live Timing PKL 載入位置資料"""
    
def _load_position_data_from_fastf1(self, year, race, session, lap) -> Dict:
    """從 FastF1 載入位置資料"""
    
def _extract_tire_info_from_stints(self, driver_stints: Dict, driver_num: str, lap: int) -> Dict:
    """從 driver_stints 提取輪胎資訊"""
```

---

## ✅ 檢查清單（開發前必讀）

- [x] ✅ 用 `semantic_search` 搜索類似功能
- [x] ✅ 用 `file_search` 檢查 `modules/gui/` 資料夾
- [x] ✅ 用 `grep_search` 驗證要調用的方法存在
- [x] ✅ 閱讀 `rain_analysis` 作為架構範本
- [x] ✅ 確認使用 `UniversalDataLoader` 和 `UniversalChartWidget`
- [x] ✅ Demo 驗證完成（FastF1 + Live Timing PKL）
- [x] ❌ 無任何假設性編碼或憑空想像的方法

---

**最後更新**: 2025-12-08  
**版本**: v2.1 - Demo 驗證完成  
**狀態**: Demo 驗證通過 → 準備開始 Phase 1 實現


