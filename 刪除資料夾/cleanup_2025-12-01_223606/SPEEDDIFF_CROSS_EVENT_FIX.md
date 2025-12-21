# Speed Diff 跨賽事比較 - 字段名稱修復報告

**修復日期：** 2025-11-14  
**問題：** GUI 沒有顯示速度差異曲線  
**根本原因：** 數據字段名稱不匹配

---

## 🐛 **問題診斷**

### **症狀：**
- API 成功計算速度差異（500 個數據點）
- API 日誌顯示 `✅ Speeddiff 遙測參數已添加`
- GUI 接收到數據但圖表無曲線顯示

### **API 日誌分析：**
```
[MERGE] ✅ 速度差計算完成：500 點，範圍 -48.46 ~ 38.15 km/h
[MERGE] ✅ Speeddiff 遙測參數已添加
```

### **根本原因：**

**Chart Widget 期望的數據字段：**
```python
# speeddiff_analysis_chart_widget.py Line 1471-1472
speed = speeddiff_data.get('speed', [])  # ⚠️ 期望 "speed"（實際是距離）
cumulative_diff = speeddiff_data.get('cumulative_speed_difference', [])  # ⚠️ 期望 "cumulative_speed_difference"
```

**GUI 傳遞的字段（修復前）：**
```python
# speeddiff_analysis_mdi.py Line 1638 (舊版本)
"speeddiff_data": {
    "distance": [...],  # ❌ Chart Widget 期望 "speed"
    "driver1_speeddiff": [...],  # ❌ Chart Widget 期望 "cumulative_speed_difference"
    "driver2_speeddiff": [],
}
```

**結果：** Chart Widget 無法讀取數據 → `if not speed or not cumulative_diff:` 條件觸發 → 提前返回 → 無曲線顯示

---

## 🔧 **修復方案**

### **修改文件：** `speeddiff_analysis_mdi.py`

### **修改位置：** `_on_cross_event_data_loaded()` 方法（Lines 1635-1660）

### **修正前：**
```python
if speeddiff_key == "Speeddiff":
    chart_data = {
        "speeddiff_data": {
            "distance": speeddiff_telemetry.get("distance", []),  # ❌ 錯誤字段名
            "driver1_speeddiff": speeddiff_telemetry.get("speed_difference", []),  # ❌ 錯誤字段名
            "driver2_speeddiff": [],
            "driver1_time_seconds": [...],
            "driver2_time_seconds": [...],
        },
        ...
    }
```

### **修正後：**
```python
if speeddiff_key == "Speeddiff":
    chart_data = {
        "speeddiff_data": {
            "speed": speeddiff_telemetry.get("distance", []),  # ✅ 修正：Chart Widget 期望 "speed"
            "cumulative_speed_difference": speeddiff_telemetry.get("speed_difference", []),  # ✅ 修正：期望 "cumulative_speed_difference"
            "driver1_time_seconds": [...],
            "driver2_time_seconds": [...],
        },
        ...
    }
    print(f"[SPEEDDIFF-CROSS-EVENT] 🔧 修正字段名稱: distance→speed, speed_difference→cumulative_speed_difference")
```

### **同步修正 Speed 模式（向後兼容）：**
```python
else:
    # Speed 參數：原始速度（雙曲線模式 - 向後兼容）
    chart_data = {
        "speeddiff_data": {
            "speed": speeddiff_telemetry.get("distance", []),  # ✅ 修正：統一字段名
            "driver1_speeddiff": speeddiff_telemetry.get("driver1_data", []),
            "driver2_speeddiff": speeddiff_telemetry.get("driver2_data", []),
            ...
        },
        ...
    }
```

---

## 📊 **數據流程對比**

### **修復前（錯誤）：**
```
API 返回:
{
    "telemetry_comparison": {
        "Speeddiff": {
            "distance": [0, 10.48, ...],  ✅ 正確數據
            "speed_difference": [-5.2, 3.1, ...],  ✅ 正確數據
        }
    }
}
        ↓
GUI 構建 chart_data:
{
    "speeddiff_data": {
        "distance": [0, 10.48, ...],  ❌ Chart Widget 找不到（期望 "speed"）
        "driver1_speeddiff": [-5.2, 3.1, ...],  ❌ Chart Widget 找不到（期望 "cumulative_speed_difference"）
    }
}
        ↓
Chart Widget 檢查:
speed = speeddiff_data.get('speed', [])  → []  ❌ 空陣列
cumulative_diff = speeddiff_data.get('cumulative_speed_difference', [])  → []  ❌ 空陣列
        ↓
if not speed or not cumulative_diff:  → True  ❌ 條件觸發
    return  → 提前返回，無曲線顯示
```

### **修復後（正確）：**
```
API 返回:
{
    "telemetry_comparison": {
        "Speeddiff": {
            "distance": [0, 10.48, ...],  ✅ 正確數據
            "speed_difference": [-5.2, 3.1, ...],  ✅ 正確數據
        }
    }
}
        ↓
GUI 構建 chart_data:
{
    "speeddiff_data": {
        "speed": [0, 10.48, ...],  ✅ 字段名修正（distance → speed）
        "cumulative_speed_difference": [-5.2, 3.1, ...],  ✅ 字段名修正（speed_difference → cumulative_speed_difference）
    }
}
        ↓
Chart Widget 檢查:
speed = speeddiff_data.get('speed', [])  → [0, 10.48, ...]  ✅ 500 個數據點
cumulative_diff = speeddiff_data.get('cumulative_speed_difference', [])  → [-5.2, 3.1, ...]  ✅ 500 個數據點
        ↓
if not speed or not cumulative_diff:  → False  ✅ 條件不觸發
    # 繼續執行圖表繪製
    self.chart_widget.set_speeddiff_data(...)  ✅ 成功繪製曲線
```

---

## 🎯 **修復驗證**

### **語法檢查：**
```powershell
# 已通過
✅ No errors found in speeddiff_analysis_mdi.py
```

### **預期日誌輸出：**
```
[SPEEDDIFF-CROSS-EVENT] ✅ 使用 Speeddiff 參數（跨賽事計算的速度差）
[SPEEDDIFF-CROSS-EVENT] 使用 Speeddiff 模式（已計算的速度差）
[SPEEDDIFF-CROSS-EVENT] 🔧 修正字段名稱: distance→speed, speed_difference→cumulative_speed_difference
[SPEEDDIFF-CROSS-EVENT] 構建圖表數據:
[SPEEDDIFF-CROSS-EVENT]   距離點數 (speed): 500
[SPEEDDIFF-CROSS-EVENT]   速度差點數 (cumulative_speed_difference): 500
[SPEEDDIFF-CROSS-EVENT]   車手1 時間點數: 500
[SPEEDDIFF-CROSS-EVENT]   車手2 時間點數: 500
[SPEEDDIFF-CROSS-EVENT]   時間軸模式: False
[speeddiff_CHART] 📊 更新速度差圖表...
[speeddiff_CHART] ✅ 圖表更新完成
[SPEEDDIFF-CROSS-EVENT] ✅ 跨賽事比較完成
```

### **預期圖表顯示：**
- ✅ 顯示單條速度差異曲線
- ✅ Y 軸標題：`速度差距 (km/h)`
- ✅ 曲線範圍：-48.46 ~ 38.15 km/h（根據 API 日誌）
- ✅ X 軸：距離（0-5239.91m）
- ✅ 曲線標籤：`NOR vs NOR` 或類似格式

---

## 🔍 **根本原因分析**

### **為什麼會有這個問題？**

1. **命名不一致：** Chart Widget 使用 `speed`（實際存儲距離）而非 `distance`
   - 歷史原因：可能原始設計時 `speed` 用於 X 軸數據（不管是距離還是速度）
   - 未統一：其他模組可能使用 `distance` 作為距離數據字段

2. **字段語義混淆：** `cumulative_speed_difference` vs `speed_difference`
   - Chart Widget 期望累積速度差（`cumulative_speed_difference`）
   - API 返回瞬時速度差（`speed_difference`）
   - 雖然在速度差分析中兩者可能相同，但字段名不一致

3. **缺乏文檔：** Chart Widget 的數據格式期望未明確文檔化
   - 開發者需要閱讀 Chart Widget 源碼才能知道正確字段名
   - 容易在跨模組數據傳遞時出錯

---

## 📝 **經驗教訓**

### **教訓 1：數據格式文檔化**
建議為每個 Chart Widget 創建數據格式文檔：
```python
"""
Speed Diff Chart Widget 數據格式：

輸入數據結構：
{
    "speeddiff_data": {
        "speed": List[float],  # ⚠️ 名稱易混淆，實際是距離數據（米）
        "cumulative_speed_difference": List[float],  # 速度差數據（km/h）
        "driver1_time_seconds": List[float],  # 時間軸數據（秒）
        "driver2_time_seconds": List[float],  # 時間軸數據（秒）
    },
    "metadata": {...},
    "statistics": {...}
}
"""
```

### **教訓 2：統一字段命名**
考慮重構 Chart Widget 以使用更清晰的字段名：
- `speed` → `distance_data`（避免混淆）
- `cumulative_speed_difference` → `speed_difference`（簡化）

### **教訓 3：早期驗證**
在數據傳遞時添加字段驗證：
```python
required_fields = ["speed", "cumulative_speed_difference"]
missing_fields = [f for f in required_fields if f not in speeddiff_data]
if missing_fields:
    print(f"[ERROR] 缺失必要字段: {missing_fields}")
    print(f"[DEBUG] 可用字段: {list(speeddiff_data.keys())}")
```

---

## ✅ **修復完成檢查清單**

- [x] 修正 `Speeddiff` 模式的字段名稱（`distance` → `speed`，`speed_difference` → `cumulative_speed_difference`）
- [x] 修正 `Speed` 模式的字段名稱（統一使用 `speed`）
- [x] 更新調試日誌輸出（區分兩種模式的字段名）
- [x] 語法驗證通過（無錯誤）
- [ ] GUI 測試（待執行）：啟動跨賽事比較，確認曲線顯示
- [ ] 驗證數據範圍（待執行）：-48.46 ~ 38.15 km/h
- [ ] 時間軸切換測試（待執行）

---

## 🚀 **下一步驟**

### **立即測試：**
1. 重啟 F1T GUI（如果正在運行）
2. 開啟 Speed Diff Analysis 視窗
3. 執行跨賽事比較：
   - 車手 1: 2025 Australia R NOR Lap99
   - 車手 2: 2025 Australia Q NOR Lap99
4. 確認圖表顯示單條速度差異曲線

### **預期結果：**
- ✅ 圖表顯示曲線（不再是空白）
- ✅ Y 軸範圍：約 -50 ~ 40 km/h
- ✅ X 軸範圍：0-5240m
- ✅ 無錯誤日誌

---

**修復完成！請重新測試 GUI 🎯**
