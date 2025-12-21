# 記憶體洩漏修復進度總結

## 🎯 核心問題

**TypeError on GUI shutdown**: `'NoneType' object does not support the context manager protocol`

**根本原因**: 9 個 Lap Analysis 模組的 QThread 未正確清理，導致 DummyThread 殘留

---

## 📈 修復歷程

### v1: 基礎 Cleanup 增強
**實現**:
- ✅ 添加 `processEvents()` 等待異步刪除
- ✅ 添加 `gc.collect()` 強制垃圾回收
- ✅ 添加 CRITICAL 日誌追蹤

**測試結果**:
- ✅ cleanup() 被調用
- ❌ objgraph 顯示物件仍然洩漏
- ❌ 沒有診斷信息確認原因

**結論**: Cleanup 執行了，但不起作用

---

### v2: 深度 Cleanup 增強
**實現**:
- ✅ 10 輪 `processEvents()` (每輪 20ms)
- ✅ 引用計數診斷（`sys.getrefcount()`）
- ✅ 引用來源診斷（`gc.get_referrers()`）
- ✅ GC 回收物件數追蹤

**測試結果**:
- ✅ cleanup() 執行成功（所有步驟完成）
- ✅ 日誌確認：斷開信號 ✅、解除註冊 ✅、deleteLater ✅
- ❌ **GC 回收 0 個物件** ← 關鍵發現！
- ❌ 關閉速度變慢（10 輪 events = 200ms）
- ❌ objgraph 仍顯示洩漏

**日誌證據**:
```
logs/f1_gui_2025-10-15.log:105404
[SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）
```

**結論**: Cleanup 代碼正確，但**物件仍被強引用**，GC 無法回收

---

### v3: 引用持有者追蹤
**實現**:
- ✅ **清理前**追蹤引用狀態
  - SpeedAnalysisModule 本身的引用數
  - speed_chart_widget 的引用數
  - 引用來源分類（dict, QWidget, frame, function）
  
- ✅ **清理後**再次追蹤並對比
  - 引用數是否減少？
  - 哪些類型的引用仍然存在？
  - 識別主要引用持有者

- ✅ GC 回收 0 時顯著警告
  ```python
  if collected == 0:
      print("⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！")
  ```

**目標**:
找出**誰**持有這些強引用：
- `analysis_manager.registered_modules` 字典？
- `linkage_manager.linkages` 字典？
- `QMdiSubWindow` 父視窗？
- 信號連接殘留？

---

## 🔍 當前狀態

### 已確認的事實
1. ✅ cleanup() 方法被正確調用
2. ✅ 所有 cleanup 步驟執行成功
3. ✅ 信號已斷開
4. ✅ 已從管理器解除註冊
5. ✅ deleteLater() 已調用
6. ✅ 多輪 processEvents 已執行
7. ❌ **GC 回收 0 個物件** ← 核心問題
8. ❌ objgraph 顯示物件未銷毀

### 問題診斷
**根本原因**: 物件被**強引用**，無法被 GC 回收

**可能的引用持有者**:
- 🔍 全域管理器字典（`analysis_manager`, `linkage_manager`）
- 🔍 MDI 父視窗（`QMdiSubWindow`）
- 🔍 彈出視窗（`PopoutSubWindow`）
- 🔍 信號連接殘留（PyQt 內部）
- 🔍 Qt parent-child 關係

---

## 🧪 下一步測試

### 測試 v3 引用追蹤
1. **啟動 GUI**:
   ```powershell
   python f1t_gui_main.py
   ```

2. **打開 → 關閉速度模組**

3. **檢查 CRITICAL 日誌**:
   ```powershell
   Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "CRITICAL.*🔍" -Context 0,2 | Select-Object -Last 80
   ```

### 期待的診斷信息
```
【清理前】
[CRITICAL] 🔍 SpeedAnalysisModule 本身引用數: X
[CRITICAL] 🔍 模組被引用數量: Y
[CRITICAL] 🔍 模組引用來源分類:
[CRITICAL]     - dict: N 個
[CRITICAL]     - QMdiSubWindow: M 個
[CRITICAL]     - frame: K 個

【清理後】
[CRITICAL] 🔍 SpeedAnalysisModule 清理後引用數: X'
[CRITICAL] 🔍 模組清理後被引用數量: Y'
[CRITICAL] 🔍 清理後引用來源分類:
[CRITICAL]     - dict: N' 個  ← 如果仍 > 0，說明字典未清除
[CRITICAL]     - QMdiSubWindow: M' 個  ← 如果仍 > 0，說明 MDI 未釋放

[SPEED_MDI] ✅ 已執行垃圾回收（回收 K 個物件）
[CRITICAL] ⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！  ← 如果出現
```

---

## 🎯 修復策略

根據 v3 測試結果，選擇對應方案：

### 情況 1: dict 引用殘留
**修復**:
```python
# 強制刪除字典項
if self._module_id in analysis_manager.registered_modules:
    del analysis_manager.registered_modules[self._module_id]
```

### 情況 2: QMdiSubWindow 引用
**修復**:
```python
# 主動移除子視窗
parent = self.parent()
if isinstance(parent, QMdiSubWindow):
    mdi_area = parent.mdiArea()
    mdi_area.removeSubWindow(parent)
```

### 情況 3: 信號連接殘留
**修復**:
```python
# 斷開所有連到 self 的信號
self.data_manager.disconnect(self)
```

---

## 📊 成功指標

修復成功的判斷標準：

1. ✅ `gc.collect()` 回收 > 0 個物件
2. ✅ 清理後引用數顯著減少
3. ✅ objgraph 顯示物件計數 -1
4. ✅ 不再出現 DummyThread TypeError
5. ✅ 關閉速度可接受（< 200ms）

---

## 📝 測試檢查清單

- [ ] 執行 v3 測試
- [ ] 收集引用追蹤日誌
- [ ] 分析引用來源分類
- [ ] 識別主要引用持有者
- [ ] 確認 GC 回收物件數
- [ ] 選擇對應修復方案
- [ ] 實施修復
- [ ] 驗證修復效果

---

**當前版本**: v3 引用追蹤增強  
**狀態**: 🧪 待測試  
**預計完成**: 識別引用持有者後，針對性修復
