```mermaid
flowchart TB
    Start([用戶啟動 GUI]) --> CheckCache{檢查 JSON<br/>是否存在?}
    
    CheckCache -->|不存在| RunCLI[執行 CLI Function 99]
    CheckCache -->|存在| CheckFresh{檢查檔案<br/>是否新鮮?<br/>168 小時內}
    
    CheckFresh -->|過期| RunCLI
    CheckFresh -->|新鮮| ReadJSON[讀取本地 JSON]
    
    RunCLI --> FastF1[調用 FastF1 API<br/>get_event_schedule]
    FastF1 --> GetTime[獲取當前 UTC 時間<br/>reference = now]
    
    GetTime --> LoopEvents{遍歷所有賽事}
    LoopEvents --> GetRaceTime[獲取正賽時間<br/>Session5DateUtc]
    
    GetRaceTime --> Compare{race_dt_utc<br/>≤<br/>reference?}
    
    Compare -->|是| SetCompleted[is_completed = True]
    Compare -->|否| SetUpcoming[is_completed = False<br/>計算 days_until_race]
    
    SetCompleted --> SaveJSON[保存到 JSON]
    SetUpcoming --> SaveJSON
    
    SaveJSON --> MoreEvents{還有賽事?}
    MoreEvents -->|是| LoopEvents
    MoreEvents -->|否| ExportJSON[生成<br/>season_calendar_*.json]
    
    ReadJSON --> ParseJSON[解析 JSON]
    ExportJSON --> ParseJSON
    
    ParseJSON --> CreateEvents[創建 SeasonEvent 物件<br/>包含 is_completed 欄位]
    
    CreateEvents --> SplitEvents[分離賽事]
    SplitEvents --> CompletedList[completed_events =<br/>is_completed == True]
    SplitEvents --> UpcomingList[upcoming_events =<br/>is_completed == False]
    
    CompletedList --> FormatCompleted[格式化顯示:<br/>race_key + date]
    UpcomingList --> FormatUpcoming[格式化顯示:<br/>race_key + date + suffix]
    
    FormatUpcoming --> AddSuffix[添加後綴:<br/>EN: [Upcoming]<br/>ZH: [未開賽]<br/>JA: [未開催]]
    
    FormatCompleted --> AddToCombo[添加到 race_combo]
    AddSuffix --> AddToCombo
    
    AddToCombo --> InsertSeparator{有已完賽<br/>且有未開賽?}
    InsertSeparator -->|是| AddSeparator[插入分隔線]
    InsertSeparator -->|否| DisplayGUI[顯示在 GUI]
    AddSeparator --> DisplayGUI
    
    DisplayGUI --> End([用戶看到<br/>分類的賽事列表])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style Compare fill:#fff4e6
    style SetCompleted fill:#d4edda
    style SetUpcoming fill:#cce5ff
    style AddSuffix fill:#fff3cd
    style FastF1 fill:#f8d7da
```

# Upcoming Race 判斷流程圖

## 關鍵決策點說明

### 1. UTC 時間比較
```python
is_completed = bool(race_dt_utc and race_dt_utc <= reference)
```

- **已完賽**: 正賽時間 ≤ 當前時間
- **未開賽**: 正賽時間 > 當前時間

### 2. 時間節點範例

**當前時間**: 2025-10-20 10:00:00 UTC

| 賽事 | 正賽時間 (UTC) | 比較結果 | 狀態 |
|------|----------------|---------|------|
| United States | 2025-10-19 19:00 | 19 號 ≤ 20 號 | ✅ Completed |
| Mexico | 2025-10-26 20:00 | 26 號 > 20 號 | ❌ Upcoming |

### 3. GUI 顯示效果

```
┌────────────────────────────────────┐
│ Race Selector                      │
├────────────────────────────────────┤
│ Netherlands (2025-08-31)           │ ← Completed
│ Italy (2025-09-07)                 │ ← Completed
│ Singapore (2025-10-05)             │ ← Completed
│ United States (2025-10-19)         │ ← Completed
├────────────────────────────────────┤ ← Separator
│ Mexico (2025-10-26) [Upcoming]     │ ← Upcoming
│ Brazil (2025-11-02) [Upcoming]     │ ← Upcoming
│ Las Vegas (2025-11-22) [Upcoming]  │ ← Upcoming
└────────────────────────────────────┘
```

## 數據流向

```
FastF1 API
    ↓
CLI Function 99
    ↓
JSON 檔案 (with is_completed)
    ↓
SeasonCalendarProvider
    ↓
GUI race_combo (with [Upcoming] suffix)
    ↓
用戶界面
```

## 刷新策略

```
每 7 天自動檢查 → 過期則重新生成 → 更新 JSON → GUI 自動載入
```
