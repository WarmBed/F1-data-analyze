# 位置追蹤系統開發任務 (Position Tracking System)

**創建日期**: 2026-01-05  
**狀態**: 規劃中 (Planning)  
**優先級**: P0 (最高)

---

## 📋 專案概述

開發完整的 F1 賽車位置追蹤模擬系統，支援雙模式（簡易/完整）並整合至策略模擬器 GUI。

---

## ✅ 已確認的技術能力

### 1. **彎角速度分析** ✅
- **CLI 模組**: `CLI_modules/cli/analyzer/all_drivers_cornering_analysis.py`
- **JSON 數據**: `json/all_drivers_cornering_analysis_*.json`
- **數據結構**:
  ```json
  {
    "selected_corners": {
      "low_speed": {"corner_number": 2, "avg_apex_speed": 93.5},
      "mid_speed": {"corner_number": 11, "avg_apex_speed": 168.2},
      "high_speed": {"corner_number": 7, "avg_apex_speed": 261.8}
    }
  }
  ```

### 2. **直線加速分析** ✅
- **CLI 模組**: `CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py`
- **JSON 數據**: `json/all_drivers_straight_line_speed_*.json`
- **數據結構**:
  ```json
  {
    "driver_speeds": [{
      "driver": "HAM",
      "max_speed_kmh": 337.0,
      "acceleration_time_100_300_seconds": 3.879,
      "acceleration_distance_100_300_meters": 212.26,
      "avg_acceleration_100_300_ms2": 9.74,
      "segment_start_speed_kmh": 114.0,
      "segment_end_speed_kmh": 337.0
    }]
  }
  ```

### 3. **Live Timing 數據** ✅
- **更新頻率**: 16ms (60 FPS)
- **數據位置**: `json/LiveF1/2025/{賽事名稱}/`
- **包含數據**:
  - CarData.z.jsonl (速度、油門、DRS)
  - Position.z.jsonl (賽道位置)
  - TimingData.jsonl (圈速、扇區時間)
  - TrackStatus.jsonl (旗幟狀態)

### 4. **Track Map 系統** ✅
- **模組**: `modules/gui/live_timing/live_timing_modules/track_map.py`
- **數據結構**:
  - `track_length`: 賽道總長度(米)
  - `track_points`: 包含 x, y, distance 的軌跡點
  - `track_outline`: 賽道輪廓座標

### 5. **超車預測** ✅
- **F83 Overtake Predictor**: `CLI_modules/cli/prediction/overtake_prediction/predictor.py`
- **整合位置**: `modules/gui/live_timing/core/data_manager.py`

---

## 🚀 開發決策 (2026-01-05)

### 決策 1: 速度模型數據源
- **選擇**: 1.B - 使用 FP2 Live Timing 數據
- **方案**: 從 FP2 live timing 下載 speed vs position 數據
- **數據來源**: `json/LiveF1/2025/{Race}_Practice_2/CarData.z.jsonl`
- **優勢**: 
  - 提供完整的速度 vs 距離曲線
  - 真實反映賽道特性
  - 可用於所有 2025+ 賽事

### 決策 2: DRS 區域配置
- **選擇**: 2.A - 手動配置 DRS 區域
- **實施計劃**:
  - 先開發 DRS 功能但不啟用
  - 後續加入至 `track_map.json`
  - **需要開發**: 新 CLI 模組獲取 DRS 區域數據

### 決策 3: Pit Lane 時間損失
- **選擇**: 從歷史進站數據計算
- **實施計劃**:
  - **需要開發**: 新 CLI 模組分析歷史進站數據
  - 計算每條賽道的平均 pit_loss_time
  - 輸出至 JSON 供模擬器使用

### 決策 4: 模擬時間步長
- **選擇**: 用戶可選 + GUI 插值
- **實施方案**:
  - Sim 後台: 用戶選擇步長 (預設 1.0s, 範圍 0.1s-10.0s)
  - GUI 前端: 固定 16ms 插值顯示
  - 同步機制: Sim 計算完整圈 → GUI 插值播放

### 決策 5: SC 場景處理
- **選擇**: 5.A - 保持位置 + 降速至 SC 速度
- **SC 速度**: 約 120 km/h
- **時間間距**: 需要進一步評估
- **實施計劃**:
  - **需要開發**: 新 CLI 模組分析 SC 期間車輛間距變化
  - 統計歷史 SC 場景的車輛壓縮模式

---

## 📝 待開發 CLI 模組清單

### 模組 1: DRS 區域數據提取器 (F-NEW-1)
**功能**: 從 FIA 數據或歷史 Live Timing 分析 DRS 區域位置

**輸入**:
- Year, Race, Session

**輸出 JSON**:
```json
{
  "year": 2025,
  "race": "Japan",
  "track_name": "Suzuka",
  "drs_zones": [
    {
      "zone_id": 1,
      "detection_line_distance": 1200.0,
      "activation_line_distance": 1350.0,
      "end_distance": 2100.0,
      "length_meters": 750.0
    },
    {
      "zone_id": 2,
      "detection_line_distance": 4500.0,
      "activation_line_distance": 4650.0,
      "end_distance": 5400.0,
      "length_meters": 750.0
    }
  ]
}
```

**實施方法**:
1. 從 Live Timing CarData.z 分析 DRS 欄位何時變化
2. 對應 Position.z 的 distance 欄位
3. 統計多圈數據取平均值

**優先級**: P1 (高)  
**預估工時**: 4-6 小時

---

### 模組 2: Pit Lane 時間損失分析器 (F-NEW-2)
**功能**: 從歷史進站數據計算每條賽道的 pit_loss_time

**輸入**:
- Year, Race (分析該賽道 2022-2025 所有正賽)

**輸出 JSON**:
```json
{
  "track_name": "Suzuka",
  "races_analyzed": [
    {"year": 2022, "race": "Japan", "session": "R"},
    {"year": 2023, "race": "Japan", "session": "R"},
    {"year": 2024, "race": "Japan", "session": "R"},
    {"year": 2025, "race": "Japan", "session": "R"}
  ],
  "pit_lane_analysis": {
    "avg_pit_loss_time_seconds": 22.3,
    "std_dev_seconds": 1.2,
    "min_loss_seconds": 20.1,
    "max_loss_seconds": 24.8,
    "sample_size": 156,
    "pit_lane_length_estimated_meters": 320.0
  },
  "pit_stop_duration_stats": {
    "avg_stop_duration_seconds": 2.8,
    "fastest_stop_seconds": 2.1,
    "slowest_stop_seconds": 3.9
  }
}
```

**實施方法**:
1. 讀取現有 `driver_detailed_pitstop_records_{year}_{race}_R.json`
2. 計算 lap_in vs lap_out 的時間差 - pit_duration
3. 統計多年數據取平均值
4. 估算 pit_lane_length (假設 pit lane 速度限制 80 km/h)

**優先級**: P1 (高)  
**預估工時**: 3-4 小時

---

### 模組 3: SC 間距壓縮分析器 (F-NEW-3)
**功能**: 分析 SC 期間車輛間距變化模式

**輸入**:
- Year, Race, Session (有 SC 的正賽)

**輸出 JSON**:
```json
{
  "year": 2025,
  "race": "Japan",
  "session": "R",
  "sc_events": [
    {
      "sc_id": 1,
      "start_lap": 15,
      "end_lap": 18,
      "duration_laps": 3,
      "sc_speed_kmh": 118.5,
      "gap_compression": {
        "initial_gaps_seconds": [1.2, 0.8, 2.3, 1.5, ...],
        "final_gaps_seconds": [0.5, 0.4, 0.6, 0.5, ...],
        "avg_initial_gap": 1.45,
        "avg_final_gap": 0.52,
        "compression_rate_per_lap": 0.31
      },
      "position_changes": []
    }
  ],
  "global_stats": {
    "avg_sc_speed_kmh": 120.0,
    "avg_final_gap_seconds": 0.5,
    "std_dev_gap_seconds": 0.15
  }
}
```

**實施方法**:
1. 從 Live Timing TimingData 檢測 SC 觸發 (GapToLeader 顯示 "SC")
2. 從 CarData.z 分析 SC 車速
3. 從 TimingData 追蹤每輛車的間距變化 (GapToLeader, IntervalToPositionAhead)
4. 統計壓縮速率和最終間距

**優先級**: P2 (中)  
**預估工時**: 5-7 小時

---

## 🏗️ 架構設計 (初步)

### 核心組件

```
strategy_simulator/
├── core/
│   ├── lap_simulator.py (現有 - 簡易模式)
│   ├── position_tracker.py (新增 - 完整模式)
│   ├── speed_model.py (新增 - FP2 數據載入)
│   ├── overtake_calculator.py (新增 - 超車概率)
│   └── sc_handler.py (新增 - SC 場景處理)
├── data/
│   ├── track_configs/ (新增 - 賽道配置)
│   │   ├── drs_zones.json
│   │   ├── pit_lane_data.json
│   │   └── sc_compression_stats.json
│   └── speed_profiles/ (新增 - 速度曲線)
│       └── {year}_{race}_FP2_speed_profile.json
└── gui/
    ├── input_panel.py (修改 - 新增模式選擇)
    └── visualization/ (新增 - 位置追蹤視覺化)
        ├── track_position_widget.py
        └── overtake_heatmap_widget.py
```

---

## 🎯 開發階段

### Phase 1: CLI 模組開發 (4-8 週)
- [ ] F-NEW-1: DRS 區域數據提取器
- [ ] F-NEW-2: Pit Lane 時間損失分析器
- [ ] F-NEW-3: SC 間距壓縮分析器
- [ ] 驗證所有 JSON 數據格式

### Phase 2: 速度模型 (2-3 週)
- [ ] FP2 Live Timing 數據載入器
- [ ] 速度 vs 距離曲線建模
- [ ] DRS 速度增益模型 (先用假設值)
- [ ] 彎角減速模型整合

### Phase 3: 位置追蹤核心 (3-4 週)
- [ ] position_tracker.py 實現
- [ ] 20 車同步模擬
- [ ] 超車判定邏輯
- [ ] Lapping 處理

### Phase 4: GUI 整合 (2-3 週)
- [ ] Radio Button 模式選擇
- [ ] 時間步長配置 UI
- [ ] 計算時間估算顯示
- [ ] 進度條與中斷機制

### Phase 5: 視覺化 (2-3 週)
- [ ] Track Position Widget (類似 Live Timing)
- [ ] Overtake Heatmap
- [ ] 策略比較圖表

### Phase 6: SC 場景 (1-2 週)
- [ ] SC 降速邏輯
- [ ] 間距壓縮模擬
- [ ] SC 結束加速

---

## 🔍 其他待確認問題

### 技術問題
1. **交通阻塞 (Traffic)**: 慢車阻擋如何影響速度？
   - 需要定義 "阻塞距離" (例如前車在 50m 內且慢 20+ km/h)
   - 速度降低幅度：5-15 km/h？

2. **超車成功率**: F83 預測器輸出概率 → 如何轉換為實際超車？
   - 使用隨機數 vs 固定閾值？
   - 超車持續時間：1-3 秒？

3. **輪胎磨損對速度影響**: 
   - 現有系統有 tire_degradation → lap_time_delta
   - 如何映射至速度曲線？ (彎角減速 + 加速減弱)

4. **Fuel Load 影響**:
   - 簡化模型: -0.03s/lap per kg？
   - 或: 影響加速度？

### 數據問題
5. **FP2 vs Race 差異**: FP2 速度曲線能否代表正賽？
   - FP2 通常更快 (低燃料 + 新胎)
   - 需要修正係數？

6. **賽道演化 (Track Evolution)**: 正賽隨圈數變快
   - 忽略？或加入簡單修正？

---

## 📊 資源與參考

### 現有模組參考
- Rain Analysis: `modules/gui/rain_analysis/` (UniversalAnalysisMDI 架構範本)
- Live Timing: `modules/gui/live_timing/` (位置追蹤、插值、視覺化)
- Monte Carlo: `strategy_simulator/core/monte_carlo.py` (SC 事件生成)

### 數據位置
- Corner Analysis: `json/all_drivers_cornering_analysis_*.json`
- Straight Line Speed: `json/all_drivers_straight_line_speed_*.json`
- Live Timing: `json/LiveF1/2025/{Race}_{Session}/`
- Pit Stops: `json/driver_detailed_pitstop_records_*.json`

---

## 📅 時程規劃

**預估總工時**: 14-23 週 (3.5-5.8 個月)

**里程碑**:
- 2026-02-01: Phase 1 完成 (CLI 模組)
- 2026-02-22: Phase 2 完成 (速度模型)
- 2026-03-22: Phase 3 完成 (位置追蹤核心)
- 2026-04-12: Phase 4 完成 (GUI 整合)
- 2026-05-03: Phase 5 完成 (視覺化)
- 2026-05-17: Phase 6 完成 (SC 場景)
- 2026-05-31: 測試與優化

---

## 🔄 更新日誌

### 2026-01-05
- 創建開發任務文檔
- 確認技術能力和數據源
- 記錄開發決策 (1.B, 2.A, 3, 4, 5.A)
- 定義 3 個待開發 CLI 模組
- 列出待確認問題清單
