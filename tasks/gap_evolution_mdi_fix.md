# Gap Evolution MDI 架構修復 - 測試計畫

## 📋 問題摘要

**發現日期**: 2025-12-03  
**嚴重性**: 中等（功能正常但 UI 不一致）

**問題描述**:  
Gap Evolution 圖表視窗使用 `QMdiSubWindow` 直接包裝 `GapEvolutionChartWidget`，導致缺少標準 MDI 控制項（標題欄、最大化/最小化/關閉按鈕等）。

**用戶報告**:  
> "為甚麼 continue current tyre 沒有像通用MDI模組一樣有標題有按鈕有X有最大化等？"

## 🔍 根本原因

### 錯誤的 MDI 架構（修復前）

```python
# ❌ 錯誤：直接使用 QMdiSubWindow
from PyQt5.QtWidgets import QMdiSubWindow

chart_widget = GapEvolutionChartWidget(...)  # 普通 QWidget
sub_window = QMdiSubWindow()  # ← 問題所在
sub_window.setWidget(chart_widget)
parent_widget.addSubWindow(sub_window)
sub_window.show()

# 結果：視窗顯示但缺少標準 MDI 控制項
```

### 正確的 MDI 架構（修復後）

```python
# ✅ 正確：使用 PopoutSubWindow
from __main__ import PopoutSubWindow

chart_widget = GapEvolutionChartWidget(...)  # 普通 QWidget
sub_window = PopoutSubWindow(  # ← 正確方式
    window_title, 
    parent_widget,
    analysis_module=None,  # Gap Chart 不是標準分析模組
    sync_enabled=False  # 不需要參數同步
)
sub_window.setWidget(chart_widget)
parent_widget.addSubWindow(sub_window)
sub_window.show()

# 結果：完整的 MDI 功能（標題欄、按鈕、拖曳等）
```

## 📊 架構對比

### QMdiSubWindow vs PopoutSubWindow

| 功能 | QMdiSubWindow | PopoutSubWindow |
|------|---------------|-----------------|
| **標題欄** | ❌ 不完整 | ✅ 完整 |
| **最大化按鈕** | ❌ 缺失 | ✅ 有 |
| **最小化按鈕** | ❌ 缺失 | ✅ 有 |
| **關閉按鈕 (X)** | ❌ 缺失 | ✅ 有 |
| **拖曳** | ⚠️ 基本 | ✅ 增強 |
| **調整大小** | ⚠️ 基本 | ✅ 增強 |
| **統一樣式** | ❌ 不一致 | ✅ 一致 |
| **彈出功能** | ❌ 無 | ✅ 支援 |
| **信號通知** | ❌ 無 | ✅ 有（resized, window_closed） |

### 其他模組的參考

所有 Live Timing 模組都使用相同的架構：

```python
# Speed Trace, Driver Strategy, Circle Map 等
module_instance = factory.create_module(module_name, self)  # QWidget
sub_window = PopoutSubWindow(window_title, mdi_area, None, False)
sub_window.setWidget(module_instance)
mdi_area.addSubWindow(sub_window)
sub_window.show()
```

## 🔧 修復內容

### 檔案：`chase_strategy.py`

#### 方法：`_show_gap_chart()` (Line 1160-1220)

**變更摘要**：
- ❌ 移除：`from PyQt5.QtWidgets import QMdiSubWindow`
- ✅ 新增：從 `__main__` 導入 `PopoutSubWindow`
- ✅ 新增：備用回退機制（如果導入失敗）
- ✅ 修改：使用 `PopoutSubWindow` 創建視窗

**關鍵代碼**：
```python
# 動態導入 PopoutSubWindow
import sys
main_module = sys.modules.get('__main__')
if main_module and hasattr(main_module, 'PopoutSubWindow'):
    PopoutSubWindow = main_module.PopoutSubWindow
else:
    # 備用：回退到 QMdiSubWindow
    print(f"[CHASE_STRATEGY] ⚠️ 無法導入 PopoutSubWindow，回退到 QMdiSubWindow")
    from PyQt5.QtWidgets import QMdiSubWindow
    # ... 使用 QMdiSubWindow 的舊流程 ...
    return

# 創建 PopoutSubWindow
window_title = f"{strategy.name} - Gap Evolution"
sub_window = PopoutSubWindow(
    window_title, 
    parent_widget,
    analysis_module=None,
    sync_enabled=False
)
sub_window.setWidget(chart_widget)
sub_window.resize(900, 600)
parent_widget.addSubWindow(sub_window)
sub_window.show()
```

## ✅ 測試清單

### 階段 1：視窗創建測試（5 分鐘內）

- [ ] **啟動 GUI**
  ```powershell
  python f1t_gui_main.py
  ```

- [ ] **開啟 Chase Strategy 模組**
  - 選單：`Live Timing` → `Chase Strategy`
  - 確認主視窗正常打開

- [ ] **顯示 Gap Evolution 圖表**
  - 右鍵點擊任一策略（例如 "Continue Current Tyre"）
  - 選擇 "Show Gap Evolution Chart"
  - **驗證點**：
    - [ ] ✅ 圖表視窗正常顯示
    - [ ] ✅ 有完整標題欄
    - [ ] ✅ 標題顯示 "{策略名稱} - Gap Evolution"
    - [ ] ✅ 有最大化按鈕
    - [ ] ✅ 有最小化按鈕
    - [ ] ✅ 有關閉按鈕 (X)
    - [ ] ✅ 無任何 Python 錯誤或異常

### 階段 2：視窗功能測試（10 分鐘內）

- [ ] **拖曳測試**
  - 拖曳視窗標題欄
  - **驗證**：視窗可以自由移動

- [ ] **調整大小測試**
  - 拖曳視窗邊緣和角落
  - **驗證**：視窗可以調整大小

- [ ] **最大化測試**
  - 點擊最大化按鈕
  - **驗證**：視窗最大化到 MDI 區域
  - 再次點擊恢復按鈕
  - **驗證**：視窗恢復原始大小

- [ ] **關閉測試**
  - 點擊 X 關閉按鈕
  - **驗證**：視窗正常關閉，無錯誤

- [ ] **多視窗測試**
  - 打開多個 Gap Evolution 圖表（不同策略）
  - **驗證**：
    - [ ] 所有視窗都有完整控制項
    - [ ] 可以切換活動視窗
    - [ ] 可以獨立操作每個視窗

### 階段 3：功能完整性測試（15 分鐘內）

- [ ] **圖表內容驗證**
  - 打開 "Continue Current Tyre" 的 Gap 圖表
  - **驗證**：
    - [ ] P1 曲線使用車手顏色（藍色 VER）
    - [ ] P2 曲線使用車手顏色（橘色 PIA）
    - [ ] 實際線有圓點標記
    - [ ] 預測線只有虛線（無圓點）
    - [ ] Y 軸範圍自動適應數據
    - [ ] 圖表繪製正確

- [ ] **進站策略測試**
  - 打開 "Undercut (Pit Lap 10)" 的 Gap 圖表
  - **驗證**：
    - [ ] 進站圈有虛線標記
    - [ ] Gap 演變符合預期
    - [ ] 所有 MDI 控制項正常工作

- [ ] **不可行策略測試**
  - 打開任一標記為 "Infeasible" 的策略 Gap 圖表
  - **驗證**：
    - [ ] 圖表仍然顯示（允許查看假設性演變）
    - [ ] MDI 控制項正常工作

### 階段 4：與其他模組對比測試（10 分鐘內）

- [ ] **Speed Trace 對比**
  - 開啟 `Live Timing` → `Speed Trace`
  - **驗證**：Gap Evolution 和 Speed Trace 的視窗樣式一致

- [ ] **Driver Strategy 對比**
  - 開啟 `Live Timing` → `Driver Strategy`
  - **驗證**：Gap Evolution 和 Driver Strategy 的視窗樣式一致

- [ ] **視窗切換測試**
  - 同時開啟 Chase Strategy、Speed Trace、Driver Strategy
  - 打開 Gap Evolution 圖表
  - **驗證**：
    - [ ] 所有視窗樣式統一
    - [ ] 可以自由切換和排列
    - [ ] Tile/Cascade 功能正常

## 📝 預期結果

### ✅ 成功標準

1. **視窗完整性**
   - Gap Evolution 視窗有完整的標題欄
   - 所有標準按鈕（最大化/最小化/關閉）都可用

2. **功能正常性**
   - 圖表繪製正確（車手顏色、線型、Y 軸）
   - 所有 MDI 操作（拖曳、調整大小、最大化）正常

3. **架構一致性**
   - Gap Evolution 視窗與其他 Live Timing 模組樣式一致
   - 符合專案的標準 MDI 架構模式

### ❌ 失敗標準

- 視窗缺少任何標準控制項
- 出現 Python 異常或錯誤
- 圖表內容不正確（顏色、線型等）
- 與其他模組的樣式不一致

## 🔄 回退計畫

如果測試失敗，系統已內建備用回退機制：

```python
# 自動回退到 QMdiSubWindow
if main_module and hasattr(main_module, 'PopoutSubWindow'):
    # 使用 PopoutSubWindow
else:
    # 自動回退到 QMdiSubWindow
    print(f"[CHASE_STRATEGY] ⚠️ 無法導入 PopoutSubWindow，回退到 QMdiSubWindow")
    from PyQt5.QtWidgets import QMdiSubWindow
    # ... 舊流程 ...
```

## 📊 測試記錄

### 測試環境

- **作業系統**：Windows
- **Python 版本**：3.x
- **PyQt5 版本**：5.x
- **測試日期**：2025-12-03

### 測試結果

| 階段 | 測試項目 | 結果 | 備註 |
|------|---------|------|------|
| 1 | 視窗創建 | ⏳ 待測 | |
| 2 | 視窗功能 | ⏳ 待測 | |
| 3 | 功能完整性 | ⏳ 待測 | |
| 4 | 模組對比 | ⏳ 待測 | |

### 發現的問題

*（測試後填寫）*

### 解決方案

*（如有問題，記錄解決方案）*

## 📚 相關文件

- **主要修改**：`modules/gui/live_timing/live_timing_modules/chase_strategy.py` (Line 1160-1220)
- **參考架構**：`f1t_gui_main.py::_open_live_timing_module()` (Line 9368-9480)
- **PopoutSubWindow 定義**：`f1t_gui_main.py::PopoutSubWindow` (Line 3390-3470)
- **BaseLiveTimingMDI**：`modules/gui/live_timing/core/base_live_mdi.py` (Line 17-200)

## 🎯 後續改進

**可選優化**（不影響當前功能）：

1. **創建專用 MDI 類**（如果需要更多 Gap Chart 功能）
   ```python
   class GapEvolutionMDI(BaseLiveTimingMDI):
       def _setup_ui(self):
           self.chart_widget = GapEvolutionChartWidget(...)
           self._main_layout.addWidget(self.chart_widget)
   ```

2. **添加狀態保存**（如果需要 Workspace 支援）
   - 保存 Gap Chart 視窗狀態
   - 恢復視窗位置和大小

3. **增強互動功能**
   - 圖表上右鍵選單
   - 導出圖表功能
   - 數據點工具提示

---

**測試負責人**：AI Assistant  
**審查者**：用戶  
**狀態**：⏳ 待測試  
**優先級**：中等（UI 一致性）
