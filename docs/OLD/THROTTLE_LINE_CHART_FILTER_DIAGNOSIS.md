# Throttle Line Chart 過濾問題診斷報告

## 🔍 問題發現（2025-10-21）

### 用戶回報
> "使用者已經filter但顯示的曲線卻是含有filter資訊的"

### 日誌分析

從 `f1_gui_2025-10-21.log` 中發現關鍵問題：

```log
[THROTTLE-LINE DEBUG] ?? [Flag Markers] pit_laps=[30, 33], flag_labels={1: 'Y', 2: 'R', 3: 'R', 29: 'R', 30: 'R', 33: 'R', 34: 'R'}
[THROTTLE-LINE DEBUG] ? [Filter Status] filter_pit_laps=True, filter_yellow_flags=True, filter_red_flags=True
? [_apply_filters] Removed Pit Stop lap: 29
? [_apply_filters] Removed Pit Stop lap: 30
????[_apply_filters] Filtering completed:
  - Original laps: 57
  - Removed Pit: 2, Yellow: 0, Red: 0    ← ❌ 問題在這裡！
  - Remaining laps: 55
```

### 關鍵發現

1. ✅ **Flag Markers 正確識別了標記**：
   - Yellow Flag: lap 1
   - Red Flag: laps 2, 3, 29, 30, 33, 34
   - Pit Stop: laps 30, 33

2. ✅ **過濾設定都啟用了**：
   - `filter_pit_laps=True`
   - `filter_yellow_flags=True`
   - `filter_red_flags=True`

3. ❌ **但是只移除了 Pit Stop，沒有移除 Yellow/Red Flag**：
   - Removed Pit: 2 ✅
   - Removed Yellow: 0 ❌ (應該移除 lap 1)
   - Removed Red: 0 ❌ (應該移除 laps 2, 3, 29, 30, 33, 34)

---

## 🎯 根本原因分析

### 問題定位

`_apply_filters()` 方法調用了以下函數來提取需要過濾的圈數：

```python
caution_laps = extract_caution_laps(driver_payload) if self._filter_yellow_flags else set()
red_flag_laps = extract_red_flag_laps(driver_payload) if self._filter_red_flags else set()
```

**這兩個函數返回了空集合！**

### 函數實現分析

**檔案**: `modules/gui/driver_race/detailed_lap_analysis/lap_filter_utils.py`

```python
def extract_caution_laps(driver_data: Dict[str, Any]) -> Set[int]:
    """Gather lap numbers flagged as caution from summary data."""
    caution_laps: Set[int] = set()

    summary = driver_data.get("smart_markers_summary", {})
    safety_summary = summary.get("accident_safety_detection", {})
    if not isinstance(safety_summary, dict):
        return caution_laps

    for key in CAUTION_SUMMARY_KEYS:
        laps = safety_summary.get(key)
        if isinstance(laps, (list, tuple, set)):
            for lap in laps:
                lap_int = normalize_lap_number(lap)
                if lap_int is not None:
                    caution_laps.add(lap_int)
    return caution_laps
```

**問題**：
- 函數從 `driver_data["smart_markers_summary"]["accident_safety_detection"]` 提取數據
- 但是傳入的 `driver_payload` 可能沒有這個結構！

### 數據結構分析

在 `_process_data()` 中：

```python
# L432: 調用 _apply_filters
lap_records, filter_stats = self._apply_filters(lap_records, target)
```

**`target` 的結構**（來自 API）：
```python
target = {
    "driver_code": "NOR",
    "team": "McLaren",
    "laps": [...],
    "summary": {...},
    # ❓ 可能沒有 "smart_markers_summary"
}
```

**但是 `extract_caution_laps()` 期望的結構**：
```python
driver_data = {
    "smart_markers_summary": {
        "accident_safety_detection": {
            "safety_car_laps": [1],
            "red_flag_laps": [2, 3, 29, 30, 33, 34],
            ...
        }
    }
}
```

---

## 💡 可能的原因

### 假設 1: `target` 沒有 `smart_markers_summary`

API 返回的 `target` 數據結構中，可能沒有 `smart_markers_summary` 鍵，或者這個鍵的結構與 `extract_caution_laps()` 期望的不同。

### 假設 2: 數據存在但鍵名不同

Flag 標記的數據可能存在於其他地方，例如：
- `target["summary"]`
- `target["annotations"]`
- `target["smart_markers"]`（而不是 `smart_markers_summary`）

### 假設 3: 數據結構層級不同

`extract_caution_laps()` 期望的路徑是：
```
driver_data["smart_markers_summary"]["accident_safety_detection"][key]
```

但實際的路徑可能是：
```
driver_data["summary"]["smart_markers"]["accident_safety_detection"][key]
```
或其他變體。

---

## 🔧 調試增強

已增加以下調試輸出來驗證假設：

```python
# 檢查 driver_payload 的結構
print(f"🔍🔍🔍 [_apply_filters] driver_payload keys: {list(driver_payload.keys())}")
print(f"🔍🔍🔍 [_apply_filters] 'smart_markers_summary' in driver_payload: {'smart_markers_summary' in driver_payload}")

# 如果有 smart_markers_summary，顯示其內容
if 'smart_markers_summary' in driver_payload:
    smart_markers = driver_payload.get('smart_markers_summary', {})
    print(f"🔍🔍🔍 [_apply_filters] smart_markers_summary keys: {list(smart_markers.keys())}")
    if 'accident_safety_detection' in smart_markers:
        safety = smart_markers['accident_safety_detection']
        print(f"🔍🔍🔍 [_apply_filters] accident_safety_detection keys: {list(safety.keys())}")

# 檢查 extract 函數的返回值
caution_laps = extract_caution_laps(driver_payload) if self._filter_yellow_flags else set()
print(f"🔍🔍🔍 [_apply_filters] Caution laps (Yellow Flag): {caution_laps if caution_laps else 'EMPTY SET (extracted nothing!)'}")

red_flag_laps = extract_red_flag_laps(driver_payload) if self._filter_red_flags else set()
print(f"🔍🔍🔍 [_apply_filters] Red flag laps: {red_flag_laps if red_flag_laps else 'EMPTY SET (extracted nothing!)'}")
```

---

## 📋 下一步行動

### 1. 重新測試並收集日誌

執行以下操作：
1. 啟動 GUI
2. 開啟 Throttle Line Chart
3. 選擇 Driver 1 (VER)
4. 選擇 Driver 2 (NOR)
5. 檢查終端/日誌輸出

### 2. 關鍵檢查點

從新的調試輸出中確認：

**✅ 如果看到**：
```
🔍🔍🔍 [_apply_filters] driver_payload keys: ['driver_code', 'team', 'laps', 'summary', 'smart_markers_summary']
🔍🔍🔍 [_apply_filters] 'smart_markers_summary' in driver_payload: True
🔍🔍🔍 [_apply_filters] smart_markers_summary keys: ['accident_safety_detection', ...]
🔍🔍🔍 [_apply_filters] Caution laps (Yellow Flag): {1}
🔍🔍🔍 [_apply_filters] Red flag laps: {2, 3, 29, 30, 33, 34}
```
→ **結論**: 數據結構正確，但 `lap_is_under_caution()` 或 `lap_is_under_red_flag()` 的邏輯有問題

**❌ 如果看到**：
```
🔍🔍🔍 [_apply_filters] driver_payload keys: ['driver_code', 'team', 'laps', 'summary']
🔍🔍🔍 [_apply_filters] 'smart_markers_summary' in driver_payload: False
🔍🔍🔍 [_apply_filters] Caution laps (Yellow Flag): EMPTY SET (extracted nothing!)
🔍🔍🔍 [_apply_filters] Red flag laps: EMPTY SET (extracted nothing!)
```
→ **結論**: `target` 數據結構中沒有 `smart_markers_summary`，需要從其他地方提取

### 3. 可能的修復方案

#### 方案 A: 修復數據結構（如果是 API 問題）

如果 API 返回的 `target` 沒有 `smart_markers_summary`，需要：
1. 從 API 的其他字段提取 flag 信息
2. 構建正確的 `smart_markers_summary` 結構
3. 傳遞給 `_apply_filters()`

#### 方案 B: 使用已提取的 flag 信息（推薦）

在 `_process_data()` 中，`helper_sets = self._extract_flag_sets(lap_records)` 已經提取了所有 flag 信息：

```python
helper_sets = {
    "pit_laps": set([30, 33]),
    "caution_laps": set([1]),
    "invalid_laps": set([...]),
    "flag_labels": {1: 'Y', 2: 'R', 3: 'R', ...}
}
```

**修復思路**：
1. 將 `helper_sets` 傳遞給 `_apply_filters()`
2. 直接使用 `helper_sets["caution_laps"]` 和從 `flag_labels` 提取的 Red Flag 圈數
3. 不再依賴 `extract_caution_laps()` 和 `extract_red_flag_laps()`

**優勢**：
- 不依賴 `smart_markers_summary` 的結構
- 直接使用已經正確提取的數據
- 避免數據結構不一致的問題

#### 方案 C: 修復 extract 函數以支援多種數據結構

修改 `extract_caution_laps()` 和 `extract_red_flag_laps()` 以支援多種可能的數據結構：

```python
def extract_caution_laps(driver_data: Dict[str, Any]) -> Set[int]:
    caution_laps: Set[int] = set()

    # 嘗試路徑 1: smart_markers_summary.accident_safety_detection
    summary = driver_data.get("smart_markers_summary", {})
    safety_summary = summary.get("accident_safety_detection", {})
    
    # 嘗試路徑 2: summary.smart_markers.accident_safety_detection
    if not safety_summary:
        summary = driver_data.get("summary", {})
        smart_markers = summary.get("smart_markers", {})
        safety_summary = smart_markers.get("accident_safety_detection", {})
    
    # 嘗試路徑 3: 直接在 driver_data 中
    if not safety_summary:
        safety_summary = driver_data.get("accident_safety_detection", {})
    
    if isinstance(safety_summary, dict):
        for key in CAUTION_SUMMARY_KEYS:
            laps = safety_summary.get(key)
            if isinstance(laps, (list, tuple, set)):
                for lap in laps:
                    lap_int = normalize_lap_number(lap)
                    if lap_int is not None:
                        caution_laps.add(lap_int)
    
    return caution_laps
```

---

## 🎯 推薦方案

**推薦使用方案 B**：使用已提取的 `helper_sets` 數據

**理由**：
1. ✅ **數據已經正確提取**：`_extract_flag_sets()` 已經正確識別了所有 flag
2. ✅ **避免重複工作**：不需要再次解析相同的數據
3. ✅ **結構簡單**：不依賴複雜的數據路徑
4. ✅ **維護性高**：只需要修改一個地方（`_apply_filters()`）

**實現步驟**：
1. 修改 `_apply_filters()` 的簽名，接受 `helper_sets` 參數
2. 直接使用 `helper_sets["caution_laps"]`
3. 從 `helper_sets["flag_labels"]` 提取 Red Flag 圈數

---

## 📝 待驗證

執行測試後需要確認：
1. [ ] `driver_payload` 的完整結構（所有 keys）
2. [ ] 是否有 `smart_markers_summary` 鍵
3. [ ] 如果有，其內部結構是什麼
4. [ ] `extract_caution_laps()` 和 `extract_red_flag_laps()` 的返回值
5. [ ] `helper_sets` 中的數據是否正確

---

**報告時間**: 2025-10-21  
**狀態**: 待測試驗證  
**下一步**: 重新啟動 GUI 並收集新的調試日誌
