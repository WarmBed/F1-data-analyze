# 🔍 Race Weather Forecast (Function 96) 調查報告

**日期：** 2025-10-13  
**調查目標：** `race_weather_forecast.py` 開發狀態與 CLI -f96 整合情況

---

## 📊 調查結果總覽

### ✅ 已完成的部分

#### 1. **核心分析模組** ✅ 完整實作
**檔案位置：** `CLI_modules/cli/analyzer/race_weather_forecast.py`

**功能描述：**
- 賽事天氣預報生成器
- 整合 Open-Meteo API（免費）
- 支援天氣預報（forecast）和歷史數據（archive）
- 智能刷新機制（12 小時自動檢查）
- 參考 Function 99（Season Calendar）的架構模式

**核心功能：**
```python
generate_race_weather_forecast(
    year: Optional[int] = None,
    event_name: Optional[str] = None,
    save_json: bool = True,
    force: bool = False,
    calendar_data: Optional[Dict[str, Any]] = None,
    http_get: Optional[HttpGetter] = None,
) -> RaceWeatherResult
```

**數據來源：**
- `https://api.open-meteo.com/v1/forecast` - 天氣預報
- `https://archive-api.open-meteo.com/v1/archive` - 歷史天氣
- Function 99 Season Calendar - 賽事日期和賽道資訊

**支援賽道：** 33 個賽道座標已配置
- Abu Dhabi, Australia, Austria, Azerbaijan, Bahrain
- Belgian, British, Canadian, Chinese, Dutch
- Emilia Romagna, French, Hungarian, Italian, Japanese
- Las Vegas, Mexico City, Miami, Monaco, Portuguese
- Qatar, Russian, Sakhir, Saudi Arabian, Singapore
- Spanish, São Paulo, Turkish, Tuscan, United States
- 70th Anniversary Grand Prix, Eifel, Styrian

**輸出內容：**
- 賽事前 2 天、前 1 天、比賽當天的天氣預報
- 前兩年同日期的歷史天氣數據
- 逐小時詳細數據（溫度、降雨、雲量、風速、風向）
- 每日摘要（最高/最低溫、降雨總量、平均雲量）

**JSON 輸出目錄：**
- `json/weather/race_weather_forecast_{year}_{event_slug}_{timestamp}.json`

#### 2. **JSON 輸出配置** ✅ 已配置
**檔案位置：** `CLI_modules/cli/core/json_output_config.py`

```python
ANALYSIS_TYPE_DIRECTORIES = {
    # ... 其他配置 ...
    "race_weather_forecast": "weather",  # Line 68
}
```

**輸出目錄：** `json/weather/`

---

### ❌ 缺少的部分

#### 1. **Function Mapper 整合** ❌ 未完成

**問題位置：** `CLI_modules/cli/core/function_mapper.py` Line 95

**當前狀態：**
```python
# 96: self._execute_race_weather_forecast,  # ⚠️ 尚未實現，已禁用
```

**缺少的實作：**
1. `_execute_race_weather_forecast()` 方法
2. Function 96 的啟用（取消註釋）
3. 幫助文檔條目

#### 2. **CLI 幫助文檔** ❌ 未添加

**問題位置：** `f1_analysis_modular_main.py` 的 `show_help()` 方法

**當前狀態：** 沒有 Function 96 的說明

---

## 🔧 整合方案

### 步驟 1: 實作 `_execute_race_weather_forecast()` 方法

**參考範本：** Function 99 (`_execute_season_calendar_analysis`)

**建議實作位置：** `function_mapper.py` Line 3040 附近（Function 99 之後）

```python
def _execute_race_weather_forecast(self, **kwargs):
    """Function 96: 賽事天氣預報 (支援 Open-Meteo API + 12小時智能刷新)"""
    
    try:
        from CLI_modules.cli.analyzer.race_weather_forecast import (
            generate_race_weather_forecast,
            check_weather_forecast_freshness
        )
        
        # 參數處理
        year = kwargs.get("year")
        event_name = kwargs.get("race")  # 從 race 參數映射到 event_name
        force = kwargs.get("force", False)
        
        # 自動選擇年份
        if not year:
            if self.data_loader and getattr(self.data_loader, "year", None):
                year = self.data_loader.year
            else:
                year = datetime.now().year
        
        # 生成天氣預報
        print(f"\n🌤️  賽事天氣預報: {year} {event_name or '(自動選擇下一場比賽)'}")
        print("🔍 數據來源: Open-Meteo API (免費)")
        print("📅 包含: 比賽日前2天預報 + 前2年歷史數據\n")
        
        result = generate_race_weather_forecast(
            year=int(year),
            event_name=event_name,
            save_json=True,
            force=force
        )
        
        return self._standardize_result(result, 96, "賽事天氣預報")
        
    except Exception as exc:
        return {
            "success": False,
            "message": f"賽事天氣預報失敗: {exc}",
            "function_id": "96",
            "data": None,
        }
```

### 步驟 2: 啟用 Function 96

**修改位置：** `function_mapper.py` Line 95

**修改前：**
```python
# 96: self._execute_race_weather_forecast,  # ⚠️ 尚未實現，已禁用
```

**修改後：**
```python
96: self._execute_race_weather_forecast,  # 賽事天氣預報
```

### 步驟 3: 添加幫助文檔

**修改位置：** `f1_analysis_modular_main.py` 的 `show_help()` 方法

**建議插入位置：** Function 97 (Championship Standings) 之前

```python
print("\n96. 🌤️  賽事天氣預報 (Race Weather Forecast)")
print("    ⭐ 狀態：新增功能 (NEW)")
print("    功能描述：獲取比賽週末的天氣預報和歷史天氣數據")
print("    輸入參數：年份、賽事名稱（可選，預設選擇下一場比賽）")
print("    數據來源：Open-Meteo API（免費，無需API Key）")
print("    主要輸出：")
print("      [STATS] JSON格式：")
print("        • Race_Weather_Forecast (天氣預報數據)")
print("          - forecast.days: 比賽日前2天、前1天、當天的預報")
print("          - historical.entries: 前2年同日期的歷史天氣")
print("          - 逐小時數據: 溫度、降雨、雲量、風速、風向")
print("        • Coordinates (賽道座標)")
print("          - latitude, longitude, timezone, circuit, country")
print("        • Calendar_Event (賽事資訊)")
print("          - event_name, round, race_date_local, race_date_utc")
print("      輸出目錄：json/weather/")
print("      智能刷新：12小時自動更新")
print("      支援賽道：33個F1賽道（含座標和時區）")
```

---

## 🧪 測試計畫

### 測試 1: 基本功能測試
```powershell
# 測試：自動選擇下一場比賽
python f1_analysis_modular_main.py -f 96

# 測試：指定年份和賽事
python f1_analysis_modular_main.py -f 96 -y 2025 -r Japan

# 測試：強制刷新
python f1_analysis_modular_main.py -f 96 -y 2025 -r Japan --force
```

### 測試 2: 智能刷新測試
```powershell
# 第一次執行：生成新檔案
python f1_analysis_modular_main.py -f 96 -y 2025 -r Monaco

# 第二次執行（12小時內）：使用快取
python f1_analysis_modular_main.py -f 96 -y 2025 -r Monaco

# 預期輸出：
# "使用快取檔案（X 小時前）"
```

### 測試 3: JSON 輸出驗證
```powershell
# 檢查輸出檔案
dir json\weather\race_weather_forecast_*.json

# 驗證 JSON 結構
python -c "import json; data = json.load(open('json/weather/race_weather_forecast_2025_japan_*.json')); print(json.dumps(data, indent=2, ensure_ascii=False))"
```

---

## 📋 檢查清單

### 必須完成的任務

- [ ] 實作 `_execute_race_weather_forecast()` 方法
- [ ] 啟用 Function 96（取消註釋）
- [ ] 添加幫助文檔條目
- [ ] 執行基本功能測試
- [ ] 驗證 JSON 輸出格式
- [ ] 測試智能刷新機制
- [ ] 測試錯誤處理（無效賽事名稱、網路錯誤等）

### 可選的增強任務

- [ ] 添加 GUI 整合（參考 Season Progress 模組）
- [ ] 添加 API 端點（refactored_api.py）
- [ ] 添加單元測試
- [ ] 文檔更新（README、CHANGELOG）

---

## 🎯 預期功能

### 使用情境 1: 賽前天氣查詢
```bash
# 查詢日本站比賽週末天氣
python f1_analysis_modular_main.py -f 96 -y 2025 -r Japan
```

**輸出範例：**
```
🌤️  賽事天氣預報: 2025 Japan
🔍 數據來源: Open-Meteo API (免費)
📅 包含: 比賽日前2天預報 + 前2年歷史數據

[INFO] Generating latest season calendar data for weather lookup...
[OK] Weather JSON saved to json/weather/race_weather_forecast_2025_japan_20251013T100000Z.json

比賽日前2天 (2025-04-04):
- 溫度: 12°C ~ 18°C
- 降雨機率: 30%
- 風速: 15 km/h (東北風)

比賽日前1天 (2025-04-05):
- 溫度: 13°C ~ 19°C
- 降雨機率: 20%
- 風速: 12 km/h (東風)

比賽當天 (2025-04-06):
- 溫度: 14°C ~ 20°C
- 降雨機率: 10%
- 風速: 10 km/h (東南風)

歷史參考 (2024-04-06):
- 溫度: 15°C ~ 21°C
- 降雨: 0.0 mm
```

### 使用情境 2: 自動選擇下一場比賽
```bash
# 不指定賽事，自動查詢下一場比賽
python f1_analysis_modular_main.py -f 96 -y 2025
```

**功能：**
- 自動從 Season Calendar 選擇最近的未來比賽
- 如果賽季結束，選擇最後一場比賽

---

## 💡 技術亮點

### 1. **智能刷新機制**
- 12 小時內使用快取，避免重複 API 調用
- 參考 Function 99 的成熟架構

### 2. **完整的賽道數據**
- 33 個賽道的經緯度、時區、賽道名稱
- 支援別名映射（如 "Suzuka" → "Japanese Grand Prix"）

### 3. **豐富的數據維度**
- 逐小時詳細數據（溫度、降雨、雲量、風速、風向）
- 每日摘要統計
- 歷史對比（前2年同日期）

### 4. **無需 API Key**
- 使用 Open-Meteo 免費 API
- 無需註冊或認證

---

## 🚀 下一步行動

1. **立即實作** `_execute_race_weather_forecast()` 方法
2. **啟用 Function 96** 並添加幫助文檔
3. **執行測試** 驗證所有功能正常
4. **更新文檔** 標記為已完成功能

**預計完成時間：** 30 分鐘

---

**報告完成** ✅
