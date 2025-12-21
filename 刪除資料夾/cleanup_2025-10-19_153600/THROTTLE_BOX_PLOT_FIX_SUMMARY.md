# 🔧 Throttle Box Plot 死當問題修復總結

**修復日期**: 2025-10-17  
**問題類型**: GUI 主執行緒死鎖  
**受影響模組**: `modules/gui/Throttle_analysis/throttle_box_plot_analysis/`

---

## **🔍 問題根源分析**

### **1. 死當的直接原因**

Throttle Box Plot 在 `update_lap_parameters()` 中使用 `worker.wait(200)` **同步等待 API Worker 停止**，造成主執行緒阻塞 200ms。當與進度管理器的信號連接錯誤結合時，會導致主執行緒完全死鎖。

### **2. 時序問題**

```
步驟 1: update_lap_parameters() 被調用
步驟 2: [已禁用] _show_loading_progress() 連接到舊 Worker
步驟 3: stop_loading() → _cleanup_api_worker() → worker.wait(200) 🔴 阻塞 200ms
步驟 4: load_data() 創建新 Worker
步驟 5: [Bug] 進度管理器仍持有舊 Worker 的信號連接 → 死鎖
```

### **3. 與其他模組的對比**

| **模組** | **API 使用** | **Worker 清理方式** | **進度管理器** | **死當風險** |
|---------|------------|-------------------|--------------|------------|
| **Throttle Box Plot (修復前)** | ✅ 使用 | `worker.wait(200)` 🔴 同步阻塞 | ✅ 有 (時序錯誤) | 🔴 **高** |
| **Throttle Box Plot (修復後)** | ✅ 使用 | `deleteLater()` ✅ 異步清理 | ❌ 已移除 | ✅ **無** |
| **Accident Analysis** | ✅ 使用 | `deleteLater()` ✅ 異步清理 | ❌ 無 | ✅ **無** |
| **Lap Time Box Plot** | ❌ **不使用** | N/A (無 Worker) | ❌ 無 | ✅ **無** |

---

## **✅ 已實施的修復**

### **修復 1: 移除 wait(200ms) 同步等待**

**檔案**: `throttle_box_plot_analysis_mdi.py` (第 358-390 行)

**修復前**:
```python
def _cleanup_api_worker(self) -> None:
    if self._api_worker:
        if self._api_worker.isRunning():
            self._api_worker.requestInterruption()
            self._api_worker.wait(200)  # 🔴 阻塞主執行緒 200ms
        
        # ... 斷開信號 ...
        
        self._api_worker.deleteLater()
        self._api_worker = None
```

**修復後**:
```python
def _cleanup_api_worker(self) -> None:
    """
    清理 API Worker（完全異步，無阻塞）
    
    ✅ 修復：參考 Accident Analysis 的完全異步機制
    - 使用 requestInterruption() 請求中斷
    - 使用 deleteLater() 異步刪除
    - 移除 wait() 同步等待（避免主執行緒阻塞）
    - 確保無 GUI 卡頓
    """
    if self._api_worker:
        # ✅ 僅請求中斷，不等待（避免 200ms 阻塞）
        if self._api_worker.isRunning():
            self._api_worker.requestInterruption()
        
        # ✅ 斷開所有信號連接
        try:
            self._api_worker.progress.disconnect()
        except Exception:
            pass
        # ... 其他 disconnect ...
        
        # ✅ 使用 deleteLater() 異步刪除（Qt 事件循環處理）
        self._api_worker.deleteLater()
        self._api_worker = None
```

### **修復 2: 移除進度管理器（時序問題）**

**檔案**: `throttle_box_plot_analysis_mdi.py` (第 875-890 行)

**修復前**:
```python
# ⚠️ 暫時禁用進度管理器（避免死機）
# self._show_loading_progress()  # 會連接到舊 Worker
```

**修復後**:
```python
# ✅ 移除進度管理器（時序問題已無法解決）
# 原因：_show_loading_progress() 會在數據載入前連接到即將被清理的舊 Worker
# 造成信號連接錯誤，導致主執行緒死鎖
# 改為依靠 data_manager 的 status_changed 信號提供載入狀態
```

---

## **🎯 技術細節**

### **Qt 異步清理機制**

```python
# ✅ 正確的異步清理流程 (Accident Analysis 模式)

# 步驟 1: 請求中斷（標記執行緒需要停止）
if worker.isRunning():
    worker.requestInterruption()

# 步驟 2: 斷開信號連接（防止懸空指標）
try:
    worker.progress.disconnect()
    worker.success.disconnect()
    worker.failure.disconnect()
    worker.finished.disconnect()
except Exception:
    pass

# 步驟 3: 使用 deleteLater() 異步刪除
worker.deleteLater()  # Qt 事件循環會在安全時機刪除
worker = None

# ✅ 無需 wait()，執行緒會自行檢查中斷標記並停止
# ✅ deleteLater() 確保在事件循環中安全刪除
# ✅ 主執行緒完全不阻塞
```

### **為什麼 wait() 會導致問題？**

1. **阻塞主執行緒**: `wait(200)` 會讓主執行緒停止處理事件 200ms
2. **信號處理延遲**: Qt 信號無法在 wait() 期間正常處理
3. **死鎖風險**: 如果 Worker 在等待某個信號回調，而主執行緒正在 wait()，就會死鎖
4. **進度管理器衝突**: 進度管理器的 QTimer 無法在 wait() 期間觸發

---

## **⚠️ 發現的其他問題**

### **Lap Time Box Plot 完全不使用 API！**

**檔案**: `modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py`

**問題**:
```python
class LapTimeBoxPlotWidget(QWidget):  # ❌ 直接繼承 QWidget，不使用 UniversalDataLoader
    
    def load_data(self, year=None, race=None, session=None):
        # ❌ 只搜尋本地 JSON 檔案
        json_file = self._search_json_file(year, race, session)
        
        if json_file:
            # ❌ 直接讀取本地 JSON (同步)
            self._load_from_json(json_file)
        else:
            # ❌ CLI 調用已禁用，不使用 API
            self._generate_via_cli(year, race, session)  # 返回 False
```

**違反政策**: 完全違反 API-ONLY 政策，需要重構！

---

## **📋 測試檢查清單**

### **必須通過的測試**:

- [x] **Import 測試**: Throttle Box Plot 模組可正常導入
- [x] **MDI 初始化**: 視窗可正常創建並顯示
- [x] **API 請求**: 可正常發送 API 請求並接收數據
- [ ] **參數更新**: 更新 year/race/session 不會死鎖 **（需要實際測試）**
- [ ] **重複載入**: 連續多次載入數據不會死鎖 **（需要實際測試）**
- [ ] **視窗關閉**: 關閉視窗時 Worker 正確清理 **（需要實際測試）**
- [ ] **錯誤處理**: API 失敗時不會死鎖 **（需要實際測試）**

### **性能測試**:

- [ ] 載入數據時 GUI 無明顯卡頓
- [ ] 更新參數時響應時間 < 100ms
- [ ] 無 200ms 阻塞延遲

---

## **🚀 下一步行動**

### **優先級 1: 實際測試 Throttle Box Plot**

```powershell
# 啟動 GUI 並測試 Throttle Box Plot
python f1t_gui_main.py

# 測試步驟:
# 1. 打開 Throttle Box Plot
# 2. 更新參數 (year/race/session)
# 3. 連續更新多次
# 4. 檢查是否死鎖
# 5. 檢查 GUI 是否卡頓
```

### **優先級 2: 修復 Lap Time Box Plot 使用 API**

Lap Time Box Plot 需要完全重構為 API-ONLY 模式：

1. 繼承 `UniversalDataLoader` 而非 `QWidget`
2. 使用 API Worker 異步載入數據
3. 移除本地 JSON 直接讀取邏輯
4. 參考 Throttle Box Plot 的架構

### **優先級 3: 統一所有模組的清理機制**

檢查所有使用 API Worker 的模組，確保都使用完全異步清理：

```bash
# 搜尋所有使用 wait() 的模組
grep -r "\.wait(" modules/gui/
```

---

## **📚 參考架構**

### **推薦參考順序**:

1. **Accident Analysis** (`accident_data_manager.py`) - 最佳的異步清理範例
2. **Throttle Box Plot** (修復後) - 完整的 API-ONLY 實現
3. **Rain Analysis** (`rain_analysis_mdi.py`) - 通用架構標準範本

### **避免參考**:

- ❌ Lap Time Box Plot (不使用 API，架構過時)
- ❌ 任何使用 `worker.wait()` 的舊代碼

---

## **✅ 修復驗證**

**預期結果**:

1. ✅ Throttle Box Plot 打開時無卡頓
2. ✅ 更新參數時無 200ms 延遲
3. ✅ 連續更新不會死鎖
4. ✅ 關閉視窗時 Worker 正確清理
5. ✅ API 失敗時不會死鎖

**如果仍然死鎖**:

1. 檢查日誌中的錯誤訊息
2. 確認 API 服務器正在運行
3. 檢查是否有其他信號連接問題
4. 考慮完全移除進度管理器相關代碼

---

**修復狀態**: ✅ 代碼已更新，等待實際測試驗證

**責任工程師**: GitHub Copilot  
**審核狀態**: 待用戶測試確認
