# F1T GUI EXE 建構檢查清單 ✅

**檢查日期**: 2026-01-06  
**建構工具**: `build_exe_gui.py`  
**Spec 檔案**: `F1T_GUI_clean.spec`

---

## ✅ 環境狀態

### 1. Python 環境
- ✅ Python 3.13.5
- ✅ PyInstaller 6.17.0

### 2. 關鍵套件
- ✅ PyQt5
- ✅ pandas
- ✅ numpy
- ✅ matplotlib
- ✅ pyqtgraph
- ✅ requests
- ✅ fastf1

### 3. Strategy Simulator 模組
- ✅ `strategy_simulator.gui.main_window` 可導入
- ✅ `strategy_simulator.core.competitive_monte_carlo` 可導入
- ✅ `strategy_simulator.core.lap_simulator` 可導入
- ✅ `strategy_simulator.core.race_simulator` 可導入

### 4. Spec 配置
- ✅ `F1T_GUI_clean.spec` 存在
- ✅ 包含 `strategy_simulator` 模組導入
- ✅ 包含 `strategy_simulator` 資料夾打包

---

## 📋 已修復的問題

### 問題 1: Strategy Simulator 模組未包含
**症狀**: Spec 文件中缺少 `strategy_simulator` 的導入和打包配置

**修復**:
1. 在 `hidden_imports` 中添加：
   ```python
   'strategy_simulator',
   'strategy_simulator.gui',
   'strategy_simulator.gui.main_window',
   'strategy_simulator.core',
   'strategy_simulator.core.competitive_monte_carlo',
   # ... 等 30+ 個模組
   ```

2. 在 `added_files` 中添加：
   ```python
   (str(project_root / 'strategy_simulator'), 'strategy_simulator'),
   ```

---

## 🚀 建構步驟

### 方式 1: 使用 GUI 工具（推薦）
```powershell
python build_exe_gui.py
```
- 點擊「⚡ 一鍵建構 EXE」
- 預設使用系統 Python（不需虛擬環境）
- 預設使用單檔案模式（加密保護）

### 方式 2: 直接使用 PyInstaller
```powershell
python -m PyInstaller F1T_GUI_clean.spec --noconfirm
```

---

## 📊 輸出說明

### 單檔案模式（預設）
- **輸出**: `dist/F1T_GUI.exe`
- **重新命名**: `dist/F1-TelemetryStation-Pro-V0.12.1.exe`
- **特點**: 單一 EXE 檔案，加密保護，易於分發

### 目錄模式（開發用）
- **輸出**: `dist/F1T_GUI/` 資料夾
- **特點**: 啟動快，但無加密保護

---

## ⚠️ 注意事項

1. **日誌輸出**: EXE 模式下預設禁用日誌（透過 `runtime_hook_disable_logger.py`）

2. **控制台視窗**: 預設隱藏（`console=False`），除錯時可在 GUI 工具中勾選「EXE 顯示控制台視窗」

3. **建構時間**: 單檔案模式約需 3-5 分鐘

4. **檔案大小**: 預計約 300-400 MB（包含所有依賴）

---

## ✅ 確認清單

建構前請確認：
- [x] Python 3.13.5 已安裝
- [x] PyInstaller 6.17.0 已安裝
- [x] 所有關鍵套件已安裝
- [x] Strategy Simulator 可正常導入
- [x] F1T_GUI_clean.spec 包含所有必要模組
- [x] build_exe_gui.py 可執行

**✅ 所有檢查通過，可以開始建構！**

---

## 🎉 建構完成後

1. 測試 EXE 檔案：
   - 啟動應用程式
   - 測試 Strategy Simulator 功能
   - 確認所有分析模組正常

2. 分發：
   - 單檔案模式：直接分發 `.exe` 檔案
   - 目錄模式：壓縮整個資料夾

3. 版本號管理：
   - 更新 `config/version.py` 中的 `APP_VERSION`
   - 自動使用於檔案命名
