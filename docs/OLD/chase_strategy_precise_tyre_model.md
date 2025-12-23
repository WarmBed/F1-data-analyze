# Chase Strategy - 精確輪胎衰退模型整合

## 📅 更新日期
**2025-01-XX** - 完成所有 5 個策略的精確輪胎衰退模型整合

---

## ✅ 完成項目

### 1. **Pit Loss 數據庫整合** (已完成)
- ✅ 整合 `config/pit_loss_database.json`
- ✅ 21+ 賽道的賽道專屬進站損失數據
- ✅ 支援 Green Flag / Safety Car / VSC 三種情況

### 2. **輪胎衰退模型整合** (已完成)
- ✅ 整合 `config/tire_degradation_database.json`
- ✅ 24 個賽道的配方專屬衰退係數
- ✅ 二次方程式模型：`degradation(t) = base_rate * t + 0.5 * acceleration * t²`
- ✅ 即時衰退速度：`d(degradation)/dt = base_rate + acceleration * t`

### 3. **策略 1-5 全面升級** (已完成)

#### 策略 1：繼續當前輪胎
- ✅ 精確計算 P1/P2 各自的衰退速度
- ✅ 考慮配方差異（SOFT/MEDIUM/HARD）
- ✅ 考慮輪胎齡差異

#### 策略 2：立即進站 Undercut
- ✅ P2 換與 P1 **相同配方**的新胎
- ✅ 計算新胎 vs 舊胎的速度優勢
- ✅ 考慮進站損失 (21s Bahrain)

#### 策略 3：等待安全車
- ✅ P2 在 SC 期間換新胎（同配方）
- ✅ SC 進站優勢（10s 節省）
- ✅ 假設 5 圈後 SC 出現

#### 策略 4：主動進站模擬
- ✅ 用戶指定進站圈數和配方
- ✅ 計算指定配方的新胎優勢
- ✅ 動態評估可行性

#### 策略 5：P1 先進站
- ✅ P1 換新胎（同配方）vs P2 舊胎
- ✅ 計算 P1 是否能反超
- ✅ 評估 P2 的剩餘優勢

---

## 🔧 核心實現

### 新增方法

#### `_get_compound_degradation_rate(compound, tyre_age) -> float`
計算輪胎的即時衰退速度（秒/圈）

```python
# 二次方程式模型
degradation(t) = base_rate * t + 0.5 * acceleration * t²

# 即時衰退速度（導數）
rate = base_rate + acceleration * tyre_age
```

**範例輸出**：
- Bahrain SOFT age=15: 0.2048 s/lap
- Bahrain MEDIUM age=5: 0.1192 s/lap
- Monaco MEDIUM age=20: 0.1262 s/lap

#### `_calculate_new_tyre_advantage(new_compound, old_compound, old_tyre_age) -> float`
計算新胎相對於舊胎的速度優勢（秒/圈）

**計算公式**：
```python
advantage = (old_tyre_rate - new_tyre_rate) + (old_grip - new_grip)
```

**組成部分**：
1. **衰退優勢**：舊胎衰退更嚴重 → 正值
2. **配方優勢**：
   - SOFT: -0.5s (最快)
   - MEDIUM: -0.25s
   - HARD: 0.0s (基準)

**範例計算**：
```
New SOFT(age=1) vs Old SOFT(age=15):
  Degradation: 0.2048 - 0.1558 = +0.0490 s/lap (舊胎慢)
  Grip: -0.50 - (-0.50) = 0.00 s/lap (同配方無差異)
  Total: +0.0490 s/lap (新胎優勢)
```

---

## 📊 測試結果

### 測試 1: Bahrain（高衰退賽道）
**情境**：P1 SOFT(age=15) vs P2 MEDIUM(age=5), Gap: 5.0s, Lap 40/57

| 策略 | 可行性 | 每圈優勢 | 總優勢 | 說明 |
|------|--------|----------|--------|------|
| 1. 繼續當前輪胎 | ❌ | +0.0856 s | +1.46s | 剩餘圈數不足 |
| 2. 立即進站 | ❌ | +0.0490 s | -20.22s | 進站損失過大 |
| 3. 等待安全車 | ✅ | +0.0665 s | +10.73s | SC 節省 10s |
| 4. 主動進站 | ❌ | +0.0560 s | -20.16s | 進站損失過大 |
| 5. P1 先進站 | ❌ | +0.2134 s | -12.37s | 剩餘圈數不足 |

**關鍵發現**：
- P2 的 MEDIUM(age=5) 已經比 P1 的 SOFT(age=15) 快 0.0856 s/lap
- 策略 3（等待 SC）唯一可行，因為 SC 節省 10s 進站損失

### 測試 2: Monaco（低衰退賽道）
**情境**：P1 MEDIUM(age=20) vs P2 MEDIUM(age=10), Gap: 3.0s, Lap 50/78

| 策略 | 可行性 | 每圈優勢 | 總優勢 | 說明 |
|------|--------|----------|--------|------|
| 1. 繼續當前輪胎 | ❌ | +0.0100 s | +0.28s | 優勢太小 |
| 2. 立即進站 | ❌ | +0.0190 s | -20.99s | 進站損失過大 |
| 3. 等待安全車 | ✅ | +0.0240 s | +11.03s | SC 節省 10.5s |

**關鍵發現**：
- Monaco 低衰退賽道，輪胎齡差異影響較小（只有 0.01 s/lap）
- 策略 3 依然是唯一可行選項

---

## 🎯 與 Driver Strategy 的一致性

**完全對齊**：
1. ✅ 相同的二次方程式衰退模型
2. ✅ 相同的配方抓地力優勢 (`grip_advantage`)
3. ✅ 相同的賽道數據庫（24 circuits）
4. ✅ 相同的計算邏輯

**驗證範例**：
```
Driver Strategy: SOFT age=15 → 0.2048 s/lap
Chase Strategy:  SOFT age=15 → 0.2048 s/lap ✅ 完全一致
```

---

## 🔬 技術細節

### 配方抓地力優勢解釋
```python
grip_advantage = {'SOFT': -0.5, 'MEDIUM': -0.25, 'HARD': 0.0}
```

**負值 = 更快**：
- SOFT 比 HARD 快 0.5 秒/圈
- MEDIUM 比 HARD 快 0.25 秒/圈

**計算新胎 vs 舊胎**：
```python
grip_diff = old_grip - new_grip

# 範例：新 SOFT vs 舊 MEDIUM
# = (-0.25) - (-0.5) = +0.25 s/lap (SOFT 更快)
```

### 策略配方選擇邏輯
- **策略 2-3**：換與 P1 **相同配方**的新胎（undercut 策略）
- **策略 4**：用戶指定配方（靈活策略）
- **策略 5**：P1 換與自己**相同配方**的新胎

---

## 📈 實際案例分析

### 案例 1：舊 SOFT vs 新 MEDIUM（反直覺結果）
```
P2 換新 MEDIUM(age=1) vs P1 舊 SOFT(age=15):
  衰退優勢: +0.0936 s/lap (新胎衰退少)
  配方劣勢: -0.25 s/lap (SOFT 配方更快)
  總優勢: -0.1564 s/lap (負值 = 新 MEDIUM 更慢！)
```

**結論**：即使換新胎，MEDIUM 也追不上舊 SOFT（配方劣勢太大）

### 案例 2：同配方新胎優勢
```
P2 換新 SOFT(age=1) vs P1 舊 SOFT(age=15):
  衰退優勢: +0.0490 s/lap
  配方優勢: 0.00 s/lap (同配方)
  總優勢: +0.0490 s/lap (新胎更快)
```

**結論**：同配方換新胎有明顯優勢（但需考慮進站損失）

---

## 🚀 未來可能的改進

1. **動態配方選擇**：策略 2-3 可以考慮換更快配方（SOFT）而不是同配方
2. **Stint 平均優勢**：目前使用即時優勢，可以考慮整個 stint 的平均優勢
3. **溫度影響**：加入賽道溫度對衰退速度的影響
4. **進站時機優化**：策略 2 可以計算最佳進站圈數（不一定是立即）

---

## ✅ 總結

**成功整合**：
- ✅ 所有 5 個策略均使用精確輪胎衰退模型
- ✅ 完全與 Driver Strategy 對齊
- ✅ 賽道專屬數據（pit loss + tyre degradation）
- ✅ 配方專屬特性（SOFT/MEDIUM/HARD）
- ✅ 通過 Bahrain 和 Monaco 驗證測試

**用戶體驗改進**：
- 更準確的追趕預測
- 更真實的策略評估
- 更可靠的進站建議

**代碼質量**：
- 模組化設計（`_get_compound_degradation_rate`, `_calculate_new_tyre_advantage`）
- 可維護性高（統一數據庫）
- 可擴展性強（新增賽道/配方只需更新 JSON）
