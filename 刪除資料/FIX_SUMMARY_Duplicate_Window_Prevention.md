# 🔧 Pitstop 重複視窗問題修復摘要

**修復日期**: 2025-10-06  
**問題嚴重性**: 🔴 CRITICAL  
**修復狀態**: ✅ **已完成，待測試驗證**

---

## 📌 問題總結

在某些條件下按下 "Update All Analysis" 或使用批次分析功能時，系統會創建**多個相同的 Pitstop 分析模組視窗**，嚴重違反 MDI 單一視窗管理原則。

**證據**:
- 用戶報告畫面出現 **3個** Pitstop 視窗
- 日誌顯示相同視窗標題被創建3次（17:52:10, 17:57:12, 18:00:26）

---

## 🔍 根本原因

### 主要原因
`f1t_gui_main.py::create_analysis_window()` 方法在創建新視窗前**沒有檢查 MDI 區域中是否已存在相同模組的視窗**。

### 觸發路徑
1. **批次分析** (`analyze_multiple_functions`) → 為每個選中的模組調用 `analyze_function()`
2. `analyze_function()` → 調用 `create_analysis_window()`
3. `create_analysis_window()` → **直接創建新視窗，無重複檢查** ❌

---

## 🛠️ 實施的修復

### 修復 1: 重複視窗檢查機制

**檔案**: `f1t_gui_main.py`  
**位置**: `create_analysis_window()` 方法開始處

**修改內容**:
```python
# 🔧 [FIX] 重複視窗檢查機制 - 防止創建多個相同視窗
# 步驟1: 獲取預期的視窗標題模式
expected_title_patterns = self._get_expected_window_title_pattern(
    function_name, 
    current_year, 
    current_race, 
    current_session
)

# 步驟2: 檢查MDI區域中是否已存在相同視窗
existing_window = self._find_existing_window(mdi_area, expected_title_patterns)

if existing_window:
    # 找到已存在的視窗，聚焦而不是創建新視窗
    logger.info(f"[DUPLICATE_CHECK] ✅ 找到已存在視窗: {existing_window.windowTitle()}")
    logger.info(f"[DUPLICATE_CHECK] ⏭️ 跳過創建,將聚焦現有視窗")
    
    # 激活並聚焦現有視窗
    mdi_area.setActiveSubWindow(existing_window)
    existing_window.show()
    existing_window.raise_()
    existing_window.setFocus()
    
    return  # 🚫 不創建新視窗，直接返回

logger.info(f"[DUPLICATE_CHECK] ✅ 未找到重複視窗，繼續創建: {function_name}")
```

**效果**:
- ✅ 檢測到重複視窗時，直接聚焦現有視窗而非創建新視窗
- ✅ 記錄詳細日誌，便於調試
- ✅ 支援多語言視窗標題匹配

---

### 修復 2: 視窗標題模式生成器

**新增方法**: `_get_expected_window_title_pattern()`

**功能**:
- 根據功能名稱、年份、賽事、賽段生成預期的視窗標題模式
- 支援多語言（中文、英文、日文）
- 使用萬用字元（`*`）匹配日期變化

**支援的模組**:
- Pitstop Analysis (進站分析 / ピットストップ分析)
- Accident Analysis (事故分析)
- Track Analysis (賽道分析 / トラック分析)
- Rain Analysis (降雨分析 / 雨況分析)
- Tire Analysis (輪胎分析 / タイヤ分析)
- Speed/Brake/Throttle/Gear/RPM/Acceleration Analysis

**範例輸出**:
```python
# 輸入: function_name="Pitstop Analysis", year="2025", race="Australia", session="R"
# 輸出:
[
    "Pitstop Analysis_2025_Australia*_R",
    "Pitstop Analysis - 2025 Australia*R",
    "ピットストップ分析_2025_Australia*_R",
    "進站分析_2025_Australia*_R",
    ...
]
```

---

### 修復 3: 視窗查找器

**新增方法**: `_find_existing_window()`

**功能**:
- 在 MDI 區域中查找匹配標題模式的現有視窗
- 使用 `fnmatch` 模組進行萬用字元匹配
- 返回第一個匹配的視窗（如果存在）

**匹配邏輯**:
```python
import fnmatch

for sub_window in mdi_area.subWindowList():
    window_title = sub_window.windowTitle()
    
    for pattern in title_patterns:
        if fnmatch.fnmatch(window_title, pattern):
            # 找到匹配！
            return sub_window

return None  # 未找到匹配
```

---

## 📊 影響範圍

### 受益的模組
所有通過 `create_analysis_window` 創建的分析模組：

1. ✅ Pitstop Analysis
2. ✅ Accident Analysis
3. ✅ Track Analysis
4. ✅ Rain Analysis
5. ✅ Tire Analysis
6. ✅ Speed/Brake/Throttle/Gear/RPM/Acceleration Analysis

### 不受影響的模組
- 遙測分析概覽（使用不同的創建流程）
- 圈速箱型圖（使用專門的創建方法）

---

## 🧪 測試驗證

**測試計畫**: 詳見 `TEST_PLAN_Duplicate_Window_Fix.md`

### 關鍵測試案例

1. **批次分析重複檢查** ⏳
   - 執行批次分析2次
   - 預期: 第2次不創建新視窗

2. **雙擊功能樹重複檢查** ⏳
   - 雙擊同一項目2次
   - 預期: 第2次聚焦現有視窗

3. **不同參數允許多視窗** ⏳
   - 切換年份/賽事後創建視窗
   - 預期: 允許創建新視窗

4. **日誌驗證** ⏳
   - 檢查日誌中的重複檢查訊息
   - 預期: 出現 `[DUPLICATE_CHECK]` 日誌

---

## 📝 技術細節

### 檔案修改清單

| 檔案 | 修改類型 | 行數變化 |
|-----|---------|---------|
| `f1t_gui_main.py` | 功能增強 | +約100行 |

### 新增/修改的方法

1. **create_analysis_window()** - 添加重複檢查邏輯
2. **_get_expected_window_title_pattern()** - 新增方法
3. **_find_existing_window()** - 新增方法

### 依賴項

- **標準庫**: `fnmatch` (已包含在 Python 標準庫)
- **無新增第三方依賴**

---

## 🎯 驗證檢查清單

開發者自檢:
- [x] 程式碼已編寫並提交
- [x] 添加詳細日誌記錄
- [x] 處理邊緣案例（多語言、不同參數）
- [x] 創建測試計畫
- [x] 創建問題報告文件

測試人員驗證:
- [ ] 測試案例1: 批次分析重複檢查
- [ ] 測試案例2: 雙擊重複檢查
- [ ] 測試案例3: 不同參數多視窗
- [ ] 測試案例4: Update All Analysis
- [ ] 測試案例5: 多語言匹配
- [ ] 測試案例6: 日誌驗證
- [ ] 回歸測試: 所有模組正常工作

---

## 🚀 部署建議

### 部署步驟
1. ✅ 備份當前版本的 `f1t_gui_main.py`
2. ✅ 應用修復（已完成）
3. ⏳ 執行完整測試計畫
4. ⏳ 驗證所有測試案例通過
5. ⏳ 更新用戶文檔（如需要）
6. ⏳ 發布更新

### 回退計畫
如果發現嚴重問題，可以：
1. 恢復備份的 `f1t_gui_main.py`
2. 或暫時禁用重複檢查（保留日誌記錄）

---

## 📚 相關文件

1. **問題報告**: `CRITICAL_BUG_REPORT_Duplicate_Pitstop_Windows.md`
2. **測試計畫**: `TEST_PLAN_Duplicate_Window_Fix.md`
3. **本摘要**: `FIX_SUMMARY_Duplicate_Window_Prevention.md`

---

## 💡 後續改進建議

### 短期（1-2週）
1. 完成所有測試驗證
2. 監控用戶反饋
3. 修復任何發現的邊緣案例

### 中期（1個月）
1. 實施視窗 ID 系統（更精確的重複檢測）
2. 添加全域視窗註冊表
3. 優化批次分析流程

### 長期（3個月）
1. 統一所有模組的視窗管理策略
2. 提供 "允許重複視窗" 配置選項
3. 實現視窗快速切換功能

---

**修復人員**: GitHub Copilot  
**審查人員**: 待確認  
**批准人員**: 待確認  
**最後更新**: 2025-10-06
