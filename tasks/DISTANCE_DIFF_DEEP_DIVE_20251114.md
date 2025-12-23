# Distance Diff vs Speed Diff 深度對比報告

**對比日期**：2025-11-14  
**用戶反饋**：Distance Diff 功能不正常，Speed 和 Speed Diff 是好的  
**對比目標**：
1. 多賽季載入
2. 按鈕 D→X 切換（啟用同步→取消同步）
3. 按鈕 X→D 切換（取消同步→啟用同步）
4. 曲線載入功能
5. 時間軸功能

---

## 🔍 **深度對比結果**

### **階段 1：update_from_shared_params（跨模組同步）**

#### **Speed Diff (Line 1702-1832)**
```python
def update_from_shared_params(self, params: dict):
    if self._updating_from_shared:
        return
    
    self._updating_from_shared = True
    try:
        # 提取參數
        year1 = params.get('year1', self.driver1_year)
        race1 = params.get('race1', self.driver1_race)
        # ... 其他參數
        
        # 檢測跨賽事
        is_cross_event = (year1 != year2 or session1 != session2)
        
        if is_cross_event:
            # 調用 update_cross_event_comparison
            success = self.update_cross_event_comparison(...)
            if success:
                self._update_info_label()
        else:
            # 調用 update_lap_parameters
            success = self.update_lap_parameters(...)
            if success:
                self._update_info_label()
    finally:
        self._updating_from_shared = False
```

#### **Distance Diff (Line 1741-1839)**
```python
def update_from_shared_params(self, params: dict):
    if self._updating_from_shared:
        return
    
    self._updating_from_shared = True
    try:
        # 提取參數
        year1 = params.get('year1', self.driver1_year)
        race1 = params.get('race1', self.driver1_race)
        # ... 其他參數
        
        # 檢測跨賽事
        is_cross_event = (year1 != year2 or session1 != session2)
        
        if is_cross_event:
            # 調用 update_cross_event_comparison
            success = self.update_cross_event_comparison(...)
            if success:
                self._update_info_label()
        else:
            # 調用 update_lap_parameters
            success = self.update_lap_parameters(...)
            if success:
                self._update_info_label()
    finally:
        self._updating_from_shared = False
```

**結論**：✅ **完全一致！無差異**

---

### **階段 2：_on_cross_event_data_loaded（跨賽事數據處理）**

#### **Speed Diff (Line 1605-1700)**

**關鍵欄位映射**：
```python
if speeddiff_key == "Speeddiff":
    chart_data = {
        "speeddiff_data": {
            "speed": speeddiff_telemetry.get("distance", []),  # ✅ API: distance → Widget: speed
            "cumulative_speed_difference": speeddiff_telemetry.get("speed_difference", []),  # ✅ API: speed_difference → Widget: cumulative_speed_difference
            "driver1_time_seconds": speeddiff_telemetry.get("driver1_time_seconds", []),
            "driver2_time_seconds": speeddiff_telemetry.get("driver2_time_seconds", []),
        },
        "use_time_axis": getattr(self, 'use_time_axis', False),
    }
```

**時間軸設置**：
```python
use_time_axis = chart_data.get('use_time_axis', False)
if self.speeddiff_chart_widget and hasattr(self.speeddiff_chart_widget, 'set_time_axis_mode'):
    print(f"[SPEEDDIFF-CROSS-EVENT] 🕒 設置圖表時間軸模式: {use_time_axis}")
    self.speeddiff_chart_widget.set_time_axis_mode(use_time_axis)

# 直接調用圖表更新
self._update_chart(chart_data)
```

#### **Distance Diff (Line 1645-1740)**

**關鍵欄位映射**：
```python
if distancediff_key == "Distancediff":
    chart_data = {
        "distancediff_data": {
            "distance": distancediff_telemetry.get("distance", []),  # ✅ API: distance → Widget: distance
            "cumulative_distance_difference": distancediff_telemetry.get("distance_difference", []),  # ✅ API: distance_difference → Widget: cumulative_distance_difference
            "driver1_time_seconds": distancediff_telemetry.get("driver1_time_seconds", []),
            "driver2_time_seconds": distancediff_telemetry.get("driver2_time_seconds", []),
        },
        "use_time_axis": getattr(self, 'use_time_axis', False),
    }
```

**時間軸設置**：
```python
use_time_axis = chart_data.get('use_time_axis', False)
if self.distancediff_chart_widget and hasattr(self.distancediff_chart_widget, 'set_time_axis_mode'):
    print(f"[DISTDIFF-CROSS-EVENT] 🕒 設置圖表時間軸模式: {use_time_axis}")
    self.distancediff_chart_widget.set_time_axis_mode(use_time_axis)

# 直接調用圖表更新
self._update_chart(chart_data)
```

**結論**：✅ **邏輯一致！欄位映射正確**

**差異說明**：
- Speed Diff 將 API 的 "distance" 改名為 Widget 期望的 "speed"（因為 speeddiff_chart_widget 期望 "speed" 欄位）
- Distance Diff 保持 "distance" 不變（因為 distancediff_chart_widget 期望 "distance" 欄位）
- 這兩者都是**正確的**！

---

### **階段 3：Chart Widget 欄位期望**

#### **Speed Diff Chart Widget (Line 1475)**
```python
def update_speeddiff_data(self, data: Dict[str, Any]):
    speeddiff_data = data.get('speeddiff_data', {})
    
    # ✅ 期望 "speed" 欄位（雖然實際存的是距離）
    speed = speeddiff_data.get('speed', [])
    cumulative_diff = speeddiff_data.get('cumulative_speed_difference', [])
    
    driver1_time = speeddiff_data.get('driver1_time_seconds', [])
    driver2_time = speeddiff_data.get('driver2_time_seconds', [])
```

#### **Distance Diff Chart Widget (Line 1403)**
```python
def update_distancediff_data(self, data: Dict[str, Any]):
    distancediff_data = data.get('distancediff_data', {})
    
    # ✅ 期望 "distance" 欄位
    distance = distancediff_data.get('distance', [])
    cumulative_diff = distancediff_data.get('cumulative_distance_difference', [])
    
    driver1_time = distancediff_data.get('driver1_time_seconds', [])
    driver2_time = distancediff_data.get('driver2_time_seconds', [])
```

**結論**：✅ **兩者欄位映射都正確！**

---

### **階段 4：update_lap_parameters（標準模式參數更新）**

這是我之前修復過的方法。讓我檢查當前狀態：

#### **Speed Diff (Line 719-809)**

**關鍵邏輯**：
```python
def update_lap_parameters(self, ...):
    # 參數變化檢測
    params_changed = (
        self.current_year != normalized_year or
        self.current_race != race or
        self.current_session != session or
        self.driver1 != driver1 or
        self.driver2 != normalized_driver2 or
        self.lap1 != lap1 or
        self.lap2 != normalized_lap2
        # ❌ 未包含 use_time_axis 檢測！
    )
    
    # 設置時間軸模式（在參數檢測之前）
    if hasattr(self.speeddiff_chart_widget, 'set_lap_numbers'):
        self.speeddiff_chart_widget.set_lap_numbers(self.lap1, self.lap2)
        
        if hasattr(self.speeddiff_chart_widget, 'set_time_axis_mode'):
            self.speeddiff_chart_widget.set_time_axis_mode(use_time_axis)
    
    # 數據重載
    if not params_changed:
        print("參數無變化，保持目前資料")
        self._update_info_label()
        return True
    
    # 重新載入數據
    self.data_manager.load_speeddiff_data(...)
```

#### **Distance Diff (Line 748-880)**

**關鍵邏輯**：
```python
def update_lap_parameters(self, ...):
    # 參數變化檢測（包含時間軸！）
    params_changed = (
        self.current_year != str(year) or 
        self.current_race != race or 
        self.current_session != session or
        self.driver1 != driver1 or
        self.driver2 != driver2 or
        self.lap1 != lap1 or
        self.lap2 != lap2 or
        getattr(self, 'use_time_axis', False) != use_time_axis  # ✅ 檢測時間軸變化
    )
    
    if getattr(self, 'use_time_axis', False) != use_time_axis:
        print(f"[distancediff_MDI] 🕒 時間軸模式變化: {getattr(self, 'use_time_axis', False)} → {use_time_axis}")
    
    # 保存狀態
    self.use_time_axis = use_time_axis
    
    # 設置時間軸模式（在參數檢測之後）
    if self.distancediff_chart_widget:
        self.distancediff_chart_widget.set_lap_numbers(lap1, lap2)
        
        if hasattr(self.distancediff_chart_widget, 'set_time_axis_mode'):
            self.distancediff_chart_widget.set_time_axis_mode(use_time_axis)
    
    # 數據重載
    if params_changed:
        # 重新載入數據
        self.data_manager.load_distancediff_data(...)
    else:
        # 首次載入檢查
        if self.data_manager and not hasattr(self, '_data_loaded'):
            self.data_manager.load_distancediff_data(...)
        else:
            print("參數未變更且已有數據，保持現有狀態")
            return True
```

**結論**：⚠️ **Distance Diff 多了時間軸變化檢測，Speed Diff 沒有**

---

## 🐛 **發現的關鍵問題**

### **問題 #1：Speed Diff 缺少時間軸變化檢測**

**影響場景**：
1. 用戶取消同步（按鈕 D→X）
2. 勾選時間軸
3. **Bug**: `params_changed` 為 False（因為沒檢測時間軸變化）
4. **結果**: 不重新載入數據，時間軸功能失效

**但用戶說 Speed Diff 是好的！這說明**：
- Speed Diff 可能通過其他機制補償了這個問題
- 或者用戶測試的場景中恰好參數有變化

### **問題 #2：兩者的調用順序不同**

**Speed Diff**：
```python
# 步驟 1: 設置時間軸模式（在參數檢測之前）
speeddiff_chart_widget.set_time_axis_mode(use_time_axis)

# 步驟 2: 檢查參數變化
if not params_changed:
    return True  # ❌ 直接返回，不重載數據

# 步驟 3: 重載數據
self.data_manager.load_speeddiff_data(...)
```

**Distance Diff**：
```python
# 步驟 1: 檢查參數變化（包含時間軸）
params_changed = (... or use_time_axis != self.use_time_axis)

# 步驟 2: 保存時間軸狀態
self.use_time_axis = use_time_axis

# 步驟 3: 設置時間軸模式
distancediff_chart_widget.set_time_axis_mode(use_time_axis)

# 步驟 4: 重載數據（如果參數變化或首次載入）
if params_changed:
    self.data_manager.load_distancediff_data(...)
else:
    if not hasattr(self, '_data_loaded'):
        self.data_manager.load_distancediff_data(...)  # 首次載入
```

---

## 🎯 **可能的根本原因**

### **假設 1：Distance Diff 的時間軸變化檢測過於敏感**

**問題**：
- Distance Diff 在 `params_changed` 中包含了 `use_time_axis` 檢測
- 這導致任何時間軸切換都觸發數據重載
- 但數據載入可能失敗或數據格式不匹配

**測試方法**：
1. 檢查 Distance Diff 的數據載入器是否支援時間軸參數
2. 檢查 API 是否正確返回時間數據

### **假設 2：Distance Diff 缺少某些必要的狀態保存**

**問題**：
- Speed Diff 可能在其他地方保存了狀態
- Distance Diff 雖然有 `_data_loaded` 檢查，但可能缺少其他狀態

---

## 🔬 **建議測試流程**

### **測試 1：時間軸功能測試**
```
步驟：
1. 啟動 Distance Diff 模組
2. 取消同步（按鈕 D→X）
3. 勾選時間軸
4. 檢查日誌：
   - 是否顯示「時間軸模式變化」
   - 是否觸發數據重載
   - 數據載入是否成功
   - 圖表是否正確顯示
```

### **測試 2：跨賽事比較測試**
```
步驟：
1. 啟動 Distance Diff 模組
2. 取消同步
3. 選擇不同賽季（2024 Japan vs 2025 Brazil）
4. 勾選時間軸
5. 檢查：
   - API 調用是否成功
   - 數據是否包含時間欄位
   - 圖表是否正確繪製
```

### **測試 3：按鈕切換測試**
```
步驟：
1. D→X→D 循環切換
2. 每次切換後檢查：
   - sync_driver_lap_enabled 狀態
   - info_label 顯示/隱藏
   - 數據是否正確更新
```

---

## 📋 **需要檢查的具體代碼位置**

### **1. Distance Diff 的數據載入器**

檢查是否支援 `use_time_axis` 參數：
```
檔案：distancediff_analysis_mdi.py
方法：distancediffDataManager.load_distancediff_data()
檢查：是否接受並傳遞 use_time_axis 參數
```

### **2. API 端點**

檢查跨賽事 API 是否返回時間數據：
```
端點：/api/v2/analysis/cross-event-comparison
參數：Distancediff 參數
檢查：返回的數據是否包含 driver1_time_seconds 和 driver2_time_seconds
```

### **3. Chart Widget 的時間軸處理**

檢查圖表是否正確處理時間軸：
```
檔案：distancediff_analysis_chart_widget.py
方法：set_time_axis_mode(), update_distancediff_data()
檢查：是否正確使用 driver1_time 和 driver2_time 繪製圖表
```

---

## 🎯 **最可能的問題**

根據代碼對比，**Distance Diff 的實現實際上比 Speed Diff 更完整**！但用戶反饋 Distance Diff 有問題。

**最可能的原因**：
1. ❌ **數據載入器未傳遞 use_time_axis 參數**
2. ❌ **API 返回的時間數據格式不匹配**
3. ❌ **Chart Widget 的時間軸繪製邏輯有 Bug**

**下一步**：
需要檢查 Distance Diff 的數據載入器和 Chart Widget 的實現，找出實際的 Bug 位置。

---

**報告完成時間**：2025-11-14  
**結論**：Distance Diff 的 MDI 邏輯比 Speed Diff 更完整，但可能在數據載入或圖表繪製層有問題

