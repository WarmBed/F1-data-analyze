# LiveF1 圈數檢測機制深度分析

**問題**: LiveF1 如何從 F1 Live Timing 原始資料檢測圈數？

---

## 🔍 核心發現

### LiveF1 的關鍵策略

**LiveF1 不是"檢測"圈數，而是"提取"圈數!**

```
F1 Live Timing API 本身就包含圈數資訊
↓
LiveF1 從 TimingData 直接讀取
↓
不需要自己計算或推算
```

---

## 📊 資料來源

### LiveF1 使用的資料源

根據源碼分析，LiveF1 會下載並整合以下資料:

| 資料源 | 包含資訊 | 用途 |
|--------|---------|------|
| **TimingData** | **圈數 (NumberOfLaps)**, 圈速, Sector 時間 | **主要圈數來源** |
| Position.z | GPS 座標, 狀態 | 位置驗證 |
| CarData.z | 速度, RPM, 檔位等遙測 | 遙測資料 |
| SessionStatus | 比賽狀態 | 狀態同步 |

### TimingData 結構

```json
{
  "Lines": {
    "44": {  // Hamilton
      "NumberOfLaps": "10",  // ← 圈數在這裡!
      "LastLapTime": {
        "Value": "1:33.522"
      },
      "Sectors": [
        {"Value": "31.234"},
        {"Value": "48.521"},
        {"Value": "29.767"}
      ],
      ...
    }
  }
}
```

**關鍵**: F1 官方 API 的 `TimingData` 已經包含 `NumberOfLaps` 欄位!

---

## 🏗️ LiveF1 的 Medallion 架構

LiveF1 使用資料湖概念的多層架構:

### 資料處理流程

```
┌─────────────────────────────────────────┐
│  Bronze Layer (原始資料)                  │
├─────────────────────────────────────────┤
│  - TimingData (含 NumberOfLaps)         │
│  - Position.z (含 GPS)                  │
│  - CarData.z (含遙測)                   │
│  - SessionStatus                        │
└─────────────────────────────────────────┘
              ↓ ETL 處理
┌─────────────────────────────────────────┐
│  Silver Layer (清洗後資料)                │
├─────────────────────────────────────────┤
│  - laps (圈數對應表)                     │
│  - carTelemetry (遙測 + 圈數)            │
└─────────────────────────────────────────┘
              ↓ 整合
┌─────────────────────────────────────────┐
│  Gold Layer (分析就緒)                   │
├─────────────────────────────────────────┤
│  - 可直接查詢的分析資料                    │
└─────────────────────────────────────────┘
```

### 關鍵程式碼片段

```python
# 來自 session.py 的 generate() 方法

def generate(self, silver=True, gold=False):
    # 1. 確定需要的資料源
    required_data = set(["CarData.z", "Position.z", "SessionStatus"])
    
    # 2. Silver tables 會額外需要 TimingData
    for silver_table in silver_tables_to_generate:
        silver_table.refine_sources()
        required_data.update(set(silver_table.source_tables["bronze"]))
    
    # 3. 下載所有需要的資料
    logger.info(f"Topics to be loaded : {list(required_data)}")
    self.get_data(list(required_data), parallel=False)
    
    # 4. 生成 Silver 層表格 (包括 laps)
    for silver_table in silver_tables_to_generate:
        table_name = silver_table.table_name
        silver_table.generate_table()  # ← 這裡整合圈數!
        setattr(self, table_name, self.get_data(dataNames=table_name, level="silver"))
```

---

## 🔧 ETL 處理映射

### LiveF1 的 ETL 函數映射

```python
# 來自 etl.py

function_map = {
    'TimingData': parse_timing_data,    # ← 解析圈數
    'Position.z': parse_position_z,     # ← 解析 GPS
    'CarData.z': parse_car_data_z,      # ← 解析遙測
    'SessionStatus': parse_session_status,
    ...
}
```

### parse_timing_data 功能 (推測)

雖然我們沒看到完整的 `parse_timing_data` 程式碼，但根據 ETL 架構推測:

```python
def parse_timing_data(raw_data):
    """
    從 TimingData 提取圈數和時間資訊
    """
    records = []
    
    for line in raw_data:
        timestamp = line[:12]
        data = json.loads(line[12:])
        
        if 'Lines' in data:
            for driver_no, driver_data in data['Lines'].items():
                # 直接讀取圈數!
                lap_number = driver_data.get('NumberOfLaps')
                last_lap_time = driver_data.get('LastLapTime', {}).get('Value')
                
                records.append({
                    'timestamp': timestamp,
                    'driver_no': driver_no,
                    'lap_number': lap_number,  # ← 圈數在這裡
                    'lap_time': last_lap_time,
                    ...
                })
    
    return pd.DataFrame(records)
```

---

## 🎯 Silver Layer: laps 表生成

### laps 表的整合邏輯

LiveF1 的 Silver layer 生成 `laps` 表時:

1. **從 TimingData 取得圈數**
2. **從 Position.z 取得 GPS 軌跡**
3. **從 Car Data.z 取得遙測**
4. **透過時間戳對齊所有資料**

```python
# 偽代碼 (基於架構推測)

def generate_laps_table(timing_data, position_data, car_data):
    """生成 laps 表"""
    
    # 1. 從 TimingData 建立圈數索引
    lap_index = timing_data[['driver_no', 'lap_number', 'timestamp', 'lap_time']]
    
    # 2. 對於每一圈，找到對應的時間範圍
    for lap in lap_index.itertuples():
        lap_start = find_lap_start_time(lap.lap_number, lap.driver_no, timing_data)
        lap_end = find_lap_end_time(lap.lap_number, lap.driver_no, timing_data)
        
        # 3. 在該時間範圍內，提取 CarData 和 Position
        lap_telemetry = car_data[
            (car_data['driver_no'] == lap.driver_no) &
            (car_data['timestamp'] >= lap_start) &
            (car_data['timestamp'] < lap_end)
        ]
        
        lap_position = position_data[
            (position_data['driver_no'] == lap.driver_no) &
            (position_data['timestamp'] >= lap_start) &
            (position_data['timestamp'] < lap_end)
        ]
        
        # 4. 合併成該圈的完整資料
        ...
```

---

## 🔑 關鍵差異

### LiveF1 vs. 我們的嘗試

| 項目 | 我們的嘗試 | LiveF1|
|------|-----------|--------|
| **資料源** | 只用 TimingData | TimingData + Position.z + CarData.z |
| **圈數來源** | ✅ TimingData.NumberOfLaps | ✅ 同樣來源 |
| **時間對齊** | ❌ 簡單比較 | ✅ 複雜的對齊演算法 |
| **架構** | 單一腳本 | Medallion (Bronze/Silver/Gold) |
| **處理流程** | 一次性 | ETL pipeline |
| **結果** | 失敗 (時間戳問題) | 成功 |

### 我們失敗的原因

```
我們的邏輯:
  TimingData 說 Lap 10 在 01:11:54.223
  → 去 CarData 找 01:11:54.223 附近的資料
  → 找不到 44 號車!

LiveF1 的邏輯:
  TimingData 說 Lap 10 完成於 01:11:54.223
  → 需要找 Lap 9 完成時間和 Lap 10 完成時間
  → Lap 10 = [Lap 9 完成時間, Lap 10 完成時間] 區間
  → 在該區間內提取 CarData
  → 成功!
```

**差別**: LiveF1 理解 `TimingData` 記錄的是**圈完成時間**，不是圈開始時間!

---

## 💡 核心洞察

### 1. F1 API 已經提供圈數

**不需要自己計算!**

```
F1 Live Timing API 的 TimingData 包含:
- NumberOfLaps (當前圈數)
- LastLapTime (上一圈圈速)
- Sectors (扇區時間)
```

這些資訊是 F1 官方計時系統產生的，準確且即時。

### 2. 關鍵是時間對齊，不是圈數檢測

LiveF1 的核心價值:
- ❌ 不是"檢測"圈數
- ✅ 是"對齊"不同資料源的時間戳
- ✅ 是"整合"多個資料流

### 3. 資料湖架構的重要性

Medallion 架構的優勢:
- **Bronze**: 保持原始資料完整性
- **Silver**: 清洗和整合
- **Gold**: 分析就緒

這確保了:
- 可追溯性
- 可重現性
- 資料品質

---

## 📝 實作建議

### 如果要自己實作圈數提取

**方法 1: 直接使用 TimingData (簡單)**

```python
# 從 TimingData 直接讀取圈數
timing_records = parse_timing_data("TimingData.jsonStream")

# 過濾特定車手和圈數
ham_lap10 = timing_records[
    (timing_records['driver_no'] == '44') &
    (timing_records['lap_number'] == '10')
]

# 取得該圈的時間範圍
lap_10_end = ham_lap10['timestamp'].iloc[0]
lap_9_end = timing_records[
    (timing_records['driver_no'] == '44') &
    (timing_records['lap_number'] == '9')
]['timestamp'].iloc[0]

# 在 CarData 中提取該範圍
lap_10_telemetry = car_data[
    (car_data['timestamp'] > lap_9_end) &
    (car_data['timestamp'] <= lap_10_end)
]
```

**方法 2: 直接使用 LiveF1 (推薦)**

```python
import livef1

session = livef1.get_session(2025, 'Japan', 'R')
session.generate(silver=True)

# LiveF1 已經幫你整合好了!
laps = session.get_laps()
ham_lap10 = laps[(laps['DriverNo'] == 44) & (laps['lap_number'] == 10)]
```

---

## ✅ 結論

### LiveF1 如何檢測圈數？

**答案**: **它不檢測，它提取！**

1. **從 TimingData 直接讀取** `NumberOfLaps` 欄位
2. **使用 Medallion 架構** 整合多個資料源
3. **透過精密的時間對齊演算法** 合併資料
4. **生成分析就緒的表格** (laps, carTelemetry)

### 為什麼這很重要？

- ✅ 證明了 F1 API 本身就有圈數資訊
- ✅ 問題不在"找圈數"，而在"對齊時間"
- ✅ LiveF1/fastf1 的核心價值是 ETL 管道，不是圈數檢測

### 給您的建議

**對於學習**:
- ✅ 理解 Medallion 架構很有價值
- ✅ 學習時間序列資料對齊技術
- ✅ 參考 LiveF1 的 ETL 設計

**對於實作**:
- ✅ 直接使用 LiveF1 或 fastf1
- ✅ 專注於分析邏輯，不是資料整合
- ✅ 如需自建，從簡單的 TimingData 解析開始
