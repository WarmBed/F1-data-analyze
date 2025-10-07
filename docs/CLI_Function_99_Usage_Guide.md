# CLI 功能 99 使用指南
## 賽季賽程批量查詢 (2020-2025)

**更新日期**: 2025-10-07  
**功能版本**: v2.0 - 支援批量查詢

---

## 📋 功能概述

CLI 功能 99 已升級，現在預設會**批量查詢 2020-2025 年所有賽季**的賽程資料，並輸出為單一 JSON 檔案。

### ✨ 新功能特點

- ✅ **批量查詢**: 一次性查詢 2020-2025 共 6 個賽季
- ✅ **完整數據**: 包含所有賽事的詳細會話時間
- ✅ **統計摘要**: 自動計算總賽事數、已完成/未來賽事
- ✅ **單一 JSON**: 所有年份數據整合在一個檔案中
- ✅ **向後兼容**: 仍支援單一年份查詢模式

---

## 🚀 使用方式

### 模式 1: 批量查詢 (預設，2020-2025)

```powershell
# 查詢所有年份 (2020-2025)
python f1_analysis_modular_main.py -f 99
```

**輸出範例**:
```
🎯 啟用批量查詢模式: 2020-2025 年所有賽季

================================================================================
🏎️  F1 賽季賽程批量查詢 (2020-2025)
================================================================================

📅 正在查詢 2020 年賽季...
   ✅ 成功: 17 場賽事 (17 已完成)
📅 正在查詢 2021 年賽季...
   ✅ 成功: 22 場賽事 (22 已完成)
📅 正在查詢 2022 年賽季...
   ✅ 成功: 22 場賽事 (22 已完成)
📅 正在查詢 2023 年賽季...
   ✅ 成功: 23 場賽事 (23 已完成)
📅 正在查詢 2024 年賽季...
   ✅ 成功: 24 場賽事 (24 已完成)
📅 正在查詢 2025 年賽季...
   ✅ 成功: 23 場賽事 (17 已完成)

💾 JSON 已儲存: json\season_calendar_2020-2025_20251007T120000Z.json

================================================================================
📊 總結:
   • 總賽事數: 131
   • 已完成: 125
   • 未來賽事: 6
================================================================================
```

### 模式 2: 單一年份查詢 (傳統模式)

如果需要只查詢特定年份，可以在代碼中設定 `all_years=False`：

```python
# 在 function_mapper.py 中修改
result = generate_season_calendar(int(year), save_json=True, all_years=False)
```

或通過命令列參數：
```powershell
python f1_analysis_modular_main.py -f 99 -y 2024
```

---

## 📦 輸出 JSON 結構

### 批量查詢模式 JSON 結構

```json
{
  "success": true,
  "message": "2020-2025 年賽季賽程查詢完成",
  "metadata": {
    "years": [2020, 2021, 2022, 2023, 2024, 2025],
    "generated_at": "2025-10-07T12:00:00+00:00",
    "total_events_all_years": 131,
    "completed_events_all_years": 125,
    "upcoming_events_all_years": 6,
    "cache_enabled": false,
    "output_file": "json/season_calendar_2020-2025_20251007T120000Z.json"
  },
  "data": {
    "2020": {
      "success": true,
      "message": "2020 年賽季賽程查詢成功",
      "metadata": {
        "year": 2020,
        "total_rounds": 17,
        "completed_rounds": 17,
        "upcoming_rounds": 0
      },
      "data": [
        {
          "round": 1,
          "event_name": "Austrian Grand Prix",
          "official_name": "FORMULA 1 ROLEX GROSSER PREIS VON ÖSTERREICH 2020",
          "country": "Austria",
          "location": "Spielberg",
          "is_completed": true,
          "race_date_local": "2020-07-05T15:10:00+02:00",
          "race_date_utc": "2020-07-05T13:10:00+00:00",
          "session_dates": {
            "session1_name": "Practice 1",
            "session1_local": "2020-07-03T11:00:00+02:00",
            "session1_utc": "2020-07-03T09:00:00+00:00",
            "session2_name": "Practice 2",
            "session3_name": "Practice 3",
            "session4_name": "Qualifying",
            "session5_name": "Race"
          }
        }
        // ... 更多賽事
      ],
      "summary": {
        "last_completed_event": {
          "round": 17,
          "event_name": "Abu Dhabi Grand Prix",
          "race_date_local": "2020-12-13T17:10:00+04:00"
        }
      }
    },
    "2021": { /* 2021 年數據 */ },
    "2022": { /* 2022 年數據 */ },
    "2023": { /* 2023 年數據 */ },
    "2024": { /* 2024 年數據 */ },
    "2025": { /* 2025 年數據 */ }
  },
  "summary": {
    "years_covered": 6,
    "total_events": 131,
    "completed_events": 125,
    "upcoming_events": 6
  }
}
```

### 單一年份模式 JSON 結構

```json
{
  "success": true,
  "message": "2024 年賽季賽程查詢成功",
  "metadata": {
    "year": 2024,
    "generated_at": "2025-10-07T12:00:00+00:00",
    "total_rounds": 24,
    "completed_rounds": 24,
    "upcoming_rounds": 0,
    "output_file": "json/season_calendar_2024_20251007T120000Z.json"
  },
  "data": [
    // 賽事列表
  ],
  "summary": {
    "last_completed_event": { /* 最後完成的賽事 */ },
    "next_event": { /* 下一場賽事 (如有) */ }
  }
}
```

---

## 📊 數據欄位說明

### 頂層欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `success` | boolean | 查詢是否成功 |
| `message` | string | 執行狀態訊息 |
| `metadata` | object | 元數據資訊 |
| `data` | object/array | 實際賽程數據 |
| `summary` | object | 統計摘要 |

### 賽事欄位 (每個 event)

| 欄位 | 類型 | 說明 |
|------|------|------|
| `round` | integer | 分站編號 |
| `event_name` | string | 賽事名稱 (例: "Japanese Grand Prix") |
| `official_name` | string | 官方完整名稱 |
| `country` | string | 國家 |
| `location` | string | 舉辦城市 |
| `is_completed` | boolean | 是否已完成 |
| `race_date_local` | string | 比賽日期 (當地時間 ISO 8601) |
| `race_date_utc` | string | 比賽日期 (UTC ISO 8601) |
| `days_until_race` | integer/null | 距離比賽天數 (已完成為 null) |
| `session_dates` | object | 所有會話時間 |

### 會話時間欄位

每個賽事包含 5 個會話 (Practice 1-3, Qualifying, Race):

| 欄位格式 | 說明 |
|----------|------|
| `session{1-5}_name` | 會話名稱 |
| `session{1-5}_local` | 當地時間 (ISO 8601) |
| `session{1-5}_utc` | UTC 時間 (ISO 8601) |

---

## 🔧 進階配置

### 修改預設行為

在 `CLI_modules/cli/core/function_mapper.py` 中的 `_execute_season_calendar_analysis()` 方法:

```python
def _execute_season_calendar_analysis(self, **kwargs):
    # 修改這行來改變預設行為
    all_years = kwargs.get("all_years", True)  # True=批量, False=單一年份
    
    if all_years:
        result = generate_season_calendar(save_json=True, all_years=True)
    else:
        # 單一年份邏輯
        ...
```

### 自定義年份範圍

在 `CLI_modules/cli/analyzer/season_calendar_analysis.py` 的 `_generate_multi_year_calendar()` 函數:

```python
def _generate_multi_year_calendar(*, save_json: bool = True):
    # 修改這行來改變年份範圍
    years = list(range(2020, 2026))  # 改為 range(2018, 2026) 可查詢 2018-2025
    ...
```

---

## 💡 使用建議

### 1. GUI 整合
批量 JSON 可用於 GUI 模組的年份選擇器：

```python
# 讀取批量 JSON
with open("season_calendar_2020-2025_xxx.json") as f:
    all_seasons = json.load(f)

# 提取所有年份
available_years = list(all_seasons["data"].keys())

# 填充下拉選單
for year in available_years:
    year_data = all_seasons["data"][year]
    if year_data["success"]:
        combo_box.addItem(year, year_data)
```

### 2. 賽事查找
快速查找特定年份的賽事：

```python
def find_race_info(all_seasons_json, year, race_name):
    year_data = all_seasons_json["data"][str(year)]
    for event in year_data["data"]:
        if race_name.lower() in event["event_name"].lower():
            return event
    return None

# 使用範例
japan_2024 = find_race_info(all_seasons, 2024, "Japan")
print(f"比賽時間: {japan_2024['race_date_local']}")
```

### 3. 統計分析
計算多年度統計：

```python
def calculate_season_stats(all_seasons_json):
    stats = {
        "total_races_per_year": {},
        "average_races_per_year": 0,
        "countries_visited": set()
    }
    
    for year, year_data in all_seasons_json["data"].items():
        if year_data["success"]:
            total_rounds = year_data["metadata"]["total_rounds"]
            stats["total_races_per_year"][year] = total_rounds
            
            for event in year_data["data"]:
                stats["countries_visited"].add(event["country"])
    
    stats["average_races_per_year"] = (
        sum(stats["total_races_per_year"].values()) / 
        len(stats["total_races_per_year"])
    )
    stats["countries_visited"] = list(stats["countries_visited"])
    
    return stats
```

---

## 🐛 故障排除

### 問題 1: 執行後沒有輸出

**原因**: FastF1 警告訊息被壓制  
**解決**: 檢查 `json/` 目錄中是否有生成的檔案

```powershell
Get-ChildItem -Path json -Filter "season_calendar_2020-2025*.json" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1
```

### 問題 2: 某些年份查詢失敗

**原因**: FastF1 API 限制或網路問題  
**解決**: 
1. 檢查 JSON 中對應年份的 `success` 欄位
2. 重新執行查詢
3. 檢查是否啟用了緩存

### 問題 3: JSON 檔案過大

**原因**: 包含 6 年完整數據  
**解決**: 
- 使用 JSON 壓縮儲存
- 或改用單一年份查詢模式
- 或實作 JSON 分割功能

---

## 📈 效能優化

### 緩存建議

啟用 FastF1 緩存以提升查詢速度：

```python
# 在 season_calendar_analysis.py 中確保啟用
fastf1.Cache.enable_cache("f1_analysis_cache")
```

### 並行查詢 (未來規劃)

可改用 `concurrent.futures` 並行查詢多年份：

```python
from concurrent.futures import ThreadPoolExecutor

def _generate_multi_year_calendar_parallel():
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(generate_season_calendar, year, save_json=False): year
            for year in range(2020, 2026)
        }
        # ... 處理結果
```

---

## 📝 版本歷史

### v2.0 (2025-10-07)
- ✨ 新增批量查詢模式 (2020-2025)
- ✨ 新增多年度統計摘要
- ✨ 改善 JSON 輸出結構
- ✅ 保持向後兼容性

### v1.0 (原始版本)
- 基本單一年份查詢功能

---

## 🔗 相關功能

- **功能 1**: 降雨分析
- **功能 12**: 圈速比較
- **功能 99**: 賽季賽程查詢 ⬅️ 當前功能

---

## 📞 技術支援

如有問題或建議，請參考：
- 專案 GitHub Issues
- 開發團隊 Discord
- 技術文檔: `docs/` 目錄

---

**最後更新**: 2025-10-07  
**作者**: F1T 開發團隊
