# F1T GUI 打包日誌級別設置說明

## 📋 修改摘要 (2025-10-11)

### 🎯 **目標**
確保打包的 EXE 檔案只記錄 **DEBUG 級別或以上**的日誌訊息，避免日誌檔案被 TRACE 級別的訊息淹沒。

---

## 🔧 **修改內容**

### 1️⃣ **創建 Runtime Hook** (`pyinstaller_runtime_hook.py`)

**作用**：在 EXE 啟動時自動設置環境變數 `F1_LOG_LEVEL=DEBUG`

```python
import os
import sys

# 設置日誌級別為 DEBUG
if 'F1_LOG_LEVEL' not in os.environ:
    os.environ['F1_LOG_LEVEL'] = 'DEBUG'
    print(f"[RUNTIME_HOOK] 已設置 F1_LOG_LEVEL=DEBUG")
```

**位置**：專案根目錄  
**PyInstaller 整合**：在 `F1T_GUI.spec` 中的 `runtime_hooks` 參數指定

---

### 2️⃣ **修改 PyInstaller 配置** (`F1T_GUI.spec`)

**變更**：添加 runtime hook 到打包流程

```python
a = Analysis(
    # ... 其他配置 ...
    runtime_hooks=['pyinstaller_runtime_hook.py'],  # ← 新增這行
    # ... 其他配置 ...
)
```

**效果**：
- EXE 啟動時會先執行 `pyinstaller_runtime_hook.py`
- 自動設置 `F1_LOG_LEVEL=DEBUG`
- 無需用戶手動設置環境變數

---

### 3️⃣ **更新打包腳本** (`Build_F1T_GUI.bat`)

**變更內容**：

1. **移除環境變數設置段落**（已改由 runtime hook 處理）
2. **更新打包訊息**：
   ```batch
   echo       內建 Runtime Hook: 自動設置 F1_LOG_LEVEL=DEBUG
   ```

3. **更新成功訊息**：
   ```batch
   echo    ⚠️  日誌級別設定:
   echo    - 已內建 Runtime Hook 自動設置 F1_LOG_LEVEL=DEBUG
   echo    - 所有 DEBUG 級別或以上的訊息都會寫入日誌檔案
   echo    - 如需更改級別，請修改 pyinstaller_runtime_hook.py
   ```

---

## 📊 **日誌級別對照表**

| 級別 | 數值 | 說明 | 是否記錄到檔案 |
|------|------|------|----------------|
| TRACE | 5 | 超詳細追蹤訊息 | ❌ 不記錄（過濾掉） |
| **DEBUG** | **10** | **調試訊息** | **✅ 記錄（設定值）** |
| INFO | 20 | 一般資訊訊息 | ✅ 記錄 |
| WARNING | 30 | 警告訊息 | ✅ 記錄 |
| ERROR | 40 | 錯誤訊息 | ✅ 記錄 |
| CRITICAL | 50 | 嚴重錯誤 | ✅ 記錄 |

**設定 `F1_LOG_LEVEL=DEBUG` 後**：
- ✅ DEBUG、INFO、WARNING、ERROR、CRITICAL 都會記錄
- ❌ TRACE 訊息會被過濾（減少日誌噪音）

---

## 🧪 **測試驗證**

### 測試腳本
運行 `test_runtime_hook_log_level.py` 驗證設置：

```powershell
python test_runtime_hook_log_level.py
```

**預期輸出**：
```
✅ 日誌級別正確設置為 DEBUG
✅ 日誌系統已設置為 DEBUG 級別
```

---

## 🚀 **打包流程**

### 執行打包
```powershell
.\Build_F1T_GUI.bat
```

### 打包步驟說明
```
[1/5] 清理舊檔案              → 刪除 build/ 和 dist/
[2/5] 檢查 .spec 檔案         → 驗證 F1T_GUI.spec 存在
[3/5] 檢查 PyInstaller        → 確認已安裝
[4/5] 執行打包                → 使用 pyinstaller + runtime hook
[5/5] 驗證輸出                → 檢查 dist\F1T_GUI.exe
```

---

## 📝 **運行時行為**

### EXE 啟動流程
```
1. 用戶執行 dist\F1T_GUI.exe
2. PyInstaller 解壓臨時檔案到 _MEIPASS 目錄
3. ⭐ 執行 pyinstaller_runtime_hook.py
   → 設置 F1_LOG_LEVEL=DEBUG
4. 啟動 f1t_gui_main.py
5. core.logger.setup_logging() 讀取 F1_LOG_LEVEL
   → 設置 FileHandler 的 level=DEBUG
6. 只有 DEBUG 或以上級別的訊息會寫入 logs\f1_gui_*.log
```

---

## 🔄 **如何修改日誌級別**

### 方法 1: 修改 Runtime Hook（推薦）

編輯 `pyinstaller_runtime_hook.py`:
```python
os.environ['F1_LOG_LEVEL'] = 'INFO'  # 改為 INFO 級別
```

重新打包：
```powershell
.\Build_F1T_GUI.bat
```

### 方法 2: 用戶環境變數（臨時）

用戶可在運行前設置：
```powershell
$env:F1_LOG_LEVEL = "WARNING"
.\dist\F1T_GUI.exe
```

**優先級**：
1. 用戶環境變數（最高）
2. Runtime Hook 設定（預設）

---

## ✅ **驗證清單**

打包完成後檢查：

- [ ] `dist\F1T_GUI.exe` 已生成
- [ ] 執行 EXE，檢查 `logs\f1_gui_*.log` 是否創建
- [ ] 日誌檔案中沒有 `[TRACE]` 訊息
- [ ] 日誌檔案中有 `[DEBUG]`、`[INFO]`、`[WARNING]`、`[ERROR]` 訊息
- [ ] EXE 啟動無錯誤

---

## 📌 **重要說明**

### 為什麼選擇 DEBUG 而非 INFO？

1. **開發階段需求**：保留調試訊息有助於診斷問題
2. **過濾 TRACE**：TRACE 級別訊息過於詳細，會產生大量日誌
3. **平衡點**：DEBUG 提供足夠詳細的資訊，同時避免日誌過大

### 未來優化建議

1. **生產版本**：可將級別設為 `INFO` 或 `WARNING`
2. **配置檔案**：考慮從 `config.ini` 讀取日誌級別
3. **GUI 設定**：在設置介面添加日誌級別選項

---

## 🐛 **問題排查**

### 日誌檔案仍有大量 TRACE 訊息

**可能原因**：Runtime Hook 未生效

**解決方法**：
1. 檢查 `F1T_GUI.spec` 中 `runtime_hooks` 是否正確配置
2. 檢查 `pyinstaller_runtime_hook.py` 是否在專案根目錄
3. 重新打包：`.\Build_F1T_GUI.bat`

### EXE 無法啟動

**可能原因**：Runtime Hook 有語法錯誤

**解決方法**：
1. 先測試 Runtime Hook：`python pyinstaller_runtime_hook.py`
2. 檢查是否有語法錯誤
3. 查看 PyInstaller 打包日誌

---

**修改日期**：2025-10-11  
**修改人員**：GitHub Copilot  
**測試狀態**：✅ 已驗證通過
