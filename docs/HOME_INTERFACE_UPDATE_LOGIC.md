# 🏠 Home 介面更新邏輯說明文件

## 📋 文件資訊
- **文件名稱**: Home Interface Update Logic
- **創建日期**: 2025-10-27
- **版本**: 1.0.0
- **適用範圍**: F1 Telemetry Station Pro GUI

---

## 🎯 概述

Home 介面是 F1T GUI 的歡迎頁面，整合了四個核心數據視窗：
1. **賽季進度總覽** (Season Progress) - 左上
2. **天氣時間軸** (Weather Timeline) - 左下
3. **車隊積分榜** (Constructor Standings) - 中欄
4. **車手積分榜** (Driver Standings) - 右欄

所有模組遵循 **API-ONLY 模式**，通過 REST API 動態獲取數據。

---

## 🏗️ 架構總覽

### 整體流程圖
```
f1t_gui_main.py (create_welcome_tab)
    ↓
    ├─ SeasonProgressMDI (左上)
    │   └─ SeasonProgressDataLoader (API-ONLY)
    │       └─ API: function_id=97 (championship_standings)
    │
    ├─ WeatherTimelineMDI (左下)
    │   └─ WeatherTimelineDataLoader
    │       └─ API: function_id=96 (race_weather_forecast)
    │
    ├─ ConstructorStandingsMDI (中欄)
    │   └─ ConstructorStandingsDataLoader
    │       └─ API: function_id=97 (championship_standings)
    │
    └─ DriverStandingsMDI (右欄)
        └─ DriverStandingsDataLoader
            └─ API: function_id=97 (championship_standings)
```

---

## 📊 1. 車手積分榜 (Driver Standings)

### 1.1 數據流向
```
用戶開啟 Home 介面
    ↓
DriverStandingsMDI.__init__(year="2025")
    ↓
DriverStandingsDataLoader.load_data(year=2025, function_id=97)
    ↓
UniversalDataLoader._load_from_api()
    ↓
POST https://api.f1telemetrystationpro.org/api/v2/analyze
    params: {function_id: 97, year: 2025}
    ↓
CLI Backend (championship_standings_analysis.py)
    ↓
FastF1 Ergast API → 獲取車手積分數據
    ↓
返回 JSON: {drivers: [...], metadata: {...}}
    ↓
DriverStandingsDataLoader._transform_data_for_display()
    ↓
DriverStandingsWidget.populate_table(data)
    ↓
顯示車手積分榜表格
```

### 1.2 數據結構
**API 響應格式**:
```json
{
  "success": true,
  "data": {
    "drivers": [
      {
        "position": 1,
        "position_text": "1",
        "points": 393.0,
        "wins": 8,
        "points_delta": null,
        "driver": {
          "code": "VER",
          "full_name": "Max Verstappen",
          "number": 1,
          "nationality": "Dutch"
        },
        "constructors": [
          {"name": "Red Bull Racing", "nationality": "Austrian"}
        ]
      }
    ],
    "metadata": {
      "season_year": 2025,
      "round": 18
    }
  }
}
```

### 1.3 更新邏輯
**檔案**: `modules/gui/driver_standings/driver_standings_data_loader.py`

```python
class DriverStandingsDataLoader(UniversalDataLoader):
    CLI_FUNCTION = 97  # 使用 CLI Function 97
    
    def load_data(self, force_refresh: bool = False):
        """載入車手積分資料"""
        params = {
            "year": self.year,
            "function_id": self.CLI_FUNCTION,
            "force_refresh": force_refresh
        }
        
        # 調用基類 API 載入邏輯
        super().load_data(**params)
    
    def _transform_data_for_display(self, raw_data):
        """轉換為表格顯示格式"""
        drivers = raw_data["data"]["drivers"]
        
        transformed_rows = []
        for entry in drivers:
            driver_info = entry["driver"]
            team = entry["constructors"][0]["name"].replace(" F1 Team", "")
            
            transformed_rows.append({
                "position": entry["position"],
                "driver_code": driver_info["code"],
                "driver_name": driver_info["full_name"],
                "team": team,
                "points": entry["points"],
                "wins": entry["wins"],
                "points_delta": entry["points_delta"]
            })
        
        return {"standings": transformed_rows, ...}
```

### 1.4 刷新策略（三級智能模式）
**智能刷新機制** (CLI Backend):
- **正常模式**: 120 小時 (5 天) - 賽程間期
- **賽前加速模式**: 12 小時 - 賽前 2 天內
- **賽後加速模式**: 6 小時 - 賽後 24 小時內（新增）

```python
def _determine_standings_refresh_interval(year: int) -> float:
    """判斷積分榜刷新間隔 - 三級智能模式"""
    
    # 🔥 最高優先級：賽後 24 小時內（處理處罰、修正）
    if 0 <= hours_since_race <= 24:
        return 6  # 賽後加速模式：6 小時
    
    # 🚨 次要優先級：賽前 2 天內
    if 0 <= days_until_race <= 2:
        return 12  # 賽前加速模式：12 小時
    
    # ✅ 正常模式：賽程間期
    return 120  # 正常模式：5 天
```

**刷新策略時間軸**:
```
賽前 2 天        比賽日        賽後 24 小時          賽程間期
    ↓              ↓                ↓                  ↓
  12小時          12小時           6小時              120小時
  (賽前)          (賽前)          (賽後)             (正常)
```

---

## 🏁 2. 車隊積分榜 (Constructor Standings)

### 2.1 數據流向
與車手積分榜類似，但使用 `data.constructors[]` 欄位。

### 2.2 數據結構
**API 響應格式**:
```json
{
  "success": true,
  "data": {
    "constructors": [
      {
        "position": 1,
        "points": 589.0,
        "wins": 8,
        "points_delta": null,
        "constructor": {
          "id": "mclaren",
          "name": "McLaren F1 Team",
          "nationality": "British"
        }
      }
    ],
    "metadata": {
      "season_year": 2025,
      "round": 18
    }
  }
}
```

### 2.3 更新邏輯
**檔案**: `modules/gui/constructor_standings/constructor_standings_data_loader.py`

```python
class ConstructorStandingsDataLoader(UniversalDataLoader):
    CLI_FUNCTION = 97  # 同樣使用 Function 97
    
    def _load_team_slug_mapping(self):
        """載入車隊名稱 → team_slug 映射表"""
        # 從 team_colors JSON 載入顏色映射
        team_color_files = json_dir.glob(f"team_colors_{year}_*.json")
        
        # 正確路徑: data.teams (不是 team_palette)
        teams_data = color_data["data"]["teams"]
        for team_slug, info in teams_data.items():
            team_name = info["team_name"]
            team_slug_map[team_name] = team_slug
        
        return team_slug_map
    
    def _transform_data_for_display(self, raw_data):
        """轉換為表格顯示格式 + team_slug 映射"""
        constructors = raw_data["data"]["constructors"]
        team_slug_map = self._load_team_slug_mapping()
        
        transformed_rows = []
        for entry in constructors:
            team_name = entry["constructor"]["name"].replace(" F1 Team", "")
            team_slug = team_slug_map.get(team_name, team_name.lower())
            
            transformed_rows.append({
                "position": entry["position"],
                "constructor_name": team_name,
                "team_slug": team_slug,  # ✅ 用於顏色查詢
                "points": entry["points"],
                "wins": entry["wins"],
                "points_delta": entry["points_delta"]
            })
        
        return {"standings": transformed_rows, ...}
```

### 2.4 顏色映射機制
車隊積分榜需要額外的顏色映射邏輯：

**步驟 1**: 載入 `team_colors_{year}_{timestamp}.json`
```json
{
  "data": {
    "teams": {
      "mclaren": {
        "team_name": "McLaren",
        "primary_color": "#FF8000",
        "secondary_color": "#47C7FC"
      }
    }
  }
}
```

**步驟 2**: 建立 `team_name → team_slug` 映射
```python
team_slug_map = {
    "McLaren": "mclaren",
    "Red Bull": "red bull",
    "Ferrari": "ferrari",
    ...
}
```

**步驟 3**: 在顯示時查詢顏色
```python
from modules.gui.themes.color_palette_provider import color_palette_provider

team_slug = row["team_slug"]
bg_color = color_palette_provider.get_team_color(team_slug)
```

---

## 📅 3. 賽季進度總覽 (Season Progress)

### 3.1 數據流向
```
SeasonProgressMDI
    ↓
SeasonProgressDataLoader.load_data(year=2025, function_id=97)
    ↓
API: /api/v2/analyze?function_id=97&year=2025
    ↓
返回: {drivers: [...], constructors: [...]}
    ↓
_compose_season_summary() → 生成摘要文字
    ↓
SeasonProgressWidget.update_display(data)
```

### 3.2 數據結構
**顯示內容**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 2025 年度賽季進度總覽
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 賽程進度
   • 總場次: 24 場
   • 已完成: 18 場
   • 剩餘場次: 6 場

🏆 積分榜領先者
   • 車手領先者: Max Verstappen - 393 分
   • 車隊領先者: McLaren - 589 分

🏁 下一場賽事
   • 名稱: São Paulo Grand Prix
   • 日期: 2025-11-03
   • 國家: Brazil
```

### 3.3 更新邏輯
**檔案**: `modules/gui/season_progress/season_progress_data_loader.py`

```python
class SeasonProgressDataLoader(UniversalDataLoader):
    CLI_FUNCTION = 97
    
    def __init__(self, year: str, parent=None):
        super().__init__(analysis_type="season_progress", parent=parent)
        
        # ⚠️ API-ONLY 模式：完全禁用本地 JSON 回退
        self._allow_local_fallback = False
    
    def _compose_season_summary(self, year, total_events, 
                                 completed_events, upcoming_events, 
                                 next_event):
        """生成賽季摘要文字"""
        base_text = tr(
            "standings_season_summary_base",
            "{year} 年度共 {total} 場賽事，已完成 {completed} 場，剩餘 {upcoming} 場。"
        ).format(year=year, total=total_events, 
                 completed=completed_events, 
                 upcoming=upcoming_events)
        
        if next_event:
            name = next_event["event_name"]
            race_date = next_event["race_date"]
            country = next_event["country"]
            
            details_text = tr(
                "standings_next_event_detail",
                "下一場賽事：{name}（{country}），比賽日期 {date}"
            ).format(name=name, country=country, date=race_date)
            
            return f"{base_text} {details_text}"
        
        return base_text
```

### 3.4 API-ONLY 模式特性
**重要**: 賽季進度模組是**嚴格 API-ONLY** 模式：
- ✅ **允許**: API 請求
- ❌ **禁止**: 本地 JSON 讀取
- ❌ **禁止**: CLI subprocess 調用

```python
# ⚠️ API-ONLY 模式檢查
if not self._allow_local_fallback:
    self._debug("[CALENDAR] ⚠️ API-ONLY mode: Local JSON calendar loading disabled")
    return None
```

---

## 🌦️ 4. 天氣時間軸 (Weather Timeline)

### 4.1 賽事選擇邏輯
**檔案**: `f1t_gui_main.py` (create_welcome_tab)

```python
# 🌦️ Weather Timeline: 優先選擇下一場未開賽的賽事
weather_race = "Japan Grand Prix"  # 預設值

try:
    year_int = int(current_year)
    events = self._season_provider.get_completed_events(year_int)
    
    # 分離已完賽和未開賽的賽事
    completed_events = [e for e in events if e.is_completed]
    upcoming_events = [e for e in events if not e.is_completed]
    
    # ✅ 優先選擇下一場未開賽（天氣預報對未來賽事更有意義）
    if upcoming_events:
        next_event = upcoming_events[0]
        weather_race = next_event.race_key
        print(f"[WELCOME] Weather Timeline: 選擇下一場未開賽 → {weather_race}")
    elif completed_events:
        # 回退：如果沒有未開賽的賽事，使用最新已完賽
        next_event = completed_events[-1]
        weather_race = next_event.race_key
        print(f"[WELCOME] Weather Timeline: 無未開賽賽事，使用最新已完賽 → {weather_race}")
    else:
        weather_race = "Japan"
        print(f"[WELCOME] Weather Timeline: 無賽事數據，使用預設值 → {weather_race}")
    
except Exception as e:
    print(f"[WELCOME] ⚠️ Weather Timeline 賽事選擇失敗: {e}")
    weather_race = "Japan"  # 使用簡短格式
```

### 4.2 數據流向
```
WeatherTimelineMDI(year="2025", event="Sao Paulo")
    ↓
WeatherTimelineDataLoader.load_data(year=2025, event="Sao Paulo", function_id=96)
    ↓
API: /api/v2/analyze?function_id=96&year=2025&event=Sao Paulo
    ↓
CLI Backend (race_weather_forecast_analysis.py)
    ↓
Open-Meteo API → 獲取天氣預報數據
    ↓
返回 JSON: {forecast: {days: [...]}, historical: {...}}
    ↓
WeatherTimelineWidget.display_forecast(data)
```

### 4.3 數據結構
**API 響應格式**:
```json
{
  "forecast": {
    "days": [
      {
        "label": "race_minus_2",
        "date": "2025-11-01",
        "summary": {
          "temperature_max": 28.5,
          "temperature_min": 18.2,
          "precipitation_sum": 2.5,
          "cloudcover_mean": 45.0,
          "windspeed_max": 15.3,
          "winddirection_cardinal": "SE",
          "relativehumidity_mean": 65.0
        }
      },
      {
        "label": "race_minus_1",
        "date": "2025-11-02",
        ...
      },
      {
        "label": "race_day",
        "date": "2025-11-03",
        ...
      }
    ]
  },
  "historical": {
    "entries": {
      "2024_race_minus_0": {...},
      "2023_race_minus_0": {...}
    }
  },
  "calendar_event": {
    "event_name": "São Paulo Grand Prix",
    "race_date": "2025-11-03"
  }
}
```

### 4.4 更新邏輯
**檔案**: `modules/gui/weather_timeline/weather_timeline_data_loader.py`

```python
class WeatherTimelineDataLoader(UniversalDataLoader):
    CLI_FUNCTION = 96  # 天氣預報功能
    
    def __init__(self, year: str, event: str, parent=None):
        super().__init__(analysis_type="weather_timeline", parent=parent)
        
        self.year = str(year)
        self.event = str(event)
        
        # API-ONLY 模式：允許本地 JSON 後備（已存在的檔案）
        self._allow_local_fallback = True
    
    def _validate_data_format(self, raw_data):
        """驗證天氣數據格式"""
        # 必須包含 forecast 和 days
        if "forecast" not in raw_data:
            return False
        
        forecast = raw_data["forecast"]
        if "days" not in forecast or len(forecast["days"]) == 0:
            return False
        
        # 驗證每一天的數據結構
        for day in forecast["days"]:
            required_keys = ["label", "date", "summary"]
            if not all(key in day for key in required_keys):
                return False
        
        return True
    
    def _transform_data_for_display(self, raw_data):
        """轉換為時間軸顯示格式"""
        forecast_days = raw_data["forecast"]["days"]
        historical_entries = raw_data.get("historical", {}).get("entries", {})
        
        # 按日期排序預報數據
        sorted_days = sorted(forecast_days, key=lambda d: d["date"])
        
        return {
            "forecast_days": sorted_days,
            "historical_data": historical_entries,
            "event_info": raw_data.get("calendar_event", {})
        }
```

### 4.5 視覺化邏輯
**天氣圖標映射**:
```python
def _get_weather_icon(self, precipitation, cloudcover):
    """根據降雨和雲量判斷天氣圖標"""
    if precipitation > 5.0:
        return "🌧️ 雨天"
    elif cloudcover > 70.0:
        return "☁️ 多雲"
    elif cloudcover > 30.0:
        return "⛅ 局部多雲"
    else:
        return "☀️ 晴天"
```

**顏色映射**:
```python
def _get_temperature_color(self, temp):
    """根據溫度返回背景顏色"""
    if temp >= 30:
        return "#FF6B6B"  # 紅色：高溫
    elif temp >= 20:
        return "#FFD93D"  # 黃色：溫暖
    elif temp >= 10:
        return "#6BCB77"  # 綠色：涼爽
    else:
        return "#4D96FF"  # 藍色：寒冷
```

---

## 🔄 5. 統一數據載入架構

所有四個模組都繼承自 `UniversalDataLoader`，遵循統一的數據載入流程。

### 5.1 UniversalDataLoader 基類
**檔案**: `modules/gui/base/universal_data_loader_base.py`

```python
class UniversalDataLoader(QObject):
    """通用數據載入器基類 - API-ONLY 模式"""
    
    # 信號定義
    load_started = pyqtSignal()
    load_success = pyqtSignal(dict)
    load_error = pyqtSignal(str)
    load_progress = pyqtSignal(int)
    
    def load_data(self, **kwargs):
        """統一數據載入入口"""
        self.load_started.emit()
        
        # 步驟 1: 嘗試從 API 載入
        if self._load_from_api(**kwargs):
            return
        
        # 步驟 2: API 失敗，檢查是否允許本地回退
        if self._allow_local_fallback:
            if self._load_from_local_json(**kwargs):
                return
        
        # 步驟 3: 所有方法失敗
        self.load_error.emit("數據載入失敗")
    
    def _load_from_api(self, **kwargs):
        """從 API 載入數據"""
        try:
            url = f"{API_BASE_URL}/api/v2/analyze"
            params = {
                "function_id": kwargs["function_id"],
                "year": kwargs["year"],
                ...
            }
            
            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()
            
            raw_data = response.json()
            
            # 驗證數據格式
            if not self._validate_data_format(raw_data):
                return False
            
            # 轉換數據
            display_data = self._transform_data_for_display(raw_data)
            
            # 發送成功信號
            self.load_success.emit(display_data)
            return True
            
        except Exception as e:
            print(f"[API] 載入失敗: {e}")
            return False
    
    def _load_from_local_json(self, **kwargs):
        """從本地 JSON 載入數據（僅當 _allow_local_fallback=True）"""
        if not self._allow_local_fallback:
            return False
        
        # 搜尋匹配的 JSON 檔案
        patterns = self._build_filename_patterns(**kwargs)
        json_files = self._search_json_files(patterns)
        
        if not json_files:
            return False
        
        # 讀取最新的檔案
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        # 驗證並轉換
        if self._validate_data_format(raw_data):
            display_data = self._transform_data_for_display(raw_data)
            self.load_success.emit(display_data)
            return True
        
        return False
```

### 5.2 API-ONLY 模式分級
| 模組 | 允許本地 JSON | 允許 CLI 調用 |
|------|--------------|--------------|
| Driver Standings | ✅ 是 | ❌ 否 |
| Constructor Standings | ✅ 是 | ❌ 否 |
| Season Progress | ❌ **否** | ❌ 否 |
| Weather Timeline | ✅ 是 | ❌ 否 |

**Season Progress 是最嚴格的 API-ONLY 模式**，完全禁用本地 JSON 回退。

---

## 📡 6. API 端點說明

### 6.1 積分榜 API (Function 97)
**端點**: `POST /api/v2/analyze`

**請求參數**:
```json
{
  "function_id": "97",
  "year": 2025,
  "round": "latest",  // 可選
  "include_drivers": true,
  "include_constructors": true,
  "force_refresh": false
}
```

**響應格式**:
```json
{
  "success": true,
  "message": "積分榜分析完成",
  "data": {
    "drivers": [...],
    "constructors": [...],
    "metadata": {
      "season_year": 2025,
      "round": 18,
      "resolved_round": 18,
      "timestamp": "2025-10-27T10:30:00Z"
    },
    "summary": {
      "total_events": 24,
      "completed_events": 18,
      "remaining_events": 6,
      "next_race": {
        "name": "São Paulo Grand Prix",
        "date": "2025-11-03"
      }
    }
  },
  "execution_time": "2.35s"
}
```

### 6.2 天氣預報 API (Function 96)
**端點**: `POST /api/v2/analyze`

**請求參數**:
```json
{
  "function_id": "96",
  "year": 2025,
  "event": "Sao Paulo",
  "force_refresh": false
}
```

**響應格式**:
```json
{
  "success": true,
  "forecast": {
    "days": [...]
  },
  "historical": {
    "entries": {...}
  },
  "calendar_event": {
    "event_name": "São Paulo Grand Prix",
    "race_date": "2025-11-03",
    "circuit_name": "Autódromo José Carlos Pace"
  }
}
```

---

## 🔧 7. CLI 後端分析邏輯

### 7.1 積分榜生成 (Function 97)
**檔案**: `CLI_modules/cli/analyzer/championship_standings_analysis.py`

```python
def generate_championship_standings(
    year: int,
    round_hint: Optional[str] = None,
    force_refresh: bool = False,
    include_drivers: bool = True,
    include_constructors: bool = True,
) -> ChampionshipStandingsResult:
    """
    生成積分榜 JSON
    
    流程:
    1. 檢查緩存新鮮度 (check_standings_freshness)
    2. 如果需要刷新或 force_refresh=True:
       a. 使用 FastF1 Ergast API 獲取數據
       b. 應用車手-車隊覆寫配置 (driver_team_overrides.json)
       c. 計算積分差距 (points_delta)
       d. 提取賽程摘要 (calendar summary)
    3. 導出 JSON 到 json/ 目錄
    4. 返回結構化結果
    """
    
    # 步驟 1: 檢查緩存
    freshness = check_standings_freshness(year)
    
    if freshness["is_fresh"] and not force_refresh:
        print(f"[STANDINGS] ✅ 使用緩存 ({freshness['age_formatted']})")
        return _load_existing_standings(freshness["path"])
    
    # 步驟 2: 從 Ergast API 獲取數據
    ergast = Ergast()
    
    if include_drivers:
        driver_standings_df = ergast.get_driver_standings(
            season=year, 
            round=round_hint or "last"
        ).content[0]
    
    if include_constructors:
        constructor_standings_df = ergast.get_constructor_standings(
            season=year,
            round=round_hint or "last"
        ).content[0]
    
    # 步驟 3: 載入車手-車隊覆寫
    overrides = load_driver_overrides(year)
    
    # 步驟 4: 處理車手積分榜
    drivers_list = []
    for idx, row in driver_standings_df.iterrows():
        driver_code = row["driverCode"]
        
        # 應用覆寫（如果存在）
        if driver_code in overrides:
            team_info = overrides[driver_code]
            constructor_id = team_info["constructor_id"]
            constructor_name = team_info["team_name"]
        else:
            constructor_id = row.get("constructorId")
            constructor_name = row.get("constructorName")
        
        drivers_list.append({
            "position": int(row["position"]),
            "points": float(row["points"]),
            "wins": int(row["wins"]),
            "driver": {
                "code": driver_code,
                "full_name": f"{row['givenName']} {row['familyName']}"
            },
            "constructors": [
                {"name": constructor_name, "id": constructor_id}
            ]
        })
    
    # 步驟 5: 計算積分差距
    leader_points = drivers_list[0]["points"]
    for driver in drivers_list[1:]:
        driver["points_delta"] = leader_points - driver["points"]
    
    # 步驟 6: 提取賽程摘要
    calendar_summary = _extract_calendar_summary(year)
    
    # 步驟 7: 導出 JSON
    output_data = {
        "success": True,
        "data": {
            "drivers": drivers_list,
            "constructors": constructors_list,
            "metadata": {
                "season_year": year,
                "round": resolved_round,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "summary": calendar_summary
        }
    }
    
    json_path = _ensure_json_dir() / f"championship_standings_{year}_R{round}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    return output_data
```

### 7.2 天氣預報生成 (Function 96)
**檔案**: `CLI_modules/cli/analyzer/race_weather_forecast_analysis.py`

```python
def generate_race_weather_forecast(
    year: int,
    event: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    生成賽事天氣預報
    
    流程:
    1. 從 season_calendar 獲取賽事日期和座標
    2. 調用 Open-Meteo API 獲取未來 7 天天氣預報
    3. 提取歷史同期天氣數據（過去 3 年）
    4. 計算天氣摘要統計
    5. 導出 JSON
    """
    
    # 步驟 1: 獲取賽事資訊
    calendar_event = _find_event_in_calendar(year, event)
    
    if not calendar_event:
        raise ValueError(f"找不到賽事: {year} {event}")
    
    race_date = calendar_event["race_date"]
    latitude = calendar_event["circuit_latitude"]
    longitude = calendar_event["circuit_longitude"]
    
    # 步驟 2: 計算預報日期範圍（賽前 2 天到賽後 1 天）
    race_datetime = datetime.strptime(race_date, "%Y-%m-%d")
    forecast_days = [
        race_datetime - timedelta(days=2),  # race_minus_2
        race_datetime - timedelta(days=1),  # race_minus_1
        race_datetime,                       # race_day
        race_datetime + timedelta(days=1)   # race_plus_1
    ]
    
    # 步驟 3: 調用 Open-Meteo API
    forecast_data = _fetch_weather_forecast(
        latitude=latitude,
        longitude=longitude,
        dates=forecast_days
    )
    
    # 步驟 4: 獲取歷史天氣（過去 3 年同期）
    historical_data = _fetch_historical_weather(
        latitude=latitude,
        longitude=longitude,
        years=[year-1, year-2, year-3],
        target_date=race_datetime
    )
    
    # 步驟 5: 組裝輸出數據
    output_data = {
        "forecast": {
            "days": [
                {
                    "label": "race_minus_2",
                    "date": forecast_days[0].strftime("%Y-%m-%d"),
                    "summary": forecast_data[0]
                },
                ...
            ]
        },
        "historical": {
            "entries": historical_data
        },
        "calendar_event": calendar_event
    }
    
    # 步驟 6: 導出 JSON
    json_path = _ensure_json_dir() / f"race_weather_forecast_{year}_{event}_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    return output_data
```

---

## 🔄 8. 自動刷新機制

### 8.1 智能刷新策略（三級模式）
**積分榜刷新間隔** - 根據賽事狀態動態調整：

```python
def _determine_standings_refresh_interval(year: int) -> float:
    """
    智能判斷積分榜刷新間隔 - 三級模式
    
    優先級（由高到低）:
    1. 賽後加速模式：賽後 0-24 小時 → 6 小時刷新
    2. 賽前加速模式：賽前 0-2 天 → 12 小時刷新
    3. 正常模式：賽程間期 → 120 小時刷新（5 天）
    """
    
    # 🔥 最高優先級：賽後 24 小時內（密集監控）
    # 原因：賽後可能有處罰、積分修正、技術檢驗結果
    if 0 <= hours_since_race <= 24:
        print("[REFRESH] 🏁 賽後監控期")
        print("[REFRESH] 🔥 啟用賽後加速模式（6 小時）")
        return 6  # 賽後加速模式
    
    # 🚨 次要優先級：賽前 2 天內（頻繁檢查）
    # 原因：賽前積分榜狀態對比賽策略有重要影響
    if 0 <= days_until_race <= 2:
        print("[REFRESH] �️ 賽事臨近")
        print("[REFRESH] ⚡ 啟用賽前加速模式（12 小時）")
        return 12  # 賽前加速模式
    
    # ✅ 正常模式：賽程間期（穩定期）
    print("[REFRESH] ✅ 使用正常模式（120 小時）")
    return 120  # 正常模式
```

**刷新策略時間軸圖**:
```
        賽前 2 天                比賽日               賽後 24 小時              下一場賽事
           │                      │                        │                        │
           ▼                      ▼                        ▼                        ▼
    ┌──────────────┐      ┌──────────────┐       ┌──────────────┐         ┌──────────────┐
    │   賽前加速   │      │   賽前加速   │       │   賽後加速   │         │   正常模式   │
    │  12 小時刷新 │ ───▶ │  12 小時刷新 │ ───▶  │   6 小時刷新 │ ───▶    │ 120 小時刷新 │
    │              │      │              │       │              │         │   (5 天)     │
    └──────────────┘      └──────────────┘       └──────────────┘         └──────────────┘
         (48h)                 (當天)              (24h 密集)                 (穩定期)
```

**實際範例**:
```
2025-11-01 00:00  →  賽前 2 天（巴西站 11-03）
                     刷新間隔: 12 小時
                     
2025-11-03 14:00  →  比賽進行中
                     刷新間隔: 12 小時（仍在賽前模式）
                     
2025-11-03 16:30  →  比賽結束
                     刷新間隔: 6 小時（切換到賽後模式）
                     
2025-11-03 22:30  →  賽後 6 小時
                     刷新間隔: 6 小時（賽後監控期）
                     
2025-11-04 04:30  →  賽後 12 小時
                     刷新間隔: 6 小時（仍在監控期）
                     
2025-11-04 16:30  →  賽後 24 小時
                     刷新間隔: 120 小時（切換到正常模式）
```

**賽後加速模式的重要性**:
- ✅ **處罰裁決**: 賽後 24 小時內可能有時間處罰或罰分
- ✅ **技術檢驗**: 車輛技術檢驗結果可能導致積分變動
- ✅ **上訴結果**: 車隊上訴裁決結果
- ✅ **數據修正**: FIA 官方積分修正

### 8.2 緩存新鮮度檢查
```python
def check_standings_freshness(year: int) -> Dict[str, Any]:
    """
    檢查積分榜 JSON 是否需要刷新
    
    返回:
    {
        "exists": bool,
        "path": str,
        "age_hours": float,
        "is_fresh": bool,
        "should_regenerate": bool,
        "reason": str,
        "refresh_interval_hours": float  # 動態刷新間隔
    }
    """
    
    # 尋找最新的積分榜 JSON
    pattern = f"championship_standings_{year}_*.json"
    candidates = sorted(json_dir.glob(pattern), 
                        key=lambda p: p.stat().st_mtime, 
                        reverse=True)
    
    if not candidates:
        return {
            "exists": False,
            "should_regenerate": True,
            "reason": "找不到現有積分檔案"
        }
    
    # 計算檔案年齡
    latest_file = candidates[0]
    file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)
    age = datetime.now() - file_mtime
    age_hours = age.total_seconds() / 3600
    
    # 使用智能刷新間隔判斷
    refresh_interval = _determine_standings_refresh_interval(year)
    is_fresh = age_hours < refresh_interval
    
    return {
        "exists": True,
        "path": str(latest_file),
        "age_hours": round(age_hours, 2),
        "age_formatted": _format_timedelta(age),
        "is_fresh": is_fresh,
        "should_regenerate": not is_fresh,
        "reason": "檔案仍在有效期內" if is_fresh else "檔案已過期",
        "refresh_interval_hours": refresh_interval
    }
```

### 8.3 強制刷新
用戶可以在 GUI 中手動觸發強制刷新：
```python
# 在 DriverStandingsMDI 中
def refresh_data(self):
    """手動刷新積分榜數據"""
    self.data_loader.load_data(force_refresh=True)
```

---

## 🎨 9. 視覺化呈現

### 9.1 視窗佈局
```
┌─────────────────────────────────────────────────────────────┐
│ F1 TelemetryStation Pro                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  Season Progress│  Constructor    │  Driver         │   │
│  │  (左上 33%)     │  Standings      │  Standings      │   │
│  │                 │  (中欄 33%)     │  (右欄 34%)     │   │
│  │  • 總場次: 24   │                 │                 │   │
│  │  • 已完成: 18   │  1. McLaren     │  1. Verstappen  │   │
│  │  • 剩餘: 6      │  2. Red Bull    │  2. Norris      │   │
│  │                 │  3. Ferrari     │  3. Leclerc     │   │
│  ├─────────────────┤                 │                 │   │
│  │  Weather        │                 │                 │   │
│  │  Timeline       │                 │                 │   │
│  │  (左下 33%)     │                 │                 │   │
│  │                 │                 │                 │   │
│  │  🌦️ 2 天前      │                 │                 │   │
│  │  ☁️ 1 天前      │                 │                 │   │
│  │  ☀️ 比賽日      │                 │                 │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 顏色主題
**車隊顏色映射** (通過 `color_palette_provider`):
```python
team_colors = {
    "mclaren": "#FF8000",      # 橙色
    "red bull": "#1E41FF",     # 藍色
    "ferrari": "#DC0000",      # 紅色
    "mercedes": "#00D2BE",     # 青色
    "aston martin": "#006F62", # 深綠色
    "alpine": "#0090FF",       # 天藍色
    "williams": "#005AFF",     # 藍色
    "rb": "#2B4562",           # 深藍色
    "kick sauber": "#00E701",  # 綠色
    "haas": "#FFFFFF"          # 白色
}
```

### 9.3 表格樣式
**積分榜表格**:
```python
# 表頭樣式
table.setStyleSheet("""
    QHeaderView::section {
        background-color: #E8E8E8;
        color: #333333;
        font-weight: bold;
        padding: 8px;
        border: none;
        border-bottom: 2px solid #CCCCCC;
    }
    
    QTableWidget {
        gridline-color: #E0E0E0;
        selection-background-color: #D0E8FF;
    }
    
    QTableWidget::item {
        padding: 5px;
    }
""")

# 車隊顏色背景
team_item = QTableWidgetItem(team_name)
team_item.setBackground(QBrush(QColor(team_color)))
table.setItem(row, 3, team_item)
```

---

## 🐛 10. 錯誤處理與日誌

### 10.1 錯誤處理機制
**數據載入錯誤**:
```python
try:
    response = requests.post(API_URL, params=params, timeout=30)
    response.raise_for_status()
    
except requests.Timeout:
    self.load_error.emit("API 請求超時，請稍後再試")
    
except requests.HTTPError as e:
    if e.response.status_code == 404:
        self.load_error.emit("找不到數據（404）")
    elif e.response.status_code == 500:
        self.load_error.emit("伺服器錯誤（500）")
    else:
        self.load_error.emit(f"HTTP 錯誤：{e.response.status_code}")
        
except Exception as e:
    self.load_error.emit(f"未知錯誤：{str(e)}")
```

### 10.2 日誌輸出
**調試日誌**:
```python
def _debug(self, message: str):
    """輸出調試訊息"""
    if self._debug_enabled:
        print(f"[{self.ANALYSIS_TYPE.upper()}] {message}")
```

**範例輸出**:
```
[DRIVER_STANDINGS] 初始化完成: year=2025
[DRIVER_STANDINGS] 開始載入車手積分資料: {'year': '2025', 'function_id': 97}
[API] 請求 URL: https://api.f1telemetrystationpro.org/api/v2/analyze
[API] 請求參數: {'function_id': '97', 'year': 2025}
[API] ✅ API 請求成功 (2.35s)
[VALIDATION] ✅ 數據驗證通過 (20 位車手)
[TRANSFORM] ✅ 轉換 20 位車手資料
[DRIVER_STANDINGS] ✅ 數據載入完成
```

---

## 📚 11. 相關檔案清單

### 11.1 GUI 模組
```
modules/gui/
├── driver_standings/
│   ├── __init__.py
│   ├── driver_standings_data_loader.py      # 車手積分資料載入器
│   ├── driver_standings_widget.py           # 車手積分表格元件
│   └── driver_standings_mdi.py              # MDI 視窗管理
│
├── constructor_standings/
│   ├── __init__.py
│   ├── constructor_standings_data_loader.py # 車隊積分資料載入器
│   ├── constructor_standings_widget.py      # 車隊積分表格元件
│   └── constructor_standings_mdi.py         # MDI 視窗管理
│
├── season_progress/
│   ├── __init__.py
│   ├── season_progress_data_loader.py       # 賽季進度資料載入器
│   ├── season_progress_widget.py            # 賽季進度顯示元件
│   └── season_progress_mdi.py               # MDI 視窗管理
│
├── weather_timeline/
│   ├── __init__.py
│   ├── weather_timeline_data_loader.py      # 天氣時間軸資料載入器
│   ├── weather_timeline_widget.py           # 天氣時間軸圖表元件
│   └── weather_timeline_mdi.py              # MDI 視窗管理
│
└── base/
    └── universal_data_loader_base.py        # 通用資料載入器基類
```

### 11.2 CLI 後端
```
CLI_modules/cli/analyzer/
├── championship_standings_analysis.py       # 積分榜分析（Function 97）
├── race_weather_forecast_analysis.py        # 天氣預報（Function 96）
└── season_calendar_analysis.py              # 賽季日曆
```

### 11.3 配置檔案
```
config/
├── driver_team_overrides.json               # 車手-車隊手動覆寫配置
└── analysis_config.py                       # 分析配置
```

### 11.4 主程式
```
f1t_gui_main.py                              # GUI 主程式（create_welcome_tab）
refactored_api.py                            # REST API 伺服器
```

---

## 🔍 12. 常見問題 (FAQ)

### Q1: 積分榜多久刷新一次？
**A**: 使用三級智能刷新策略：
- **賽後加速模式**: 6 小時（賽後 0-24 小時，最高優先級）
  - 監控處罰、技術檢驗結果、積分修正
- **賽前加速模式**: 12 小時（賽前 0-2 天）
  - 頻繁更新賽前積分狀態
- **正常模式**: 120 小時（5 天，賽程間期）
  - 穩定期降低刷新頻率

**完整刷新週期範例**:
```
賽前 3 天: 120h → 賽前 2 天: 12h → 比賽日: 12h → 
賽後 6h: 6h → 賽後 12h: 6h → 賽後 18h: 6h → 賽後 24h: 6h → 
賽後 25h+: 120h (恢復正常)
```

### Q2: 為什麼天氣時間軸顯示的賽事不是最新的？
**A**: 天氣時間軸優先選擇**下一場未開賽的賽事**，因為天氣預報對未來賽事更有意義。

### Q3: 如何手動強制刷新積分榜？
**A**: 在 MDI 視窗中點擊「刷新」按鈕，會傳遞 `force_refresh=True` 參數給 API。

### Q4: 積分榜的車隊顏色如何映射？
**A**: 通過 `team_colors_{year}_{timestamp}.json` 建立 `team_name → team_slug` 映射，再使用 `color_palette_provider.get_team_color(team_slug)` 獲取顏色。

### Q5: API-ONLY 模式是否完全禁用本地 JSON？
**A**: 不完全是。只有 **Season Progress** 模組是完全禁用（`_allow_local_fallback=False`），其他模組允許在 API 失敗時回退到本地 JSON。

### Q6: 如何添加新的 Home 介面模組？
**A**: 
1. 創建繼承自 `UniversalDataLoader` 的資料載入器
2. 實現 `_validate_data_format()` 和 `_transform_data_for_display()`
3. 創建對應的 Widget 和 MDI 類別
4. 在 `f1t_gui_main.py` 的 `create_welcome_tab()` 中添加模組

---

## 📝 13. 變更歷史

### v1.0.0 (2025-10-27)
- ✅ 初始版本完成
- ✅ 記錄車手積分榜更新邏輯
- ✅ 記錄車隊積分榜更新邏輯
- ✅ 記錄賽季進度總覽更新邏輯
- ✅ 記錄天氣時間軸更新邏輯
- ✅ 記錄智能刷新機制
- ✅ 記錄 API-ONLY 模式政策

### v1.1.0 (2025-10-27) - 三級智能刷新
- ✅ 新增賽後加速模式（6 小時刷新，持續 24 小時）
- ✅ 優化刷新策略優先級（賽後 > 賽前 > 正常）
- ✅ 增強賽後監控功能（處罰、技術檢驗、積分修正）
- ✅ 更新文檔說明刷新策略時間軸

---

## 📞 聯絡資訊

如有問題或需要進一步說明，請參考：
- **專案文檔**: `docs/` 目錄
- **API 文檔**: `docs/API_DOCUMENTATION.md`
- **架構指南**: `.github/copilot-instructions.md`

---

**文件結束**
