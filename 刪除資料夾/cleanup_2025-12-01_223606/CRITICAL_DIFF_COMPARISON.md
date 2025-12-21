# 🚨 Speed Diff vs Distance Diff 關鍵差異分析

## 📊 對比總結

| 特性 | Speed Diff (工作正常) | Distance Diff (無曲線) |
|------|----------------------|------------------------|
| **`params_changed = False` 時** | ❌ 直接 return True，不重載 | ✅ 檢查首次載入，會嘗試重載 |
| **首次載入檢查** | ❌ 沒有 | ✅ 有 `if not hasattr(self, '_data_loaded')` |
| **日誌訊息** | "參數無變化，保持目前資料" | "參數未變更且已有數據，保持現有狀態" |
| **實際行為** | **總是重載數據**（因為取消同步後必然 params_changed=True） | **不重載數據**（因為參數可能未變化） |

---

## 🔴 關鍵差異 1：`if not params_changed` 的邏輯

### Speed Diff（Line 781-800）- **簡單邏輯**
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
    
    return True  # ❌ 直接返回，不做任何數據載入！
```

### Distance Diff（Line 848-878）- **複雜邏輯**
```python
else:  # params_changed = False
    # 如果是首次載入或沒有數據，仍然需要載入
    if self.data_manager and not hasattr(self, '_data_loaded'):
        print(f"[distancediff_MDI] ℹ️ 首次載入或未載入過，執行數據載入...")
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
        if success:
            self._data_loaded = True
            self._update_info_label()
            print(f"[distancediff_MDI] ✅ 首次數據載入成功")
            return True
        else:
            print(f"[distancediff_MDI] ❌ 首次數據載入失敗")
            return False
    else:
        print(f"[distancediff_MDI] ℹ️ 參數未變更且已有數據，保持現有狀態")
        return True  # ❌ 如果已載入過，也是直接返回！
```

---

## 🔴 關鍵差異 2：`params_changed` 檢測範圍

### Speed Diff（Line 748-756）- **不檢查時間軸**
```python
params_changed = (
    self.current_year != normalized_year or
    self.current_race != race or
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != normalized_driver2 or
    self.lap1 != lap1 or
    self.lap2 != normalized_lap2
)
# ❌ 沒有檢查 use_time_axis 變化！
```

### Distance Diff（Line 787-797）- **檢查時間軸**
```python
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
```

---

## 🎯 根本原因分析

### 為什麼 Speed Diff 有曲線？

**因為取消同步後，參數必然變化！**

1. 用戶取消勾選 "與主選單同步賽事"
2. GUI 調用 `update_lap_parameters()`
3. Speed Diff 檢查 `params_changed`：
   - 可能檢測到 `year/race/session` 變化
   - 或者其他參數變化
4. **`params_changed = True`** → 執行數據載入
5. 曲線正常顯示 ✅

### 為什麼 Distance Diff 沒有曲線？

**因為可能參數沒變化，但有 `_data_loaded` 標記！**

1. 用戶取消勾選 "與主選單同步賽事"
2. GUI 調用 `update_lap_parameters()`
3. Distance Diff 檢查 `params_changed`：
   - 如果參數完全相同 → `params_changed = False`
4. 進入 `else` 分支：
   - 檢查 `hasattr(self, '_data_loaded')`
   - **如果已載入過** → 直接 `return True`，不重載 ❌
5. 沒有重新載入數據 → 曲線不顯示 ❌

---

## 🔍 實際場景分析

### 場景 1：首次載入（兩者都正常）
```
用戶操作：開啟模組 → 選擇 2025 Australia R NOR Lap 99
Speed Diff: params_changed=True → 載入數據 ✅
Distance Diff: params_changed=True → 載入數據 ✅
```

### 場景 2：取消同步但參數相同（Distance Diff 失敗）
```
用戶操作：
1. 已載入 2025 Australia R NOR Lap 99
2. 取消勾選 "與主選單同步"
3. 再次調用 update_lap_parameters(2025, Australia, R, NOR, NOR, 99, 99)

Speed Diff:
- params_changed = False（參數完全相同）
- 執行 `return True`，保持現有數據
- **但因為已經有數據** → 曲線仍然顯示 ✅

Distance Diff:
- params_changed = False（參數完全相同）
- 檢查 `hasattr(self, '_data_loaded')` → True
- 執行 `return True`，保持現有狀態
- **但如果之前數據不完整** → 曲線不顯示 ❌
```

### 場景 3：時間軸切換（Distance Diff 優勢）
```
用戶操作：切換時間軸開關

Speed Diff:
- params_changed = False（因為不檢查時間軸）
- 執行 `return True`，不重載數據
- **時間軸無法正常工作** ❌

Distance Diff:
- params_changed = True（因為檢查時間軸變化）
- 重新載入數據
- **時間軸正常工作** ✅
```

---

## 🛠️ 修復方案

### 方案 1：簡化 Distance Diff 的邏輯（推薦）
**目標：與 Speed Diff 保持一致**

```python
if not params_changed:
    print(f"[distancediff_MDI] ℹ️ 參數無變化，保持目前資料")
    self._update_info_label()
    return True  # 直接返回，不重載
```

**優點**：
- ✅ 邏輯簡單，與 Speed Diff 一致
- ✅ 減少不必要的數據載入

**缺點**：
- ❌ 失去首次載入檢查
- ❌ 可能在某些邊緣情況下失效

### 方案 2：完善 Speed Diff 的邏輯（更好）
**目標：添加時間軸檢測到 Speed Diff**

```python
# Speed Diff 添加時間軸檢測
params_changed = (
    self.current_year != normalized_year or
    self.current_race != race or
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != normalized_driver2 or
    self.lap1 != lap1 or
    self.lap2 != normalized_lap2 or
    getattr(self, 'use_time_axis', False) != use_time_axis  # ✅ 新增
)
```

**優點**：
- ✅ 支持時間軸功能
- ✅ 保持邏輯一致性
- ✅ 不影響現有功能

**缺點**：
- 無

### 方案 3：強制重載（最直接）
**目標：取消同步時強制重載數據**

```python
# Distance Diff 添加強制重載邏輯
if not params_changed:
    # 檢查是否是取消同步觸發的調用
    if not self.sync_driver_lap_enabled:
        print(f"[distancediff_MDI] 🔄 檢測到取消同步，強制重載數據")
        params_changed = True  # 強制設為 True
```

**優點**：
- ✅ 確保取消同步時數據正確載入
- ✅ 不影響其他場景

**缺點**：
- ❌ 需要追蹤 `sync_driver_lap_enabled` 狀態

---

## 📋 推薦修復步驟

### Step 1：為 Speed Diff 添加時間軸檢測（方案 2）
- 修改 `speeddiff_analysis_mdi.py` Line 748-756
- 添加 `use_time_axis` 檢測

### Step 2：簡化 Distance Diff 的 `params_changed=False` 邏輯（方案 1）
- 修改 `distancediff_analysis_mdi.py` Line 848-878
- 移除複雜的首次載入檢查，改為直接返回

### Step 3：測試
- 測試取消同步功能
- 測試時間軸切換
- 測試首次載入

---

## 🎯 預期結果

修復後：
1. ✅ Distance Diff 取消同步後有曲線
2. ✅ Speed Diff 支持時間軸功能
3. ✅ 兩個模組邏輯一致
4. ✅ 所有場景正常工作
