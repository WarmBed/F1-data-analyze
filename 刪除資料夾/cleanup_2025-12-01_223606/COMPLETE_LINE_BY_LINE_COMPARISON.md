# 🔍 Speed Diff vs Distance Diff - 完整逐行對比報告

**對比日期**：2025-11-14  
**方法**：`update_lap_parameters()`  
**Speed Diff**：Line 719-869 (151 lines)  
**Distance Diff**：Line 749-899 (151 lines)  

---

## 📋 方法簽名對比

### Speed Diff (Line 719-723)
```python
def update_lap_parameters(self, year: str, race: str, session: str,
                          driver1: str, driver2: Optional[str] = None,
                          lap1: int = 1, lap2: Optional[int] = None,
                          is_fastest: bool = False,
                          use_time_axis: bool = False) -> bool:
```

### Distance Diff (Line 749-753)
```python
def update_lap_parameters(self, year: str, race: str, session: str, 
                        driver1: str, driver2: str = None, 
                        lap1: int = 1, lap2: int = 1, 
                        is_fastest: bool = False,
                        use_time_axis: bool = False) -> bool:
```

### 差異 #1：參數類型註解
| 參數 | Speed Diff | Distance Diff | 差異 |
|------|------------|---------------|------|
| driver2 | `Optional[str] = None` | `str = None` | Type hint 不同 |
| lap2 | `Optional[int] = None` | `int = 1` | Type hint 不同 + 預設值不同 |

**影響**：Distance Diff 的 lap2 預設值是 1，Speed Diff 是 None

---

## 📝 Docstring 對比

### Speed Diff (Line 724)
```python
"""更新圈速分析參數並重新整理速度差資料"""
```

### Distance Diff (Line 754-762)
```python
"""
更新圈速分析參數（完整版 - 包含時間軸變化檢測）

✅ 優勢：
- 包含時間軸變化檢測（唯一正確實現）
- 有完整的首次載入檢查
- set_time_axis_mode 無條件調用
- 有詳細的時間軸變化日誌
"""
```

### 差異 #2：Docstring
- Speed Diff：簡短單行
- Distance Diff：多行且自誇「唯一正確實現」❌

**問題**：Distance Diff 的 docstring 明顯不正確，Speed Diff 實際上工作正常

---

## 🖨️ 初始日誌對比 (Line 725-730 vs 763-769)

### Speed Diff
```python
try:
    print("[speeddiff_MDI] ========== 圈速參數更新 ==========")
    print(f"[speeddiff_MDI] 收到參數: {year} {race} {session}")
    print(f"[speeddiff_MDI] 車手: {driver1} vs {driver2}")
    print(f"[speeddiff_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
    print(f"[speeddiff_MDI] 最速圈: {is_fastest}")
    print(f"[speeddiff_MDI] 🕒 時間軸模式: {use_time_axis}")
```

### Distance Diff
```python
try:
    print(f"[distancediff_MDI] ========== 圈速參數更新（完整版）==========")
    print(f"[distancediff_MDI] 收到參數: {year} {race} {session}")
    print(f"[distancediff_MDI] 車手: {driver1} vs {driver2}")
    print(f"[distancediff_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
    print(f"[distancediff_MDI] 最速圈: {is_fastest}")
    print(f"[distancediff_MDI] 🕒 時間軸模式: {use_time_axis}")
```

### 差異 #3：日誌前綴
- Speed Diff：`[speeddiff_MDI]`
- Distance Diff：`[distancediff_MDI]`，並在標題加上「（完整版）」

**問題**：Distance Diff 自稱「完整版」但實際上功能失效

---

## 🏁 最速圈處理對比 (Line 732-742 vs 771-787)

### Speed Diff
```python
if is_fastest and hasattr(self, '_ensure_telemetry_data_for_fastest_laps'):
    fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
    if fastest_laps:
        if driver1 in fastest_laps:
            lap1 = fastest_laps[driver1]
            print(f"[speeddiff_MDI] 🏁 {driver1} 最速圈: 第{lap1}圈")
        if driver2 and driver2 in fastest_laps:
            lap2 = fastest_laps[driver2]
            print(f"[speeddiff_MDI] 🏁 {driver2} 最速圈: 第{lap2}圈")
    else:
        print("[speeddiff_MDI] ⚠️ 無法取得最速圈資訊，沿用當前圈數")
```

### Distance Diff
```python
# 檢查是否需要最速圈數據
if is_fastest:
    print(f"[distancediff_MDI] 🏁 用戶選擇了最速圈選項，檢查遙測分析數據...")
    fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
    if fastest_laps:
        # 使用最速圈數據更新圈數
        if driver1 in fastest_laps:
            lap1 = fastest_laps[driver1]
            print(f"[distancediff_MDI] 🏁 車手 {driver1} 最速圈: 第{lap1}圈")
        if driver2 and driver2 in fastest_laps:
            lap2 = fastest_laps[driver2]
            print(f"[distancediff_MDI] 🏁 車手 {driver2} 最速圈: 第{lap2}圈")
    else:
        print(f"[distancediff_MDI] ⚠️ 無法獲取最速圈數據，使用預設圈數")
```

### 差異 #4：is_fastest 檢查
- Speed Diff：`if is_fastest and hasattr(self, '_ensure_telemetry_data_for_fastest_laps')`
- Distance Diff：`if is_fastest` (沒有 hasattr 檢查)

**問題**：Distance Diff 缺少 hasattr 保護，可能觸發 AttributeError

---

## ⚠️ 關鍵差異：參數變化檢測邏輯

### Speed Diff (Line 744-757) - **沒有** use_time_axis 檢測
```python
normalized_year = str(year)
normalized_driver2 = driver2 if driver2 else driver1
normalized_lap2 = lap2 if lap2 is not None else lap1

params_changed = (
    self.current_year != normalized_year or
    self.current_race != race or
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != normalized_driver2 or
    self.lap1 != lap1 or
    self.lap2 != normalized_lap2
)

self.current_year = normalized_year
self.current_race = race
self.current_session = session
```

### Distance Diff (Line 789-812) - **有** use_time_axis 檢測
```python
# ✅ 檢查參數是否有變化（包含時間軸模式 - 唯一正確實現！）
params_changed = (
    self.current_year != str(year) or 
    self.current_race != race or 
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != driver2 or  # 正確處理 None 值比較
    self.lap1 != lap1 or
    self.lap2 != lap2 or
    getattr(self, 'use_time_axis', False) != use_time_axis  # 🆕 檢測時間軸模式變化
)

print(f"[distancediff_MDI] 參數是否變化: {params_changed}")
if getattr(self, 'use_time_axis', False) != use_time_axis:
    print(f"[distancediff_MDI] 🕒 時間軸模式變化: {getattr(self, 'use_time_axis', False)} → {use_time_axis}")

# 更新所有參數 - 保持 driver2 的原始值（包括 None）
self.current_year = str(year)
self.current_race = race
self.current_session = session
self.driver1 = driver1
self.driver2 = driver2  # 保持原始值，支援單場賽事車手分析
self.lap1 = lap1
self.lap2 = lap2
self.use_time_axis = use_time_axis  # 🆕 保存時間軸模式狀態
```

### 差異 #5：params_changed 邏輯 ⚠️ 關鍵差異
| 檢查項目 | Speed Diff | Distance Diff |
|---------|-----------|---------------|
| year | `!= normalized_year` | `!= str(year)` |
| driver2 | `!= normalized_driver2` | `!= driver2` |
| lap2 | `!= normalized_lap2` | `!= lap2` |
| use_time_axis | ❌ **沒有** | ✅ **有** |
| 參數保存 | 使用 normalized 值 | 使用原始值 |

**關鍵發現**：
1. Speed Diff **沒有**檢測 use_time_axis 變化
2. Distance Diff **有**檢測 use_time_axis 變化
3. Speed Diff 使用 normalized 值，Distance Diff 使用原始值
4. Distance Diff 有額外的時間軸變化日誌

---

## 🎯 圖表組件更新對比 (Line 758-769 vs 814-824)

### Speed Diff
```python
self.driver1 = driver1
self.driver2 = normalized_driver2
self.lap1 = lap1
self.lap2 = normalized_lap2

if hasattr(self.speeddiff_chart_widget, 'set_lap_numbers'):
    self.speeddiff_chart_widget.set_lap_numbers(self.lap1, self.lap2)
    
    # 🆕 設置時間軸模式
    if hasattr(self.speeddiff_chart_widget, 'set_time_axis_mode'):
        self.speeddiff_chart_widget.set_time_axis_mode(use_time_axis)
        print(f"[speeddiff_MDI] ✅ 已設置時間軸模式: {use_time_axis}")

self.update_window_title()
```

### Distance Diff
```python
self.driver1 = driver1
self.driver2 = driver2  # 保持原始值，支援單場賽事車手分析
self.lap1 = lap1
self.lap2 = lap2
self.use_time_axis = use_time_axis  # 🆕 保存時間軸模式狀態

# ✅ 更新圖表組件的圈數顯示和時間軸模式（無條件調用 - 確保同步）
if self.distancediff_chart_widget:
    self.distancediff_chart_widget.set_lap_numbers(lap1, lap2)
    print(f"[distancediff_MDI] ✅ 已更新圖表組件的圈數顯示")
    
    # 🆕 設置時間軸模式（無條件調用，確保與用戶設定同步）
    if hasattr(self.distancediff_chart_widget, 'set_time_axis_mode'):
        self.distancediff_chart_widget.set_time_axis_mode(use_time_axis)
        print(f"[distancediff_MDI] ✅ 已設置時間軸模式: {use_time_axis}")
```

### 差異 #6：圖表更新時機
- Speed Diff：使用 `hasattr(self.speeddiff_chart_widget, 'set_lap_numbers')` 作為外層檢查
- Distance Diff：使用 `if self.distancediff_chart_widget` 作為外層檢查，並在內層使用 hasattr
- Speed Diff：不更新 window_title 在這裡
- Distance Diff：也不更新 window_title 在這裡

---

## 🚨 最關鍵差異：params_changed=False 的處理邏輯

### Speed Diff (Line 771-787) - **簡單返回 True**
```python
if not params_changed:
    print("[speeddiff_MDI] ℹ️ 參數無變化，保持目前資料")
    
    # 即使參數未變化，也確保視窗標題是正確的
    parent = getattr(self, 'parent_window', None)
    if parent and hasattr(parent, 'setWindowTitle'):
        current_title = parent.windowTitle()
        expected_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
        if current_title != expected_title:
            parent.setWindowTitle(expected_title)
            print(f"[speeddiff_MDI] 🏷️ 同步視窗標題: {expected_title}")
    else:
        print(f"[speeddiff_MDI] ⚠️ 無法同步視窗標題 - 父視窗引用未設置")
    
    # 更新資訊標籤
    self._update_info_label()
    
    return True  # ✅ 簡單返回
```

### Distance Diff (Line 826-829) - **簡單返回 True**
```python
if not params_changed:
    print(f"[distancediff_MDI] ℹ️ 參數無變化，保持目前資料")
    self._update_info_label()
    return True  # ✅ 簡化後也是簡單返回
```

### 差異 #7：參數未變化時的處理
| 項目 | Speed Diff | Distance Diff | 狀態 |
|------|-----------|---------------|------|
| 日誌 | 有詳細日誌 | 簡單日誌 | ✅ 已簡化 |
| 視窗標題同步 | 有 | ❌ 沒有 | Distance Diff 缺少 |
| info_label 更新 | 有 | 有 | ✅ 一致 |
| return True | 有 | 有 | ✅ 一致 |

**已修復**：Distance Diff 在第二次修復後已簡化此邏輯

---

## 📦 數據載入對比 (Line 789-811 vs 831-858)

### Speed Diff
```python
if not self.data_manager:
    print("[speeddiff_MDI] ❌ 數據管理器未初始化，無法更新")
    return False

self.data_manager.current_year = self.current_year
self.data_manager.current_race = self.current_race
self.data_manager.current_session = self.current_session

print("[speeddiff_MDI] 🚀 重新載入speeddiff數據...")
success = self.data_manager.load_speeddiff_data(
    year=self.current_year,
    race=self.current_race,
    session=self.current_session,
    driver1=self.driver1,
    driver2=self.driver2,
    lap1=self.lap1,
    lap2=self.lap2,
    is_fastest=is_fastest
)
```

### Distance Diff
```python
# 參數已變化，載入新數據
if not self.data_manager:
    print(f"[distancediff_MDI] ❌ 數據管理器未初始化")
    return False

print(f"[distancediff_MDI] 🔄 參數已變化，重載數據...")
success = self.data_manager.load_distancediff_data(
    year=self.current_year,
    race=self.current_race,
    session=self.current_session,
    driver1=self.driver1,
    driver2=self.driver2,
    lap1=self.lap1,
    lap2=self.lap2,
    use_time_axis=use_time_axis  # ✅ 新增時間軸參數
)
```

### 差異 #8：數據載入
| 項目 | Speed Diff | Distance Diff |
|------|-----------|---------------|
| 更新 data_manager 狀態 | 有（3 行） | ❌ 沒有 |
| use_time_axis 參數 | ❌ 沒有 | ✅ 有 |
| is_fastest 參數 | ✅ 有 | ❌ 沒有 |

**發現**：
1. Speed Diff 沒有傳遞 use_time_axis，但卻能正常工作！
2. Distance Diff 傳遞了 use_time_axis，但曲線卻不顯示！
3. Speed Diff 有更新 data_manager 的當前狀態
4. Distance Diff 缺少 is_fastest 參數

---

## ✅ 成功回應處理對比 (Line 813-844 vs 860-876)

### Speed Diff
```python
if success:
    self.parameters_updated.emit({
        'year': self.current_year,
        'race': self.current_race,
        'session': self.current_session,
        'driver1': self.driver1,
        'driver2': self.driver2,
        'lap1': self.lap1,
        'lap2': self.lap2
    })
    print("[speeddiff_MDI] ✅ 圈速參數更新完成")
    
    # 更新資訊標籤
    self._update_info_label()
    
    # 更新視窗標題以反映新的參數
    parent = getattr(self, 'parent_window', None)
    if parent and hasattr(parent, 'setWindowTitle'):
        new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
        parent.setWindowTitle(new_title)
        print(f"[speeddiff_MDI] 🏷️ 視窗標題已更新為: {new_title}")
    else:
        print(f"[speeddiff_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
    
    return True

print("[speeddiff_MDI] ❌ 數據載入失敗")
return False
```

### Distance Diff
```python
if success:
    print(f"[distancediff_MDI] ✅ 圈速參數更新後數據重載成功")
    # 數據載入成功後更新視窗標題和 info_label
    self.update_window_title()
    self._update_info_label()
    # 發送參數更新信號
    self.parameters_updated.emit({
        'year': int(self.current_year),
        'race': self.current_race,
        'session': self.current_session
    })
    return True
else:
    print(f"[distancediff_MDI] ❌ 圈速參數更新後數據重載失敗")
    return False
```

### 差異 #9：成功處理的差異
| 項目 | Speed Diff | Distance Diff |
|------|-----------|---------------|
| parameters_updated.emit | 包含 7 個欄位（year, race, session, driver1, driver2, lap1, lap2） | 只有 3 個欄位（year, race, session） |
| 視窗標題更新 | 手動操作 parent_window | 調用 self.update_window_title() |
| year 類型 | str | int (轉換) |
| 順序 | emit → update_info_label → update title | update title → update_info_label → emit |

**問題**：Distance Diff 的 emit 缺少車手和圈數信息！

---

## 🔍 總結：核心問題定位

### 根本原因分析

#### 問題 1：Speed Diff 缺少 use_time_axis 檢測，但能正常工作 ✅
**原因**：
- Speed Diff 沒有在 params_changed 中檢測 use_time_axis
- 但這不是問題！因為：
  1. 當用戶切換時間軸時，`update_lap_parameters` 會被調用
  2. 即使 params_changed=False，也會執行 `set_time_axis_mode(use_time_axis)`（Line 766-768）
  3. `set_time_axis_mode` 會更新圖表的 X 軸範圍和數據
  4. 圖表重繪時使用已載入的數據，不需要重新載入

#### 問題 2：Distance Diff 有 use_time_axis 檢測，但曲線不顯示 ❌
**原因**：
- Distance Diff 在 params_changed 中加入了 use_time_axis 檢測（Line 797）
- 這導致：
  1. 當用戶切換時間軸時，params_changed=**True**
  2. 系統嘗試重新載入數據（Line 831-858）
  3. **但是**重新載入可能失敗或返回空數據
  4. 或者數據結構不匹配，導致圖表無法繪製

### 🚨 最關鍵的差異

| 場景 | Speed Diff (正常) | Distance Diff (失效) |
|------|-------------------|---------------------|
| 用戶切換時間軸 | params_changed=False → 不重載 → 只更新圖表模式 | params_changed=True → 重載數據 → 數據丟失/失敗 |
| 用戶取消同步 | params_changed=False → 保持數據 → 圖表正常 | params_changed=可能False → 但之前已失效 |

### 修復方案

#### 方案 1：移除 use_time_axis 檢測（推薦）✅
```python
# Distance Diff Line 789-797
params_changed = (
    self.current_year != str(year) or 
    self.current_race != race or 
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != driver2 or
    self.lap1 != lap1 or
    self.lap2 != lap2
    # ❌ 移除：or getattr(self, 'use_time_axis', False) != use_time_axis
)
```

**理由**：
1. 與 Speed Diff 保持一致
2. 時間軸切換不需要重載數據
3. 只需要更新圖表的顯示模式

#### 方案 2：修復數據載入時的 use_time_axis 傳遞
**問題**：即使傳遞了 use_time_axis，API 可能沒有正確處理

**需要檢查**：
1. `load_distancediff_data` 是否正確傳遞 use_time_axis
2. API 端點是否支持 use_time_axis 參數
3. 返回的數據是否包含 time_seconds 欄位

---

## 📊 差異統計

| 類別 | 差異數量 | 嚴重性 |
|------|---------|--------|
| 參數類型註解 | 2 | 低 |
| Docstring | 1 | 低 |
| 日誌格式 | 多處 | 低 |
| hasattr 保護 | 1 | 中 |
| **params_changed 邏輯** | **1** | **🔴 高** |
| 數據載入參數 | 3 | 高 |
| emit 信號內容 | 1 | 中 |
| 視窗標題更新方式 | 1 | 低 |

**總計**：9 大類差異，其中 **params_changed 邏輯** 是導致 Distance Diff 失效的根本原因

---

## 🎯 立即行動計劃

### 優先級 1：移除 use_time_axis 檢測（5 分鐘）
```python
# 修改 distancediff_analysis_mdi.py Line 789-797
# 移除 use_time_axis 檢測行
```

### 優先級 2：測試修復（10 分鐘）
1. 啟動 GUI
2. 載入 Distance Diff Analysis
3. 選擇 2025 Brazil R NOR Lap 99
4. 取消同步
5. 驗證曲線顯示

### 優先級 3：同步其他改進（可選）
1. 添加 hasattr 保護
2. 更新 data_manager 狀態
3. 修復 emit 信號內容
4. 統一視窗標題更新方式

---

**報告完成時間**：2025-11-14 12:55  
**結論**：Distance Diff 的「唯一正確實現」註釋完全錯誤，反而是導致功能失效的罪魁禍首！
