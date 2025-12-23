# 🏎️ F1 官方 Live Timing API Mini-Sector 數據來源分析

**日期**: 2025-12-15  
**結論**: ⚠️ F1 官方 API **不直接提供** Mini-Sector 數據，但 OpenF1 有！

---

## 📡 F1 官方 Live Timing API 架構

### 1. **SignalR WebSocket 實時連接**

```
端點: wss://livetiming.formula1.com/signalr
協議: SignalR 1.5
Hub: Streaming
```

### 2. **可用的數據主題** (已在系統中實現)

```python
F1_OFFICIAL_TOPICS = [
    "CarData.z",              # 車輛遙測 (RPM, Speed, Gear, Throttle, Brake, DRS)
    "Position.z",             # 位置數據 (X, Y, Z 座標)
    "TimingData",             # 計時數據 (Position, Gap, Interval, LapTime)
    "TimingAppData",          # ⭐ App 數據 (包含扇區時間)
    "DriverList",             # 車手列表
    "WeatherData",            # 天氣數據
    "TrackStatus",            # 賽道狀態
    "RaceControlMessages",    # 賽會訊息
    "SessionInfo",            # 賽事資訊
    "SessionStatus",          # 賽事狀態
    "LapCount",               # 圈數
    "CurrentTyres",           # 當前輪胎
    "TyreStintSeries",        # 輪胎 Stint
    "PitStopSeries",          # 進站資訊
]
```

---

## ❌ **Mini-Sector 數據狀態**

### 結論：F1 官方 API **不提供** Mini-Sector 原始數據

經過調查，F1 官方 Live Timing API 的數據結構如下：

#### **TimingAppData** (扇區時間)
```json
{
  "Lines": {
    "1": {  // 車手編號
      "Sectors": [
        {
          "Stopped": false,
          "PreviousValue": "28.502",
          "Value": "28.321",
          "Status": 2049,  // 2048=無效, 2049=綠色, 2051=紫色, 2064=黃色
          "OverallFastest": false,
          "PersonalFastest": true
        },
        // S2, S3...
      ]
    }
  }
}
```

**重點發現**：
- ✅ 有 **3 個扇區** (S1, S2, S3) 的時間和狀態
- ❌ **沒有** Mini-Sector 細分數據
- ✅ 每個扇區有顏色狀態 (2048/2049/2051/2064)

---

## 🔍 OpenF1 vs F1 官方 API

| 特性 | F1 官方 API | OpenF1 API |
|------|-------------|------------|
| **扇區數據** | ✅ S1/S2/S3 (3個) | ✅ S1/S2/S3 (3個) |
| **Mini-Sector** | ❌ **不提供** | ✅ **提供 23 個** |
| **數據來源** | SignalR WebSocket | HTTP REST |
| **實時性** | ✅ 實時 | ✅ 準實時 (~1秒延遲) |
| **歷史數據** | ❌ 需權限 | ✅ 2018年至今 |
| **免費** | ✅ 是 | ✅ 是 |

---

## 🎯 Mini-Sector 數據實際來源

### **OpenF1 是唯一提供 Mini-Sector 數據的免費API**

```python
# OpenF1 提供完整的 mini-sector 數據
import requests

r = requests.get('https://api.openf1.org/v1/laps?session_key=9159&driver_number=1&lap_number=1')
lap = r.json()[0]

# ✅ 每個扇區有 7-8 個 mini-sector
segments_s1 = lap['segments_sector_1']  # [2064, 2049, 2049, 2049, 2049, 2049, 2049, 2049]
segments_s2 = lap['segments_sector_2']  # [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049]
segments_s3 = lap['segments_sector_3']  # [2049, 2049, 2049, 2049, 2051, 2049, 2049]

# 總共 23 個 mini-sector per lap
```

---

## 🤔 為什麼 F1 官方不提供 Mini-Sector？

### 推測原因：

1. **數據量問題**: 
   - 3 個扇區 vs 23 個 mini-sector = 7.6 倍數據量
   - 20 車手 × 23 segments = 460 個數據點/圈
   
2. **商業考量**:
   - Mini-Sector 是 F1 TV Pro 獨家功能
   - 可能希望保持此功能作為付費訂閱賣點

3. **API 設計**:
   - F1 官方 API 設計較早 (2018年前)
   - Mini-Sector 功能可能是後來添加到 F1 TV

---

## 🚀 實現建議

### **推薦方案：整合 OpenF1 API**

#### 原因：
1. ✅ **唯一提供 Mini-Sector 的免費來源**
2. ✅ **數據格式清晰**，直接可用
3. ✅ **歷史數據完整** (2018年至今)
4. ✅ **社群維護**，穩定可靠

#### 實現方案：

```python
# 方案 A: 純 OpenF1 (推薦用於歷史回放)
from modules.gui.live_timing.core.openf1_client import OpenF1Client

client = OpenF1Client()
mini_sectors = client.get_lap_mini_sectors(session_key=9601, driver_number=1)

# 方案 B: F1 官方 (實時) + OpenF1 (Mini-Sector 歷史補充)
# 1. 使用 F1 SignalR 獲取實時數據 (低延遲)
# 2. 圈速完成後，從 OpenF1 補充 mini-sector 數據
```

---

## 💡 替代方案 (不推薦)

### 方案 C: FastF1 計算 (不準確)

```python
# ❌ 不推薦：自行計算 mini-sector
# 問題：
# 1. 無法得知官方的 mini-sector 劃分邏輯
# 2. 無法復現官方的顏色判定 (2048/2049/2051/2064)
# 3. 計算量大，不適合實時場景

import fastf1
session = fastf1.get_session(2024, 'Abu Dhabi', 'R')
laps = session.laps.pick_driver('VER').pick_fastest()
telemetry = laps.get_telemetry()

# 需要自行劃分 23 個 segment... (不準確)
```

---

## 📊 數據流程建議

### **歷史回放模式** (推薦)
```
GUI → OpenF1 API → Mini-Sector 數據 → Ranking Tower 顯示
```

### **實時模式** (混合方案)
```
1. F1 SignalR (實時) → 基礎數據 (位置、差距、圈速)
2. 圈速完成觸發 → OpenF1API → 補充 Mini-Sector
3. Ranking Tower 更新 Mini-Sector 欄位
```

---

## 🎯 最終建議

### **使用 OpenF1 作為 Mini-Sector 唯一數據來源**

**優點**:
- ✅ 數據完整且準確
- ✅ 與 F1 官方完全一致
- ✅ 無需複雜計算
- ✅ 免費且穩定

**缺點**:
- ⚠️ 實時性較 F1 SignalR 稍差 (~1秒)
- ⚠️ 需要依賴第三方服務

**結論**: 
對於 Ranking Tower 的 Mini-Sector 功能，**OpenF1 是最佳選擇**，因為 F1 官方 API 根本不提供此數據。

---

## 📚 相關文件

- **F1 SignalR 客戶端**: `modules/gui/live_timing/core/signalr_client.py`
- **OpenF1 分析報告**: `docs/OpenF1_MiniSector_Analysis.md`
- **測試腳本**: `test_openf1_segments.py`

---

## 🏁 實現步驟

1. ✅ **已確認**: F1 官方不提供 Mini-Sector
2. ✅ **已確認**: OpenF1 提供完整 Mini-Sector
3. ⏳ **下一步**: 整合 OpenF1 到 Ranking Tower
4. ⏳ **優化**: 實現緩存機制減少 API 請求

---

**最終答案**: 
# F1 官方 Live Timing API **不提供** Mini-Sector 數據！
# 唯一免費來源是 **OpenF1 API**！
