# 速度分析模組記憶體洩漏深度分析

**分析日期**: 2025-10-15  
**Objgraph 報告**: `objgraph_report_20251015_180153.txt`  
**問題**: 關閉 Lap Analysis 模組後，對象未被清理

---

## 🔍 Objgraph 報告關鍵發現

### 關閉前 vs 關閉後對比

**打開 9 個模組後** (行 1833-1843):
```
102. ↑ SpeedAnalysisModule                             1 (+1)
103. ↑ SpeedDataManager                                1 (+1)
104. ↑ SpeedAnalysisChartWidget                        1 (+1)
105. ↑ SpeedChartWidget                                1 (+1)
107. ↑ SpeedAnalysisDataLoader                         1 (+1)
```

**關閉所有模組後** (行 3340+):
```
[ACTION] close all lap analysis module (物件總數: 115564, 變化: +32)

⚠️ 關鍵問題: 
- 物件總數應該減少（回到 112K），但實際只從 116K 降到 115K
- 減少幅度太小 (~1400 objects)，應該減少 ~3600 objects
- 9 個模組的對象仍然殘留在記憶體中
```

### 殘留對象統計（關閉後仍存在）

根據報告，關閉後仍有：
- **SpeedAnalysisModule**: 1 個 ❌
- **SpeedDataManager**: 1 個 ❌
- **SpeedAnalysisChartWidget**: 1 個 ❌
- **SpeedChartWidget**: 1 個 ❌
- **SpeedAnalysisDataLoader**: 1 個 ❌

**結論**: 5 個核心對象都沒有被垃圾回收！

---

## 🏗️ 速度模組架構分析

### 模組組件層次結構

```
SpeedAnalysisModule (MDI 主模組)
├── 1. SpeedDataManager (數據管理器)
│   └── SpeedAnalysisDataLoader (數據載入器)
│       └── TelemetryApiWorker (QThread, 已有 cleanup)
│
├── 2. SpeedAnalysisChartWidget (圖表容器)
│   └── SpeedChartWidget (實際圖表)
│       ├── Matplotlib Figure
│       ├── QTableWidget (統計表)
│       └── 各種 UI 組件
│
└── 3. main_widget (主 UI 容器)
    ├── QVBoxLayout
    └── 各種控制組件
```

### 引用關係圖

```
SpeedAnalysisModule
    ├─[持有]→ data_manager (SpeedDataManager)
    │           ├─[持有]→ _speed_loader (SpeedAnalysisDataLoader)
    │           │           └─[持有]→ _api_worker (TelemetryApiWorker)
    │           │
    │           ├─[信號連接]→ data_loaded
    │           ├─[信號連接]→ error_occurred
    │           └─[信號連接]→ loading_progress
    │
    ├─[持有]→ speed_chart_widget (SpeedAnalysisChartWidget)
    │           ├─[持有]→ chart_widget (SpeedChartWidget)
    │           │           ├─[持有]→ figure (Matplotlib)
    │           │           └─[持有]→ stats_table (QTableWidget)
    │           │
    │           └─[註冊於]→ linkage_manager (全局單例)
    │
    └─[持有]→ main_widget (QWidget)
```

---

## 🎯 您的問題：關閉模組時是一起關閉還是各自關閉？

### 答案：**理論上應該各自清理，但實際上存在循環引用導致無法清理**

### 當前清理順序（理論流程）

#### 步驟 1: 用戶點擊關閉按鈕
```python
# 主 GUI 調用
module.cleanup()
```

#### 步驟 2: SpeedAnalysisModule.cleanup() 執行
```python
def cleanup(self):
    # 2.1 從分析模組管理器解除註冊
    if self._analysis_manager:
        self._analysis_manager.unregister_module(self._module_id)
    
    # 2.2 清理 DataManager
    if self.data_manager:
        self.data_manager.cleanup()  # → 進入步驟 3
    
    # 2.3 清理圖表組件
    if self.speed_chart_widget:
        linkage_manager.unregister_module(self.speed_chart_widget)
        self.speed_chart_widget.cleanup()  # → 進入步驟 4
        self.speed_chart_widget.deleteLater()
    
    # 2.4 清理主 UI
    if self.main_widget:
        self.main_widget.deleteLater()
```

#### 步驟 3: SpeedDataManager.cleanup() 執行
```python
def cleanup(self):
    # 3.1 清理 Loader
    if self._speed_loader:
        self._speed_loader.cleanup()  # → 清理 API Worker (QThread)
        
        # 3.2 斷開信號
        self._speed_loader.data_loaded.disconnect()
        self._speed_loader.load_error.disconnect()
        
        # 3.3 標記刪除
        self._speed_loader.deleteLater()
        self._speed_loader = None
```

#### 步驟 4: SpeedChartWidget.cleanup() 執行
```python
def cleanup(self):
    # 4.1 清理 Matplotlib
    if self.chart_widget.figure:
        self.chart_widget.figure.clear()
        plt.close(self.chart_widget.figure)
    
    # 4.2 清理 QTableWidget
    for row in range(self.stats_table.rowCount()):
        for col in range(self.stats_table.columnCount()):
            item = self.stats_table.takeItem(row, col)
            del item
    
    # 4.3 清理信號接收器
    if self.receiver:
        self.receiver.deleteLater()
```

---

## ❌ 問題根源：為什麼沒有清理成功？

### 問題 1: `deleteLater()` 是異步的

```python
# 當前實現
self.speed_chart_widget.deleteLater()  # ← 僅加入刪除隊列
self.main_widget.deleteLater()         # ← 不是立即刪除

# 問題：cleanup() 返回後，對象仍然存在！
# 需要事件循環處理 deleteLater 隊列
```

**時間線**:
```
T0: cleanup() 被調用
T1: deleteLater() 執行（僅加入隊列）
T2: cleanup() 返回 ← 此時對象仍存在！
T3: 事件循環下一輪 ← 真正刪除
T4: 但如果此時 GUI 已關閉，事件循環已停止 ← 對象永遠不會被刪除
```

---

### 問題 2: 循環引用導致引用計數不為零

#### 引用鏈 1: 信號連接導致的循環引用
```python
# SpeedDataManager 創建時
self._speed_loader.data_loaded.connect(self._on_data_loaded)

# 這創建了:
SpeedDataManager → _speed_loader → Signal → _on_data_loaded (method) → SpeedDataManager
     ↑___________________________________________________________________|
     
引用鏈: A → B → signal → method → A (循環！)
```

#### 引用鏈 2: 全局管理器持有引用
```python
# SpeedAnalysisModule 註冊時
self._analysis_manager.register_module(self)
linkage_manager.register_module(self.speed_chart_widget)

# 這創建了:
SpeedAnalysisModule → speed_chart_widget
                         ↑
                         |
                    linkage_manager (全局單例)
                    
# 即使 SpeedAnalysisModule 被刪除，linkage_manager 仍持有 speed_chart_widget 的引用！
```

#### 引用鏈 3: 父子關係
```python
# Qt 的父子關係
SpeedAnalysisModule (parent)
    ├── main_widget (child) ← QWidget 父子關係
    └── speed_chart_widget (child)

# 問題：即使調用 deleteLater()，如果父對象未被刪除，子對象也不會被刪除
```

---

### 問題 3: 未強制處理事件循環

```python
# 當前實現
def cleanup(self):
    self.speed_chart_widget.deleteLater()
    # 函數直接返回，沒有處理事件循環

# 應該添加:
from PyQt5.QtWidgets import QApplication
QApplication.processEvents()  # ← 強制處理待刪除對象
```

---

### 問題 4: cleanup() 順序問題

**當前順序**:
1. 從管理器解除註冊
2. 清理 DataManager
3. 清理 ChartWidget
4. 清理 MainWidget

**問題**: DataManager 和 ChartWidget 都持有對 Module 的引用（通過信號），但 Module 沒有先斷開這些連接！

**正確順序應該是**:
1. **斷開所有信號連接**
2. 從管理器解除註冊
3. 清理子組件（DataManager, ChartWidget）
4. 清理 MainWidget
5. **強制處理事件循環**
6. **將自身設為 None**

---

## ✅ 完整修復方案

### 修復 1: 改進 cleanup() 順序和完整性

```python
def cleanup(self):
    """清理資源 - 完整版本"""
    try:
        print(f"[SPEED_MDI] 🧹 ========== 開始清理 ==========")
        
        # ========== 階段 1: 斷開所有信號連接 ==========
        print(f"[SPEED_MDI] 階段 1: 斷開信號連接")
        
        # 1.1 斷開 DataManager 的信號
        if hasattr(self, 'data_manager') and self.data_manager:
            try:
                self.data_manager.data_loaded.disconnect()
            except:
                pass
            try:
                self.data_manager.error_occurred.disconnect()
            except:
                pass
        
        # 1.2 斷開 ChartWidget 的信號（如果有）
        if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
            # ... 斷開所有信號
            pass
        
        # ========== 階段 2: 從全局管理器解除註冊 ==========
        print(f"[SPEED_MDI] 階段 2: 解除註冊")
        
        # 2.1 從分析模組管理器解除註冊
        if hasattr(self, '_analysis_manager') and self._analysis_manager:
            self._analysis_manager.unregister_module(self._module_id)
        
        # 2.2 從連動管理器解除註冊
        if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
            from modules.gui.lap_analysis.linkage_manager import linkage_manager
            linkage_manager.unregister_module(self.speed_chart_widget)
        
        # ========== 階段 3: 清理子組件 ==========
        print(f"[SPEED_MDI] 階段 3: 清理子組件")
        
        # 3.1 清理 DataManager（會清理 Loader 和 QThread）
        if hasattr(self, 'data_manager') and self.data_manager:
            self.data_manager.cleanup()
            self.data_manager.deleteLater()
            self.data_manager = None
        
        # 3.2 清理 ChartWidget
        if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
            if hasattr(self.speed_chart_widget, 'cleanup'):
                self.speed_chart_widget.cleanup()
            self.speed_chart_widget.deleteLater()
            self.speed_chart_widget = None
        
        # 3.3 清理 MainWidget
        if hasattr(self, 'main_widget') and self.main_widget:
            self.main_widget.deleteLater()
            self.main_widget = None
        
        # ========== 階段 4: 強制處理事件循環 ==========
        print(f"[SPEED_MDI] 階段 4: 處理事件循環")
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()  # ← 關鍵！強制處理 deleteLater
        
        # ========== 階段 5: 強制垃圾回收 ==========
        print(f"[SPEED_MDI] 階段 5: 強制垃圾回收")
        import gc
        gc.collect()
        
        # ========== 階段 6: 清理內部引用 ==========
        print(f"[SPEED_MDI] 階段 6: 清理內部引用")
        self.current_year = None
        self.current_race = None
        self.current_session = None
        
        print(f"[SPEED_MDI] ✅ ========== 清理完成 ==========")
        
    except Exception as e:
        print(f"[ERROR] [SPEED_MDI] cleanup() 失敗: {e}")
        import traceback
        traceback.print_exc()
```

---

### 修復 2: 主 GUI 確保處理事件循環

```python
# f1t_gui_main.py - 關閉模組後
def close_lap_analysis_module(self, module):
    """關閉 Lap Analysis 模組"""
    try:
        # 調用 cleanup
        module.cleanup()
        
        # 從 MDI 移除
        if module in self.active_subwindows:
            self.active_subwindows.remove(module)
        
        # 關鍵！強制處理事件循環
        self.app.processEvents()
        
        # 再次垃圾回收
        import gc
        gc.collect()
        
    except Exception as e:
        print(f"[ERROR] 關閉模組失敗: {e}")
```

---

### 修復 3: DataManager cleanup 改進

```python
def cleanup(self):
    """清理 SpeedDataManager 資源 - 改進版"""
    try:
        print(f"[DATAMANAGER] 🧹 開始清理...")
        
        # 1. 先斷開信號（避免循環引用）
        try:
            self.data_loaded.disconnect()
        except:
            pass
        try:
            self.error_occurred.disconnect()
        except:
            pass
        
        # 2. 清理 Loader（會清理 QThread）
        if hasattr(self, '_speed_loader') and self._speed_loader:
            if hasattr(self._speed_loader, 'cleanup'):
                self._speed_loader.cleanup()
            
            # 斷開 loader 的信號
            try:
                self._speed_loader.data_loaded.disconnect()
            except:
                pass
            
            self._speed_loader.deleteLater()
            
            # 強制處理事件
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            self._speed_loader = None
        
        # 3. 清理狀態
        self.current_year = None
        self.current_race = None
        self._is_loading = False
        
        print(f"[DATAMANAGER] ✅ 清理完成")
        
    except Exception as e:
        print(f"[ERROR] [DATAMANAGER] cleanup() 失敗: {e}")
```

---

## 📊 修復效果預測

### 修復前（當前狀態）
```
打開 9 個模組:
- 物件總數: 112K → 116K (+3600)

關閉 9 個模組:
- 物件總數: 116K → 115K (-1400) ❌ 只減少 38%
- SpeedAnalysisModule: 1 個殘留
- SpeedDataManager: 1 個殘留
- SpeedChartWidget: 1 個殘留
```

### 修復後（預期）
```
打開 9 個模組:
- 物件總數: 112K → 116K (+3600)

關閉 9 個模組:
- 物件總數: 116K → 112K (-3600) ✅ 完全恢復
- SpeedAnalysisModule: 0 個 ✅
- SpeedDataManager: 0 個 ✅
- SpeedChartWidget: 0 個 ✅
```

---

## 🎯 回答您的問題總結

### 問題：關閉速度模組時，5 個組件是一起關閉還是各自關閉？

**答案**：

1. **理論設計**：各自順序清理
   - Module 先清理 → DataManager 再清理 → Loader 最後清理

2. **實際情況**：都沒有真正被清理（導致洩漏）
   - ❌ `deleteLater()` 是異步的，不會立即清理
   - ❌ 信號連接創建循環引用
   - ❌ 全局管理器持有引用
   - ❌ 沒有強制處理事件循環
   - ❌ 清理順序不對（應該先斷開信號）

3. **正確做法**：
   - ✅ 先斷開所有信號連接（破壞循環引用）
   - ✅ 從全局管理器解除註冊
   - ✅ 按順序清理子組件
   - ✅ 調用 `deleteLater()` 後**強制 `processEvents()`**
   - ✅ 強制垃圾回收
   - ✅ 將所有引用設為 `None`

---

**結論**：5 個組件理論上應該各自清理，但由於實現問題（異步刪除、循環引用、缺少事件處理），實際上都沒有被清理，全部洩漏在記憶體中！
