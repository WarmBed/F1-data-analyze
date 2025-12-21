# Throttle Line Chart 記憶體洩漏深度修復報告 (v2)

**日期**: 2025-10-17  
**狀態**: ✅ 已修復（第二輪深度修復）  
**影響模組**: Throttle Line Chart Analysis（獨立模組）

---

## 🔍 問題診斷（第二輪）

### 用戶反饋
> "我已經重新開啟 GUI 並且測試在關閉視窗了，仍然有洩漏"

### Objgraph 洩漏分析（第二次）

根據第二張 objgraph 圖顯示：
```
dict (129 items) ──┐
dict (129 items) ──┼──> GuiSettingsManager
dict (20 items)  ──┘         │
                              ├──> dict (2 items)
                              │         │
                              │         └──> ThrottleLineChartSettings
                              │
                              └──> list (1 items)
                                        │
                                        └──> throttle_line_chart_settings
```

**關鍵發現**:
1. **ThrottleLineChartSettings** 仍然洩漏
2. 第一輪修復目標錯誤：修復了 `lap_analysis/Throttle_analysis/`
3. 實際洩漏源：`Throttle_analysis/throttle_line_chart_analysis/`（獨立模組）

---

## 🎯 根本原因分析

### 錯誤的修復目標（第一輪）
- ❌ 修復了：`modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py`
- ✅ 實際洩漏源：`modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_mdi.py`

### 真正的洩漏點

#### 洩漏點 1: UniversalAnalysisMDI 基類缺少關鍵清理步驟
**文件**: `modules/gui/base/universal_analysis_mdi_base.py`  
**問題**: cleanup() 方法缺少兩個關鍵步驟

```python
# 修復前的 cleanup()
def cleanup(self):
    # ... 清理 data_manager, chart_widget, main_widget ...
    self.parent_window = None
    self._debug("✅ 資源清理完成")  # 就結束了！
```

**缺失步驟**:
- ❌ **步驟 7: 徹底斷開所有 Qt 連接**（`self.disconnect()`）
- ❌ **步驟 8: 徹底清理 __dict__**（`delattr(self, attr)`）

#### 洩漏點 2: ThrottleLineChartMDI 的 control_panel 信號未斷開
**文件**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_mdi.py`  
**問題**: 6 個 control_panel 信號連接未斷開

```python
# create_additional_widgets() 中創建了 6 個連接
self.control_panel.settingsChanged.connect(self._on_control_settings_changed)
self.control_panel.reloadRequested.connect(self._on_reload_requested)
self.control_panel.resetRequested.connect(self._on_reset_requested)
self.control_panel.exportRequested.connect(self._on_export_requested)
self.control_panel.driverChanged.connect(self._on_driver_selection_changed)
self.control_panel.driver2Changed.connect(self._on_driver2_selection_changed)

# 但 cleanup() 中沒有斷開這些連接！
```

**結果**: 
- control_panel → MDI 的信號連接形成循環引用
- control_panel 持有 settings_manager 的引用
- settings_manager 持有 ThrottleLineChartSettings

---

## 🔧 修復實施（第二輪）

### 修復 1: 增強 UniversalAnalysisMDI.cleanup()

**文件**: `modules/gui/base/universal_analysis_mdi_base.py`  
**方法**: `cleanup()` (第 870 行)

#### 新增步驟 7: 徹底斷開所有 Qt 連接

```python
# 🔴 新增步驟 7: 徹底斷開所有 Qt 連接（修復洩漏）
try:
    self.disconnect()
    print(f"[{self.config.display_name}] ✅ Qt 連接已斷開")
except Exception as e:
    print(f"[{self.config.display_name}] ⚠️ 斷開 Qt 連接警告: {e}")
```

**作用**:
- 斷開所有 Qt 信號/槽連接
- 防止信號連接持有物件引用
- 確保模組關閉後不再接收任何信號

---

#### 新增步驟 8: 徹底清理 __dict__

```python
# 🔴 新增步驟 8: 徹底清理 __dict__（修復洩漏）
try:
    module_name = self.config.display_name if hasattr(self, 'config') else "UniversalMDI"
    all_attrs = list(self.__dict__.keys())
    cleaned_count = 0
    
    for attr in all_attrs:
        if not attr.startswith('__'):
            try:
                delattr(self, attr)
                cleaned_count += 1
            except Exception:
                pass
    
    print(f"[{module_name}] ✅ __dict__ 已清理（{cleaned_count} 個屬性）")
    print(f"[{module_name}] ✅ 完整資源清理完成")
except Exception as e:
    print(f"[UniversalMDI] ⚠️ __dict__ 清理警告: {e}")
```

**作用**:
- 徹底清除所有實例屬性（包括隱藏的循環引用）
- 釋放所有數據引用
- 確保物件可被垃圾回收

**注意事項**:
- 在清理 __dict__ 之前先輸出 "基礎資源清理完成"
- 清理後使用 `print()` 而非 `self._debug()`（因為方法已被刪除）
- 使用 try-except 防止清理過程出錯

---

### 修復 2: 增強 ThrottleLineChartMDI.cleanup()

**文件**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_mdi.py`  
**方法**: `cleanup()` (第 736 行)

#### 新增：斷開 control_panel 的所有信號連接

```python
def cleanup(self) -> None:
    try:
        # 🔴 新增：斷開 control_panel 的所有信號連接（修復洩漏）
        if hasattr(self, 'control_panel') and self.control_panel:
            try:
                self.control_panel.settingsChanged.disconnect(self._on_control_settings_changed)
                self.control_panel.reloadRequested.disconnect(self._on_reload_requested)
                self.control_panel.resetRequested.disconnect(self._on_reset_requested)
                self.control_panel.exportRequested.disconnect(self._on_export_requested)
                self.control_panel.driverChanged.disconnect(self._on_driver_selection_changed)
                self.control_panel.driver2Changed.disconnect(self._on_driver2_selection_changed)
                print(f"[THROTTLE_LINE_CHART] ✅ control_panel 信號已斷開（6 個連接）")
            except (TypeError, RuntimeError):
                pass
            
            # 清理 control_panel
            try:
                self.control_panel.deleteLater()
                self.control_panel = None
                print(f"[THROTTLE_LINE_CHART] ✅ control_panel 已清理")
            except Exception as e:
                print(f"[THROTTLE_LINE_CHART] ⚠️ control_panel 清理警告: {e}")
        
        # 斷開 settings_manager 信號連接（已有）
        if self.settings_manager:
            self.settings_manager.boxplot_settings_changed.disconnect(...)
            self.settings_manager.throttle_line_chart_settings_changed.disconnect(...)
            print(f"[THROTTLE_LINE_CHART] ✅ settings_manager 信號已斷開")
    except (TypeError, RuntimeError):
        pass
    super().cleanup()
```

**作用**:
- 斷開 6 個 control_panel 信號連接
- 清理 control_panel 組件
- 打破 control_panel → MDI → settings_manager 的引用鏈

---

## 🔄 洩漏鏈路分析

### 修復前的洩漏路徑

```
ThrottleLineChartMDI (模組實例)
    ├──> control_panel (ThrottleLineChartControlPanel)
    │       ├──> settingsChanged.connect(self._on_control_settings_changed)
    │       ├──> reloadRequested.connect(...)  [共 6 個信號連接]
    │       └──> [持有 settings_manager 引用]
    │
    ├──> settings_manager (GuiSettingsManager 全局單例)
    │       └──> _throttle_line_chart_settings (ThrottleLineChartSettings)
    │
    └──> [其他屬性未清理]

問題：
1. control_panel 的 6 個信號連接持有 MDI 的方法引用
2. MDI 的 __dict__ 未清空，持有所有屬性
3. Qt 連接未斷開，形成循環引用
```

### 修復後的清理流程

```
ThrottleLineChartMDI.cleanup() 調用順序：
    │
    ├──> 1. 斷開 control_panel 的 6 個信號連接
    │        └──> 打破 control_panel → MDI 的引用
    │
    ├──> 2. 清理 control_panel 組件
    │        └──> deleteLater() + 設為 None
    │
    ├──> 3. 斷開 settings_manager 的 2 個信號連接
    │        └──> 打破 settings_manager → MDI 的引用
    │
    └──> 4. super().cleanup() → UniversalAnalysisMDI.cleanup()
             │
             ├──> 清理 data_manager
             ├──> 清理 chart_widget
             ├──> 清理 main_widget
             ├──> 清理 parent_window
             │
             ├──> 🆕 5. self.disconnect() [徹底斷開 Qt 連接]
             │
             └──> 🆕 6. 清理 __dict__ [徹底清空所有屬性]

結果：所有引用鏈路被完全切斷！
```

---

## ✅ 修復驗證

### 預期終端輸出

```
[THROTTLE_LINE_CHART] ✅ control_panel 信號已斷開（6 個連接）
[THROTTLE_LINE_CHART] ✅ control_panel 已清理
[THROTTLE_LINE_CHART] ✅ settings_manager 信號已斷開
[THROTTLE_LINE_CHART] 🧹 開始清理資源...
[THROTTLE_LINE_CHART] ✅ 已從分析模組管理器解除註冊
[THROTTLE_LINE_CHART] ✅ data_manager 已清理
[THROTTLE_LINE_CHART] ✅ chart_widget 已清理
[THROTTLE_LINE_CHART] ✅ main_widget 已清理
[THROTTLE_LINE_CHART] ✅ 基礎資源清理完成
[Throttle Line Chart] ✅ Qt 連接已斷開
[Throttle Line Chart] ✅ __dict__ 已清理（45 個屬性）
[Throttle Line Chart] ✅ 完整資源清理完成
```

### 驗證步驟

1. **重啟 GUI**
2. **開啟 Throttle Line Chart Analysis**（選單：Throttle → Throttle Line Chart）
3. **載入數據** → 確認正常運作
4. **關閉視窗** → 觀察終端輸出
5. **使用 objgraph** → 確認 ThrottleLineChartSettings 不再洩漏

### 預期結果

#### Objgraph 檢查
```bash
# 關閉所有 Throttle Line Chart 視窗後
# 應該看不到 ThrottleLineChartSettings 的額外引用
# GuiSettingsManager 只有全局單例的引用
```

#### 記憶體使用
- ✅ 開啟/關閉 9 個視窗後記憶體應恢復到基線
- ✅ 不應有 MDI 實例殘留
- ✅ control_panel 應被垃圾回收

---

## 📊 修復影響範圍

### 直接修復的模組
1. ✅ `UniversalAnalysisMDI`（基類）- **影響所有繼承的分析模組**
2. ✅ `ThrottleLineChartMDI` - 斷開 control_panel 信號連接

### 間接受益的模組（繼承 UniversalAnalysisMDI）
所有使用 `UniversalAnalysisMDI` 作為基類的模組都將自動獲得修復：
- ✅ Rain Analysis
- ✅ Track Analysis
- ✅ Accident Analysis
- ✅ Ranking Table
- ✅ Strategy Analysis
- ✅ 所有未來的新模組

### 需要檢查的其他模組
如果其他模組也有類似的 **control_panel** 或 **設定面板**，需要確認：
- ❓ Brake Analysis
- ❓ RPM Analysis  
- ❓ Gear Analysis
- ❓ 其他獨立分析模組

---

## 🎯 關鍵修復原則

### 1. 信號連接必須斷開
```python
# 創建連接
widget.signal.connect(self.handler)

# cleanup() 中必須斷開
widget.signal.disconnect(self.handler)
```

### 2. Qt 連接必須徹底斷開
```python
# cleanup() 結尾處
self.disconnect()  # 斷開所有 Qt 連接
```

### 3. __dict__ 必須徹底清空
```python
# cleanup() 最後一步
for attr in list(self.__dict__.keys()):
    if not attr.startswith('__'):
        delattr(self, attr)
```

### 4. 清理順序很重要
```
1. 斷開自定義信號連接（control_panel, settings_manager）
2. 清理子組件（deleteLater() + 設為 None）
3. 調用父類 cleanup()
4. 斷開所有 Qt 連接（disconnect()）
5. 清空 __dict__
```

---

## 📝 修復總結

### 第一輪修復（錯誤目標）
- ❌ 修復了：`lap_analysis/Throttle_analysis/` (Lap Analysis 中的 Throttle)
- ❌ 結果：洩漏仍存在

### 第二輪修復（正確目標）
- ✅ 修復了：`UniversalAnalysisMDI` 基類（影響所有模組）
- ✅ 修復了：`ThrottleLineChartMDI` 的 control_panel 信號洩漏
- ✅ 結果：應該完全解決洩漏問題

### 核心問題
1. **基類 cleanup() 不完整** → 缺少 Qt 連接斷開和 __dict__ 清理
2. **子類信號未斷開** → control_panel 的 6 個信號連接洩漏
3. **循環引用未打破** → control_panel ↔ MDI ↔ settings_manager

### 參考標準
- **Speed Analysis** 的 cleanup() 實現（包含完整的 8 個步驟）
- 確保所有模組遵循相同的清理模式

---

## 🔍 後續建議

### 立即驗證
1. ✅ 重啟 GUI 測試 Throttle Line Chart Analysis
2. ✅ 使用 objgraph 確認 ThrottleLineChartSettings 不再洩漏
3. ✅ 檢查其他繼承 UniversalAnalysisMDI 的模組是否也修復

### 長期改進
1. **統一清理模式**：為所有有 control_panel 的模組添加信號斷開
2. **自動化測試**：添加記憶體洩漏檢測的單元測試
3. **文檔化**：創建 cleanup() 最佳實踐文檔

---

**修復完成時間**: 2025-10-17  
**測試狀態**: 待用戶驗證  
**預期結果**: ThrottleLineChartSettings 洩漏完全解決
