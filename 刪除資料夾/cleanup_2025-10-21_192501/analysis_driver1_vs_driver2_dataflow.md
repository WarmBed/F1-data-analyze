# Driver 1 vs Driver 2 數據流深度對比分析

## 🔍 完整數據流追蹤（逐行對比）

### Driver 1 數據載入流程

#### 階段 1: 創建 data_manager (create_data_manager)

**檔案**: `throttle_line_chart_mdi.py` L581-590

```python
def create_data_manager(self) -> ThrottleLineChartDataLoader:
    # 1️⃣ 創建 loader
    loader = ThrottleLineChartDataLoader(self)
    
    # 2️⃣ ❌ 問題：使用 self._global_filter_settings（可能是舊值）
    loader.update_filter_settings(
        filter_pit_laps=self._global_filter_settings.get("filter_pit_laps", True),
        filter_yellow_flags=self._global_filter_settings.get("filter_yellow_flags", True),
        filter_red_flags=self._global_filter_settings.get("filter_red_flags", True),
        reprocess=False,
    )
    return loader
```

**問題分析**：
- 使用 `self._global_filter_settings.get("filter_pit_laps", True)`
- `self._global_filter_settings` 是在 `__init__()` 中初始化的快取字典
- 如果用戶在創建 MDI 之後才改變設定，這裡讀取的是**舊值**！

#### Driver 1 完整流程：

```
創建流程：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T1: ThrottleLineChartMDI.__init__()
    → self._global_filter_settings = dict(settings_manager.get_boxplot_settings())
    → 假設此時讀取到 {filter_pit_laps: True, filter_yellow_flags: True, filter_red_flags: True}
    
T2: create_data_manager() 被調用（初始化時）
    → loader = ThrottleLineChartDataLoader(self)
    → loader.__init__() 內部：
       → initial_filters = gui_settings_manager.get_boxplot_settings()
       → update_filter_settings(pit=True, yellow=True, red=True, reprocess=False)
       → self._filter_pit_laps = True（✅ 設定正確）
    
    → create_data_manager() 繼續：
       → loader.update_filter_settings(
            filter_pit_laps=self._global_filter_settings.get("filter_pit_laps", True),  # ← 使用快取值
            filter_yellow_flags=self._global_filter_settings.get("filter_yellow_flags", True),
            filter_red_flags=self._global_filter_settings.get("filter_red_flags", True),
            reprocess=False,
         )
       → 由於值相同（都是 True），changed=False，直接返回
    
T3: 用戶改變 System Settings（取消勾選過濾）
    → settings_manager.update_boxplot_settings(pit=False, yellow=False, red=False)
    → _on_global_filter_settings_changed() 被觸發
    → self._global_filter_settings 更新為 {pit: False, yellow: False, red: False}
    → self.data_manager.update_filter_settings(pit=False, yellow=False, red=False, reprocess=True)
    → ✅ Driver 1 的過濾設定被更新並重新處理數據
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Driver 2 數據載入流程

#### 階段 1: 創建 temp_loader (_on_driver2_selection_changed)

**檔案**: `throttle_line_chart_mdi.py` L841-857（修復後）

```python
def _on_driver2_selection_changed(self, driver_code: str) -> None:
    # ...
    
    # 載入第二位車手資料
    if hasattr(self.data_manager, "load_data"):
        # 建立第二個資料載入器實例
        from .throttle_line_chart_data_loader import ThrottleLineChartDataLoader
        
        # ✅ 修復：temp_loader 在 __init__() 中會自動從 settings_manager 讀取最新設定
        temp_loader = ThrottleLineChartDataLoader(self)
        
        # 🔍 DEBUG: 顯示 temp_loader 實際使用的過濾設定（來自 __init__）
        print(f"🔍 [Driver2 Loader Created] Filter settings: pit={temp_loader._filter_pit_laps}, yellow={temp_loader._filter_yellow_flags}, red={temp_loader._filter_red_flags}")
        
        # 載入第二位車手資料
        temp_loader.data_loaded.connect(self._on_driver2_data_loaded)
        temp_loader.load_data(...)
```

#### Driver 2 完整流程：

```
創建流程：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T1: ThrottleLineChartMDI.__init__()
    → self._global_filter_settings = dict(settings_manager.get_boxplot_settings())
    → 假設此時讀取到 {filter_pit_laps: True, filter_yellow_flags: True, filter_red_flags: True}
    
T2: 用戶改變 System Settings（勾選過濾）
    → settings_manager.update_boxplot_settings(pit=True, yellow=True, red=True)
    → _on_global_filter_settings_changed() 被觸發
    → self._global_filter_settings 更新為 {pit: True, yellow: True, red: True}
    
T3: 用戶選擇 Driver 2
    → _on_driver2_selection_changed() 被觸發
    → temp_loader = ThrottleLineChartDataLoader(self)
    
    → temp_loader.__init__() 內部：
       → self._filter_pit_laps = True（預設值）
       → self._filter_yellow_flags = True（預設值）
       → self._filter_red_flags = True（預設值）
       
       → initial_filters = self.settings_manager.get_boxplot_settings()
       → 🔍 此時 initial_filters = {pit: True, yellow: True, red: True}（從 settings_manager 讀取）
       
       → update_filter_settings(
            filter_pit_laps=initial_filters.get("filter_pit_laps", True),  # ← True
            filter_yellow_flags=initial_filters.get("filter_yellow_flags", True),  # ← True
            filter_red_flags=initial_filters.get("filter_red_flags", True),  # ← True
            reprocess=False,
         )
       → 由於值相同（預設值也是 True），changed=False，直接返回
       → ❌ 實際的 self._filter_pit_laps 保持為 True（預設值）
    
    → temp_loader.load_data() 執行
    → _process_data() 被調用
    → _apply_filters() 使用 self._filter_pit_laps = True（應該過濾）
    
    → ✅ 理論上應該會過濾這些圈數...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 關鍵差異發現

### 差異 1: Driver 1 會接收設定變更信號

**Driver 1 (self.data_manager)**:
```python
# 在 ThrottleLineChartDataLoader.__init__() 中
try:
    self.settings_manager.boxplot_settings_changed.connect(
        self._on_global_filter_settings_changed
    )
except Exception as exc:
    self._debug(f"無法連接系統設定信號: {exc}")
```

**結果**: 當用戶改變 System Settings 時，Driver 1 的 data_manager 會：
1. 接收到 `boxplot_settings_changed` 信號
2. 觸發 `_on_global_filter_settings_changed()`
3. 調用 `update_filter_settings(reprocess=True)` 重新處理數據

---

### 差異 2: Driver 2 (temp_loader) 是臨時的，不會接收信號

**Driver 2 (temp_loader)**:
- temp_loader 在 `_on_driver2_selection_changed()` 中被創建
- temp_loader 也會在 `__init__()` 中註冊信號監聽
- **但是**，temp_loader 是在**用戶選擇 Driver 2 時**才創建的
- 如果用戶**先改變設定，再選擇 Driver 2**，temp_loader 會讀取到最新設定
- 如果用戶**先選擇 Driver 2，再改變設定**，temp_loader 已經載入完數據並丟棄了！

---

## ❌ 真正的問題

### 場景重現：

```
用戶操作順序：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 開啟 Throttle Line Chart
2. 選擇 Driver 1: VER ✅
   → Driver 1 數據載入（使用預設過濾 True）
3. 選擇 Driver 2: NOR ✅
   → temp_loader 創建（使用預設過濾 True）
   → Driver 2 數據載入（過濾 pit/yellow/red）
   → temp_loader 丟棄
4. 用戶開啟 System Settings，勾選過濾選項 ✅
   → settings_manager 更新
   → Driver 1 接收信號，重新處理數據（過濾生效）
   → ❌ Driver 2 已經載入完畢，temp_loader 已經丟棄，不會更新！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**問題**：
- Driver 1 是持久的（self.data_manager），會接收設定變更信號
- Driver 2 是臨時的（temp_loader），載入完數據後就丟棄了，不會接收後續的設定變更！

---

## 🔧 真正的解決方案

### 方案 A: Driver 2 也使用持久化的 loader

**問題**: 需要重構架構，複雜度高

### 方案 B: 當設定變更時，重新載入 Driver 2 數據 ✅

**實現**: 在 `_on_global_filter_settings_changed()` 中，如果 Driver 2 已載入，重新載入其數據

### 方案 C: Driver 2 使用 Driver 1 的 chart_widget 緩存數據 ✅

**實現**: 檢查 `_on_driver2_data_loaded()` 的實現，看是否正確更新了緩存

---

讓我檢查當前的實現...
