# F1 賽道介紹模組 - 功能驗證與整合調查報告

**調查日期**: 2025-11-09  
**調查範圍**: CLI 功能驗證、高程資料生成、JSON 架構分析  
**遵循原則**: 反幻覺編碼五原則（零假設、完全驗證）

---

## 📊 調查摘要

本次調查針對賽道介紹模組（Function 53）的開發準備工作，完成以下驗證：

1. ✅ **高程剖面圖數據** - 成功生成 27 條賽道的完整高程資料
2. ✅ **超車統計功能** (Function 16.1) - CLI 完整實現，待 GUI 整合
3. ✅ **事故統計功能** (Function 6 & 4.5) - 已有 TURN 彎道資訊
4. ✅ **賽道地圖渲染** - TrackMapWidget 已完整實現

---

## 🏔️ 高程剖面圖資料 - 已完成

### 成果概述

| 項目 | 結果 | 詳情 |
|------|------|------|
| **賽道數量** | 27 條 | 2020-2025 賽季使用的所有賽道 |
| **總座標點數** | 3,477 個 | 平均每條賽道 128 個座標點 |
| **資料完整性** | 100% | 所有座標點都有有效高程值 |
| **處理時間** | 1.8 分鐘 | 無 API 限流，一次性查詢成功 |
| **儲存位置** | `json/f1-circuits-master/circuit_data/` | 標準化 JSON 格式 |

### 資料結構

```json
{
  "circuit_id": "jp-1962",
  "basic_info": {
    "name": "Suzuka International Racing Course",
    "location": "Suzuka",
    "country": "JP",
    "length_meters": 5807,
    "opened_year": 1962,
    "reference_altitude": 60
  },
  "coordinates": [
    {
      "lon": 136.540283,
      "lat": 34.843344,
      "elevation": 28.0,
      "distance_km": 0.0
    }
  ],
  "elevation_profile": {
    "min_elevation": 18.0,
    "max_elevation": 68.0,
    "elevation_change": 50.0,
    "avg_elevation": 46.1,
    "max_elevation_point": {
      "distance_km": 3.661,
      "elevation": 68.0
    },
    "min_elevation_point": {
      "distance_km": 0.413,
      "elevation": 18.0
    }
  },
  "metadata": {
    "total_points": 172,
    "valid_elevation_points": 172,
    "track_length_calculated_km": 5.801,
    "generated_timestamp": "2025-11-09T...",
    "data_source": "Open-Elevation API v1"
  }
}
```

### 重點賽道高程特性

| 賽道 | 座標點數 | 高低差 | 特性 |
|------|---------|--------|------|
| **鈴鹿 (Suzuka)** | 172 | 50m | 🟠 中等高低差 |
| **斯帕 (Spa-Francorchamps)** | 153 | **109m** | 🔴 極具挑戰性（最大高低差）|
| **摩納哥 (Monaco)** | 160 | 63m | 🟠 中等高低差 |
| **奧斯丁 COTA** | 171 | 33m | 🟡 輕微起伏 |
| **新加坡** | 116 | 34m | 🟡 輕微起伏 |

### 自動化腳本

**檔案**: `batch_generate_circuit_elevation_data.py`

**功能**:
- ✅ 批次處理 27 條賽道
- ✅ 一次性查詢所有座標點高程（無批次限制）
- ✅ 斷點續傳（處理失敗可重啟繼續）
- ✅ 錯誤記錄（失敗賽道記錄到 `failed_circuits_log.json`）
- ✅ API 節流保護（每 5 條賽道延遲 15 秒）

**命名規則**: `{country_code}_{year}_elevation_data.json`  
**範例**: `jp_1962_elevation_data.json` (鈴鹿)

---

## 🏁 CLI Function 16.1 - 年度超車統計 (已驗證)

### 功能確認

**Function ID**: 16.1  
**功能名稱**: 全部車手年度超車統計 (All Drivers Annual Overtaking Statistics)  
**檔案位置**: `CLI_modules/cli/analyzer/all_drivers_annual_overtaking_statistics.py`  
**開發日期**: 2025-08-05  
**狀態**: ✅ CLI 完整實現，❌ GUI 未整合

### 核心功能（已實現）

| 功能 | 狀態 | 說明 |
|------|------|------|
| **分析範圍** | ✅ | 整個賽事的所有車手 |
| **超車次數統計** | ✅ | `overtakes_made` 欄位 |
| **被超次數統計** | ✅ | `overtaken_by` 欄位 |
| **淨超車計算** | ✅ | `net_overtaking = overtakes_made - overtaken_by` |
| **超車成功率** | ✅ | `overtaking_success_rate = (overtakes_made / total_attempts) × 100%` |
| **車手排名** | ✅ | 按淨超車數降序排列 |

### 數據分析方法（已驗證）

```python
# Line 165-182: _get_driver_real_overtaking_stats()
driver_laps = data_loader.laps[data_loader.laps['Driver'] == driver_abbr]
driver_laps = driver_laps.sort_values('LapNumber')
position_changes = driver_laps['Position'].diff().fillna(0)

# 負數 = 位置前進 (超車)
overtakes_made = len(position_changes[position_changes < 0])
# 正數 = 位置後退 (被超車)
overtaken_by = len(position_changes[position_changes > 0])
```

### JSON 輸出結構（已驗證）

```json
{
  "analysis_info": {
    "function_id": "16.1",
    "analysis_type": "all_drivers_annual_overtaking_statistics",
    "timestamp": "20251109_HHMMSS",
    "race_info": "2025 Japan",
    "total_drivers": 20
  },
  "annual_overtaking_statistics": [
    {
      "abbreviation": "VER",
      "driver_name": "Max Verstappen",
      "team_name": "Red Bull Racing",
      "car_number": "1",
      "race_position": 1,
      "overtakes_made": 8,
      "overtaken_by": 2,
      "net_overtaking": 6,
      "overtaking_success_rate": 80.0,
      "avg_overtaking_position": 0.0
    }
  ],
  "summary": {
    "total_drivers": 20,
    "total_overtakes": 100,
    "average_overtakes_per_driver": 5.0,
    "best_performer": {
      "driver": "Max Verstappen",
      "net_overtaking": 6
    }
  }
}
```

### 限制與注意事項

1. **後備機制** (Line 218-264)
   - 當 FastF1 數據不完整時，使用 `_generate_reasonable_overtaking_estimate()`
   - 提供預估值而非真實數據
   - **建議**：使用時確保 `data_loader.laps` 存在

2. **依賴項**
   - 需要 `data_loader.laps` 包含 `Position` 和 `LapNumber` 欄位
   - 需要 `data_loader.results` 包含車手基本資訊

3. **GUI 整合狀態**
   - ✅ CLI 功能完整實現
   - ❌ **尚未發現** GUI 包裝模組
   - 📋 需要建立 `modules/gui/overtaking_analysis/` 模組

---

## 🚨 CLI Function 6 - 事故統計摘要 (已驗證)

### 功能確認

**Function ID**: 6  
**功能名稱**: 事故統計摘要 (Accident Statistics Summary)  
**檔案位置**: `modules/gui/accident_analysis/accident_statistics_summary.py`  
**狀態**: ✅ 已實現，⚠️ 彎道資訊在 Function 4.5

### 已實現的統計項目

```python
# Line 117-133: analyze_accident_statistics()
statistics['incident_types'] = {
    'accidents': 0,        # ✅ 碰撞事故
    'flags': 0,            # ✅ 旗幟事件（包含黃旗）
    'investigations': 0,   # ✅ 調查事件
    'penalties': 0,        # ✅ 處罰事件
    'safety_cars': 0,      # ✅ 安全車出動
    'red_flags': 0         # ✅ 紅旗中斷
}
```

**✅ Yellow Flag、Red Flag、Safety Car 統計已完整實現**

### 數據來源確認

**race_control_messages 實際欄位** (已驗證):
```python
['Time', 'Category', 'Message', 'Status', 'Flag', 'Scope', 'Sector', 'RacingNumber', 'Lap']
```

**關鍵發現**：
- ✅ **有 `Sector` 欄位！** (值為 1, 2, 3, 4 或 NaN)
- ✅ 有 `Lap` 欄位 (可映射到圈數)
- ✅ 有 `Time` 欄位 (可映射到 telemetry 距離)
- ✅ 有 `Flag` 欄位 (YELLOW, RED 等)

### 實際事件範例 (2024 Japan)

```
事件 6:
  Sector: 4.0
  Flag: YELLOW
  Message: YELLOW IN TRACK SECTOR 4
  Lap: 1

事件 8:
  Sector: nan
  Flag: RED
  Message: RED FLAG
  Lap: 1
```

### 當前 JSON 結構

```json
{
  "function_id": 6,
  "data": {
    "total_incidents": 8,
    "incident_types": {
      "accidents": 0,
      "flags": 6,
      "safety_cars": 0,
      "red_flags": 1
    },
    "incident_distribution_by_lap": {
      "1": 8
    }
  }
}
```

**❌ 目前沒有彎道資訊**

### 建議增強方案

**選項 1：使用 Sector 欄位（最簡單）** ⚡

```python
# 在 analyze_accident_statistics() 中增加:
statistics['incident_distribution_by_sector'] = {
    '1': 2,
    '2': 1,
    '3': 3,
    '4': 2
}
```

**優點**：
- ✅ 只需新增一個統計欄位
- ✅ 數據已存在，無需額外計算
- ✅ **不影響現有 JSON 架構**

**缺點**：
- ❌ 精度較低（扇區 vs 彎道）- 鈴鹿有 18 個彎道但只有 3 個扇區

---

## 🎯 CLI Function 4.5 - 所有事件詳細列表 (已驗證)

### 功能確認

**Function ID**: 4.5  
**功能名稱**: 所有事件詳細列表 (All Incidents Analysis)  
**檔案位置**: `modules/gui/accident_analysis/all_incidents_analysis.py`  
**狀態**: ✅ **包含 TURN (彎道) 資訊！**

### 關鍵發現：TURN 資訊已存在！

**實際代碼驗證**（Line 408-419）

```python
def extract_track_position(message_text):
    """提取賽道位置信息"""
    message_upper = message_text.upper()
    
    # 提取彎道信息
    turn_matches = re.findall(r'TURN (\d+)', message_upper)
    if turn_matches:
        return f"Turn {turn_matches[0]}"  # ✅ 有提取 TURN 號碼！
    
    # 提取其他位置信息
    if 'PIT ENTRY' in message_upper:
        return 'Pit Entry'
    elif 'PIT EXIT' in message_upper:
        return 'Pit Exit'
    elif 'START/FINISH' in message_upper:
        return 'Start/Finish Line'
    
    return 'Unknown'
```

### 實際 JSON 數據範例（2022 Japan）

**✅ 找到 8 個包含 TURN 資訊的事件！**

```json
{
  "sequence_number": 11,
  "lap": 1,
  "message": "CAR 5 (VET) SPUN AND CONTINUED AT TURN 1",
  "category": "OTHER",
  "sector": null
}

{
  "sequence_number": 36,
  "lap": 24,
  "message": "TURN 11 INCIDENT INVOLVING CARS 18 (STR) AND 47 (MSC) NOTED",
  "category": "ACCIDENT",
  "sector": null
}

{
  "sequence_number": 39,
  "lap": 29,
  "message": "TURN 16 INCIDENT INVOLVING CARS 16 (LEC) AND 11 (PER) NOTED",
  "category": "CONTACT",
  "sector": null
}
```

### TURN 資訊提取邏輯

**代碼位置**: Line 335-348

```python
# 在 extract_flags() 函數中
turn_match = re.search(r'TURN (\d+)', message_upper)
corner_match = re.search(r'CORNER (\d+)', message_upper)

if turn_match:
    flag_info["location"] = f"TURN_{turn_match.group(1)}"  # ✅
elif corner_match:
    flag_info["location"] = f"CORNER_{corner_match.group(1)}"  # ✅
```

### 現有問題與建議

**⚠️ 問題**：JSON 沒有單獨的 `turn` 欄位！

```json
{
  "message": "TURN 11 INCIDENT...",  // ✅ TURN 資訊在訊息文字中
  "sector": null,                     // ❌ 沒有 turn 欄位
  "category": "ACCIDENT"
}
```

**💡 建議方案**：在現有結構下新增 `track_location` 欄位

```json
{
  "message": "TURN 11 INCIDENT INVOLVING CARS 18 (STR) AND 47 (MSC) NOTED",
  "sector": null,
  "track_location": {
    "type": "TURN",
    "number": 11,
    "description": "Turn 11"
  },
  "category": "ACCIDENT"
}
```

**實現方式**：
```python
# 在 process_all_incidents() 中增加：
track_location = extract_detailed_track_position(message_text)
incident["track_location"] = track_location
```

---

## 🗺️ TrackMapWidget - 賽道地圖渲染 (已驗證)

### 功能確認

**檔案位置**: `modules/gui/track_analysis/track_map_widget.py`  
**狀態**: ✅ 完整實現，生產就緒

### 核心功能（已實現）

| 功能 | 狀態 | 程式碼位置 |
|------|------|-----------|
| **彎道標註** | ✅ | `_draw_official_corners()` (Lines 373-422) |
| **座標轉換** | ✅ | `world_to_screen()` |
| **智能偏移** | ✅ | `_calculate_corner_offset()` |
| **數據載入** | ✅ | `load_track_data()` |

### 彎道標註實現

```python
# Line 373-422: _draw_official_corners()
# 白色背景、黑色文字的彎道標記，智能偏移避免重疊
```

**特點**：
- ✅ 白色圓形背景，黑色文字
- ✅ 智能位置偏移（避免與賽道線重疊）
- ✅ 支援 official_corners 數據結構
- ✅ 完全無需修改即可使用

---

## 📋 賽道模組開發整合計畫

### 階段 1：CLI 後端 (Function 53)

**檔案**: `CLI_modules/cli/analyzer/circuit_introduction_analysis.py`

**功能需求**：
1. ✅ 讀取 f1-circuits-master GeoJSON (已有自動化腳本)
2. ✅ 讀取高程資料 JSON (已完成 27 條賽道)
3. ✅ 整合 FastF1 official_corners (已有實現參考)
4. ⚠️ 整合超車統計 (Function 16.1 CLI 完成，需調用)
5. ⚠️ 整合事故統計 (Function 4.5 完成，需調用)

**輸出 JSON 結構建議**：

```json
{
  "function_id": 53,
  "function_name": "Circuit Introduction Analysis",
  "circuit_info": {
    "circuit_id": "jp-1962",
    "name": "Suzuka International Racing Course",
    "location": "Suzuka, Japan",
    "length_meters": 5807,
    "coordinates": [...],
    "elevation_profile": {...}
  },
  "official_corners": [
    {"number": 1, "distance": 150.5, "angle": 90},
    {"number": 2, "distance": 450.2, "angle": 45}
  ],
  "overtaking_statistics": {
    "total_overtakes_at_circuit": 120,
    "overtaking_hotspots": [
      {"corner": 1, "overtakes": 25, "success_rate": 65.5},
      {"corner": 11, "overtakes": 18, "success_rate": 52.3}
    ]
  },
  "incident_statistics": {
    "total_incidents": 45,
    "incidents_by_corner": [
      {"corner": 1, "incidents": 8, "types": ["yellow_flag", "contact"]},
      {"corner": 11, "incidents": 5, "types": ["spin", "accident"]}
    ]
  }
}
```

### 階段 2：GUI 前端

**模組結構**：
```
modules/gui/circuit_analysis/
├── circuit_introduction_module.py    # 主模組
├── circuit_introduction_mdi.py       # MDI 管理
├── circuit_data_loader.py            # 數據載入器（繼承 UniversalDataLoader）
└── circuit_chart_widget.py           # 圖表繪製
```

**UI 元件需求**：
1. ✅ 賽道地圖 - 使用現有 `TrackMapWidget`
2. ✅ 高程剖面圖 - 使用生成的 elevation_data.json
3. ⚠️ 彎道號碼標註 - `_draw_official_corners()` 已實現
4. ⚠️ 超車熱點標記 - 疊加在賽道圖上
5. ⚠️ 事故統計圖表 - 按彎道分佈

### 階段 3：數據映射邏輯

**挑戰**：
- GPS 座標 (f1-circuits-master) → FastF1 Distance (官方彎道)
- 事件 Time → Telemetry Distance → Corner Number

**解決方案**：
```python
def map_event_to_corner(event_time, telemetry_data, official_corners):
    """
    事件時間 → 賽道距離 → 彎道號碼
    
    Args:
        event_time: 事件時間戳記
        telemetry_data: FastF1 telemetry (包含 Time, Distance)
        official_corners: 官方彎道資料 (包含 Number, Distance)
    
    Returns:
        corner_number: 最近的彎道號碼
    """
    # 1. 找到最接近事件時間的 telemetry 記錄
    closest_telem = telemetry_data[telemetry_data['Time'] == event_time].iloc[0]
    event_distance = closest_telem['Distance']
    
    # 2. 找到最近的彎道
    distances = [c['Distance'] for c in official_corners]
    corner_idx = min(range(len(distances)), 
                    key=lambda i: abs(distances[i] - event_distance))
    
    return official_corners[corner_idx]['Number']
```

---

## 🎯 總結與下一步行動

### ✅ 已完成

1. **高程剖面圖資料** - 27 條賽道，3,477 個座標點，100% 完整
2. **CLI 功能驗證** - Function 16.1 (超車)、Function 6 (事故摘要)、Function 4.5 (事件詳細)
3. **TURN 資訊確認** - Function 4.5 已提取彎道號碼（需結構化）
4. **GUI 組件確認** - TrackMapWidget 完整可用
5. **✅ track_location 欄位已添加** (2025-11-09) - Function 8 成功新增結構化賽道位置資訊

### 🎉 track_location 欄位實作完成報告 (2025-11-09)

#### 修改目標函數確認

經過 CLI Function Mapper 完整調查，確認：
- **Function 8**（整數）：`CLI_modules/cli/analyzer/all_incidents_summary.py` - **正確目標** ✅
- **Function 4.5**（字串）：`modules/gui/accident_analysis/all_incidents_analysis.py` - GUI 模組 ❌

**結論**：Function 8 才是生成 `all_incidents_summary_{year}_{race}_{session}.json` 的 CLI 主函數。

#### 實作內容

1. **新增函數** `extract_track_location(message)` (~line 725):
   - 提取 TURN/CORNER 號碼，返回結構化數據
   - 格式: `{"type": "TURN", "number": 11, "description": "Turn 11"}`

2. **修改** `analyze_all_incidents()` 函數 (~line 320):
   - 在 `incident_detail` 字典中添加 `track_location` 欄位
   - 完全向後兼容，所有原有欄位保持不變

#### 測試結果（2022 Japanese Grand Prix）

- ✅ 總事件數：41
- ✅ 有 `track_location` 的事件：8 個（19.5%）
- ✅ 所有原有欄位完整保留（100% 向後兼容）
- ✅ 函數單元測試：4/4 通過

**發現的 8 個 TURN 事件**：
1. Lap 1 - Turn 1: CAR 5 (VET) 打滑
2. Lap 3 - Turn 12: CAR 10 (GAS) 事件（3 條相關記錄）
3. Lap 24 - Turn 11: CAR 18 (STR) vs CAR 47 (MSC) 碰撞
4. Lap 25 - Turn 11: 上述事件審查結果
5. Lap 29 - Turn 16: CAR 16 (LEC) vs CAR 11 (PER) 賽道邊界（2 條記錄）

**JSON 範例**：
```json
{
  "sequence_number": 11,
  "lap": 1,
  "message": "CAR 5 (VET) SPUN AND CONTINUED AT TURN 1",
  "category": "OTHER",
  "severity": "LOW",
  "sector": null,
  "track_location": {
    "type": "TURN",
    "number": 1,
    "description": "Turn 1"
  }
}
```

#### 驗證腳本

- `test_track_location_field.py` - 函數測試 + JSON 結構檢查
- `verify_backward_compatibility.py` - 向後兼容性驗證

### ⚠️ 待開發

1. **CLI Function 53** - 賽道介紹分析後端
2. **GUI 整合** - CircuitIntroductionModule + MDI
3. **數據映射** - GPS ↔ FastF1 Distance ↔ Corner Number

### 🚀 建議優先順序

1. **高優先級**：
   - ~~修改 Function 4.5/8，新增結構化 `track_location` 欄位~~ ✅ **已完成**
   - 開發 CLI Function 53 基礎架構

2. **中優先級**：
   - GUI 超車統計模組（Function 16.1 包裝）
   - 賽道地圖與高程圖整合

3. **低優先級**：
   - 多賽道對比功能
   - 歷史數據趨勢分析

---

## 📚 參考文件

- **高程資料腳本**: `batch_generate_circuit_elevation_data.py`
- **測試腳本**: `test_elevation_profile_japan.py`, `test_race_control_structure.py`
- **驗證腳本**: `check_circuit_elevation_data.py`, `check_turn_in_incidents.py`
- **track_location 測試**: `test_track_location_field.py`, `verify_backward_compatibility.py`
- **開發文件**: `docs/develop task/circuit_introduction_module_development.md`

---

**報告完成日期**: 2025-11-09  
**最後更新**: 2025-11-09 - track_location 欄位實作完成  
**驗證方法**: 反幻覺編碼原則（grep_search + read_file + 實際測試）  
**下一步更新**: CLI Function 53 開發進度
