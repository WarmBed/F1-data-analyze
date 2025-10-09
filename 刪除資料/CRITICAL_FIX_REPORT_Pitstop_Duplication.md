# 🚨 重大修復報告：Pitstop 重複視窗問題

## 📋 問題摘要

**發現時間**：2025-10-06  
**問題類型**：API-ONLY 模式違規導致重複視窗創建  
**影響模組**：Brake 分析、RPM 分析  
**嚴重程度**：🔴 高

---

## 🔍 問題分析

### 根本原因

Brake 和 RPM 模組在處理**最速圈更新**時，違反了 **API-ONLY 模式政策**（2025-10-03），自動觸發 `main_window.create_telemetry_analysis()` 方法，導致：

1. ❌ 創建了不必要的遙測分析視窗
2. ❌ 遙測分析視窗創建過程中附帶啟動了 Pitstop 分析視窗
3. ❌ 每次更新 driver/lap/fastest lap 都會重複觸發

### 觸發流程

```
用戶更新圈速參數（driver/lap/fastest lap）
    ↓
f1t_gui_main.py::update_all_lap_analysis()
    ↓
brake_analysis_mdi.py::update_lap_parameters()
    ↓
BrakeDataManager::load_brake_data(is_fastest=True)
    ↓
BrakeDataManager::_check_and_load_telemetry_if_needed() 
    ↓
❌ 調用 main_window.create_telemetry_analysis()  ← 問題點！
    ↓
🚨 創建遙測分析視窗 + Pitstop 分析視窗
```

---

## ✅ 修復方案

### 修復原則

遵循 **API-ONLY 模式政策**：

- ✅ **允許**：讀取本地 JSON 緩存
- ✅ **允許**：通過 REST API 獲取數據  
- ✅ **允許**：檢查現有視窗
- ❌ **禁止**：自動創建新視窗
- ❌ **禁止**：自動啟動 CLI 進程

### 修復內容

#### 1. `_check_and_load_telemetry_if_needed()` 方法

**修復前**：
```python
def _check_and_load_telemetry_if_needed(self):
    # 檢查本地 JSON
    telemetry_file = self._find_telemetry_analysis_file(...)
    if telemetry_file:
        return True
    
    # ❌ 找不到就嘗試創建視窗
    if hasattr(main_window, 'create_telemetry_analysis'):
        main_window.create_telemetry_analysis()  # ← 問題！
        return True
```

**修復後**：
```python
def _check_and_load_telemetry_if_needed(self):
    """遵循 API-ONLY 模式
    
    ⚠️ 此方法只檢查本地 JSON 緩存，不自動創建視窗
    """
    # ✅ 檢查本地 JSON 緩存
    telemetry_file = self._find_telemetry_analysis_file(...)
    if telemetry_file:
        print(f"📂 [API-ONLY] 找到本地遙測分析緩存")
        return True
    
    # ❌ 不自動創建視窗，改為提示用戶
    print("⚠️ [API-ONLY] 遙測分析數據不存在於本地緩存")
    print("💡 [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
    print("💡 [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")
    return False
```

#### 2. `_trigger_telemetry_analysis()` 方法

**修復前**：
```python
def _trigger_telemetry_analysis(self):
    # 檢查是否已有視窗
    for sub_window in main_window.mdi_area.subWindowList():
        if "遙測分析" in sub_window.windowTitle():
            return True
    
    # ❌ 沒有就創建一個
    if hasattr(main_window, 'create_telemetry_analysis'):
        main_window.create_telemetry_analysis()  # ← 問題！
        return True
```

**修復後**：
```python
def _trigger_telemetry_analysis(self):
    """API-ONLY 模式：不自動創建視窗"""
    # ✅ 檢查是否已有視窗（但不創建）
    for sub_window in main_window.mdi_area.subWindowList():
        if "遙測分析" in sub_window.windowTitle():
            print(f"🎯 [API-ONLY] 找到現有遙測分析視窗")
            return True
    
    # ✅ 改為僅檢查本地 JSON 緩存
    print(f"💡 [API-ONLY] 未找到現有遙測分析視窗，檢查本地緩存...")
    return self._check_and_load_telemetry_if_needed()
```

---

## 🎯 修復對象

### 已修復
- ✅ `modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py`
  - ✅ `_check_and_load_telemetry_if_needed()` 方法（第 789-834 行）

### 待修復
- ⏳ `modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py`
  - ⏳ `_trigger_telemetry_analysis()` 方法（第 895-928 行）
- ⏳ `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py`
  - ⏳ 相同問題，需要同樣修復

---

## 📊 影響範圍

### 用戶體驗改善
- ✅ 不再在更新圈速參數時自動創建 Pitstop 視窗
- ✅ 不再在更新圈速參數時自動創建遙測分析視窗
- ✅ 更新流程更加輕量級和可預測

### 功能影響
- ℹ️ 用戶需要**手動**開啟遙測分析模組（如需最速圈數據）
- ℹ️ 或通過 API 預先獲取遙測分析數據
- ℹ️ 或手動執行 CLI 生成 JSON 緩存

---

## 🧪 測試建議

### 測試場景 1：最速圈更新
1. 開啟 Brake 分析視窗
2. 勾選 "最速圈" 選項
3. 更新 driver1/driver2
4. ✅ 預期：不創建 Pitstop 視窗
5. ✅ 預期：終端顯示提示訊息

### 測試場景 2：本地緩存讀取
1. 預先手動執行：`python f1_analysis_modular_main.py -f 8 -y 2025 -r Japan -s R`
2. 開啟 Brake 分析視窗，勾選最速圈
3. ✅ 預期：正常讀取緩存，不創建視窗

### 測試場景 3：RPM 模組
1. 重複測試場景 1，使用 RPM 模組
2. ✅ 預期：同樣不創建 Pitstop 視窗

---

## 📝 後續行動

### 立即行動
1. ⏳ 完成 `_trigger_telemetry_analysis()` 方法修復
2. ⏳ 修復 RPM 模組相同問題
3. ⏳ 全面測試 Brake/RPM/Gear/Throttle 等所有圈速模組

### 長期改進
1. 📋 創建統一的最速圈數據獲取服務
2. 📋 避免每個模組重複實現遙測分析檢查邏輯
3. 📋 統一 API-ONLY 模式執行標準

---

## 🔗 相關文檔

- **API-ONLY 模式政策**：`.github/copilot-instructions.md` 第 44-94 行
- **原始問題報告**：`dist/logs/f1_gui_2025-10-06.log`
- **討論紀錄**：本次對話

---

## ✍️ 修復作者

**AI 助手**：GitHub Copilot  
**用戶**：mike2  
**修復日期**：2025-10-06

---

## 📌 備註

此修復是 **API-ONLY 模式政策** 執行的一部分，旨在確保：

> GUI 絕不自動啟動 CLI 進程或創建新視窗，  
> 只允許通過 API 或讀取本地 JSON 獲取數據。

這符合系統架構現代化和網路化的長期目標。
