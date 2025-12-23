# F85: Live Timing 超車預測整合報告

**日期**: 2025-01-XX  
**狀態**: 完成  

## 概述

F85 功能將 F83 超車預測器成功整合至 Live Timing GUI 系統，使用者可以在即時排名塔中看到每位車手對前車的超車機率。

## 架構設計

### 整合點

1. **LiveTimingDataManager** (`modules/gui/live_timing/core/data_manager.py`)
   - 新增延遲導入函數 `_lazy_import_overtake_predictor()`
   - 新增初始化方法 `_init_overtake_predictor()`
   - 新增預測更新方法 `_update_overtake_predictions()`
   - 新增間距解析方法 `_parse_gap_seconds()`

2. **RankingTableWidget** (`modules/gui/live_timing/live_timing_modules/ranking_tower.py`)
   - 新增 OT% 欄位 (欄位索引 20)
   - 新增 `_set_overtake_probability()` 方法
   - 更新欄位數量從 22 增加至 23

### 數據流

```
快照更新 → _on_playback_tick() 
         → _update_overtake_predictions()
         → OvertakePredictor.predict()
         → 更新 snapshot['drivers'][driver_num]['overtake_probability']
         → RankingTableWidget 顯示 OT%
```

## 功能特性

### 超車機率計算

F83 預測器考慮以下因素：
- 間距 (gap_seconds)
- 間距變化率 (gap_delta)
- DRS 可用性 (drs_available)
- 輪胎化合物差異 (attacker_tyre vs defender_tyre)
- 輪胎壽命差 (tyre_age_diff)
- 賽道狀態 (track_status_green)
- 進攻者位置 (attacker_position)
- 比賽進度 (race_progress)

### 顯示格式

| 機率範圍 | 信心等級 | 背景顏色 | 說明 |
|---------|---------|---------|------|
| >= 70% | HIGH | 綠色 | 高超車機會 |
| >= 40% | MEDIUM | 黃色 | 中等機會 |
| >= 20% | LOW | 橙色 | 低機會 |
| < 20% | - | 預設 | 超車困難 |
| P1 | - | 預設 | 顯示 "-" |

### 快取策略

- 每圈只計算一次超車預測（避免頻繁計算）
- 使用 `_cached_overtake_predictions` 快取結果
- 使用 `_last_overtake_prediction_lap` 追蹤上次計算的圈數

## 測試結果

```python
# 測試場景
P1 VER: OT% = 0.0%      # 領先者沒有前車
P2 LEC: OT% = 14.6%     # 與 VER 相距 0.8s
P3 NOR: OT% = 11.3%     # 與 LEC 相距 1.5s
P4 PIA: OT% = 77.7%     # 與 NOR 相距 0.5s (DRS 範圍)
```

## 使用方式

1. 啟動 Live Timing GUI
2. 載入任一賽事回放
3. 在排名塔中查看 OT% 欄位
4. 高亮顯示的車手有較高的超車機會

## 相關檔案

- `CLI_modules/cli/prediction/overtake_prediction/predictor.py` - F83 核心預測器
- `modules/gui/live_timing/core/data_manager.py` - 數據管理器整合
- `modules/gui/live_timing/live_timing_modules/ranking_tower.py` - 排名塔顯示
- `models/overtake_prediction/overtake_xgb_v3.json` - 訓練好的 XGBoost 模型

## 未來改進

1. **F84 LLM 整合**: 為高超車機率場景提供自然語言解釋
2. **歷史追蹤**: 記錄預測結果與實際超車的對比
3. **即時提醒**: 當超車機率超過閾值時發送通知
