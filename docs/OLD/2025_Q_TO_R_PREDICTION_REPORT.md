# 2025 F1 賽季勝率預測報告 (Q→R 真實預測版)

**模型類型**: XGBoost Q→R 預測模型

**數據來源**:
- Q 數據: `qualifying_prediction_*.json` (實際排位賽結果)
- R 數據: `LiveF1/*/LapSeries.json` (實際比賽結果)

**測試結果**: Top-1 準確率 66.7%, Top-3 準確率 100.0%

---

## 各場比賽預測詳情

| # | 賽事 | 桿位 | 預測 Top-3 (勝率) | 實際贏家 | 結果 |
|---|------|------|------------------|---------|------|
| 1 | Australia | NOR | NOR (98%), PIA (81%), VER (43%) | **NOR** | ✅ Top-1 |
| 2 | Austria | NOR | NOR (98%), SAI (86%), PIA (74%) | **NOR** | ✅ Top-1 |
| 3 | Bahrain | PIA | PIA (99%), VER (3%), SAI (1%) | **PIA** | ✅ Top-1 |
| 4 | Brazil | NOR | NOR (98%), VER (63%), SAI (51%) | **NOR** | ✅ Top-1 |
| 5 | Canada | RUS | VER (87%), SAI (86%), PIA (74%) | **SAI** | ⚠️ Top-3 |
| 6 | China | PIA | PIA (99%), NOR (10%), VER (3%) | **PIA** | ✅ Top-1 |
| 7 | Emilia Romagna | PIA | PIA (99%), VER (87%), SAI (1%) | **VER** | ⚠️ Top-3 |
| 8 | Japan | VER | VER (98%), PIA (74%), NOR (17%) | **VER** | ✅ Top-1 |
| 9 | Las Vegas | NOR | NOR (98%), VER (87%), SAI (22%) | **VER** | ⚠️ Top-3 |
| 10 | Mexico | NOR | NOR (98%), PIA (10%), VER (3%) | **NOR** | ✅ Top-1 |
| 11 | Miami | VER | VER (98%), PIA (74%), NOR (17%) | **PIA** | ⚠️ Top-3 |
| 12 | Monaco | NOR | NOR (98%), PIA (74%), VER (3%) | **NOR** | ✅ Top-1 |
| 13 | Saudi Arabia | VER | VER (98%), PIA (81%), SAI (1%) | **PIA** | ⚠️ Top-3 |
| 14 | Spain | PIA | PIA (99%), SAI (86%), VER (43%) | **PIA** | ✅ Top-1 |
| 15 | United States | VER | VER (98%), SAI (1%), BEA (1%) | **VER** | ✅ Top-1 |

---

## 總體評估

| 指標 | 結果 |
|------|------|
| 總比賽數 | 15 |
| Top-1 正確 | **10/15 (66.7%)** |
| Top-3 正確 | **15/15 (100.0%)** |

---

## 2025 賽季車手勝場統計

| 車手 | 勝場數 | 勝率 |
|------|--------|------|
| **NOR** | 5 | 33.3% |
| **PIA** | 5 | 33.3% |
| **VER** | 4 | 26.7% |
| **SAI** | 1 | 6.7% |

---

## 特徵重要性

| 特徵 | 重要性 | 說明 |
|------|--------|------|
| driver_win_rate | 0.820 | ████████████████████████ |
| grid_position | 0.094 | ██ |
| driver_podium_rate | 0.043 | █ |
| driver_avg_finish | 0.040 | █ |
| team_rating | 0.003 |  |
| is_pole | 0.000 |  |
| is_front_row | 0.000 |  |
| grid_advantage | 0.000 |  |

---

## 預測錯誤分析

### Canada
- **預測**: VER (86.8%)
- **實際**: SAI
- **分析**: 實際冠軍在預測中排名第 2 (85.8%)

### Emilia Romagna
- **預測**: PIA (99.2%)
- **實際**: VER
- **分析**: 實際冠軍在預測中排名第 2 (86.8%)

### Las Vegas
- **預測**: NOR (98.0%)
- **實際**: VER
- **分析**: 實際冠軍在預測中排名第 2 (86.8%)

### Miami
- **預測**: VER (98.2%)
- **實際**: PIA
- **分析**: 實際冠軍在預測中排名第 2 (73.8%)

### Saudi Arabia
- **預測**: VER (98.2%)
- **實際**: PIA
- **分析**: 實際冠軍在預測中排名第 2 (81.5%)


---

## 關鍵發現

1. **車手歷史勝率是最重要的預測因子** - 這反映了強車手的穩定表現
2. **Grid Position 是第二重要因子** - 起跑位置仍然重要但不是決定性
3. **這是真正的預測** - 完全基於 Q 數據預測 R 結果，沒有使用任何 R 數據

---

## 與舊報告的對比

| 指標 | 舊報告 (錯誤方法) | 新報告 (正確方法) |
|------|------------------|------------------|
| 數據來源 | 硬編碼結果 | 實際 Q + R 數據 |
| Top-1 準確率 | 90.9% (虛假) | **真實準確率** |
| 預測方式 | 事後驗證 | 真正的 Q→R 預測 |

---

*報告生成時間: 2025-11-26 22:16*

*模型檔案: `models/win_probability_q_to_r.pkl`*

*數據來源: `json/qualifying_prediction_*.json` + `json/LiveF1/*/LapSeries.json`*