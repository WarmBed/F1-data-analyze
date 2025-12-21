# 🔍 Speed vs Speed Diff - X→D 按鈕觸發邏輯完整對比報告

**對比日期**：2025-11-14  
**對比方法**：遵循 `0.標準化對比流程.md` 和 `0_關鍵詢問.md`  
**觸發場景**：用戶按下「X→D」按鈕（從跨賽事模式切換到普通模式）

---

## 📋 基本資訊

**功能名稱**：X→D 按鈕觸發的跨賽事數據載入邏輯

**模組 A（參考模組）**：Speed Analysis (`speed_analysis_mdi.py`)

**模組 B（對比模組）**：Speed Diff Analysis (`speeddiff_analysis_mdi.py`)

**涉及的核心方法**：
1. `update_cross_event_comparison()` - 跨賽事比較參數更新
2. `_on_cross_event_data_loaded()` - 跨賽事數據載入成功處理
3. `update_from_shared_params()` - 從全域共享參數池更新（X→D 觸發入口）

---

## 🔍 階段 1：方法定位

### 1.1 方法位置

| 方法 | Speed Analysis | Speed Diff Analysis |
|------|----------------|---------------------|
| `update_cross_event_comparison` | Line 1013-1086 | Line 1544-1603 |
| `_on_cross_event_data_loaded` | Line 1087-1156 | Line 1605-1701 |
| `update_from_shared_params` | Line 1157-1227 | Line 1702-1772 |

### 1.2 調用鏈追蹤

**觸發流程**：
```
用戶按下 X→D 按鈕
    ↓
主 GUI 調用 update_from_shared_params(params)
    ↓
檢測 is_cross_event = True
    ↓
調用 update_cross_event_comparison(...)
    ↓
創建 CrossEventComparisonWorker
    ↓
Worker.success.connect(_on_cross_event_data_loaded)
    ↓
API 返回數據 → _on_cross_event_data_loaded(result)
    ↓
構建 chart_data → _update_chart(chart_data)
```

---

## 📖 方法 1：update_cross_event_comparison()

### 方法簽名對比

#### Speed Analysis (Line 1013-1015)
```python
def update_cross_event_comparison(self, year1: str, race1: str, session1: str, driver1: str, lap1: int,
                                 year2: str, race2: str, session2: str, driver2: str, lap2: int,
                                 is_fastest: bool = False, use_time_axis: bool = False) -> bool:
```

#### Speed Diff Analysis (Line 1544-1546)
```python
def update_cross_event_comparison(self, year1: str, race1: str, session1: str, driver1: str, lap1: int,
                                  year2: str, race2: str, session2: str, driver2: str, lap2: int,
                                  is_fastest: bool = False, use_time_axis: bool = False):
```

**差異 #1：返回類型註解**
- Speed: `-> bool:` ✅ 有返回類型註解
- Speed Diff: 無返回類型註解 ⚠️

**影響**：低（功能無影響，只是類型提示缺失）

---

### Docstring 對比

#### Speed Analysis (Line 1016)
```python
"""更新跨賽事比較參數（支援跨年度/跨賽段）"""
```

#### Speed Diff Analysis (Line 1547-1556)
```python
"""
更新跨賽事比較參數

參數：
- year1, race1, session1, driver1, lap1: 車手 1 的賽事資訊
- year2, race2, session2, driver2, lap2: 車手 2 的賽事資訊
- is_fastest: 是否使用最快圈（暫未使用）
- use_time_axis: 是否使用時間軸模式
"""
```

**差異 #2：Docstring 詳細度**
- Speed: 簡短單行
- Speed Diff: 詳細多行，包含參數說明 ✅

**影響**：低（文檔質量差異）

---

### 日誌前綴對比 (Line 1017-1020 vs 1557-1560)

#### Speed Analysis
```python
try:
    print(f"[CROSS-EVENT] ========== 跨賽事比較更新 ==========")
    print(f"[CROSS-EVENT] 車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
    print(f"[CROSS-EVENT] 車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
    print(f"[CROSS-EVENT] 🕒 時間軸模式: {use_time_axis}")
```

#### Speed Diff Analysis
```python
try:
    print(f"[SPEEDDIFF-CROSS-EVENT] ========== 更新跨賽事比較參數 ==========")
    print(f"[SPEEDDIFF-CROSS-EVENT] 車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
    print(f"[SPEEDDIFF-CROSS-EVENT] 車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
    print(f"[SPEEDDIFF-CROSS-EVENT] 時間軸模式: {use_time_axis}")
```

**差異 #3：日誌前綴**
- Speed: `[CROSS-EVENT]`
- Speed Diff: `[SPEEDDIFF-CROSS-EVENT]`

**差異 #4：emoji 使用**
- Speed: `🕒 時間軸模式`
- Speed Diff: `時間軸模式` (無 emoji)

**影響**：低（日誌格式差異）

---

### 參數保存邏輯對比 (Line 1022-1033 vs 1562-1573)

#### Speed Analysis
```python
# 保存跨賽事比較的參數
self.driver1_year = year1
self.driver1_race = race1
self.driver1_session = session1
self.driver1 = driver1
self.lap1 = lap1

self.driver2_year = year2
self.driver2_race = race2
self.driver2_session = session2
self.driver2 = driver2
self.lap2 = lap2
```

#### Speed Diff Analysis
```python
# 儲存所有參數
self.driver1_year = year1
self.driver1_race = race1
self.driver1_session = session1
self.driver1 = driver1
self.lap1 = lap1

self.driver2_year = year2
self.driver2_race = race2
self.driver2_session = session2
self.driver2 = driver2
self.lap2 = lap2
```

**差異 #5：註釋用詞**
- Speed: `# 保存跨賽事比較的參數`
- Speed Diff: `# 儲存所有參數`

**影響**：無（功能完全一致）

---

### 同步模式停用對比 (Line 1035-1036 vs 1575-1577)

#### Speed Analysis
```python
# ⚠️ 關鍵：跨賽事比較時停用同步，避免被 Update All Analysis 覆蓋
self.sync_driver_lap_enabled = False
print(f"[CROSS-EVENT] ⚠️ 已停用同步模式 (sync_driver_lap_enabled = False)")
```

#### Speed Diff Analysis
```python
# 關鍵：取消同步模式（避免觸發遞迴更新）
self.sync_driver_lap_enabled = False
self.use_time_axis = use_time_axis
```

**差異 #6：註釋和日誌**
- Speed: 有詳細註釋 + 日誌輸出 ✅
- Speed Diff: 簡短註釋 + **直接保存 use_time_axis** + **無日誌** ⚠️

**影響**：中（Speed Diff 缺少日誌，但多了 use_time_axis 保存）

---

### 時間軸設定保存對比 (Line 1038-1039 vs 1577)

#### Speed Analysis
```python
# 保存時間軸設定
self.use_time_axis = use_time_axis
print(f"[CROSS-EVENT] 🕒 已保存時間軸設定: use_time_axis={use_time_axis}")
```

#### Speed Diff Analysis
```python
self.use_time_axis = use_time_axis  # (在上一步驟中已保存)
```

**差異 #7：保存位置和日誌**
- Speed: 單獨一步，有日誌 ✅
- Speed Diff: 與 sync_driver_lap_enabled 同步，無日誌 ⚠️

**影響**：低（功能一致，日誌缺失）

---

### info_label 更新對比 (Line 1041-1042 vs 1579-1580)

#### Speed Analysis
```python
# 更新資訊標籤（顯示跨賽事比較資訊）
self._update_info_label()
```

#### Speed Diff Analysis
```python
# 更新資訊標籤
self._update_info_label()
```

**差異 #8：註釋詳細度**
- Speed: 註釋說明用途
- Speed Diff: 簡單註釋

**影響**：無（功能一致）

---

### API Worker 創建對比 (Line 1044-1053 vs 1582-1590)

#### Speed Analysis
```python
# 實作跨賽事比較邏輯：調用 API 端點
print(f"[CROSS-EVENT] 開始調用 API 端點: /api/v2/analysis/cross-event-comparison")

# 創建 API Worker
api_worker = CrossEventComparisonWorker(
    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
    force_refresh=False,
    timeout=120
)
```

#### Speed Diff Analysis
```python
# 創建 API Worker
print(f"[SPEEDDIFF-CROSS-EVENT] 🚀 創建跨賽事比較 Worker...")
self.api_worker = CrossEventComparisonWorker(
    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2
)
```

**差異 #9：Worker 參數**
- Speed: 有 `force_refresh=False` 和 `timeout=120` ✅
- Speed Diff: **缺少這兩個參數** ⚠️

**差異 #10：Worker 存儲**
- Speed: 局部變數 `api_worker`
- Speed Diff: 存儲為實例變數 `self.api_worker` ✅

**影響**：中（Speed Diff 缺少超時控制，但存儲為實例變數更好管理）

---

### 信號連接對比 (Line 1055-1058 vs 1592-1595)

#### Speed Analysis
```python
# 連接信號
api_worker.success.connect(self._on_cross_event_data_loaded)
api_worker.failure.connect(self._on_cross_event_load_error)
api_worker.progress.connect(self._on_api_progress)
```

#### Speed Diff Analysis
```python
# 連接信號
self.api_worker.success.connect(self._on_cross_event_data_loaded)
self.api_worker.failure.connect(self._on_cross_event_load_error)
self.api_worker.progress.connect(lambda value: print(f"[SPEEDDIFF-CROSS-EVENT] 進度: {value}%"))
```

**差異 #11：progress 信號處理**
- Speed: 連接到 `self._on_api_progress` 方法 ✅
- Speed Diff: 使用 lambda 直接打印進度 ⚠️

**影響**：低（Speed 有專門的進度處理方法，更結構化）

---

### Worker 啟動對比 (Line 1060-1063 vs 1597-1600)

#### Speed Analysis
```python
# 啟動 Worker
api_worker.start()

print(f"[CROSS-EVENT] API 請求已啟動")
return True
```

#### Speed Diff Analysis
```python
# 啟動 Worker
print(f"[SPEEDDIFF-CROSS-EVENT] 🔄 啟動 API 請求...")
self.api_worker.start()

return True
```

**差異 #12：日誌時機**
- Speed: Worker 啟動後才打印日誌
- Speed Diff: Worker 啟動前先打印日誌

**影響**：無（順序差異，功能一致）

---

### 異常處理對比 (Line 1065-1069 vs 1601-1605)

#### Speed Analysis
```python
except Exception as e:
    print(f"[ERROR] [CROSS-EVENT] 跨賽事比較更新失敗: {e}")
    import traceback
    traceback.print_exc()
    return False
```

#### Speed Diff Analysis
```python
except Exception as e:
    print(f"[ERROR] [SPEEDDIFF-CROSS-EVENT] 更新參數失敗: {e}")
    import traceback
    traceback.print_exc()
    return False
```

**差異 #13：錯誤訊息**
- Speed: `跨賽事比較更新失敗`
- Speed Diff: `更新參數失敗` (更簡潔)

**影響**：無（功能一致）

---

## 📖 方法 2：_on_cross_event_data_loaded()

### 方法簽名對比 (Line 1087 vs 1605)

#### Speed Analysis
```python
def _on_cross_event_data_loaded(self, result: Dict[str, Any]) -> None:
    """處理跨賽事比較數據載入成功"""
```

#### Speed Diff Analysis
```python
def _on_cross_event_data_loaded(self, result: Dict[str, Any]) -> None:
    """處理跨賽事比較數據載入成功"""
```

**差異**：完全一致 ✅

---

### 數據提取對比 (Line 1088-1097 vs 1606-1615)

#### Speed Analysis
```python
try:
    print(f"[CROSS-EVENT] ✅ 數據載入成功")
    
    # 提取數據
    data = result.get("data", {})
    meta = result.get("meta", {})
    
    print(f"[CROSS-EVENT] 數據鍵值: {list(data.keys())}")
    print(f"[CROSS-EVENT] 元數據: {meta}")
    
    # 檢查是否有遙測比較數據
    if "telemetry_comparison" in data:
        telemetry_comp = data["telemetry_comparison"]
        print(f"[CROSS-EVENT] 遙測參數: {list(telemetry_comp.keys())}")
```

#### Speed Diff Analysis
```python
try:
    print(f"[SPEEDDIFF-CROSS-EVENT] ✅ 數據載入成功")
    
    # 提取數據
    data = result.get("data", {})
    meta = result.get("meta", {})
    
    print(f"[SPEEDDIFF-CROSS-EVENT] 數據鍵值: {list(data.keys())}")
    print(f"[SPEEDDIFF-CROSS-EVENT] 元數據: {meta}")
    
    # 檢查是否有遙測比較數據
    if "telemetry_comparison" in data:
        telemetry_comp = data["telemetry_comparison"]
        print(f"[SPEEDDIFF-CROSS-EVENT] 遙測參數: {list(telemetry_comp.keys())}")
```

**差異**：僅日誌前綴不同，邏輯完全一致 ✅

---

### 🚨 關鍵差異：遙測數據提取邏輯

#### Speed Analysis (Line 1098-1106) - **簡單單一檢查**
```python
# 提取速度數據（如果存在）
if "Speed" in telemetry_comp:
    speed_telemetry = telemetry_comp["Speed"]
    
    # 構建符合 _update_chart 期望的數據格式
    chart_data = {
        "speed_data": {
            "distance": speed_telemetry.get("distance", []),
            "driver1_speed": speed_telemetry.get("driver1_data", []),
            "driver2_speed": speed_telemetry.get("driver2_data", []),
```

#### Speed Diff Analysis (Line 1617-1630) - **複雜雙重檢查**
```python
# 提取速度差異數據（優先檢查 "Speeddiff"，其次 "Speed"）
speeddiff_key = None
if "Speeddiff" in telemetry_comp:
    speeddiff_key = "Speeddiff"
    print(f"[SPEEDDIFF-CROSS-EVENT] ✅ 使用 Speeddiff 參數（跨賽事計算的速度差）")
elif "Speed" in telemetry_comp:
    speeddiff_key = "Speed"
    print(f"[SPEEDDIFF-CROSS-EVENT] ⚠️ 使用 Speed 參數（原始速度，非速度差）")

if speeddiff_key:
    speeddiff_telemetry = telemetry_comp[speeddiff_key]
    
    # ✅ 根據參數類型構建不同的數據格式
    if speeddiff_key == "Speeddiff":
        # Speeddiff 參數：已計算的速度差（單曲線模式）
```

**差異 #14：數據來源檢查邏輯** ⚠️ 關鍵差異
- Speed: 直接檢查 `"Speed"` 鍵 ✅
- Speed Diff: 優先檢查 `"Speeddiff"`，再檢查 `"Speed"` ✅✅

**影響**：**高** - Speed Diff 有向後兼容邏輯，更靈活

---

### 🚨 關鍵差異：chart_data 構建邏輯

#### Speed Analysis (Line 1106-1123) - **單一格式**
```python
chart_data = {
    "speed_data": {
        "distance": speed_telemetry.get("distance", []),
        "driver1_speed": speed_telemetry.get("driver1_data", []),
        "driver2_speed": speed_telemetry.get("driver2_data", []),
        # 🆕 新增時間數據
        "driver1_time_seconds": speed_telemetry.get("driver1_time_seconds", []),
        "driver2_time_seconds": speed_telemetry.get("driver2_time_seconds", []),
    },
    "comparison_info": data.get("comparison_info", {}),
    "cross_event_metadata": data.get("cross_event_metadata", {}),
    "use_time_axis": getattr(self, 'use_time_axis', False),  # 傳遞時間軸設定
}
```

#### Speed Diff Analysis (Line 1632-1666) - **雙重格式**

**模式 1：Speeddiff 參數（已計算的速度差）**
```python
if speeddiff_key == "Speeddiff":
    # Speeddiff 參數：已計算的速度差（單曲線模式）
    chart_data = {
        "speeddiff_data": {
            "speed": speeddiff_telemetry.get("distance", []),  # ✅ 修正：Chart Widget 期望 "speed" (實際是距離)
            "cumulative_speed_difference": speeddiff_telemetry.get("speed_difference", []),  # ✅ 修正：期望 "cumulative_speed_difference"
            "driver1_time_seconds": speeddiff_telemetry.get("driver1_time_seconds", []),
            "driver2_time_seconds": speeddiff_telemetry.get("driver2_time_seconds", []),
        },
        "comparison_info": data.get("comparison_info", {}),
        "cross_event_metadata": data.get("cross_event_metadata", {}),
        "use_time_axis": getattr(self, 'use_time_axis', False),
    }
    print(f"[SPEEDDIFF-CROSS-EVENT] 使用 Speeddiff 模式（已計算的速度差）")
    print(f"[SPEEDDIFF-CROSS-EVENT] 🔧 修正字段名稱: distance→speed, speed_difference→cumulative_speed_difference")
```

**模式 2：Speed 參數（原始速度 - 向後兼容）**
```python
else:
    # Speed 參數：原始速度（雙曲線模式 - 向後兼容）
    chart_data = {
        "speeddiff_data": {
            "speed": speeddiff_telemetry.get("distance", []),  # ✅ 修正：Chart Widget 期望 "speed"
            "driver1_speeddiff": speeddiff_telemetry.get("driver1_data", []),  # ⚠️ 原始速度
            "driver2_speeddiff": speeddiff_telemetry.get("driver2_data", []),  # ⚠️ 原始速度
            # 時間數據
            "driver1_time_seconds": speeddiff_telemetry.get("driver1_time_seconds", []),
            "driver2_time_seconds": speeddiff_telemetry.get("driver2_time_seconds", []),
        },
        "comparison_info": data.get("comparison_info", {}),
        "cross_event_metadata": data.get("cross_event_metadata", {}),
        "use_time_axis": getattr(self, 'use_time_axis', False),
    }
    print(f"[SPEEDDIFF-CROSS-EVENT] 使用 Speed 模式（原始速度 - 向後兼容）")
```

**差異 #15：數據格式適配** ⚠️ 最關鍵差異
- Speed: 固定使用 `"speed_data"` 鍵，字段名固定 ✅
- Speed Diff: 使用 `"speeddiff_data"` 鍵，根據來源調整字段名 ✅✅
  - Speeddiff 來源：`distance → speed`, `speed_difference → cumulative_speed_difference`
  - Speed 來源：保持 `driver1_speeddiff`, `driver2_speeddiff`

**影響**：**極高** - Speed Diff 有字段名修正邏輯，確保 Chart Widget 正確接收數據

---

### 日誌輸出對比 (Line 1125-1131 vs 1668-1677)

#### Speed Analysis
```python
print(f"[CROSS-EVENT] 構建圖表數據:")
print(f"[CROSS-EVENT]   距離點數: {len(chart_data['speed_data']['distance'])}")
print(f"[CROSS-EVENT]   車手1速度點數: {len(chart_data['speed_data']['driver1_speed'])}")
print(f"[CROSS-EVENT]   車手2速度點數: {len(chart_data['speed_data']['driver2_speed'])}")
print(f"[CROSS-EVENT]   車手1 時間點數: {len(chart_data['speed_data']['driver1_time_seconds'])}")
print(f"[CROSS-EVENT]   車手2 時間點數: {len(chart_data['speed_data']['driver2_time_seconds'])}")
print(f"[CROSS-EVENT]   🕒 時間軸模式: {chart_data['use_time_axis']}")
```

#### Speed Diff Analysis
```python
print(f"[SPEEDDIFF-CROSS-EVENT] 構建圖表數據:")
print(f"[SPEEDDIFF-CROSS-EVENT]   距離點數 (speed): {len(chart_data['speeddiff_data'].get('speed', []))}")
if speeddiff_key == "Speeddiff":
    print(f"[SPEEDDIFF-CROSS-EVENT]   速度差點數 (cumulative_speed_difference): {len(chart_data['speeddiff_data'].get('cumulative_speed_difference', []))}")
else:
    print(f"[SPEEDDIFF-CROSS-EVENT]   車手1速度差異點數: {len(chart_data['speeddiff_data'].get('driver1_speeddiff', []))}")
    print(f"[SPEEDDIFF-CROSS-EVENT]   車手2速度差異點數: {len(chart_data['speeddiff_data'].get('driver2_speeddiff', []))}")
print(f"[SPEEDDIFF-CROSS-EVENT]   車手1 時間點數: {len(chart_data['speeddiff_data']['driver1_time_seconds'])}")
print(f"[SPEEDDIFF-CROSS-EVENT]   車手2 時間點數: {len(chart_data['speeddiff_data']['driver2_time_seconds'])}")
print(f"[SPEEDDIFF-CROSS-EVENT]   時間軸模式: {chart_data['use_time_axis']}")
```

**差異 #16：日誌適配**
- Speed: 固定格式日誌
- Speed Diff: 根據數據來源動態調整日誌內容 ✅

**影響**：中（Speed Diff 日誌更詳細，有助於調試）

---

### set_time_axis_mode 調用對比 (Line 1133-1136 vs 1679-1682)

#### Speed Analysis
```python
# ⚠️ 關鍵：先設置時間軸模式，再更新圖表
use_time_axis = chart_data.get('use_time_axis', False)
if self.speed_chart_widget and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
    print(f"[CROSS-EVENT] 🕒 設置圖表時間軸模式: {use_time_axis}")
    self.speed_chart_widget.set_time_axis_mode(use_time_axis)
```

#### Speed Diff Analysis
```python
# 關鍵：先設置時間軸模式，再更新圖表
use_time_axis = chart_data.get('use_time_axis', False)
if self.speeddiff_chart_widget and hasattr(self.speeddiff_chart_widget, 'set_time_axis_mode'):
    print(f"[SPEEDDIFF-CROSS-EVENT] 🕒 設置圖表時間軸模式: {use_time_axis}")
    self.speeddiff_chart_widget.set_time_axis_mode(use_time_axis)
```

**差異 #17：widget 名稱**
- Speed: `self.speed_chart_widget`
- Speed Diff: `self.speeddiff_chart_widget`

**影響**：無（正確的 widget 引用）

---

### 圖表更新和完成日誌對比 (Line 1138-1141 vs 1684-1687)

#### Speed Analysis
```python
# 直接調用圖表更新方法
print(f"[CROSS-EVENT] 開始更新圖表...")
self._update_chart(chart_data)
print(f"[CROSS-EVENT] ✅ 跨賽事比較完成")
```

#### Speed Diff Analysis
```python
# 直接調用圖表更新方法
print(f"[SPEEDDIFF-CROSS-EVENT] 開始更新圖表...")
self._update_chart(chart_data)
print(f"[SPEEDDIFF-CROSS-EVENT] ✅ 跨賽事比較完成")
```

**差異**：僅日誌前綴不同，邏輯完全一致 ✅

---

### 錯誤情況處理對比 (Line 1142-1145 vs 1688-1691)

#### Speed Analysis
```python
else:
    print(f"[CROSS-EVENT] ⚠️ 數據中沒有 Speed 遙測")
else:
    print(f"[CROSS-EVENT] ⚠️ 數據中沒有 telemetry_comparison")
```

#### Speed Diff Analysis
```python
else:
    print(f"[SPEEDDIFF-CROSS-EVENT] ⚠️ 數據中沒有 Speeddiff 或 Speed 遙測")
else:
    print(f"[SPEEDDIFF-CROSS-EVENT] ⚠️ 數據中沒有 telemetry_comparison")
```

**差異 #18：錯誤訊息**
- Speed: `沒有 Speed 遙測`
- Speed Diff: `沒有 Speeddiff 或 Speed 遙測` ✅

**影響**：低（Speed Diff 訊息更準確）

---

## 📖 方法 3：update_from_shared_params()

### 方法簽名和 Docstring 對比 (Line 1157-1181 vs 1702-1726)

**差異**：
- Speed: 完整的 Docstring，包含參數說明和來源解釋 ✅✅
- Speed Diff: **完全相同的 Docstring**，只是模組名稱不同 ✅

**影響**：無（文檔質量一致）

---

### 遞迴防護對比 (Line 1182-1184 vs 1727-1729)

#### Speed Analysis
```python
if self._updating_from_shared:
    print(f"[SPEED_MDI] [SHARED_PARAMS] ⚠️  正在更新中，防止遞迴")
    return
```

#### Speed Diff Analysis
```python
if self._updating_from_shared:
    print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS] ⚠️  正在更新中，防止遞迴")
    return
```

**差異**：僅日誌前綴不同，邏輯完全一致 ✅

---

### 參數提取對比 (Line 1186-1203 vs 1731-1748)

**邏輯完全一致**，包括：
- 設置 `_updating_from_shared = True`
- 提取 10 個參數（year1, race1, session1, driver1, lap1, year2, race2, session2, driver2, lap2）
- 提取 `use_time_axis`
- 使用 `params.get(key, default)` 模式

**差異**：僅日誌前綴不同 ✅

---

### 跨賽事檢測和調用對比 (Line 1205-1222 vs 1750-1767)

#### Speed Analysis
```python
# 檢測是否為跨賽事比較
is_cross_event = (year1 != year2 or session1 != session2)

if is_cross_event:
    print(f"[SPEED_MDI] [SHARED_PARAMS] 🌍 檢測到跨賽事比較:")
    print(f"[SPEED_MDI] [SHARED_PARAMS]   車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
    print(f"[SPEED_MDI] [SHARED_PARAMS]   車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
    
    # 調用跨賽事比較方法
    print(f"[SPEED_MDI] [SHARED_PARAMS] 🔄 調用 update_cross_event_comparison")
    success = self.update_cross_event_comparison(
        year1=year1, race1=race1, session1=session1, driver1=driver1, lap1=lap1,
        year2=year2, race2=race2, session2=session2, driver2=driver2, lap2=lap2,
        is_fastest=False,
        use_time_axis=use_time_axis
    )
    
    if success:
        print(f"[SPEED_MDI] [SHARED_PARAMS] ✅ 跨賽事比較更新成功")
        # ⚠️ [參數資訊標籤] 更新資訊標籤顯示
        self._update_info_label()
        print(f"[SPEED_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤")
    else:
        print(f"[SPEED_MDI] [SHARED_PARAMS] ❌ 跨賽事比較更新失敗")
```

#### Speed Diff Analysis
```python
# 檢測是否為跨賽事比較
is_cross_event = (year1 != year2 or session1 != session2)

if is_cross_event:
    print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS] 🌍 檢測到跨賽事比較:")
    print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS]   車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
    print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS]   車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
    
    # 調用跨賽事比較方法
    print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS] 🔄 調用 update_cross_event_comparison")
    success = self.update_cross_event_comparison(
        year1=year1, race1=race1, session1=session1, driver1=driver1, lap1=lap1,
        year2=year2, race2=race2, session2=session2, driver2=driver2, lap2=lap2,
        is_fastest=False,
        use_time_axis=use_time_axis
    )
    
    if success:
        print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS] ✅ 跨賽事比較更新成功")
        # 更新資訊標籤顯示
        self._update_info_label()
        print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤")
    else:
        print(f"[SPEEDDIFF_MDI] [SHARED_PARAMS] ❌ 跨賽事比較更新失敗")
```

**差異 #19：註釋**
- Speed: `# ⚠️ [參數資訊標籤] 更新資訊標籤顯示`
- Speed Diff: `# 更新資訊標籤顯示`

**影響**：無（功能完全一致）

---

## 📊 差異彙總表

| # | 位置 | 類型 | Speed Analysis | Speed Diff Analysis | 優先級 | 評估 |
|---|------|------|----------------|---------------------|--------|------|
| 1 | update_cross_event_comparison 簽名 | 返回類型註解 | 有 `-> bool` | 無 | 🟢 低 | 型別提示缺失 |
| 2 | update_cross_event_comparison docstring | 文檔詳細度 | 簡短 | 詳細 ✅ | 🟢 低 | Speed Diff 更好 |
| 3-4 | 日誌前綴和 emoji | 日誌格式 | `[CROSS-EVENT]` + emoji | `[SPEEDDIFF-CROSS-EVENT]` | 🟢 低 | 格式差異 |
| 5 | 參數保存註釋 | 註釋用詞 | "保存" | "儲存" | 🟢 低 | 無影響 |
| 6-7 | 同步模式停用 | 日誌和位置 | 單獨步驟 + 詳細日誌 | 合併步驟 + 無日誌 | 🟡 中 | Speed 日誌更好 |
| 8 | info_label 更新 | 註釋 | 詳細 | 簡單 | 🟢 低 | 無影響 |
| 9 | API Worker 參數 | force_refresh, timeout | 有 ✅ | 缺少 ⚠️ | 🟡 中 | Speed Diff 缺少超時控制 |
| 10 | Worker 存儲 | 變數作用域 | 局部變數 | 實例變數 ✅ | 🟢 低 | Speed Diff 更好管理 |
| 11 | progress 信號 | 處理方式 | 專門方法 ✅ | lambda 打印 | 🟡 中 | Speed 更結構化 |
| 12 | Worker 啟動日誌 | 日誌時機 | 啟動後 | 啟動前 | 🟢 低 | 無影響 |
| 13 | 異常處理訊息 | 錯誤訊息 | 詳細 | 簡潔 | 🟢 低 | 無影響 |
| **14** | **數據來源檢查** | **邏輯結構** | **單一 Speed 檢查** | **雙重檢查 Speeddiff/Speed** ✅✅ | **🔴 高** | **Speed Diff 有向後兼容** |
| **15** | **chart_data 構建** | **數據格式適配** | **固定格式** | **雙重格式 + 字段名修正** ✅✅ | **🔴 極高** | **Speed Diff 有字段映射邏輯** |
| 16 | 日誌輸出 | 日誌內容 | 固定 | 動態適配 ✅ | 🟡 中 | Speed Diff 更詳細 |
| 17 | set_time_axis_mode | widget 名稱 | speed_chart_widget | speeddiff_chart_widget | 🟢 低 | 正確引用 |
| 18 | 錯誤訊息 | 訊息準確性 | "Speed" | "Speeddiff 或 Speed" ✅ | 🟢 低 | Speed Diff 更準確 |
| 19 | update_from_shared_params 註釋 | 註釋格式 | `⚠️ [參數資訊標籤]` | 簡單 | 🟢 低 | 無影響 |

---

## 🎯 核心差異分析

### 差異 #14 + #15：Speed Diff 的雙重數據源適配邏輯

**這是兩個模組最關鍵的差異！**

#### Speed Analysis 的邏輯（簡單直接）
```
檢查 telemetry_comparison 是否包含 "Speed"
    ↓
如果有 → 構建 speed_data 格式
    ↓
使用固定字段: distance, driver1_speed, driver2_speed
```

**優點**：
- ✅ 簡單清晰
- ✅ 邏輯直觀
- ✅ 維護容易

**缺點**：
- ❌ 無向後兼容
- ❌ 只支持單一數據格式

#### Speed Diff Analysis 的邏輯（複雜靈活）
```
檢查 telemetry_comparison 包含什麼？
    ↓
優先檢查 "Speeddiff" → 如果有:
    ↓
    構建 speeddiff_data 格式（模式 1）
    字段映射: distance → speed
              speed_difference → cumulative_speed_difference
    單曲線模式（已計算的速度差）
    ↓
否則檢查 "Speed" → 如果有:
    ↓
    構建 speeddiff_data 格式（模式 2）
    字段映射: distance → speed
              driver1_data → driver1_speeddiff
              driver2_data → driver2_speeddiff
    雙曲線模式（原始速度 - 向後兼容）
```

**優點**：
- ✅✅ 支持雙重數據源
- ✅✅ 有字段名修正邏輯
- ✅✅ 向後兼容舊 API
- ✅ 適應不同 Chart Widget 期望

**缺點**：
- ⚠️ 邏輯較複雜
- ⚠️ 需要維護兩套格式
- ⚠️ 調試較困難

---

## 🏆 模組優勢對比

### Speed Analysis 的優勢

1. ✅ **更完善的 Worker 參數**：
   - 有 `force_refresh=False`（可控制強制刷新）
   - 有 `timeout=120`（超時保護）

2. ✅ **更結構化的進度處理**：
   - 使用 `_on_api_progress` 專門方法
   - 可擴展為進度條顯示

3. ✅ **更詳細的日誌**：
   - 同步模式停用有專門日誌
   - 時間軸設定保存有專門日誌

### Speed Diff Analysis 的優勢

1. ✅✅ **雙重數據源支持**（最關鍵）：
   - 優先使用 `Speeddiff`（已計算的速度差）
   - 向後兼容 `Speed`（原始速度）

2. ✅✅ **字段名修正邏輯**（最關鍵）：
   - `distance → speed`（符合 Chart Widget 期望）
   - `speed_difference → cumulative_speed_difference`
   - `driver1_data → driver1_speeddiff`

3. ✅ **更詳細的 Docstring**：
   - 參數說明完整
   - 用途解釋清楚

4. ✅ **更好的 Worker 管理**：
   - 存儲為 `self.api_worker`（實例變數）
   - 可後續停止或重新啟動

5. ✅ **更準確的錯誤訊息**：
   - `沒有 Speeddiff 或 Speed 遙測`（涵蓋兩種情況）

---

## 🚀 建議改進方案

### 對 Speed Analysis 的建議

#### 建議 #1：添加雙重數據源支持（優先級：高）
```python
# 修改 _on_cross_event_data_loaded (Line 1098)
# 改為類似 Speed Diff 的雙重檢查邏輯
speed_key = None
if "Speed" in telemetry_comp:
    speed_key = "Speed"
elif "Telemetry" in telemetry_comp:  # 其他可能的鍵
    speed_key = "Telemetry"
```

#### 建議 #2：將 Worker 存儲為實例變數（優先級：中）
```python
# 修改 Line 1050
self.api_worker = CrossEventComparisonWorker(...)
```

### 對 Speed Diff Analysis 的建議

#### 建議 #1：添加 Worker 超時參數（優先級：高）
```python
# 修改 Line 1585
self.api_worker = CrossEventComparisonWorker(
    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
    force_refresh=False,  # 新增
    timeout=120  # 新增
)
```

#### 建議 #2：改進進度處理（優先級：中）
```python
# 添加專門的進度處理方法
def _on_api_progress(self, value: int) -> None:
    """處理 API 請求進度"""
    try:
        if hasattr(self, 'loading_progress'):
            bounded = max(0, min(int(value), 100))
            # self.loading_progress.emit(bounded)  # 可選
            print(f"[SPEEDDIFF-CROSS-EVENT] 進度: {bounded}%")
    except Exception:
        pass

# 修改 Line 1594
self.api_worker.progress.connect(self._on_api_progress)
```

#### 建議 #3：添加同步模式停用日誌（優先級：低）
```python
# 修改 Line 1575-1577
self.sync_driver_lap_enabled = False
print(f"[SPEEDDIFF-CROSS-EVENT] ⚠️ 已停用同步模式 (sync_driver_lap_enabled = False)")
self.use_time_axis = use_time_axis
print(f"[SPEEDDIFF-CROSS-EVENT] 🕒 已保存時間軸設定: use_time_axis={use_time_axis}")
```

---

## ✅ 測試場景建議

### 場景 1：標準跨賽事比較（Speed 數據源）
1. 打開 Speed Diff Analysis
2. 按下 X→D 按鈕
3. 選擇：2024 Japan R NOR vs 2025 Brazil R NOR
4. 預期：使用 "Speed" 數據源（向後兼容模式）

### 場景 2：標準跨賽事比較（Speeddiff 數據源）
1. 打開 Speed Diff Analysis
2. 按下 X→D 按鈕
3. 選擇：2024 Japan R NOR vs 2025 Brazil R NOR
4. 預期：使用 "Speeddiff" 數據源（已計算速度差）

### 場景 3：時間軸模式測試
1. 執行場景 1 或 2
2. 勾選「使用時間軸」
3. 預期：X 軸切換到時間 (s)

### 場景 4：同步模式測試
1. 執行場景 1 或 2
2. 檢查 `sync_driver_lap_enabled` 是否為 False
3. 確認不會被 Update All Analysis 覆蓋

---

## 🎓 經驗總結

### Speed Diff 的設計優勢

1. **字段名修正邏輯**：
   - API 返回 `distance`，Chart Widget 期望 `speed`
   - 有明確的映射和轉換
   - 日誌清楚標註「修正字段名稱」

2. **向後兼容設計**：
   - 支持舊版 API（Speed 格式）
   - 支持新版 API（Speeddiff 格式）
   - 兩種模式都能正常工作

3. **詳細的調試信息**：
   - 日誌清楚標註使用哪種模式
   - 數據點數統計詳細
   - 錯誤訊息準確

### Speed 的設計優勢

1. **更完善的異常處理**：
   - Worker 有超時保護
   - 進度處理有專門方法
   - 可擴展性更好

2. **更簡潔的邏輯**：
   - 單一數據源，易於理解
   - 維護成本低
   - 調試簡單

### 建議的統一方向

**結合兩者優勢**：
1. 採用 Speed Diff 的雙重數據源和字段映射邏輯 ✅
2. 採用 Speed 的 Worker 超時和進度處理 ✅
3. 統一日誌格式和錯誤訊息 ✅

---

## 📋 最終檢查清單

```markdown
### 代碼對比完成度
- [x] update_cross_event_comparison() 完整對比
- [x] _on_cross_event_data_loaded() 完整對比
- [x] update_from_shared_params() 完整對比
- [x] 所有日誌語句已對比
- [x] 所有條件判斷已對比
- [x] 所有異常處理已對比

### 差異記錄完成度
- [x] 19 個差異已記錄
- [x] 每個差異有完整位置
- [x] 每個差異有代碼對比
- [x] 每個差異有影響分析
- [x] 優先級已標註

### 改進建議完成度
- [x] Speed Analysis 改進建議（2 項）
- [x] Speed Diff Analysis 改進建議（3 項）
- [x] 測試場景建議（4 個）
- [x] 統一方向建議

**總體完成度**：100%  
**關鍵發現**：Speed Diff 有更強的向後兼容和字段映射邏輯  
**建議**：兩個模組都很優秀，建議結合各自優勢進行統一改進
```

---

**報告完成時間**：2025-11-14 13:45  
**對比方法**：完全遵循標準化對比流程  
**對比行數**：Speed (215 行) vs Speed Diff (271 行)  
**關鍵結論**：Speed Diff 的字段映射和雙重數據源邏輯是核心優勢！✅
