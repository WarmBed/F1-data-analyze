# NSSM 日誌目錄遷移指南

## 📋 變更說明

**日期**: 2025-10-13  
**變更內容**: 將 NSSM 服務日誌從 `logs/` 目錄遷移到 `nssm/logs/` 目錄

### 變更前
```
logs/
├── f1t-api.log
├── f1t-api.error.log
├── periodic-update.log
├── periodic-update.error.log
├── cloudflare-tunnel.log
├── cloudflare-tunnel.error.log
├── f1_gui.log               # GUI 應用程式日誌（保留在 logs/）
├── f1_cli.log               # CLI 應用程式日誌（保留在 logs/）
└── ...
```

### 變更後
```
nssm/logs/                    # ← 新位置：NSSM 服務專用
├── f1t-api.log
├── f1t-api.error.log
├── periodic-update.log
├── periodic-update.error.log
├── cloudflare-tunnel.log
└── cloudflare-tunnel.error.log

logs/                         # ← 保留：一般應用程式日誌
├── f1_gui.log
├── f1_cli.log
├── f1_api_*.log             # API 手動執行日誌
└── ...
```

## 🎯 變更原因

1. **清晰的組織結構**: NSSM 服務日誌與一般應用程式日誌分開
2. **易於管理**: 所有 NSSM 相關檔案集中在 `nssm/` 目錄
3. **避免混淆**: 區分服務模式日誌和手動執行日誌
4. **便於維護**: 獨立的 `.gitignore` 和清理腳本

## 🚀 遷移步驟

### 步驟 1: 停止所有服務（需要管理員權限）
```powershell
.\nssm\Stop_All_Services.bat
```

或使用 PowerShell：
```powershell
Stop-Service F1T-*
```

### 步驟 2: 遷移現有日誌檔案
```powershell
.\nssm\migrate-logs.ps1
```

此腳本會自動：
- 檢查 `logs/` 目錄中的 NSSM 日誌
- 移動到 `nssm\logs/` 目錄
- 如果目標檔案已存在，則合併內容
- 顯示遷移摘要

### 步驟 3: 重新安裝服務（更新日誌路徑）
```powershell
# 以管理員身份執行
.\nssm\install-services-admin.ps1
```

此腳本會：
- 自動檢測現有服務
- 詢問是否要重新安裝（輸入 Y）
- 使用新的日誌路徑重新配置服務

### 步驟 4: 啟動服務
```powershell
.\nssm\Start_All_Services.bat
```

### 步驟 5: 驗證日誌位置
```powershell
.\nssm\Check_Service_Status.bat
```

檢查 "LOG FILES STATUS" 部分，確認日誌檔案在 `nssm\logs\` 目錄。

## 📝 已更新的檔案

### 配置檔案
- ✅ `nssm/install-services.ps1` - 日誌目錄改為 `$PSScriptRoot\logs`
- ✅ `nssm/Check_Service_Status.bat` - 日誌目錄改為 `%SCRIPT_DIR%logs`

### 新增檔案
- ✅ `nssm/logs/.gitignore` - 忽略所有 `.log` 檔案
- ✅ `nssm/logs/README.md` - 日誌目錄說明文件
- ✅ `nssm/migrate-logs.ps1` - 自動遷移腳本
- ✅ `nssm/NSSM_LOG_MIGRATION_GUIDE.md` - 本文件

### VS Code 任務
- ✅ `tasks.json` - 已更新為使用 `.bat` 檔案
- ✅ `launch.json` - 已更新為使用 `.bat` 檔案

## 🔍 驗證日誌輸出

執行以下命令確認服務正在寫入新位置：

```powershell
# 查看 API 服務最新日誌
Get-Content .\nssm\logs\f1t-api.log -Tail 20

# 即時監控日誌
Get-Content .\nssm\logs\f1t-api.log -Wait -Tail 10

# 檢查所有日誌檔案
Get-ChildItem .\nssm\logs\*.log | Select-Object Name, Length, LastWriteTime
```

## ⚠️ 故障排除

### 問題 1: 服務無法啟動
**原因**: 日誌目錄不存在  
**解決方案**:
```powershell
New-Item -ItemType Directory -Force -Path "nssm\logs"
Restart-Service F1T-*
```

### 問題 2: 日誌檔案仍在舊位置
**原因**: 服務配置未更新  
**解決方案**:
```powershell
# 檢查服務配置
.\nssm\nssm.exe get F1T-API AppStdout
.\nssm\nssm.exe get F1T-API AppStderr

# 應該顯示: C:\Users\...\nssm\logs\f1t-api.log
```

如果顯示舊路徑，重新執行步驟 3（重新安裝服務）。

### 問題 3: 權限錯誤
**原因**: NSSM 服務無法寫入 `nssm\logs\` 目錄  
**解決方案**:
```powershell
# 確保目錄權限正確
icacls "nssm\logs" /grant "NT AUTHORITY\SYSTEM:(OI)(CI)F"
icacls "nssm\logs" /grant "NT AUTHORITY\LOCAL SERVICE:(OI)(CI)F"
```

## 📊 日誌管理最佳實踐

### 定期清理
```powershell
# 刪除 7 天前的日誌
Get-ChildItem .\nssm\logs\*.log | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | 
    Remove-Item -Verbose
```

### 日誌輪替
```powershell
# 配置 NSSM 自動輪替（每天或 10MB）
.\nssm\nssm.exe set F1T-API AppRotateFiles 1
.\nssm\nssm.exe set F1T-API AppRotateOnline 1
.\nssm\nssm.exe set F1T-API AppRotateSeconds 86400
.\nssm\nssm.exe set F1T-API AppRotateBytes 10485760

# 對其他服務重複以上命令
.\nssm\nssm.exe set F1T-PeriodicUpdate AppRotateFiles 1
# ...
```

### 監控日誌大小
```powershell
# 查看所有日誌總大小
$totalSize = (Get-ChildItem .\nssm\logs\*.log | Measure-Object -Property Length -Sum).Sum
$totalMB = [math]::Round($totalSize / 1MB, 2)
Write-Host "Total log size: $totalMB MB"
```

## ✅ 完成檢查清單

遷移完成後，請確認以下項目：

- [ ] 所有服務已停止
- [ ] `migrate-logs.ps1` 執行成功
- [ ] `install-services.ps1` 重新安裝服務
- [ ] 所有服務已啟動
- [ ] `Check_Service_Status.bat` 顯示新的日誌路徑
- [ ] 新日誌檔案正在寫入 `nssm\logs\` 目錄
- [ ] VS Code 任務可以正常執行
- [ ] 舊的 `logs/` 目錄中 NSSM 日誌已移除

## 🎊 完成！

日誌遷移完成後，您的 NSSM 服務日誌將集中管理在 `nssm\logs\` 目錄中。

如有任何問題，請參考：
- `nssm\README.md` - NSSM 快速指南
- `nssm\NSSM_GUIDE.md` - 詳細文檔
- `nssm\logs\README.md` - 日誌管理說明
