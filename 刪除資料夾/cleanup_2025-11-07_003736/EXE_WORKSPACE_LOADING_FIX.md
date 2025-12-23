# EXE Workspace 載入問題修復 (2025-10-28)

## 🔍 問題診斷

### 問題描述
在 `.py` 模式下載入含有 26 個模組的 workspace 正常運作，但在 EXE 模式下會造成：
1. **主 GUI 無反應/阻塞**
2. **程式當機跳掉**
3. **API 429 錯誤彈窗**
4. **沒有 LOG 輸出**無法診斷問題

### 根本原因
1. **LOG 系統被完全禁用**：EXE 模式下日誌系統被強制設置為 `NullHandler`
2. **API 限流未處理**：多個模組同時載入時觸發 API 429 錯誤
3. **錯誤對話框導致阻塞**：429 錯誤彈出 `QMessageBox` 阻塞主線程
4. **沒有載入延遲**：Workspace 重建時所有視窗同時請求 API

---

## ✅ 修復方案

### 修復 1: 啟用 EXE 日誌系統

**檔案**: `core/logger.py`

**修改內容**:
```python
# 之前：完全禁用 EXE 日誌
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# 之後：條件式啟用日誌
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
FORCE_SILENT = os.getenv('F1T_EXE_SILENT_MODE') == '1'

# 只有當環境變數 F1T_EXE_SILENT_MODE=1 時才禁用日誌
if IS_EXE_MODE and FORCE_SILENT:
    # 使用 NullHandler
else:
    # 正常記錄日誌到 logs/ 目錄
```

**效果**:
- ✅ EXE 模式現在會在 `logs/` 目錄記錄完整的 DEBUG 日誌
- ✅ 可以追蹤 Workspace 載入過程
- ✅ 可以診斷 API 錯誤和崩潰原因

---

### 修復 2: Runtime Hook 啟用 DEBUG

**檔案**: `pyinstaller_runtime_hook.py`

**修改內容**:
```python
# 之前：CRITICAL 級別（完全靜默）
os.environ['F1_LOG_LEVEL'] = 'CRITICAL'
os.environ['F1T_EXE_SILENT_MODE'] = '1'

# 之後：DEBUG 級別（詳細記錄）
os.environ['F1_LOG_LEVEL'] = 'DEBUG'
# os.environ['F1T_EXE_SILENT_MODE'] = '1'  # 註解掉
```

**效果**:
- ✅ EXE 啟動時自動設置 DEBUG 級別
- ✅ 所有模組的載入過程都會被記錄
- ✅ API 請求和錯誤會被完整記錄

---

### 修復 3: API 429 錯誤優雅處理

**檔案**: `modules/gui/accident_analysis/accident_data_manager.py`

**修改內容 A - Worker 層級**:
```python
# 之前：直接 raise_for_status() 拋出異常
response.raise_for_status()

# 之後：檢查狀態碼並優雅處理
if response.status_code == 429:
    # API 限流錯誤 - 不要彈窗，靜默失敗
    self.failure.emit("API 請求過於頻繁，請稍後再試 (429 Too Many Requests)")
    return
elif response.status_code >= 500:
    # 伺服器錯誤
    self.failure.emit(f"API 伺服器錯誤 ({response.status_code})")
    return
elif response.status_code >= 400:
    # 客戶端錯誤（除了 429）
    error_msg = response.json().get("message", response.text)
    self.failure.emit(f"API 請求錯誤 ({response.status_code}): {error_msg}")
    return

response.raise_for_status()
```

**修改內容 B - 錯誤處理層級**:
```python
def _on_api_error(self, message: str) -> None:
    self._error(f"API 請求失敗: {message}")
    self._is_loading = False
    
    # ✅ 如果是 429 錯誤，靜默處理不彈窗
    is_rate_limit = "429" in message or "Too Many Requests" in message
    
    if is_rate_limit:
        # 429 錯誤：靜默處理，只發送狀態訊息
        self.status_changed.emit("API 請求過於頻繁，請稍後手動重新載入")
        # ❌ 不發送 error_occurred 信號，避免彈窗
        print(f"[ACCIDENT_API] ⚠️ API 限流 (429): {message}")
    else:
        # 其他錯誤：正常處理
        self.error_occurred.emit(f"API 請求失敗: {message}")
```

**效果**:
- ✅ 429 錯誤不再彈出對話框
- ✅ 不會阻塞主線程導致 GUI 無反應
- ✅ 錯誤訊息記錄在 LOG 中供事後查看
- ✅ 狀態列顯示友善的錯誤訊息

---

### 修復 4: Workspace 載入延遲機制

**檔案**: `core/workspace_serializer.py`

**修改內容**:
```python
# 之前：直接循環重建所有視窗
for window_config in mdi_windows_config:
    self._rebuild_mdi_window(mdi_area, window_config)

# 之後：加入延遲和錯誤隔離
import time
for window_index, window_config in enumerate(mdi_windows_config):
    print(f"[WORKSPACE] 🔨 重建視窗 {window_index + 1}/{len(mdi_windows_config)}")
    
    # ✅ 在每個視窗之間加入延遲（避免 API 限流）
    if window_index > 0:
        delay_ms = 500  # 500ms 延遲
        print(f"[WORKSPACE] ⏱️ 延遲 {delay_ms}ms 避免 API 限流...")
        time.sleep(delay_ms / 1000.0)
    
    try:
        self._rebuild_mdi_window(mdi_area, window_config)
    except Exception as e:
        # ✅ 單個視窗失敗不影響其他視窗
        print(f"[WORKSPACE] ⚠️ 視窗重建失敗，繼續處理下一個: {e}")
        traceback.print_exc()
```

**效果**:
- ✅ 每個模組載入之間延遲 500ms
- ✅ 避免同時發送大量 API 請求
- ✅ 降低觸發 429 限流的機率
- ✅ 單個模組失敗不影響其他模組載入

---

## 📊 測試計劃

### 測試步驟
1. **啟動新編譯的 EXE**
   ```powershell
   dist\F1T_GUI.exe
   ```

2. **載入 26 個模組的 Workspace**
   - 選擇 File → Load Workspace
   - 選擇問題 Workspace 檔案
   
3. **觀察行為**
   - ✅ 主視窗應保持響應
   - ✅ 不應出現 429 錯誤彈窗
   - ✅ 模組逐步載入（每個間隔 500ms）
   - ✅ 失敗的模組不影響其他模組

4. **檢查 LOG 檔案**
   ```powershell
   # 查看今天的 GUI 日誌
   Get-Content "logs\f1_gui_2025-10-28.log" -Tail 100
   
   # 即時監控（使用 monitor_exe_log.ps1）
   .\monitor_exe_log.ps1
   ```

### 預期 LOG 輸出
```
[WORKSPACE] 🔄 開始反序列化 Workspace...
[WORKSPACE] 📊 需要重建 X 個分頁
[WORKSPACE] 🔨 重建分頁: 'Tab 1' (Y 個視窗)
[WORKSPACE] 🔨 重建視窗 1/Y
[WORKSPACE] 📋 視窗類型: accident_analysis
[WORKSPACE] ⏱️ 延遲 500ms 避免 API 限流...
[WORKSPACE] 🔨 重建視窗 2/Y
...
[ACCIDENT_API] ⚠️ API 限流 (429): API 請求過於頻繁...
[WORKSPACE] ⚠️ 視窗重建失敗，繼續處理下一個: ...
[WORKSPACE] ✅ Workspace 反序列化完成！
```

---

## 📝 注意事項

### 1. 日誌檔案位置
- **開發模式 (.py)**: `logs/f1_gui_YYYY-MM-DD.log`
- **EXE 模式**: `logs/f1_gui_YYYY-MM-DD.log` (相同位置)
- **錯誤日誌**: `logs/f1_gui_error_YYYY-MM-DD.log`

### 2. API 限流建議
- **同時載入上限**: 建議不超過 10 個模組
- **延遲調整**: 如仍遇到 429，可增加延遲到 1000ms
- **手動重試**: 429 錯誤的模組可手動重新載入

### 3. 生產環境配置
如果需要完全靜默的 EXE（不記錄日誌）：
```python
# 在 pyinstaller_runtime_hook.py 中啟用
os.environ['F1T_EXE_SILENT_MODE'] = '1'
```

---

## 🔧 相關檔案

- `core/logger.py` - 日誌系統核心
- `pyinstaller_runtime_hook.py` - EXE 啟動配置
- `core/workspace_serializer.py` - Workspace 載入邏輯
- `modules/gui/accident_analysis/accident_data_manager.py` - API 錯誤處理範例
- `F1T_GUI.spec` - PyInstaller 配置
- `monitor_exe_log.ps1` - 即時日誌監控腳本

---

## ✅ 修復總結

| 問題 | 修復方案 | 狀態 |
|------|---------|------|
| LOG 完全禁用 | 條件式啟用日誌系統 | ✅ 已修復 |
| API 429 彈窗阻塞 | 優雅處理不彈窗 | ✅ 已修復 |
| 同時請求過多 | 加入 500ms 延遲 | ✅ 已修復 |
| 單點故障影響全局 | 錯誤隔離機制 | ✅ 已修復 |

**編譯版本**: `dist/F1T_GUI.exe` (2025-10-28)
**測試狀態**: ⏳ 待用戶測試
