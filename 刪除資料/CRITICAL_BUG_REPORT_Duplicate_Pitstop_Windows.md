# 🚨 嚴重問題報告：Pitstop 分析模組違反 MDI 規則創建多個視窗

**報告時間**: 2025-10-06  
**問題嚴重性**: 🔴 **CRITICAL** - 嚴重違反 MDI 視窗管理原則  
**影響範圍**: 所有通過批次分析創建的模組（Pitstop, Accident, Track等）

---

## 📋 問題摘要

在某些條件下按下 "Update All Analysis" 或使用批次分析功能時，系統會創建**多個相同的 Pitstop 分析模組視窗**，違反 MDI 單一視窗規則。用戶報告畫面出現3個 Pitstop 視窗。

---

## 🔍 根本原因分析

### 1. **缺少重複視窗檢查機制**

**位置**: `f1t_gui_main.py` → `create_analysis_window()` 方法 (line 8136-8300)

**問題程式碼**:
```python
def create_analysis_window(self, function_name):
    """為功能樹的分析項目創建新視窗 - 升級支援模組化架構"""
    # ... 省略前置檢查 ...
    
    # [❌ 問題] 直接創建模組，沒有檢查是否已存在
    analysis_module = self._create_analysis_module(function_name)
    
    if analysis_module:
        window_title = analysis_module.get_window_title(
            current_year_value,
            current_race_value,
            current_session_value,
        )
        analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
        
        # [❌ 問題] 直接添加到 MDI，不檢查重複
        mdi_area.addSubWindow(analysis_window)
        analysis_window.show()
```

**缺陷**:
- ❌ 沒有檢查 `mdi_area` 中是否已經存在相同模組類型的視窗
- ❌ 沒有比對視窗標題或參數（year, race, session）
- ❌ 批次分析時會為每次調用創建新視窗

---

### 2. **批次分析觸發多次創建**

**位置**: `f1t_gui_main.py` → `analyze_multiple_functions()` 方法 (line 4368-4375)

**問題程式碼**:
```python
def analyze_multiple_functions(self, items):
    """批量分析多個功能"""
    print(f"[BATCH_ANALYSIS] 開始批量分析 {len(items)} 個模組")
    
    for item in items:
        function_name = item.text(0)
        print(f"[BATCH_ANALYSIS] 正在創建: {function_name}")
        # [❌ 問題] 每次都調用 analyze_function，不檢查重複
        self.analyze_function(function_name)
```

**執行流程**:
1. 用戶選擇多個模組（例如：降雨分析、賽道分析、進站分析、事故分析）
2. 右鍵選擇 "批量執行分析"
3. 系統對每個模組調用 `analyze_function()`
4. `analyze_function()` 調用 `create_analysis_window()`
5. **每次都創建新視窗，不管是否已存在**

---

### 3. **日誌證據**

**日誌分析**: `logs/f1_gui_2025-10-06.log`

#### 第1次創建（正常初始化）
```log
2025-10-06 17:52:10 | INFO | [OK] [MODULE_FACTORY] 創建進站分析模組實例
2025-10-06 17:52:10 | INFO | [OK] [MDI] 已創建MDI子視窗: Pitstop Analysis_2025_Australia (2025-03-16)_R
```

#### 第2次創建（批次分析觸發）
```log
2025-10-06 17:57:10 | INFO | [BATCH_ANALYSIS] 開始批量分析 7 個模組
2025-10-06 17:57:12 | INFO | [BATCH_ANALYSIS] 正在創建: ピットストップ分析
2025-10-06 17:57:12 | INFO | [OK] [MODULE_FACTORY] 創建進站分析模組實例
2025-10-06 17:57:12 | INFO | [OK] [MDI] 已創建MDI子視窗: Pitstop Analysis_2025_Australia (2025-03-16)_R
```

#### 第3次創建（再次批次分析）
```log
2025-10-06 18:00:26 | INFO | [BATCH_ANALYSIS] 正在創建: Pitstop Analysis
2025-10-06 18:00:26 | INFO | [OK] [MODULE_FACTORY] 創建進站分析模組實例
2025-10-06 18:00:26 | INFO | [OK] [MDI] 已創建MDI子視窗: Pitstop Analysis_2025_Australia (2025-03-16)_R
```

**結論**: 相同的視窗標題 `Pitstop Analysis_2025_Australia (2025-03-16)_R` 被創建了3次！

---

## 🎯 影響範圍

### 受影響的模組
1. ✅ **Pitstop Analysis** (進站分析) - 用戶已確認
2. ⚠️ **Accident Analysis** (事故分析) - 高機率受影響
3. ⚠️ **Track Analysis** (賽道分析) - 高機率受影響
4. ⚠️ **Rain Analysis** (降雨分析) - 高機率受影響
5. ⚠️ **Tire Analysis** (輪胎分析) - 高機率受影響
6. ⚠️ **所有遙測分析模組** (Speed, Brake, Throttle等) - 可能受影響

### 觸發條件
1. ✅ **批次分析** - 用戶選擇多個模組右鍵執行
2. ⚠️ **重複點擊功能樹項目** - 雙擊同一項目多次
3. ⚠️ **Update All Analysis** - 可能間接觸發（需驗證）

---

## 🔧 修復方案

### 方案 A：在 `create_analysis_window` 中添加重複檢查 ✅ **推薦**

**修改位置**: `f1t_gui_main.py` line 8136

**修復邏輯**:
```python
def create_analysis_window(self, function_name):
    """為功能樹的分析項目創建新視窗 - 升級支援模組化架構"""
    print(f"[DEBUG] [CREATE_WINDOW] =============== 開始創建分析視窗 ===============")
    print(f"[DEBUG] [CREATE_WINDOW] 功能名稱: '{function_name}'")
    
    # [新增] 檢查是否為首次使用分析功能
    self.check_and_remove_welcome_page()
    
    # ... 省略特殊處理邏輯 ...
    
    # 獲取當前活動的分頁和MDI區域
    current_tab = self.tab_widget.currentWidget()
    if current_tab is None:
        return
    
    mdi_area = self._find_mdi_area(current_tab)
    if mdi_area is None:
        return

    current_year = self.year_combo.currentText()
    current_race = self.race_combo.currentText()
    current_session = self.session_combo.currentText()
    
    # 🔧 [新增] 重複視窗檢查機制
    # 步驟1: 獲取預期的視窗標題格式
    expected_title_pattern = self._get_expected_window_title_pattern(
        function_name, 
        current_year, 
        current_race, 
        current_session
    )
    
    # 步驟2: 檢查MDI區域中是否已存在相同視窗
    existing_window = self._find_existing_window(mdi_area, expected_title_pattern)
    
    if existing_window:
        # 找到已存在的視窗，聚焦而不是創建新視窗
        logger.info(f"[DUPLICATE_CHECK] ✅ 找到已存在視窗: {existing_window.windowTitle()}")
        logger.info(f"[DUPLICATE_CHECK] ⏭️ 跳過創建，將聚焦現有視窗")
        
        # 激活並聚焦現有視窗
        mdi_area.setActiveSubWindow(existing_window)
        existing_window.show()
        existing_window.raise_()
        existing_window.setFocus()
        
        # 提示用戶（可選）
        # QMessageBox.information(
        #     self, 
        #     "視窗已存在", 
        #     f"'{existing_window.windowTitle()}' 視窗已經開啟，已將其聚焦。"
        # )
        
        return  # 🚫 不創建新視窗
    
    logger.info(f"[DUPLICATE_CHECK] ✅ 未找到重複視窗，繼續創建")
    
    # ... 繼續原有的創建邏輯 ...
```

**新增輔助方法**:
```python
def _get_expected_window_title_pattern(self, function_name, year, race, session):
    """
    根據功能名稱和參數生成預期的視窗標題模式
    
    返回: str 或 list[str] - 可能的視窗標題模式
    """
    # 清理 race 參數（移除日期後綴）
    race_clean = self._get_race_key_from_display(race)
    
    # 根據功能名稱判斷模組類型
    module_mapping = {
        "Pitstop Analysis": ["Pitstop Analysis", "ピットストップ分析", "進站分析"],
        "Accident Analysis": ["Accident Analysis", "事故分析"],
        "Track Analysis": ["Track Analysis", "トラック分析", "賽道分析"],
        "Rain Analysis": ["Rain Analysis", "降雨分析", "雨況分析"],
        # ... 其他模組 ...
    }
    
    # 查找匹配的模組類型
    for key, aliases in module_mapping.items():
        for alias in aliases:
            if alias in function_name:
                # 生成所有可能的標題格式
                return [
                    f"{alias}_{year}_{race_clean}*_{session}",  # 支援萬用字元
                    f"{alias} - {year} {race_clean}*{session}",
                    f"{alias}_年份={year}_賽事={race_clean}_賽段={session}"
                ]
    
    # 無法判斷模組類型，返回基於功能名稱的通用模式
    return [f"{function_name}*{year}*{race_clean}*{session}"]

def _find_existing_window(self, mdi_area, title_patterns):
    """
    在MDI區域中查找匹配標題模式的現有視窗
    
    參數:
        mdi_area: CustomMdiArea - MDI區域
        title_patterns: str or list[str] - 標題模式（支援萬用字元）
    
    返回:
        QMdiSubWindow 或 None
    """
    import fnmatch
    
    # 確保 title_patterns 是列表
    if isinstance(title_patterns, str):
        title_patterns = [title_patterns]
    
    # 遍歷所有子視窗
    for sub_window in mdi_area.subWindowList():
        window_title = sub_window.windowTitle()
        
        # 檢查是否匹配任一模式
        for pattern in title_patterns:
            if fnmatch.fnmatch(window_title, pattern):
                logger.debug(f"[DUPLICATE_CHECK] 找到匹配視窗: '{window_title}' 匹配模式 '{pattern}'")
                return sub_window
    
    return None
```

---

### 方案 B：在 `analyze_multiple_functions` 中添加檢查

**修改位置**: `f1t_gui_main.py` line 4368

**優點**:
- 批次分析時統一檢查
- 可以在批次開始前過濾已存在的視窗

**缺點**:
- 只解決批次分析，不解決雙擊重複
- 邏輯分散，維護困難

---

### 方案 C：在 `mdi_area.addSubWindow` 前檢查

**修改位置**: `f1t_gui_main.py` line 8275

**優點**:
- 最終防線，確保不會添加重複視窗

**缺點**:
- 此時模組已經創建（浪費資源）
- 檢查位置太晚

---

## 🎯 推薦實施方案

**採用方案 A** + **方案 B 補強**

1. **主要修復**: 在 `create_analysis_window` 開始時檢查重複（方案A）
2. **批次優化**: 在 `analyze_multiple_functions` 中預先過濾（方案B）
3. **防禦性編程**: 在 `addSubWindow` 前最終檢查（方案C）

---

## 📊 測試計畫

### 測試案例1: 批次分析重複檢查
**步驟**:
1. 開啟 F1T GUI
2. 在功能樹中選擇 "Pitstop Analysis" + "Accident Analysis"
3. 右鍵選擇 "批量執行分析"
4. **再次**選擇相同模組並執行批量分析
5. **預期結果**: 第2次不創建新視窗，聚焦現有視窗

### 測試案例2: 雙擊重複檢查
**步驟**:
1. 雙擊 "Pitstop Analysis" 創建視窗
2. 再次雙擊 "Pitstop Analysis"
3. **預期結果**: 不創建新視窗，聚焦現有視窗

### 測試案例3: 不同參數允許多視窗
**步驟**:
1. Year=2025, Race=Australia 創建 Pitstop Analysis
2. 切換 Year=2024, Race=Japan
3. 再次創建 Pitstop Analysis
4. **預期結果**: 允許創建第2個視窗（參數不同）

### 測試案例4: Update All Analysis 不觸發重複
**步驟**:
1. 創建若干遙測分析視窗
2. 按下 "Update All Analysis"
3. **預期結果**: 只更新現有視窗，不創建新視窗

---

## 🚀 實施優先級

- **P0 (立即)**: 實施方案A - 核心重複檢查機制
- **P1 (短期)**: 添加測試案例1-4的單元測試
- **P2 (中期)**: 優化批次分析流程（方案B）
- **P3 (長期)**: 統一所有模組的視窗管理策略

---

## 📝 備註

- 此問題可能影響所有模組化分析視窗
- 修復後需要全面回歸測試
- 建議在 `PopoutSubWindow` 層級添加視窗 ID 機制以支援更精確的重複檢查
- 考慮添加 "允許多視窗" 配置選項（高級用戶需求）

---

**報告人**: GitHub Copilot  
**審查人**: 待確認  
**批准人**: 待確認  
