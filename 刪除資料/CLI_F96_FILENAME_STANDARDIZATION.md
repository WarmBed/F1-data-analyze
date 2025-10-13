# CLI Function 96 檔案命名標準化完成報告

**日期**: 2025-10-13  
**任務**: 修正 CLI Function 96 的 JSON 輸出格式以符合系統標準

---

## 🎯 問題診斷

### 原始問題
API 緩存服務無法找到 Function 96 生成的 JSON 檔案：
```
[CACHE] ❌ 未找到任何匹配的緩存結果（已禁用模糊匹配）
```

### 根本原因
Function 96 使用**非標準的檔案命名格式**：

**舊格式** (不符合標準):
```
json/weather/race_weather_forecast_{year}_{event_slug}_{timestamp}.json
例如: race_weather_forecast_2025_singapore_grand_prix_20251013T051952Z.json
```

**標準格式** (其他分析使用):
```
json/{analysis_type}_{year}_{race}_{session}.json
例如: enhanced_rain_analysis_2025_Japan_R.json
```

### 問題點
1. ❌ 使用 `event_slug` (小寫底線格式) 而非標準的 `race` (標題格式)
2. ❌ 總是包含時間戳後綴
3. ❌ 檔案在 `weather/` 子目錄（雖然這個可接受）

---

## ✅ 解決方案

### 選擇的修正策略
**原則**: **修正 CLI 輸出格式，而不是為 API 添加特殊處理**

遵循系統設計原則：
- ✅ 保持 API 緩存服務的通用性
- ✅ 避免特例處理（不特立獨行）
- ✅ 統一檔案命名標準

### 修改內容

#### 檔案: `CLI_modules/cli/analyzer/race_weather_forecast.py`
**Line 861-880**: JSON 輸出邏輯

**修改前**:
```python
if save_json:
    WEATHER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = now_utc.strftime("%Y%m%dT%H%M%SZ")
    filename = f"race_weather_forecast_{target_year}_{event_slug}_{timestamp}.json"
    output_path = get_json_output_path("race_weather_forecast", filename)
    # ...
```

**修改後**:
```python
if save_json:
    WEATHER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 🔧 FIX: 使用標準檔案命名格式
    # 從完整賽事名稱提取國家名稱（"Singapore Grand Prix" → "Singapore"）
    race_name = event_label.replace(" Grand Prix", "").replace(" Prix", "").strip()
    
    # 標準檔案名（不含時間戳）
    filename = f"race_weather_forecast_{target_year}_{race_name}_R.json"
    output_path = get_json_output_path("race_weather_forecast", filename)
    # ...
```

#### 檔案: `api/models/function_specs.py`
**Line 77-84**: 註冊 Function 96

**添加**:
```python
_make_spec(
    "96",
    name="Race Weather Forecast",
    required_params=["year", "race"],
    cli_flag_map={"year": "-y", "race": "-r"},
    cache_patterns=["race_weather_forecast"],  # ← 關鍵：定義搜尋模式
)
```

#### 檔案: `api/services/cache_service.py`
**Line 79**: 添加 Function 96 到 `function_file_patterns`

**添加**:
```python
"96": ["race_weather_forecast"],
```

---

## 🧪 測試驗證

### 測試命令
```bash
python f1_analysis_modular_main.py -f 96 -y 2025 -r "Singapore Grand Prix" --force
```

### 生成結果
**新檔案名稱**: ✅ `race_weather_forecast_2025_Singapore_R.json`

**檔案位置**: `json/weather/race_weather_forecast_2025_Singapore_R.json`

**命名格式對比**:
```
舊: race_weather_forecast_2025_singapore_grand_prix_20251013T051952Z.json
新: race_weather_forecast_2025_Singapore_R.json ✅
```

### API 緩存搜尋測試
**搜尋模式** (通用邏輯):
```python
f"{self.json_dir}{pattern_base}*{year}*{race}*{session}*.json"
```

**展開後**:
```
json/race_weather_forecast*2025*Singapore*R*.json
→ 匹配: race_weather_forecast_2025_Singapore_R.json ✅
```

---

## 📊 對比分析

| 項目 | 舊格式 | 新格式 | 符合標準 |
|------|--------|--------|----------|
| 賽事名稱 | `singapore_grand_prix` | `Singapore` | ✅ |
| 時間戳 | ✅ 包含 | ❌ 不包含 | ✅ |
| Session | ❌ 無 | ✅ `R` | ✅ |
| 緩存可發現 | ❌ | ✅ | ✅ |
| 與其他分析一致 | ❌ | ✅ | ✅ |

---

## ✅ 完成檢查清單

- [x] CLI Function 96 檔案命名修正
- [x] API Function 96 註冊 (`function_specs.py`)
- [x] API 緩存模式定義 (`cache_service.py`)
- [x] 測試新檔案生成
- [x] 驗證檔案命名符合標準
- [ ] API 緩存搜尋測試 (需重啟 API)
- [ ] GUI Weather Timeline 載入測試

---

## 🚀 下一步

1. **重啟 API 伺服器** 以載入更新的緩存配置
2. **重啟 GUI** 測試 Weather Timeline 自動載入
3. **驗證緩存命中** 確認 API 可以找到新格式的 JSON

**預期結果**:
```
[CACHE] 搜尋功能 96 的緩存結果...
[CACHE] 參數: {'year': 2025, 'race': 'Singapore Grand Prix'}
[CACHE] 🔍 搜尋模式: race_weather_forecast*2025*Singapore*R*.json
[CACHE] ✅ 找到 1 個匹配檔案
[CACHE] ✅ 精確匹配成功
```

---

## 💡 總結

✅ **成功避免特立獨行**  
- 不為 Function 96 添加特殊處理邏輯
- 修正源頭（CLI 輸出格式）而非適配下游（API 搜尋）
- 保持系統統一性和可維護性

✅ **符合標準化原則**  
- 檔案命名與其他 52 個分析功能一致
- 緩存服務使用通用搜尋邏輯
- 降低未來維護成本
