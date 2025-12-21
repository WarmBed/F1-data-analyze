# F120 數據異常診斷報告

**報告日期**: 2025-12-13  
**問題分類**: 彎道採樣點定位錯誤  
**嚴重等級**: 🔴 高（影響所有車手數據有效性）

---

## 🔍 異常數據案例

### 案例 1: ANT - T6 (低速彎)
```json
{
  "median_speed": 110.0 km/h,      // ❌ 中位數 110 不符合低速彎定義 (<100)
  "min_speed": 69.3 km/h,          // ✅ 最小值符合
  "max_speed": 282.0 km/h,         // ❌ 出現高速直線速度！
  "cv": 49.93%,                    // ❌ 變異係數 50% 極度異常
  "speeds_raw": [88.3, 69.3, 70.8, 86.0, 76.0, 282.0, 151.0, 110.0, 151.0, ...]
  //                                              ^^^^  ^^^^       ^^^^
  //                                              直線速度混入！
}
```

### 案例 2: ALO - T7 (中速彎)
```json
{
  "median_speed": 95.0 km/h,       // ✅ 符合中速彎定義
  "min_speed": 58.0 km/h,          // ❌ 出現低速彎速度
  "max_speed": 120.4 km/h,         // ⚠️  過高（接近直線）
  "cv": 22.93%,                    // ❌ 變異過大
  "speeds_raw": [99.0, 59.0, 97.0, 66.0, 120.4, 58.0, 62.0, ...]
  //                   ^^^^       ^^^^  ^^^^^  ^^^^  ^^^^
  //                   異常低速混入
}
```

### 案例 3: ALO - T8 (高速彎)
```json
{
  "median_speed": 236.73 km/h,     // ✅ 符合高速彎定義
  "min_speed": 97.25 km/h,         // ❌ 出現減速段速度
  "max_speed": 252.72 km/h,        // ✅ 符合
  "cv": 26.57%,                    // ❌ 變異過大
  "speeds_raw": [237.5, 142.9, 245.0, 135.0, 252.7, 97.25, ...]
  //                    ^^^^^        ^^^^^        ^^^^^
  //                    減速段混入
}
```

---

## 🎯 根本原因分析

### 問題 1: **採樣容差過大**
**當前實現** (`_get_speed_at_distance` 方法):
```python
# 策略 1: 標準容差 ±10m
nearby = telemetry[
    (telemetry['Distance'] >= target_distance - tolerance) &  # ±10m
    (telemetry['Distance'] <= target_distance + tolerance)
]

# 策略 2: 擴大容差 ±15m, ±20m
for extended_tolerance in [15, 20]:  # ❌ 容差過大
    nearby = telemetry[...]
```

**問題**:
- ±20m 的容差在低速彎道會跨越多個賽道階段
- 例如：T6 apex_distance = 2627.3m，容差 ±20m 覆蓋 2607-2647m 範圍
- 這範圍可能包含：減速段 → apex → 加速段 → 直線

**數據證據**:
- ANT T6: 出現 282 km/h（明顯是直線加速段）
- ALO T7: 出現 58 km/h（明顯是減速段）
- ALO T8: 出現 97 km/h（明顯是入彎減速）

---

### 問題 2: **線性插值不適用於彎道**
**當前實現**:
```python
# 策略 3: 線性插值
if distance_gap > 30:  # ❌ 30m 太大
    return None

interpolated_speed = speed_before + \
    (speed_after - speed_before) * \
    (target_distance - dist_before) / (dist_after - dist_before)
```

**問題**:
- 彎道速度變化非線性（加速度變化劇烈）
- 在 30m 距離內進行線性插值會產生錯誤速度

---

### 問題 3: **未使用最小速度採樣**
**當前實現**:
```python
closest_idx = (nearby['Distance'] - target_distance).abs().idxmin()
return float(nearby.loc[closest_idx, 'Speed'])  # ❌ 只取最接近的一個點
```

**應該使用** (參考 `_calculate_corner_average_speed`):
```python
apex_speed = apex_tel['Speed'].min()  # ✅ 取範圍內的最小速度
```

---

## 📊 影響範圍

### 受影響車手統計
- **ANT**: T6 CV=49.93% (極度異常)
- **ALO**: T6 CV=13.18%, T7 CV=22.93%, T8 CV=26.57%
- **NOR**: (需檢查)
- **OCO**: (需檢查)
- **PIA**: (需檢查)

### 數據可信度評估
| 車手 | T6 (低速) | T7 (中速) | T8 (高速) | 整體評分 |
|------|-----------|-----------|-----------|----------|
| ANT  | ❌ 不可信 | ⚠️  可疑   | ⚠️  可疑   | 30%      |
| ALO  | ⚠️  可疑   | ❌ 不可信 | ❌ 不可信 | 20%      |
| VER  | ✅ 正常   | ✅ 正常   | ✅ 正常   | 95%      |

---

## 🔧 修復方案

### 方案 A: **收緊容差 + 最小速度採樣** (推薦)
```python
def _get_speed_at_distance(self, telemetry: pd.DataFrame,
                           target_distance: float,
                           tolerance: float = 5) -> Optional[float]:  # ✅ 收緊至 ±5m
    """獲取彎道 apex 速度（使用最小速度採樣）"""
    try:
        # 策略 1: 嚴格容差範圍內取最小速度
        nearby = telemetry[
            (telemetry['Distance'] >= target_distance - tolerance) &
            (telemetry['Distance'] <= target_distance + tolerance)
        ]
        
        if not nearby.empty:
            return float(nearby['Speed'].min())  # ✅ 取最小速度而非最接近點
        
        # 策略 2: 適度擴大容差（最多 ±10m）
        for extended_tolerance in [7, 10]:  # ✅ 不超過 10m
            nearby = telemetry[
                (telemetry['Distance'] >= target_distance - extended_tolerance) &
                (telemetry['Distance'] <= target_distance + extended_tolerance)
            ]
            if not nearby.empty:
                return float(nearby['Speed'].min())  # ✅ 取最小速度
        
        # 策略 3: 移除線性插值（不可靠）
        return None  # ❌ 找不到就放棄，不進行插值
        
    except Exception:
        return None
```

### 方案 B: **使用 Speed.min() 範圍採樣** (最保守)
```python
def _get_speed_at_distance(self, telemetry: pd.DataFrame,
                           target_distance: float,
                           window_size: float = 10) -> Optional[float]:
    """獲取彎道 apex 速度（固定窗口最小值）"""
    try:
        # 固定窗口：±10m 範圍內取最小速度
        window = telemetry[
            (telemetry['Distance'] >= target_distance - window_size) &
            (telemetry['Distance'] <= target_distance + window_size)
        ]
        
        if window.empty:
            return None
        
        return float(window['Speed'].min())  # ✅ 絕對最小速度
        
    except Exception:
        return None
```

---

## ✅ 修復後預期效果

### ANT T6 修復後預測
```json
// 當前（錯誤）
{
  "median_speed": 110.0,
  "min_speed": 69.3,
  "max_speed": 282.0,  // ❌ 異常
  "cv": 49.93%         // ❌ 異常
}

// 修復後（預期）
{
  "median_speed": 68.0,     // ✅ 符合低速彎定義
  "min_speed": 69.3,
  "max_speed": 88.3,        // ✅ 移除直線速度
  "cv": < 10%               // ✅ 正常變異
}
```

### ALO T7 修復後預測
```json
// 當前（錯誤）
{
  "median_speed": 95.0,
  "min_speed": 58.0,   // ❌ 異常低
  "max_speed": 120.4,  // ❌ 異常高
  "cv": 22.93%         // ❌ 異常
}

// 修復後（預期）
{
  "median_speed": 97.0,     // ✅ 符合中速彎
  "min_speed": 95.0,        // ✅ 移除減速段
  "max_speed": 103.4,       // ✅ 移除加速段
  "cv": < 8%                // ✅ 正常變異
}
```

---

## 🚀 執行計畫

### 階段 1: 代碼修復 (預計 15 分鐘)
- [ ] 修改 `_get_speed_at_distance` 方法
  - 收緊容差至 ±5m (default), 最大 ±10m
  - 使用 `Speed.min()` 取代 `closest_idx`
  - 移除線性插值策略
- [ ] 修改 `_calculate_corner_average_speed` 方法
  - 統一使用 ±5m 容差

### 階段 2: 測試驗證 (預計 10 分鐘)
- [ ] 重新執行 F120: `python f1_analysis_modular_main.py -f 120 -y 2025 -r "Abu Dhabi" -s FP2`
- [ ] 檢查 ANT T6 是否移除 282 km/h 異常值
- [ ] 檢查 ALO T7/T8 變異係數是否降至 <10%
- [ ] 驗證所有車手 CV 值在合理範圍 (<15%)

### 階段 3: 視覺化更新 (預計 5 分鐘)
- [ ] 重新生成 Box Plot 圖表
- [ ] 確認異常值消失

---

## 📝 結論

**問題根源**: 
- 彎道採樣容差過大 (±20m)
- 未使用最小速度採樣
- 線性插值不適用於彎道

**修復優先級**: 🔴 **極高** (影響所有分析結果有效性)

**預期修復時間**: 30 分鐘

**驗證標準**: 
- ✅ 所有車手 CV < 15%
- ✅ 速度範圍符合彎道類型定義
- ✅ 無明顯異常值混入
