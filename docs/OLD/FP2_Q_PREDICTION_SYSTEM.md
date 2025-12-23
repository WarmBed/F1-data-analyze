# FP2→Q 排位賽預測系統說明

**創建日期**: 2025-12-13  
**功能編號**: Function 75 / Function 76  
**模型版本**: v3.10 (FP2 版本)

---

## 📋 系統概述

FP2→Q 預測系統使用**週五下午 FP2 練習賽**的數據來預測**週六排位賽 (Q)** 的成績，比 FP3→Q 系統提前約 **18-24 小時**提供預測。

### 🎯 設計目的

1. **提前預測**: 週五晚上即可獲得排位賽預測
2. **策略價值**: 幫助分析車隊在週五到週六的調校方向
3. **補充系統**: 與 FP3→Q 系統互補，提供雙重驗證
4. **長距離數據**: 利用 FP2 豐富的正賽模擬長跑數據

---

## 🏗️ 系統架構

```
FP2 數據收集 (Function 70)
    ↓
FP2→Q 模型訓練 (Function 75)
    ↓
FP2→Q 預測生成 (Function 76)
    ↓
JSON 輸出: json/fp2_qualifying_prediction_{year}_{race}.json
```

### 與 FP3→Q 系統對比

| 項目 | FP3→Q (Function 73/74) | FP2→Q (Function 75/76) |
|------|------------------------|------------------------|
| **數據源** | FP3 (週六上午) | FP2 (週五下午) |
| **預測時間** | 排位賽前 2-3 小時 | 排位賽前 18-24 小時 |
| **預期準確度** | 高 (Top-1: ~60-70%) | 中 (Top-1: ~50-60%) |
| **特徵數量** | 16 特徵 (v3.10) | 16 特徵 (v3.10) |
| **模型目錄** | `models/track_specific_v3.10/` | `models/fp2_q_specific_v3.10/` |
| **JSON 輸出** | `qualifying_prediction_{year}_{race}.json` | `fp2_qualifying_prediction_{year}_{race}.json` |
| **用途** | 最終排位賽預測 | 早期預測 + 調校分析 |

---

## 🛠️ 使用指南

### 步驟 1: 收集訓練數據 (可選)

如果需要重新訓練模型，先收集 FP2 數據：

```powershell
# 收集單場賽事的 FP2 數據
python f1_analysis_modular_main.py -f 70 -y 2024 -r Japan

# 收集整個賽季的 FP2 數據
python f1_analysis_modular_main.py -f 70 -y 2024 --season

# 收集多個賽季的 FP2 數據
python f1_analysis_modular_main.py -f 70 --start-year 2018 --end-year 2024
```

**注意**: Function 70 會自動優先使用 FP3，如需專門收集 FP2 數據，需修改代碼或手動處理。

---

### 步驟 2: 訓練 FP2→Q 模型 (Function 75)

```powershell
# 訓練單一賽道模型
python f1_analysis_modular_main.py -f 75 --track Japan

# 訓練所有賽道模型 (24 個賽道)
python f1_analysis_modular_main.py -f 75

# 自訂訓練參數
python f1_analysis_modular_main.py -f 75 --track Monaco --trials 500 --cv-folds 3 --workers 4
```

**參數說明**:
- `--track`: 指定單一賽道名稱 (預設: 訓練所有賽道)
- `--trials`: Optuna 超參數優化試驗次數 (預設: 500)
- `--cv-folds`: 交叉驗證 folds (預設: 3)
- `--workers`: 並行處理器數量 (預設: 1)
- `--start-year`: 訓練數據起始年份 (預設: 2018)
- `--end-year`: 訓練數據結束年份 (預設: 2024)

**輸出**:
- 模型檔案: `models/fp2_q_specific_v3.10/{track}.pkl`
- 訓練報告: `fp2_q_v3.10_training_results.json`

---

### 步驟 3: 生成 FP2→Q 預測 (Function 76)

```powershell
# 生成單場賽事預測
python f1_analysis_modular_main.py -f 76 -y 2025 -r Japan

# 批次生成預測
python f1_analysis_modular_main.py -f 76 -y 2025 -r Australia
python f1_analysis_modular_main.py -f 76 -y 2025 -r Bahrain
python f1_analysis_modular_main.py -f 76 -y 2025 -r Monaco
```

**輸出**:
- JSON 檔案: `json/fp2_qualifying_prediction_{year}_{race}.json`

---

## 📊 JSON 輸出結構

```json
{
  "metadata": {
    "track": "Japan",
    "year": 2025,
    "session": "Q",
    "data_source": "FP2",
    "model_r2": 0.7845,
    "model_mae": 0.285,
    "sample_count": 142,
    "prediction_time": "2025-12-13T18:30:00",
    "model_version": "v3.10_FP2",
    "feature_count": 16,
    "has_actual_results": false
  },
  "predictions": [
    {
      "rank": 1,
      "driver": "VER",
      "team": "Red Bull Racing",
      "fp2_time": 89.234,
      "predicted_time": 88.912,
      "actual_q_time": null,
      "improvement": -0.322
    },
    {
      "rank": 2,
      "driver": "LEC",
      "team": "Ferrari",
      "fp2_time": 89.456,
      "predicted_time": 89.123,
      "actual_q_time": null,
      "improvement": -0.333
    }
    // ... 更多車手
  ]
}
```

---

## 🔍 特徵架構 (v3.10 FP2 版本)

### 16 個特徵 (與 FP3→Q 相同架構)

#### v3.0 基礎特徵 (8)
1. `ideal_s1` - FP2 最快 Sector 1 時間
2. `ideal_s2` - FP2 最快 Sector 2 時間
3. `ideal_s3` - FP2 最快 Sector 3 時間
4. `ideal_lap` - FP2 最快單圈時間
5. `low_speed_apex` - 低速彎頂點速度 (25th percentile)
6. `mid_speed_apex` - 中速彎頂點速度 (50th percentile)
7. `high_speed_apex` - 高速彎頂點速度 (75th percentile)
8. `max_speed` - 最高速度

#### v3.3 交互特徵 (3)
9. `s1_s2_ratio` - Sector 1 / Sector 2 比例
10. `sector_cv` - 速度變異係數 (std / mean)
11. `s2_lap_ratio` - Sector 2 / 總圈時比例

#### v3.4 速度特徵 (3)
12. `max_speed_lap_ratio` - 最高速度 × 圈時 / 1000
13. `max_speed_s2_ratio` - 最高速度 / Sector 2 時間
14. `speed_consistency` - 速度一致性 (1 - cv)

#### v3.5 FP2 排位特徵 (2)
15. `fp2_relative_position` - FP2 相對排名位置 (0-1)
16. `fp2_gap_to_fastest` - FP2 與最快圈的差距 (秒)

---

## ⚠️ 注意事項

### 1. 訓練數據要求

目前 Function 75 需要專門的 FP2→Q 訓練數據檔案:
- 檔案位置: `training_data/fp2_q_training_data.json`
- **目前尚未實作專門的 FP2 數據收集器**

**臨時解決方案**:
- 修改 Function 70 的代碼，強制使用 FP2 而非 FP3
- 或手動收集 FP2 數據並構建訓練集

### 2. 預期準確度

FP2→Q 預測的準確度預計比 FP3→Q **低 5-10%**:
- FP2 距離排位賽更遠（週五 vs 週六）
- 週五到週六車隊會進行大量調校
- FP2 通常專注長距離測試，非單圈速度

**預期性能**:
- Top-1 準確率: 50-60% (vs FP3 的 60-70%)
- Top-3 準確率: 80-90% (vs FP3 的 90-100%)
- 平均 MAE: 0.3-0.5s (vs FP3 的 0.2-0.3s)

### 3. 使用場景

✅ **適合使用 FP2→Q 的情況**:
- 週五晚上需要早期預測
- 分析車隊調校策略（FP2 vs FP3 差異）
- 比較 FP2 和 FP3 預測，找出異常車隊
- 投注或預測比賽需要提前決策

❌ **不適合使用 FP2→Q 的情況**:
- 需要最高準確度的最終預測 → 使用 FP3→Q (Function 74)
- Sprint 週末（沒有 FP2）
- 天氣變化劇烈的週末

---

## 🧪 測試範例

### 測試 Import

```powershell
python -c "from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper; mapper = F1AnalysisFunctionMapper(); print(f'Function 75: {75 in mapper.function_mapping}'); print(f'Function 76: {76 in mapper.function_mapping}')"
```

預期輸出:
```
✅ Import 成功
✅ Function 75: True
✅ Function 76: True
```

### 測試訓練 (單一賽道)

```powershell
python f1_analysis_modular_main.py -f 75 --track Japan
```

### 測試預測生成

```powershell
python f1_analysis_modular_main.py -f 76 -y 2024 -r Japan
```

---

## 🔮 未來改進計劃

1. **專門的 FP2 數據收集器**
   - 修改 Function 70，支援 `--session FP2` 參數
   - 或創建 Function 70.2 專門收集 FP2 數據

2. **FP2+FP3 組合模型**
   - 利用 FP2 和 FP3 雙重數據
   - 捕捉車隊調校方向

3. **GUI 整合**
   - 在排位賽預測模組中顯示 FP2 和 FP3 雙重預測
   - 比較兩者差異，分析調校效果

4. **自動化 Pipeline**
   - 週五晚上自動生成 FP2→Q 預測
   - 週六中午自動生成 FP3→Q 預測
   - 比較兩者差異並生成報告

---

## 📝 相關文檔

- FP3→Q 預測系統: Function 73/74
- Q→R 正賽預測系統: Function 80
- 訓練數據收集: Function 70
- API 規格: `api/models/function_specs.py`

---

## ❓ 常見問題

### Q1: 為什麼需要 FP2→Q 預測？

**A**: 提前預測的戰略價值：
- 週五晚上即可獲得排位賽預測
- 分析車隊調校方向（FP2 → FP3 → Q 的演進）
- 為投注、幻想比賽等需求提供早期決策依據

### Q2: FP2→Q 的準確度有多高？

**A**: 預期比 FP3→Q **低 5-10%**：
- FP3→Q: Top-1 準確率 60-70%
- FP2→Q: Top-1 準確率 50-60%
- 差異原因: 週五到週六車隊會調校，FP2 數據較舊

### Q3: 如何收集 FP2 訓練數據？

**A**: 目前需要手動處理：
1. 修改 Function 70 代碼，強制使用 FP2
2. 或等待未來的 Function 70.2 (FP2 專用收集器)

### Q4: Sprint 週末可以用嗎？

**A**: 不建議，因為：
- Sprint 週末沒有傳統的 FP2
- 改用 Sprint Qualifying 或 Sprint 數據
- 建議使用 FP3→Q (Function 74) 或等待 Sprint 專用模型

---

## 👨‍💻 開發者資訊

**實作者**: GitHub Copilot  
**實作日期**: 2025-12-13  
**程式碼位置**:
- 訓練器: `CLI_modules/cli/core/function_mapper.py::_execute_fp2_q_batch_trainer`
- 生成器: `CLI_modules/cli/core/function_mapper.py::_execute_fp2_q_prediction_generator`
- API 規格: `api/models/function_specs.py`

**版本歷史**:
- v1.0 (2025-12-13): 初始版本，架構與 FP3→Q 相同
