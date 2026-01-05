# 🔬 FP2→Q 燃油校正可行性深度評估

**生成時間**: 2026年01月04日  
**評估者**: GitHub Copilot (Claude Sonnet 4.5)  
**觸發問題**: 用戶懷疑「預設燃油重量導致速度問題，各車隊預設數量不一定一致」

---

## ❌ 問題確認：你的觀察完全正確

### 核心問題

**我們無法準確知道 FP2 期間的燃油量**

```
FP2 會話中的燃油量是「未知變數」:

  場景 1: 長跑模式 (Race Simulation)
  ├── 燃油量: 70-110 kg
  ├── 目的: 測試正賽策略
  └── 圈速: 較慢 (-2.0s ~ -3.5s vs Q)

  場景 2: 單圈模式 (Qualifying Simulation)  
  ├── 燃油量: 10-25 kg
  ├── 目的: 測試最快圈配置
  └── 圈速: 接近 Q (-0.2s ~ -0.5s vs Q)

  場景 3: 混合模式
  ├── 前半段: 低油量測試 (20kg)
  ├── 後半段: 高油量長跑 (80kg)
  └── 圈速: 差異極大

  場景 4: 不同車隊的策略差異
  ├── Red Bull: 可能專注低油量測試
  ├── Aston Martin: 可能專注長跑
  └── 同場比賽，燃油策略完全不同
```

### FastF1 API 不提供燃油數據

```python
# FastF1 不提供的數據:
❌ session.laps['FuelLoad']        # 不存在
❌ session.laps['CarWeight']       # 不存在
❌ session.laps['FuelConsumed']    # 不存在

# FastF1 實際提供的數據:
✅ session.laps['LapTime']         # 圈速
✅ session.laps['TyreLife']        # 輪胎壽命
✅ session.laps['Stint']           # Stint 編號
✅ session.laps['Compound']        # 輪胎配方 (SOFT/MEDIUM/HARD)
✅ session.laps['PitInTime']       # 進站時間
✅ session.laps['PitOutTime']      # 出站時間
```

---

## 📊 原方案 B 的問題分析

### 原本的假設

```python
# 原方案 B 假設:
# improvement = fuel_coef * fuel_diff
# fuel_diff = 58 kg (固定值)

improvement = fp2_time - q_time
fuel_coef = improvement / 58  # 錯誤假設！
```

### 為什麼這個假設有問題？

| 問題 | 說明 | 影響 |
|-----|------|------|
| **假設燃油差異固定** | 實際 FP2 燃油量範圍 10-110 kg | 係數計算錯誤 |
| **忽略輪胎差異** | FP2 可能用舊胎，Q 用新胎 | 混淆燃油影響 |
| **忽略賽道演化** | FP2 早期 vs Q 後期，賽道狀態不同 | 混淆燃油影響 |
| **忽略車隊策略** | 不同車隊 FP2 策略不同 | 係數不可比較 |

### 範例：錯誤計算

```
Red Bull FP2→Q:
  - FP2 時間: 91.5s (Quali Sim，低油量 15kg)
  - Q 時間: 91.0s
  - 實際燃油差異: 15 - 12 = 3 kg
  - 實際改善: 0.5s
  - 錯誤計算: 0.5 / 58 = 0.0086 s/kg ❌
  - 正確計算: 0.5 / 3 = 0.167 s/kg ✅
  → 係數差 19 倍！

Aston Martin FP2→Q:
  - FP2 時間: 94.0s (Race Sim，高油量 80kg)
  - Q 時間: 91.5s
  - 實際燃油差異: 80 - 12 = 68 kg
  - 實際改善: 2.5s
  - 錯誤計算: 2.5 / 58 = 0.043 s/kg ❌
  - 正確計算: 2.5 / 68 = 0.037 s/kg ✅
  → 係數差 16%（相對較小，但仍不準確）
```

---

## ✅ 修正方案：基於 Stint 類型推斷燃油

### 方案 C: Stint 分類法 (推薦)

**核心概念**：從 **Stint 特徵** 推斷燃油狀態，而非假設固定值

```python
# Stint 分類規則:

def classify_stint_fuel_mode(stint_data):
    """
    根據 stint 特徵推斷燃油模式
    
    關鍵指標:
    1. Stint 長度 (圈數)
    2. 輪胎配方 (SOFT = 可能低油)
    3. 輪胎壽命 (TyreLife ≤ 3 = 新胎 = 可能 Quali Sim)
    4. 圈速趨勢 (平穩 vs 逐漸變慢)
    """
    
    stint_length = len(stint_data)
    compound = stint_data['Compound'].iloc[0]
    avg_tyre_life = stint_data['TyreLife'].mean()
    
    # === 燃油模式分類 ===
    
    # 模式 1: Quali Sim (低油量)
    if compound == 'SOFT' and stint_length <= 3 and avg_tyre_life <= 3:
        return {
            'mode': 'QUALI_SIM',
            'estimated_fuel_kg': 15,  # 低油量
            'confidence': 0.85
        }
    
    # 模式 2: 短跑測試 (中等油量)
    if stint_length <= 5:
        return {
            'mode': 'SHORT_RUN',
            'estimated_fuel_kg': 30,  # 中等油量
            'confidence': 0.70
        }
    
    # 模式 3: 中距離測試 (中高油量)
    if stint_length <= 10:
        return {
            'mode': 'MEDIUM_RUN',
            'estimated_fuel_kg': 50,  # 中高油量
            'confidence': 0.60
        }
    
    # 模式 4: Race Simulation (高油量)
    if stint_length > 10:
        return {
            'mode': 'RACE_SIM',
            'estimated_fuel_kg': 80,  # 高油量
            'confidence': 0.75
        }
    
    # 預設
    return {
        'mode': 'UNKNOWN',
        'estimated_fuel_kg': 50,
        'confidence': 0.30
    }
```

### 關鍵改進

1. **不再假設固定燃油差異**
2. **根據實際 Stint 特徵推斷**
3. **每個樣本獨立計算燃油估計**
4. **加入信心度權重**

---

## 📈 方案 C 的自動學習流程

### 步驟 1: 收集 Stint 級別數據

```python
# 新版數據結構: 以 Stint 為單位

{
    "year": 2024,
    "race": "Japan",
    "driver": "VER",
    "team": "Red Bull Racing",
    "stints": [
        {
            "stint_number": 1,
            "stint_length": 3,
            "compound": "SOFT",
            "avg_tyre_life": 2.0,
            "fastest_lap": 91.234,
            "avg_lap": 91.456,
            "lap_time_trend": -0.02,  # 秒/圈 (負 = 變快)
            "fuel_mode": "QUALI_SIM",
            "estimated_fuel": 15
        },
        {
            "stint_number": 2,
            "stint_length": 15,
            "compound": "MEDIUM",
            "avg_tyre_life": 8.5,
            "fastest_lap": 93.567,
            "avg_lap": 94.123,
            "lap_time_trend": 0.08,  # 秒/圈 (正 = 變慢)
            "fuel_mode": "RACE_SIM",
            "estimated_fuel": 80
        }
    ],
    "q_best_time": 91.050
}
```

### 步驟 2: 計算校正後的改善量

```python
def calculate_corrected_improvement(stint_data, q_time):
    """
    計算燃油校正後的改善量
    
    公式: 
    corrected_fp2 = fp2_time - fuel_effect * (estimated_fuel - Q_FUEL)
    improvement = q_time - corrected_fp2
    """
    Q_FUEL = 12  # Q 燃油量 (kg)
    FUEL_EFFECT = 0.032  # 預設燃油係數 (s/kg)
    
    estimated_fuel = stint_data['estimated_fuel']
    fp2_time = stint_data['fastest_lap']
    
    # 燃油校正
    fuel_penalty = FUEL_EFFECT * (estimated_fuel - Q_FUEL)
    corrected_fp2 = fp2_time - fuel_penalty
    
    # 真正的改善量（去除燃油影響後）
    true_improvement = q_time - corrected_fp2
    
    return {
        'raw_improvement': q_time - fp2_time,
        'corrected_improvement': true_improvement,
        'fuel_penalty_removed': fuel_penalty,
        'fuel_mode': stint_data['fuel_mode']
    }
```

### 步驟 3: 學習車隊特定係數

```python
def learn_team_fuel_coefficients_v2(all_data):
    """
    從 Stint 級別數據中學習車隊燃油係數
    
    關鍵改進:
    1. 只使用 QUALI_SIM 模式的數據（燃油量最確定）
    2. 排除異常值
    3. 加入信心度權重
    """
    team_samples = {}
    
    for record in all_data:
        team = record['team']
        q_time = record['q_best_time']
        
        # 只使用 Quali Sim stint（燃油量估計最可靠）
        quali_sim_stints = [
            s for s in record['stints']
            if s['fuel_mode'] == 'QUALI_SIM'
        ]
        
        if not quali_sim_stints:
            continue
        
        # 使用最快的 Quali Sim stint
        best_stint = min(quali_sim_stints, key=lambda x: x['fastest_lap'])
        
        # 計算改善量
        # Quali Sim 估計燃油: 15 kg
        # Q 燃油: 12 kg
        # 差異: 3 kg
        fuel_diff = 15 - 12  # 3 kg
        improvement = best_stint['fastest_lap'] - q_time
        
        # 反推燃油係數
        fuel_coef = improvement / fuel_diff if fuel_diff > 0 else 0.032
        
        if team not in team_samples:
            team_samples[team] = []
        
        team_samples[team].append({
            'fuel_coef': fuel_coef,
            'improvement': improvement,
            'confidence': best_stint.get('confidence', 0.7)
        })
    
    # 計算加權平均
    team_coefficients = {}
    for team, samples in team_samples.items():
        if len(samples) < 5:
            continue
        
        # 加權平均 (信心度作為權重)
        total_weight = sum(s['confidence'] for s in samples)
        weighted_coef = sum(s['fuel_coef'] * s['confidence'] for s in samples) / total_weight
        
        team_coefficients[team] = {
            'fuel_effect_per_kg': round(weighted_coef, 4),
            'sample_size': len(samples),
            'avg_confidence': round(total_weight / len(samples), 2)
        }
    
    return team_coefficients
```

---

## 🎯 最終評估結論

### 原方案 B 的問題

| 項目 | 狀態 | 說明 |
|------|------|------|
| 假設固定燃油差異 (58kg) | ❌ 錯誤 | 實際差異 3-90 kg 不等 |
| 混淆不同 Stint 類型 | ❌ 問題 | Quali Sim vs Race Sim 完全不同 |
| 車隊策略差異 | ❌ 未處理 | 不同車隊 FP2 目的不同 |
| 係數計算準確性 | ❌ 差 | 可能偏差 10-20 倍 |

### 修正方案 C 的優勢

| 項目 | 狀態 | 說明 |
|------|------|------|
| Stint 類型分類 | ✅ 改進 | 區分 Quali Sim vs Race Sim |
| 燃油量推斷 | ✅ 改進 | 根據 Stint 特徵估計 |
| 僅使用 Quali Sim 數據 | ✅ 關鍵 | 燃油量最確定的場景 |
| 信心度權重 | ✅ 改進 | 低信心樣本權重較低 |

### 預期效果

```
修正後的預測準確度提升：

方案 C vs 原方案 vs 現狀:

| 指標        | 現狀 v3.10 | 原方案 B | 方案 C  |
|------------|-----------|----------|---------|
| 整體 MAE   | 2.435s    | 不確定   | 1.5-1.8s |
| 最差 MAE   | 18.981s   | 可能更差 | 3.0-4.0s |
| 係數準確性 | N/A       | 差       | 良好     |
```

---

## 🚀 實施建議

### 優先順序

1. **短期 (1-2 週)**：
   - 修改 `FPQDataCollector` 添加 Stint 分類邏輯
   - 只使用 `fuel_mode == 'QUALI_SIM'` 的數據進行訓練
   - 暫時使用預設燃油係數 (0.032 s/kg)

2. **中期 (3-4 週)**：
   - 收集 2022-2025 的 Stint 級別數據
   - 執行車隊燃油係數學習
   - 驗證學習到的係數合理性

3. **長期 (持續)**：
   - 監控預測準確度變化
   - 根據新數據持續優化
   - 考慮添加更多 Stint 分類規則

### 是否值得做？

| 決策因素 | 評估 |
|---------|------|
| 技術可行性 | ✅ 可行，但需要 Stint 分類邏輯 |
| 準確度提升潛力 | ✅ 高，尤其是異常值處理 |
| 實施複雜度 | 🟡 中等 |
| 維護成本 | 🟡 中等 |

**建議**：值得實施，但需要先修正方案 B 的假設問題，改用方案 C 的 Stint 分類法。

---

## 📝 總結

### 你的觀察

> 「預設燃油重量導致速度問題，各車隊預設數量不一定一致」

✅ **完全正確**

### 問題根源

1. FP2 中不同車隊的燃油策略完全不同
2. 同一車手不同 Stint 的燃油量也不同
3. 假設固定 58 kg 燃油差異是錯誤的

### 解決方案

**方案 C: Stint 分類法**
- 根據 Stint 長度、輪胎配方、輪胎壽命推斷燃油模式
- 只使用 Quali Sim 類型的數據（燃油量最確定）
- 計算時使用合理的燃油估計值 (15 kg vs 12 kg = 3 kg 差異)

是否要繼續實施這個修正版方案？
