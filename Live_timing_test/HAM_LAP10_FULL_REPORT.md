# HAM Lap 10 完整資料分析

**車手**: Lewis Hamilton (44號)  
**比賽**: 2025 日本站 (Suzuka) 正賽  
**圈數**: Lap 10  
**來源**: fastf1 (F1 Live Timing API)

---

## 📊 核心資料

### 基本資訊

```
圈速: 1分33.522秒
圈開始時間: 1:10:20.486 (比賽開始後)
總資料點: 714 個
平均採樣率: ~7.6 Hz (每秒 7-8 個資料點)
```

---

## 🏎️ 遙測資料統計

### 速度 (Speed)

| 項目 | 數值 |
|------|------|
| **資料點數** | 714 |
| **最小速度** | 69 km/h (Spoon 彎) |
| **最大速度** | 309 km/h (主直道) |
| **平均速度** | 222.7 km/h |
| **中位數速度** | 228.9 km/h |

**分析**: 
- Suzuka 主直道最高速達 **309 km/h**
- 最慢點在 Spoon 彎 (**69 km/h**),這是賽道上最慢的彎角
- 平均速度 222.7 km/h 顯示這是一條高速賽道

### RPM (引擎轉速)

| 項目 | 數值 |
|------|------|
| **最小 RPM** | 5,187 |
| **最大 RPM** | 12,006 |
| **平均 RPM** | 10,267 |

**分析**:
- 引擎大部分時間保持在 **10,000+ RPM** 高轉區
- 最高轉速 12,006 RPM 接近 F1 引擎極限
- 低轉區 (5,187 RPM) 出現在慢速彎

### 檔位分佈 (nGear)

| 檔位 | 資料點數 | 百分比 |
|------|---------|--------|
| 3 檔 | 79 | 11.1% |
| 4 檔 | 56 | 7.8% |
| 5 檔 | 135 | 18.9% |
| **6 檔** | **174** | **24.4%** ← 最常用 |
| 7 檔 | 141 | 19.7% |
| 8 檔 | 129 | 18.1% |

**分析**:
- **6檔**使用最頻繁 (24.4%),Suzuka 中速彎多
- 8檔 (18.1%) 主要在主直道使用
- 3-4檔 (18.9%) 在 Spoon、Degner 等慢速彎

### 油門 (Throttle)

| 項目 | 數值 |
|------|------|
| **平均油門開度** | 72.1% |
| **全油門 (100%) 次數** | 45 個資料點 |
| **全油門比例** | 6.3% |

**分析**:
- 平均 72.1% 油門開度顯示這圈**節奏流暢**
- 全油門僅佔 6.3%,說明 Suzuka 需要**精準油門控制**
- 大部分時間處於部分油門 (70-90%)

### 煞車 (Brake)

| 項目 | 數值 |
|------|------|
| **煞車點數量** | 133 個資料點 |
| **煞車時間比例** | 18.6% |

**分析**:
- 18.6% 時間在煞車,符合 Suzuka 的技術彎道特性
- 主要煞車點: 
  - Turn 1 (髮夾彎)
  - Spoon 彎
  - Casio三角

---

## 📈 資料樣本

### 圈開始 (前 10 筆)

```
時間    速度   RPM   檔位  油門   煞車
0.00s   269   10879   7    99.3    0
0.06s   269   10907   7    99.2    0
0.13s   270   10937   7    99.0    0
0.24s   273   10986   7    99.0    0
0.29s   274   11008   7    99.0    0
```

**觀察**: 圈開始時已在 **7檔**, 速度 **269-274 km/h**, 全油門通過

### 圈結束 (最後 10 筆)

```
時間    速度   RPM   檔位  油門   煞車
92.49s  255   11662   6    99.0    0
92.68s  259   11229   6    99.0    0
93.02s  264   10804   6    99.0    0
93.09s  265   10718   7    99.0    0
93.52s  270   10829   7    99.0    0
```

**觀察**: 圈結束時加速中,從 **6檔換至7檔**, 速度 **255→270 km/h**

---

## 🔍 關鍵發現

### 1. Suzuka 賽道特性體現

- **高速賽道**: 平均速度 222.7 km/h
- **技術性彎道多**: 6檔使用最頻繁 (不是7/8檔)
- **需精準控制**: 煞車比例 18.6%,油門平均 72.1%

### 2. Hamilton 的駕駛風格

- **流暢**: 油門開度穩定在 70-99% 區間
- **精準**: 全油門僅 6.3%,避免輪胎過度磨損
- **節奏感**: 從資料點分佈看,沒有突兀的動作

### 3. 資料品質

- ✅ **714 個資料點**,平均 ~130ms 一筆 (高頻率)
- ✅ **無異常值**,速度範圍 69-309 km/h 合理
- ✅ **完整性**: 包含 Speed, RPM, Gear, Throttle, Brake, DRS 等所有Channel

---

## 📂 資料檔案

### CSV 輸出

完整遙測資料已儲存至:
```
Live_timing_test/HAM_Lap10_telemetry.csv
```

**包含欄位** (18個):
```
Date, SessionTime, DriverAhead, DistanceToDriverAhead,
Time, RPM, Speed, nGear, Throttle, Brake, DRS,
Source, Distance, RelativeDistance, Status, X, Y, Z
```

### 使用範例

```python
import pandas as pd

# 讀取資料
df = pd.read_csv('HAM_Lap10_telemetry.csv')

# 繪製速度曲線
import matplotlib.pyplot as plt
plt.plot(df['Time'], df['Speed'])
plt.xlabel('Time (s)')
plt.ylabel('Speed (km/h)')
plt.title('HAM Lap 10 Speed Trace')
plt.show()
```

---

## 🎯 與 LiveTiming 原始資料比較

| 面向 | LiveTiming (原始) | fastf1 (處理後) |
|------|-------------------|-----------------|
| **Lap 10 識別** | ❌ 需手動整合 TimingData | ✅ 自動對應 |
| **資料點數** | 無法提取 | **714 點** |
| **速度範圍** | 包含異常值 (4000+ km/h) | 69-309 km/h (已清理) |
| **資料結構** | 巢狀 JSON | Pandas DataFrame |
| **額外資訊** | 需額外下載 Position.z | 已整合 (X, Y, Z 座標) |
| **使用難度** | 複雜 | 簡單 (10行程式碼) |

---

## 💡 應用建議

### 1. 速度分析

```python
# 找出最快/最慢的區段
max_speed_idx = df['Speed'].idxmax()
min_speed_idx = df['Speed'].idxmin()

print(f"最快點: {df.loc[max_speed_idx, 'Speed']} km/h at {df.loc[max_speed_idx, 'Time']}")
print(f"最慢點: {df.loc[min_speed_idx, 'Speed']} km/h at {df.loc[min_speed_idx, 'Time']}")
```

### 2. 煞車分析

```python
# 找出所有煞車點
brake_points = df[df['Brake'] > 0]
print(f"煞車次數: {len(brake_points)}")
```

### 3. 檔位最佳化

```python
# 分析每個檔位的速度分佈
for gear in df['nGear'].unique():
    gear_data = df[df['nGear'] == gear]
    print(f"檔位 {gear}: 平均速度 {gear_data['Speed'].mean():.1f} km/h")
```

### 4. InfluxDB 整合

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# 寫入 InfluxDB
client = InfluxDBClient(url="http://localhost:8086", token="your-token", org="your-org")
write_api = client.write_api(write_options=SYNCHRONOUS)

for _, row in df.iterrows():
    point = Point("f1_telemetry") \
        .tag("driver", "HAM") \
        .tag("lap", "10") \
        .field("speed", row['Speed']) \
        .field("rpm", row['RPM']) \
        .field("throttle", row['Throttle']) \
        .time(row['SessionTime'])
    
    write_api.write(bucket="f1-data", record=point)
```

---

## ✅ 總結

### HAM Lap 10 資料點數量: **714 個**

**包含資訊**:
- ✅ 速度 (每個資料點)
- ✅ RPM (每個資料點)
- ✅ 檔位 (每個資料點)
- ✅ 油門開度 (每個資料點)
- ✅ 煞車狀態 (每個資料點)
- ✅ GPS 座標 (X, Y, Z)
- ✅ DRS 狀態
- ✅ 時間戳 (相對/絕對)

**資料品質**: 優秀 (無異常值,完整性高)

**取得方式**: fastf1 (極簡,10行程式碼)

**建議下一步**:
1. 視覺化速度曲線
2. 與其他車手比較 (如 VER, LEC)
3. 整合至 InfluxDB 做時序分析
4. 建立 Dashboard 即時監控
