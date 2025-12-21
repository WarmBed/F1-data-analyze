# Workspace 載入問題診斷報告

## 📅 診斷日期: 2025-10-23

## 🔍 問題描述

**症狀**: 使用 Load Workspace 載入降雨模組時，沒有 MDI 視窗生成

**用戶操作**:
1. 保存包含 Rain Analysis 模組的 Workspace
2. 重新載入 Workspace
3. 結果：MDI 區域空白，沒有視窗顯示

---

## 🎯 根本原因

### 問題 1: `window_type` 名稱不匹配

**發現**:
- Workspace 保存的 `window_type`: `"rain_weather"`
- `_create_analysis_module` 映射表中的 key: `"rain_analysis"`
- **結果**: 映射查找失敗，返回 `None`

**證據** (從資料庫中提取的配置):
```json
{
  "window_type": "rain_weather",
  "window_title": "🌧️ Rain Analysis_2025_United States_R",
  "parameters": {
    "year": "2025",
    "race": "United States",
    "session": "R"
  }
}
```

**根本原因**:
1. Workspace 序列化時使用 `analysis_type` 屬性作為 `window_type`
2. `RainAnalysisModuleAdapter` 的 `analysis_type = "rain_weather"`
3. 但 `_create_analysis_module` 的映射表只有 `"rain_analysis"`

---

## ✅ 解決方案

### 修改: `f1t_gui_main.py` Line 12215-12223

**修改前**:
```python
"rain_analysis": [
    ("rain_analysis", "Rain Analysis"),
    "雨況分析",
    "降雨分析",
],
```

**修改後**:
```python
"rain_analysis": [
    ("rain_analysis", "Rain Analysis"),
    ("rain_weather", "Rain Weather"),  # ✅ 添加 Workspace 使用的別名
    "雨況分析",
    "降雨分析",
],
```

**效果**:
- ✅ `_create_analysis_module` 現在可以識別 `"rain_weather"` 類型
- ✅ 映射會將 `"rain_weather"` 轉換為 `"rain_analysis"` 模組類型
- ✅ Workspace 載入時能正確創建 Rain Analysis 模組

---

## 🧪 驗證步驟

### 步驟 1: 檢查修改是否生效

```powershell
# 檢查檔案是否包含新的別名
Get-Content f1t_gui_main.py | Select-String "rain_weather"
```

**預期輸出**:
```
    ("rain_weather", "Rain Weather"),  # ✅ 添加 Workspace 使用的別名
```

### 步驟 2: 重啟 GUI 並測試

```powershell
# 重啟 GUI
python f1t_gui_main.py
```

**操作**:
1. 載入之前保存的 Workspace (含 Rain Analysis)
2. 觀察終端輸出

**預期成功的 log**:
```
[WORKSPACE] ========== 開始重建 MDI 視窗（與手動開啟一致） ==========
[WORKSPACE] 📋 視窗類型: rain_weather
[WORKSPACE] 🔧 調用主視窗的 _create_analysis_module() 方法...
[DEBUG]    [MODULE_FACTORY] 使用提供的模組類型提示: rain_weather
[DEBUG]    [MODULE_FACTORY] 開始創建降雨分析模組...
[OK] [MODULE_FACTORY] 降雨分析適配器導入成功
[INIT] [MODULE_FACTORY] 降雨分析模組參數: 2025 United States R
[OK] 降雨分析模組初始化成功
[WORKSPACE] ✅ 模組創建成功: RainAnalysisModuleAdapter
[WORKSPACE] 📊 當前參數: 2025 United States R
[WORKSPACE] 🏷️ 動態生成標題: 'Rain Analysis - 2025 United States R'
[WORKSPACE] 📦 PopoutSubWindow 已創建
[WORKSPACE] 🎨 Widget 已設置
[WORKSPACE] 📏 尺寸已設置: 1200x800
[WORKSPACE] ✅ 已添加到 MDI 區域
[WORKSPACE] 🔗 已連接 window_closed 信號
[WORKSPACE] 📋 已添加到 active_subwindows 追蹤列表
[WORKSPACE] 👁️ 視窗已顯示
[WORKSPACE] 📍 位置已自動計算
[WORKSPACE] ========== MDI 視窗重建完成 ==========
```

**預期結果**:
- ✅ Rain Analysis 視窗成功創建
- ✅ 視窗顯示在 MDI 區域
- ✅ 視窗標題使用當前 GUI 參數
- ✅ 視窗內容正確載入

---

## 🔍 調試工具

如果問題仍然存在，可使用以下腳本進行診斷：

### check_workspace_json.py
```powershell
python check_workspace_json.py
```
**用途**: 查看 Workspace 保存的 `window_type` 是什麼

### debug_workspace_load.py
```powershell
python debug_workspace_load.py
```
**用途**: 檢查 `_rebuild_mdi_window` 和 `_create_analysis_module` 方法是否存在

---

## 📊 影響範圍

### 直接影響
- ✅ Rain Analysis 模組的 Workspace 載入
- ✅ 所有使用 `"rain_weather"` 作為 `analysis_type` 的模組

### 潛在影響
- ⚠️  其他模組如果 `analysis_type` 與映射表 key 不一致，也會有同樣問題

### 建議檢查的模組
需要確認以下模組的 `analysis_type` 是否在映射表中：

| 模組 | analysis_type | 映射表 key | 是否匹配 |
|------|---------------|------------|---------|
| RainAnalysisModuleAdapter | `rain_weather` | `rain_analysis` | ✅ 已修復 |
| TireAnalysisModuleAdapter | `tire` | `tire_analysis` | ⚠️ 需檢查 |
| TrackAnalysisUniversal | `track_analysis` | `track_analysis` | ✅ 匹配 |
| PitstopAnalysisModule | `pitstop` | `pitstop_analysis` | ⚠️ 需檢查 |
| AccidentAnalysisModule | `accident_analysis` | `accident_analysis` | ✅ 匹配 |

---

## ✅ 解決方案總結

### 短期修復（已完成）
1. ✅ 在 `_create_analysis_module` 的映射表中添加 `"rain_weather"` 別名
2. ✅ 映射 `"rain_weather"` → `"rain_analysis"` 模組類型

### 長期優化（建議）
1. **統一命名**: 將所有模組的 `analysis_type` 與映射表 key 統一
2. **自動檢測**: 在 Workspace 序列化時，檢查 `analysis_type` 是否在映射表中
3. **錯誤提示**: `_create_analysis_module` 返回 `None` 時，添加詳細的錯誤訊息

---

## 📝 測試清單

- [ ] 重啟 GUI
- [ ] 載入包含 Rain Analysis 的 Workspace
- [ ] 確認 MDI 視窗成功創建
- [ ] 確認視窗標題正確
- [ ] 確認視窗內容正確載入
- [ ] 測試 Popout 功能
- [ ] 測試視窗關閉

---

**診斷工具**:
- ✅ `check_workspace_json.py` - 檢查保存的配置
- ✅ `debug_workspace_load.py` - 檢查方法存在性
- ✅ `check_workspace_structure.py` - 檢查資料庫結構

**相關檔案**:
- `f1t_gui_main.py` (Line 12215-12223) - ✅ 已修改
- `core/workspace_serializer.py` (Line 664-780) - ✅ 已修改（統一流程）
- `modules/gui/rain_analysis/rain_analysis_module.py` - `analysis_type = "rain_weather"`

---

**診斷者**: GitHub Copilot  
**修復狀態**: ✅ 已修復  
**測試狀態**: ⏳ 等待用戶驗證
