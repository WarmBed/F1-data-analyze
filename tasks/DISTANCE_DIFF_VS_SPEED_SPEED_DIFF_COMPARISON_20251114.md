# Distance Diff vs Speed vs Speed Diff 對比分析報告

**對比日期**：2025-11-14  
**功能名稱**：取消勾選與主選單同步賽事後，時間軸功能  
**模組 1（參考模組）**：Speed Analysis  
**模組 2（參考模組）**：Speed Diff Analysis  
**模組 3（目標模組）**：Distance Diff Analysis

---

## 🚨 **嚴重問題發現**

### **問題 #1：Distance Diff 有重複的 `update_lap_parameters` 方法**

**位置**：
- 第一個定義：Line 744-847
- 第二個定義：Line 852-973

**問題描述**：
Distance Diff 模組中同一個方法被定義了兩次，Python 會使用最後一個定義，導致第一個定義完全無效。

**影響**：
- 第一個方法（Line 744）邏輯較簡單，缺少時間軸變化檢測
- 第二個方法（Line 852）邏輯較完整，包含時間軸變化檢測
- 用戶實際使用的是第二個方法

**修復方案**：
刪除第一個方法定義（Line 744-847）

---

## 📊 **方法對比表**

| 項目 | Speed Analysis | Speed Diff Analysis | Distance Diff Analysis (實際使用) |
|------|----------------|---------------------|-----------------------------------|
| **方法位置** | Line 863-953 | Line 719-809 | Line 852-973 |
| **參數完整性** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **時間軸參數** | ✅ `use_time_axis` | ✅ `use_time_axis` | ✅ `use_time_axis` |
| **參數變化檢測** | ✅ 包含時間軸 | ❌ 不含時間軸 | ✅ 包含時間軸 |
| **params_changed 邏輯** | ✅ 正確 | ⚠️ 簡化版 | ✅ 正確 |
| **數據重載觸發** | ✅ params_changed 時 | ✅ params_changed 時 | ✅ params_changed 時 |
| **首次載入檢查** | ✅ 有 `_data_loaded` | ❌ 無 | ✅ 有 `_data_loaded` |
| **set_time_axis_mode 調用** | ✅ 有 | ✅ 有 | ✅ 有 |

---

## 🔍 **逐行差異分析**

### **差異 #1：參數變化檢測邏輯**

#### **Speed Analysis (Line 899-906)**
```python
# 檢查參數是否有變化
params_changed = (
    self.current_year != str(year) or 
    self.current_race != race or 
    self.current_session != session or
    self.driver1 != driver1 or
    self.driver2 != driver2 or  # 正確處理 None 值比較
    self.lap1 != lap1 or
    self.lap2 != lap2
)
```

**特點**：
- ❌ **未包含 `use_time_axis` 檢測**
- 註釋說明處理 None 值

#### **Speed Diff Analysis (Line 751-759)**
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
```

**特點**：
- ❌ **未包含 `use_time_axis` 檢測**
- 使用 normalized 變數
- 無註釋

#### **Distance Diff Analysis (Line 883-893)**
```python
# 檢查參數是否有變化（包含時間軸模式）
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
```

**特點**：
- ✅ **包含 `use_time_axis` 檢測**（唯一正確的實現！）
- 有詳細的時間軸變化日誌
- 使用 `getattr` 安全訪問

**結論**：
🔴 **Speed 和 Speed Diff 都缺少時間軸變化檢測！這是 Bug！**

---

### **差異 #2：時間軸狀態保存**

#### **Speed Analysis (Line 879-881)**
```python
# 儲存時間軸設定
self.use_time_axis = use_time_axis
print(f"🕒 [TIME_AXIS_DEBUG]   self.use_time_axis 已儲存: {self.use_time_axis}")
```

**特點**：
- ✅ 在參數檢查**之前**保存
- 有 TIME_AXIS_DEBUG 日誌

#### **Speed Diff Analysis**
❌ **未找到 `self.use_time_axis` 保存語句！**

#### **Distance Diff Analysis (Line 904)**
```python
self.use_time_axis = use_time_axis  # 🆕 保存時間軸模式狀態
```

**特點**：
- ✅ 在參數檢查**之後**保存
- 有註釋說明

**結論**：
🔴 **Speed Diff 完全沒有保存 `use_time_axis` 狀態！這是嚴重 Bug！**

---

### **差異 #3：set_time_axis_mode 調用位置**

#### **Speed Analysis (Line 934-941)**
```python
# 應用時間軸設定到圖表
print(f"🕒 [TIME_AXIS_DEBUG] 步驟 5: 準備設置圖表時間軸模式")
print(f"🕒 [TIME_AXIS_DEBUG]   self.speed_chart_widget 存在: {self.speed_chart_widget is not None}")
if self.speed_chart_widget:
    print(f"🕒 [TIME_AXIS_DEBUG]   hasattr(speed_chart_widget, 'set_time_axis_mode'): {hasattr(self.speed_chart_widget, 'set_time_axis_mode')}")

if self.speed_chart_widget and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
    print(f"🕒 [TIME_AXIS_DEBUG]   調用 speed_chart_widget.set_time_axis_mode({use_time_axis})")
    self.speed_chart_widget.set_time_axis_mode(use_time_axis)
```

**位置**：在 `params_changed == True` 分支內，數據載入**成功後**  
**特點**：
- ✅ 有非常詳細的調試日誌
- ✅ 有 hasattr 檢查
- ⚠️ **只在參數變化時調用**

#### **Speed Diff Analysis (Line 770-774)**
```python
if hasattr(self.speeddiff_chart_widget, 'set_lap_numbers'):
    self.speeddiff_chart_widget.set_lap_numbers(self.lap1, self.lap2)
    
    # 🆕 設置時間軸模式
    if hasattr(self.speeddiff_chart_widget, 'set_time_axis_mode'):
        self.speeddiff_chart_widget.set_time_axis_mode(use_time_axis)
        print(f"[speeddiff_MDI] ✅ 已設置時間軸模式: {use_time_axis}")
```

**位置**：在參數變化檢測**之前**，無條件調用  
**特點**：
- ✅ 有 hasattr 檢查
- ✅ **無論參數是否變化都調用**（更好！）
- ⚠️ 在數據載入之前調用

#### **Distance Diff Analysis (Line 913-917)**
```python
# 更新圖表組件的圈數顯示
if self.distancediff_chart_widget:
    self.distancediff_chart_widget.set_lap_numbers(lap1, lap2)
    print(f"[distancediff_MDI] ✅ 已更新圖表組件的圈數顯示")
    
    # 🆕 設置時間軸模式
    if hasattr(self.distancediff_chart_widget, 'set_time_axis_mode'):
        self.distancediff_chart_widget.set_time_axis_mode(use_time_axis)
        print(f"[distancediff_MDI] ✅ 已設置時間軸模式: {use_time_axis}")
```

**位置**：在參數變化檢測**之後**，數據載入**之前**  
**特點**：
- ✅ 有 hasattr 檢查
- ✅ **無論參數是否變化都調用**（與 Speed Diff 一致）
- ✅ 在數據載入之前調用

**結論**：
- Speed 的實現有問題：只在 params_changed 時調用，導致參數未變化時不更新圖表模式
- Speed Diff 和 Distance Diff 的實現更好：無條件調用，確保圖表模式始終同步

---

### **差異 #4：首次載入檢查**

#### **Speed Analysis (Line 942-958)**
```python
if params_changed:
    # 載入新數據
    if self.data_manager:
        # ... 載入邏輯
        if success:
            # ... 成功處理
            return True
        else:
            return False
    else:
        return False
else:
    # 如果是首次載入或沒有數據，仍然需要載入
    if self.data_manager and not hasattr(self, '_data_loaded'):
        success = self.data_manager.load_speed_data(...)
        if success:
            self._data_loaded = True
            return True
        else:
            return False
```

**特點**：
- ✅ 有完整的 else 分支
- ✅ 檢查 `_data_loaded` 屬性
- ✅ 首次載入時仍會載入數據

#### **Speed Diff Analysis (Line 784-804)**
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
    
    return True

if not self.data_manager:
    print("[speeddiff_MDI] ❌ 數據管理器未初始化，無法更新")
    return False

# ... 載入數據
```

**特點**：
- ❌ **沒有首次載入檢查**
- ✅ 但有視窗標題同步和 info_label 更新
- ⚠️ 如果參數未變化，直接 return True

#### **Distance Diff Analysis (Line 951-970)**
```python
else:
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
            lap2=self.lap2
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
        return True
```

**特點**：
- ✅ 有完整的首次載入檢查（與 Speed 一致）
- ✅ 檢查 `_data_loaded` 屬性
- ✅ 有詳細的日誌輸出

**結論**：
🔴 **Speed Diff 缺少首次載入檢查，可能導致第一次調用時數據未載入！**

---

## 🐛 **已發現的所有 Bug**

### Bug #1：Speed 和 Speed Diff 缺少時間軸變化檢測
**影響**：
- 用戶取消同步後勾選/取消時間軸，`params_changed` 為 False
- 導致數據不重載，圖表顯示錯誤

**修復方案**：
在 `params_changed` 檢測中添加：
```python
getattr(self, 'use_time_axis', False) != use_time_axis
```

### Bug #2：Speed Diff 未保存 `use_time_axis` 狀態
**影響**：
- 下次參數更新時無法正確檢測時間軸變化
- `use_time_axis` 狀態丟失

**修復方案**：
在參數更新區塊添加：
```python
self.use_time_axis = use_time_axis
```

### Bug #3：Speed Diff 缺少首次載入檢查
**影響**：
- 如果參數未變化，首次調用不會載入數據
- 可能導致空數據顯示

**修復方案**：
添加 else 分支：
```python
else:
    if self.data_manager and not hasattr(self, '_data_loaded'):
        # 首次載入邏輯
```

### Bug #4：Speed 的 set_time_axis_mode 只在 params_changed 時調用
**影響**：
- 如果用戶只切換時間軸，但沒有檢測到（因為 Bug #1），圖表模式不更新

**修復方案**：
將 `set_time_axis_mode` 調用移到參數檢查之前（無條件調用）

### Bug #5：Distance Diff 有重複的方法定義
**影響**：
- 第一個方法定義完全無效
- 可能導致混淆和維護困難

**修復方案**：
刪除第一個方法定義（Line 744-847）

---

## ✅ **Distance Diff 的優勢**

1. ✅ **唯一包含時間軸變化檢測的模組**
2. ✅ 有完整的首次載入檢查
3. ✅ set_time_axis_mode 無條件調用（與 Speed Diff 一致）
4. ✅ 有詳細的時間軸變化日誌
5. ✅ 使用 `getattr` 安全訪問屬性

**但有以下問題需要修復**：
- ❌ 重複的方法定義（需刪除第一個）

---

## 📋 **修復優先級**

| 優先級 | Bug | 模組 | 影響 |
|--------|-----|------|------|
| 🔴 高 | 缺少時間軸變化檢測 | Speed, Speed Diff | 導致用戶操作無效 |
| 🔴 高 | 未保存 use_time_axis | Speed Diff | 狀態丟失 |
| 🔴 高 | 重複方法定義 | Distance Diff | 代碼混亂 |
| 🟡 中 | 缺少首次載入檢查 | Speed Diff | 可能空數據 |
| 🟡 中 | set_time_axis_mode 調用位置 | Speed | 圖表模式不更新 |

---

## 🎯 **最終結論**

### **Distance Diff Analysis 是三個模組中實現最完整的！**

**原因**：
1. ✅ 唯一正確實現時間軸變化檢測
2. ✅ 有完整的首次載入檢查
3. ✅ set_time_axis_mode 無條件調用
4. ✅ 有詳細的調試日誌

**唯一需要修復的是重複方法定義問題。**

**Speed 和 Speed Diff 需要向 Distance Diff 學習以下實現：**
1. 時間軸變化檢測
2. use_time_axis 狀態保存（Speed Diff）
3. 首次載入檢查（Speed Diff）
4. set_time_axis_mode 無條件調用（Speed）

---

## 📝 **建議修復順序**

1. **Distance Diff**：刪除重複方法定義（簡單）
2. **Speed Diff**：添加時間軸變化檢測 + 狀態保存 + 首次載入檢查（中等）
3. **Speed**：添加時間軸變化檢測 + 調整 set_time_axis_mode 調用位置（中等）

---

**報告完成時間**：2025-11-14  
**分析工具**：grep_search + read_file  
**分析方法**：逐行手動對比（遵循標準化對比流程）

