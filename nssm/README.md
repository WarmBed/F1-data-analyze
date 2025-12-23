# F1T NSSM 服務管理系統

**Windows 專業級服務管理解決方案**

使用 NSSM (Non-Sucking Service Manager) 將 F1T 系統轉換為 Windows 原生服務。

---

## 🚀 快速開始（3 步驟）

### **1. 一鍵安裝**

以**管理員權限**執行 PowerShell，然後運行：

```powershell
.\nssm\quick-setup.ps1
```

這將自動：
- ✅ 下載並安裝 NSSM
- ✅ 註冊所有 F1T 服務
- ✅ 配置自動重啟和日誌
- ✅ 啟動服務

---

### **2. 管理服務**

```powershell
# 查看狀態
.\nssm\manage-services.ps1

# 啟動所有服務
.\nssm\manage-services.ps1 -Action Start

# 停止所有服務
.\nssm\manage-services.ps1 -Action Stop

# 重啟所有服務
.\nssm\manage-services.ps1 -Action Restart
```

---

### **3. 使用 Windows 服務管理器**

```powershell
services.msc
```

---

## 📁 檔案結構

```
nssm/
├── quick-setup.ps1           # 一鍵安裝嚮導（推薦使用）
├── install-nssm.ps1          # 下載並安裝 NSSM
├── install-services.ps1      # 註冊所有服務
├── uninstall-services.ps1    # 卸載所有服務
├── manage-services.ps1       # 統一管理介面
├── NSSM_GUIDE.md            # 完整使用指南
└── README.md                # 本檔案
```

---

## 🎯 管理的服務

| 服務名稱 | 顯示名稱 | 程式 | 功能 |
|---------|---------|------|------|
| **F1T-API** | F1T Telemetry API Server | `refactored_api.py` | REST API 服務 |
| **F1T-PeriodicUpdate** | F1T Periodic Update Service | `periodic_update_service.py` | 定時數據更新 |
| **F1T-CloudflareTunnel** | F1T Cloudflare Tunnel | `cloudflared.exe` | 公開 API 到網際網路 |

---

## ✨ 核心功能

### **自動化管理**
- ✅ **開機自啟** - 系統啟動時自動運行
- ✅ **崩潰恢復** - 服務崩潰自動重啟
- ✅ **依賴管理** - 服務啟動順序控制
- ✅ **日誌輪轉** - 自動管理日誌檔案大小

### **專業監控**
- ✅ **Windows 整合** - 使用 services.msc 管理
- ✅ **進程監控** - CPU/記憶體使用追蹤
- ✅ **日誌分析** - 即時日誌查看
- ✅ **狀態報告** - 詳細服務狀態

---

## 📚 詳細文檔

完整的使用指南請參閱：[NSSM_GUIDE.md](NSSM_GUIDE.md)

內容包括：
- 📖 詳細安裝步驟
- 🔧 進階配置選項
- 🛠️ 故障排除指南
- 📊 命令速查表
- 💡 最佳實踐建議

---

## 🆚 與其他方案比較

| 功能 | NSSM | PowerShell | Supervisor | Docker |
|------|------|-----------|-----------|--------|
| **Windows 原生** | ✅ 完整 | ✅ 有限 | ❌ | ⚠️ |
| **自動重啟** | ✅ | ❌ | ✅ | ✅ |
| **開機自啟** | ✅ | ⚠️ | ❌ | ⚠️ |
| **GUI 管理** | ✅ | ❌ | ⚠️ | ❌ |
| **安裝難度** | 🟢 | 🟢 | 🔴 | 🟡 |
| **生產就緒** | ✅ | ⚠️ | ❌ | ✅ |

**NSSM 是 Windows 上最專業的進程管理方案！**

---

## 🎓 常用命令速查

### **服務管理**

```powershell
# 狀態查看
.\nssm\manage-services.ps1 -Action Status

# 啟動/停止/重啟
.\nssm\manage-services.ps1 -Action Start
.\nssm\manage-services.ps1 -Action Stop
.\nssm\manage-services.ps1 -Action Restart

# 單一服務操作
.\nssm\manage-services.ps1 -Action Start -Service F1T-API
```

---

### **日誌查看**

```powershell
# 即時日誌追蹤
Get-Content logs\f1t-api.log -Tail 50 -Wait
Get-Content logs\periodic-update.log -Tail 50 -Wait
Get-Content logs\cloudflare-tunnel.log -Tail 50 -Wait

# 開啟日誌目錄
.\nssm\manage-services.ps1 -Action Logs
```

---

### **NSSM 命令**

```powershell
# 查看服務配置
.\nssm\nssm.exe dump F1T-API

# 編輯服務（GUI）
.\nssm\nssm.exe edit F1T-API

# 修改參數
.\nssm\nssm.exe set F1T-API AppRestartDelay 10000
```

---

### **Windows 服務命令**

```powershell
# PowerShell 管理
Get-Service F1T-*
Start-Service -Name F1T-API
Stop-Service -Name F1T-API -Force
Restart-Service -Name F1T-API

# 開啟服務管理器
services.msc
```

---

## ⚠️ 重要提醒

### **管理員權限**
所有服務管理操作都需要**管理員權限**。

右鍵 PowerShell → **以系統管理員身分執行**

---

### **首次使用**

1. **執行快速安裝**:
   ```powershell
   .\nssm\quick-setup.ps1
   ```

2. **驗證服務狀態**:
   ```powershell
   .\nssm\manage-services.ps1 -Action Status
   ```

3. **測試 API**:
   ```powershell
   Invoke-WebRequest http://localhost:8000/health
   ```

---

## 🔗 相關連結

- **NSSM 官網**: https://nssm.cc/
- **下載連結**: https://nssm.cc/download
- **使用文檔**: https://nssm.cc/usage
- **完整指南**: [NSSM_GUIDE.md](NSSM_GUIDE.md)

---

## 📞 支援

遇到問題？

1. 查看 **[NSSM_GUIDE.md](NSSM_GUIDE.md)** 的故障排除章節
2. 檢查日誌檔案: `logs\*.log` 和 `logs\*.error.log`
3. 查看 Windows 事件日誌: `eventvwr.msc`

---

**版本**: 1.0.0  
**最後更新**: 2025-10-13  
**維護者**: F1T Team
