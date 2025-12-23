# 樹狀圖架構重構任務

## 📋 任務概述
將 GUI 主視窗的分析功能樹狀圖重構為三層架構，並實現智能批量操作功能。

## 🎯 目標
1. 將 MDI 模組從 "Single Race Driver Analysis" 群組中拆分出來
2. 實現三層架構：Race Overview、Driver Performance、Multi-Season
3. 展開顯示所有子模組（Lap Analysis 的 8 個子模組、Detailed Lap 的 2 個視圖等）
4. 實現智能批量操作：Shift 全選時過濾掉父項目，只開啟葉節點

## 📊 新架構設計

```
📁 Race Overview Analysis（賽事總覽分析）
├── Rain Analysis
├── Track Analysis
├── Pitstop Analysis
├── Accident Analysis
└── Tire Strategy Analysis

📁 Driver Performance Analysis（車手表現分析）
├── Lap Analysis (Telemetry)
│   ├── Speed Analysis
│   ├── Brake Analysis
│   ├── Throttle Analysis
│   ├── Gear Analysis
│   ├── RPM Analysis
│   ├── Acceleration Analysis
│   ├── Speed Diff Analysis
│   └── Distance Diff Analysis
├── Detailed Lap Analysis
│   ├── Detailed Lap Table
│   └── Lap Time Box Plot
├── Throttle Analysis
│   ├── Throttle Box Plot
│   └── Throttle Line Chart
└── Ideal Lap Analysis
    ├── Ranking Table
    ├── Sector Heat Map (Coming Soon)
    └── Sector Comparison (Coming Soon)

📁 Multi-Season Analysis（多賽季分析）
└── Coming Soon...
```

## 🔧 實現清單

### Phase 1: 樹狀圖結構重構
- [x] 修改 `create_analysis_tree()` 函數
- [x] 實現三層架構（Race Overview / Driver Performance / Multi-Season）
- [x] 添加所有子模組項目
- [x] 使用 Emoji 圖標美化
- [x] 標記開發中的功能（Coming Soon）

### Phase 2: 批量操作邏輯
- [x] 修改 `ContextMenuTreeWidget.show_context_menu()`
  - [x] 過濾葉節點（childCount() == 0）
  - [x] 區分單選和多選右鍵選單
- [x] 修改 `analyze_multiple_functions()`
  - [x] 二次過濾確保只處理葉節點
  - [x] 添加日誌顯示過濾的父項目數量
  - [x] 傳遞 batch_mode=True 參數
- [x] 修改 `analyze_function()`
  - [x] 添加 batch_mode 參數
  - [x] batch_mode=True 時跳過對話框
  - [x] 實現所有子項目的直接開啟邏輯

### Phase 3: 子項目映射
- [x] Lap Analysis 子模組映射
  - [x] Speed Analysis → speed_analysis
  - [x] Brake Analysis → brake
  - [x] Throttle Analysis → throttle
  - [x] Gear Analysis → gear
  - [x] RPM Analysis → rpm
  - [x] Acceleration Analysis → acceleration
  - [x] Speed Diff Analysis → speed_diff
  - [x] Distance Diff Analysis → distancediff
- [x] Detailed Lap Analysis 子模組映射
  - [x] Detailed Lap Table → detail_table
  - [x] Lap Time Box Plot → box_plot
- [x] Throttle Analysis 子模組映射
  - [x] Throttle Box Plot
  - [x] Throttle Line Chart
- [x] Ideal Lap Analysis 子模組映射
  - [x] Ranking Table
  - [x] Sector Heat Map (禁用)
  - [x] Sector Comparison (禁用)

### Phase 4: 國際化支援
- [x] 添加新的翻譯字串
  - [x] race_overview_analysis
  - [x] driver_performance_analysis
  - [x] multi_season_analysis
  - [x] 所有子模組名稱
- [x] 更新中英文翻譯檔案

### Phase 5: 測試驗證
- [ ] 單擊父項目 → 彈出對話框
- [ ] 單擊子項目 → 直接開啟模組
- [ ] Shift 全選 → 只開啟葉節點，不彈出對話框
- [ ] Ctrl 多選 → 批量開啟選中的葉節點
- [ ] 右鍵選單顯示正確
- [ ] 所有子模組都能正確開啟

## 📝 技術細節

### 葉節點過濾邏輯
```python
# 只處理沒有子項目的項目（葉節點）
analyzable_items = [
    item for item in selected_items 
    if item.childCount() == 0
]
```

### 批量模式標記
```python
def analyze_function(self, function_name, batch_mode=False):
    # batch_mode=True 時，跳過對話框直接開啟子模組
    if not batch_mode and is_parent_item:
        show_dialog()
    else:
        open_module_directly()
```

## 🎯 預期成果
- ✅ 樹狀圖結構清晰，功能分類明確
- ✅ 用戶可以看到所有可用的子模組
- ✅ 單選和批量操作都支援
- ✅ 批量操作不會彈出對話框
- ✅ 保留原有的對話框工作流
- ✅ 為未來擴展預留空間

## 📅 時間記錄
- 開始時間: 2025-10-09
- 預計完成: 2025-10-09
- 實際完成: [待填寫]

## ✅ 驗收標準
1. 樹狀圖顯示三層架構
2. 所有子模組都可見
3. 單擊父項目彈出對話框
4. 單擊子項目直接開啟
5. Shift 全選不觸發對話框
6. 批量操作只處理葉節點
7. 無報錯，所有功能正常

## 🐛 已知問題
- 無

## 📌 備註
- 此重構不影響現有功能
- 保持向後兼容
- 遵循 API-ONLY 模式政策
