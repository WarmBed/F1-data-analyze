# Workspace 載入與手動開啟統一化修改總結

## 📅 修改日期: 2025-10-11

## 🎯 修改目標

將 Workspace 載入流程修改為與手動開啟**完全一致**，實現以下統一：

1. **參數來源統一**: 從主視窗 GUI 實時獲取
2. **參數獲取統一**: 使用 `parameter_provider` 
3. **標題生成統一**: 動態調用 `get_window_title()`
4. **尺寸設定統一**: 使用 `analysis_module.get_default_size()`
5. **位置設定統一**: 調用 `_position_subwindow()` 自動計算
6. **模組創建統一**: 使用 `main_window._create_analysis_module()`
7. **信號連接統一**: 連接 `window_closed` 信號
8. **追蹤列表統一**: 添加到 `active_subwindows`
9. **數據載入統一**: 調用 API 而非讀取 JSON

---

## 📊 修改前後完整對比

| 項目 | 修改前（Workspace 載入） | 修改後（與手動開啟一致） | 變更 |
|------|------------------------|------------------------|------|
| **參數來源** | JSON 配置 `parameters.get()` | 主視窗 GUI `year_combo.currentText()` | ✅ 統一 |
| **參數獲取** | 直接讀取 JSON | `parameter_provider` 模式 | ✅ 統一 |
| **標題來源** | JSON `window_title` | 動態 `get_window_title()` | ✅ 統一 |
| **標題生成** | 靜態字串 | 當前 GUI 參數生成 | ✅ 統一 |
| **尺寸來源** | JSON `size` | `get_default_size()` | ✅ 統一 |
| **位置來源** | JSON `position` | `_position_subwindow()` | ✅ 統一 |
| **模組創建** | `_create_module_instance()` | `_create_analysis_module()` | ✅ 統一 |
| **PopoutSubWindow** | ✅ 有 | ✅ 有 | ✅ 一致 |
| **彈出功能** | ✅ 支援 | ✅ 支援 | ✅ 一致 |
| **信號連接** | ❌ 無 | ✅ `window_closed` | ✅ 統一 |
| **追蹤列表** | ❌ 無 | ✅ `active_subwindows` | ✅ 統一 |
| **數據載入** | 讀取 JSON 檔案 | 調用 API | ✅ 統一 |

---

## 🔧 核心修改內容

### 檔案: `core/workspace_serializer.py`

#### 方法: `_rebuild_mdi_window()` (Line 672-780)

**修改策略**: 完全複製手動開啟的流程

#### 關鍵程式碼變更

##### 1. 參數獲取（從 JSON → 從 GUI）

**修改前**:
```python
parameters = window_config.get('parameters', {})
year = parameters.get('year')
race = parameters.get('race')
session = parameters.get('session')
```

**修改後**:
```python
current_year = self.main_window.year_combo.currentText()
current_race = self.main_window.race_combo.currentText()
current_session = self.main_window.session_combo.currentText()
clean_race = self.main_window._get_race_key_from_display(current_race)
```

---

##### 2. 模組創建（直接創建 → 使用工廠）

**修改前**:
```python
analysis_module = self._create_module_instance(window_type, parameters)
```

**修改後**:
```python
analysis_module = self.main_window._create_analysis_module(
    window_type,
    module_type_hint=window_type
)
```

**優勢**:
- ✅ 使用主視窗的模組工廠，確保一致性
- ✅ 自動使用 `parameter_provider` 獲取參數
- ✅ 與手動開啟完全相同的初始化流程

---

##### 3. 標題生成（靜態 → 動態）

**修改前**:
```python
window_title = window_config.get('window_title', '')
```

**修改後**:
```python
if hasattr(analysis_module, 'get_window_title'):
    window_title = analysis_module.get_window_title(
        current_year,
        clean_race,
        current_session
    )
else:
    window_title = analysis_module.get_title()
```

**優勢**:
- ✅ 標題反映當前 GUI 參數
- ✅ 支援多語系動態生成
- ✅ 參數變更時標題自動更新

---

##### 4. 視窗包裝（一致）

**修改前**:
```python
from f1t_gui_main import PopoutSubWindow
subwindow = PopoutSubWindow(window_title, mdi_area, analysis_module)
subwindow.setWidget(module_widget)
```

**修改後**:
```python
from f1t_gui_main import PopoutSubWindow
analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
content_widget = analysis_module.get_widget()
analysis_window.setWidget(content_widget)
```

**說明**: 流程與手動開啟完全相同

---

##### 5. 尺寸設定（JSON → 模組推薦）

**修改前**:
```python
size = window_config.get('size', {'width': 800, 'height': 600})
subwindow.resize(size['width'], size['height'])
```

**修改後**:
```python
width, height = analysis_module.get_default_size()
analysis_window.resize(width, height)
```

**優勢**:
- ✅ 使用模組推薦的最佳尺寸
- ✅ 不同模組可以有不同尺寸

---

##### 6. 位置設定（固定 → 自動計算）

**修改前**:
```python
position = window_config.get('position', {'x': 0, 'y': 0})
subwindow.move(position['x'], position['y'])
```

**修改後**:
```python
self.main_window._position_subwindow(mdi_area, analysis_window)
```

**優勢**:
- ✅ 自動計算避免重疊
- ✅ 多視窗載入時位置整齊
- ✅ 適應不同螢幕解析度

---

##### 7. 信號連接（新增）

**修改前**: ❌ 無信號連接

**修改後**:
```python
if hasattr(analysis_window, 'window_closed'):
    analysis_window.window_closed.connect(
        lambda: self.main_window.on_subwindow_closed(analysis_window)
    )
```

**優勢**:
- ✅ 視窗關閉時正確清理資源
- ✅ 與手動開啟的生命週期管理一致

---

##### 8. 追蹤列表（新增）

**修改前**: ❌ 不加入追蹤列表

**修改後**:
```python
if hasattr(self.main_window, 'active_subwindows'):
    self.main_window.active_subwindows.append(analysis_window)
```

**優勢**:
- ✅ 主視窗可以追蹤所有活動視窗
- ✅ 參數更新時可以通知所有視窗
- ✅ 與手動開啟的視窗管理一致

---

##### 9. 顯示流程（調整順序）

**修改前**:
```python
mdi_area.addSubWindow(subwindow)
subwindow.resize(...)
subwindow.move(...)
subwindow.show()
```

**修改後**:
```python
mdi_area.addSubWindow(analysis_window)
analysis_window.show()
self.main_window._position_subwindow(mdi_area, analysis_window)
```

**優勢**:
- ✅ 與手動開啟的顯示順序完全一致
- ✅ 先 show() 再 position，確保位置計算正確

---

## 🎯 關鍵效果

### 1. 參數行為統一

**場景**: 保存 Workspace 時參數為 2024 Japan，載入時主視窗顯示 2025 Australia

| 修改前 | 修改後 |
|-------|-------|
| 視窗標題: "Rain Analysis - 2024 Japan R" | 視窗標題: "Rain Analysis - 2025 Australia Q" |
| 數據: 2024 Japan（從 JSON） | 數據: 2025 Australia（從 API） |
| ❌ 與當前 GUI 參數不一致 | ✅ 與當前 GUI 參數完全一致 |

### 2. 數據載入統一

**場景**: Workspace 載入後視窗數據來源

| 修改前 | 修改後 |
|-------|-------|
| 讀取本地 JSON 檔案 | 調用 API 獲取最新數據 |
| 使用緩存數據（可能過期） | 使用實時數據 |
| ❌ 不反映參數變更 | ✅ 反映當前參數 |

### 3. 視窗管理統一

**場景**: 視窗關閉、參數更新

| 修改前 | 修改後 |
|-------|-------|
| 關閉時無清理 | 關閉時觸發 `on_subwindow_closed` |
| 不在追蹤列表中 | 在 `active_subwindows` 列表中 |
| 參數更新時無法通知 | 參數更新時可以通知更新 |
| ❌ 生命週期管理不完整 | ✅ 生命週期管理完整 |

---

## 🧪 測試策略

### 階段 1: 靜態驗證 ✅
- ✅ Import 測試通過
- ✅ 方法簽名正確
- ✅ 依賴方法存在

**測試腳本**: `test_workspace_unification_import.py`  
**結果**: 4/4 通過

### 階段 2: GUI 功能測試 ⏳
- ⏳ 基礎載入測試
- ⏳ **參數變更測試**（關鍵）
- ⏳ Popout 功能測試
- ⏳ API 調用驗證

**測試指南**: `WORKSPACE_RAIN_ANALYSIS_GUI_TEST_GUIDE.md`

### 階段 3: 擴展測試 ⏳
- ⏳ 擴展至其他模組
- ⏳ 多視窗載入測試
- ⏳ 壓力測試

---

## 📈 影響範圍

### 直接影響
- ✅ Rain Analysis 模組（首個測試對象）
- 🔄 其他分析模組（後續擴展）

### 系統影響
- ✅ Workspace 序列化/反序列化邏輯
- ✅ 參數傳遞機制
- ✅ 視窗生命週期管理

### 用戶影響
- ✅ 載入 Workspace 後視窗標題正確
- ✅ 視窗數據反映當前參數
- ✅ 視窗行為與手動開啟一致

---

## 🚨 風險與緩解

### 風險 1: 參數不匹配
**描述**: 主視窗參數與模組需求不一致  
**機率**: 低  
**緩解**: `_create_analysis_module()` 已有參數驗證

### 風險 2: API 不可用
**描述**: API 服務未運行  
**機率**: 中  
**緩解**: 錯誤處理，顯示友好提示

### 風險 3: 舊 Workspace 不相容
**描述**: 舊版本 Workspace 檔案可能缺少欄位  
**機率**: 低  
**緩解**: 新流程只需要 `window_type`，其他欄位不再使用

---

## 📚 相關文檔

1. **測試計畫**: `WORKSPACE_RAIN_ANALYSIS_UNIFICATION_TEST_PLAN.md`
2. **GUI 測試指南**: `WORKSPACE_RAIN_ANALYSIS_GUI_TEST_GUIDE.md`
3. **Import 測試腳本**: `test_workspace_unification_import.py`
4. **開發指導**: `.github/copilot-instructions.md`

---

## ✅ 下一步行動

### 立即執行
1. **執行 GUI 測試**
   ```powershell
   python f1t_gui_main.py
   ```
   
2. **驗證關鍵測試**
   - Test 2: 參數變更測試
   - Test 6: API 調用驗證

### 測試通過後
3. **擴展至其他模組**
   - Tire Strategy
   - Track Analysis
   - Accident Analysis
   - 等...

4. **更新文檔**
   - 記錄測試結果
   - 更新開發指南

### 長期優化
5. **向後兼容處理**
   - 檢測舊 Workspace 格式
   - 提供升級路徑

6. **性能優化**
   - API 調用緩存
   - 批次載入多視窗

---

## 📊 成功指標

### 必須達成
- ✅ Workspace 載入後視窗標題使用當前 GUI 參數
- ✅ Workspace 載入後調用 API 而非讀取 JSON
- ✅ 所有功能與手動開啟完全一致

### 期望達成
- ✅ 所有 GUI 測試通過
- ✅ 無錯誤或警告
- ✅ 用戶體驗流暢

### 加分項
- ⭐ 性能優於手動開啟
- ⭐ 支援更多模組類型
- ⭐ 錯誤處理更完善

---

## 👥 貢獻者

**開發**: GitHub Copilot  
**審核**: (待填)  
**測試**: (待填)

---

## 📅 版本歷史

### v1.0 (2025-10-11)
- ✅ 完成 `_rebuild_mdi_window()` 修改
- ✅ 通過靜態驗證測試
- ⏳ 等待 GUI 功能測試

---

**文檔狀態**: ✅ 完成  
**修改狀態**: ✅ 已實現  
**測試狀態**: ⏳ 進行中  
**部署狀態**: ⏳ 待驗證
