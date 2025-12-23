# F1 2025 各賽道最重要特徵一覽

**模型版本**: V3.8 | **生成時間**: 2025-11-06

## 📊 各賽道最重要特徵（TOP 1）

| # | 賽道 | 最重要特徵 | 占比 | 類型 |
|---|------|-----------|------|------|
| 1 | Australia | `ideal_lap` | **36.14%** | 理想圈速 |
| 2 | China | `speed_consistency` | **37.20%** | 速度一致性 |
| 3 | Japan | `ideal_lap` | **35.73%** | 理想圈速 |
| 4 | Bahrain | `ideal_lap` | **26.20%** | 理想圈速 |
| 5 | Saudi Arabia | `high_speed_apex` | **18.67%** | 高速彎角 |
| 6 | Miami | `ideal_s1` | **25.42%** | 分段時間 |
| 7 | Emilia Romagna | `ideal_s2` | **38.40%** | 分段時間 |
| 8 | Monaco | `fp3_gap_to_fastest` | **24.88%** | FP3表現 |
| 9 | Spain | `ideal_s3` | **36.61%** | 分段時間 |
| 10 | Canada | `ideal_s1` | **30.20%** | 分段時間 |
| 11 | Austria | `s1_s2_ratio` | **19.74%** | 分段比例 |
| 12 | Great Britain | `ideal_s1` | **61.77%** | 分段時間 |
| 13 | Belgium | `ideal_s2` | **56.28%** | 分段時間 |
| 14 | Hungary | `ideal_s2` | **23.66%** | 分段時間 |
| 15 | Netherlands | `mid_speed_apex` | **34.04%** | 中速彎角 |
| 16 | Italy | `ideal_s2` | **58.83%** | 分段時間 |
| 17 | Azerbaijan | `ideal_lap` | **25.42%** | 理想圈速 |
| 18 | Singapore | `ideal_s2` | **43.01%** | 分段時間 |
| 19 | United States | `ideal_lap` | **32.65%** | 理想圈速 |
| 20 | Mexico | `max_speed_lap_ratio` | **14.26%** | 速度比例 |
| 21 | Brazil | `low_speed_apex` | **81.22%** | 低速彎角 |
| 22 | Las Vegas | `mid_speed_apex` | **100.00%** | 中速彎角 ⚠️ |
| 23 | Qatar | `ideal_s2` | **39.68%** | 分段時間 |
| 24 | Abu Dhabi | `fp3_gap_to_fastest` | **36.40%** | FP3表現 |

---

## 🎯 特徵類型分布

### 理想圈速系列 (6 賽道)
- **Australia**, **Japan**, **Bahrain**, **Azerbaijan**, **United States**
- 平均重要性: 31.23%

### 分段時間 (12 賽道)
- **Miami** (S1), **Canada** (S1), **Great Britain** (S1)
- **Emilia Romagna** (S2), **Belgium** (S2), **Hungary** (S2), **Italy** (S2), **Singapore** (S2), **Qatar** (S2)
- **Spain** (S3)
- 平均重要性: 40.69%

### 彎角性能 (3 賽道)
- **Saudi Arabia** (高速), **Netherlands** (中速), **Brazil** (低速), **Las Vegas** (中速)
- 平均重要性: 62.03%

### FP3 練習賽表現 (2 賽道)
- **Monaco**, **Abu Dhabi**
- 平均重要性: 30.64%

### 其他 (2 賽道)
- **China** (速度一致性), **Austria** (S1/S2比例), **Mexico** (速度/圈速比)
- 平均重要性: 17.07%

---

## 🔥 極端值賽道

### 特徵占比 > 50%
1. **Las Vegas** - `mid_speed_apex` (100.00%) ⚠️ 異常值
2. **Brazil** - `low_speed_apex` (81.22%)
3. **Great Britain** - `ideal_s1` (61.77%)
4. **Italy** - `ideal_s2` (58.83%)
5. **Belgium** - `ideal_s2` (56.28%)

### 特徵占比 < 20%
1. **Mexico** - `max_speed_lap_ratio` (14.26%)
2. **Saudi Arabia** - `high_speed_apex` (18.67%)
3. **Austria** - `s1_s2_ratio` (19.74%)

---

## 💡 關鍵洞察

### 1. 分段時間主導
**12 個賽道 (50%)** 的最重要特徵是分段理想時間，顯示「完美執行各分段」是預測排位賽成績的關鍵。

### 2. S2 特別重要
**7 個賽道**的第一特徵是 `ideal_s2`，包括 Spa (Belgium)、Monza (Italy)、Singapore 等著名賽道。

### 3. FP3 作為預測指標
Monaco 和 Abu Dhabi 高度依賴 FP3 練習賽的表現，反映這些賽道的排位賽與練習賽有強關聯性。

### 4. 特殊賽道
- **Brazil**: 低速彎角 (81.22%) 絕對主導，反映 Interlagos 賽道特性
- **Great Britain**: S1 分段 (61.77%) 極端重要，Silverstone 賽道的獨特性
- **Las Vegas**: 數據異常需要重新訓練

---

**完整報告**: [feature_importance_summary_v3.8_readable.md](./feature_importance_summary_v3.8_readable.md)  
**快速參考**: [feature_importance_summary_quick_reference.md](./feature_importance_summary_quick_reference.md)  
**原始數據**: [feature_importance_summary_v3.8_20251106_072945.json](./feature_importance_summary_v3.8_20251106_072945.json)
