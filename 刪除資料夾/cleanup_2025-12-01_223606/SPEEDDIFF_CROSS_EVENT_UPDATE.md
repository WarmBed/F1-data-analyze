# Speed Diff 跨賽事比較功能更新報告

**更新日期：** 2025-11-14  
**功能：** Speed Diff Analysis 跨賽事比較（計算速度差異）  
**參考來源：** CLI Function 13 (`two_driver_telemetry_comparison_fixed.py`)

---

## 📋 **更新摘要**

### **問題背景**

原始實現中，跨賽事比較只是簡單合併兩個 JSON 的原始速度數據，未計算速度差異：

```json
{
    "telemetry_comparison": {
        "Speed": {
            "driver1_data": [japan_speed],  // ❌ 原始速度
            "driver2_data": [monaco_speed]  // ❌ 原始速度
        }
    }
}
```

這導致 Speed Diff Chart Widget 顯示的是兩條原始速度曲線，而非速度差異曲線。

### **修復方案**

在 API 端（`api/routers/analysis.py`）添加速度差異計算邏輯，參考 CLI Function 13 的 `_calculate_speed_difference()` 方法：

1. ✅ 提取兩個車手的原始速度數據
2. ✅ 找出共同的距離範圍
3. ✅ 插值到共同的距離數組（500個採樣點）
4. ✅ 計算速度差異：`speed_diff = speed1 - speed2`
5. ✅ 插值時間數據（用於時間軸模式）
6. ✅ 構建 `Speeddiff` 遙測參數

---

## 🔧 **API 端修改（`api/routers/analysis.py`）**

### **修改位置：** `_merge_cross_event_telemetry()` 函數

### **新增功能：**

1. **速度差異計算邏輯**（參考 CLI Function 13）：
   ```python
   # 提取速度數據
   driver1_speed = np.array(telemetry_comp1["Speed"].get("driver1_data", []))
   driver2_speed = np.array(telemetry_comp2["Speed"].get("driver1_data", []))
   distance1 = np.array(telemetry_comp1["Speed"].get("distance", []))
   distance2 = np.array(telemetry_comp2["Speed"].get("distance", []))
   
   # 找出共同的距離範圍
   common_min = max(distance1.min(), distance2.min())
   common_max = min(distance1.max(), distance2.max())
   
   # 創建共同的距離數組（500個採樣點）
   common_distance = np.linspace(common_min, common_max, 500)
   
   # 插值速度數據到共同距離
   speed1_interp = np.interp(common_distance, distance1, driver1_speed)
   speed2_interp = np.interp(common_distance, distance2, driver2_speed)
   
   # 計算速度差（driver1 - driver2）
   speed_diff = speed1_interp - speed2_interp
   ```

2. **構建 Speed Difference 結果**：
   ```python
   merged_speed_difference = {
       'distance': common_distance.tolist(),
       'speed_difference': speed_diff.tolist(),
       'max_diff': float(np.max(speed_diff)),
       'min_diff': float(np.min(speed_diff)),
       'mean_diff': float(np.mean(speed_diff)),
       'reference': f"{driver1} - {driver2}",
       'driver1_time_seconds': time1_interp.tolist(),
       'driver2_time_seconds': time2_interp.tolist(),
       'time_reference': 'seconds_from_lap_start'
   }
   ```

3. **構建 Speeddiff 遙測參數**（用於 GUI）：
   ```python
   merged_telemetry["Speeddiff"] = {
       "name": "Speed Difference",
       "distance": merged_speed_difference["distance"],
       "speed_difference": merged_speed_difference["speed_difference"],
       "driver1_time_seconds": merged_speed_difference.get("driver1_time_seconds", []),
       "driver2_time_seconds": merged_speed_difference.get("driver2_time_seconds", []),
       "time_reference": merged_speed_difference.get("time_reference", "")
   }
   ```

---

## 🎨 **GUI 端修改（`speeddiff_analysis_mdi.py`）**

### **修改位置：** `_on_cross_event_data_loaded()` 方法

### **更新邏輯：**

優先檢查 `Speeddiff` 參數（已計算的速度差），其次回退到 `Speed` 參數（原始速度，向後兼容）：

```python
# 提取速度差異數據（優先檢查 "Speeddiff"，其次 "Speed"）
speeddiff_key = None
if "Speeddiff" in telemetry_comp:
    speeddiff_key = "Speeddiff"
    print(f"[SPEEDDIFF-CROSS-EVENT] ✅ 使用 Speeddiff 參數（跨賽事計算的速度差）")
elif "Speed" in telemetry_comp:
    speeddiff_key = "Speed"
    print(f"[SPEEDDIFF-CROSS-EVENT] ⚠️ 使用 Speed 參數（原始速度，非速度差）")

if speeddiff_key == "Speeddiff":
    # Speeddiff 參數：已計算的速度差（單曲線模式）
    chart_data = {
        "speeddiff_data": {
            "distance": speeddiff_telemetry.get("distance", []),
            "driver1_speeddiff": speeddiff_telemetry.get("speed_difference", []),  # ✅ 速度差數據
            "driver2_speeddiff": [],  # 空陣列（單曲線模式）
            "driver1_time_seconds": speeddiff_telemetry.get("driver1_time_seconds", []),
            "driver2_time_seconds": speeddiff_telemetry.get("driver2_time_seconds", []),
        },
        ...
    }
else:
    # Speed 參數：原始速度（雙曲線模式 - 向後兼容）
    chart_data = {
        "speeddiff_data": {
            "distance": speeddiff_telemetry.get("distance", []),
            "driver1_speeddiff": speeddiff_telemetry.get("driver1_data", []),  # ⚠️ 原始速度
            "driver2_speeddiff": speeddiff_telemetry.get("driver2_data", []),  # ⚠️ 原始速度
            ...
        },
        ...
    }
```

---

## 📊 **數據流對比**

### **修改前（錯誤）：**

```
API 返回:
{
    "telemetry_comparison": {
        "Speed": {
            "driver1_data": [japan_speed_raw],  // ❌ 原始速度
            "driver2_data": [monaco_speed_raw]  // ❌ 原始速度
        }
    }
}
        ↓
GUI 提取:
driver1_speeddiff = Speed["driver1_data"]  // ❌ 誤把原始速度當速度差
driver2_speeddiff = Speed["driver2_data"]  // ❌ 誤把原始速度當速度差
        ↓
Chart Widget:
顯示兩條原始速度曲線  // ❌ 錯誤！
```

### **修改後（正確）：**

```
API 計算:
speed_diff = speed1_interp - speed2_interp  // ✅ 計算速度差
        ↓
API 返回:
{
    "telemetry_comparison": {
        "Speeddiff": {
            "speed_difference": [calculated_diff],  // ✅ 已計算的速度差
            "distance": [common_distance],
            "driver1_time_seconds": [...],
            "driver2_time_seconds": [...]
        },
        "Speed": {  // ✅ 保留原始速度（給 Speed Analysis 用）
            "driver1_data": [...],
            "driver2_data": [...]
        }
    }
}
        ↓
GUI 提取:
driver1_speeddiff = Speeddiff["speed_difference"]  // ✅ 正確的速度差
driver2_speeddiff = []  // ✅ 空陣列（單曲線模式）
        ↓
Chart Widget:
顯示單條速度差異曲線  // ✅ 正確！
```

---

## 🧪 **測試計畫**

### **階段 1：API 測試**

```powershell
# 啟動 API 服務器
python refactored_api.py

# 測試跨賽事比較端點
curl -X POST "http://localhost:8000/api/v2/analysis/cross-event-comparison?driver1=VER&year1=2025&race1=Japan&session1=R&lap1=1&driver2=LEC&year2=2024&race2=Monaco&session2=Q&lap2=1"
```

**預期結果：**
- ✅ 返回包含 `Speeddiff` 參數的 JSON
- ✅ `speed_difference` 陣列包含計算好的速度差
- ✅ 包含時間數據（`driver1_time_seconds`, `driver2_time_seconds`）

### **階段 2：GUI 測試**

1. 啟動 F1T GUI：`python f1t_gui_main.py`
2. 開啟 Speed Diff Analysis 視窗
3. 設定跨賽事比較：
   - 車手 1: 2025 Japan R VER Lap1
   - 車手 2: 2024 Monaco Q LEC Lap1
4. 點擊「載入數據」

**預期結果：**
- ✅ 控制台輸出：`使用 Speeddiff 參數（跨賽事計算的速度差）`
- ✅ 圖表顯示單條速度差異曲線
- ✅ Y 軸標題：`速度差距 (km/h)`
- ✅ 曲線標籤：`VER - LEC` 或類似格式

### **階段 3：時間軸切換測試**

1. 在 Speed Diff 視窗中，勾選「使用時間軸」
2. 驗證 X 軸切換為時間軸（秒）

**預期結果：**
- ✅ X 軸範圍從距離（米）切換為時間（秒）
- ✅ 曲線正確更新
- ✅ 無 AttributeError 錯誤

---

## 📝 **API 返回格式範例**

### **跨賽事 Speed Diff 完整 JSON 結構：**

```json
{
    "success": true,
    "message": "跨賽事遙測比較完成 (2025 Japan R vs 2024 Monaco Q)",
    "data": {
        "comparison_info": {
            "driver1": "VER",
            "driver2": "LEC",
            "act_lap1_number": 1,
            "act_lap2_number": 1,
            "lap_time1": "1:30.123",
            "lap_time2": "1:12.456",
            "compound1": "SOFT",
            "compound2": "MEDIUM",
            "tyre_life1": 5,
            "tyre_life2": 10
        },
        "telemetry_comparison": {
            "Speeddiff": {
                "name": "Speed Difference",
                "distance": [0, 11.61, 23.23, ..., 3337],
                "speed_difference": [-5.2, 3.1, 7.8, ..., -2.4],
                "driver1_time_seconds": [0, 0.1, 0.2, ..., 85.3],
                "driver2_time_seconds": [0, 0.12, 0.24, ..., 72.1],
                "time_reference": "seconds_from_lap_start"
            },
            "Speed": {
                "name": "速度 (km/h)",
                "driver1_data": [280, 285, 290, ...],
                "driver2_data": [275, 282, 288, ...],
                "distance": [0, 11.61, 23.23, ...],
                "driver1_time_seconds": [...],
                "driver2_time_seconds": [...]
            },
            "RPM": {...},
            "Brake": {...},
            ...
        },
        "speed_difference": {
            "distance": [0, 11.61, 23.23, ..., 3337],
            "speed_difference": [-5.2, 3.1, 7.8, ..., -2.4],
            "max_diff": 15.6,
            "min_diff": -12.3,
            "mean_diff": 2.1,
            "reference": "VER - LEC",
            "driver1_time_seconds": [...],
            "driver2_time_seconds": [...],
            "time_reference": "seconds_from_lap_start"
        },
        "cross_event_metadata": {
            "driver1_event": {
                "year": 2025,
                "race": "Japan",
                "session": "R",
                "lap": 1
            },
            "driver2_event": {
                "year": 2024,
                "race": "Monaco",
                "session": "Q",
                "lap": 1
            },
            "comparison_mode": "cross_event"
        }
    },
    "cross_event": true,
    "function_id": "13",
    "timestamp": 1700000000.0
}
```

---

## ✅ **完成檢查清單**

- [x] API 端添加速度差異計算邏輯
- [x] 參考 CLI Function 13 的 `_calculate_speed_difference()` 方法
- [x] 構建 `Speeddiff` 遙測參數
- [x] 插值時間數據（支援時間軸模式）
- [x] GUI 優先檢查 `Speeddiff` 參數
- [x] 向後兼容 `Speed` 參數（原始速度）
- [x] 語法驗證通過（無錯誤）
- [ ] API 端測試（待執行）
- [ ] GUI 端測試（待執行）
- [ ] 時間軸切換測試（待執行）

---

## 🚀 **下一步驟**

### **立即執行：**
1. 啟動 API 服務器測試計算邏輯
2. 啟動 GUI 測試跨賽事比較
3. 驗證速度差異曲線正確顯示

### **未來擴展：**
1. **Distance Diff**：添加距離差異計算（參考 `_calculate_distance_difference()`）
2. **Time Diff**：添加時間差異計算（參考 `_calculate_time_difference()`）
3. **統一處理**：抽取共同邏輯為獨立函數

---

## 📚 **參考文件**

- **CLI 實現**：`CLI_modules/cli/analyzer/two_driver_telemetry_comparison_fixed.py`
  - `_calculate_speed_difference()` (Line 446)
  - `_calculate_distance_difference()` (Line 577)
  - `_calculate_time_difference()` (Line 638)

- **API 路由**：`api/routers/analysis.py`
  - `_merge_cross_event_telemetry()` (Line 21)
  - `/cross-event-comparison` 端點 (Line 308)

- **GUI 模組**：`modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py`
  - `_on_cross_event_data_loaded()` (Line 1605)

---

**更新完成！請進行測試 🎯**
