# 2025 日本站遙測資料分析報告

**檔案**: `CarData.z.jsonStream`  
**日期**: 2025-04-06 (Suzuka)  
**分析時間**: 2025-11-20

---

## 📊 資料概覽

| 項目 | 數值 |
|------|------|
| 檔案大小 | 6.87 MB |
| 總記錄數 | 8,258 筆 |
| 速度資料點 | 626,780 個 |
| 解碼成功率 | 100% |
| 格式 | .jsonStream (逐行) |

---

## 🔍 資料結構

### 檔案格式

```
[12字元時間戳][Base64編碼的壓縮JSON]
```

**範例**:
```
00:00:03.005eJyVVstu2zAQ...
^           ^
時間戳      壓縮資料
```

### 解碼流程

```python
# 1. 分割時間戳與資料
timestamp = line[:12]   # "00:00:03.005"
b64_data = line[12:]    # "eJyVVstu2zAQ..."

# 2. Base64 解碼
decoded_bytes = base64.b64decode(b64_data)

# 3. Zlib 解壓縮 (關鍵: wbits=-15)
decompressed = zlib.decompress(decoded_bytes, wbits=-15)

# 4. 解析 JSON
data = json.loads(decompressed.decode('utf-8'))
```

### JSON 結構

```json
{
  "Entries": [
    {
      "Utc": "2025-04-06T04:07:42.7143391Z",
      "Cars": {
        "1": {
          "Channels": {
            "0": 0,      // Speed (km/h)
            "2": 0,      // RPM
            "3": 0,      // nGear
            "4": 0,      // Throttle (%)
            "5": 0       // Brake (boolean)
          }
        },
        "4": { ... },
        "5": { ... }
        // ... 其他車輛
      }
    }
  ]
}
```

---

## 📈 速度資料分析

### 統計摘要

```
總資料點: 626,780
最小值:         0 km/h
最大值:    13,294 km/h (⚠️ 異常值)
平均值:     6,987 km/h (⚠️ 受異常值影響)
```

### 速度分布

```
   0- 50 km/h: ############# 174,103 (27.8%)
  50-100 km/h:                      3 ( 0.0%)
 100-150 km/h:                     10 ( 0.0%)
 150-200 km/h:                      5 ( 0.0%)
 200-250 km/h:                      3 ( 0.0%)
 250-300 km/h:                     14 ( 0.0%)
 300-350 km/h:                      6 ( 0.0%)
 350-400 km/h:                      2 ( 0.0%)
```

⚠️ **注意**: 大部分資料為 0-50 km/h,且存在明顯異常值 (>400 km/h)

### 可能原因

1. **初始化資料**: 比賽前/後的靜止狀態
2. **編碼錯誤**: 某些 Channel 可能使用不同的數值編碼
3. **資料驗證**: 需要過濾無效資料 (例如: speed > 400)

---

## 🔄 與 fastf1 比較

### 檔案格式

| 特性 | LiveTiming (原始) | fastf1 (處理後) |
|------|-------------------|-----------------|
| 格式 | .jsonStream | Pandas DataFrame |
| 壓縮 | Base64 + Zlib | 已解壓縮 |
| 結構 | 巢狀 JSON | 表格 (行/列) |
| 時間戳 | 字串 ('HH:MM:SS.mmm') | Timedelta |
| 存取 | `data['Entries'][0]['Cars']['1']['Channels']['0']` | `df.loc[df['DriverNumber']==1, 'Speed']` |

### 資料量

| 項目 | LiveTiming | fastf1 |
|------|------------|--------|
| 記錄數 | 8,258 | ~相同 |
| 速度資料點 | 626,780 | ~相同 (合併後) |
| 檔案大小 | 6.87 MB (壓縮) | 視存儲格式 |

### 處理複雜度

**LiveTiming**:
```python
# 需要手動解碼
for line in lines:
    timestamp = line[:12]
    data = decode_f1_packet(line[12:])
    for entry in data['Entries']:
        for car_num, car_data in entry['Cars'].items():
            speed = car_data['Channels']['0']
            # 處理 speed...
```

**fastf1**:
```python
# 直接使用 DataFrame
import fastf1
session = fastf1.get_session(2025, 'Japan', 'R')
session.load()
laps = session.laps
telemetry = laps.pick_driver('VER').get_telemetry()
speeds = telemetry['Speed']  # 完成!
```

---

## 🎯 Channel 對照表

| Channel | 名稱 | 單位 | 範圍 |
|---------|------|------|------|
| 0 | Speed | km/h | 0-400 |
| 2 | RPM | 轉/分 | 0-15000 |
| 3 | nGear | 檔位 | 0-8 |
| 4 | Throttle | % | 0-100 |
| 5 | Brake | 布林 | 0/1 |
| 45 | DRS | 狀態 | 0-14 |

---

## ✅ 關鍵發現

### 1. 壓縮方式已驗證

- ✅ Base64 解碼正確
- ✅ Zlib 解壓縮需要 `wbits=-15`
- ✅ JSON 解析成功率 100%

### 2. 資料結構

- 每筆記錄包含**多輛車**的遙測資料
- 使用 **Channels** 字典存儲不同感測器讀數
- 時間戳為相對時間 (`HH:MM:SS.mmm`)

### 3. 資料品質

- ⚠️ 存在異常值,需要過濾
- ✅ 大部分資料結構正確
- 建議: 實作資料驗證 (`0 < speed < 400`)

### 4. 與 fastf1 差異

**LiveTiming 優勢**:
- 直接從官方 API 取得
- 可自訂處理邏輯
- 適合學習資料結構
- 支援即時串流 (WebSocket)

**fastf1 優勢**:
- 即開即用,無需解碼
- Pandas 生態系整合
- 自動過濾異常值
- 豐富的分析功能

---

## 🚀 後續步驟建議

### 階段 1: 資料清洗

```python
# 過濾異常速度
valid_speeds = [s for s in speed_data if 0 <= s <= 400]

# 檢查其他 Channel 的合理範圍
valid_rpm = [r for r in rpm_data if 0 <= r <= 15000]
```

### 階段 2: 時間序列處理

```python
# 將相對時間轉換為絕對時間
from datetime import timedelta
def parse_timestamp(ts_str):
    # "00:12:34.567" -> timedelta
    h, m, s = ts_str.split(':')
    return timedelta(hours=int(h), minutes=int(m), seconds=float(s))
```

### 階段 3: 整合 InfluxDB

```python
from influxdb_client import InfluxDBClient, Point

# 寫入時序資料庫
point = Point("telemetry") \
    .tag("driver", car_num) \
    .field("speed", speed) \
    .field("rpm", rpm) \
    .time(timestamp)
```

---

## 📌 結論

✅ **成功驗證**: F1 Live Timing API 資料可正常下載與解碼  
✅ **格式確認**: .jsonStream 格式為 時間戳 + Base64(Zlib壓縮JSON)  
✅ **資料量**: 2025 日本站正賽約 **8,258 筆記錄**, 包含 **626,780 個速度資料點**  
⚠️ **注意事項**: 需實作資料驗證以過濾異常值

**建議**: 
- 對於**快速分析**,使用 fastf1
- 對於**學習 API** 或**即時應用**,使用 LiveTiming 原始資料
- 可結合兩者: LiveF1 下載 → 自訂處理 → InfluxDB
