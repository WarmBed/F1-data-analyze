# Qt.QueuedConnection 問題分析與解決方案

## 問題回顧

### 原始問題
用戶報告：更新 year/race/session 參數時，Lap Analysis 子模組崩潰

### 誤診
我錯誤地認為問題是「在非 UI 線程更新 Qt Widget」，並添加了 `Qt.QueuedConnection` 修復

### 實際後果
1. ✅ Qt.QueuedConnection 本身可以正常傳遞信號（測試已證明）
2. ❌ 但導致 Speed Analysis 等模組無法調用 API
3. ❌ 測試腳本掛起，無法完成數據載入

## 根本原因分析

### Qt.AutoConnection vs Qt.QueuedConnection

**AutoConnection (默認)**:
- 如果發送者和接收者在同一線程 → 直接調用（DirectConnection）
- 如果發送者和接收者在不同線程 → 排隊調用（QueuedConnection）
- ✅ Qt 自動選擇最佳策略

**QueuedConnection (強制排隊)**:
- 信號總是排隊到接收者的事件循環
- ❌ 如果事件循環未正確運行，信號可能永遠不會被處理
- ❌ 可能導致程式掛起或響應延遲

### 為什麼 Speed Analysis 失敗？

```python
# 原始代碼（正常工作）
self._api_worker.success.connect(self._on_api_success)

# 修改後（失敗）
self._api_worker.success.connect(self._on_api_success, Qt.QueuedConnection)
```

**問題**:
1. API Worker 在 QThread 中運行
2. 發射 `success` 信號
3. 使用 AutoConnection 時，Qt 自動處理線程切換
4. 使用 QueuedConnection 時，信號被排隊到接收者的事件循環
5. 如果接收者的事件循環阻塞或未運行 → 信號永遠不會被處理

## 正確的修復方案

### 方案 1: 使用默認的 AutoConnection（推薦）
```python
# 保持原樣，讓 Qt 自動處理
self._api_worker.success.connect(self._on_api_success)
```

**優點**:
- Qt 會根據線程自動選擇最佳連接類型
- 不會破壞現有功能
- 性能最佳

### 方案 2: 確保槽函數在 UI 線程執行
```python
@pyqtSlot(dict)
def _on_api_success(self, result: Dict):
    # 使用 QMetaObject.invokeMethod 確保在 UI 線程執行
    from PyQt5.QtCore import QMetaObject, Qt as QtCore
    
    def update_ui():
        # UI 更新代碼
        self.chart_widget.update_data(data)
    
    QMetaObject.invokeMethod(
        self, 
        update_ui, 
        QtCore.Qt.QueuedConnection
    )
```

**優點**:
- 明確控制 UI 更新在主線程執行
- 不影響信號的正常傳遞

**缺點**:
- 代碼複雜度增加
- 可能不必要（Qt 已經處理了）

### 方案 3: 在槽函數中使用 QTimer.singleShot
```python
@pyqtSlot(dict)
def _on_api_success(self, result: Dict):
    # 延遲到下一個事件循環
    from PyQt5.QtCore import QTimer
    
    QTimer.singleShot(0, lambda: self._update_ui_with_data(result))

def _update_ui_with_data(self, result: Dict):
    # UI 更新代碼
    data = result.get('data', {})
    self.chart_widget.update_data(data)
```

**優點**:
- 確保 UI 更新在主事件循環中執行
- 避免阻塞當前線程

**缺點**:
- 代碼複雜度增加
- 輕微的性能開銷

## 結論

### 撤銷所有 Qt.QueuedConnection 修改
原因:
1. 破壞了 API 調用功能
2. AutoConnection 已經足夠安全
3. Qt 的默認行為是經過良好測試的

### 原始崩潰的真正原因
可能是:
1. **競爭條件**: 20 個視窗同時更新參數時，資源競爭
2. **記憶體洩漏**: QPainter 資源未正確釋放
3. **事件循環阻塞**: 大量同步更新導致事件循環阻塞
4. **Qt Widget 生命週期問題**: Widget 被刪除時仍有待處理的信號

### 下一步建議
1. ✅ 撤銷所有 Qt.QueuedConnection 修改（已完成）
2. 🔍 使用 Qt Creator 的 Profiler 診斷原始崩潰
3. 🔍 添加日誌記錄來追蹤崩潰前的操作序列
4. 🔍 檢查 QPainter 和 QPixmap 的使用是否正確
5. 🔍 確認 Widget 的 deleteLater() 調用順序

## 經驗教訓

1. **不要假設問題的根本原因** - 我假設是線程安全問題，但實際可能不是
2. **測試每一個修改** - 應該在修改後立即測試，而不是批量修復
3. **理解 Qt 的默認行為** - AutoConnection 已經很智能，不需要手動覆蓋
4. **小心使用 QueuedConnection** - 只在明確需要時使用，並確保事件循環正常運行
