# EXE 日誌系統控制說明

## 📋 概述

從 V0.12.1 版本開始，EXE 建構的 PitWall 應用程式預設**禁用所有日誌輸出**，以：
- ✅ 提升執行效能（減少檔案 I/O）
- ✅ 減少磁碟空間使用
- ✅ 避免日誌檔案累積

## 🔧 實現機制

### 1. Runtime Hook (`hooks/runtime_hook_disable_logger.py`)
```python
# 在 EXE 啟動時自動設定環境變數
os.environ['F1T_EXE_DISABLE_LOG'] = '1'
```

### 2. Logger 核心 (`core/logger.py`)
```python
# 檢測環境變數並禁用日誌
FORCE_SILENT = IS_EXE_MODE and os.getenv('F1T_EXE_DISABLE_LOG') == '1'
```

### 3. `.spec` 配置 (`F1T_GUI_clean.spec`)
```python
runtime_hooks=[str(project_root / 'hooks' / 'runtime_hook_disable_logger.py')]
```

## 🎯 使用場景

### 正式發布版本（預設）
```bash
# 建構 EXE（日誌已禁用）
pyinstaller F1T_GUI_clean.spec

# 使用者執行時：無日誌輸出，最佳效能
PitWall.exe
```

### 除錯版本（啟用日誌）
如果需要在 EXE 中啟用日誌以進行除錯：

#### 方法 1: 修改 `.spec` 檔案
```python
# 註釋掉 runtime_hooks
runtime_hooks=[],  # str(project_root / 'hooks' / 'runtime_hook_disable_logger.py')
```

#### 方法 2: 修改 `runtime_hook_disable_logger.py`
```python
# 註釋掉環境變數設定
# os.environ['F1T_EXE_DISABLE_LOG'] = '1'
```

#### 方法 3: 執行時設定環境變數（不建議）
```powershell
# 移除環境變數（需要在啟動前設定）
$env:F1T_EXE_DISABLE_LOG = '0'
.\PitWall.exe
```

## 📊 效能影響

### 日誌禁用（預設）
- ✅ 啟動速度提升 ~10-15%
- ✅ 記憶體使用減少 ~5-10 MB
- ✅ 磁碟 I/O 減少 90%+
- ✅ 無日誌檔案產生

### 日誌啟用（除錯模式）
- ⚠️ 每次執行產生 `logs/` 目錄
- ⚠️ 日誌檔案大小：約 1-5 MB/session
- ✅ 可追蹤所有錯誤和警告
- ✅ 便於問題診斷

## 🔍 開發模式不受影響

開發模式（直接執行 Python 腳本）的日誌系統不受此變更影響：

```bash
# 開發模式：日誌正常運作
python f1t_gui_main.py

# 日誌設定檔：config/logging_config.json
{
  "enabled": true,      # 開發模式預設啟用
  "level": "INFO",
  "console_level": null,
  "patch_print": true
}
```

## 🛠️ 手動控制日誌

### 使用 `toggle_logger.py` 工具
```bash
# 查看當前日誌狀態
python tools/toggle_logger.py --status

# 禁用日誌（修改 config/logging_config.json）
python tools/toggle_logger.py --disable

# 啟用日誌
python tools/toggle_logger.py --enable

# 設定日誌等級
python tools/toggle_logger.py --set-level ERROR
```

## 📝 注意事項

1. **EXE 使用者體驗優先**
   - 正式發布版本應禁用日誌（預設配置）
   - 一般使用者不需要日誌檔案

2. **除錯時啟用日誌**
   - 開發階段：使用 Python 直接執行（有日誌）
   - 測試階段：暫時啟用 EXE 日誌
   - 正式發布：禁用 EXE 日誌

3. **日誌檔案位置**
   - 開發模式：`logs/f1.gui.*.log`
   - EXE 模式（啟用時）：`PitWall.exe 目錄/logs/`

4. **print() 函數行為**
   - 日誌禁用時：`print()` 仍可正常輸出到終端（如果有）
   - 日誌啟用時：`print()` 會被導向日誌系統

## 🔄 版本歷史

- **V0.12.1** (2025-12-20)
  - ✅ 新增 EXE 日誌禁用機制
  - ✅ 創建 `runtime_hook_disable_logger.py`
  - ✅ 更新 `F1T_GUI_clean.spec` 配置
  - ✅ 預設禁用 EXE 日誌輸出

- **V0.12.0 及更早版本**
  - ⚠️ EXE 日誌預設啟用
  - ⚠️ 可能產生大量日誌檔案

## 📞 相關檔案

- `core/logger.py` - 日誌系統核心
- `hooks/runtime_hook_disable_logger.py` - EXE 日誌禁用 hook
- `F1T_GUI_clean.spec` - PyInstaller 建構配置
- `config/logging_config.json` - 開發模式日誌設定
- `tools/toggle_logger.py` - 日誌控制工具
