# FP2→Q 車隊燃油校正改善報告

**生成時間**: 2026年1月4日  
**版本**: 方案 B v1.0  
**評估數據**: 2022-2025 共 73 場比賽, 1140 個樣本

---

## 📊 執行摘要

### 車隊燃油習慣學習結果

| 車隊 | Quali Sim 圈數 | 平均改善量 | 估計 FP2 燃油 | 校正值 |
|------|---------------|-----------|--------------|--------|
| RB | 13 | 1.131s | 47.3kg | 1.131s |
| Racing Bulls | 7 | 1.190s | 49.2kg | 1.190s |
| AlphaTauri | 37 | 1.239s | 50.7kg | 1.239s |
| Aston Martin | 63 | 1.253s | 51.2kg | 1.253s |
| Kick Sauber | 20 | 1.292s | 52.4kg | 1.292s |
| Alpine | 70 | 1.480s | 58.3kg | 1.480s |
| McLaren | 45 | 1.544s | 60.3kg | 1.544s |
| Williams | 61 | 1.611s | 62.4kg | 1.611s |
| Alfa Romeo | 33 | 1.628s | 62.9kg | 1.628s |
| Haas F1 Team | 67 | 1.645s | 63.4kg | 1.645s |
| Red Bull Racing | 41 | 1.748s | 66.6kg | 1.748s |
| Ferrari | 33 | 1.746s | 66.6kg | 1.746s |
| Mercedes | 50 | 1.827s | 69.1kg | 1.827s |

### 關鍵發現

1. **車隊間燃油策略差異顯著**
   - 燃油量範圍: 47.3kg (RB) ~ 69.1kg (Mercedes)
   - 差距達 21.8kg，對應約 0.7s 的圈速差異

2. **頭部車隊傾向較高燃油測試**
   - Red Bull Racing: 66.6kg
   - Ferrari: 66.6kg
   - Mercedes: 69.1kg
   - 可能反映更多 Race Simulation 測試

3. **小車隊傾向較低燃油測試**
   - RB (Visa Cash App RB): 47.3kg
   - Racing Bulls: 49.2kg
   - 可能專注於 Quali Sim 以最大化 FP2 排名表現

---

## 📈 校正方法效果比較

| 方法 | 樣本數 | MAE | 中位數 | P90 | 最大誤差 |
|------|-------|-----|--------|-----|---------|
| 無校正 (直接使用 FP2) | 1140 | 2.285s | 1.555s | 5.735s | 9.974s |
| 固定校正 (58kg) | 1140 | 1.472s | 0.934s | 3.879s | 8.118s |
| **車隊特定校正** | 1140 | **1.417s** | **0.758s** | 4.191s | 8.842s |
| 車隊校正 (僅 Quali Sim) | 559 | **0.912s** | 0.561s | 1.869s | 8.842s |

### 改善幅度

- **車隊校正 vs 固定校正**: 
  - MAE 改善: 0.055s (3.7%)
  - 中位數改善: 0.176s (18.8%)

- **僅 Quali Sim 圈的準確度**: 
  - MAE: 0.912s
  - 比全部樣本好 36%

---

## 🏎️ 按賽事改善分析

### Top 10 改善最大的賽事

| 賽事 | 固定 MAE | 車隊 MAE | 改善 |
|------|----------|----------|------|
| 2024 Emilia Romagna | 1.075s | 0.794s | +0.281s |
| 2024 Netherlands | 1.542s | 1.276s | +0.266s |
| 2025 Emilia Romagna | 1.635s | 1.369s | +0.266s |
| 2025 Italy | 0.948s | 0.684s | +0.264s |
| 2024 Abu Dhabi | 1.134s | 0.886s | +0.248s |
| 2025 Saudi Arabia | 1.248s | 1.000s | +0.248s |
| 2025 Australia | 0.755s | 0.514s | +0.241s |
| 2024 Singapore | 1.146s | 0.923s | +0.223s |
| 2023 Netherlands | 1.492s | 1.271s | +0.221s |
| 2024 Saudi Arabia | 1.089s | 0.875s | +0.214s |

### 效果不佳的賽事

| 賽事 | 固定 MAE | 車隊 MAE | 改善 |
|------|----------|----------|------|
| 2022 Austria | 1.789s | 2.085s | -0.296s |
| 2024 Canada | 4.412s | 4.700s | -0.288s |
| 2023 Las Vegas | 2.012s | 2.285s | -0.273s |
| 2023 Australia | 0.606s | 0.865s | -0.258s |

**分析**: 某些賽事車隊策略變化較大，歷史習慣可能不適用

---

## 🔧 技術實現

### 已完成的修改

1. **學習腳本**: `learn_team_fuel_habits.py`
   - 從訓練數據學習各車隊的 FP2 燃油習慣
   - 優先使用 Quali Sim 圈 (tire_age ≤ 3)
   - 輸出: `training_data/team_fuel_habits.json`

2. **Function 76 整合**
   - 載入車隊燃油習慣檔案
   - 預測時應用車隊特定校正值
   - JSON 輸出增加 `fuel_correction` 和 `fuel_correction_source` 欄位

3. **評估腳本**: `evaluate_fuel_correction.py`
   - 比較四種校正方法
   - 按賽事分析改善效果

### 使用方式

```powershell
# 1. 學習車隊燃油習慣 (首次或需要更新時)
python learn_team_fuel_habits.py

# 2. 執行 FP2→Q 預測 (已自動載入車隊校正)
python f1_analysis_modular_main.py -f 76 -y 2025 -r Japan

# 3. 評估校正效果
python evaluate_fuel_correction.py
```

---

## 📋 結論與建議

### ✅ 方案 B 有效性

1. **車隊燃油習慣確實存在且可學習**
   - 13 個車隊的燃油策略有明顯差異
   - 從 47.3kg 到 69.1kg，差距 21.8kg

2. **整體改善有限但穩定**
   - MAE 改善 3.7% (0.055s)
   - 中位數改善 18.8% (0.176s)

3. **Quali Sim 圈數據品質最高**
   - 僅 Quali Sim 圈的 MAE: 0.912s
   - 建議模型訓練優先使用 Quali Sim 圈

### 🔮 後續改進建議

1. **動態車隊校正**
   - 考慮賽季內車隊策略變化
   - 使用最近 N 場比賽的滾動平均

2. **賽道特定校正**
   - 某些賽道可能影響燃油策略
   - 結合賽道類型進行分層校正

3. **異常檢測**
   - 識別並過濾策略異常的樣本
   - 減少訓練數據噪音

4. **模型重訓練**
   - 在特徵中加入 `team_fuel_correction` 作為輸入
   - 讓 XGBoost 學習如何使用車隊校正

---

## 📁 相關檔案

| 檔案 | 說明 |
|------|------|
| [learn_team_fuel_habits.py](learn_team_fuel_habits.py) | 車隊燃油習慣學習腳本 |
| [evaluate_fuel_correction.py](evaluate_fuel_correction.py) | 校正效果評估腳本 |
| [training_data/team_fuel_habits.json](training_data/team_fuel_habits.json) | 車隊燃油習慣數據 |
| [training_data/fuel_correction_evaluation.json](training_data/fuel_correction_evaluation.json) | 評估結果 JSON |
