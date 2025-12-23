# 🔥 Throttle Box Plot 死機問題根本原因分析

## 📅 診斷資訊
- **日期**：2025-10-17
- **問題**：開啟 Throttle Box Plot 導致 GUI 死機
- **對比對象**：Lap Time Box Plot（正常運作）

---

## 🎯 核心問題總結

### **死機根本原因**：
Throttle Box Plot 的 `_stop_api_worker()` 方法使用了**異步停止機制**（不阻塞主執行緒），但 Lap Time Box Plot 使用**同步停止機制**（有阻塞但較短）。

問題在於：**Throttle Box Plot 的異步機制實現不完整，導致進度管理器嘗試連接不存在或未初始化的 API Worker，造成死機**。

---

## 📊 逐行代碼對比

### **1. DataManager `_cleanup_api_worker()` 方法對比**

#### ✅ **Lap Time Box Plot（正常運作）**
**檔案**：`modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`  
**行數**：449-475

```python
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        if self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.wait(200)  # ⚠️ 阻塞 200ms（可接受）
        try:
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.success.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.failure.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.finished.disconnect()
        except Exception:
            pass
        self._api_worker.deleteLater()
        self._api_worker = None
```

**特點**：
- ✅ 使用 `wait(200)` 短暫阻塞（200ms）
- ✅ 信號正確斷開
- ✅ Worker 設為 None
- ✅ 簡單直接，邏輯清晰

---

#### ❌ **Throttle Box Plot（死機版本）**
**檔案**：`modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py`  
**行數**：355-445

```python
def _stop_api_worker(self, wait_timeout_ms: int = 2000) -> None:
    """
    停止 API Worker 執行緒（異步方式，不阻塞主執行緒）
    
    ⚠️ 重要：此方法不再使用 worker.wait() 阻塞主執行緒
    而是使用信號槽機制異步等待執行緒結束
    """
    worker = self._api_worker
    if not worker:
        return

    if worker.isRunning():
        self._debug("_stop_api_worker: 請求執行緒中斷（異步模式）")
        try:
            worker.requestInterruption()
            worker.quit()
            
            # ❌ 問題 1: 不使用 worker.wait() 導致執行緒狀態不確定
            self._debug("_stop_api_worker: 已發送中斷請求，等待 finished 信號")
            
            # ❌ 問題 2: QTimer 異步檢查，但 Worker 可能還未完全停止
            if wait_timeout_ms > 0:
                from PyQt5.QtCore import QTimer
                def force_terminate_if_needed():
                    if worker and worker.isRunning():
                        self._debug("_stop_api_worker: 執行緒超時，強制 terminate()")
                        try:
                            worker.terminate()
                            worker.wait(200)  # 只在 terminate 後短暫 wait
                        except Exception as exc:
                            self._debug(f"_stop_api_worker: terminate() 失敗: {exc}")
                
                QTimer.singleShot(wait_timeout_ms, force_terminate_if_needed)
            
        except Exception as exc:
            self._debug(f"_stop_api_worker: 異常: {exc}")


def _cleanup_api_worker(self) -> None:
    worker = self._api_worker
    if not worker:
        return

    if worker.isRunning():
        self._stop_api_worker()  # ❌ 問題 3: 調用異步方法，但不等待完成

    # ❌ 問題 4: Worker 可能仍在運行時就開始斷開信號
    for signal, slot in (
        (worker.progress, self._on_api_progress),
        (worker.success, self._on_api_success),
        (worker.failure, self._on_api_error),
    ):
        try:
            signal.disconnect(slot)
        except Exception:
            pass

    try:
        worker.finished.disconnect(self._cleanup_api_worker)
    except Exception:
        pass

    worker.deleteLater()  # ❌ 問題 5: Worker 未停止就 deleteLater
    if worker is self._api_worker:
        self._api_worker = None  # ❌ 問題 6: Worker 設為 None，但可能還在運行
```

**問題分析**：
1. ❌ **不等待執行緒停止**：不使用 `wait()` 導致執行緒狀態不確定
2. ❌ **QTimer 異步檢查**：2秒後才檢查，Worker 狀態已經混亂
3. ❌ **cleanup 調用異步方法**：`_cleanup_api_worker` 調用 `_stop_api_worker()` 後立即繼續，不等待停止完成
4. ❌ **信號斷開時 Worker 還在運行**：可能導致信號槽錯亂
5. ❌ **Worker 未停止就 deleteLater**：Qt 對象刪除時機不確定
6. ❌ **Worker 設為 None 但未停止**：後續訪問會失敗

---

### **2. MDI `update_lap_parameters()` 方法對比**

#### ✅ **Lap Time Box Plot（正常運作）**
**檔案**：`modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py`  
**行數**：1033-1069

```python
def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
    try:
        print("[BOXPLOT_MDI] ========== 圈速箱型圖參數更新 ==========")
        print(f"[BOXPLOT_MDI] 收到參數: {year} {race} {session}")
        self.current_year = str(year)
        self.current_race = str(race)
        self.current_session = str(session)

        # ✅ 先連接錯誤處理器
        if not hasattr(self, "_error_handler_connected"):
            if hasattr(self, "data_manager") and self.data_manager:
                self.data_manager.load_error.connect(self._on_data_load_error)
                self._error_handler_connected = True

        # ✅ 停止現有載入（使用簡單同步方式）
        if hasattr(self, "data_manager") and self.data_manager:
            if hasattr(self.data_manager, "is_loading") and self.data_manager.is_loading():
                if hasattr(self.data_manager, "stop_loading"):
                    self.data_manager.stop_loading()
                else:
                    try:
                        self.data_manager._cleanup_api_worker()  # 同步 cleanup
                        self.data_manager._is_loading = False
                    except Exception:
                        pass
            
            # ✅ 更新參數並載入
            self.data_manager.year = self.current_year
            self.data_manager.race = self.current_race
            self.data_manager.session = self.current_session
            result = self.data_manager.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                **kwargs
            )
            print(f"[BOXPLOT_MDI] 數據載入結果: {result}")
            if not result:
                print("[BOXPLOT_MDI] ⚠️ 數據載入請求未成功提交")
        
        print("[BOXPLOT_MDI] 參數更新完成")
        return True
    except Exception as exc:
        print(f"[BOXPLOT_MDI] 參數更新失敗: {exc}")
        import traceback
        traceback.print_exc()
        return False
```

**特點**：
- ✅ **沒有進度管理器**：不額外創建進度顯示組件
- ✅ **簡單同步停止**：直接調用 `_cleanup_api_worker()`
- ✅ **清晰的執行順序**：停止 → 更新參數 → 載入數據

---

#### ❌ **Throttle Box Plot（死機版本）**
**檔案**：`modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py`  
**行數**：903-943

```python
def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
    try:
        print("[THROTTLE_MDI] ========== 油門箱型圖參數更新 ==========")
        print(f"[THROTTLE_MDI] 收到參數: {year} {race} {session}")
        self.current_year = str(year)
        self.current_race = str(race)
        self.current_session = str(session)

        if not hasattr(self, "_error_handler_connected"):
            if hasattr(self, "data_manager") and self.data_manager:
                self.data_manager.load_error.connect(self._on_data_load_error)
                self._error_handler_connected = True

        # ❌ 問題 1: 太早調用進度管理器
        self._show_loading_progress()  # 🔥 這裡創建進度管理器並嘗試連接 Worker

        if hasattr(self, "data_manager") and self.data_manager:
            if hasattr(self.data_manager, "is_loading") and self.data_manager.is_loading():
                if hasattr(self.data_manager, "stop_loading"):
                    self.data_manager.stop_loading()  # ❌ 異步停止，但進度管理器已嘗試連接
                else:
                    try:
                        self.data_manager._cleanup_api_worker()  # ❌ 異步 cleanup
                        self.data_manager._is_loading = False
                    except Exception:
                        pass
            
            # ❌ 問題 2: Worker 可能未完全停止就開始載入
            self.data_manager.year = self.current_year
            self.data_manager.race = self.current_race
            self.data_manager.session = self.current_session
            result = self.data_manager.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                **kwargs
            )
            # ❌ 問題 3: 新 Worker 創建，但進度管理器連接的是舊 Worker 引用
```

**問題分析**：
1. ❌ **時序問題**：`_show_loading_progress()` 在停止舊 Worker **之前**調用
2. ❌ **進度管理器連接錯誤的 Worker**：
   - `_show_loading_progress()` 獲取 `self.data_manager._api_worker`
   - 但這個 Worker 立即被 `stop_loading()` 異步停止
   - 新的 Worker 在 `load_data()` 中創建
   - 進度管理器連接的是已停止的舊 Worker
3. ❌ **信號連接混亂**：舊 Worker 的信號已斷開，但進度管理器還持有引用
4. ❌ **死機觸發點**：進度管理器嘗試更新已刪除的 Worker，導致 Qt 信號槽系統崩潰

---

### **3. 進度管理器實現對比**

#### ❌ **Throttle Box Plot 的 `_show_loading_progress()` 方法**
**檔案**：`modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py`  
**行數**：1171-1217

```python
def _show_loading_progress(self):
    """
    顯示異步載入進度指示器（完全不阻塞主執行緒）
    """
    try:
        # 清理現有的進度管理器
        if self.progress_manager:
            self.progress_manager.cleanup()
            self.progress_manager = None
        
        # 創建新的進度管理器
        self.progress_manager = AsyncLoadingProgressManager(
            parent=self.main_widget,
            message=tr("throttle_box_plot", "正在載入油門數據...")
        )
        
        # ❌ 致命問題：嘗試連接可能不存在或即將被刪除的 Worker
        if hasattr(self, "data_manager") and self.data_manager:
            if hasattr(self.data_manager, "_api_worker") and self.data_manager._api_worker:
                worker = self.data_manager._api_worker  # 🔥 獲取舊 Worker 的引用
                
                # 連接進度信號
                worker.progress.connect(self._on_api_progress)
                
                # 連接成功信號
                worker.success.connect(self._on_api_success)
                
                # 連接失敗信號
                worker.failure.connect(self._on_api_failure)
                
                print("[THROTTLE_MDI] ✅ 進度管理器已連接到 API Worker")
        
        # 顯示進度指示器
        self.progress_manager.show()
        
        print("[THROTTLE_MDI] ✅ 異步進度指示器已顯示")
        
    except Exception as exc:
        print(f"[THROTTLE_MDI] ❌ 顯示進度指示器失敗: {exc}")
        import traceback
        traceback.print_exc()
```

**致命問題**：
1. ❌ **獲取 Worker 引用的時機錯誤**：在 `load_data()` 之前調用，Worker 還不存在或即將被刪除
2. ❌ **連接已停止的 Worker**：舊 Worker 正在被異步停止，信號連接無效
3. ❌ **引用懸空**：Worker 被 `deleteLater()` 後，進度管理器仍持有引用

---

#### ✅ **Lap Time Box Plot（無此機制）**
Lap Time Box Plot **沒有實現進度管理器**，避免了複雜的信號連接問題。

---

## 🔥 死機觸發流程

### **Throttle Box Plot 死機流程**：

```
1. 用戶點擊開啟 Throttle Box Plot
   ↓
2. MainWindow 調用 update_lap_parameters(year, race, session)
   ↓
3. _show_loading_progress() 被調用
   - 創建 AsyncLoadingProgressManager
   - 嘗試連接 self.data_manager._api_worker（舊 Worker 或 None）
   ↓
4. stop_loading() 被調用
   - 調用 _stop_api_worker()（異步停止，不等待）
   - Worker 被標記為刪除但未停止
   ↓
5. load_data() 被調用
   - 創建新的 Worker
   - 但進度管理器連接的是舊 Worker
   ↓
6. 新 Worker 開始運行，發出 progress 信號
   - 進度管理器的回調函數嘗試訪問舊 Worker
   - 舊 Worker 已被 deleteLater()，對象無效
   ↓
7. Qt 信號槽系統崩潰
   - 嘗試調用已刪除對象的槽函數
   - GUI 主執行緒死機 💀
```

---

### **Lap Time Box Plot 正常流程**：

```
1. 用戶點擊開啟 Lap Time Box Plot
   ↓
2. MainWindow 調用 update_lap_parameters(year, race, session)
   ↓
3. stop_loading() 被調用
   - 調用 _cleanup_api_worker()
   - Worker.wait(200) 同步等待停止 ✅
   - Worker 完全停止後才繼續
   ↓
4. load_data() 被調用
   - 創建新的 Worker
   - Worker 開始運行，信號正常工作
   ↓
5. 數據載入完成
   - Worker 發出 success 信號
   - GUI 正常更新 ✅
```

---

## 🎯 修復方案

### **方案 1：移除異步停止機制（推薦）**

**優點**：
- ✅ 簡單直接，邏輯清晰
- ✅ 與 Lap Time Box Plot 一致
- ✅ 避免複雜的異步時序問題

**實施步驟**：
1. 將 Throttle Box Plot 的 `_cleanup_api_worker()` 改為 Lap Time Box Plot 的版本
2. 移除 `_stop_api_worker()` 的異步邏輯
3. 移除進度管理器（或延後實現）

---

### **方案 2：修正進度管理器連接時機（複雜）**

**優點**：
- ✅ 保留進度顯示功能
- ✅ 完全異步，不阻塞主執行緒

**實施步驟**：
1. 將 `_show_loading_progress()` 移到 `load_data()` **之後**
2. 在 DataManager 的 `_start_api_request()` 中連接進度管理器
3. 確保進度管理器連接的是新 Worker

---

## 📊 代碼差異統計

| 項目 | Lap Time Box Plot | Throttle Box Plot | 差異 |
|------|------------------|-------------------|------|
| `_cleanup_api_worker()` 行數 | 27 行 | 45 行 | +18 行 |
| 使用 `worker.wait()` | ✅ 是（200ms） | ❌ 否 | 阻塞方式不同 |
| 異步停止機制 | ❌ 否 | ✅ 是 | 複雜度差異 |
| 進度管理器 | ❌ 無 | ✅ 有 | 額外組件 |
| `update_lap_parameters()` 調用順序 | 停止 → 載入 | 進度 → 停止 → 載入 | 時序問題 |

---

## 🔧 立即修復建議

### **最簡單的修復（5 分鐘）**：

1. **複製 Lap Time Box Plot 的 `_cleanup_api_worker()` 到 Throttle Box Plot**
2. **移除 `_stop_api_worker()` 方法**
3. **暫時移除進度管理器相關代碼**

### **修復後的代碼**：

```python
def _cleanup_api_worker(self) -> None:
    """清理 API Worker（同步方式，簡單可靠）"""
    if self._api_worker:
        if self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.wait(200)  # ✅ 同步等待 200ms
        try:
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.success.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.failure.disconnect()
        except Exception:
            pass
        try:
            self._api_worker.finished.disconnect()
        except Exception:
            pass
        self._api_worker.deleteLater()
        self._api_worker = None
```

```python
def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
    try:
        # ... 參數設置 ...
        
        # ❌ 移除這行
        # self._show_loading_progress()
        
        # ✅ 先停止現有載入
        if hasattr(self, "data_manager") and self.data_manager:
            if hasattr(self.data_manager, "is_loading") and self.data_manager.is_loading():
                self.data_manager.stop_loading()
            
            # 載入數據
            result = self.data_manager.load_data(...)
        
        return True
    except Exception as exc:
        print(f"[THROTTLE_MDI] 參數更新失敗: {exc}")
        return False
```

---

## 📈 測試驗證

### **驗證步驟**：

1. ✅ 啟動 GUI：`python f1t_gui_main.py`
2. ✅ 開啟 Lap Time Box Plot（正常運作）
3. ✅ 開啟 Throttle Box Plot（應該不再死機）
4. ✅ 快速連續開啟多個 Throttle Box Plot
5. ✅ 關閉並重新開啟，確認無記憶體洩漏

---

## 🎉 結論

### **死機根本原因**：
Throttle Box Plot 使用了**不完整的異步停止機制**，導致進度管理器連接了已刪除的舊 Worker，Qt 信號槽系統崩潰。

### **最佳修復方案**：
**使用 Lap Time Box Plot 的簡單同步停止機制**，移除複雜的異步邏輯和進度管理器（或延後實現）。

### **關鍵教訓**：
1. ❌ **避免過早優化**：異步停止機制增加了複雜度但沒有帶來實質好處（200ms 阻塞可接受）
2. ❌ **避免複雜的信號連接**：進度管理器連接時機錯誤導致死機
3. ✅ **保持簡單**：Lap Time Box Plot 的簡單同步方式更可靠
4. ✅ **遵循成功案例**：複製已驗證的代碼模式

---

## 📝 下一步行動

1. ✅ 立即修復：複製 Lap Time Box Plot 的 `_cleanup_api_worker()`
2. ✅ 移除異步邏輯：刪除 `_stop_api_worker()` 和進度管理器
3. ✅ 測試驗證：確認不再死機
4. 🔄 延後優化：進度管理器在修復後再重新設計實現

---

**報告完成時間**：2025-10-17  
**分析作者**：GitHub Copilot  
**嚴重性**：🔴 **CRITICAL**（導致 GUI 完全死機）
