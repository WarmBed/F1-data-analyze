# Simple Mode Gap 計算修正報告

**日期**: 2026-01-05  
**問題**: Simple Mode 的 `gap_to_leader` 使用錯誤的計算方式  
**修正**: 改為基於累積時間 (`total_time`) 的正確計算

---

## 問題描述

用戶報告 Simple Mode 中的差距計算異常：
1. **問題 1**: 差距不是與 P1 的累積時間差
2. **問題 2**: HAM/LEC 異常追上領先車手
3. **根本原因**: `gap_to_leader` 使用 `track_position` 差異，而非真實累積時間

## 根本原因分析

### 錯誤的計算方式（修正前）
```python
# ❌ Line 1190-1193 (舊版)
gaps = {}
leader_track_pos = new_order[0][1].track_position if new_order else 0

for pos, (driver_code, state) in enumerate(new_order, 1):
    # 錯誤：使用 track_position 差異作為時間差距
    gap_to_leader = leader_track_pos - state.track_position
    gaps[driver_code] = gap_to_leader
```

**為何錯誤？**
- `track_position` 是**賽道位置**指標，非真實時間
- 不考慮：
  - 進站時間損失
  - 累積圈時差異
  - 輪胎性能變化
  - 燃油重量影響

### 正確的計算方式（修正後）
```python
# ✅ Line 1183-1193 (新版)
gaps = {}
leader_total_time = new_order[0][1].total_time if new_order else 0.0

for pos, (driver_code, state) in enumerate(new_order, 1):
    # 正確：使用累積時間差異
    gap_to_leader = state.total_time - leader_total_time
    gaps[driver_code] = gap_to_leader
    state.gap_to_leader = gap_to_leader
```

**為何正確？**
- `total_time` 在 Line 1096 累積：`state.total_time += actual_lap_time`
- 考慮：
  - ✅ 所有圈時累積
  - ✅ 進站時間損失
  - ✅ 輪胎衰退影響
  - ✅ 燃油重量影響
  - ✅ SC/VSC 影響

---

## 修正內容

### 檔案位置
`strategy_simulator/core/race_simulator.py`

### 變更範圍
Line 1183-1193 (`_simulate_lap()` 方法)

### 具體修改
```diff
  # ========== PHASE 5: Assign final positions ==========
  gaps = {}
- leader_track_pos = new_order[0][1].track_position if new_order else 0
+ leader_total_time = new_order[0][1].total_time if new_order else 0.0
  
  for pos, (driver_code, state) in enumerate(new_order, 1):
      old_pos = state.position
      state.position = pos
      
-     # Calculate gap to leader
-     gap_to_leader = leader_track_pos - state.track_position
+     # ✅ Calculate gap to leader using cumulative time (not track_position)
+     # This shows the true time difference, including pit stops and pace variations
+     gap_to_leader = state.total_time - leader_total_time
      gaps[driver_code] = gap_to_leader
      state.gap_to_leader = gap_to_leader
```

---

## 預期影響

### 修正前的行為（錯誤）
- HAM 進站後，gap 可能顯示為 -5s（因為 track_position 變化）
- 實際累積時間差異被忽略
- 進站時間損失未正確反映
- 差距計算與實際賽況不符

### 修正後的行為（正確）
- HAM 進站後，gap 顯示累積時間差異（例如 +22s）
- 差距反映真實比賽狀況
- 進站策略的時間成本準確
- 與 2025 Abu Dhabi 實際賽果可比較

---

## 驗證計劃

### 測試腳本
- `test_gap_calculation_logic.py` - 最小化邏輯測試
- `test_abu_dhabi_2025_gap_fix.py` - 實際賽事驗證

### 驗證標準
1. **進站前後差距**：進站車手應顯示 +20s 以上差距
2. **累積效應**：圈時差異應累積反映
3. **實際賽果比較**：與 2025 Abu Dhabi 實際差距誤差 < 10s

### 實際賽果參考（2025 Abu Dhabi GP）
```
1. VER - Winner
2. PIA - +12.594s
3. NOR - +16.572s
4. LEC - +23.279s
5. RUS - +48.563s
```

---

## 相關系統

### 不受影響的模組
- **Complete Mode (PositionTracker)**: 使用獨立的差距計算邏輯
- **Long Run Data**: 不影響基準數據
- **Strategy Optimizer**: 可能因正確差距計算而改進優化結果

### 可能受益的功能
- **蒙地卡羅模擬**: 更準確的勝率預測
- **策略比較**: 正確反映策略差異的時間成本
- **實際賽事驗證**: 可與實際 F1 賽果進行比較

---

## 開發記錄

### 發現過程
1. 用戶報告：「gap 不是 P1 的累積差距」
2. 檢查 `_simulate_lap()` 發現使用 `track_position`
3. 確認 `total_time` 已在 Line 1096 正確更新
4. 修正 gap 計算改用 `total_time`

### 修正時間
- **發現問題**: 2026-01-05 15:45
- **完成修正**: 2026-01-05 16:20
- **驗證測試**: 進行中

---

## 備註

### track_position 的正確用途
- `track_position` 仍用於超車判定（Line 1149-1180）
- 用於判斷車輛在賽道上的相對位置
- **不應**用於計算時間差距

### 未來改進
- [ ] 加入單元測試驗證 gap 計算
- [ ] 與實際 F1 賽果進行系統化比較
- [ ] 文檔化 `track_position` vs `total_time` 的使用場景
