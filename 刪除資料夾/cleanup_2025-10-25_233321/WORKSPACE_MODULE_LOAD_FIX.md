# Workspace 模組載入修復報告 - Pitstop / Accident / Tire

## 📋 問題描述

**用戶報告**：Workspace 無法載入以下模組的視窗：
- ❌ Pitstop Analysis（進站分析）
- ❌ Accident Analysis（事故分析）
- ❌ Tire Strategy Analysis（輪胎策略分析）

**症狀**：
- 手動開啟模組 → ✅ 正常運作
- 從 Workspace 載入 → ❌ 視窗無法創建
- 其他模組（如 Rain Analysis）→ ✅ 正常載入

---

## 🔍 根本原因分析

### 問題核心：`analysis_type` 與別名不匹配

**Workspace 載入流程**：
```
1. Workspace 保存時記錄 analysis_module.analysis_type
   ↓
2. Workspace 載入時查找 module_alias_groups[analysis_type]
   ↓
3. 使用映射創建對應的模組
```

**問題所在**：

| 模組 | 模組的 `analysis_type` | `module_alias_groups` 的 key | 是否匹配 |
|------|----------------------|----------------------------|---------|
| Pitstop Analysis | `"pitstop"` | `"pitstop_analysis"` | ❌ 不匹配 |
| Accident Analysis | `"accident"` | `"accident_analysis"` | ❌ 不匹配 |
| Tire Strategy | `"tire"` | `"tire_analysis"` | ❌ 不匹配 |
| Rain Analysis | `"rain_analysis"` | `"rain_analysis"` | ✅ 匹配 |

---

## 🔍 詳細調查

### 步驟 1：檢查模組的 `analysis_type` 屬性

**Pitstop Analysis**：
```python
# modules/gui/pitstop_analysis/pitstop_analysis_mdi.py:1541
self.analysis_type = "pitstop"  # ⚠️ 簡短形式
```

**Accident Analysis**：
```python
# modules/gui/accident_analysis/accident_analysis_mdi.py:941
self.analysis_type = "accident"  # ⚠️ 簡短形式
```

**Tire Strategy**：
```python
# modules/gui/tire_analysis/tire_analysis_module.py:51
self.analysis_type = 'tire'  # ⚠️ 簡短形式
```

### 步驟 2：檢查 Workspace 如何保存 `analysis_type`

**保存流程**（`core/workspace_serializer.py`）：
```python
# Line 231-233
if hasattr(analysis_module, 'analysis_type'):
    window_type = analysis_module.analysis_type  # ✅ 直接讀取
    print(f"[WORKSPACE] ✅ 直接識別模組類型: '{window_type}'")
```

**結果**：Workspace 保存時記錄的是 `"pitstop"`、`"accident"`、`"tire"`

### 步驟 3：檢查 Workspace 如何載入模組

**載入流程**（`f1t_gui_main.py`）：
```python
# Line 12187-12198 - module_alias_groups 字典
"pitstop_analysis": [  # ❌ key 是 "pitstop_analysis"
    ("pitstop_analysis", "Pitstop Analysis"),
    "進站分析",
    ...
],
```

**問題**：
- Workspace 查找 `module_alias_groups["pitstop"]` → ❌ **找不到！**
- 因為 key 是 `"pitstop_analysis"`，不是 `"pitstop"`

---

## ✅ 解決方案

### 修復：添加簡短形式的別名

在 `module_alias_groups` 中為每個模組添加其 `analysis_type` 作為別名。

---

### 修復 1：Pitstop Analysis

**文件**：`f1t_gui_main.py` (Line 12187-12195)

**修正代碼**：
```python
"pitstop_analysis": [
    ("pitstop_analysis", "Pitstop Analysis"),
    "pitstop",  # ✅ 新增：Workspace 使用的原始 key（模組的 analysis_type）
    "進站分析",
    "Pitstop Analysis",
    "ピットストップ分析",
],
```

**效果**：
- Workspace 查找 `module_alias_groups["pitstop"]` → ✅ **找到！** → 映射到 `"pitstop_analysis"`
- 模組工廠創建 `PitstopAnalysisModule` → ✅ 視窗成功載入

---

### 修復 2：Accident Analysis

**文件**：`f1t_gui_main.py` (Line 12196-12201)

**修正代碼**：
```python
"accident_analysis": [
    ("accident_analysis", "Accident Analysis"),
    "accident",  # ✅ 新增：Workspace 使用的原始 key（模組的 analysis_type）
    "事故分析",
    "Accident Analysis",
],
```

---

### 修復 3：Tire Strategy Analysis

**文件**：`f1t_gui_main.py` (Line 12255-12262)

**修正代碼**：
```python
"tire_analysis": [
    ("tire_analysis", "Tire Analysis"),
    ("tire_strategy_analysis", "Tire Strategy Analysis"),
    "tire",  # ✅ 新增：Workspace 使用的原始 key（模組的 analysis_type）
    "輪胎分析",
    "輪胎策略分析",
    "タイヤ戦略分析",
],
```

---

## 📊 修復前後對比

### 修復前（❌ 錯誤流程）

```
Workspace 保存：
  → 記錄 analysis_type = "pitstop"
  → 保存到 workspace.json

Workspace 載入：
  → 查找 module_alias_groups["pitstop"]
  → ❌ KeyError: 'pitstop' not found
  → 模組創建失敗
  → 視窗無法載入
```

### 修復後（✅ 正確流程）

```
Workspace 保存：
  → 記錄 analysis_type = "pitstop"
  → 保存到 workspace.json

Workspace 載入：
  → 查找 module_alias_groups["pitstop"]
  → ✅ 找到別名 "pitstop" → 映射到 "pitstop_analysis"
  → 模組工廠創建 PitstopAnalysisModule
  → ✅ 視窗成功載入
```

---

## 🧪 測試建議

### 測試場景 1：保存並載入 Pitstop Analysis

```markdown
步驟：
1. 手動開啟 Pitstop Analysis 模組
2. 設置參數（Year: 2025, Race: Australia, Session: R）
3. 保存 Workspace（命名為 "Test_Pitstop"）
4. 關閉所有視窗
5. 載入 "Test_Pitstop" Workspace
6. ✅ 驗證：Pitstop Analysis 視窗成功創建，標題和參數正確
```

### 測試場景 2：保存並載入 Accident Analysis

```markdown
步驟：
1. 手動開啟 Accident Analysis 模組
2. 設置參數（Year: 2025, Race: Japan, Session: R）
3. 保存 Workspace（命名為 "Test_Accident"）
4. 關閉所有視窗
5. 載入 "Test_Accident" Workspace
6. ✅ 驗證：Accident Analysis 視窗成功創建，標題和參數正確
```

### 測試場景 3：保存並載入 Tire Strategy

```markdown
步驟：
1. 手動開啟 Tire Strategy Analysis 模組
2. 設置參數（Year: 2025, Race: Monaco, Session: R）
3. 保存 Workspace（命名為 "Test_Tire"）
4. 關閉所有視窗
5. 載入 "Test_Tire" Workspace
6. ✅ 驗證：Tire Strategy 視窗成功創建，標題和參數正確
```

### 測試場景 4：混合多模組 Workspace

```markdown
步驟：
1. 同時開啟以下模組：
   - Rain Analysis
   - Pitstop Analysis
   - Accident Analysis
   - Tire Strategy Analysis
   - Track Analysis
2. 為每個模組設置不同參數
3. 保存 Workspace（命名為 "Multi_Module_Test"）
4. 關閉所有視窗
5. 載入 "Multi_Module_Test" Workspace
6. ✅ 驗證：所有 5 個視窗都成功創建，參數正確
```

---

## 🔍 與 Rain Analysis 修復的對比

### Rain Analysis 的修復（之前）

**問題**：`analysis_type = "rain_analysis"` 但 Workspace 保存時使用 `"rain_weather"`

**修復方式**：
```python
"rain_analysis": [
    ("rain_analysis", "Rain Analysis"),
    "rain_weather",  # ✅ 添加 Workspace 使用的 key
    ...
],
```

### Pitstop / Accident / Tire 的修復（本次）

**問題**：`analysis_type` 使用簡短形式（`"pitstop"`），但 `module_alias_groups` key 使用完整形式（`"pitstop_analysis"`）

**修復方式**：
```python
"pitstop_analysis": [
    ("pitstop_analysis", "Pitstop Analysis"),
    "pitstop",  # ✅ 添加模組的 analysis_type
    ...
],
```

**共同模式**：
- 都是 `analysis_type` 與 `module_alias_groups` key 不匹配
- 都通過添加別名解決

---

## 📈 修復狀態總覽

### 已修復模組

| 模組 | `analysis_type` | 添加的別名 | 狀態 | 測試 |
|------|----------------|----------|------|------|
| Rain Analysis | `rain_analysis` | `rain_weather` | ✅ 已修復 | ✅ 已驗證 |
| Pitstop Analysis | `pitstop` | `pitstop` | ✅ 已修復 | ⏳ 待測試 |
| Accident Analysis | `accident` | `accident` | ✅ 已修復 | ⏳ 待測試 |
| Tire Strategy | `tire` | `tire` | ✅ 已修復 | ⏳ 待測試 |

### 其他模組狀態檢查

建議檢查以下模組是否有類似問題：

| 模組 | `analysis_type` | `module_alias_groups` key | 是否需要修復 |
|------|----------------|--------------------------|-------------|
| Track Analysis | `track_analysis` | `track_analysis` | ✅ 匹配 |
| Speed Analysis | `speed` | `speed_analysis` | ⚠️ 待檢查 |
| Throttle Analysis | `throttle` | `throttle_analysis` | ⚠️ 待檢查 |
| Brake Analysis | `brake` | `brake_analysis` | ⚠️ 待檢查 |

**建議**：批次檢查所有模組的 `analysis_type`，確保都有對應的別名。

---

## 💡 長期改進建議

### 建議 1：統一 `analysis_type` 命名規則

**問題**：目前有兩種命名風格
- 簡短形式：`"pitstop"`, `"accident"`, `"tire"`
- 完整形式：`"rain_analysis"`, `"track_analysis"`

**改進方案**：
```python
# 選項 A：統一使用完整形式（推薦）
self.analysis_type = "pitstop_analysis"
self.analysis_type = "accident_analysis"
self.analysis_type = "tire_analysis"

# 選項 B：統一使用簡短形式
self.analysis_type = "rain"
self.analysis_type = "track"
```

**優點**：
- 消除映射不匹配問題
- 代碼更一致
- 減少維護成本

---

### 建議 2：添加自動驗證機制

**實現**：在 Workspace 保存時檢查 `analysis_type` 是否在 `module_alias_groups` 中

```python
def validate_analysis_type(analysis_type: str) -> bool:
    """驗證 analysis_type 是否可以被 Workspace 載入"""
    for module_key, aliases in module_alias_groups.items():
        if analysis_type in aliases or analysis_type == module_key:
            return True
    
    # 警告：無法載入
    logger.warning(f"⚠️ analysis_type '{analysis_type}' 無法被 Workspace 載入！")
    logger.warning(f"💡 建議：在 module_alias_groups['{analysis_type}_analysis'] 中添加 '{analysis_type}' 別名")
    return False
```

---

### 建議 3：添加單元測試

**測試案例**：
```python
def test_all_analysis_types_have_aliases():
    """測試所有模組的 analysis_type 都有對應的別名"""
    
    # 收集所有模組的 analysis_type
    all_modules = [
        PitstopAnalysisModule,
        AccidentAnalysisModule,
        TireAnalysisModule,
        RainAnalysisUniversal,
        TrackAnalysisUniversal,
        # ... 其他模組
    ]
    
    for module_class in all_modules:
        instance = module_class()
        analysis_type = instance.analysis_type
        
        # 驗證能在 module_alias_groups 中找到
        found = False
        for module_key, aliases in module_alias_groups.items():
            if analysis_type in aliases or analysis_type == module_key:
                found = True
                break
        
        assert found, f"❌ {module_class.__name__} 的 analysis_type='{analysis_type}' 無法被 Workspace 載入！"
```

---

## 📎 相關文件

- **主修復報告**：`WORKSPACE_TITLE_UPDATE_FIX.md`
- **標題更新分析**：`TITLE_UPDATE_ISSUE_ANALYSIS.md`
- **此載入修復報告**：`WORKSPACE_MODULE_LOAD_FIX.md`

---

## 🎓 經驗總結

### 1. 別名映射的重要性

**教訓**：當系統使用字串標識符（如 `analysis_type`）進行映射時，必須確保：
- 標識符在所有使用位置保持一致
- 或者提供完整的別名映射

**解決方案**：
- 統一命名規則（最佳）
- 提供完整的別名映射（折衷）

---

### 2. 保存與載入的對稱性

**原則**：
```
保存時記錄什麼 → 載入時必須能識別什麼
```

如果保存 `"pitstop"`，載入時必須能識別 `"pitstop"`。

---

### 3. 調試技巧

**如何快速定位類似問題**：

```bash
# 步驟 1：找出模組的 analysis_type
grep -r "self.analysis_type" modules/gui/

# 步驟 2：檢查 module_alias_groups 是否有對應別名
grep "analysis_type_value" f1t_gui_main.py

# 步驟 3：如果沒有，添加別名
```

---

## ✅ 修復狀態

- **狀態**：✅ 已修復
- **測試**：⏳ 待測試
- **影響範圍**：Pitstop Analysis, Accident Analysis, Tire Strategy Analysis
- **向下兼容**：✅ 完全兼容（只添加別名，不改變現有邏輯）
- **日期**：2025-10-23

---

**文件版本**：1.0  
**最後更新**：2025-10-23  
**作者**：GitHub Copilot  
**狀態**：已修復，待用戶測試驗證
