# F1T NSSM 服務管理系統 - 完整指南

**版本**: 1.0.0  
**建立日期**: 2025-10-13  
**適用平台**: Windows 10/11  
**需求**: PowerShell 5.1+, 管理員權限

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [安裝步驟](#安裝步驟)
3. [服務管理](#服務管理)
4. [進階配置](#進階配置)
5. [故障排除](#故障排除)
6. [最佳實踐](#最佳實踐)

---

## 🎯 系統概述

### **什麼是 NSSM？**

NSSM (Non-Sucking Service Manager) 是 Windows 上最佳的第三方服務管理工具：

| 功能 | NSSM | PowerShell Jobs | Supervisor |
|------|------|----------------|-----------|
| **Windows 原生支援** | ✅ 完整 | ✅ 有限 | ❌ 不支援 |
| **自動重啟** | ✅ 內建 | ❌ 需手動 | N/A |
| **開機自啟** | ✅ 簡單 | ⚠️ 複雜 | N/A |
| **GUI 管理** | ✅ services.msc | ❌ 無 | N/A |
| **日誌重定向** | ✅ 完整 | ⚠️ 基本 | N/A |
| **服務依賴** | ✅ 支援 | ❌ 無 | N/A |
| **崩潰恢復** | ✅ 自動 | ❌ 無 | N/A |

### **F1T 服務架構**

本系統管理 3 個核心服務：

```
┌─────────────────────────────────────────────────────┐
│                   F1T 服務架構                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────┐                               │
│  │  F1T-API        │  REST API 服務                 │
│  │  Port: 8000     │  refactored_api.py            │
│  └────────┬────────┘                               │
│           │                                        │
│           │ (依賴)                                 │
│           ↓                                        │
│  ┌─────────────────┐                               │
│  │ PeriodicUpdate  │  定時更新服務                  │
│  │ Scheduler       │  periodic_update_service.py   │
│  └─────────────────┘                               │
│                                                     │
│  ┌─────────────────┐                               │
│  │ Cloudflare      │  公開 API 到網際網路            │
│  │ Tunnel          │  cloudflared.exe              │
│  └─────────────────┘                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📦 安裝步驟

### **步驟 1: 下載並安裝 NSSM**

以**管理員權限**執行 PowerShell：

```powershell
# 方式 A: 自動下載安裝（推薦）
.\nssm\install-nssm.ps1

# 方式 B: 手動下載
# 1. 訪問 https://nssm.cc/download
# 2. 下載 nssm-2.24.zip
# 3. 解壓縮到 nssm\ 目錄
```

**安裝過程**：
```
[1/6] Checking system architecture...
  System: Windows win64
  OK 64-bit system detected

[2/6] Checking existing NSSM installation...
  (如果已安裝，可選擇跳過)

[3/6] Creating download directory...
  OK Directory created: nssm\downloads

[4/6] Downloading NSSM 2.24...
  URL: https://nssm.cc/release/nssm-2.24.zip
  OK Downloaded successfully (0.57MB)

[5/6] Extracting NSSM...
  OK Extracted to: nssm\nssm-2.24

[6/6] Verifying NSSM installation...
  OK NSSM executable found: nssm\nssm-2.24\win64\nssm.exe
  Version: NSSM 2.24 2014-08-31
  OK Shortcut created: nssm\nssm.exe
```

**驗證安裝**：
```powershell
.\nssm\nssm.exe version
# 輸出: NSSM 2.24 2014-08-31
```

---

### **步驟 2: 安裝 F1T 服務**

以**管理員權限**執行：

```powershell
.\nssm\install-services.ps1
```

**安裝過程**：
```
[1/8] Locating NSSM...
  OK NSSM found: nssm\nssm.exe

[2/8] Project root: C:\...\F1-data-analyze

[3/8] Locating Python...
  OK Python: C:\...\python.exe

[4/8] Creating logs directory...
  OK Created: logs

[5/8] Checking for existing services...
  (如果已存在，提示是否重新安裝)

[6/8] Installing services...

  Installing: F1T-API
    Display: F1T Telemetry API Server
    Creating service...
    Configuring...
    OK Installed successfully

  Installing: F1T-PeriodicUpdate
    Display: F1T Periodic Update Service
    Creating service...
    Configuring...
    OK Installed successfully

  Installing: F1T-CloudflareTunnel
    Display: F1T Cloudflare Tunnel
    Creating service...
    Configuring...
    OK Installed successfully

[7/8] Configuring service dependencies...
  OK F1T-PeriodicUpdate depends on F1T-API

[8/8] Verifying installation...
  OK F1T-API: Status=Stopped, StartType=Automatic
  OK F1T-PeriodicUpdate: Status=Stopped, StartType=Automatic
  OK F1T-CloudflareTunnel: Status=Stopped, StartType=Automatic

============================================================
 Service Installation Complete!
============================================================

Results:
  Installed: 3 / 3
  Verified:  3 / 3

Start all services now? (y/n)
```

---

## 🚀 服務管理

### **基本命令**

```powershell
# === 啟動服務 ===
.\nssm\manage-services.ps1 -Action Start              # 啟動所有服務
.\nssm\manage-services.ps1 -Action Start -Service F1T-API  # 啟動單一服務

# === 停止服務 ===
.\nssm\manage-services.ps1 -Action Stop               # 停止所有服務
.\nssm\manage-services.ps1 -Action Stop -Service F1T-API   # 停止單一服務

# === 重啟服務 ===
.\nssm\manage-services.ps1 -Action Restart            # 重啟所有服務

# === 查看狀態 ===
.\nssm\manage-services.ps1 -Action Status             # 查看所有狀態
.\nssm\manage-services.ps1                            # 預設顯示狀態

# === 開啟日誌目錄 ===
.\nssm\manage-services.ps1 -Action Logs               # 用檔案總管開啟
```

---

### **狀態輸出範例**

```powershell
PS> .\nssm\manage-services.ps1 -Action Status

============================================================
F1T Service Manager - Status Services
============================================================

Service Status:
============================================================

  F1T-API
    Status:      Running         ✅
    Start Type:  Automatic
    Display:     F1T Telemetry API Server

  F1T-PeriodicUpdate
    Status:      Running         ✅
    Start Type:  Automatic
    Display:     F1T Periodic Update Service

  F1T-CloudflareTunnel
    Status:      Running         ✅
    Start Type:  Automatic
    Display:     F1T Cloudflare Tunnel

Process Information:
============================================================

  Python
    PID:     12345
    CPU:     15.2s
    Memory:  85.6MB

  Python
    PID:     12346
    CPU:     8.7s
    Memory:  62.3MB

  Cloudflared
    PID:     12347
    CPU:     120.5s
    Memory:  28.9MB

Recent Log Activity:
============================================================

  f1t-api.log
    Size:    2.5MB
    Updated: 30s ago

  periodic-update.log
    Size:    1.2MB
    Updated: 1m ago

  cloudflare-tunnel.log
    Size:    0.8MB
    Updated: 45s ago
```

---

### **使用 Windows 服務管理器**

```powershell
# 開啟 Windows 服務管理器
services.msc
```

在 GUI 中可以：
- ✅ 啟動/停止/重啟服務
- ✅ 查看服務狀態
- ✅ 修改啟動類型（自動/手動/停用）
- ✅ 設定服務依賴
- ✅ 查看服務屬性
- ✅ 設定恢復選項

---

## 🔧 進階配置

### **修改服務參數**

使用 NSSM 直接修改：

```powershell
# 修改應用程式路徑
.\nssm\nssm.exe set F1T-API Application "C:\path\to\python.exe"

# 修改應用程式參數
.\nssm\nssm.exe set F1T-API AppParameters "refactored_api.py --port 8080"

# 修改工作目錄
.\nssm\nssm.exe set F1T-API AppDirectory "C:\path\to\project"

# 修改啟動類型
.\nssm\nssm.exe set F1T-API Start SERVICE_AUTO_START    # 自動
.\nssm\nssm.exe set F1T-API Start SERVICE_DEMAND_START  # 手動
.\nssm\nssm.exe set F1T-API Start SERVICE_DISABLED      # 停用

# 修改重啟延遲（毫秒）
.\nssm\nssm.exe set F1T-API AppRestartDelay 10000       # 10 秒
```

---

### **配置自動重啟**

```powershell
# 設定崩潰後自動重啟
.\nssm\nssm.exe set F1T-API AppExit Default Restart

# 設定重啟延遲（毫秒）
.\nssm\nssm.exe set F1T-API AppRestartDelay 5000        # 5 秒

# 設定重啟節流（避免頻繁重啟）
.\nssm\nssm.exe set F1T-API AppThrottle 1500            # 1.5 秒內重啟視為失敗
```

---

### **配置日誌輪轉**

```powershell
# 啟用日誌輪轉（當檔案達到指定大小時自動輪轉）
.\nssm\nssm.exe set F1T-API AppStdoutRotateFiles 5     # 保留 5 個備份
.\nssm\nssm.exe set F1T-API AppStdoutRotateBytes 10485760  # 10MB 輪轉

.\nssm\nssm.exe set F1T-API AppStderrRotateFiles 5
.\nssm\nssm.exe set F1T-API AppStderrRotateBytes 10485760
```

---

### **設定環境變數**

```powershell
# 新增環境變數
.\nssm\nssm.exe set F1T-API AppEnvironmentExtra "DEBUG=true" "LOG_LEVEL=INFO"

# 查看當前環境變數
.\nssm\nssm.exe get F1T-API AppEnvironmentExtra
```

---

### **配置服務依賴**

```powershell
# 設定依賴（PeriodicUpdate 依賴 API）
.\nssm\nssm.exe set F1T-PeriodicUpdate DependOnService F1T-API

# 查看依賴
.\nssm\nssm.exe get F1T-PeriodicUpdate DependOnService

# 移除依賴
.\nssm\nssm.exe reset F1T-PeriodicUpdate DependOnService
```

---

## 🛠️ 故障排除

### **問題 1: 服務無法啟動**

**症狀**: 服務狀態顯示 "Stopped"，啟動後立即停止

**診斷步驟**:
```powershell
# 1. 查看錯誤日誌
Get-Content logs\f1t-api.error.log -Tail 50

# 2. 手動測試應用程式
python refactored_api.py

# 3. 檢查服務配置
.\nssm\nssm.exe dump F1T-API

# 4. 查看 Windows 事件日誌
Get-EventLog -LogName Application -Source "F1T-API" -Newest 10
```

**常見原因**:
- ❌ Python 路徑錯誤
- ❌ 工作目錄錯誤
- ❌ 缺少依賴套件
- ❌ 埠號被佔用
- ❌ 權限不足

**解決方案**:
```powershell
# 重新配置服務
.\nssm\uninstall-services.ps1
.\nssm\install-services.ps1

# 或手動修正
.\nssm\nssm.exe edit F1T-API    # 開啟 GUI 編輯器
```

---

### **問題 2: 服務頻繁重啟**

**症狀**: 服務狀態在 Running 和 Stopped 之間不斷切換

**診斷**:
```powershell
# 查看日誌
Get-Content logs\f1t-api.log -Tail 100
Get-Content logs\f1t-api.error.log -Tail 100

# 檢查重啟配置
.\nssm\nssm.exe get F1T-API AppRestartDelay
.\nssm\nssm.exe get F1T-API AppThrottle
```

**解決方案**:
```powershell
# 增加重啟延遲
.\nssm\nssm.exe set F1T-API AppRestartDelay 30000  # 30 秒

# 增加節流時間
.\nssm\nssm.exe set F1T-API AppThrottle 5000      # 5 秒

# 或暫時停用自動重啟
.\nssm\nssm.exe set F1T-API AppExit Default Exit
```

---

### **問題 3: 無法卸載服務**

**症狀**: 執行 uninstall-services.ps1 後服務仍存在

**解決方案**:
```powershell
# 方式 A: 手動停止並刪除
Stop-Service -Name F1T-API -Force
sc.exe delete F1T-API

# 方式 B: 使用 NSSM 強制刪除
.\nssm\nssm.exe remove F1T-API confirm

# 方式 C: 使用 Windows 登錄檔（最後手段）
# ⚠️ 謹慎操作！
Remove-Item "HKLM:\SYSTEM\CurrentControlSet\Services\F1T-API" -Recurse -Force
```

---

### **問題 4: 日誌檔案過大**

**症狀**: logs\ 目錄佔用大量磁碟空間

**解決方案**:
```powershell
# 方式 A: 啟用日誌輪轉（推薦）
.\nssm\nssm.exe set F1T-API AppStdoutRotateFiles 5
.\nssm\nssm.exe set F1T-API AppStdoutRotateBytes 10485760  # 10MB

# 方式 B: 手動清理舊日誌
Get-ChildItem logs\*.log | Where-Object { $_.Length -gt 100MB } | Remove-Item

# 方式 C: 設定定時清理任務
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File cleanup-logs.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "03:00"
Register-ScheduledTask -TaskName "F1T-LogCleanup" -Action $action -Trigger $trigger
```

---

### **問題 5: 權限錯誤**

**症狀**: "Access Denied" 或 "Permission Error"

**解決方案**:
```powershell
# 1. 確保以管理員執行
# 右鍵 PowerShell → 以系統管理員身分執行

# 2. 修改服務執行帳戶（如需要）
.\nssm\nssm.exe set F1T-API ObjectName "LocalSystem"

# 3. 檢查檔案權限
icacls logs\f1t-api.log
```

---

## 📚 最佳實踐

### **1. 開發環境配置**

```powershell
# 使用手動啟動類型（不自動啟動）
.\nssm\nssm.exe set F1T-API Start SERVICE_DEMAND_START

# 需要時手動啟動
.\nssm\manage-services.ps1 -Action Start
```

---

### **2. 生產環境配置**

```powershell
# 使用自動啟動
.\nssm\nssm.exe set F1T-API Start SERVICE_AUTO_START

# 配置自動重啟
.\nssm\nssm.exe set F1T-API AppExit Default Restart
.\nssm\nssm.exe set F1T-API AppRestartDelay 5000

# 啟用日誌輪轉
.\nssm\nssm.exe set F1T-API AppStdoutRotateFiles 5
.\nssm\nssm.exe set F1T-API AppStdoutRotateBytes 10485760
```

---

### **3. 定期維護**

```powershell
# 每週檢查服務狀態
.\nssm\manage-services.ps1 -Action Status

# 每月清理舊日誌
Get-ChildItem logs\*.log.* | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item

# 檢查服務健康度
Get-Service F1T-* | Select-Object Name, Status, StartType
```

---

### **4. 監控與告警**

```powershell
# 創建監控腳本
$script = @"
`$services = Get-Service F1T-*
foreach (`$svc in `$services) {
    if (`$svc.Status -ne 'Running') {
        Write-Host "⚠️ `$(`$svc.Name) is `$(`$svc.Status)" -ForegroundColor Red
        # 發送告警郵件或通知
    }
}
"@

# 設定定時任務（每 5 分鐘檢查）
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-Command `"$script`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "F1T-ServiceMonitor" -Action $action -Trigger $trigger
```

---

## 📊 命令速查表

### **NSSM 常用命令**

| 操作 | 命令 |
|------|------|
| 安裝服務 | `.\nssm\nssm.exe install <服務名> <應用程式路徑> <參數>` |
| 移除服務 | `.\nssm\nssm.exe remove <服務名> confirm` |
| 啟動服務 | `.\nssm\nssm.exe start <服務名>` |
| 停止服務 | `.\nssm\nssm.exe stop <服務名>` |
| 重啟服務 | `.\nssm\nssm.exe restart <服務名>` |
| 編輯服務 | `.\nssm\nssm.exe edit <服務名>` |
| 查看配置 | `.\nssm\nssm.exe dump <服務名>` |
| 設定參數 | `.\nssm\nssm.exe set <服務名> <參數> <值>` |
| 查看參數 | `.\nssm\nssm.exe get <服務名> <參數>` |
| 重置參數 | `.\nssm\nssm.exe reset <服務名> <參數>` |

---

### **PowerShell 服務命令**

| 操作 | 命令 |
|------|------|
| 查看服務 | `Get-Service F1T-*` |
| 啟動服務 | `Start-Service -Name F1T-API` |
| 停止服務 | `Stop-Service -Name F1T-API -Force` |
| 重啟服務 | `Restart-Service -Name F1T-API` |
| 查看詳細 | `Get-Service F1T-API \| Format-List *` |
| 查看進程 | `Get-Process python, cloudflared` |

---

## 🔗 相關資源

- **NSSM 官網**: https://nssm.cc/
- **NSSM 文檔**: https://nssm.cc/usage
- **下載連結**: https://nssm.cc/download
- **GitHub**: https://github.com/kirillkovalenko/nssm

---

## ✅ 總結

### **NSSM vs 其他方案**

| 特性 | NSSM | PowerShell | Supervisor | Docker |
|------|------|-----------|-----------|--------|
| **適用平台** | ✅ Windows | ✅ Windows | ❌ Linux only | ✅ 跨平台 |
| **安裝難度** | 🟢 簡單 | 🟢 無需安裝 | ❌ | 🟡 中等 |
| **Windows 服務** | ✅ 完整 | ❌ | ❌ | ⚠️ 有限 |
| **自動重啟** | ✅ | ❌ | ✅ | ✅ |
| **GUI 管理** | ✅ | ❌ | ⚠️ Web | ⚠️ 有限 |
| **生產就緒** | ✅ | ⚠️ | ❌ | ✅ |

### **推薦使用場景**

- ✅ **開發穩定後**: 使用 NSSM（當前階段）
- ✅ **長期運行**: Windows 服務最佳選擇
- ✅ **需要開機自啟**: NSSM 最簡單
- ✅ **需要自動恢復**: NSSM 內建支援
- ✅ **Windows 生產環境**: NSSM 首選

---

**最後更新**: 2025-10-13  
**文檔版本**: 1.0.0  
**維護者**: F1T Team
