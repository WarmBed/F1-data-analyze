# F1T Windows 服務管理系統

**版本**: 1.0.0  
**適用平台**: Windows 10/11  
**建立日期**: 2025-10-13

---

## 🎯 簡介

**Supervisor 不支援 Windows**，因此我們提供了 **純 PowerShell 解決方案**，無需安裝任何第三方軟體。

### ✅ 核心功能

- ✅ 一鍵啟動/停止所有服務
- ✅ 背景執行（不佔用終端）
- ✅ 自動日誌記錄
- ✅ 服務狀態監控
- ✅ 進程管理
- ✅ 零依賴（純 PowerShell）

---

## 🚀 快速開始

### **啟動所有服務**

```powershell
.\windows\start-services.ps1
```

**會啟動 3 個服務：**
- **F1T-API** - REST API 服務 (`refactored_api.py`)
- **Periodic-Update** - 定時更新服務 (`periodic_update_service.py`)
- **Cloudflare-Tunnel** - 公開 API 到外網 (`cloudflared.exe`)

---

### **查看服務狀態**

```powershell
.\windows\check-status.ps1
```

**輸出範例：**
```
[1/3] PowerShell Background Jobs:
Id  Name  State   HasMoreData
--  ----  -----   -----------
1   Job1  Running True
2   Job2  Running True
3   Job3  Running True

[2/3] Related Processes:
  Python (API/Update): PID 12345, CPU: 2.5s, Memory: 85.6MB
  Cloudflare Tunnel: PID 12346, CPU: 1.2s, Memory: 45.3MB

[3/3] Recent Log Activity:
  logs\f1t-api.log: 125.4KB, updated 30s ago
  logs\periodic-update.log: 45.2KB, updated 1m ago
  logs\cloudflare-tunnel.log: 78.9KB, updated 45s ago
```

---

### **停止所有服務**

```powershell
.\windows\stop-services.ps1
```

**會自動：**
- 停止所有 PowerShell 背景作業
- 終止相關進程
- 清理臨時檔案

---

## 📋 完整命令參考

### **基本操作**

| 操作 | 命令 |
|------|------|
| 啟動所有服務 | `.\windows\start-services.ps1` |
| 停止所有服務 | `.\windows\stop-services.ps1` |
| 查看狀態 | `.\windows\check-status.ps1` |
| 重啟所有服務 | `.\windows\stop-services.ps1; .\windows\start-services.ps1` |

---

### **日誌管理**

```powershell
# 查看 API 服務即時日誌（最後 50 行 + 持續追蹤）
Get-Content logs\f1t-api.log -Tail 50 -Wait

# 查看定時更新服務日誌
Get-Content logs\periodic-update.log -Tail 50 -Wait

# 查看 Cloudflare Tunnel 日誌
Get-Content logs\cloudflare-tunnel.log -Tail 50 -Wait

# 查看所有日誌檔案大小
Get-ChildItem logs\*.log | Select-Object Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB, 2)}}

# 清理舊日誌（保留最近 7 天）
Get-ChildItem logs\*.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
```

---

### **進程管理**

```powershell
# 查看所有 PowerShell 背景作業
Get-Job

# 查看特定作業詳細資訊
Get-Job -Id 1 | Format-List *

# 接收作業輸出
Receive-Job -Id 1

# 手動停止特定作業
Stop-Job -Id 1
Remove-Job -Id 1 -Force

# 查看 Python 進程
Get-Process python | Where-Object { $_.Path -like "*F1-data-analyze*" }

# 查看 Cloudflared 進程
Get-Process cloudflared
```

---

## 🔧 進階配置

### **修改服務定義**

編輯 `windows\start-services.ps1`，修改 `$services` 陣列：

```powershell
$services = @(
    @{
        Name = "F1T-API"                          # 服務名稱
        Command = "python"                        # 執行命令
        Args = @("refactored_api.py")            # 命令參數
        LogFile = "logs\f1t-api.log"             # 日誌檔案
        Color = "Green"                           # 顯示顏色
    },
    # ... 更多服務
)
```

---

### **新增自訂服務**

```powershell
# 範例：新增資料庫清理服務
@{
    Name = "DB-Cleanup"
    Command = "python"
    Args = @("scripts\db_cleanup.py", "--interval", "3600")
    LogFile = "logs\db-cleanup.log"
    Color = "Magenta"
}
```

---

## 🎓 故障排除

### **問題 1: 服務無法啟動**

**症狀**: 執行 `start-services.ps1` 後沒有顯示作業

**解決方案**:
```powershell
# 1. 檢查 PowerShell 執行策略
Get-ExecutionPolicy

# 2. 臨時允許腳本執行
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. 重新啟動
.\windows\start-services.ps1

# 4. 檢查日誌
Get-Content logs\f1t-api.log -Tail 50
```

---

### **問題 2: 埠號被佔用**

**症狀**: API 服務啟動失敗，日誌顯示 "Address already in use"

**解決方案**:
```powershell
# 1. 找出佔用埠號的進程
Get-NetTCPConnection -LocalPort 8000 -State Listen

# 2. 終止該進程
Stop-Process -Id <PID> -Force

# 3. 重新啟動服務
.\windows\start-services.ps1
```

---

### **問題 3: 作業殭屍狀態**

**症狀**: `Get-Job` 顯示 "Failed" 或 "Completed" 但進程仍在運行

**解決方案**:
```powershell
# 1. 清理所有作業
Get-Job | Remove-Job -Force

# 2. 手動終止進程
Get-Process python | Where-Object { $_.Path -like "*F1-data-analyze*" } | Stop-Process -Force

# 3. 重新啟動
.\windows\start-services.ps1
```

---

### **問題 4: 日誌檔案過大**

**症狀**: 日誌檔案佔用大量磁碟空間

**解決方案**:
```powershell
# 1. 檢查日誌大小
Get-ChildItem logs\*.log | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB, 2)}}

# 2. 清空特定日誌（謹慎操作）
"" | Out-File logs\f1t-api.log -Encoding utf8

# 3. 設定日誌輪轉（未來功能）
# 可在 Python 程式中使用 RotatingFileHandler
```

---

## 🆚 方案比較

### **Windows 進程管理方案對比**

| 功能 | PowerShell (本方案) | NSSM | Supervisor | Docker |
|------|-------------------|------|-----------|--------|
| **Windows 支援** | ✅ 原生 | ✅ 原生 | ❌ 不支援 | ✅ 支援 |
| **安裝難度** | 🟢 無需安裝 | 🟡 需下載 | ❌ 無法使用 | 🟡 需安裝 Docker |
| **背景執行** | ✅ 支援 | ✅ 支援 | N/A | ✅ 支援 |
| **自動重啟** | ⚠️ 手動實現 | ✅ 內建 | N/A | ✅ 內建 |
| **開機自啟** | ⚠️ 需配置 | ✅ 簡單 | N/A | ✅ 簡單 |
| **日誌管理** | ✅ 基本支援 | ✅ 完整 | N/A | ✅ 完整 |
| **適用階段** | 🎯 開發/測試 | 🎯 生產 | ❌ | 🎯 生產 |

---

## 🔄 升級路徑

### **開發階段（現在）**
```
使用 PowerShell 腳本
↓
優勢：零依賴、快速迭代、易於調試
```

### **穩定階段（1-2 週後）**
```
升級至 NSSM
↓
優勢：Windows 服務、自動重啟、開機自啟
```

### **生產階段（未來）**
```
容器化 Docker
↓
優勢：跨平台、完整隔離、易於部署
```

---

## 📚 相關資源

### **PowerShell 學習**
- [PowerShell 官方文檔](https://docs.microsoft.com/powershell/)
- [Background Jobs 指南](https://docs.microsoft.com/powershell/module/microsoft.powershell.core/about/about_jobs)

### **NSSM（未來升級）**
- [NSSM 官網](https://nssm.cc/)
- [下載連結](https://nssm.cc/download)

### **Docker（長期方案）**
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- [Docker Compose 文檔](https://docs.docker.com/compose/)

---

## ❓ 常見問題

### **Q1: 為什麼不用 Supervisor？**
**A**: Supervisor 只支援 UNIX/Linux 系統，Windows 上無法運行。

### **Q2: PowerShell 腳本會佔用終端嗎？**
**A**: 不會！服務在背景作業 (Background Job) 中執行，不佔用終端窗口。

### **Q3: 如何實現開機自啟？**
**A**: 可使用 Windows 任務排程器或升級至 NSSM。

### **Q4: 服務崩潰會自動重啟嗎？**
**A**: 當前版本不會自動重啟，建議穩定後升級至 NSSM 或 Docker。

### **Q5: 可以同時運行多個實例嗎？**
**A**: 需避免埠號衝突，建議修改配置檔案中的埠號設定。

---

## 🎯 總結

### **最佳實踐**

✅ **開發時**: 使用 PowerShell 腳本（當前方案）  
✅ **測試時**: 持續使用 PowerShell，觀察穩定性  
✅ **穩定後**: 考慮升級至 NSSM（Windows 服務）  
✅ **生產時**: 最終容器化 Docker（跨平台部署）

### **推薦工作流程**

```powershell
# 早上開始工作
.\windows\start-services.ps1

# 開發過程中檢查狀態
.\windows\check-status.ps1

# 查看日誌除錯
Get-Content logs\f1t-api.log -Tail 50 -Wait

# 晚上下班關閉
.\windows\stop-services.ps1
```

---

**最後更新**: 2025-10-13  
**文檔版本**: 1.0.0  
**維護者**: F1T Team
