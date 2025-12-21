# 🚀 快速啟動參考卡

## 📌 一鍵啟動（按 F5）

### 開發場景

| 場景 | 配置名稱 | 用途 |
|------|---------|------|
| 🎨 **純 GUI 開發** | `🎯 只啟動 GUI` | 前端開發，使用遠程 API |
| 🔧 **全棧開發** | `🚀 GUI + API (本地開發)` | 前後端聯調，本地 API |
| 🧪 **測試** | `Python: Pytest` | 執行所有單元測試 |

---

### 建置場景

| 場景 | 配置名稱 | 用途 |
|------|---------|------|
| 📦 **打包 EXE** | `📦 打包 EXE (PyInstaller)` | 使用 PyInstaller 打包 GUI |
| 🧹 **清理重建** | `📦 清理並重新打包 EXE` | 清理舊版本並重新打包 |

---

### 生產測試場景

| 場景 | 配置名稱 | 用途 |
|------|---------|------|
| 🌐 **對外 API** | `🌐 API + Cloudflare Tunnel` | 啟動 API 並對外開放 |
| 🌍 **完整系統** | `🌍 完整系統 (API + Tunnel + GUI)` | API + Tunnel + GUI 同時運行 |

---

## 🎯 發布前檢查清單

### 步驟 1：打包 EXE
```
在 VS Code 中：
1. 按 Ctrl+Shift+D（調試面板）
2. 選擇 "📦 打包 EXE (PyInstaller)"
3. 按 F5 開始打包
```

或使用命令行：
```powershell
python -m PyInstaller F1T_GUI.spec
```

### 步驟 2：測試 EXE
```powershell
# 手動執行 EXE 測試
.\dist\F1T_GUI.exe

# 或使用調試模式
.\dist\F1T_GUI.exe --debug --console
```

### 步驟 3：檢查基本功能
- [ ] EXE 正常啟動
- [ ] 主視窗正常顯示
- [ ] 無錯誤彈窗

### 步驟 4：測試 API 整合
- [ ] 啟動本地 API：`Python: API server`
- [ ] 測試數據載入
- [ ] 測試分析功能

### 步驟 5：完整系統測試
- [ ] 使用 `🌍 完整系統 (API + Tunnel + GUI)` 配置
- [ ] 測試遠程 API 連接
- [ ] 驗證所有模組正常

### 步驟 6：檢查日誌
- [ ] `dist/logs/f1_gui_*.log` 無嚴重錯誤
- [ ] 所有功能測試通過

### 步驟 6：準備發布
- [ ] 壓縮 `dist/` 目錄
- [ ] 準備發布說明
- [ ] 更新版本號

---

## 📁 快速路徑

| 項目 | 路徑 |
|------|------|
| EXE 執行檔 | `dist/F1T_GUI.exe` |
| EXE 依賴 | `dist/_internal/` |
| 日誌目錄 | `dist/logs/` |
| API 文檔 | `http://localhost:8000/docs` |
| 遠程 API | `https://api.f1telemetrystationpro.org` |

---

## 🐛 常見問題

### EXE 無法啟動
```
解決方案：
1. 使用 "🏎️ F1T GUI (EXE - 調試模式)"
2. 查看 dist/logs/ 日誌
3. 檢查 _internal/ 完整性
```

### API 連接失敗
```
解決方案：
1. 確認 API 服務已啟動
2. 檢查防火牆設置
3. 驗證網址配置
```

### Pitstop 重複視窗問題
```
解決方案：
1. 查看 FIX_GUIDE_Pitstop_Duplication.md
2. 檢查 API-ONLY 模式修復
3. 避免手動創建遙測視窗
```

---

## 💡 小技巧

### 快速重新打包
```powershell
# 清理舊版本
Remove-Item dist -Recurse -Force

# 重新打包
python -m PyInstaller F1T_GUI.spec

# 快速測試
# 按 F5 → 選擇 "🏎️ F1T GUI (EXE - 調試模式)"
```

### 查看最新日誌
```powershell
# PowerShell
Get-Content dist/logs/f1_gui_*.log -Tail 50
```

### API 健康檢查
```powershell
# 檢查本地 API
Invoke-WebRequest http://localhost:8000/health

# 檢查遠程 API
Invoke-WebRequest https://api.f1telemetrystationpro.org/health
```

---

**快速啟動**：按 `Ctrl+Shift+D` → 選擇配置 → 按 `F5` 🚀
