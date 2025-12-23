# F1T GUI V0.7.0 - EXE 打包指南

## 📋 打包準備檢查清單

### ✅ 已完成項目

1. **版本更新**
   - [x] 版本號更新至 V0.7.0
   - [x] 版本歷史更新（8 項新功能）
   - [x] 發布日期：2025-11-08

2. **SPEC 文件配置**
   - [x] F1T_GUI.spec 已更新
   - [x] 添加 FIA Parts Analysis 模組
   - [x] 添加 Lap Analysis Linkage 模組
   - [x] 添加 Workspace 序列化模組
   - [x] 添加 Telemetry Base 模組

3. **Runtime Hook**
   - [x] pyinstaller_runtime_hook.py 已創建
   - [x] 日誌級別：CRITICAL（極度靜默）
   - [x] API 模式：production
   - [x] 緩存目錄設置：~/.f1telemetrystation/cache

4. **資源檔案**
   - [x] image/logo.png (554 KB)
   - [x] image/logo.ico (95 KB)
   - [x] 所有必要圖標完整

5. **打包腳本**
   - [x] build_exe.ps1 (完整版，含詳細報告)
   - [x] build_exe_quick.ps1 (快速版)
   - [x] check_ready.py (打包前檢查)

## 🚀 打包執行步驟

### 方法 1: 完整版打包（推薦）

```powershell
.\build_exe.ps1
```

**特點**：
- 完整的環境檢查
- 詳細的進度顯示
- 自動生成建置報告
- 驗證所有資源檔案

### 方法 2: 快速打包

```powershell
.\build_exe_quick.ps1
```

**特點**：
- 最小化輸出
- 快速打包
- 適合測試

### 方法 3: 手動打包

```powershell
# 清理舊檔案
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# 執行打包
python -m PyInstaller F1T_GUI.spec --clean --noconfirm
```

## 📦 打包配置說明

### SPEC 檔案關鍵配置

```python
# EXE 配置
exe = EXE(
    name='F1T_GUI',           # EXE 檔案名稱
    debug=False,              # 生產模式
    console=False,            # GUI 應用（無終端視窗）
    upx=True,                 # 啟用 UPX 壓縮
    icon='image\\logo.ico',   # 應用程式圖標
)
```

### Runtime Hook 配置

```python
# 環境變數設置
F1_LOG_LEVEL='CRITICAL'              # 極度靜默
F1T_API_MODE='production'            # 生產環境
F1T_API_BASE_URL='https://api.f1telemetrystationpro.org'
F1T_CACHE_DIR='~/.f1telemetrystation/cache'
```

## 📊 V0.7.0 新增功能

1. ✅ FIA Parts Analysis 模組完整多國語言化
2. ✅ 整合 color_palette_provider 車手與車隊顏色系統
3. ✅ 實作內容翻譯映射系統（變更類型、分類、描述）
4. ✅ 支援 Type 欄位英文提取
5. ✅ 支援 Description 欄位完整翻譯（6 種類型說明）
6. ✅ 顯示格式完全對齊 Ideal Ranking Table 標準
7. ✅ 新增 35 位車手名稱到代碼映射系統
8. ✅ 實作 Tooltip 顯示原始中英文內容

## 🔍 打包後驗證

### 檢查項目

1. **EXE 檔案**
   - 位置：`dist\F1T_GUI.exe`
   - 預期大小：約 200-300 MB
   - 檔案應有圖標

2. **資源檔案**
   - 檢查 `dist\_internal\image\` 目錄
   - 確認 logo.png 和 logo.ico 存在

3. **功能測試**
   - 啟動 EXE：`.\dist\F1T_GUI.exe`
   - 測試 FIA Parts Analysis 模組
   - 驗證多國語言功能
   - 檢查顏色配置是否正常

## ⚠️ 已知注意事項

1. **首次運行**
   - EXE 首次運行會解壓資源到臨時目錄
   - 可能需要 10-30 秒初始化
   - 會在用戶目錄創建緩存

2. **防毒軟體**
   - 部分防毒軟體可能誤報
   - 建議添加到白名單

3. **磁碟空間**
   - 打包過程需要約 5 GB 空間
   - EXE 檔案約 200-300 MB

4. **UPX 壓縮**
   - UPX 未安裝，EXE 會較大
   - 可選安裝 UPX 減小檔案大小

## 📝 建置報告

打包完成後會在 `dist\BUILD_REPORT.txt` 生成詳細報告，包含：

- 版本資訊
- 建置環境
- 建置配置
- EXE 資訊
- V0.7.0 新增功能
- 建置統計
- 注意事項

## 🎯 下一步

1. **執行檢查**
   ```powershell
   python check_ready.py
   ```

2. **開始打包**
   ```powershell
   .\build_exe.ps1
   ```

3. **測試 EXE**
   ```powershell
   .\dist\F1T_GUI.exe
   ```

4. **驗證功能**
   - 打開 FIA Parts Analysis
   - 切換語言測試
   - 檢查顏色配置

## 📞 支援資訊

如遇問題，請檢查：
- `dist\BUILD_REPORT.txt` - 建置報告
- PyInstaller 輸出日誌
- Windows 事件檢視器

---

**F1T Development Team**  
Version: V0.7.0  
Date: 2025-11-08
