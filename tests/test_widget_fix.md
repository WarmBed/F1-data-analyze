# 🔧 get_widget() 修復測試

## ❌ 原始問題
```
TypeError: setWidget(self, widget: Optional[QWidget]): argument 1 has unexpected type 'RainAnalysisModuleAdapter'
```

**根本原因**：
- `_create_module_instance` 返回 `RainAnalysisModuleAdapter` (Adapter)
- `subwindow.setWidget()` 需要 `QWidget`
- 缺少 `.get_widget()` 調用

---

## ✅ 修復內容

**檔案**：`core/workspace_serializer.py` - `_rebuild_mdi_window` 方法

### 修改前（第 600-610 行）：
```python
# 創建模組實例
module_widget = self._create_module_instance(window_type, parameters)
if not module_widget:
    return False

# 創建 MDI 子視窗
subwindow = QMdiSubWindow()
subwindow.setWidget(module_widget)  # ❌ 錯誤：傳入 Adapter
```

### 修改後：
```python
# 創建模組實例
analysis_module = self._create_module_instance(window_type, parameters)
if not analysis_module:
    return False

# 檢查模組是否有 get_widget() 方法
if not hasattr(analysis_module, 'get_widget'):
    print(f"[WORKSPACE] ❌ 模組缺少 get_widget() 方法")
    return False

# 獲取實際的 QWidget
module_widget = analysis_module.get_widget()
if not module_widget:
    return False

# 創建 MDI 子視窗（使用 PopoutSubWindow）
from f1t_gui_main import PopoutSubWindow
subwindow = PopoutSubWindow(window_title, mdi_area, analysis_module)
subwindow.setWidget(module_widget)  # ✅ 正確：傳入 QWidget
```

---

## 🎯 關鍵改進

1. **變數命名清晰**：`analysis_module` (Adapter) vs `module_widget` (QWidget)
2. **調用 get_widget()**：獲取實際的 QWidget
3. **使用 PopoutSubWindow**：保持與 f1t_gui_main.py 的一致性
4. **錯誤檢查**：驗證 `get_widget()` 存在且返回非 None

---

## 🧪 測試步驟

### 步驟 1: 重啟 GUI
```powershell
# 強制關閉所有 Python 進程
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# 啟動 GUI
python f1t_gui_main.py
```

### 步驟 2: 載入 Workspace
1. 點擊主視窗的 **Load Workspace** 按鈕
2. 選擇已保存的 Workspace (例如 `2025_United States_R (2)`)
3. 等待視窗重建

---

## 📊 預期結果

### ✅ 成功標誌：
1. **無 TypeError**：不再出現 `argument 1 has unexpected type 'RainAnalysisModuleAdapter'`
2. **視窗出現**：Rain Analysis 視窗成功重新打開
3. **日誌正確**：
   ```
   [WORKSPACE] ✅ Rain Analysis 模組已創建 (type=rain_weather)
   [WORKSPACE] ✅ 視窗已重建: '🌧️ Rain Analysis_2025_United States_R'
   ```

### ❌ 失敗標誌：
- 仍然出現 TypeError
- 視窗沒有出現
- 日誌顯示其他錯誤

---

## 🔍 驗證命令

測試後執行：
```powershell
# 檢查最新日誌
Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 50 | Select-String "WORKSPACE|TypeError|已重建"

# 如有錯誤，查看完整堆疊
Get-Content 'logs\f1_gui_2025-10-21.log' -Encoding UTF8 -Tail 100 | Select-String -Context 5,5 "Traceback"
```
