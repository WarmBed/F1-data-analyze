# 功能 99 智能刷新機制說明
## 12 小時自動更新賽季日曆

**更新日期**: 2025-10-07  
**功能版本**: v2.1 - 智能刷新機制

---

## 🎯 功能概述

功能 99 現在具備**智能刷新機制**，會自動檢查現有 JSON 檔案的年齡，避免重複生成相同的數據：

- ✅ **< 12 小時**: 自動使用現有檔案，跳過重新生成
- ⚠️ **≥ 12 小時**: 自動重新生成最新數據
- 🔄 **強制模式**: 可手動強制更新

---

## 🚀 使用方式

### 1️⃣ 標準模式（智能刷新）

```powershell
# 執行功能 99 - 自動檢查並決定是否更新
python f1_analysis_modular_main.py -f 99
```

**行為邏輯**:
- 檢查 `json/season_calendar_2020-2025_*.json` 的最新檔案
- 如果檔案 < 12 小時: ✅ 跳過生成，使用現有檔案
- 如果檔案 ≥ 12 小時: 🔄 自動重新生成
- 如果沒有檔案: 🆕 直接生成

### 2️⃣ 強制更新模式

如果您需要立即更新（無論檔案多新），可以在代碼中設定 `force=True`：

```python
# 在 function_mapper.py 中修改
result = generate_season_calendar(save_json=True, all_years=True, force=True)
```

或通過命令列參數（需要擴展 CLI 參數解析）：
```powershell
python f1_analysis_modular_main.py -f 99 --force
```

---

## 📊 執行範例

### 範例 1: 檔案新鮮（< 12 小時）

```
🎯 啟用批量查詢模式: 2020-2025 年所有賽季
🔍 智能刷新機制: 12 小時自動檢查

================================================================================
✅ 賽季日曆檢查
================================================================================
📄 找到最新的日曆檔案:
   路徑: json\season_calendar_2020-2025_20251006T162216Z.json
   年齡: 51 分鐘前 (0.86 小時)
   狀態: ✅ 新鮮（< 12 小時）

💡 提示: 檔案仍在有效期內，跳過重新生成
   如需強制更新，請設定 force=True
================================================================================

✅ 功能 99 執行成功
📄 使用現有日曆檔案（51 分鐘前）
```

### 範例 2: 檔案過期（≥ 12 小時）

```
🎯 啟用批量查詢模式: 2020-2025 年所有賽季
🔍 智能刷新機制: 12 小時自動檢查

================================================================================
⏰ 賽季日曆需要更新
================================================================================
📄 現有檔案:
   路徑: json\season_calendar_2020-2025_20251006T040000Z.json
   年齡: 13 小時 22 分鐘前 (13.37 小時)
   狀態: ⚠️  過期（> 12 小時）

🔄 開始重新生成日曆...
================================================================================

🏎️  F1 賽季賽程批量查詢 (2020-2025)
================================================================================

📅 正在查詢 2020 年賽季...
   ✅ 成功: 17 場賽事 (17 已完成)
📅 正在查詢 2021 年賽季...
   ✅ 成功: 22 場賽事 (22 已完成)
...
```

### 範例 3: 強制更新模式

```
🎯 啟用批量查詢模式: 2020-2025 年所有賽季
🔍 智能刷新機制: 12 小時自動檢查

================================================================================
🔄 強制重新生成模式
================================================================================

🏎️  F1 賽季賽程批量查詢 (2020-2025)
================================================================================

📅 正在查詢 2020 年賽季...
   ✅ 成功: 17 場賽事 (17 已完成)
...
```

---

## 🔧 技術實現

### 新增的函數

#### `check_calendar_freshness()`

檢查賽季日曆 JSON 的新鮮度：

```python
from CLI_modules.cli.analyzer.season_calendar_analysis import check_calendar_freshness

# 檢查批量日曆（2020-2025）
freshness = check_calendar_freshness(all_years=True)

# 返回結果
{
    "exists": true,
    "path": "json/season_calendar_2020-2025_20251006T162216Z.json",
    "file_time": "2025-10-06T16:22:16+00:00",
    "current_time": "2025-10-06T17:14:00+00:00",
    "age_hours": 0.86,
    "age_formatted": "51 分鐘前",
    "is_fresh": true,
    "should_regenerate": false,
    "refresh_interval_hours": 12,
    "reason": "檔案新鮮（0.9小時前生成）"
}
```

#### 修改的函數

**`generate_season_calendar()`**:
```python
def generate_season_calendar(
    year: int = None, 
    *, 
    save_json: bool = True, 
    all_years: bool = False,
    force: bool = False  # 新增參數
) -> SeasonCalendarResult:
```

**`_generate_multi_year_calendar()`**:
```python
def _generate_multi_year_calendar(
    *, 
    save_json: bool = True,
    force: bool = False  # 新增參數
) -> SeasonCalendarResult:
    # 在函數開始時檢查新鮮度
    if not force:
        freshness = check_calendar_freshness(all_years=True)
        if freshness["is_fresh"]:
            # 讀取並返回現有檔案
            ...
```

---

## ⚙️ 配置參數

### 刷新間隔設定

在 `season_calendar_analysis.py` 中：

```python
CALENDAR_REFRESH_HOURS = 12  # 賽季日曆刷新間隔（小時）
```

**可調整範圍**:
- **6 小時**: 適合賽季進行中，頻繁更新
- **12 小時**: 平衡更新頻率和性能（預設）
- **24 小時**: 適合穩定賽季，減少 API 調用

### 修改刷新間隔

```python
# 修改為 6 小時
CALENDAR_REFRESH_HOURS = 6

# 修改為 24 小時
CALENDAR_REFRESH_HOURS = 24
```

---

## 📈 效能優化

### 減少 API 調用

智能刷新機制大幅減少不必要的 API 調用：

| 場景 | 舊版本 | 新版本 (智能刷新) | 減少比例 |
|------|--------|------------------|---------|
| GUI 啟動 (每次) | 1 次 API | 1 次 (首次) | 0% |
| GUI 啟動 (12小時內) | 1 次 API | 0 次 (讀取本地) | **100%** |
| 手動執行 -f99 | 6 次 API (2020-2025) | 0 次 (檔案新鮮) | **100%** |
| 12 小時後 | 6 次 API | 6 次 API | 0% |

**預期節省**:
- 假設每天執行 10 次 GUI 或 CLI
- 舊版本: 10 × 6 = **60 次 API 調用/天**
- 新版本: 2 × 6 = **12 次 API 調用/天**
- **節省 80% API 調用**

### JSON 檔案大小

批量 JSON (2020-2025) 約 **175 KB**，載入速度：
- HDD: < 10ms
- SSD: < 2ms
- RAM 緩存: < 1ms

遠快於 API 調用（通常 500ms - 2s）。

---

## 🔍 檢查當前狀態

### 使用 Python 腳本檢查

```python
from CLI_modules.cli.analyzer.season_calendar_analysis import check_calendar_freshness
import json

# 檢查並顯示狀態
freshness = check_calendar_freshness(all_years=True)
print(json.dumps(freshness, indent=2, ensure_ascii=False))
```

### 使用 PowerShell 檢查

```powershell
# 查找最新的批量日曆檔案
Get-ChildItem -Path json -Filter "season_calendar_2020-2025*.json" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 Name, LastWriteTime, @{
        Name='Age(Hours)'; 
        Expression={[math]::Round(((Get-Date) - $_.LastWriteTime).TotalHours, 2)}
    }

# 輸出範例:
# Name                                        LastWriteTime        Age(Hours)
# ----                                        -------------        ----------
# season_calendar_2020-2025_20251006T162216Z  2025/10/7 上午 12:22      0.86
```

---

## 🎯 使用場景

### 場景 1: 日常開發

**問題**: 反覆測試時重複生成相同數據  
**解決**: 智能刷新自動跳過，節省時間

```powershell
# 第一次執行 - 生成數據
python f1_analysis_modular_main.py -f 99
# → 6 年數據生成，耗時 30 秒

# 5 分鐘後再次執行
python f1_analysis_modular_main.py -f 99
# → 跳過生成，使用現有檔案，耗時 < 1 秒 ✅
```

### 場景 2: GUI 頻繁啟動

**問題**: 每次啟動 GUI 都調用 API  
**解決**: SeasonCalendarProvider 檢查本地檔案新鮮度

```python
# GUI 初始化時
provider = SeasonCalendarProvider()
events = provider.get_completed_events(2025)
# → 如果本地 JSON < 12 小時，直接讀取 ✅
```

### 場景 3: 賽季進行中

**問題**: 賽程可能有變動，需要最新數據  
**解決**: 12 小時自動更新，保持數據新鮮

```
上午 8:00  - 第一次執行，生成新數據
下午 2:00  - 執行，使用緩存（6 小時前）
下午 8:00  - 執行，使用緩存（12 小時前）
晚上 8:01  - 執行，自動更新（超過 12 小時）✅
```

### 場景 4: 需要即時數據

**問題**: 剛剛有新賽事結果，需要立即更新  
**解決**: 使用強制模式

```python
# 強制更新（無論檔案多新）
result = generate_season_calendar(
    save_json=True, 
    all_years=True, 
    force=True  # 強制重新生成
)
```

---

## 🐛 故障排除

### 問題 1: 想要更新但系統跳過

**原因**: 檔案仍在 12 小時內  
**解決方案**:
```python
# 方案 1: 使用 force 模式
generate_season_calendar(all_years=True, force=True)

# 方案 2: 手動刪除舊檔案
Remove-Item json\season_calendar_2020-2025_*.json
python f1_analysis_modular_main.py -f 99

# 方案 3: 調整刷新間隔
CALENDAR_REFRESH_HOURS = 6  # 改為 6 小時
```

### 問題 2: 無法讀取現有檔案

**原因**: JSON 檔案損壞或格式錯誤  
**行為**: 系統會自動回退到重新生成

```
⚠️  讀取現有檔案失敗: JSONDecodeError, 將重新生成
```

### 問題 3: 時間戳不正確

**原因**: 系統時鐘不準確  
**解決方案**:
```powershell
# Windows 同步時間
w32tm /resync

# 檢查系統時間
Get-Date
```

---

## 📊 JSON Metadata 變更

智能刷新後的 JSON 會包含額外的 metadata：

```json
{
  "success": true,
  "message": "使用現有日曆檔案（51 分鐘前）",
  "metadata": {
    "years": [2020, 2021, 2022, 2023, 2024, 2025],
    "generated_at": "2025-10-06T16:22:16+00:00",
    "last_freshness_check": "2025-10-06T17:14:00+00:00",
    "file_age_hours": 0.86,
    "is_fresh": true,
    "refresh_interval_hours": 12,
    "force_regenerated": false,
    ...
  }
}
```

**新增欄位**:
- `last_freshness_check`: 最後檢查時間
- `file_age_hours`: 檔案年齡（小時）
- `is_fresh`: 是否新鮮
- `refresh_interval_hours`: 刷新間隔設定
- `force_regenerated`: 是否強制生成

---

## 🔗 相關功能

- **SeasonCalendarProvider**: GUI 的日曆數據提供者
- **功能 99**: CLI 賽季賽程查詢
- **API Endpoint**: `/api/v2/analysis/execute?function_id=99`

---

## 📝 版本歷史

### v2.1 (2025-10-07)
- ✨ 新增 12 小時智能刷新機制
- ✨ 新增 `check_calendar_freshness()` 函數
- ✨ 新增 `force` 參數支援強制更新
- ✨ 優化輸出訊息，更清晰的狀態提示
- 📊 減少 80% 不必要的 API 調用

### v2.0 (2025-10-07)
- ✨ 新增批量查詢模式 (2020-2025)
- ✨ 新增多年度統計摘要

### v1.0
- 基本單一年份查詢功能

---

**最後更新**: 2025-10-07  
**作者**: F1T 開發團隊
