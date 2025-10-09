# 功能 5 (-f 5) JSON 輸出格式說明

## 📋 功能概述

**功能編號**: 5  
**功能名稱**: 車手進站詳細記錄 (Driver Detailed Pitstop Records)  
**分析類型**: `driver_detailed_pitstop_records`

### 命令範例
```powershell
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R
```

---

## 📁 生成的 JSON 檔案

### 檔案命名格式
```
driver_detailed_pitstop_records_{year}_{event_name}.json
```

### 實際範例
```
driver_detailed_pitstop_records_2023_Japanese_Grand_Prix.json
```

**儲存位置**: `json/` 目錄

---

## 📊 JSON 結構詳解

### 完整結構範例

```json
{
  "function_id": 5,
  "function_name": "Driver Detailed Pitstop Records",
  "analysis_type": "driver_detailed_pitstop_records",
  "session_info": {
    "event_name": "Japanese Grand Prix",
    "circuit_name": "Suzuka",
    "session_type": "Race",
    "year": 2023
  },
  "timestamp": "2025-10-07T01:47:07.886826",
  "data": {
    "VER": [
      {
        "pitstop_number": 1,
        "lap_number": 12,
        "pit_duration": 2.3,
        "session_time": "Unknown",
        "team": "Red Bull Racing"
      },
      {
        "pitstop_number": 2,
        "lap_number": 32,
        "pit_duration": 2.5,
        "session_time": "Unknown",
        "team": "Red Bull Racing"
      }
    ],
    "LEC": [
      {
        "pitstop_number": 1,
        "lap_number": 15,
        "pit_duration": 2.8,
        "session_time": "Unknown",
        "team": "Ferrari"
      }
    ]
    // ... 其他車手
  }
}
```

---

## 🔍 欄位說明

### 頂層欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `function_id` | number | 功能編號 (固定為 5) |
| `function_name` | string | 功能名稱 "Driver Detailed Pitstop Records" |
| `analysis_type` | string | 分析類型識別碼 "driver_detailed_pitstop_records" |
| `session_info` | object | 賽事會話資訊 |
| `timestamp` | string | JSON 生成時間 (ISO 8601 格式) |
| `data` | object | 車手進站數據 (主要數據) |

### `session_info` 物件

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| `event_name` | string | 賽事名稱 | "Japanese Grand Prix" |
| `circuit_name` | string | 賽道名稱 | "Suzuka" |
| `session_type` | string | 會話類型 | "Race", "Qualifying", "Practice 1" |
| `year` | number | 賽季年份 | 2023 |

### `data` 物件結構

**鍵 (Key)**: 車手代碼 (3 字母縮寫，例如 "VER", "LEC", "HAM")  
**值 (Value)**: 進站記錄陣列 (按進站順序排列)

### 進站記錄物件

每個進站記錄包含以下欄位：

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| `pitstop_number` | number | 進站序號 (第幾次進站) | 1, 2, 3 |
| `lap_number` | number | 進站圈數 | 12, 28, 45 |
| `pit_duration` | number | 進站時長 (秒) | 2.3, 23.7, 52.1 |
| `session_time` | string | 會話時間 | "Unknown" 或 "01:23:45" |
| `team` | string | 車隊名稱 | "Red Bull Racing", "Ferrari" |

---

## 📈 數據特性

### 車手排序
- 數據按車手代碼 (Driver Code) 作為鍵值
- 每位車手的進站記錄按 `pitstop_number` 順序排列

### 進站時長解讀

| 時長範圍 | 類型 | 說明 |
|---------|------|------|
| **2-4 秒** | 🟢 正常進站 | 標準換胎進站 |
| **20-30 秒** | 🟡 長進站 | 可能包含調整或輕微問題 |
| **40-60 秒** | 🔴 極長進站 | 嚴重問題或紅旗期間進站 |

### 特殊情況

**第 1 圈進站**:
```json
{
  "pitstop_number": 1,
  "lap_number": 1,
  "pit_duration": 27.0,
  "session_time": "Unknown",
  "team": "Alpine"
}
```
- 通常代表起跑事故後進站
- 或紅旗後重新起跑前的輪胎更換

**會話時間 "Unknown"**:
- 表示 OpenF1 API 未提供精確時間
- 僅提供圈數和時長數據

---

## 🎯 使用場景

### 1. 進站策略分析
```javascript
// 計算每位車手的總進站次數
Object.entries(data).forEach(([driver, stops]) => {
  console.log(`${driver}: ${stops.length} 次進站`);
});
```

### 2. 進站效率比較
```javascript
// 找出最快進站
let fastest = { driver: "", duration: Infinity };
Object.entries(data).forEach(([driver, stops]) => {
  stops.forEach(stop => {
    if (stop.pit_duration < fastest.duration && stop.pit_duration > 1) {
      fastest = { driver, duration: stop.pit_duration, lap: stop.lap_number };
    }
  });
});
```

### 3. 車隊策略對比
```javascript
// 按車隊分組進站數據
const teamStrategies = {};
Object.entries(data).forEach(([driver, stops]) => {
  const team = stops[0]?.team;
  if (!teamStrategies[team]) teamStrategies[team] = [];
  teamStrategies[team].push({ driver, stopCount: stops.length });
});
```

---

## 🔄 與其他功能的關聯

| 功能 | 關係 | 說明 |
|------|------|------|
| **功能 3** | 互補 | 車手最快進站時間排行榜 (只看最快單次) |
| **功能 4** | 互補 | 車隊進站時間排行榜 (車隊層級聚合) |
| **功能 5** | 🎯 當前 | 每位車手的完整進站歷史 (最詳細) |

### 選擇指南
- **需要快速排名** → 使用功能 3 或 4
- **需要完整歷史記錄** → 使用功能 5 (本功能)
- **需要車隊層級分析** → 使用功能 4

---

## 📝 實際數據範例 (2023 日本站)

### 正常進站範例 (Verstappen)
```json
{
  "pitstop_number": 1,
  "lap_number": 12,
  "pit_duration": 2.3,
  "session_time": "Unknown",
  "team": "Red Bull Racing"
}
```

### 長進站範例 (Zhou)
```json
{
  "pitstop_number": 2,
  "lap_number": 10,
  "pit_duration": 24.0,
  "session_time": "Unknown",
  "team": "Alfa Romeo"
}
```

### 起跑事故進站範例 (Ocon)
```json
{
  "pitstop_number": 1,
  "lap_number": 1,
  "pit_duration": 27.0,
  "session_time": "Unknown",
  "team": "Alpine"
}
```

---

## 🔧 技術細節

### 數據來源
1. **優先**: OpenF1 API (`/pit` 端點)
2. **備用**: FastF1 遙測數據推算

### 緩存機制
- **緩存鍵格式**: `driver_detailed_pitstops_{year}_{event_name}`
- **緩存位置**: `cache/` 目錄
- **緩存類型**: Pickle (.pkl)

### 執行模式
```python
# 標準執行 (使用緩存)
run_driver_detailed_pitstop_records(data_loader, show_detailed_output=False)

# 強制顯示詳細輸出 (即使有緩存)
run_driver_detailed_pitstop_records(data_loader, show_detailed_output=True)
```

---

## ⚠️ 注意事項

### 數據完整性
- ✅ 2023-2025 賽季數據完整性較高
- ⚠️ 2020-2022 賽季部分賽事可能缺少會話時間
- ❌ 2019 及以前賽季可能需要依賴 FastF1 推算

### 特殊情況處理
- **紅旗期間進站**: 時長可能異常長 (50+ 秒)
- **事故後進站**: 第 1 圈進站通常代表事故
- **未完成進站**: 極少數情況可能缺少數據

---

## 🚀 CLI 命令完整範例

### 基本命令
```powershell
# 2023 日本站正賽
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R

# 2024 摩納哥站正賽
python f1_analysis_modular_main.py -f 5 -y 2024 -r Monaco -s R

# 2025 巴林站正賽
python f1_analysis_modular_main.py -f 5 -y 2025 -r Bahrain -s R
```

### 支援的賽事類型
```powershell
# 正賽 (Race)
-s R

# 排位賽 (Qualifying) - 較少進站數據
-s Q

# 衝刺賽 (Sprint)
-s S
```

---

## 📚 相關文檔

- **功能映射器**: `CLI_modules/cli/core/function_mapper.py` (第 558 行)
- **分析器實現**: `CLI_modules/cli/analyzer/driver_detailed_pitstop_records.py`
- **OpenF1 整合**: `CLI_modules/cli/core/openf1_data_analyzer.py`

---

**文檔版本**: 1.0  
**最後更新**: 2025-10-07  
**適用功能**: 功能 5 (Driver Detailed Pitstop Records)
