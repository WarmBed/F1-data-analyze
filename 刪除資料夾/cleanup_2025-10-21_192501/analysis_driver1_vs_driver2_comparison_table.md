# Driver 1 vs Driver 2 差異對比表（完整版）

## 📊 創建流程對比

| 項目 | Driver 1 (self.data_manager) | Driver 2 (temp_loader) |
|------|------------------------------|------------------------|
| **創建時機** | 初始化時（`create_data_manager()`） | 用戶選擇 Driver 2 時（`_on_driver2_selection_changed()`） |
| **生命週期** | 持久化（與 MDI 同生命週期） | 臨時（載入完數據後丟棄） |
| **過濾設定來源** | `self._global_filter_settings`（快取） | `settings_manager`（直接讀取） |
| **初始化過濾** | `update_filter_settings(reprocess=False)` | `__init__()` 自動載入 |
| **信號連接** | 連接到 `boxplot_settings_changed` | 連接到 `boxplot_settings_changed` |
| **設定變更響應** | ✅ 調用 `update_filter_settings(reprocess=True)` | ❌ temp_loader 已丟棄，無法響應 |

---

## 🔄 設定變更流程對比

| 項目 | Driver 1 | Driver 2（修復前） | Driver 2（修復後）|
|------|----------|-------------------|-------------------|
| **T1: 初始載入** | 使用預設過濾（True） | 使用預設過濾（True） | 使用預設過濾（True） |
| **T2: 用戶改變設定** | 接收信號 → 重新處理 | ❌ temp_loader 已丟棄 | ✅ 觸發重新載入 |
| **T3: 圖表更新** | ✅ 顯示新過濾結果 | ❌ 仍顯示舊數據 | ✅ 顯示新過濾結果 |
| **最終狀態** | ✅ 正確 | ❌ 錯誤（與 Driver 1 不一致） | ✅ 正確 |

---

## 🎯 關鍵差異總結

### Driver 1: 持久化架構

```python
# 創建時（只執行一次）
self.data_manager = self.create_data_manager()

# 設定變更時（可以多次執行）
def _on_global_filter_settings_changed(settings):
    self.data_manager.update_filter_settings(reprocess=True)  # ✅ 可以調用
```

**優勢**：
- ✅ 可以接收設定變更信號
- ✅ 可以重新處理數據
- ✅ 數據保持最新狀態

---

### Driver 2: 臨時載入架構（修復前）

```python
# 創建時（用戶選擇 Driver 2）
def _on_driver2_selection_changed(driver_code):
    temp_loader = ThrottleLineChartDataLoader(self)
    temp_loader.load_data(...)
    # temp_loader 載入完數據後被丟棄

# 設定變更時
def _on_global_filter_settings_changed(settings):
    # ❌ temp_loader 不存在，無法調用 update_filter_settings
    pass
```

**問題**：
- ❌ temp_loader 被丟棄後無法更新
- ❌ Driver 2 的數據停留在舊狀態
- ❌ 與 Driver 1 不一致

---

### Driver 2: 臨時載入架構（修復後）

```python
# 創建時（用戶選擇 Driver 2）
def _on_driver2_selection_changed(driver_code):
    self.driver2 = driver_code  # ✅ 保存 Driver 2 標識
    temp_loader = ThrottleLineChartDataLoader(self)
    temp_loader.load_data(...)

# 設定變更時
def _on_global_filter_settings_changed(settings):
    # ✅ 檢查 Driver 2 是否存在
    if self.driver2:
        # ✅ 重新載入 Driver 2 數據（使用新設定）
        self._on_driver2_selection_changed(self.driver2)
```

**優勢**：
- ✅ 重新載入時會創建新的 temp_loader（使用新設定）
- ✅ Driver 2 的數據與 Driver 1 保持一致
- ✅ 完全複用現有邏輯，無新增複雜度

---

## 🔍 數據過濾檢查點對比

### Driver 1 過濾流程

```
create_data_manager()
    → ThrottleLineChartDataLoader.__init__()
        → initial_filters = settings_manager.get_boxplot_settings()
        → update_filter_settings(pit=True, yellow=True, red=True, reprocess=False)
        → self._filter_pit_laps = True ✅
    
    → update_filter_settings(pit=self._global_filter_settings["pit"], ...)
        → 再次確認過濾設定（使用快取值）
    
    → load_data(...)
        → _process_data(raw_data)
            → _apply_filters(lap_records)
                → 檢查 self._filter_pit_laps ✅
                → 過濾 Pit Stop 圈數
```

---

### Driver 2 過濾流程（修復前）

```
_on_driver2_selection_changed(driver_code)
    → ThrottleLineChartDataLoader.__init__()
        → initial_filters = settings_manager.get_boxplot_settings()
        → update_filter_settings(pit=True, yellow=True, red=True, reprocess=False)
        → self._filter_pit_laps = True ✅
    
    → load_data(...)
        → _process_data(raw_data)
            → _apply_filters(lap_records)
                → 檢查 self._filter_pit_laps ✅
                → 過濾 Pit Stop 圈數

設定變更後：
    → ❌ temp_loader 已丟棄，無法更新
    → ❌ 圖表仍顯示舊的過濾數據
```

---

### Driver 2 過濾流程（修復後）

```
_on_driver2_selection_changed(driver_code)
    → ThrottleLineChartDataLoader.__init__()
        → initial_filters = settings_manager.get_boxplot_settings()  # ← 讀取最新設定
        → update_filter_settings(pit=False, yellow=False, red=False, reprocess=False)
        → self._filter_pit_laps = False ✅
    
    → load_data(...)
        → _process_data(raw_data)
            → _apply_filters(lap_records)
                → 檢查 self._filter_pit_laps = False ✅
                → 不過濾 Pit Stop 圈數

設定變更後：
    → _on_global_filter_settings_changed() 觸發
    → 檢查 self.driver2 存在 ✅
    → 調用 _on_driver2_selection_changed(self.driver2)
    → 重新載入 Driver 2 數據（使用新設定）✅
```

---

## 📋 測試檢查清單

### 場景 1: Driver 2 載入後改變設定

| 步驟 | Driver 1 預期行為 | Driver 2 修復前 | Driver 2 修復後 |
|------|------------------|----------------|----------------|
| 1. 選擇 VER | 載入數據（預設過濾） | - | - |
| 2. 選擇 NOR | - | 載入數據（預設過濾） | 載入數據（預設過濾） |
| 3. 勾選過濾 | 重新處理（過濾生效） | ❌ 無動作 | ✅ 重新載入（過濾生效） |
| 4. 檢查圖表 | R/Y/P 處無數據點 | ❌ R/Y/P 處有數據點 | ✅ R/Y/P 處無數據點 |

---

### 場景 2: 改變設定後載入 Driver 2

| 步驟 | Driver 1 預期行為 | Driver 2 修復前 | Driver 2 修復後 |
|------|------------------|----------------|----------------|
| 1. 選擇 VER | 載入數據（預設過濾） | - | - |
| 2. 勾選過濾 | 重新處理（過濾生效） | - | - |
| 3. 選擇 NOR | - | ❌ 載入數據（使用舊設定？） | ✅ 載入數據（使用新設定） |
| 4. 檢查圖表 | R/Y/P 處無數據點 | ❌ R/Y/P 處可能有數據點 | ✅ R/Y/P 處無數據點 |

---

## 🎯 修復核心邏輯

### 修復前（有問題）

```python
def _on_global_filter_settings_changed(self, settings):
    # 只更新 Driver 1
    if isinstance(self.data_manager, ThrottleLineChartDataLoader):
        self.data_manager.update_filter_settings(reprocess=True)
    
    # ❌ Driver 2 不會更新
```

### 修復後（正確）

```python
def _on_global_filter_settings_changed(self, settings):
    # 更新 Driver 1
    if isinstance(self.data_manager, ThrottleLineChartDataLoader):
        self.data_manager.update_filter_settings(reprocess=True)
    
    # ✅ 如果 Driver 2 存在，重新載入
    if self.driver2:
        self._on_driver2_selection_changed(self.driver2)
```

---

## 💡 關鍵洞察

### 為何 Driver 1 和 Driver 2 使用不同架構？

**Driver 1 (持久化)**：
- 需要長期存在以響應設定變更
- 使用 `self.data_manager` 保存引用
- 可以調用 `update_filter_settings(reprocess=True)` 重新處理

**Driver 2 (臨時載入)**：
- 只需要載入一次數據
- 使用 `temp_loader` 臨時創建
- 載入完數據後丟棄（減少記憶體佔用）

### 為何修復使用重新載入而非重新處理？

**選項 A: 保存 temp_loader 引用（不推薦）**：
```python
# 需要新增屬性
self.driver2_loader = temp_loader

# 設定變更時
self.driver2_loader.update_filter_settings(reprocess=True)
```
❌ 增加記憶體佔用  
❌ 需要管理 temp_loader 的生命週期  
❌ 增加架構複雜度

**選項 B: 重新載入 Driver 2 數據（推薦）**：
```python
# 只需保存 driver_code
self.driver2 = driver_code

# 設定變更時
self._on_driver2_selection_changed(self.driver2)
```
✅ 記憶體佔用小（只保存字串）  
✅ 完全複用現有邏輯  
✅ 架構簡單清晰

---

**總結**: 修復 V3 使用最簡單且有效的方案，完全解決 Driver 2 過濾不一致的問題
