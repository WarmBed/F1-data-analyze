# 🚀 F1T GUI EXE 生成指南

## 📅 **更新日期**: 2025年10月22日

---

## ✅ **SPEC 檔案檢查結果**

### **階段 1: 關鍵模組檢查**
✅ Track Analysis 子模組 (5個) - 完整
✅ Lap Analysis Linkage 模組 (2個) - 完整
✅ Workspace 序列化模組 (4個) - 完整
✅ Telemetry Base 模組 (2個) - 完整

### **階段 2: Runtime Hook**
✅ `pyinstaller_runtime_hook.py` - 已創建
- 功能：自動設置 `F1_LOG_LEVEL=CRITICAL`（EXE 極度靜默模式）
- 位置：專案根目錄

### **階段 3: 資源檔案**
✅ `image/logo.png` - Splash Screen Logo
✅ `image/logo.ico` - 應用程式圖標

### **階段 4: EXE 配置**
✅ Console 模式: **False** (GUI 應用程式，無終端視窗)
✅ Debug 模式: **False** (生產環境)
✅ UPX 壓縮: **已啟用** (減小檔案大小)
✅ 應用程式圖標: `image/logo.ico`

---

## 📋 **生成 EXE 步驟**

### **1️⃣ 清理舊檔案**
```powershell
# 刪除舊的 build 和 dist 目錄
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
```

### **2️⃣ 執行 PyInstaller**
```powershell
# 使用 SPEC 檔案生成 EXE
pyinstaller F1T_GUI.spec --clean
```

**參數說明**：
- `--clean`: 清理 PyInstaller 緩存，確保全新打包
- `F1T_GUI.spec`: 使用自訂的 SPEC 配置檔案

### **3️⃣ 等待生成完成**
打包過程預計需要 **5-15 分鐘**（視電腦性能而定）

生成過程中會顯示：
```
Building EXE from EXE-00.toc...
Building COLLECT because COLLECT-00.toc is non existent
Copying files to dist\F1T_GUI\...
Building Analysis...
...
```

### **4️⃣ 檢查輸出**
生成完成後，EXE 檔案位於：
```
dist/
└── F1T_GUI.exe  (單一檔案，約 150-300 MB)
```

---

## 🧪 **測試 EXE**

### **基本功能測試**
1. **啟動測試**：
   ```powershell
   # 直接執行 EXE
   .\dist\F1T_GUI.exe
   ```
   - ✅ 無終端視窗
   - ✅ 顯示 Splash Screen
   - ✅ 主視窗正常顯示

2. **語言切換測試**：
   - Language → 中文 ✅
   - Language → English ✅
   - Language → 日本語 ✅

3. **模組載入測試**：
   - Lap Analysis → 油門分析 (スロットル分析) ✅
   - Track Analysis ✅
   - Rain Analysis ✅
   - Tire Analysis ✅

4. **API 連接測試**：
   - 選擇賽事並載入數據
   - 確認 API 請求正常
   - 圖表正常顯示

### **進階功能測試**
1. **Workspace 序列化**：
   - 保存 Workspace ✅
   - 載入 Workspace ✅
   - 分頁彈出/返回 ✅

2. **Tab 重命名**：
   - 創建新分頁 ✅
   - 右鍵重命名 ✅
   - 重複名稱處理 ✅

3. **日文翻譯**：
   - 切換到日文 ✅
   - 開啟油門分析（スロットル分析）✅
   - 圖表更新正常 ✅

---

## 📂 **SPEC 檔案摘要**

### **隱藏導入模組總數**: 200+ 個

包括：
- ✅ Throttle Analysis（完整）
- ✅ Detailed Lap Analysis（完整）
- ✅ Lap Box Plot Analysis（完整）
- ✅ Lap Analysis Chart Widgets（6 種分析）
- ✅ Championship/Standings 模組（3 個）
- ✅ Weather Timeline 模組
- ✅ Ideal Lap Analysis（3 種視圖）
- ✅ Track Analysis（完整）
- ✅ Workspace 序列化
- ✅ Linkage 模組
- ✅ All Drivers 分析（2 種）
- ✅ 第三方庫依賴（Matplotlib, Pandas, NumPy 等）

### **數據檔案**:
```python
datas=[
    ('image/logo.png', 'image'),  # Splash screen logo
    ('image/logo.ico', 'image'),  # Application icon
    # GUI 使用 API-ONLY 模式,不打包 JSON
]
```

### **Runtime Hook**:
```python
runtime_hooks=['pyinstaller_runtime_hook.py']
```

功能：
- 設置 `F1_LOG_LEVEL=CRITICAL`（EXE 極度靜默）
- 設置資源路徑 `F1T_RESOURCE_PATH`
- 設置配置目錄 `F1T_CONFIG_DIR`

---

## ⚠️ **常見問題**

### **Q1: 生成失敗，顯示 "ModuleNotFoundError"**
**A**: 檢查該模組是否在 `hiddenimports` 中，如果缺失則添加到 SPEC 檔案。

### **Q2: EXE 啟動後閃退**
**A**: 
1. 使用終端執行 EXE 查看錯誤訊息：
   ```powershell
   .\dist\F1T_GUI.exe
   ```
2. 檢查 `logs/f1_gui_*.log` 日誌檔案

### **Q3: 圖標沒有正確顯示**
**A**: 確認 `image/logo.ico` 檔案存在且格式正確（ICO 格式）。

### **Q4: EXE 檔案過大（> 500 MB）**
**A**: 
- 確認 UPX 壓縮已啟用（`upx=True`）
- 檢查是否誤打包了 `json/` 或其他大型資料夾
- 考慮使用 `excludes` 排除不必要的模組

### **Q5: 日文翻譯無法使用**
**A**: 
- ✅ 已修復（2025-10-22）
- 確認 SPEC 包含所有 Lap Analysis 模組
- 確認視窗標題檢測邏輯包含日文翻譯

---

## 🎯 **最佳實踐**

### **打包前檢查清單**
- [ ] ✅ 執行 `python check_spec.py` 驗證 SPEC 完整性
- [ ] ✅ 確認 `pyinstaller_runtime_hook.py` 存在
- [ ] ✅ 確認 `image/logo.png` 和 `image/logo.ico` 存在
- [ ] ✅ 清理舊的 `build/` 和 `dist/` 目錄
- [ ] ✅ 確認 Python 版本與開發環境一致

### **打包後測試清單**
- [ ] EXE 可正常啟動（無終端視窗）
- [ ] Splash Screen 正常顯示
- [ ] 主視窗載入正常
- [ ] 語言切換功能正常（中/英/日）
- [ ] 至少測試 3 個分析模組
- [ ] API 連接功能正常
- [ ] Workspace 儲存/載入功能正常
- [ ] Tab 重命名功能正常

---

## 📊 **版本資訊**

- **應用程式名稱**: F1 TelemetryStation Pro
- **版本號**: 請參考 `config/version.py` 中的 `APP_VERSION`
- **Python 版本**: 3.11+
- **PyInstaller 版本**: 最新版本
- **目標平台**: Windows 10/11 (64-bit)

---

## 🔄 **後續維護**

### **新增模組時**
1. 在 `F1T_GUI.spec` 的 `hiddenimports` 中添加新模組
2. 執行 `python check_spec.py` 驗證
3. 重新生成 EXE 並測試

### **更新依賴時**
1. 更新 `requirements.txt`
2. 確認新依賴是否需要添加到 `hiddenimports`
3. 重新生成 EXE 並完整測試

### **修改 Runtime Hook**
1. 編輯 `pyinstaller_runtime_hook.py`
2. 使用 `--clean` 參數重新打包
3. 測試環境變數是否正確設置

---

## ✅ **準備完成！**

現在您可以執行以下命令開始生成 EXE：

```powershell
# 清理舊檔案
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue

# 生成 EXE
pyinstaller F1T_GUI.spec --clean
```

**預計時間**: 5-15 分鐘
**輸出位置**: `dist/F1T_GUI.exe`

---

**🎉 祝您打包順利！** 🎉
