# 全部子模組遷移到模組工廠 - 批次遷移計劃

**日期**: 2025-10-09  
**目標**: 一次性將剩餘 4 個子模組全部遷移到模組工廠

---

## 📋 遷移清單

### 待遷移模組

| # | 模組名稱 | 當前代碼行數 | 工廠支援 | 難度 | 預計時間 |
|---|---------|------------|---------|------|---------|
| 1 | **Throttle Box Plot** | ~60 行 (Line 4571-4589) | ✅ Line 9616-9674 | ⭐⭐ | 5 分鐘 |
| 2 | **Throttle Line Chart** | ~55 行 (Line 4591-4655) | ✅ Line 9676-9734 | ⭐⭐ | 5 分鐘 |
| 3 | **Lap Time Box Plot** | ~20 行 (Line 4560-4570) | ❌ 無，需添加 | ⭐⭐⭐ | 10 分鐘 |
| 4 | **Ranking Table** | ~15 行 (Line 4683-4695) | ❌ 無，需添加 | ⭐⭐⭐ | 10 分鐘 |

**總計**: 150 行 → 12 行（減少 92%）  
**總時間**: ~30 分鐘

---

## 🔍 現有工廠支援分析

### ✅ 模組 1-2: Throttle Box Plot & Line Chart

**工廠代碼已存在** (Line 9616-9734):

```python
# Line 9616: Throttle Box Plot
elif module_type == "throttle_box_plot":
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module import (
            ThrottleBoxPlotModuleAdapter
        )
        # ... 工廠邏輯 ...

# Line 9676: Throttle Line Chart  
elif module_type == "throttle_line_chart":
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import (
            ThrottleLineChartModuleAdapter
        )
        # ... 工廠邏輯 ...
```

**別名映射** (Line 9338-9347):
```python
"throttle_box_plot": [
    ("throttle_box_plot", "Throttle Box Plot"),
    ("throttle_box_plot_analysis", "Throttle Box Plot Analysis"),
    "油門箱型圖",
    "Throttle Box Plot",
],
"throttle_line_chart": [
    ("throttle_line_chart", "Throttle Line Chart"),
    "油門折線圖",
],
```

**問題**: 缺少中文別名 `"油門箱線圖"` 和 `"油門折線圖"`

---

### ❌ 模組 3: Lap Time Box Plot

**工廠代碼**: 不存在，需要添加

**現有實現**: 
- 使用專用方法 `_create_detailed_lap_boxplot_window()` (Line 9114)
- 類：`LapTimeBoxPlotAnalysis`

**需要添加**:
```python
elif module_type == "laptime_box_plot":
    try:
        from modules.gui.driver_race.detailed_lap_analysis.lap_time_boxplot import (
            LapTimeBoxPlotAnalysis
        )
        # 創建 MDI 實例
        module = LapTimeBoxPlotAnalysis(parent=self)
        module.parameter_provider = parameter_provider
        
        # 設置參數
        if parameter_provider:
            current_year = int(parameter_provider.get_current_year())
            current_race = parameter_provider.get_current_race()
            current_session = parameter_provider.get_current_session()
            
            module.current_year = str(current_year)
            module.current_race = current_race
            module.current_session = current_session
        
        # 初始化
        if not module.initialize_module():
            return None
        
        return self._mark_module_factory_type(module, module_type)
```

---

### ❌ 模組 4: Ranking Table

**工廠代碼**: 不存在，需要添加

**現有實現**:
- 使用專用方法 `_create_ideal_lap_ranking_window()` (Line 9191)
- 類：`IdealLapRankingTableMDI`

**需要添加**:
```python
elif module_type == "ideal_lap_ranking":
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table_mdi import (
            IdealLapRankingTableMDI
        )
        # 創建 MDI 實例
        module = IdealLapRankingTableMDI(parent=self)
        module.parameter_provider = parameter_provider
        
        # 設置參數
        if parameter_provider:
            current_year = int(parameter_provider.get_current_year())
            current_race = parameter_provider.get_current_race()
            current_session = parameter_provider.get_current_session()
            
            module.current_year = str(current_year)
            module.current_race = current_race
            module.current_session = current_session
        
        # 初始化
        if not module.initialize_module():
            return None
        
        return self._mark_module_factory_type(module, module_type)
```

---

## 🎯 實施步驟

### 步驟 1: 更新別名映射 ⭐⭐⭐⭐⭐

#### 1.1 Throttle Box Plot (Line 9338-9344)
```python
# 添加 "油門箱線圖" 別名
"throttle_box_plot": [
    ("throttle_box_plot", "Throttle Box Plot"),
    ("throttle_box_plot_analysis", "Throttle Box Plot Analysis"),
    "油門箱型圖",
    "油門箱線圖",  # ← 新增
    "Throttle Box Plot",
],
```

#### 1.2 Throttle Line Chart (Line 9345-9347)
```python
# 別名已正確
"throttle_line_chart": [
    ("throttle_line_chart", "Throttle Line Chart"),
    "油門折線圖",  # ✅ 已有
],
```

#### 1.3 Lap Time Box Plot (新增)
```python
"laptime_box_plot": [
    ("laptime_box_plot", "Lap Time Box Plot"),
    ("lap_time_boxplot", "Lap Time BoxPlot"),
    "圈速箱線圖",
    "圈速箱型圖",
],
```

#### 1.4 Ranking Table (新增)
```python
"ideal_lap_ranking": [
    ("ideal_lap_ranking", "Ideal Lap Ranking"),
    ("ranking_table", "Ranking Table"),
    "排名表格",
    "理想圈排名",
],
```

---

### 步驟 2: 添加工廠處理邏輯 ⭐⭐⭐⭐

#### 2.1 Lap Time Box Plot 工廠處理

**插入位置**: 在 `driverlap_analysis` 處理之後 (Line ~9950)

```python
elif module_type == "laptime_box_plot":
    try:
        print(f"[DEBUG] [MODULE_FACTORY] 開始創建圈速箱線圖模組...")
        from modules.gui.driver_race.detailed_lap_analysis.lap_time_boxplot import (
            LapTimeBoxPlotAnalysis
        )
        print(f"[OK] [MODULE_FACTORY] 圈速箱線圖 MDI 導入成功")
        
        # 創建 MDI 實例
        module = LapTimeBoxPlotAnalysis(parent=self)
        print(f"✅ [MODULE_FACTORY] 圈速箱線圖 MDI 實例創建成功")
        
        # 設置參數提供者
        module.parameter_provider = parameter_provider
        
        # 設置參數
        if parameter_provider:
            current_year = int(parameter_provider.get_current_year())
            current_race = parameter_provider.get_current_race()
            current_session = parameter_provider.get_current_session()
            
            print(f"[INIT] [MODULE_FACTORY] 圈速箱線圖模組參數預設為: {current_year} {current_race} {current_session}")
            
            module.current_year = str(current_year)
            module.current_race = current_race
            module.current_session = current_session
        
        # 初始化模組
        if not module.initialize_module():
            print(f"[ERROR] [MODULE_FACTORY] 圈速箱線圖模組初始化失敗")
            return None
        
        print(f"[OK] [MODULE_FACTORY] 圈速箱線圖模組初始化成功")
        return self._mark_module_factory_type(module, module_type)
    except Exception as e:
        print(f"[ERROR] [MODULE_FACTORY] 圈速箱線圖模組創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return None
```

#### 2.2 Ranking Table 工廠處理

**插入位置**: 在 Lap Time Box Plot 之後

```python
elif module_type == "ideal_lap_ranking":
    try:
        print(f"[DEBUG] [MODULE_FACTORY] 開始創建理想圈排名表格模組...")
        from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table_mdi import (
            IdealLapRankingTableMDI
        )
        print(f"[OK] [MODULE_FACTORY] 理想圈排名表格 MDI 導入成功")
        
        # 創建 MDI 實例
        module = IdealLapRankingTableMDI(parent=self)
        print(f"✅ [MODULE_FACTORY] 理想圈排名表格 MDI 實例創建成功")
        
        # 設置參數提供者
        module.parameter_provider = parameter_provider
        
        # 設置參數
        if parameter_provider:
            current_year = int(parameter_provider.get_current_year())
            current_race = parameter_provider.get_current_race()
            current_session = parameter_provider.get_current_session()
            
            print(f"[INIT] [MODULE_FACTORY] 理想圈排名表格模組參數預設為: {current_year} {current_race} {current_session}")
            
            module.current_year = str(current_year)
            module.current_race = current_race
            module.current_session = current_session
        
        # 初始化模組
        if not module.initialize_module():
            print(f"[ERROR] [MODULE_FACTORY] 理想圈排名表格模組初始化失敗")
            return None
        
        print(f"[OK] [MODULE_FACTORY] 理想圈排名表格模組初始化成功")
        return self._mark_module_factory_type(module, module_type)
    except Exception as e:
        print(f"[ERROR] [MODULE_FACTORY] 理想圈排名表格模組創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return None
```

---

### 步驟 3: 簡化 analyze_function() 調用 ⭐⭐⭐⭐⭐

#### 3.1 Throttle Box Plot (Line 4571-4589)

**修改前** (60+ 行):
```python
elif clean_name in ["Throttle Box Plot", "油門箱線圖"]:
    print(f"[TREE_CLICK] 開啟油門箱線圖（MDI 模式）")
    try:
        from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
            ThrottleBoxPlotAnalysis
        )
        # ... 60+ 行代碼 ...
```

**修改後** (3 行):
```python
elif clean_name in ["Throttle Box Plot", "油門箱線圖"]:
    print(f"[TREE_CLICK] 開啟油門箱線圖（模組工廠模式）")
    self.main_window.create_analysis_window(clean_name)
```

#### 3.2 Throttle Line Chart (Line 4591-4655)

**修改前** (55+ 行):
```python
elif clean_name in ["Throttle Line Chart", "油門折線圖"]:
    print(f"[TREE_CLICK] 開啟油門折線圖（MDI 模式）")
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis import (
            ThrottleLineChartModule
        )
        # ... 55+ 行代碼 ...
```

**修改後** (3 行):
```python
elif clean_name in ["Throttle Line Chart", "油門折線圖"]:
    print(f"[TREE_CLICK] 開啟油門折線圖（模組工廠模式）")
    self.main_window.create_analysis_window(clean_name)
```

#### 3.3 Lap Time Box Plot (Line 4560-4570)

**修改前** (10+ 行):
```python
elif clean_name in ["Lap Time Box Plot", "圈速箱線圖"]:
    print(f"[TREE_CLICK] 開啟圈速箱線圖（直接模式）")
    try:
        # 首次開啟時移除歡迎頁面
        self.main_window.check_and_remove_welcome_page()
        
        self.main_window._create_detailed_lap_boxplot_window(...)
        # ...
```

**修改後** (3 行):
```python
elif clean_name in ["Lap Time Box Plot", "圈速箱線圖"]:
    print(f"[TREE_CLICK] 開啟圈速箱線圖（模組工廠模式）")
    self.main_window.create_analysis_window(clean_name)
```

#### 3.4 Ranking Table (Line 4683-4695)

**修改前** (12+ 行):
```python
elif clean_name in ["Ranking Table", "排名表格"]:
    print(f"[TREE_CLICK] 開啟理想圈排名表格（直接模式）")
    try:
        self.main_window._create_ideal_lap_ranking_window(...)
        # ...
```

**修改後** (3 行):
```python
elif clean_name in ["Ranking Table", "排名表格"]:
    print(f"[TREE_CLICK] 開啟理想圈排名表格（模組工廠模式）")
    self.main_window.create_analysis_window(clean_name)
```

---

## 📊 預期收益

### 代碼減少

| 模組 | 修改前 | 修改後 | 減少 | 減少比例 |
|------|-------|-------|------|---------|
| Throttle Box Plot | 60 行 | 3 行 | -57 行 | 95.0% |
| Throttle Line Chart | 55 行 | 3 行 | -52 行 | 94.5% |
| Lap Time Box Plot | 12 行 | 3 行 | -9 行 | 75.0% |
| Ranking Table | 12 行 | 3 行 | -9 行 | 75.0% |
| **總計** | **139 行** | **12 行** | **-127 行** | **91.4%** |

### 新增代碼

| 項目 | 行數 |
|------|------|
| 別名映射更新 | +8 行 |
| Lap Time Box Plot 工廠邏輯 | +40 行 |
| Ranking Table 工廠邏輯 | +40 行 |
| **總計新增** | **+88 行** |

### 淨收益

**淨減少**: 139 - 12 + 88 = **-63 行** (代碼減少 45%)

---

## ✅ 預期功能增強

### 所有模組將獲得

1. ✅ 自動 welcome 頁面處理
2. ✅ 統一錯誤處理
3. ✅ 模組類型標記 (`_factory_type`)
4. ✅ 可能的重複視窗檢查
5. ✅ 詳細的調試日誌
6. ✅ 架構一致性

---

## 🧪 測試計劃

### 測試矩陣

| 模組 | 測試項目 | 預期結果 |
|------|---------|---------|
| **Throttle Box Plot** | 點擊樹節點 | 視窗開啟，welcome 頁面移除 |
| | 日誌檢查 | 看到 `[MODULE_FACTORY]` 標記 |
| | 參數傳遞 | 2025 Australia R |
| **Throttle Line Chart** | 點擊樹節點 | 視窗開啟，welcome 頁面移除 |
| | 日誌檢查 | 看到 `[MODULE_FACTORY]` 標記 |
| | 參數傳遞 | 2025 Australia R |
| **Lap Time Box Plot** | 點擊樹節點 | 視窗開啟，welcome 頁面移除 |
| | 日誌檢查 | 看到 `[MODULE_FACTORY]` 標記 |
| | 參數傳遞 | 2025 Australia R |
| **Ranking Table** | 點擊樹節點 | 視窗開啟，welcome 頁面移除 |
| | 日誌檢查 | 看到 `[MODULE_FACTORY]` 標記 |
| | 參數傳遞 | 2025 Australia R |

---

## ⚠️ 潛在風險

### 風險 1: Throttle 模組使用 Adapter

**觀察**: 工廠使用 `ThrottleBoxPlotModuleAdapter` 和 `ThrottleLineChartModuleAdapter`  
**直接模式使用**: `ThrottleBoxPlotAnalysis` 和 `ThrottleLineChartModule`

**緩解**: 
- 檢查 Adapter 是否正確包裝了 MDI 類
- 如果不行，修改工廠使用 MDI 類（與 Detailed Lap Table 一致）

---

### 風險 2: Lap Time Box Plot 和 Ranking Table 初始化

**問題**: 可能有特殊的初始化需求

**緩解**:
- 參考 `_create_detailed_lap_boxplot_window()` 和 `_create_ideal_lap_ranking_window()` 的邏輯
- 確保工廠邏輯與專用方法一致

---

## 🚀 執行順序

1. **步驟 1**: 更新別名映射（5 分鐘）
   - Throttle Box Plot: 添加 "油門箱線圖"
   - Lap Time Box Plot: 新增別名組
   - Ranking Table: 新增別名組

2. **步驟 2**: 添加工廠邏輯（15 分鐘）
   - Lap Time Box Plot 工廠處理
   - Ranking Table 工廠處理

3. **步驟 3**: 簡化調用（5 分鐘）
   - 修改 4 個 elif 分支為統一調用

4. **步驟 4**: 語法驗證（1 分鐘）

5. **步驟 5**: 功能測試（5 分鐘）
   - 依次測試 4 個模組

**總計**: ~30 分鐘

---

**計劃創建時間**: 2025-10-09  
**預計完成時間**: ~30 分鐘  
**下一步**: 開始執行步驟 1（更新別名映射）
