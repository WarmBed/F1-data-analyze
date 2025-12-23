# F1T GUI V0.6.0 - EXE 測試驗證清單
**生成日期**: 2025-10-27  
**EXE 位置**: `dist\F1T_GUI.exe`  
**檔案大小**: 183 MB

---

## ✅ 已完成的改進

### 1. 版本號更新至 V0.6.0
- ✅ `config/version.py` - APP_VERSION = "V0.6.0"
- ✅ 版本歷史已更新
- ✅ 所有模組自動使用新版本號

### 2. Windows 任務欄圖標修復
- ✅ 添加 App User Model ID 設定
- ✅ 應用程式層級圖標設定
- ✅ Windows 平台檢測邏輯

### 3. PyInstaller 打包配置
- ✅ `.spec` 檔案已包含 `icon='image\\logo.ico'`
- ✅ Logo 圖標已打包到 EXE 中
- ✅ 所有隱藏導入已配置

---

## 🧪 測試驗證清單

### 階段 1: 基礎功能測試
- [ ] **EXE 啟動**: 雙擊 `dist\F1T_GUI.exe` 能否正常啟動
- [ ] **啟動畫面**: 顯示 "V0.6.0" 版本號
- [ ] **主視窗標題**: 顯示 "F1 TelemetryStation Pro V0.6.0"
- [ ] **無錯誤彈窗**: 啟動過程無錯誤訊息

### 階段 2: 圖標顯示測試
- [ ] **檔案總管圖標**: `F1T_GUI.exe` 顯示 F1T Logo
- [ ] **任務欄圖標**: 執行時任務欄顯示 F1T Logo（不是 Python 圖標）
- [ ] **Alt+Tab 圖標**: 切換視窗時顯示 F1T Logo
- [ ] **任務管理員圖標**: 任務管理員中顯示 F1T Logo

### 階段 3: 功能完整性測試
- [ ] **主選單載入**: 所有選單項目正常顯示
- [ ] **模組載入**: 點擊任一分析模組無錯誤
- [ ] **API 連接**: 能夠連接到 API 服務
- [ ] **數據載入**: 能夠正常載入分析數據

### 階段 4: 效能測試
- [ ] **啟動速度**: < 10 秒完成啟動
- [ ] **記憶體使用**: 初始 < 500 MB
- [ ] **CPU 使用**: 閒置時 < 5%
- [ ] **無記憶體洩漏**: 長時間執行記憶體穩定

---

## 🔧 疑難排解

### 問題 1: 任務欄仍顯示 Python 圖標

**解決方案 A - 清除圖標緩存**:
```powershell
# 執行清除腳本（已提供）
.\clear_icon_cache.ps1
```

**解決方案 B - 手動清除**:
```powershell
# 1. 關閉檔案總管
Stop-Process -Name explorer -Force

# 2. 刪除圖標緩存
Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force

# 3. 重新啟動檔案總管
Start-Process explorer
```

**解決方案 C - 重新啟動系統**:
- 完全重新啟動電腦
- 重新執行 `F1T_GUI.exe`

### 問題 2: 啟動畫面未顯示 V0.6.0

**檢查項目**:
1. 確認執行的是最新打包的 EXE
2. 檢查 `dist\image\logo.png` 是否存在
3. 查看啟動日誌輸出

### 問題 3: 模組載入失敗

**檢查項目**:
1. 確認所有依賴已打包（檢查打包日誌中的 WARNING）
2. 檢查是否有 "Hidden import not found" 錯誤
3. 驗證 `.spec` 檔案中的 `hiddenimports` 列表

---

## 📋 關鍵代碼變更

### 1. App User Model ID 設定
**檔案**: `f1t_gui_main.py` - `main()` 函數

```python
# Windows 任務欄圖標設定
if sys.platform == 'win32':
    import ctypes
    myappid = 'F1T.ProfessionalRacingAnalysis.GUI.V060'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
```

### 2. 應用程式圖標設定
**檔案**: `f1t_gui_main.py` - `main()` 函數

```python
# 設置應用程式圖標（應用程式層級）
icon_path = get_resource_path(Path("image") / "logo.ico")
if icon_path.exists():
    app.setWindowIcon(QIcon(str(icon_path)))
```

### 3. 版本號定義
**檔案**: `config/version.py`

```python
APP_VERSION = "V0.6.0"
APP_NAME = "F1 TelemetryStation Pro"
APP_FULL_TITLE = f"{APP_NAME} {APP_VERSION}"
```

---

## 🎯 預期結果

### 視覺效果
1. **啟動畫面**:
   - 白底黑字極簡風格
   - 顯示 "F1 TelemetryStation Pro"
   - 右下角顯示 "V0.6.0"
   - 進度條動畫

2. **主視窗**:
   - 標題欄: "F1 TelemetryStation Pro V0.6.0"
   - 圖標: F1T Logo
   - 完整功能選單

3. **任務欄**:
   - 圖標: F1T Logo（不是 Python 圖標）
   - 懸停顯示: "F1T Professional Racing Analysis Workstation"
   - 右鍵選單正常

### 技術效果
1. **Windows 識別**:
   - App User Model ID: `F1T.ProfessionalRacingAnalysis.GUI.V060`
   - 獨立應用程式識別（不與其他 Python 程式群組）

2. **資源整合**:
   - 所有圖標資源已打包
   - 啟動畫面資源正常載入
   - 無外部依賴

---

## 📝 測試日誌範本

```
測試日期: _________________
測試人員: _________________
EXE 版本: V0.6.0
測試環境: Windows __________

階段 1: 基礎功能
[ ] EXE 啟動 - 結果: _______________
[ ] 啟動畫面 - 版本號: _______________
[ ] 主視窗標題 - 顯示: _______________
[ ] 錯誤訊息 - 有/無: _______________

階段 2: 圖標顯示
[ ] 檔案總管 - 圖標: _______________
[ ] 任務欄 - 圖標: _______________
[ ] Alt+Tab - 圖標: _______________
[ ] 任務管理員 - 圖標: _______________

階段 3: 功能測試
[ ] 選單載入 - 結果: _______________
[ ] 模組載入 - 結果: _______________
[ ] API 連接 - 結果: _______________
[ ] 數據載入 - 結果: _______________

階段 4: 效能
啟動時間: _______ 秒
初始記憶體: _______ MB
CPU 使用: _______ %

問題記錄:
_________________________________
_________________________________
_________________________________

總體評價: [ ] 通過  [ ] 需要修正
```

---

## 🚀 下一步

### 立即測試
```powershell
# 執行 EXE
.\dist\F1T_GUI.exe
```

### 如果圖標未正確顯示
```powershell
# 執行清除腳本
.\clear_icon_cache.ps1
```

### 如果需要重新打包
```powershell
# 清理並重新打包
Remove-Item -Path "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue
pyinstaller F1T_GUI.spec --clean
```

---

**測試完成後請回報結果！** 🎯
