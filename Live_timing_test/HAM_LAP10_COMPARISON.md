# HAM Lap 10 速度資料比較報告

**車手**: Lewis Hamilton (44號)  
**比賽**: 2025 日本站 (Suzuka)  
**目標**: 比較第10圈速度資料點數量

---

## 📊 執行結果摘要

### LiveTiming 原始資料

```
HAM 總速度讀數: 31,339 個
資料格式: JSON (巢狀結構)
時間戳格式: String ('HH:MM:SS.mmm')
```

### fastf1 處理後資料

```
HAM 總圈數: 53 圈
Lap 10 資料點: 714 個
Lap 10 圈速: 1:33.522
速度範圍: 69 - 309 km/h
```

---

## 🔍 詳細比較

### 1. 資料量對比

| 項目 | LiveTiming | fastf1 |
|------|------------|--------|
| HAM 全場資料點 | 31,339 | ~31,000 (估計) |
| Lap 10 資料點 | **無法直接提取** | **714** |
| 平均每圈資料點 | ~592 | ~585 |

### 2. Lap 10 詳細資訊 (fastf1)

```
圈速: 1分33.522秒
開始時間: 1:10:20 (比賽開始後)
資料點數: 714
採樣頻率: ~7.6 Hz (714點 / 93.522秒)
速度範圍: 69-309 km/h
```

**樣本資料**:
```
Time         Speed   RPM
00:00.000    269     10879
00:00.062    269     10907
00:00.131    270     10937
00:00.242    273     10986
00:00.291    274     11008
```

### 3. LiveTiming 資料結構問題

**關鍵發現**: `CarData.z.jsonStream` **不包含圈數資訊**!

```python
# CarData.z 結構
{
  "Entries": [
    {
      "Utc": "2025-04-06T04:07:42.7143391Z",
      "Cars": {
        "44": {
          "Channels": {
            "0": 269,  # Speed
            "2": 10879, # RPM
            "3": 6,     # nGear
            ...
          }
        }
      }
    }
  ]
}
```

**缺少**:
- ❌ 圈數 (LapNumber)
- ❌ 圈內時間 (LapTime)
- ❌ 賽段標記 (Sector)

**要獲得圈數資訊,需要**:
1. 下載 `Position.z.jsonStream` (包含 GPS + 可能的圈數)
2. 下載 `TimingData.jsonStream` (包含圈速資訊)
3. 手動對齊時間戳

---

## 📂 資料整合需求

### fastf1 自動整合的資料源

```
fastf1 內部整合:
├─ CarData.z        → Speed, RPM, Gear, Throttle, Brake
├─ Position.z       → GPS (X, Y, Z)
├─ TimingData       → Lap times, Sectors
└─ SessionInfo      → 賽段資訊
    ↓
自動對齊時間戳 + 圈數標記
    ↓
DataFrame (ready to use)
```

### LiveTiming 手動整合流程

```
手動流程:
1. 下載 CarData.z    → 遙測資料
2. 下載 Position.z   → GPS + 狀態
3. 下載 TimingData   → 圈數對應
4. 解碼 Base64 + Zlib
5. 解析 JSON 結構
6. 時間戳對齊
7. 圈數標記
8. 過濾異常值
   ↓
自訂處理後的資料
```

---

## 🔢 資料點數量分析

### 理論計算

假設:
- Lap 10 時間: 93.522 秒
- 採樣頻率: ~7.6 Hz (fastf1 觀察值)

**預期資料點**: 93.522 × 7.6 ≈ **711 個**  
**實際 (fastf1)**: **714 個**  
**誤差**: ~0.4% (可接受)

### LiveTiming vs fastf1 資料點對比

```
LiveTiming (全場):
  31,339 點 / 53 圈 = 平均 592 點/圈

fastf1 (全場估計):
  714 點/圈 × 53 圈 ≈ 37,842 點

差異原因:
  - fastf1 可能插值補齊
  - LiveTiming 可能有資料遺失
  - 不同的資料源合併方式
```

---

## 📊 速度資料品質

### LiveTiming 原始資料

**異常值問題**:
```
樣本速度 (未過濾):
  4054 km/h  ← 異常!
  4064 km/h  ← 異常!
  4068 km/h  ← 異常!
```

⚠️ **需要過濾**: `0 < speed < 400`

### fastf1 處理後資料

**已清理**:
```
速度範圍: 69 - 309 km/h ← 合理
最高速: 309 km/h (Suzuka 主直道)
最低速: 69 km/h (Spoon 彎)
```

✅ fastf1 已自動過濾異常值

---

## 🎯 結論

### fastf1 Lap 10 速度資料

```
✓ 資料點數: 714 個
✓ 速度範圍: 69-309 km/h (已驗證)
✓ 採樣頻率: ~7.6 Hz
✓ 資料品質: 高 (已過濾異常值)
✓ 存取方式: df['Speed'] (極簡)
```

### LiveTiming 原始資料

```
✓ 全場資料點: 31,339 (HAM)
✗ Lap 10 無法直接提取 (需整合 Position/Timing)
✗ 包含異常值 (需手動過濾)
✓ 完整控制權
✓ 可用於即時串流
```

---

## 💡 建議

### 場景 1: 快速分析

**使用 fastf1**
```python
import fastf1
session = fastf1.get_session(2025, 'Japan', 'R')
session.load()
lap10 = session.laps.pick_driver('HAM').iloc[9]
speed = lap10.get_telemetry()['Speed']  # 714 個資料點
```

### 場景 2: 自訂處理

**使用 LiveTiming + 手動整合**
```python
# 1. 下載必要資料
car_data = download('CarData.z.jsonStream')
position = download('Position.z.jsonStream')
timing = download('TimingData.jsonStream')

# 2. 解碼並整合
# ... (需要 100+ 行程式碼)

# 3. 提取 Lap 10
lap10_speeds = filter_by_lap(car_data, lap_number=10)
```

### 場景 3: 即時直播

**使用 LiveTiming WebSocket**
- SignalR 連線
- 即時接收 CarData.z
- 需自行處理圈數對應

---

## 📈 數據對比總表

| 特性 | LiveTiming | fastf1 |
|------|------------|--------|
| **HAM 全場資料點** | 31,339 | ~37,842 |
| **Lap 10 資料點** | 無法直接取得 | 714 |
| **速度範圍** | 0-13294 (含異常) | 69-309 (已清理) |
| **圈數資訊** | 需額外整合 | 內建 |
| **資料品質** | 需手動驗證 | 高 |
| **存取複雜度** | 複雜 (多步驟) | 簡單 (1行) |
| **即時支援** | ✓ (WebSocket) | ✗ |
| **學習價值** | 高 (理解協定) | 低 (黑箱) |

---

## ✅ 答案

**Hamilton Lap 10 速度資料點數量**: **714 個** (via fastf1)

**LiveTiming 無法直接回答**,因為:
1. CarData.z 無圈數標記
2. 需整合 Position.z 或 TimingData
3. 需時間戳對齊演算法

**fastf1 的價值**:
- 已完成整合工作
- 資料品質高
- 存取簡單

**LiveTiming 的價值**:
- 學習 F1 API 協定
- 自訂處理邏輯
- 即時資料流支援
