# 📅 Upcoming Race 邏輯完整說明

**日期**: 2025-10-20  
**版本**: 1.0  
**相關功能**: CLI Function 99 + GUI Season Calendar Provider

---

## 🎯 核心邏輯概述

Upcoming（未開賽）標記是基於 **UTC 時間比較** 的自動判斷系統，用於區分已完賽和未開賽的賽事。

### 🔑 關鍵判斷公式

```python
# CLI 層 (season_calendar_analysis.py, Line 205)
is_completed = bool(race_dt_utc and race_dt_utc <= reference)

# 其中:
# - race_dt_utc: 正賽的 UTC 時間（Session 5 DateUtc）
# - reference: 當前 UTC 時間 (datetime.now(timezone.utc))
# - is_completed=True:  正賽時間 <= 現在 → 已完賽
# - is_completed=False: 正賽時間 > 現在 → 未開賽 (Upcoming)
```

---

## 📊 完整數據流程

### 1️⃣ **CLI 層：數據生成** (Function 99)

**檔案**: `CLI_modules/cli/analyzer/season_calendar_analysis.py`

#### Step 1: 獲取 FastF1 賽程數據
```python
def generate_season_calendar(year: int = None, save_json: bool = True, all_years: bool = False):
    # 從 FastF1 API 獲取賽程
    schedule = fastf1.get_event_schedule(year)
    
    # 獲取當前 UTC 時間作為參考點
    reference = datetime.now(timezone.utc)
```

#### Step 2: 判斷每場賽事是否完賽
```python
def _summarise_event(row: pd.Series, *, reference: datetime) -> Dict[str, Any]:
    # 獲取正賽時間（Session 5 = Race）
    race_dt_utc = _to_datetime(row.get("Session5DateUtc"))
    
    # 核心判斷：正賽時間是否已過
    is_completed = bool(race_dt_utc and race_dt_utc <= reference)
    
    return {
        "event_name": row.get("EventName"),
        "is_completed": is_completed,  # ✅ 關鍵欄位
        "race_date_utc": race_dt_utc.isoformat(),
        "days_until_race": _days_until(race_dt_utc, reference=reference),
        # ...
    }
```

#### Step 3: 導出 JSON 檔案
```json
{
  "2025": {
    "data": [
      {
        "round": 18,
        "event_name": "United States",
        "is_completed": true,
        "race_date_utc": "2025-10-19T19:00:00+00:00"
      },
      {
        "round": 19,
        "event_name": "Mexico",
        "is_completed": false,  // ← Upcoming!
        "race_date_utc": "2025-10-26T20:00:00+00:00",
        "days_until_race": 6
      }
    ]
  }
}
```

**輸出位置**: `json/season_calendar_2020-2025.json`

---

### 2️⃣ **GUI 層：數據讀取與轉換**

**檔案**: `modules/gui/shared/season_calendar_provider.py`

#### Step 1: 讀取 JSON 並轉換為 SeasonEvent 物件
```python
@dataclass
class SeasonEvent:
    round: int
    display_label: str       # "Mexico (2025-10-26)"
    race_key: str            # "Mexico"
    race_date: str           # "2025-10-26"
    is_completed: bool       # ✅ 從 JSON 讀取
    sessions: List[SeasonSession]
    raw_payload: Dict[str, Any]

def _transform_payload(self, payload: Dict[str, Any]) -> List[SeasonEvent]:
    for item in raw_events:
        # 直接讀取 CLI 生成的 is_completed 欄位
        is_completed = bool(item.get("is_completed"))
        
        events.append(
            SeasonEvent(
                race_key=race_key,
                is_completed=is_completed,  # ← 傳遞給 GUI
                # ...
            )
        )
```

#### Step 2: 過濾已完成的 Session
```python
def _extract_sessions(self, session_block: Dict[str, Any], *, reference: datetime):
    # 對於未開賽的賽事，只保留已經發生的練習賽/排位賽
    for idx in range(1, 7):
        utc_dt = self._parse_datetime(session_block.get(f"session{idx}_utc"))
        
        # ⚠️ 過濾未來的 Session
        if utc_dt and utc_dt > reference:
            continue  # 跳過未來的 Session
        
        sessions.append(SeasonSession(code=code, ...))
```

---

### 3️⃣ **GUI 顯示層：添加 [Upcoming] 標籤**

**檔案**: `f1t_gui_main.py`

#### Step 1: 分離已完賽和未開賽賽事
```python
def _refresh_calendar_for_year(self, year: int):
    events = self._get_calendar_events(year)
    
    # 根據 is_completed 欄位分類
    completed_events = [event for event in events if event.is_completed]
    upcoming_events = [event for event in events if not event.is_completed]
```

#### Step 2: 格式化顯示文字
```python
def _format_race_display(self, event: SeasonEvent) -> str:
    # 已完賽：直接顯示
    if event.is_completed:
        return event.display_label  # "Mexico (2025-10-26)"
    
    # 未開賽：添加 [Upcoming] 後綴
    suffix = tr("season_calendar_upcoming_suffix", "[未開賽]")
    return f"{event.display_label} {suffix}"
    # 結果: "Mexico (2025-10-26) [Upcoming]"
```

#### Step 3: 填充到下拉選單
```python
# 先添加已完賽賽事
for event in completed_events:
    label = self._format_race_display(event)  # 無後綴
    self.race_combo.addItem(label, event)

# 插入分隔線
if completed_events and upcoming_events:
    self.race_combo.insertSeparator(self.race_combo.count())

# 添加未開賽賽事（帶 [Upcoming] 後綴）
for event in upcoming_events:
    label = self._format_race_display(event)  # 有後綴
    self.race_combo.addItem(label, event)
```

---

## 🌍 國際化支援

**檔案**: `core/gui_i18n.py`

```python
'season_calendar_upcoming_suffix': {
    'zh': '[未開賽]',
    'en': '[Upcoming]',
    'ja': '[未開催]'
}
```

**範例顯示**：
- 🇺🇸 英文：`Mexico (2025-10-26) [Upcoming]`
- 🇨🇳 中文：`Mexico (2025-10-26) [未開賽]`
- 🇯🇵 日文：`Mexico (2025-10-26) [未開催]`

---

## 🕐 時間判斷細節

### UTC 時間基準

**為什麼使用 UTC？**
- ✅ 全球統一標準，避免時區混淆
- ✅ FastF1 API 提供的時間是 UTC
- ✅ 伺服器和客戶端可能在不同時區

### 判斷時機範例

假設現在是 `2025-10-20 10:00:00 UTC`：

| 賽事 | 正賽時間 (UTC) | 判斷結果 | 原因 |
|------|----------------|---------|------|
| United States | 2025-10-19 19:00 | ✅ Completed | 19 號 < 20 號 |
| Mexico | 2025-10-26 20:00 | ❌ Upcoming | 26 號 > 20 號 |
| Brazil | 2025-11-02 17:00 | ❌ Upcoming | 11 月 > 10 月 |

### 邊界情況處理

```python
# 情況 1: 正賽時間為 None（測試賽事）
if race_dt_utc is None:
    return None  # 不納入日曆

# 情況 2: 正賽時間 == 當前時間（正在進行）
race_dt_utc = datetime(2025, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
reference   = datetime(2025, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
is_completed = (race_dt_utc <= reference)  # True（已開始 = 已完賽）

# 情況 3: 正賽時間 = 當前時間 + 1 秒（即將開始）
race_dt_utc = datetime(2025, 10, 20, 10, 0, 1, tzinfo=timezone.utc)
reference   = datetime(2025, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
is_completed = (race_dt_utc <= reference)  # False（未開始 = Upcoming）
```

---

## 🔄 自動更新機制

### 智能刷新策略

**週期**: 7 天（168 小時）

```python
# season_calendar_analysis.py
CALENDAR_REFRESH_HOURS = 168  # 7 天

def check_calendar_freshness():
    age_hours = (now - file_mtime).total_seconds() / 3600
    is_fresh = age_hours < CALENDAR_REFRESH_HOURS
```

**為什麼是 7 天？**
- ✅ 賽程通常不會頻繁變動
- ✅ 減少不必要的 API 調用
- ✅ 平衡數據新鮮度和系統負載

### 手動刷新

```powershell
# 強制重新生成所有年份的日曆
python f1_analysis_modular_main.py -f 99 --force

# 單一年份刷新
python f1_analysis_modular_main.py -f 99 -y 2025 --force
```

---

## 📝 實際應用範例

### 範例 1: 賽季中期（有已完賽和未開賽）

**當前時間**: 2025-10-20

**GUI 顯示**：
```
Netherlands (2025-08-31)          ← Completed
Italy (2025-09-07)                ← Completed
Singapore (2025-10-05)            ← Completed
United States (2025-10-19)        ← Completed
─────────────────────────────────  ← 分隔線
Mexico (2025-10-26) [Upcoming]    ← Upcoming
Brazil (2025-11-02) [Upcoming]    ← Upcoming
Las Vegas (2025-11-22) [Upcoming] ← Upcoming
```

### 範例 2: 賽季末（全部已完賽）

**當前時間**: 2025-12-10

**GUI 顯示**：
```
Netherlands (2025-08-31)
Italy (2025-09-07)
...
Abu Dhabi (2025-12-08)
─────────────────────────────────
[無未開賽賽事]  ← 沒有 Upcoming Section
```

### 範例 3: 賽季初（全部未開賽）

**當前時間**: 2025-02-01

**GUI 顯示**：
```
[無已完成賽事]  ← 沒有 Completed Section
─────────────────────────────────
Bahrain (2025-03-01) [Upcoming]
Saudi Arabia (2025-03-08) [Upcoming]
Australia (2025-03-15) [Upcoming]
```

---

## 🐛 常見問題排查

### Q1: 為什麼正在進行的比賽顯示為 Completed？

**答**: 系統使用 `race_dt_utc <= reference` 判斷，只要正賽開始時間到了，就標記為 Completed。這是因為：
- 無法準確判斷比賽是否真的結束（FastF1 API 無實時狀態）
- 對於分析功能，「已開始」即可視為「可分析」

### Q2: 時區顯示不一致怎麼辦？

**答**: 
- CLI 導出的 JSON 包含 `race_date_local` 和 `race_date_utc` 兩個欄位
- GUI 顯示使用 `race_date_local`（當地時間）
- 判斷邏輯使用 `race_date_utc`（UTC）
- 確保客戶端系統時區設定正確

### Q3: 如何測試 Upcoming 邏輯？

```python
# 測試腳本
from datetime import datetime, timezone, timedelta

# 模擬未來賽事
race_dt_utc = datetime.now(timezone.utc) + timedelta(days=7)
reference = datetime.now(timezone.utc)

is_completed = bool(race_dt_utc and race_dt_utc <= reference)
print(f"Is Completed: {is_completed}")  # False
print(f"Days Until: {(race_dt_utc - reference).days}")  # 7
```

---

## 📚 相關檔案索引

### CLI 層
- `CLI_modules/cli/core/function_mapper.py` (Line 3040-3090) - Function 99 入口
- `CLI_modules/cli/analyzer/season_calendar_analysis.py` (Line 205) - is_completed 判斷邏輯

### GUI 層
- `modules/gui/shared/season_calendar_provider.py` - 數據提供者
- `f1t_gui_main.py` (Line 6318-6348) - 日曆刷新邏輯
- `f1t_gui_main.py` (Line 6490-6499) - 顯示格式化

### 配置與國際化
- `core/gui_i18n.py` (Line 878) - [Upcoming] 翻譯
- `json/season_calendar_2020-2025.json` - 數據源

---

## ✅ 最佳實踐

1. **定期刷新**: 每週執行一次 `python f1_analysis_modular_main.py -f 99` 保持數據最新
2. **時區意識**: 始終使用 UTC 進行邏輯判斷，本地時間僅用於顯示
3. **邊界測試**: 在賽季開始/結束時測試 GUI 顯示是否正確
4. **API 優先**: 生產環境優先使用 API 獲取數據，本地 JSON 作為備份

---

**文檔版本**: 1.0  
**最後更新**: 2025-10-20  
**維護者**: F1T Development Team
