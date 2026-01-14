# F1 Strategy System 實施計劃 (Phase 1-3)

## Phase 1：聯合訓練（車隊+賽道+輪胎）

### 目標
為每個**車隊+賽道+輪胎**組合訓練精確的策略係數，取代現有的固定預設值。

### 1.1 訓練腳本
- **檔案**: `CLI_modules/cli/prediction/train_strategy_coefficients.py`
- **維度**: 車隊（10）× 賽道（23）× 輪胎（3）= 690 組參數
- **公式**: 圈速 = base + 輪胎衰退 + 燃油效果 + 賽道進化

### 1.2 系統更新範圍
| 層級 | 變動 |
|------|------|
| **API** | `api/routers/config.py`: 新增 `/team-strategy-coefficients` |
| **GUI** | `driver_strategy.py`: 修改載入邏輯，優先使用車隊係數 |
| **Config** | 新增 `config/team_strategy_coefficients.json` |

---

## Phase 2：修復 Track Evolution (Driver Strategy)

### 目標
解決 Driver Strategy 預測線鋸齒狀問題，避免因中位數重算導致的波動。

### 2.1 算法改進
- **中位數快照鎖定**: 一旦某圈數據足夠並計算出中位數，永久鎖定該值。
- **固定 Baseline**: 基準圈鎖定後不再變動。
- **檔案**: `driver_strategy.py`

---

## Phase 3：Chase Strategy 重構（邏輯統一與升級）

### 目標
1.  **邏輯統一**：讓追趕策略直接使用 Driver Strategy 的預測核心，確保與主策略一致。
2.  **Pit Loss 升級**：支援不同車隊的進站效率差異（例如 Red Bull 通常比平均快 0.5s）。

### 3.1 Pit Loss 資料庫升級

**目標檔案**: `config/pit_loss_database.json`

**新結構 (Schema Change)**:
```json
"Bahrain": {
  "pit_loss_times": {
    "green_flag": 24.7,
    "safety_car": 12.8,
    "virtual_safety_car": 9.4
  },
  "team_offsets": {
    "Red Bull Racing": -0.5,
    "McLaren": -0.3,
    "Kick Sauber": +1.5
  }
}
```

### 3.2 Chase Strategy 代碼重構

**目標檔案**: `modules/gui/live_timing/live_timing_modules/chase_strategy.py`

**重構方案**:

不再重複造輪子（手算衰退率導數），而是：
1.  從 `DriverStrategy` (將提取公共邏輯) 獲取完整預測模型。
2.  計算 `time_P1 = Predict(P1_state)` 和 `time_P2 = Predict(P2_state)`。
3.  `Advantage = time_P1 - time_P2`。

**優勢**:
- ✅ 自動包含 **燃油效應**
- ✅ 自動包含 **Track Evolution**
- ✅ 自動應用 **Phase 1** 訓練出來的精確係數

### 3.3 執行步驟

1.  **數據準備**: 更新 `pit_loss_database.json` 添加隊伍 offset。
2.  **核心提取**: 將 `driver_strategy.py` 中的 `_calculate_stint_prediction` 提取為可重用的預測核心。
3.  **重寫 Chase**: 修改 `chase_strategy.py` 調用新的統一預測方法。
