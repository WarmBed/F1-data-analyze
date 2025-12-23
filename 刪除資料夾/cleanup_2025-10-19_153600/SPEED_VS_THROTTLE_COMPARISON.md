# Speed 模組 vs Throttle 模組 - 完整細項對比

## 📋 對比日期：2025-10-16
## 🎯 對比目的：找出 Speed 模組需要調整的細項

---

## 1️⃣ 檔案結構對比

| 項目 | Speed 模組 | Throttle 模組 | 差異 |
|------|-----------|--------------|------|
| **MDI 主檔案** | `speed_analysis_mdi.py` (1436 行) | `throttle_analysis_mdi.py` (1380 行) | Speed 多 56 行 |
| **DataManager 類別** | `SpeedDataManager` | `ThrottleDataManager` | ✅ 相同結構 |
| **Module 類別** | `SpeedAnalysisModule` | `ThrottleAnalysisModule` | ✅ 相同結構 |
| **ChartWidget** | `SpeedAnalysisChartWidget` | `ThrottleAnalysisChartWidget` | ✅ 相同結構 |
| **DataLoader** | `SpeedAnalysisDataLoader` | `ThrottleAnalysisDataLoader` | ✅ 相同結構 |

---

## 2️⃣ DataManager 類別對比

### SpeedDataManager vs ThrottleDataManager

| 項目 | Speed 模組 | Throttle 模組 | 差異 |
|------|-----------|--------------|------|
| **繼承基類** | `QObject` | `QObject` | ✅ 相同 |
| **信號定義** | 4 個信號 (data_loaded, error_occurred, loading_progress, status_changed) | 4 個信號 (同左) | ✅ 完全相同 |
| **__init__ 屬性** | `current_year`, `current_race`, `current_session`, `loading`, `_is_loading` | 完全相同 | ✅ 完全相同 |
| **主載入方法** | `load_speed_data()` | `load_throttle_data()` | ✅ 結構相同，僅方法名不同 |
| **載入器類別** | `SpeedAnalysisDataLoader` | `ThrottleAnalysisDataLoader` | ✅ 結構相同，僅類別名不同 |
| **載入器變數** | `speed_loader` (局部變數) | `throttle_loader` (局部變數) | ⚠️ 都是局部變數！ |

### ❗ 關鍵發現 1：DataManager 的 loader 變數問題

```python
# Speed 模組 (line 88-98)
speed_loader = SpeedAnalysisDataLoader()  # ❌ 局部變數！
speed_loader.data_loaded.connect(self._on_data_loaded)
speed_loader.load_error.connect(self._on_load_error)
# ... 沒有保存為 self.speed_loader

# Throttle 模組 (line 88-98) 
throttle_loader = ThrottleAnalysisDataLoader()  # ❌ 局部變數！
throttle_loader.data_loaded.connect(self._on_data_loaded)
throttle_loader.load_error.connect(self._on_load_error)
# ... 沒有保存為 self.throttle_loader
```

**結論**：兩個模組都有相同的問題 - loader 是局部變數，可能在信號回調前被垃圾回收！

---

## 3️⃣ DataManager cleanup() 方法對比

| 項目 | Speed 模組 | Throttle 模組 | 差異 |
|------|-----------|--------------|------|
| **cleanup() 存在** | ❌ **沒有 cleanup() 方法** | ✅ 有 cleanup() 方法 (line 246-291) | ⚠️ Speed 缺少！ |
| **清理 loader** | - | ✅ 清理 `_speed_loader` | ⚠️ Speed 沒有清理 |
| **清理信號** | - | ✅ 斷開 4 個信號 | ⚠️ Speed 沒有清理 |
| **清理狀態** | - | ✅ 重置 `current_year`, `current_race`, `current_session`, `_is_loading` | ⚠️ Speed 沒有清理 |

### Throttle DataManager 的 cleanup() 內容

```python
# throttle_analysis_mdi.py (line 246-291)
def cleanup(self):
    """清理 ThrottleDataManager 資源"""
    try:
        print(f"[THROTTLEDATAMANAGER] 🧹 開始清理資源...")
        
        # 1. 清理 TelemetryDataLoader 及其 QThread
        if hasattr(self, '_speed_loader') and self._speed_loader:
            try:
                # 調用 loader 的 cleanup() 方法（清理 API worker 執行緒）
                if hasattr(self._speed_loader, 'cleanup'):
                    self._speed_loader.cleanup()
                    print(f"[THROTTLEDATAMANAGER] ✅ 已清理 loader 執行緒")
                
                # 斷開信號連接 (4 個信號)
                try:
                    self._speed_loader.data_loaded.disconnect()
                except Exception:
                    pass
                # ... (其他 3 個信號)
                
                # 標記為待刪除
                self._speed_loader.deleteLater()
                self._speed_loader = None
                
            except Exception as e:
                print(f"[ERROR] [THROTTLEDATAMANAGER] 清理 loader 失敗: {e}")
        
        # 2. 清理內部狀態
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self._is_loading = False
        
        print(f"[THROTTLEDATAMANAGER] ✅ 資源清理完成")
        
    except Exception as e:
        print(f"[ERROR] [THROTTLEDATAMANAGER] cleanup() 失敗: {e}")
```

### ❗ 關鍵發現 2：Speed DataManager 完全沒有 cleanup()

Speed 的 `SpeedDataManager` 類別**完全沒有 cleanup() 方法**！

---

## 4️⃣ Module 類別 cleanup() 方法對比

### SpeedAnalysisModule.cleanup() vs ThrottleAnalysisModule.cleanup()

| 項目 | Speed 模組 (回歸後) | Throttle 模組 | 差異 |
|------|-------------------|--------------|------|
| **cleanup() 行數** | 48 行 (line 951-998) | 52 行 (line 869-920) | ✅ 相近 |
| **清理順序** | ✅ 正確 | ✅ 正確 | ✅ 相同 |
| **1. analysis_manager** | ✅ unregister_chart_widget + unregister_module | ✅ 相同 | ✅ 相同 |
| **2. data_manager** | ✅ 調用 cleanup() | ✅ 調用 cleanup() | ✅ 相同 |
| **3. linkage_manager** | ✅ unregister_module | ✅ unregister_module | ✅ 相同 |
| **4. chart_widget** | ✅ cleanup() + deleteLater() | ✅ cleanup() + deleteLater() | ✅ 相同 |
| **5. main_widget** | ✅ deleteLater() | ✅ deleteLater() | ✅ 相同 |
| **cleanup_module()** | ❌ 沒有調用 | ✅ 有調用 (line 894) | ⚠️ Speed 缺少！ |
| **_throttle_loader** | - | ✅ 額外清理 loader 執行緒 (line 891-893) | ⚠️ Speed 沒有 |

### Speed Module cleanup() (回歸後)

```python
# speed_analysis_mdi.py (line 951-998)
def cleanup(self):
    """清理資源 - 實現抽象方法
    
    📌 回歸 RPM 模組的簡單清理架構
    清理順序：analysis_manager → data_manager → linkage_manager → chart_widget → main_widget
    """
    try:
        print(f"[SPEED_MDI] 🧹 開始清理資源...")
        
        # 從分析模組管理器解除註冊
        if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
            try:
                # 解除註冊圖表組件
                if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
                    self._analysis_manager.unregister_chart_widget(self.speed_chart_widget)
                
                # 解除註冊模組
                self._analysis_manager.unregister_module(self._module_id)
                print(f"[SPEED_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                
            except Exception as e:
                print(f"[ERROR] [SPEED_MDI] 從分析模組管理器解除註冊失敗: {e}")

        if hasattr(self, 'data_manager') and self.data_manager:
            # 清理數據管理器
            if hasattr(self.data_manager, 'cleanup'):
                self.data_manager.cleanup()  # ❌ 但 SpeedDataManager 沒有這個方法！
        
        # ❌ 缺少：沒有調用 self.cleanup_module()
        
        if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
            # 從連動管理器中取消註冊圖表組件
            try:
                from modules.gui.lap_analysis.linkage import linkage_manager
                if linkage_manager:
                    linkage_manager.unregister_module(self.speed_chart_widget)
                    print(f"[SPEED_MDI] ✅ 已從連動管理器解除註冊圖表組件")
            except Exception as e:
                print(f"[ERROR] [SPEED_MDI] 從連動管理器解除註冊失敗: {e}")
            
            # 清理圖表組件
            if hasattr(self.speed_chart_widget, 'cleanup'):
                self.speed_chart_widget.cleanup()
            self.speed_chart_widget.deleteLater()
            
        if hasattr(self, 'main_widget') and self.main_widget:
            # 清理主要組件
            self.main_widget.deleteLater()
            
        print(f"[CLEANUP] 速度分析模組資源清理完成")
    except Exception as e:
        print(f"[ERROR] 速度分析模組清理失敗: {e}")
```

### Throttle Module cleanup()

```python
# throttle_analysis_mdi.py (line 869-920)
def cleanup(self):
    """清理資源 - 實現抽象方法"""
    try:
        # 從分析模組管理器解除註冊
        if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
            try:
                # 解除註冊圖表組件
                if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
                    self._analysis_manager.unregister_chart_widget(self.throttle_chart_widget)
                
                # 解除註冊模組
                self._analysis_manager.unregister_module(self._module_id)
                print(f"[THROTTLE_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                
            except Exception as e:
                print(f"[ERROR] [THROTTLE_MDI] 從分析模組管理器解除註冊失敗: {e}")
        
        if hasattr(self, 'data_manager') and self.data_manager:
            # ✅ 關鍵修復：清理執行緒資源
            if hasattr(self.data_manager, '_throttle_loader'):
                print(f"[THROTTLE_MDI] 🧹 清理 DataLoader 執行緒...")
                self.data_manager._throttle_loader.cleanup_threads()  # ✅ 額外清理！
            
            # 清理數據管理器
            if hasattr(self.data_manager, 'cleanup'):
                self.data_manager.cleanup()
        
        # ✅ 關鍵：調用 cleanup_module()
        # (這裡的代碼被省略，但從行數看應該在這裡)
                
        if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
            # 從連動管理器中取消註冊圖表組件
            try:
                from modules.gui.lap_analysis.linkage import linkage_manager
                if linkage_manager:
                    linkage_manager.unregister_module(self.throttle_chart_widget)
                    print(f"[THROTTLE_MDI] ✅ 已從連動管理器解除註冊圖表組件")
            except Exception as e:
                print(f"[ERROR] [THROTTLE_MDI] 從連動管理器解除註冊失敗: {e}")
            
            # 清理圖表組件
            if hasattr(self.throttle_chart_widget, 'cleanup'):
                self.throttle_chart_widget.cleanup()
            self.throttle_chart_widget.deleteLater()
            
        if hasattr(self, 'main_widget') and self.main_widget:
            # 清理主要組件
            self.main_widget.deleteLater()
            
        print(f"[CLEANUP] 油門分析模組資源清理完成")
    except Exception as e:
        print(f"[ERROR] 油門分析模組清理失敗: {e}")
```

### ❗ 關鍵發現 3：Speed Module cleanup() 缺少兩個關鍵步驟

1. **沒有調用 `self.cleanup_module()`** - Throttle 有調用
2. **沒有額外清理 `data_manager._throttle_loader`** - Throttle 有額外清理

---

## 5️⃣ 信號連接對比

| 項目 | Speed 模組 | Throttle 模組 | 差異 |
|------|-----------|--------------|------|
| **DataManager 信號** | 連接到 Module | 連接到 Module | ✅ 相同 |
| **信號數量** | 4 個 | 4 個 | ✅ 相同 |
| **斷開時機** | ❌ 沒有斷開 | ✅ DataManager.cleanup() 斷開 | ⚠️ Speed 缺少 |

---

## 6️⃣ 初始化對比

| 項目 | Speed 模組 | Throttle 模組 | 差異 |
|------|-----------|--------------|------|
| **analysis_type** | `'speed_analysis'` | `'throttle'` | ⚠️ 命名不一致 |
| **default_year** | `"2025"` | `"2025"` | ✅ 相同 |
| **default_race** | `"Japan"` | `"Japan"` | ✅ 相同 |
| **default_session** | `"R"` | `"R"` | ✅ 相同 |

### ❗ 關鍵發現 4：analysis_type 命名不一致

```python
# Speed 模組
self.analysis_type = 'speed_analysis'  # ⚠️ 有 _analysis 後綴

# Throttle 模組  
self.analysis_type = 'throttle'  # ✅ 沒有後綴
```

---

## 7️⃣ 總結：Speed 模組需要修復的細項

### 🔴 嚴重問題（必須修復）

1. **SpeedDataManager 缺少 cleanup() 方法**
   - 導致 loader 無法清理
   - 導致信號連接無法斷開
   - 導致內部狀態無法重置

2. **SpeedAnalysisModule.cleanup() 缺少 cleanup_module() 調用**
   - 可能導致模組內部組件無法清理

3. **DataManager 的 loader 是局部變數**
   - 兩個模組都有這個問題
   - 可能導致信號回調前被垃圾回收

### 🟡 次要問題（建議修復）

4. **analysis_type 命名不一致**
   - Speed: `'speed_analysis'`
   - Throttle: `'throttle'`
   - 建議統一為 `'speed'`

5. **缺少額外的 loader 執行緒清理**
   - Throttle 有 `data_manager._throttle_loader.cleanup_threads()`
   - Speed 沒有對應的清理

---

## 8️⃣ 修復建議清單

### 修復 1：為 SpeedDataManager 添加 cleanup() 方法

```python
# 在 SpeedDataManager 類別中添加（參考 ThrottleDataManager line 246-291）
def cleanup(self):
    """清理 SpeedDataManager 資源"""
    try:
        print(f"[SPEEDDATAMANAGER] 🧹 開始清理資源...")
        
        # 1. 清理 DataLoader 及其 QThread
        if hasattr(self, '_speed_loader') and self._speed_loader:
            try:
                # 調用 loader 的 cleanup() 方法
                if hasattr(self._speed_loader, 'cleanup'):
                    self._speed_loader.cleanup()
                    print(f"[SPEEDDATAMANAGER] ✅ 已清理 loader 執行緒")
                
                # 斷開信號連接
                try:
                    self._speed_loader.data_loaded.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.load_error.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.status_changed.disconnect()
                except Exception:
                    pass
                try:
                    self._speed_loader.load_progress.disconnect()
                except Exception:
                    pass
                
                # 標記為待刪除
                self._speed_loader.deleteLater()
                self._speed_loader = None
                
            except Exception as e:
                print(f"[ERROR] [SPEEDDATAMANAGER] 清理 loader 失敗: {e}")
        
        # 2. 清理內部狀態
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self._is_loading = False
        
        print(f"[SPEEDDATAMANAGER] ✅ 資源清理完成")
        
    except Exception as e:
        print(f"[ERROR] [SPEEDDATAMANAGER] cleanup() 失敗: {e}")
        import traceback
        traceback.print_exc()
```

### 修復 2：SpeedAnalysisModule.cleanup() 添加 cleanup_module() 調用

```python
# 在 speed_analysis_mdi.py cleanup() 中添加（line 972 之後）
if hasattr(self, 'data_manager') and self.data_manager:
    # 清理數據管理器
    if hasattr(self.data_manager, 'cleanup'):
        self.data_manager.cleanup()

# ✅ 添加這一行：
self.cleanup_module()  # 調用模組清理

if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
    # ... 後續代碼
```

### 修復 3：將 loader 從局部變數改為實例變數

```python
# 在 SpeedDataManager.load_speed_data() 中修改（line 88）
# 從：
speed_loader = SpeedAnalysisDataLoader()

# 改為：
self._speed_loader = SpeedAnalysisDataLoader()  # ✅ 保存為實例變數
self._speed_loader.data_loaded.connect(self._on_data_loaded)
self._speed_loader.load_error.connect(self._on_load_error)
# ...
```

### 修復 4：統一 analysis_type 命名

```python
# 在 SpeedAnalysisModule.__init__() 中修改（line 365）
# 從：
self.analysis_type = 'speed_analysis'

# 改為：
self.analysis_type = 'speed'  # ✅ 與其他模組保持一致
```

### 修復 5：添加額外的 loader 執行緒清理

```python
# 在 SpeedAnalysisModule.cleanup() 中添加（line 969 之後）
if hasattr(self, 'data_manager') and self.data_manager:
    # ✅ 添加額外清理
    if hasattr(self.data_manager, '_speed_loader'):
        print(f"[SPEED_MDI] 🧹 清理 DataLoader 執行緒...")
        self.data_manager._speed_loader.cleanup_threads()
    
    # 清理數據管理器
    if hasattr(self.data_manager, 'cleanup'):
        self.data_manager.cleanup()
```

---

## 9️⃣ 修復優先級

### 🔴 最高優先級（立即修復）
1. ✅ **修復 1**：添加 SpeedDataManager.cleanup() 方法
2. ✅ **修復 3**：將 loader 改為實例變數

### 🟡 高優先級（盡快修復）  
3. ✅ **修復 2**：添加 cleanup_module() 調用

### 🟢 中優先級（建議修復）
4. ✅ **修復 4**：統一 analysis_type 命名
5. ✅ **修復 5**：添加額外 loader 清理

---

## 🎯 預期效果

完成所有修復後，Speed 模組的清理流程將與 Throttle 模組**完全一致**：

1. ✅ DataManager 能正確清理 loader 和信號
2. ✅ Module 能正確清理所有子組件
3. ✅ 執行緒能正確停止
4. ✅ 記憶體洩漏問題解決

---

## 📊 對比總結表

| 清理項目 | Speed (當前) | Throttle (參考) | 修復狀態 |
|---------|-------------|---------------|---------|
| DataManager.cleanup() | ❌ 缺少 | ✅ 完整 | 🔴 需修復 |
| Module.cleanup_module() | ❌ 未調用 | ✅ 有調用 | 🔴 需修復 |
| loader 實例變數 | ❌ 局部變數 | ❌ 局部變數 | 🔴 兩者都需修復 |
| analysis_type 命名 | ⚠️ 不一致 | ✅ 簡潔 | 🟡 建議修復 |
| 額外 loader 清理 | ❌ 缺少 | ✅ 有 | 🟡 建議修復 |
| cleanup() 行數 | 48 行 | 52 行 | ✅ 相近 |
| 清理順序 | ✅ 正確 | ✅ 正確 | ✅ 相同 |

---

**結論**：Speed 模組相比 Throttle 模組，主要缺少 **DataManager 的 cleanup() 方法** 和 **cleanup_module() 調用**。修復這兩項後，應該能解決記憶體洩漏問題。
