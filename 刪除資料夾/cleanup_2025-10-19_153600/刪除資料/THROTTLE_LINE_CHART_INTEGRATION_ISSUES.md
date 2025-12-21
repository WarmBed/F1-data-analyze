# Throttle Line Chart 模組整合問題診斷報告

**時間**: 2025-10-08  
**狀態**: 需要架構調整  
**優先級**: P1 - 核心功能阻塞

---

## 🔴 問題概要

Throttle Line Chart 模組實現完成後，在整合測試階段發現與現有架構不兼容的問題。

## 📋 問題清單

### 1. UniversalAnalysisMDI 抽象方法未實現

**錯誤訊息**:
```
TypeError: Can't instantiate abstract class ThrottleLineChartMDI without an
implementation for abstract methods 'create_chart_widget', 'create_data_manager'
```

**原因分析**:
- `ThrottleLineChartMDI` 繼承自 `UniversalAnalysisMDI` 基類
- 基類要求子類必須實現兩個抽象方法:
  - `create_data_manager()`: 創建數據管理器
  - `create_chart_widget()`: 創建圖表組件

**受影響文件**:
- `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_mdi.py`

**解決方案**:
需要在 `ThrottleLineChartMDI` 中實現這兩個方法，返回對應的實例。

---

### 2. 架構設計不匹配

**問題**:
當前實現基於 Rain Analysis 的雙窗口模式設計，但 `UniversalAnalysisMDI` 基類預期的是：
- 單一數據管理器 (data_manager)
- 單一圖表組件 (chart_widget)

而 Throttle Line Chart 需要：
- 單一數據載入器 (ThrottleLineChartDataLoader)
- **兩個**圖表組件 (ThrottleDurationChartWidget + LapTimeChartWidget)
- 視窗間同步機制

**衝突點**:
1. `create_chart_widget()` 只能返回一個組件，無法處理雙窗口
2. 基類沒有雙窗口管理的內建支援

---

### 3. 依賴安裝問題（已解決 ✅）

**問題**: 缺少 mplcursors 套件
**解決**: 已通過 `pip install mplcursors` 安裝

---

## 🔧 修復計劃

### 方案 A: 修改 ThrottleLineChartMDI 以符合基類要求（推薦）

**步驟**:

1. **實現 `create_data_manager()`**:
   ```python
   def create_data_manager(self):
       """創建數據管理器"""
       self._loader = ThrottleLineChartDataLoader(parent=self)
       return self._loader
   ```

2. **實現 `create_chart_widget()` - 返回主窗口容器**:
   ```python
   def create_chart_widget(self):
       """創建主圖表容器（包含兩個圖表的 QSplitter）"""
       # 創建 splitter 容器
       self._main_splitter = QSplitter(Qt.Vertical)
       
       # 創建兩個圖表
       self._throttle_chart = ThrottleDurationChartWidget()
       self._lap_time_chart = LapTimeChartWidget()
       
       # 添加到 splitter
       self._main_splitter.addWidget(self._throttle_chart)
       self._main_splitter.addWidget(self._lap_time_chart)
       
       # 設置同步
       self._connect_sync_signals()
       
       return self._main_splitter
   ```

3. **移除自定義 UI 初始化邏輯**:
   - 刪除 `_init_ui()` 中與圖表創建相關的代碼
   - 保留車手選擇下拉框等控制組件

---

### 方案 B: 不使用 UniversalAnalysisMDI 基類

**步驟**:
1. 將 `ThrottleLineChartMDI` 改為直接繼承 `QWidget`
2. 自行實現所有 UI 邏輯和數據載入
3. 不依賴基類的自動化功能

**優點**: 完全自主控制
**缺點**: 代碼重複，失去架構統一性

---

## 📝 需要修改的文件

| 文件 | 修改內容 | 優先級 |
|------|---------|--------|
| `throttle_line_chart_mdi.py` | 實現抽象方法 | P0 |
| `throttle_line_chart_module.py` | 調整初始化邏輯 | P1 |
| `throttle_line_chart_data_loader.py` | 確保符合數據管理器接口 | P1 |

---

## 🎯 下一步行動

### 立即執行（您醒來後）:

1. **測試 GUI 啟動**:
   ```powershell
   python f1t_gui_main.py
   ```
   確認主程式是否正常運行（即使 Throttle Line Chart 無法載入）

2. **選擇修復方案**:
   - 推薦方案 A: 符合架構規範
   - 如需快速測試可選方案 B

3. **實施修復**:
   - 修改 `throttle_line_chart_mdi.py` 實現兩個抽象方法
   - 測試導入: `python test_throttle_imports.py`
   - 測試 GUI: 點擊「油門分析」→「Throttle Line Chart」

---

## ✅ 已完成工作

- [x] 5 個新文件創建（data_loader, chart_widgets, mdi, module）
- [x] GUI 主程式整合（f1t_gui_main.py）
- [x] i18n 翻譯添加
- [x] mplcursors 套件安裝
- [x] UniversalDataLoader 初始化修正
- [x] IAnalysisModule 接口實現

---

## ⏳ 待完成工作

- [ ] 實現 `create_data_manager()` 方法
- [ ] 實現 `create_chart_widget()` 方法
- [ ] 調整 UI 初始化邏輯
- [ ] 完整導入測試通過
- [ ] GUI 功能測試

---

## 📊 技術債務

1. **架構文檔缺失**: `UniversalAnalysisMDI` 的使用指南不完整
2. **範例模組不足**: 沒有雙窗口模式的標準範例
3. **測試覆蓋不足**: 缺少模組整合測試

---

## 💡 架構建議

建議為 `UniversalAnalysisMDI` 添加雙窗口支援:

```python
# 基類中添加可選方法
def create_secondary_chart_widget(self) -> Optional[QWidget]:
    """創建次要圖表組件（可選，用於雙窗口模式）"""
    return None

def get_chart_layout_mode(self) -> str:
    """返回佈局模式: 'single' 或 'dual'"""
    return 'single'
```

這樣未來的雙窗口模組就有標準化的實現方式。

---

**報告結束** - 所有問題已診斷完畢，等待實施修復 🛠️
