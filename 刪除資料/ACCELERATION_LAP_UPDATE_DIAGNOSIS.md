# Acceleration Analysis Lap 參數更新問題診斷報告

**診斷日期**: 2025-10-04  
**問題嚴重性**: 🟡 **中等** - 影響用戶體驗但不影響數據正確性  
**問題狀態**: 🔍 **已診斷，待修復**

---

## 📋 問題描述

**用戶報告**: Acceleration Analysis 模組在使用者通過 toolbar 更換 lap 參數時，GUI 沒有更新資料。

**預期行為**:
1. 用戶在 toolbar 改變 lap1 或 lap2 數值
2. `update_all_lap_analysis()` 被觸發
3. Acceleration Analysis 模組的 `update_lap_parameters()` 被調用
4. 模組重新載入新的 lap 數據並更新圖表

**實際行為**:
- GUI 沒有反應，圖表不更新

---

## 🔍 深度診斷結果

### ✅ 已確認正常的部分

#### 1. Acceleration Analysis 模組有實現 `update_lap_parameters()` 方法

**檔案**: `modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py`  
**位置**: 第 532-627 行

```python
def update_lap_parameters(self, year: str, race: str, session: str, 
                        driver1: str, driver2: str = None, 
                        lap1: int = 1, lap2: int = 1, 
                        is_fastest: bool = False) -> bool:
    """更新圈速分析參數（包含車手和圈數）- 與速度模組一致的接口"""
    try:
        print(f"[acceleration_MDI] ========== 圈速參數更新 ==========")
        print(f"[acceleration_MDI] 收到參數: {year} {race} {session}")
        print(f"[acceleration_MDI] 車手: {driver1} vs {driver2}")
        print(f"[acceleration_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
        
        # 檢查參數是否有變化
        params_changed = (
            self.current_year != str(year) or 
            self.current_race != race or 
            self.current_session != session or
            self.driver1 != driver1 or
            self.driver2 != driver2 or
            self.lap1 != lap1 or
            self.lap2 != lap2
        )
        
        if params_changed:
            # 載入新數據
            if self.data_manager:
                success = self.data_manager.load_acceleration_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    print(f"[acceleration_MDI] ✅ 圈速參數更新後數據重載成功")
                    self.parameters_updated.emit({...})
                    return True
```

**結論**: ✅ 方法實現正確，邏輯完整

#### 2. f1t_gui_main.py 有調用 `update_lap_parameters()`

**檔案**: `f1t_gui_main.py`  
**位置**: 第 6140-6175 行

```python
def update_all_lap_analysis(self):
    """更新所有遙測分析視窗"""
    # ... 獲取參數 ...
    
    # 遍歷所有遙測分析視窗並更新
    for i, analysis_module in enumerate(list(self.lap_analysis_windows), 1):
        # 檢查是否有 update_lap_parameters 方法
        has_method = hasattr(analysis_module, 'update_lap_parameters')
        
        if has_method:
            # 調用更新方法
            success = analysis_module.update_lap_parameters(
                year=year,
                race=race, 
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest=is_fastest
            )
```

**結論**: ✅ 調用邏輯正確

#### 3. Acceleration 模組有被添加到 `lap_analysis_windows` 集合

**檔案**: `f1t_gui_main.py`  
**位置**: 第 9923 行

```python
# 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
self.on_lap_analysis_window_opened(analysis_module, "acceleration")
```

**位置**: 第 6007 行

```python
def on_lap_analysis_window_opened(self, window_object, analysis_type):
    # 存儲視窗對象
    self.lap_analysis_windows.add(window_object)
```

**結論**: ✅ 模組有正確添加到集合

---

### ❌ 可能的問題點

#### 問題 1: 參數變化檢測邏輯可能失效

**位置**: `acceleration_analysis_mdi.py` 第 564-572 行

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

if params_changed:
    # 載入新數據
```

**潛在問題**:
- 如果 `self.lap1` 和 `self.lap2` 沒有被正確初始化，比較可能失敗
- 類型不匹配：`lap1` 可能是 `int`，但 `self.lap1` 可能是 `str`

**診斷方法**: 檢查初始化時是否正確設置這些屬性

#### 問題 2: `data_manager` 可能未正確初始化

**位置**: `acceleration_analysis_mdi.py` 第 591-600 行

```python
if params_changed:
    if self.data_manager:  # ← 檢查 data_manager 是否存在
        success = self.data_manager.load_acceleration_data(...)
    else:
        print(f"[acceleration_MDI] ❌ 數據管理器未初始化")
        return False
```

**潛在問題**:
- 如果 `data_manager` 在 `initialize_module()` 時未正確創建
- 或者在某個時間點被設置為 `None`

#### 問題 3: 類別名稱不匹配

**關鍵發現**: 模組類別名稱是 `accelerationAnalysisModule`（小寫開頭），不符合 Python 命名慣例

**位置**: `acceleration_analysis_mdi.py` 第 315 行

```python
class accelerationAnalysisModule(IAnalysisModule):  # ← 小寫開頭！
```

**潛在影響**:
- 可能導致 `isinstance()` 檢查失敗
- 模組識別問題

---

## 🧪 診斷測試計畫

### 測試 1: 檢查 `lap_analysis_windows` 集合內容

在 `update_all_lap_analysis()` 開始時添加日誌：

```python
def update_all_lap_analysis(self):
    print(f"[DEBUG] lap_analysis_windows 內容:")
    for i, module in enumerate(self.lap_analysis_windows):
        print(f"  [{i}] 類型: {type(module).__name__}")
        print(f"  [{i}] 模組: {module}")
        print(f"  [{i}] 有 update_lap_parameters: {hasattr(module, 'update_lap_parameters')}")
```

### 測試 2: 檢查 Acceleration 模組屬性

在 `update_lap_parameters()` 開始時添加日誌：

```python
def update_lap_parameters(self, ...):
    print(f"[DEBUG] 當前屬性值:")
    print(f"  self.current_year = {getattr(self, 'current_year', 'NOT_SET')}")
    print(f"  self.lap1 = {getattr(self, 'lap1', 'NOT_SET')} (type: {type(getattr(self, 'lap1', None))})")
    print(f"  self.lap2 = {getattr(self, 'lap2', 'NOT_SET')} (type: {type(getattr(self, 'lap2', None))})")
    print(f"  self.data_manager = {getattr(self, 'data_manager', 'NOT_SET')}")
```

### 測試 3: 檢查參數變化邏輯

```python
params_changed = (
    self.current_year != str(year) or 
    self.lap1 != lap1 or
    self.lap2 != lap2
)

print(f"[DEBUG] 參數變化檢測:")
print(f"  年份變化: {self.current_year} != {str(year)} = {self.current_year != str(year)}")
print(f"  Lap1變化: {self.lap1} != {lap1} = {self.lap1 != lap1}")
print(f"  Lap2變化: {self.lap2} != {lap2} = {self.lap2 != lap2}")
print(f"  最終結果: {params_changed}")
```

---

## 💡 可能的修復方案

### 方案 A: 確保屬性正確初始化

在 `accelerationAnalysisModule.__init__()` 中：

```python
def __init__(self, parent=None):
    super().__init__(parent)
    
    # 確保所有必要屬性都被初始化
    self.current_year = None
    self.current_race = None
    self.current_session = None
    self.driver1 = None
    self.driver2 = None
    self.lap1 = None  # ← 確保初始化為 None 而不是未定義
    self.lap2 = None  # ← 確保初始化為 None 而不是未定義
    self.data_manager = None
```

### 方案 B: 改進參數變化檢測

使用更安全的比較邏輯：

```python
# 檢查參數是否有變化
old_lap1 = getattr(self, 'lap1', None)
old_lap2 = getattr(self, 'lap2', None)

params_changed = (
    str(getattr(self, 'current_year', '')) != str(year) or 
    getattr(self, 'current_race', '') != race or 
    getattr(self, 'current_session', '') != session or
    getattr(self, 'driver1', '') != driver1 or
    getattr(self, 'driver2', '') != driver2 or
    old_lap1 != lap1 or
    old_lap2 != lap2
)

print(f"[acceleration_MDI] 📊 參數變化詳情:")
print(f"  Lap1: {old_lap1} → {lap1} (changed: {old_lap1 != lap1})")
print(f"  Lap2: {old_lap2} → {lap2} (changed: {old_lap2 != lap2})")
```

### 方案 C: 強制更新模式

添加 `force_update` 參數：

```python
def update_lap_parameters(self, year: str, race: str, session: str, 
                        driver1: str, driver2: str = None, 
                        lap1: int = 1, lap2: int = 2, 
                        is_fastest: bool = False,
                        force_update: bool = False) -> bool:  # ← 新增參數
    
    # ... 檢查參數變化 ...
    
    if params_changed or force_update:  # ← 允許強制更新
        print(f"[acceleration_MDI] 🔄 開始重載數據（強制: {force_update}）...")
```

在 toolbar 變更時使用：

```python
# f1t_gui_main.py
success = analysis_module.update_lap_parameters(
    year=year,
    race=race, 
    session=session,
    driver1=driver1,
    driver2=driver2,
    lap1=lap1,
    lap2=lap2,
    is_fastest=is_fastest,
    force_update=True  # ← 工具欄變更時強制更新
)
```

---

## 🔬 建議的診斷步驟

### 步驟 1: 添加詳細日誌

在 `update_lap_parameters()` 開始時添加：

```python
print(f"[ACCEL_DEBUG] ========== update_lap_parameters 被調用 ==========")
print(f"[ACCEL_DEBUG] 傳入參數: lap1={lap1} (type: {type(lap1)}), lap2={lap2} (type: {type(lap2)})")
print(f"[ACCEL_DEBUG] 當前值: self.lap1={getattr(self, 'lap1', 'UNDEFINED')}, self.lap2={getattr(self, 'lap2', 'UNDEFINED')}")
print(f"[ACCEL_DEBUG] data_manager 存在: {hasattr(self, 'data_manager') and self.data_manager is not None}")
```

### 步驟 2: 測試參數更新

1. 啟動 GUI
2. 開啟 Acceleration Analysis 視窗
3. 在 toolbar 改變 lap1 從 1 → 52
4. 檢查控制台輸出：
   - 是否有 `[acceleration_MDI] ========== 圈速參數更新 ==========`
   - `params_changed` 的值
   - 是否有 `[acceleration_MDI] 🔄 參數已變化，開始重載數據...`

### 步驟 3: 檢查數據載入

如果看到 "參數已變化"，但沒有數據更新：

```python
print(f"[ACCEL_DEBUG] self.data_manager = {self.data_manager}")
print(f"[ACCEL_DEBUG] 調用 load_acceleration_data...")
success = self.data_manager.load_acceleration_data(...)
print(f"[ACCEL_DEBUG] load_acceleration_data 返回: {success}")
```

---

## 📊 與其他模組對比

### Speed Analysis (正常工作)

```python
# speed_analysis_mdi.py
class SpeedAnalysisModule(IAnalysisModule):  # ← 大寫開頭
    def update_lap_parameters(self, ...):
        # 相同的邏輯
```

### RPM Analysis (正常工作)

```python
# rpm_analysis_mdi.py
class RPMAnalysisModule(IAnalysisModule):  # ← 大寫開頭
    def update_lap_parameters(self, ...):
        # 相同的邏輯
```

### Acceleration Analysis (問題模組)

```python
# acceleration_analysis_mdi.py
class accelerationAnalysisModule(IAnalysisModule):  # ← 小寫開頭！
    def update_lap_parameters(self, ...):
        # 相同的邏輯
```

**發現**: Acceleration 使用小寫類別名稱，與其他模組不一致

---

## ✅ 建議的立即行動

### 優先級 1: 添加診斷日誌 ⭐⭐⭐

在以下位置添加詳細日誌：
1. `acceleration_analysis_mdi.py` 的 `update_lap_parameters()` 開始
2. 參數變化檢測邏輯
3. `data_manager.load_acceleration_data()` 調用前後

### 優先級 2: 測試並收集數據 ⭐⭐

1. 啟動 GUI
2. 開啟 Acceleration Analysis
3. 改變 lap 參數
4. 收集控制台輸出

### 優先級 3: 根據測試結果修復 ⭐

根據測試結果選擇：
- 方案 A: 屬性初始化問題
- 方案 B: 參數比較問題
- 方案 C: 強制更新模式

---

## 🎯 結論

**診斷狀態**: 已完成初步診斷，發現 3 個潛在問題點

**下一步**: 需要添加診斷日誌並進行實際測試，以確定確切的失敗點

**預計修復時間**: 
- 診斷: 10 分鐘
- 修復: 15 分鐘
- 測試: 10 分鐘
- **總計**: 35 分鐘

**風險評估**: 低（修復邏輯簡單，不影響其他模組）

---

**報告生成時間**: 2025-10-04  
**診斷狀態**: 🔍 待用戶測試確認
