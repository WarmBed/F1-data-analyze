# Lap Analysis 多模組載入問題 - 診斷報告
## Lap Analysis Multi-Module Loading Issue - Diagnostic Report

**日期 / Date**: 2025-10-22  
**問題 / Issue**: Lap Analysis 多模組（速度、RPM、齒輪等）載入有問題  
**嚴重程度 / Severity**: 🔴 **HIGH** - 影響用戶體驗

---

## 🔍 問題診斷 (Problem Diagnosis)

### 錯誤訊息 (Error Messages)

從 `logs/f1_gui_2025-10-22.log` 中發現大量重複錯誤：

```
[ERROR] [LINKAGE_MANAGER] wrapped C/C++ object of type SpeeddiffAnalysisChartWidget has been deleted
[ERROR] [LINKAGE_MANAGER] wrapped C/C++ object of type distancediffAnalysisChartWidget has been deleted
[ERROR] [LINKAGE_MANAGER] wrapped C/C++ object of type timediffAnalysisChartWidget has been deleted
```

### 問題分析 (Root Cause Analysis)

#### 1. **物件生命週期問題** (Object Lifetime Issue)

**問題**:
- 當用戶載入 Workspace 時，Lap Analysis 的多個子模組視窗被創建
- 這些視窗的 ChartWidget 被註冊到 `LinkageManager.registered_modules` 列表中
- 當視窗關閉或被重新創建時，底層的 C++ Qt 物件被刪除
- 但 `registered_modules` 列表中仍然持有這些 Python 包裝器的引用
- 當 LinkageManager 嘗試向這些已刪除的 widget 發送信號時，觸發 RuntimeError

#### 2. **錯誤處理不完整** (Incomplete Error Handling)

**現有代碼** (`linkage_manager.py`):
```python
def send_x_linkage(self, distance_value: float, y_relative: float, sender=None):
    """發送X軸連動信號"""
    if not self.master_linkage_enabled:
        return
    
    # 發送給所有模組（除了發送者）
    for module in self.registered_modules:
        if module != sender and hasattr(module, 'on_x_linkage_received'):
            try:
                module.on_x_linkage_received(distance_value, y_relative)
            except Exception as e:
                print(f"[ERROR] [LINKAGE_MANAGER] X軸連動信號發送失敗: {e}")
                # ❌ 問題：只打印錯誤，沒有清理已刪除的 widget
```

**缺失的處理**:
- ❌ 沒有檢測 "wrapped C/C++ object has been deleted" 錯誤
- ❌ 沒有自動從 `registered_modules` 中移除已刪除的 widget
- ❌ 錯誤會在每次連動時重複觸發（每秒多次）

#### 3. **Workspace 反序列化問題** (Workspace Deserialization Issue)

**可能的觸發場景**:
1. 用戶儲存 Workspace（包含多個 Lap Analysis 視窗）
2. 用戶載入 Workspace
3. 系統嘗試重建所有視窗
4. 舊的 Widget 實例被刪除但未正確取消註冊
5. 新的 Widget 實例被創建並註冊
6. LinkageManager 的列表中同時存在已刪除和有效的 widget
7. 連動信號發送時失敗

---

## 🛠️ 修復方案 (Fix Solutions)

### 方案 A：增強錯誤處理 + 自動清理 ✅ **推薦**

**優點**:
- ✅ 自動檢測並移除已刪除的 widget
- ✅ 不影響現有代碼邏輯
- ✅ 防禦性編程，處理所有邊緣情況
- ✅ 減少日誌噪音

**實現**:

修改 `linkage_manager.py` 中的所有信號發送方法：

```python
def send_x_linkage(self, distance_value: float, y_relative: float, sender=None):
    """發送X軸連動信號"""
    if not self.master_linkage_enabled:
        return
    
    # 需要移除的已刪除模組
    modules_to_remove = []
    
    # 發送給所有模組（除了發送者）
    for module in self.registered_modules:
        if module != sender and hasattr(module, 'on_x_linkage_received'):
            try:
                module.on_x_linkage_received(distance_value, y_relative)
            except RuntimeError as e:
                # 檢測 C++ 物件已刪除的錯誤
                if "wrapped C/C++ object" in str(e) and "has been deleted" in str(e):
                    print(f"[LINKAGE_MANAGER] 檢測到已刪除的模組，將自動移除: {type(module).__name__}")
                    modules_to_remove.append(module)
                else:
                    print(f"[ERROR] [LINKAGE_MANAGER] X軸連動信號發送失敗: {e}")
            except Exception as e:
                print(f"[ERROR] [LINKAGE_MANAGER] X軸連動信號發送失敗: {e}")
    
    # 清理已刪除的模組
    for module in modules_to_remove:
        self._safe_remove_module(module)
    
    # 發送全域信號
    self.x_linkage_signal.emit(distance_value, y_relative)

def _safe_remove_module(self, module):
    """安全地移除已刪除的模組（不觸發信號斷開）"""
    if module in self.registered_modules:
        self.registered_modules.remove(module)
        print(f"[LINKAGE_MANAGER] 已自動清理已刪除的模組，目前共 {len(self.registered_modules)} 個模組")
```

**需要修改的方法**:
- `send_x_linkage()` ✅
- `send_x_linkage_clear()` ✅
- `send_click_linkage()` ✅
- `send_click_linkage_clear()` ✅
- `set_master_linkage_enabled()` ✅
- `set_time_axis_mode()` ✅

---

### 方案 B：強制在視窗關閉時取消註冊 ⚠️ **次要**

**優點**:
- ✅ 從源頭避免問題
- ✅ 更乾淨的物件生命週期管理

**缺點**:
- ❌ 需要修改所有 Lap Analysis 模組的關閉事件
- ❌ 需要確保所有視窗都正確實現 `closeEvent`
- ❌ Workspace 反序列化時可能仍有時序問題

**實現範例**:

```python
# 在每個 ChartWidget 中添加
def closeEvent(self, event):
    """視窗關閉時取消註冊"""
    if linkage_manager:
        linkage_manager.unregister_module(self)
    super().closeEvent(event)
```

---

### 方案 C：WeakRef 弱引用管理 🔬 **實驗性**

**優點**:
- ✅ Python 自動垃圾回收處理已刪除的 widget
- ✅ 不需要手動取消註冊

**缺點**:
- ❌ 需要重構整個 LinkageManager
- ❌ 可能影響現有功能
- ❌ 增加代碼複雜度

---

## 📝 建議修復步驟 (Recommended Fix Steps)

### 步驟 1: 實施方案 A - 增強錯誤處理

1. **修改 `linkage_manager.py`**
   - 添加 `_safe_remove_module()` 方法
   - 更新所有信號發送方法以捕獲 RuntimeError
   - 自動清理已刪除的模組

2. **測試修復**
   - 創建多個 Lap Analysis 視窗
   - 載入/儲存 Workspace
   - 檢查日誌中是否還有 "has been deleted" 錯誤

### 步驟 2: 添加視窗關閉時的清理（可選）

1. **修改所有 ChartWidget**
   - 添加 `closeEvent()` 處理
   - 確保取消註冊

### 步驟 3: 改進 Workspace 反序列化

1. **修改 `workspace_serializer.py`**
   - 在重建視窗前清理舊的註冊
   - 確保註冊順序正確

---

## 🧪 測試計劃 (Test Plan)

### 測試場景

1. **基本多模組載入**
   - [ ] 開啟 Speed Analysis
   - [ ] 開啟 RPM Analysis
   - [ ] 開啟 Gear Analysis
   - [ ] 測試連動功能
   - [ ] 檢查是否有錯誤訊息

2. **Workspace 載入/儲存**
   - [ ] 創建包含多個 Lap Analysis 視窗的 Workspace
   - [ ] 儲存 Workspace
   - [ ] 關閉所有視窗
   - [ ] 載入 Workspace
   - [ ] 檢查所有視窗是否正確重建
   - [ ] 測試連動功能
   - [ ] 檢查日誌中是否有 "has been deleted" 錯誤

3. **視窗生命週期**
   - [ ] 開啟多個視窗
   - [ ] 逐一關閉視窗
   - [ ] 檢查 LinkageManager 的 registered_modules 數量
   - [ ] 測試剩餘視窗的連動功能

---

## 📊 影響評估 (Impact Assessment)

### 當前影響

- 🔴 **用戶體驗**: 日誌中大量錯誤訊息（每秒多次）
- 🟡 **功能影響**: 連動功能可能不穩定
- 🟢 **數據完整性**: 不影響數據本身

### 修復後預期

- ✅ 錯誤訊息消失
- ✅ 連動功能穩定
- ✅ Workspace 載入流暢
- ✅ 記憶體使用優化（不累積已刪除的引用）

---

## 📚 相關檔案 (Related Files)

| 檔案 | 需要修改 | 說明 |
|------|---------|------|
| `modules/gui/lap_analysis/linkage/linkage_manager.py` | ✅ 是 | 核心修改：增強錯誤處理 |
| `modules/gui/lap_analysis/*/[*]_chart_widget.py` | ⚠️ 可選 | 添加 closeEvent 清理 |
| `core/workspace_serializer.py` | ⚠️ 可選 | 改進反序列化流程 |

---

## 🔍 其他發現 (Additional Findings)

### 日誌中的其他模式

除了 "has been deleted" 錯誤，還發現：
- `[THROTTLE_CHART]` 和 `[TIME_AXIS_DEBUG]` 的大量調試輸出
- 建議在生產環境中降低調試輸出級別

---

**診斷完成時間**: 2025-10-22  
**診斷者**: GitHub Copilot  
**下一步**: 等待用戶確認修復方案後開始實施
