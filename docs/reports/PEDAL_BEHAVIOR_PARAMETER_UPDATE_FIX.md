# Pedal Behavior 模組參數更新修復報告

**問題**: Pedal Behavior 模組不支援主程式更換 race 時自動更新數據  
**日期**: 2026-01-12  
**狀態**: ✅ **已修復**

---

## 🚨 問題描述

當使用者在主程式中更換 race（例如從 Abu Dhabi 切換到 China）時，Pedal Behavior 模組不會自動更新數據，而其他模組（如 Rain Analysis、Track Analysis）都能正常更新。

### 問題表現
- ✅ 其他模組（Rain Analysis、Traffic Analysis）正常更新
- ❌ Pedal Behavior 模組保持舊的數據
- ❌ 需要手動關閉並重新開啟模組才能載入新數據

---

## 🔍 根本原因分析

### 1. 系統參數更新機制

F1T GUI 使用 `parameter_provider` 系統來同步主程式與各個分析模組的參數：

```
主程式 (f1t_gui_main.py)
    ↓ 
parameter_provider
    ↓ 
各分析模組 (通過 update_lap_parameters)
```

**關鍵連接點**: 模組必須在創建時設置 `parameter_provider` 才能接收更新

### 2. 問題定位

檢查 `windows/managers/analysis_module_creator.py` 中的工廠創建邏輯：

**其他正常模組的模式** (例如 Traffic Timeline):
```python
# 創建模組實例
module = TrafficTimelineAnalysis(
    year=current_year,
    race=current_race,
    session=current_session
)

# ✅ 設置參數提供者
module.parameter_provider = parameter_provider  # 關鍵！

return self.main_window._mark_module_factory_type(module, module_type)
```

**Pedal Behavior 的錯誤模式** (Lines 1987-2007):
```python
# 創建模組實例
module = PedalBehaviorAnalysisMDI(
    year=current_year,
    race=current_race,
    session=current_session
)

# ❌ 缺少這一行！
# module.parameter_provider = parameter_provider

return self.main_window._mark_module_factory_type(module, module_type)
```

**結果**: Pedal Behavior 模組沒有 `parameter_provider`，因此無法接收主程式的參數更新信號。

---

## ✅ 修復方案

### 修復內容

在 `windows/managers/analysis_module_creator.py` (Line ~2005) 添加缺失的設置：

```python
# 創建模組實例
module = PedalBehaviorAnalysisMDI(
    year=current_year,
    race=current_race,
    session=current_session
)
logger.debug(f"[OK] [MODULE_FACTORY] Pedal Behavior Analysis 模組實例創建成功")

# ✅ 設置參數提供者（關鍵！用於接收主程式參數更新）
module.parameter_provider = parameter_provider

logger.debug(f"[OK] [MODULE_FACTORY] Pedal Behavior Analysis 模組初始化成功")
return self.main_window._mark_module_factory_type(module, module_type)
```

### 修復的檔案

- `windows/managers/analysis_module_creator.py` (Line 1987-2012)

---

## 🎯 修復效果

### 修復前
```
用戶操作: 主程式切換 race (Abu Dhabi → China)
    ↓
parameter_provider 發送更新信號
    ↓
Pedal Behavior 模組: ❌ 無法接收（沒有 parameter_provider）
    ↓
結果: 數據不更新，顯示舊的 Abu Dhabi 數據
```

### 修復後
```
用戶操作: 主程式切換 race (Abu Dhabi → China)
    ↓
parameter_provider 發送更新信號
    ↓
Pedal Behavior 模組: ✅ 接收到更新
    ↓
自動調用 update_lap_parameters(year="2025", race="China", session="R")
    ↓
data_manager.load_data() 載入新數據（API 優先）
    ↓
結果: 自動顯示 China 的數據 ✅
```

---

## 🧪 驗證方法

### 測試步驟
1. 啟動 F1T GUI
2. 開啟 Pedal Behavior Analysis 模組（選擇 Abu Dhabi / R）
3. 在主程式切換到不同的 race（例如 China）
4. 觀察 Pedal Behavior 模組是否自動更新

### 預期結果
- ✅ 模組標題自動更新為 "China"
- ✅ 圖表數據自動重載為 China 的數據
- ✅ 無需手動關閉/重開模組

---

## 📊 架構驗證

### Pedal Behavior 模組的完整架構

```python
PedalBehaviorAnalysisMDI (UniversalAnalysisMDI)
├── ✅ parameter_provider        # 參數提供者（修復後添加）
├── ✅ update_lap_parameters()   # 參數更新方法（已存在）
├── ✅ data_manager              # PedalBehaviorDataManager
│   └── load_data()              # API 優先載入
└── ✅ chart_widget              # 圖表組件
```

**確認檢查**:
- ✅ 繼承自 `UniversalAnalysisMDI`
- ✅ 有 `update_lap_parameters` 方法（Line 738）
- ✅ 有 `data_manager.load_data()` 實現
- ✅ 現在有 `parameter_provider` 設置

---

## 🔄 對比其他模組

### 正常工作的模組（參考）

**Rain Analysis** (Temperature Analysis):
```python
# analysis_module_creator.py
module = TempAnalysisUniversal(main_window=self.main_window)
module.parameter_provider = parameter_provider  # ✅
module.update_parameters(year, race, session)
```

**Traffic Analysis**:
```python
# analysis_module_creator.py
module = TrafficAnalysisMDI(year=current_year, race=current_race, session=current_session)
module.parameter_provider = parameter_provider  # ✅
```

**Pedal Behavior（修復後）**:
```python
# analysis_module_creator.py
module = PedalBehaviorAnalysisMDI(year=current_year, race=current_race, session=current_session)
module.parameter_provider = parameter_provider  # ✅ 已添加
```

---

## 📝 相關模組檢查

### 需要檢查的其他模組

為了確保所有模組都支援參數更新，建議檢查以下模組：

1. ✅ **Historical Track Map** - 已確認有 `update_lap_parameters`
2. ✅ **Traffic Analysis** - 已確認有 `parameter_provider`
3. ✅ **Start Reaction** - 已確認有 `update_lap_parameters`
4. ⚠️ **Long Run Analysis** - 需要檢查（QWidget 子類，非 UniversalAnalysisMDI）

---

## 🎯 總結

### 修復內容
- ✅ 在 `analysis_module_creator.py` 中添加 `module.parameter_provider = parameter_provider`
- ✅ 使 Pedal Behavior 模組能接收主程式的參數更新

### 效果
- ✅ 主程式更換 race 時，Pedal Behavior 模組自動更新數據
- ✅ 與其他模組（Rain Analysis、Traffic Analysis）行為一致
- ✅ 提升用戶體驗，無需手動重啟模組

### 技術債務
- 建議未來為所有新模組添加自動化測試，確保 `parameter_provider` 正確設置
- 建議在模組創建模板中強制要求設置 `parameter_provider`

---

**修復完成日期**: 2026-01-12  
**修復人員**: AI Assistant  
**驗證狀態**: 待用戶測試確認
