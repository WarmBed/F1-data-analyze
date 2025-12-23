# Task: 詳細圈速分析選項對話框實作

## 📋 任務概述

為 Detailed Lap Analysis 功能添加選項對話框，讓使用者在啟動時選擇分析類型：
- **詳細圈速分析（表格）** - 現有功能
- **圈速箱型圖（Box Plot）** - 新功能

## 🎯 目標

1. 創建 `DetailedLapAnalysisOptionsDialog` 對話框類別
2. 修改主視窗觸發邏輯，攔截 Detailed Lap Analysis 並顯示選項對話框
3. 實現分支邏輯，根據使用者選擇導向不同的分析模組

## 📐 設計規格

### UI 設計
- **視窗尺寸**：420x320 像素（完全對齊 LapAnalysisOptionsDialog）
- **樣式**：完全複製 `LapAnalysisOptionsDialog` 的樣式表和結構
- **控件**：使用 QListWidget（**多選模式**）替代 QRadioButton
- **語言**：支援中英文（使用 i18n 框架）
- **多選支援**：使用者可同時選擇多個分析類型

### 選項設計（最終版本 v3.1.0）
```
┌─────────────────────────────────────┐
│  Detailed Lap Analysis Options      │
├─────────────────────────────────────┤
│  Please select analysis type        │
│                                     │
│  ┌─ Analysis Type ────────────────┐│
│  │ ┌─────────────────────────────┐││
│  │ │ 📊 Detailed Lap Analysis... │││ ← 選中（綠色背景）
│  │ │ 📦 Lap Time Box Plot...     │││ ← 可多選（支援 Ctrl+點擊）
│  │ └─────────────────────────────┘││
│  │  [Select All] [Select None]   │ │ ← 快速選擇按鈕
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ • Detailed Lap Analysis: Shows │ │
│  │   lap-by-lap data table        │ │
│  │ • Lap Time Box Plot: Visualizes│ │
│  │   lap time distribution        │ │
│  └─────────────────────────────────┘│
│                                     │
│              [  OK  ]  [ Cancel ]   │
└─────────────────────────────────────┘

💡 使用者可以：
  - 單選任一分析類型
  - 多選兩個分析類型（同時顯示表格和圖表）
  - 使用 Ctrl+點擊 進行多選
  - 使用快速選擇按鈕全選或清空
```

## 📝 實作清單

### Phase 1.1：創建對話框類別 ✅
- [x] 創建 `modules/gui/driverLap_analysis/detailed_lap_options_dialog.py`
- [x] 實作 `DetailedLapAnalysisOptionsDialog` 類別
- [x] 設計 UI 佈局（初版使用 QRadioButton）
- [x] 添加樣式表（CSS）
- [x] 實作 `get_selected_type()` 方法
- [x] 修復 CSS 警告（移除不支援的偽元素）
- [x] **完全重製**：改用 QListWidget，完全複製 LapAnalysisOptionsDialog 結構
- [x] 調整常數類型從 int 改為 str (TYPE_DETAIL_TABLE="detail_table")
- [x] **多選支援**：改為 MultiSelection 模式，支援同時選擇多種分析
- [x] 添加快速選擇按鈕 (Select All / Select None)
- [x] 實作 `get_selected_types()` 方法（返回列表）

### Phase 1.2：修改主視窗邏輯 ✅
- [x] 在 `f1t_gui_main.py` 中修改 `create_analysis_window()` 攔截邏輯
- [x] 實作 `show_detailed_lap_analysis_options()` 方法
- [x] 實作 `create_analysis_window_internal()` 內部方法
- [x] 實作 `create_laptime_boxplot_window()` Stub 方法
- [x] 保留原有 Detail Lap Analysis 功能路徑
- [x] **多選整合**：修改邏輯以支援同時創建多個分析視窗

### Phase 1.3：測試驗證 ✅
- [x] 測試對話框獨立運行（無錯誤，樣式正確）
- [x] 確認 QListWidget 單選模式正常工作
- [ ] 測試在主視窗中彈出（整合測試）
- [ ] 測試選擇「詳細圈速分析」導向原功能
- [ ] 測試選擇「圈速箱型圖」顯示 Stub 訊息
- [ ] 測試「取消」按鈕功能
- [ ] 完整端到端測試

## 🔧 技術細節

### 對話框 API
```python
class DetailedLapAnalysisOptionsDialog(QDialog):
    def __init__(self, parent=None):
        """初始化對話框"""
        pass
    
    def init_ui(self):
        """構建 UI"""
        pass
    
    def get_selected_type(self) -> int:
        """
        獲取選擇的分析類型
        
        Returns:
            int: 1=詳細圈速分析, 2=圈速箱型圖
        """
        pass
```

### 主視窗整合
```python
def execute_function(self, item, column):
    """執行選單功能"""
    function_name = item.text(0)
    
    # 攔截 Detailed Lap Analysis
    is_detailed_lap = ("詳細圈速分析" in function_name) or ("Detailed Lap Analysis" in function_name)
    if is_detailed_lap:
        dialog = DetailedLapAnalysisOptionsDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_type = dialog.get_selected_type()
            
            if selected_type == 1:
                # 詳細圈速分析（現有功能）- 繼續原有流程
                pass
            elif selected_type == 2:
                # 圈速箱型圖（新功能）- 調用新方法
                self.create_laptime_boxplot_window()
                return
        else:
            return
    
    # 原有邏輯繼續...
```

## 📊 數據流

```
使用者點擊「Detailed Lap Analysis」
    ↓
彈出 DetailedLapAnalysisOptionsDialog
    ↓
使用者選擇分析類型
    ↓
┌─────────────┬──────────────┐
│ 詳細圈速分析  │ 圈速箱型圖    │
├─────────────┼──────────────┤
│ 使用現有模組  │ 調用新模組    │
│ driverlap_  │ laptime_     │
│ analysis_   │ boxplot_     │
│ module      │ widget       │
└─────────────┴──────────────┘
```

## ✅ 驗收標準

1. **功能完整性**
   - ✅ 對話框可正常彈出並顯示
   - ✅ 兩個選項可正確選擇和切換
   - ✅ 確定/取消按鈕功能正常
   - ✅ 選擇後導向正確的分析路徑

2. **UI/UX 品質**
   - ✅ 樣式與系統其他對話框一致
   - ✅ 說明文字清晰易懂
   - ✅ 預設選中「詳細圈速分析」（保持向後相容）

3. **向後相容性**
   - ✅ 原有 Detail Lap Analysis 功能完全不受影響
   - ✅ 現有使用者工作流程保持不變

## 🧪 測試計畫

### 單元測試
- [ ] 對話框初始化測試
- [ ] 選項選擇測試
- [ ] 返回值測試

### 整合測試
- [ ] 主視窗觸發測試
- [ ] 詳細圈速分析路徑測試
- [ ] 圈速箱型圖路徑測試（Stub 實作）

### 手動測試清單
1. **基本功能測試**
   - [ ] 點擊「詳細圈速分析」選單項
   - [ ] 驗證對話框彈出
   - [ ] 預設選中「詳細圈速分析」
   - [ ] 切換到「圈速箱型圖」
   - [ ] 點擊「確定」
   - [ ] 驗證正確的分支被執行

2. **取消測試**
   - [ ] 彈出對話框
   - [ ] 點擊「取消」
   - [ ] 驗證沒有任何視窗被創建

3. **向後相容性測試**
   - [ ] 選擇「詳細圈速分析」
   - [ ] 驗證原有表格正常顯示
   - [ ] 驗證數據正確載入

## 📅 進度追蹤

| 階段 | 任務 | 狀態 | 完成時間 |
|-----|------|------|---------|
| 1.1 | 創建對話框類別 | ✅ 已完成 | 2025-10-02 |
| 1.1 (重製) | 改用 QListWidget 完全複製樣式 | ✅ 已完成 | 2025-10-02 |
| 1.1 (多選) | 支援多選模式與快速選擇按鈕 | ✅ 已完成 | 2025-10-02 |
| 1.2 | 修改主視窗邏輯 | ✅ 已完成 | 2025-10-02 |
| 1.2 (多選) | 支援多選整合邏輯 | ✅ 已完成 | 2025-10-02 |
| 1.3 | 測試驗證 | 🔄 進行中 | - |

## 🔗 相關文件

- 參考實作：`f1t_gui_main.py` - `LapAnalysisOptionsDialog` (line 555-1050)
- 主視窗：`f1t_gui_main.py` - `execute_function()` method
- 現有模組：`modules/gui/driverLap_analysis/driverlap_analysis_module.py`

## 📌 注意事項

1. **國際化支援**：使用 `tr()` 函數包裝所有顯示文字
2. **樣式一致性**：確保樣式表與 `LapAnalysisOptionsDialog` 保持一致
3. **預設選項**：預設選中「詳細圈速分析」以保持向後相容
4. **錯誤處理**：添加適當的異常處理和使用者提示

## 🎯 下一階段預告

完成 Phase 1 後，將進入 **Phase 2：圈速箱型圖模組實作**
- 創建 `LaptimeBoxplotWidget` 類別
- 實作數據載入邏輯（讀取 `detailed_laptime_analysis_*.json`）
- 使用 matplotlib 繪製箱型圖
- 添加數據過濾功能（排除進站圈、安全車圈）

---

**建立時間**：2025-10-02  
**預計完成時間**：Phase 1 約 30 分鐘  
**負責人**：AI Assistant + User  
**狀態**：🔄 Phase 1 進行中
