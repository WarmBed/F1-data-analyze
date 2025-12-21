# 🖼️ F1T GUI EXE 圖示顯示修復指南

## ✅ **診斷結果**

### 配置狀態
- ✅ ICO 檔案存在: `image\logo.ico` (94,912 bytes)
- ✅ ICO 檔案格式有效: 標頭 `00-00-01-00` (標準 ICO 格式)
- ✅ ICO 包含 6 個解析度層級 (從標頭可見)
- ✅ SPEC 配置正確: `icon='image\\logo.ico'`
- ✅ PyInstaller 建置成功，無圖示相關錯誤

### 問題原因
**Windows 圖示緩存 (Icon Cache)** 未刷新，導致檔案總管顯示預設 Python 圖示或舊圖示。

---

## 🔧 **解決方案（按順序嘗試）**

### 方法 1: 執行自動清除腳本 ⭐ 推薦
```powershell
# 在 PowerShell 中執行（以系統管理員身分）
.\fix_icon_cache.ps1
```

**此腳本會**:
1. 刪除 Windows 圖示緩存資料庫
2. 重啟 Windows Explorer 進程
3. 重建圖示緩存

---

### 方法 2: 手動清除圖示緩存
```powershell
# 步驟 1: 刪除緩存檔案
Remove-Item -Path "$env:LOCALAPPDATA\IconCache.db" -Force
Remove-Item -Path "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_*.db" -Force

# 步驟 2: 重啟 Explorer
Stop-Process -Name explorer -Force
Start-Sleep -Seconds 2
Start-Process explorer
```

---

### 方法 3: 使用 ie4uinit 命令
```powershell
# Windows 內建的圖示緩存刷新工具
ie4uinit.exe -show
```

---

### 方法 4: 重新命名 EXE（強制緩存失效）
```powershell
# 臨時重新命名以繞過緩存
Move-Item "dist\F1T_GUI.exe" "dist\F1T_GUI_v2.exe"
# 檢查 F1T_GUI_v2.exe 是否顯示正確圖示
```

---

### 方法 5: 重新啟動電腦
如果以上方法都無效，重新啟動電腦可完全清除所有緩存。

---

## 🧪 **驗證步驟**

### 檢查 EXE 是否包含圖示資源
```powershell
# 方法 1: 查看檔案屬性
Get-Item "dist\F1T_GUI.exe" | Select-Object Name, Length, LastWriteTime

# 方法 2: 在檔案總管中
# 1. 右鍵點擊 F1T_GUI.exe
# 2. 選擇「內容」
# 3. 查看圖示（應顯示自訂圖示，而非 Python 預設圖示）
```

### 檢查執行中的圖示
```powershell
# 執行 EXE
.\dist\F1T_GUI.exe

# 檢查以下位置的圖示:
# 1. 工作列圖示
# 2. ALT+TAB 視窗切換圖示
# 3. 工作管理員中的應用程式圖示
```

---

## 📊 **ICO 檔案技術資訊**

### 當前 logo.ico 規格
- **檔案大小**: 94,912 bytes (~95 KB)
- **格式**: 標準 Windows ICO
- **魔術數字**: `00 00 01 00` (有效)
- **解析度層級**: 6 個 (從標頭 byte 5 可見)
- **典型解析度**: 16×16, 32×32, 48×48, 64×64, 128×128, 256×256

### ICO vs PNG 比較
| 特性 | ICO | PNG |
|------|-----|-----|
| Windows 原生支援 | ✅ 是 | ⚠️ 需轉換 |
| 多解析度支援 | ✅ 內建 | ❌ 單一解析度 |
| 檔案總管顯示 | ✅ 完美 | ⚠️ 可能失真 |
| PyInstaller 支援 | ✅ 原生 | ⚠️ 有限 |

---

## ⚠️ **常見問題**

### Q1: 為什麼建置成功但看不到圖示？
**A**: Windows 會緩存檔案圖示，即使 EXE 已包含新圖示，檔案總管可能仍顯示舊緩存。

### Q2: 清除緩存後仍未顯示？
**A**: 嘗試:
1. 確認 logo.ico 不是損壞的檔案
2. 使用 `icon='image/logo.ico'` (正斜線) 而非 `image\\logo.ico`
3. 檢查 SPEC 檔案中的 `icon` 路徑是否正確
4. 重新建置: `pyinstaller F1T_GUI.spec --clean`

### Q3: 執行時工作列顯示預設圖示？
**A**: 這是 PyQt5 的問題，需要在程式碼中額外設定:
```python
app = QApplication(sys.argv)
app.setWindowIcon(QIcon('image/logo.ico'))  # 設定應用程式圖示
```

---

## 🔍 **進階診斷**

### 檢查 EXE 的 PE 資源
```powershell
# 使用 Resource Hacker 或 PE Explorer 工具
# 打開 F1T_GUI.exe
# 查看 Icon Group 資源
# 應該能看到嵌入的圖示資源
```

### 查看建置日誌
```powershell
Select-String -Path "build\F1T_GUI\warn-F1T_GUI.txt" -Pattern "icon|ICON" -Context 3
```

---

## 📝 **完整修復流程總結**

```powershell
# 1. 確認檔案存在
Test-Path "image\logo.ico"
Test-Path "dist\F1T_GUI.exe"

# 2. 清除圖示緩存
.\fix_icon_cache.ps1

# 3. 如果仍未顯示，重新建置
Remove-Item "build" -Recurse -Force
Remove-Item "dist" -Recurse -Force
pyinstaller F1T_GUI.spec --clean

# 4. 驗證新 EXE
Get-Item "dist\F1T_GUI.exe"

# 5. 如果還是沒有，重新啟動電腦
```

---

## ✅ **預期結果**

完成修復後，您應該看到:
- ✅ 檔案總管中的 F1T_GUI.exe 顯示自訂圖示（F1 相關圖示）
- ✅ 工作列顯示自訂圖示（執行時）
- ✅ ALT+TAB 視窗切換顯示自訂圖示
- ✅ EXE 內容視窗顯示自訂圖示

---

**建立時間**: 2025/10/22 19:15
**EXE 版本**: F1T_GUI.exe (192,128,657 bytes)
**ICO 檔案**: image/logo.ico (94,912 bytes, 6 解析度)
