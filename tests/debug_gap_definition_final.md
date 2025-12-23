# Gap Trend 定義混亂問題

## 問題診斷

有**兩種不同的 Gap 定義**混在一起了：

### 1. DataManager 的 gap_trend（Live Timing 用）
```python
# gap_seconds = gap_to_ahead （對前車的距離，永遠正值）
gap_trend = 當前圈 gap_to_ahead - 上一圈 gap_to_ahead

# 例子：NOR (P3) 追 VER (P1)
# Lap 17: gap_to_ahead = 5.0s
# Lap 18: gap_to_ahead = 4.5s
# gap_trend = 4.5 - 5.0 = -0.5 s/lap （負值 = 追近）✅
```

### 2. 驗證腳本的 gap（相對位置）
```python
# gap = p1_gap_to_leader - p2_gap_to_leader
# 正值 = P1 落後 P2
# 負值 = P1 領先 P2

# 例子：TSU (P1) vs NOR (P2)
# Lap 17: TSU gap_to_leader=22.125, NOR gap_to_leader=26.980
# gap = 22.125 - 26.980 = -4.855s （TSU 領先）

# Lap 18: TSU gap_to_leader=23.167, NOR gap_to_leader=27.782
# gap = 23.167 - 27.782 = -4.615s （TSU 領先，優勢縮小）
# gap_trend = -4.615 - (-4.855) = +0.24 s/lap
```

## 矛盾點

**Lap 18 的 gap_trend = +0.24 s/lap**：
- 用驗證腳本的定義：Gap 從 -4.855 變成 -4.615（絕對值變小）
  - TSU 的領先優勢縮小
  - **NOR 正在追近** ✅
  
- 但 trend_advantage = -gap_trend = -0.24 s/lap（負值）
  - 表示「P2 沒有優勢」？
  - **錯誤！** ❌

## 正確的修正

驗證腳本應該：
1. **不計算相對 gap**
2. **直接計算 P2 對 P1 的 gap_to_ahead**
3. 這樣 gap_trend 才會符合 Chase Strategy 的定義

```python
# 正確方式
p2_gap_to_p1 = |p2_gap_to_leader - p1_gap_to_leader|
gap_trend = 當前圈 p2_gap_to_p1 - 上一圈 p2_gap_to_p1

# Lap 17: p2_gap_to_p1 = 4.855s
# Lap 18: p2_gap_to_p1 = 4.615s
# gap_trend = 4.615 - 4.855 = -0.24 s/lap （負值 = NOR 追近）✅
# trend_advantage = -(-0.24) = +0.24 s/lap （正值 = NOR 有優勢）✅
```
