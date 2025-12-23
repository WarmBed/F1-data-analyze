# Speed 模組記憶體洩漏診斷 v3 - 深度引用追蹤

## 📋 變更摘要

**版本**: v3 Enhanced Reference Tracking  
**日期**: 2025-10-15  
**狀態**: 🧪 待測試

### 問題回顧

- **v2 測試結果**: cleanup() 執行成功 ✅，但 **GC 回收 0 個物件** ❌
- **根本原因**: 物件被強引用，無法被垃圾回收
- **需求**: 找出是**誰**持有這些強引用

---

## 🔍 v3 新增功能

### 1. **清理前引用追蹤**
在 `cleanup()` 開始時，立即追蹤：

**追蹤 SpeedAnalysisModule 本身**:
```python
self_refcount = sys.getrefcount(self)  # 引用數量
self_referrers = gc.get_referrers(self)  # 誰持有引用

# 分類引用來源（dict, QWidget, frame, function...）
self_ref_types = {<type>: <count>}
```

**追蹤 speed_chart_widget**:
```python
widget_value = self.speed_chart_widget
refcount_before = sys.getrefcount(widget_value)
referrers = gc.get_referrers(widget_value)

# 分類並顯示前 5 個引用來源的詳細信息
```

### 2. **清理後對比追蹤**
在 `cleanup()` 完成後，再次檢查：

**對比模組引用數變化**:
```python
清理前: self_refcount = X
清理後: self_refcount_after = Y
結果: Y 應該接近 1（只剩當前方法的局部引用）
```

**對比 widget 引用數變化**:
```python
清理前: refcount_before = X
清理後: refcount_widget_after = Y
結果: 如果 Y 仍然 > 2，說明有殘留引用
```

### 3. **引用來源分類**
將引用來源按類型分類並統計：

```
模組引用來源分類:
  - dict: 3 個  ← 可能是 analysis_manager, linkage_manager
  - QMdiSubWindow: 1 個  ← MDI 父視窗
  - frame: 10 個  ← Python 呼叫堆疊（正常）
  - function: 2 個  ← 信號連接（需要斷開）
```

### 4. **GC 回收警告**
如果 `gc.collect()` 返回 0：
```python
if collected == 0:
    print("⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！")
```

---

## 🧪 測試步驟

### 前置條件
確保已應用 v3 修改：
- ✅ `speed_analysis_mdi.py` 已更新
- ✅ 引用追蹤代碼已添加

### 執行測試
1. **啟動 GUI**:
   ```powershell
   python f1t_gui_main.py
   ```

2. **打開速度模組**:
   - 選單 → 遙測分析 → 速度分析
   - 等待數據載入完成

3. **關閉速度模組**:
   - 點擊 MDI 視窗的 ❌ 關閉按鈕
   - 或右鍵選單 → 關閉

4. **立即檢查日誌**:
   ```powershell
   Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "CRITICAL.*SPEED" | Select-Object -Last 50
   ```

---

## 📊 預期輸出

### 正常情況（無洩漏）

**清理前**:
```
[CRITICAL] SpeedAnalysisModule 本身引用數: 5
[CRITICAL] 模組被引用數量: 4
[CRITICAL] 模組引用來源分類:
[CRITICAL]     - frame: 3 個
[CRITICAL]     - QMdiSubWindow: 1 個
```

**清理後**:
```
[CRITICAL] SpeedAnalysisModule 清理後引用數: 2
[CRITICAL] 模組清理後被引用數量: 1
[CRITICAL] 模組引用來源分類:
[CRITICAL]     - frame: 1 個
[SPEED_MDI] ✅ 已執行垃圾回收（回收 15 個物件）
```

### 洩漏情況（有問題）

**清理前**:
```
[CRITICAL] SpeedAnalysisModule 本身引用數: 8
[CRITICAL] 模組被引用數量: 7
[CRITICAL] 模組引用來源分類:
[CRITICAL]     - dict: 3 個  ← ⚠️ 全域字典持有
[CRITICAL]     - QMdiSubWindow: 1 個
[CRITICAL]     - frame: 3 個
```

**清理後**:
```
[CRITICAL] SpeedAnalysisModule 清理後引用數: 6  ← ⚠️ 仍然很多！
[CRITICAL] 模組清理後被引用數量: 5  ← ⚠️ 沒減少！
[CRITICAL] 模組引用來源分類:
[CRITICAL]     - dict: 3 個  ← ⚠️ 仍然存在！
[CRITICAL]     - QMdiSubWindow: 1 個
[CRITICAL]     - frame: 1 個
[SPEED_MDI] ✅ 已執行垃圾回收（回收 0 個物件）  ← ⚠️ 關鍵問題！
[CRITICAL] ⚠️⚠️⚠️ GC 回收了 0 個物件！物件仍被強引用！
```

---

## 🎯 診斷目標

根據輸出，識別**引用持有者**：

### dict 類型引用
**可能原因**:
- `analysis_manager.registered_modules` 字典未清除
- `linkage_manager.linkages` 字典未清除
- 其他全域字典

**驗證方法**:
```python
# 在 cleanup 後檢查
print(f"analysis_manager.registered_modules: {len(analysis_manager.registered_modules)}")
print(f"linkage_manager.linkages: {len(linkage_manager.linkages)}")
```

### QMdiSubWindow 引用
**可能原因**:
- MDI 父視窗仍持有子視窗引用
- `QMdiArea.subWindowList()` 未更新

**驗證方法**:
```python
# 在 cleanup 後檢查
sub_windows = self.mdi_area.subWindowList()
print(f"MDI 仍有 {len(sub_windows)} 個子視窗")
```

### function 類型引用
**可能原因**:
- 信號/槽連接未完全斷開
- lambda 函數持有引用

**驗證方法**:
```python
# 檢查信號是否有連接
print(f"data_loaded 連接數: {self.data_manager.data_loaded.receivers(signal)}")
```

---

## 🔧 後續修復方向

根據診斷結果，選擇對應修復方案：

### 如果是 dict 引用問題
```python
# 強制清除全域字典
if self._module_id in analysis_manager.registered_modules:
    del analysis_manager.registered_modules[self._module_id]

# 驗證清除成功
assert self._module_id not in analysis_manager.registered_modules
```

### 如果是 QMdiSubWindow 問題
```python
# 主動移除子視窗
parent = self.parent()
if isinstance(parent, QMdiSubWindow):
    mdi_area = parent.mdiArea()
    mdi_area.removeSubWindow(parent)
    parent.deleteLater()
```

### 如果是 function 引用問題
```python
# 使用 disconnect() 的更強形式
try:
    self.data_manager.disconnect(self)  # 斷開所有連到 self 的信號
except:
    pass
```

---

## 📝 測試檢查清單

- [ ] ✅ 執行測試（打開 → 關閉速度模組）
- [ ] ✅ 收集 CRITICAL 日誌輸出
- [ ] ✅ 分析清理前引用數量和來源
- [ ] ✅ 分析清理後引用數量和來源
- [ ] ✅ 對比前後差異
- [ ] ✅ 識別主要引用持有者（dict? QWidget? function?）
- [ ] ✅ 確認 GC 回收物件數（0 = 問題，>0 = 改善）
- [ ] ✅ 根據結果選擇修復方案
- [ ] ✅ 回報測試結果

---

## 🚀 執行測試

準備好後，執行：
```powershell
# 啟動 GUI
python f1t_gui_main.py

# 測試後查看日誌
Select-String -Path "logs\f1_gui_2025-10-15.log" -Pattern "CRITICAL.*🔍" -Context 0,2 | Select-Object -Last 80
```

請測試後回報：
1. **清理前引用來源分類**
2. **清理後引用來源分類**
3. **GC 回收物件數**
4. **主要引用持有者類型**
