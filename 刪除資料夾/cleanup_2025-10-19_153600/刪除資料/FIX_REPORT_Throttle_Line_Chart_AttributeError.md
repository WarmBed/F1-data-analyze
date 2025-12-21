# 🐛 油門折線圖 AttributeError 修復報告

## 問題總結

**症狀**：在嘗試開啟油門折線圖分析時出現 `AttributeError: 'StyleHMainWindow' object has no attribute '_get_current_year_from_tab'` 錯誤。

**錯誤訊息**：
```python
File "f1t_gui_main.py", line 8487, in _create_throttle_line_chart_window
    current_year = self._get_current_year_from_tab(current_tab)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'StyleHMainWindow' object has no attribute '_get_current_year_from_tab'
```

**根本原因**：`_create_throttle_line_chart_window()` 方法調用了不存在的輔助方法來獲取參數。

---

## 🔍 問題分析

### 錯誤位置
`f1t_gui_main.py` line 8487-8489

### 原始程式碼（有問題）
```python
# ❌ 錯誤：調用不存在的方法
current_year = self._get_current_year_from_tab(current_tab)
current_race = self._get_current_race_from_tab(current_tab)
current_session = self._get_current_session_from_tab(current_tab)
```

### 問題原因

1. **方法不存在**：
   - `_get_current_year_from_tab()`, `_get_current_race_from_tab()`, `_get_current_session_from_tab()` 這三個方法從未在 `StyleHMainWindow` 類別中定義
   - 可能是複製貼上程式碼時漏掉了相關實現

2. **不一致的模式**：
   - 系統中其他所有分析模組都使用 `MainWindowParameterProvider` 來獲取參數
   - 只有這個方法使用了不存在的私有方法

3. **缺乏參考**：
   - 開發者可能沒有參考其他已實現的模組（如圈速箱型圖、進站分析等）

---

## ✅ 修復方案

### 修改策略

**參考成功的模組實現**：
- ✅ `_create_detailed_lap_boxplot_window()` - 使用 `MainWindowParameterProvider`
- ✅ 進站分析模組 - 使用 `MainWindowParameterProvider`
- ✅ 事故分析模組 - 使用 `MainWindowParameterProvider`

### 修改內容

#### 第一部分：參數獲取（line 8487-8489）

**修改前**：
```python
current_year = self._get_current_year_from_tab(current_tab)
current_race = self._get_current_race_from_tab(current_tab)
current_session = self._get_current_session_from_tab(current_tab)
```

**修改後**：
```python
# 🔧 修復：使用 MainWindowParameterProvider 獲取參數（參考其他模組）
parameter_provider = MainWindowParameterProvider(self)
current_year = parameter_provider.get_current_year()
current_race = parameter_provider.get_current_race()
current_session = parameter_provider.get_current_session()
```

#### 第二部分：模組創建流程（完整重構）

**修改前（使用工廠模式，但實現不完整）**：
```python
# 使用模組工廠創建模組
try:
    module = self._module_factory_create(
        module_type="throttle_line_chart",
        parameter_provider=current_tab  # ❌ 錯誤：傳入 tab 而非 parameter_provider
    )
    
    if module is None:
        print("[THROTTLE_LINE] 模組創建失敗")
        return
    
    # 獲取 widget 並創建 MDI 子視窗
    widget = module.get_widget()
    window_title = module.get_window_title(self.i18n_manager)
    # ...
```

**修改後（直接創建，參考圈速箱型圖模式）**：
```python
# 獲取 MDI 區域
mdi_area = None
if isinstance(current_tab, CustomMdiArea):
    mdi_area = current_tab
else:
    for child in current_tab.findChildren(CustomMdiArea):
        mdi_area = child
        break

if mdi_area is None:
    print("[THROTTLE_LINE] 錯誤: 找不到MDI區域")
    QMessageBox.warning(self, "錯誤", "找不到MDI區域")
    return

print("[THROTTLE_LINE] 開始創建油門折線圖模組...")

try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import (
        ThrottleLineChartModule,
    )

    # 創建模組實例
    module = ThrottleLineChartModule()
    
    # 設置參數提供者
    module.parameter_provider = parameter_provider

    # 設置當前參數
    try:
        year_int = int(current_year)
    except (TypeError, ValueError):
        year_int = current_year

    module.current_year = str(year_int)
    module.current_race = current_race
    module.current_session = current_session

    print(f"[THROTTLE_LINE] 模組參數: {year_int} {current_race} {current_session}")

    # 初始化模組
    widget = module.initialize_module(
        year=year_int,
        race=current_race,
        session=current_session
    )

    if widget:
        print("[THROTTLE_LINE] ✅ 模組初始化成功")
        
        # 獲取視窗標題
        window_title = module.get_window_title(
            year=str(year_int),
            race=current_race,
            session=current_session
        )
        
        # 創建 MDI 子視窗
        sub_window = PopoutSubWindow(window_title, mdi_area, module)
        sub_window.setWidget(widget)
        
        # 設置模組的父視窗引用
        module.set_parent_window(sub_window)
        
        # 設置視窗大小
        width, height = module.get_default_size()
        sub_window.resize(width, height)
        
        # 添加到 MDI 區域
        mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        print(f"[THROTTLE_LINE] ✅ 油門折線圖視窗已創建: {window_title}")
        
    else:
        print("[THROTTLE_LINE] ❌ 模組初始化失敗")
        QMessageBox.warning(
            self,
            "初始化失敗",
            "油門折線圖模組初始化失敗\n請檢查日誌"
        )

except Exception as e:
    print(f"[THROTTLE_LINE] ❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    QMessageBox.critical(
        self,
        "創建失敗",
        f"創建油門折線圖視窗時發生錯誤:\n{str(e)}"
    )
```

---

## 🎯 修復邏輯說明

### 為何採用直接創建而非工廠模式？

1. **一致性**：
   - 圈速箱型圖 (`_create_detailed_lap_boxplot_window`) 使用直接創建
   - 這是系統中已驗證可靠的模式

2. **參數傳遞清晰**：
   ```python
   # 直接創建模式：參數傳遞明確
   module = ThrottleLineChartModule()
   module.parameter_provider = parameter_provider
   module.current_year = str(year_int)
   module.current_race = current_race
   module.current_session = current_session
   
   # 工廠模式：參數隱藏在工廠內部，不易追蹤
   module = self._module_factory_create(
       module_type="throttle_line_chart",
       parameter_provider=current_tab  # ❌ 還傳錯了！
   )
   ```

3. **錯誤處理完整**：
   - 直接創建可以在每個步驟添加詳細的錯誤檢查
   - 工廠模式將錯誤隱藏在內部

4. **調試方便**：
   - 直接創建：可以在每個步驟打印調試訊息
   - 工廠模式：需要深入工廠內部才能調試

---

## 📊 影響範圍

### 受影響的檔案
- ✅ `f1t_gui_main.py` - `_create_throttle_line_chart_window()` 方法（已修復）

### 相關模組
- ✅ `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_module.py` - 油門折線圖模組（無需修改）
- ✅ `MainWindowParameterProvider` - 參數提供者（無需修改）

### 其他檢查

已驗證其他分析模組使用正確的模式：
- ✅ 圈速箱型圖 - 使用 `MainWindowParameterProvider` ✓
- ✅ 進站分析 - 使用 `MainWindowParameterProvider` ✓
- ✅ 事故分析 - 使用 `MainWindowParameterProvider` ✓
- ✅ 遙測分析 - 使用 `MainWindowParameterProvider` ✓

---

## 🧪 測試驗證

### 測試步驟

1. **啟動 GUI**：
   ```powershell
   python f1t_gui_main.py
   ```

2. **選擇賽事參數**：
   - 年份：2025
   - 賽事：Japan
   - 會話：R

3. **開啟油門折線圖分析**：
   - 在功能樹展開「油門分析」
   - 點擊「油門折線圖」
   - 或使用右鍵選單選擇「分析」

4. **預期結果**：
   - ✅ 成功創建油門折線圖視窗
   - ✅ 視窗標題正確顯示：「油門折線圖 - 2025 Japan R」
   - ✅ 不會出現 `AttributeError`
   - ✅ 模組正確初始化，顯示載入介面

### 測試案例

**案例 1：正常創建**
```python
# 輸入：點擊油門折線圖功能
# 期望輸出：
[THROTTLE_LINE] 開始創建油門折線圖視窗...
[THROTTLE_LINE] 參數: 2025 Japan R
[THROTTLE_LINE] 開始創建油門折線圖模組...
[THROTTLE_LINE] 模組參數: 2025 Japan R
[THROTTLE_LINE] ✅ 模組初始化成功
[THROTTLE_LINE] ✅ 油門折線圖視窗已創建: 油門折線圖 - 2025 Japan R
```

**案例 2：無活動分頁**
```python
# 輸入：未選擇任何分頁時點擊功能
# 期望輸出：
[THROTTLE_LINE] 錯誤: 無活動分頁
# 顯示警告對話框：「錯誤 - 無活動分頁」
```

**案例 3：參數不完整**
```python
# 輸入：未選擇賽事資料時點擊功能
# 期望輸出：
[THROTTLE_LINE] 錯誤: 參數不完整 Year=None, Race=None, Session=None
# 顯示警告對話框：「參數錯誤 - 無法獲取當前年份、賽事或會話資訊」
```

---

## 💡 最佳實踐總結

### 1. 參數獲取統一模式
**所有分析模組都應遵循**：
```python
# ✅ 正確模式
parameter_provider = MainWindowParameterProvider(self)
current_year = parameter_provider.get_current_year()
current_race = parameter_provider.get_current_race()
current_session = parameter_provider.get_current_session()

# ❌ 錯誤模式
current_year = self._get_current_year_from_tab(tab)  # 方法不存在
```

### 2. 模組創建標準流程
```python
# 1. 導入模組類
from modules.gui.xxx.xxx_module import XxxModule

# 2. 創建實例
module = XxxModule()

# 3. 設置參數提供者
module.parameter_provider = parameter_provider

# 4. 設置當前參數
module.current_year = str(year)
module.current_race = race
module.current_session = session

# 5. 初始化模組
widget = module.initialize_module(year=year, race=race, session=session)

# 6. 創建 MDI 子視窗
if widget:
    window_title = module.get_window_title(...)
    sub_window = PopoutSubWindow(window_title, mdi_area, module)
    sub_window.setWidget(widget)
    module.set_parent_window(sub_window)
    # ...
```

### 3. 參考已驗證的實現
開發新功能時，應參考：
- ✅ `_create_detailed_lap_boxplot_window()` - 圈速箱型圖（最佳參考）
- ✅ 進站分析模組創建流程
- ✅ 事故分析模組創建流程

### 4. 錯誤處理完整性
```python
try:
    # 主要邏輯
    if not widget:
        print("❌ 初始化失敗")
        QMessageBox.warning(self, "錯誤", "詳細錯誤訊息")
        return
except Exception as e:
    print(f"❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    QMessageBox.critical(self, "錯誤", f"詳細錯誤:\n{str(e)}")
```

---

## 🔧 相關問題預防

### 檢查清單（新增功能時）

- [ ] 是否使用 `MainWindowParameterProvider` 獲取參數？
- [ ] 是否參考了已驗證的模組實現？
- [ ] 是否在每個關鍵步驟添加了錯誤處理？
- [ ] 是否添加了詳細的調試日誌輸出？
- [ ] 是否驗證了 MDI 區域存在性？
- [ ] 是否正確設置模組的參數提供者？
- [ ] 是否在初始化前設置了當前參數？

### 程式碼審查重點

1. **避免憑空調用不存在的方法**
   ```python
   # ❌ 危險：沒有檢查方法是否存在
   result = self._some_helper_method(param)
   
   # ✅ 安全：使用已知存在的標準方法
   provider = MainWindowParameterProvider(self)
   result = provider.get_current_year()
   ```

2. **參數傳遞類型檢查**
   ```python
   # ❌ 錯誤：傳入錯誤類型
   module = self._factory(parameter_provider=current_tab)  # tab 不是 provider!
   
   # ✅ 正確：傳入正確類型
   parameter_provider = MainWindowParameterProvider(self)
   module.parameter_provider = parameter_provider
   ```

---

## ✅ 修復狀態

- [x] 問題定位
- [x] 根本原因分析
- [x] 參考其他模組實現
- [x] 程式碼修復（參數獲取）
- [x] 程式碼修復（模組創建流程）
- [x] 完整性驗證
- [ ] 實際測試驗證（等待用戶測試）
- [ ] 文檔更新

---

## 📝 後續建議

### 短期
1. **測試驗證**：實際運行 GUI，測試油門折線圖功能是否正常
2. **日誌監控**：觀察是否有其他隱藏錯誤

### 中期
1. **統一模式**：檢查所有分析模組是否都使用相同的創建模式
2. **文檔更新**：更新開發者指南，明確模組創建標準流程

### 長期
1. **程式碼生成器**：創建模板工具，自動生成標準的模組創建程式碼
2. **靜態檢查**：添加 linter 規則，檢查方法調用是否存在

---

**修復時間**：2025-10-08  
**修復者**：GitHub Copilot  
**嚴重程度**：🔴 高（功能完全無法使用）  
**修復方式**：參考已驗證的實現，統一使用 `MainWindowParameterProvider`  
**驗證狀態**：待實際測試 ⏳
